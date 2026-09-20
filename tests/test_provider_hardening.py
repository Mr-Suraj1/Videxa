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
    assert captured["max_retries"] == 2
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
