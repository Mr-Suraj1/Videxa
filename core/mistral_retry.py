"""Bounded retry handling for temporary Mistral request limits."""

from __future__ import annotations

import email.utils
import json
import random
import time
from datetime import datetime, timezone
from typing import Any


MAX_ATTEMPTS = 3
MAX_RETRY_AFTER_SECONDS = 30.0
BASE_BACKOFF_SECONDS = 1.0


class MistralProviderError(RuntimeError):
    def __init__(self, message: str, *, category: str, status_code: int | None = None):
        super().__init__(message)
        self.category = category
        self.status_code = status_code


def _provider_response(exc: Exception) -> tuple[int | None, Any, Any]:
    response = getattr(exc, "response", None)
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status is None and response is not None:
        status = getattr(response, "status_code", None)
    headers = getattr(response, "headers", None) or getattr(exc, "headers", None) or {}
    payload: Any = getattr(exc, "body", None)
    if payload is None and response is not None:
        try:
            payload = response.json()
        except Exception:
            payload = getattr(response, "text", "")
    return status, headers, payload


def _payload_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload.lower()
    try:
        return json.dumps(payload, default=str).lower()
    except (TypeError, ValueError):
        return str(payload).lower()


def _retry_after(headers: Any) -> float | None:
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
        # Do not retry before the provider's requested delay. Defer to the
        # user instead of sleeping too long or violating Retry-After.
        return -1.0
    return max(0.0, seconds)


def _classify_429(payload: Any) -> str:
    text = _payload_text(payload)
    if any(term in text for term in (
        "insufficient_quota", "billing", "spending limit", "payment required",
        "quota exceeded", "workspace_quota", "exceeded your quota",
    )):
        return "quota"
    return "rate_limit"


def invoke_with_mistral_retry(model: Any, prompt: Any) -> Any:
    """Invoke once or retry transient 429s using Retry-After / bounded backoff."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return model.invoke(prompt)
        except Exception as exc:
            status, headers, payload = _provider_response(exc)
            if status not in {402, 429}:
                raise
            category = _classify_429(payload)
            if category == "quota":
                raise MistralProviderError(
                    "Mistral usage quota or billing limit was reached. Check the workspace usage and billing limits before retrying.",
                    category="quota", status_code=status,
                ) from exc
            if status == 402:
                raise MistralProviderError(
                    "Mistral requires a billing or quota action. Check the workspace usage and billing limits before retrying.",
                    category="quota", status_code=402,
                ) from exc
            if attempt == MAX_ATTEMPTS:
                raise MistralProviderError(
                    "Mistral is temporarily rate limited. Wait for the limit to reset, then retry analysis.",
                    category="rate_limit", status_code=429,
                ) from exc
            delay = _retry_after(headers)
            if delay == -1.0:
                raise MistralProviderError(
                    "Mistral requested a longer retry delay. Wait for the provider limit to reset, then retry analysis.",
                    category="rate_limit", status_code=429,
                ) from exc
            if delay is None:
                delay = min(MAX_RETRY_AFTER_SECONDS,
                            BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)) * random.uniform(0.75, 1.25))
            time.sleep(delay)
    raise AssertionError("unreachable")
