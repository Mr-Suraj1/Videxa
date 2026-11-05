import logging

import pytest

import core.llm as llm
import core.transcriber as transcriber


def test_gemini_client_uses_configured_key_and_model(monkeypatch):
    captured = {}
    monkeypatch.setenv("GOOGLE_API_KEY", "not-for-logs")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(llm, "ChatGoogleGenerativeAI", lambda **kwargs: captured.update(kwargs) or kwargs)
    llm.get_llm(temperature=0.2)
    assert captured["google_api_key"] == "not-for-logs"
    assert captured["temperature"] == 0.2
    assert captured["timeout"] == 60
    assert captured["max_retries"] == 0
    assert captured["model"] == "gemini-3.7-flash"


def test_gemini_model_is_overridable_via_env(monkeypatch):
    captured = {}
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-flash")
    monkeypatch.setattr(llm, "ChatGoogleGenerativeAI", lambda **kwargs: captured.update(kwargs) or kwargs)
    llm.get_llm()
    assert captured["model"] == "gemini-1.5-flash"


class FakeResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self.payload = payload or {"transcript": "translated"}

    def json(self):
        return self.payload


def test_sarvam_retries_only_transient_failure(monkeypatch, tmp_path):
    piece = tmp_path / "piece.wav"
    piece.write_bytes(b"audio")
    responses = iter([FakeResponse(503), FakeResponse(200)])
    monkeypatch.setenv("SARVAM_API_KEY", "not-for-logs")
    monkeypatch.setattr(transcriber.requests, "post", lambda *_, **__: next(responses))
    monkeypatch.setattr(transcriber.time, "sleep", lambda _: None)
    assert transcriber._send_to_sarvam(str(piece)) == "translated"


def test_sarvam_does_not_retry_auth_failure(monkeypatch, tmp_path):
    piece = tmp_path / "piece.wav"
    piece.write_bytes(b"audio")
    calls = []
    monkeypatch.setenv("SARVAM_API_KEY", "not-for-logs")
    monkeypatch.setattr(transcriber.requests, "post", lambda *_, **__: calls.append(True) or FakeResponse(401))
    with pytest.raises(transcriber.TranscriptionError, match="could not transcribe"):
        transcriber._send_to_sarvam(str(piece))
    assert len(calls) == 1


def test_provider_logs_never_include_api_key(monkeypatch, tmp_path, caplog):
    piece = tmp_path / "piece.wav"
    piece.write_bytes(b"audio")
    secret = "sensitive-provider-key"
    monkeypatch.setenv("SARVAM_API_KEY", secret)
    monkeypatch.setattr(transcriber.requests, "post", lambda *_, **__: FakeResponse(401))
    caplog.set_level(logging.WARNING)
    with pytest.raises(transcriber.TranscriptionError):
        transcriber._send_to_sarvam(str(piece))
    assert secret not in caplog.text


def test_gemini_retry_honors_retry_after_seconds(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 429
        response = type("Response", (), {"headers": {"Retry-After": "5"}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ProviderFailure()
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert delays == [5.0]


def test_gemini_retry_honors_retry_after_http_date(monkeypatch):
    import core.gemini_retry as retry
    import email.utils
    from datetime import datetime, timezone, timedelta

    future = datetime.now(timezone.utc) + timedelta(seconds=3)
    date_str = email.utils.format_datetime(future)

    class ProviderFailure(Exception):
        http_status = 429
        response = type("Response", (), {"headers": {"Retry-After": date_str}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ProviderFailure()
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert len(delays) == 1
    assert 0.0 <= delays[0] <= 5.0


def test_gemini_does_not_retry_before_long_retry_after(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 429
        response = type("Response", (), {"headers": {"Retry-After": "3600"}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ProviderFailure()

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("long provider delay must not sleep"))
    with pytest.raises(retry.GeminiProviderError) as error:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert error.value.category == "rate_limit"
    assert model.calls == 1


def test_gemini_fallback_backoff_is_bounded_and_capped(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 429
        response = type("Response", (), {"headers": {}})()

    class Model:
        def invoke(self, prompt):
            raise ProviderFailure()

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    monkeypatch.setattr(retry.random, "uniform", lambda low, high: high)
    with pytest.raises(retry.GeminiProviderError) as error:
        retry.invoke_with_gemini_retry(Model(), "prompt")
    assert error.value.category == "rate_limit"
    assert len(delays) == retry.MAX_ATTEMPTS - 1
    assert delays == [1.25, 2.5]
    assert all(d <= retry.MAX_RETRY_AFTER_SECONDS for d in delays)


def test_gemini_quota_failure_is_not_retried(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 429
        response = type("Response", (), {"headers": {"Retry-After": "3"}})()

        def __str__(self):
            return "exceeded your quota: billing limit reached"

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ProviderFailure()

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("quota errors must not sleep/retry"))
    with pytest.raises(retry.GeminiProviderError) as error:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert error.value.category == "quota"
    assert model.calls == 1


def test_gemini_auth_failure_is_not_retried(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 401
        response = type("Response", (), {"headers": {}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ProviderFailure()

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("auth errors must not sleep/retry"))
    with pytest.raises(retry.GeminiProviderError) as error:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert error.value.category == "auth"
    assert model.calls == 1


def test_gemini_503_is_retried(monkeypatch):
    import core.gemini_retry as retry

    class ProviderFailure(Exception):
        http_status = 503
        response = type("Response", (), {"headers": {}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls < retry.MAX_ATTEMPTS:
                raise ProviderFailure()
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert len(delays) == retry.MAX_ATTEMPTS - 1


def test_gemini_503_sdk_exception_retries_and_succeeds(monkeypatch):
    """GoogleAPIError / ServerError with code=503 is retried and succeeds."""
    from google.genai.errors import ServerError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ServerError(503, {"message": "model experiencing high demand", "status": "UNAVAILABLE"})
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert len(delays) == 1


def test_gemini_503_sdk_exception_exhausts_all_attempts(monkeypatch):
    """Persistent ServerError 503 stops after MAX_ATTEMPTS total attempts."""
    from google.genai.errors import ServerError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ServerError(503, {"message": "model experiencing high demand", "status": "UNAVAILABLE"})

    model = Model()
    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    with pytest.raises(retry.GeminiProviderError) as exc_info:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert exc_info.value.category == "rate_limit"
    assert model.calls == retry.MAX_ATTEMPTS
    assert len(delays) == retry.MAX_ATTEMPTS - 1


def test_gemini_429_sdk_rate_limit_not_classified_as_quota(monkeypatch):
    """ClientError 429 with RESOURCE_EXHAUSTED status is retried, not treated as quota."""
    from google.genai.errors import ClientError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ClientError(429, {"message": "rate limit exceeded", "status": "RESOURCE_EXHAUSTED"})
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert len(delays) == 1


def test_gemini_504_sdk_exception_retries_and_succeeds(monkeypatch):
    """ServerError with code=504 is retried and succeeds on the next attempt."""
    from google.genai.errors import ServerError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ServerError(504, {"message": "deadline exceeded", "status": "DEADLINE_EXCEEDED"})
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_gemini_retry(Model(), "prompt") == "ok"
    assert len(delays) == 1


def test_gemini_503_long_retry_after_stops_and_preserves_status_code(monkeypatch):
    """503 with Retry-After > cap stops immediately with status_code=503, not 429."""
    from google.genai.errors import ServerError
    import core.gemini_retry as retry

    class Response:
        headers = {"Retry-After": "3600"}

    exc = ServerError(503, {"message": "model experiencing high demand", "status": "UNAVAILABLE"})
    exc.response = Response()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise exc

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("long Retry-After must not sleep"))
    with pytest.raises(retry.GeminiProviderError) as exc_info:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert exc_info.value.category == "rate_limit"
    assert exc_info.value.status_code == 503
    assert model.calls == 1


def test_google_rate_limit_error_quota_is_not_retried(monkeypatch):
    """GoogleRateLimitError (no .code attr) with quota message stops immediately."""
    from langchain_google_genai.chat_models import GoogleRateLimitError
    import core.gemini_retry as retry

    msg = (
        "Error calling model 'gemini-3.8-flash' (RESOURCE_EXHAUSTED): "
        "429 RESOURCE_EXHAUSTED. exceeded your quota: daily limit reached. "
        "Please retry in 19h3m33s."
    )

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise GoogleRateLimitError(msg)

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("quota must not sleep/retry"))
    with pytest.raises(retry.GeminiProviderError) as exc_info:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert exc_info.value.category == "quota"
    assert exc_info.value.status_code == 429
    assert model.calls == 1


def test_google_auth_error_is_not_retried(monkeypatch):
    """GoogleAuthenticationError (no .code attr) is classified as auth failure."""
    from langchain_google_genai.chat_models import GoogleAuthenticationError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise GoogleAuthenticationError("Invalid API key.")

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("auth must not sleep/retry"))
    with pytest.raises(retry.GeminiProviderError) as exc_info:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert exc_info.value.category == "auth"
    assert exc_info.value.status_code == 401
    assert model.calls == 1


def test_gemini_504_sdk_exception_exhausts_all_attempts(monkeypatch):
    """Persistent ServerError 504 stops after MAX_ATTEMPTS and reports status_code=504."""
    from google.genai.errors import ServerError
    import core.gemini_retry as retry

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ServerError(504, {"message": "deadline exceeded", "status": "DEADLINE_EXCEEDED"})

    model = Model()
    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    with pytest.raises(retry.GeminiProviderError) as exc_info:
        retry.invoke_with_gemini_retry(model, "prompt")
    assert exc_info.value.category == "rate_limit"
    assert exc_info.value.status_code == 504
    assert model.calls == retry.MAX_ATTEMPTS
    assert len(delays) == retry.MAX_ATTEMPTS - 1
