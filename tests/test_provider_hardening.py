import logging

import pytest

import core.llm as llm
import core.transcriber as transcriber


def test_mistral_client_uses_bounded_timeout_and_retry(monkeypatch):
    captured = {}
    monkeypatch.setenv("MISTRAL_API_KEY", "not-for-logs")
    monkeypatch.setattr(llm, "ChatMistralAI", lambda **kwargs: captured.update(kwargs) or kwargs)
    llm.get_llm(temperature=0.2)
    assert captured["api_key"] == "not-for-logs"
    assert captured["timeout"] == 60
    assert captured["max_retries"] == 0
    assert captured["max_concurrent_requests"] == 4


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


def test_mistral_retry_honors_retry_after(monkeypatch):
    import core.mistral_retry as retry

    class ProviderFailure(Exception):
        status_code = 429
        body = {"message": "Rate limit exceeded"}
        response = type("Response", (), {"headers": {"Retry-After": "4"}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            if self.calls == 1:
                raise ProviderFailure()
            return "ok"

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    assert retry.invoke_with_mistral_retry(Model(), "prompt") == "ok"
    assert delays == [4.0]


def test_mistral_fallback_backoff_is_bounded_and_capped(monkeypatch):
    import core.mistral_retry as retry

    class ProviderFailure(Exception):
        status_code = 429
        body = {"message": "Rate limit exceeded"}
        response = type("Response", (), {"headers": {}})()

    class Model:
        def invoke(self, prompt):
            raise ProviderFailure()

    delays = []
    monkeypatch.setattr(retry.time, "sleep", delays.append)
    monkeypatch.setattr(retry.random, "uniform", lambda low, high: high)
    with pytest.raises(retry.MistralProviderError) as error:
        retry.invoke_with_mistral_retry(Model(), "prompt")
    assert error.value.category == "rate_limit"
    assert len(delays) == retry.MAX_ATTEMPTS - 1
    assert delays == [1.25, 2.5]
    assert all(delay <= retry.MAX_RETRY_AFTER_SECONDS for delay in delays)


def test_mistral_quota_failure_is_not_retried(monkeypatch):
    import core.mistral_retry as retry

    class ProviderFailure(Exception):
        status_code = 429
        body = {"code": "insufficient_quota", "message": "billing limit reached"}
        response = type("Response", (), {"headers": {"Retry-After": "3"}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ProviderFailure()

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("quota errors must not sleep/retry"))
    with pytest.raises(retry.MistralProviderError) as error:
        retry.invoke_with_mistral_retry(model, "prompt")
    assert error.value.category == "quota"
    assert model.calls == 1


def test_mistral_does_not_retry_before_long_retry_after(monkeypatch):
    import core.mistral_retry as retry

    class ProviderFailure(Exception):
        status_code = 429
        body = {"message": "Rate limit exceeded"}
        response = type("Response", (), {"headers": {"Retry-After": "3600"}})()

    class Model:
        calls = 0

        def invoke(self, prompt):
            self.calls += 1
            raise ProviderFailure()

    model = Model()
    monkeypatch.setattr(retry.time, "sleep", lambda _: pytest.fail("long provider delay must be deferred"))
    with pytest.raises(retry.MistralProviderError) as error:
        retry.invoke_with_mistral_retry(model, "prompt")
    assert error.value.category == "rate_limit"
    assert model.calls == 1
