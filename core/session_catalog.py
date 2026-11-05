"""Small persistent catalog for discovering processed video sessions."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _database_path() -> Path:
    configured = os.getenv("VIDEXA_SESSION_DB")
    return Path(configured) if configured else Path("vector_db") / "sessions.sqlite3"


def _connect() -> sqlite3.Connection:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS video_sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(video_sessions)")}
    migrations = {
        "transcript": "TEXT",
        "processing_status": "TEXT NOT NULL DEFAULT 'completed'",
        "analysis_status": "TEXT NOT NULL DEFAULT 'completed'",
        "analysis_error": "TEXT",
        "summary": "TEXT",
        "action_items": "TEXT",
        "key_decisions": "TEXT",
        "open_questions": "TEXT",
    }
    for column, definition in migrations.items():
        if column not in columns:
            connection.execute(f"ALTER TABLE video_sessions ADD COLUMN {column} {definition}")
    return connection


def save_session(session_id: str, title: str) -> None:
    """Persist a session label without retaining source URLs or transcripts."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id or ""):
        raise ValueError("A valid session ID is required.")
    normalized_title = (title or "Untitled video").strip()[:500] or "Untitled video"
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            """INSERT INTO video_sessions (session_id, title, created_at)
               VALUES (?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET title = excluded.title""",
            (session_id, normalized_title, created_at),
        )


def save_transcript(session_id: str, transcript: str) -> None:
    """Create/update a recoverable session as soon as transcription succeeds."""
    _validate_session_id(session_id)
    if not transcript or not transcript.strip():
        raise ValueError("A non-empty transcript is required.")
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute(
            """INSERT INTO video_sessions
                   (session_id, title, created_at, transcript, processing_status, analysis_status)
               VALUES (?, 'Analysis pending', ?, ?, 'completed', 'pending')
               ON CONFLICT(session_id) DO UPDATE SET
                   transcript = excluded.transcript,
                   processing_status = 'completed',
                   analysis_status = CASE WHEN video_sessions.analysis_status = 'completed'
                       THEN video_sessions.analysis_status ELSE 'pending' END,
                   analysis_error = NULL""",
            (session_id, now, transcript),
        )


def _validate_session_id(session_id: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", session_id or ""):
        raise ValueError("A valid session ID is required.")


def get_session(session_id: str) -> dict[str, Any] | None:
    _validate_session_id(session_id)
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM video_sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
    return dict(row) if row else None


def update_session_status(session_id: str, *, analysis_status: str, analysis_error: str | None = None) -> None:
    _validate_session_id(session_id)
    with _connect() as connection:
        cursor = connection.execute(
            """UPDATE video_sessions SET analysis_status = ?, analysis_error = ?
               WHERE session_id = ? AND transcript IS NOT NULL""",
            (analysis_status, analysis_error, session_id),
        )
        if cursor.rowcount == 0:
            raise KeyError("A saved transcript was not found for this session.")


def save_analysis(session_id: str, title: str, summary: str, action_items: str,
                  key_decisions: str, open_questions: str) -> None:
    _validate_session_id(session_id)
    with _connect() as connection:
        cursor = connection.execute(
            """UPDATE video_sessions SET title = ?, summary = ?, action_items = ?,
                   key_decisions = ?, open_questions = ?, analysis_status = 'completed',
                   analysis_error = NULL WHERE session_id = ? AND transcript IS NOT NULL""",
            (title[:500] or "Untitled video", summary, action_items, key_decisions,
             open_questions, session_id),
        )
        if cursor.rowcount == 0:
            raise KeyError("A saved transcript was not found for this session.")


def delete_session(session_id: str) -> bool:
    """Remove a session record. Returns True if a row was deleted."""
    _validate_session_id(session_id)
    with _connect() as connection:
        cursor = connection.execute(
            "DELETE FROM video_sessions WHERE session_id = ?", (session_id,)
        )
    return cursor.rowcount > 0


def list_sessions(limit: int = 500) -> list[dict[str, str]]:
    """Return recently processed session labels for the local user interface."""
    if not 1 <= limit <= 5000:
        raise ValueError("Session list limit must be between 1 and 5000.")
    with _connect() as connection:
        rows = connection.execute(
            """SELECT session_id, title, created_at, processing_status, analysis_status FROM video_sessions
               ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]
