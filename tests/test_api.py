"""API boundary tests with external Videxa providers replaced by test doubles."""

from fastapi.testclient import TestClient
import pytest

from backend.app import app
from backend import services
from core.pipeline import AnalysisFailure
from core.gemini_retry import GeminiProviderError


client = TestClient(app)


def test_health_and_openapi_are_available():
    assert client.get("/health").json() == {"status": "ok"}
    openapi = client.get("/openapi.json").json()
    assert "/process" in openapi["paths"]
    assert "/chat" in openapi["paths"]
    assert "/exports/pdf" in openapi["paths"]
    assert "/sessions/{session_id}/analysis/retry" in openapi["paths"]
    assert "/sessions/{session_id}/content" in openapi["paths"]


def test_process_validates_request():
    response = client.post("/process", json={"source": "   "})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request data."}


def test_process_returns_serializable_analysis(monkeypatch):
    calls = []

    def fake_service(source, language):
        calls.append((source, language))
        return {
            "session_id": "session-123",
            "transcript": "Meeting transcript.",
            "title": "Planning",
            "summary": "A summary.",
            "action_items": "1. Ship release",
            "key_decisions": "1. Release Friday",
            "open_questions": "No open questions found.",
            "rag_chain": object(),
        }

    monkeypatch.setattr(
        services,
        "run_pipeline",
        fake_service,
    )
    response = client.post(
        "/process",
        json={"source": "  https://youtu.be/abc123  ", "language": "hinglish"},
    )
    assert response.status_code == 200
    assert calls == [("https://youtu.be/abc123", "hinglish")]
    assert response.json() == {
        "status": "completed",
        "session_id": "session-123",
        "transcript": "Meeting transcript.",
        "analysis": {
            "title": "Planning",
            "summary": "A summary.",
            "action_items": "1. Ship release",
            "key_decisions": "1. Release Friday",
            "open_questions": "No open questions found.",
        },
    }


def test_process_hides_unexpected_errors(monkeypatch):
    def fail(source, language):
        raise RuntimeError("secret path and provider key")

    monkeypatch.setattr(services, "run_pipeline", fail)
    response = client.post("/process", json={"source": "https://youtu.be/abc123"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Analysis could not be completed."}


def test_process_preserves_session_id_when_analysis_fails(monkeypatch):
    cause = GeminiProviderError("Gemini API is temporarily rate limited. Wait for the limit to reset, then retry.", category="rate_limit", status_code=429)
    monkeypatch.setattr(services, "run_pipeline", lambda *_: (_ for _ in ()).throw(AnalysisFailure("saved-session", cause)))
    response = client.post("/process", json={"source": "https://youtu.be/abc123"})
    assert response.status_code == 429
    assert response.json() == {
        "detail": "Gemini API is temporarily rate limited. Wait for the limit to reset, then retry.",
        "session_id": "saved-session",
        "processing_status": "completed",
        "analysis_status": "rate_limited",
    }


def test_retry_analysis_route_uses_existing_session_id(monkeypatch):
    calls = []
    monkeypatch.setattr(services, "retry_analysis", lambda session_id: calls.append(session_id) or {
        "session_id": session_id, "transcript": "Saved", "title": "Title", "summary": "Summary",
        "action_items": "Actions", "key_decisions": "Decisions", "open_questions": "Questions",
    })
    response = client.post("/sessions/recover-me/analysis/retry")
    assert response.status_code == 200
    assert response.json()["session_id"] == "recover-me"
    assert calls == ["recover-me"]


@pytest.mark.parametrize(
    ("analysis_status", "has_analysis"),
    [("completed", True), ("pending", False), ("failed", False)],
)
def test_session_content_returns_saved_data_for_session_states(monkeypatch, analysis_status, has_analysis):
    session = {
        "session_id": "recover-me",
        "title": "Planning",
        "transcript": "Saved transcript.",
        "analysis_status": analysis_status,
        "summary": "Summary" if has_analysis else None,
        "action_items": "Actions" if has_analysis else None,
        "key_decisions": "Decisions" if has_analysis else None,
        "open_questions": "Questions" if has_analysis else None,
    }
    monkeypatch.setattr(services, "get_session", lambda _session_id: session)
    response = client.get("/sessions/recover-me/content")
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "recover-me"
    assert payload["transcript"] == "Saved transcript."
    assert (payload["analysis"] is not None) is has_analysis


def test_session_content_service_includes_analysis_only_when_completed(monkeypatch):
    monkeypatch.setattr(services, "get_session", lambda session_id: {
        "session_id": session_id,
        "title": "Planning",
        "transcript": "Saved transcript.",
        "analysis_status": "completed",
        "summary": "Summary",
        "action_items": "Actions",
        "key_decisions": "Decisions",
        "open_questions": "Questions",
    })
    assert services.session_content("recover-me") == {
        "session_id": "recover-me",
        "title": "Planning",
        "transcript": "Saved transcript.",
        "analysis": {
            "title": "Planning",
            "summary": "Summary",
            "action_items": "Actions",
            "key_decisions": "Decisions",
            "open_questions": "Questions",
        },
    }


def test_session_content_returns_not_found_without_saved_transcript(monkeypatch):
    monkeypatch.setattr(services, "get_session", lambda _session_id: None)
    response = client.get("/sessions/old-session/content")
    assert response.status_code == 404
    assert response.json() == {"detail": "Saved transcript content was not found for this session."}


def test_chat_uses_existing_rag_service(monkeypatch):
    calls = []
    monkeypatch.setattr(
        services,
        "answer_question",
        lambda session_id, question: calls.append((session_id, question)) or "Answer",
    )
    response = client.post(
        "/chat",
        json={"session_id": "session-123", "question": "What happened?"},
    )
    assert response.status_code == 200
    assert response.json() == {"session_id": "session-123", "answer": "Answer"}
    assert calls == [("session-123", "What happened?")]


def test_exports_use_real_export_services():
    response = client.post(
        "/exports/transcript",
        json={"transcript": "Namaste team"},
    )
    assert response.status_code == 200
    assert response.content.decode("utf-8") == "Namaste team"
    assert response.headers["content-type"].startswith("text/plain")

    response = client.post(
        "/exports/analysis",
        json={"summary": "A summary.", "action_items": ["Ship release"]},
    )
    assert response.status_code == 200
    assert b"# Videxa Analysis" in response.content

    response = client.post(
        "/exports/pdf",
        json={"title": "Planning", "summary": "A summary."},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-")


def test_export_validation_errors_are_safe():
    response = client.post("/exports/transcript", json={})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request data."}

    response = client.post("/exports/transcript", json={"transcript": "   "})
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request data."}

    response = client.post("/chat", json={"session_id": "bad id", "question": "Hi"})
    assert response.status_code == 422
