"""Bounded retry handling for temporary Gemini API quota limits."""

from __future__ import annotations

import email.utils
import random
import time
from datetime import datetime, timezone
from typing import Any

MAX_ATTEMPTS = 3
MAX_RETRY_AFTER_SECONDS = 30.0
BASE_BACKOFF_SECONDS = 1.0


class GeminiProviderError(RuntimeError):
    def __init__(self, message: str, *, category: str, status_code: int | None = None):
        super().__init__(message)
        self.category = category
        self.status_code = status_code


def _http_status(exc: Exception) -> int | None:
    # google.genai.errors.APIError stores HTTP status as .code (int).
    # LangChain wraps it as GoogleAPIError, which inherits the same attribute.
    for attr in ("http_status", "_http_status", "status_code", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    # LangChain-typed errors inherit from ChatGoogleGenerativeAIError, not APIError,
    # so they carry no .code. Map by class name so they reach the right handler path.
    cls_name = type(exc).__name__
    if cls_name in ("GoogleRateLimitError", "ModelRateLimitError"):
        return 429
    if cls_name in ("GoogleAuthenticationError", "ModelAuthenticationError"):
        return 401
    if cls_name in ("GooglePermissionDeniedError", "ModelPermissionDeniedError"):
        return 403
    # google.api_core legacy class-name fallbacks.
    if cls_name == "ResourceExhausted":
        return 429
    if cls_name in ("ServiceUnavailable", "DeadlineExceeded"):
        return 503
    if cls_name == "Unauthenticated":
        return 401
    if cls_name == "PermissionDenied":
        return 403
    return None


def _is_quota(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(term in msg for term in (
        "quota", "billing", "insufficient_quota",
        "exceeded your quota", "daily limit",
    ))


def _is_auth_failure(exc: Exception, status: int | None) -> bool:
    if status in {401, 403}:
        return True
    return type(exc).__name__ in ("Unauthenticated", "PermissionDenied")


def _retry_after(exc: Exception) -> float | None:
    """Extract Retry-After delay from exception. Returns -1.0 if the delay exceeds the cap."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None) or {}
    value = next((v for k, v in headers.items() if str(k).lower() == "retry-after"), None)
    if value is None:
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        try:
            retry_at = email.utils.parsedate_to_datetime(str(value))
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
        except (TypeError, ValueError, OverflowError):
            return None
    if seconds > MAX_RETRY_AFTER_SECONDS:
        return -1.0
    return max(0.0, seconds)


def invoke_with_gemini_retry(model: Any, prompt: Any) -> Any:
    """Invoke once or retry transient 429/503/504s with bounded backoff."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            status = _http_status(exc)
            # Explicit model-not-found check before auth check
            cls_name = type(exc).__name__
            if cls_name in ("GoogleModelNotFoundError", "ModelNotFoundError") or status == 404:
                model_name = getattr(model, "model", "unknown")
                raise GeminiProviderError(
                    f"Gemini model '{model_name}' was not found. Update GEMINI_MODEL in your .env file "
                    f"(try: gemini-2.0-flash or gemini-1.5-flash-latest).",
                    category="config",
                    status_code=404,
                ) from exc
            if _is_auth_failure(exc, status):
                raise GeminiProviderError(
                    "Gemini API rejected the credentials. Check GOOGLE_API_KEY in the backend environment.",
                    category="auth",
                    status_code=status or 401,
                ) from exc
            if status not in {429, 503, 504}:
                raise
            if _is_quota(exc):
                raise GeminiProviderError(
                    "Gemini API quota or billing limit reached. Check GOOGLE_API_KEY quota in Google Cloud Console.",
                    category="quota",
                    status_code=status,
                ) from exc
            if attempt == MAX_ATTEMPTS:
                raise GeminiProviderError(
                    "Gemini API is temporarily rate limited. Wait for the limit to reset, then retry.",
                    category="rate_limit",
                    status_code=status,
                ) from exc
            delay = _retry_after(exc)
            if delay == -1.0:
                raise GeminiProviderError(
                    "Gemini API requested a longer retry delay. Wait for the provider limit to reset, then retry.",
                    category="rate_limit",
                    status_code=status,
                ) from exc
            if delay is None:
                delay = min(
                    MAX_RETRY_AFTER_SECONDS,
                    BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)) * random.uniform(0.75, 1.25),
                )
            time.sleep(delay)
    raise AssertionError("unreachable")
