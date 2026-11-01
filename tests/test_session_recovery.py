"""Transcript persistence and retry coverage without media/provider calls."""

import sqlite3

import pytest

import core.pipeline as pipeline
import core.session_catalog as catalog


def test_existing_sqlite_sessions_survive_backward_compatible_migration(monkeypatch, tmp_path):
    database = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE video_sessions (session_id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO video_sessions VALUES (?, ?, ?)",
            ("old-session", "Old title", "2026-01-01T00:00:00+00:00"),
        )
    monkeypatch.setenv("VIDEXA_SESSION_DB", str(database))

    session = catalog.get_session("old-session")
    assert session["title"] == "Old title"
    assert session["transcript"] is None
    assert session["processing_status"] == "completed"
    assert session["analysis_status"] == "completed"
    assert catalog.list_sessions()[0]["session_id"] == "old-session"


def test_transcript_is_saved_before_title_generation_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEXA_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    monkeypatch.setattr(pipeline, "process_input", lambda source: ["audio.wav"])
    monkeypatch.setattr(pipeline, "transcribe_all", lambda chunks, language: "Retained transcript")
    monkeypatch.setattr(pipeline, "cleanup_audio_files", lambda chunks: None)

    # Inspect SQLite directly at the moment the first AI operation starts.
    def assert_saved_then_fail(transcript):
        sessions = catalog.list_sessions()
        assert len(sessions) == 1
        session = catalog.get_session(sessions[0]["session_id"])
        assert session["transcript"] == "Retained transcript"
        assert session["processing_status"] == "completed"
        raise RuntimeError("provider outage")

    monkeypatch.setattr(pipeline, "generate_title", assert_saved_then_fail)
    with pytest.raises(pipeline.AnalysisFailure) as failure:
        pipeline.run_pipeline("https://youtu.be/example")
    assert catalog.get_session(failure.value.session_id)["analysis_status"] == "failed"


def test_analysis_retry_uses_saved_transcript_without_media_calls(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEXA_SESSION_DB", str(tmp_path / "sessions.sqlite3"))
    catalog.save_transcript("retry-session", "Transcript that should be reused")
    calls = []
    monkeypatch.setattr(pipeline, "process_input", lambda *_: pytest.fail("download must not run"))
    monkeypatch.setattr(pipeline, "transcribe_all", lambda *_: pytest.fail("transcription must not run"))
    monkeypatch.setattr(pipeline, "generate_title", lambda text: calls.append(("title", text)) or "Recovered title")
    monkeypatch.setattr(pipeline, "summarize", lambda text: calls.append(("summary", text)) or "Summary")
    monkeypatch.setattr(pipeline, "extract_action_items", lambda text: "Actions")
    monkeypatch.setattr(pipeline, "extract_key_decisions", lambda text: "Decisions")
    monkeypatch.setattr(pipeline, "extract_questions", lambda text: "Questions")
    monkeypatch.setattr(pipeline, "build_rag_chain", lambda *args, **kwargs: "rag")

    result = pipeline.analyze_saved_transcript("retry-session")
    assert result["session_id"] == "retry-session"
    assert result["transcript"] == "Transcript that should be reused"
    assert calls == [("title", "Transcript that should be reused"),
                     ("summary", "Transcript that should be reused")]
    saved = catalog.get_session("retry-session")
    assert saved["analysis_status"] == "completed"
    assert saved["title"] == "Recovered title"
    assert saved["summary"] == "Summary"
