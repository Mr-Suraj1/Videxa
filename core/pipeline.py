"""Shared Videxa processing pipeline orchestration."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

from core.extractor import (
    extract_action_items,
    extract_key_decisions,
    extract_questions,
)
from core.rag_engine import build_rag_chain
from core.session_catalog import (
    get_session, save_analysis, save_transcript, update_session_status,
)
from core.summarizer import generate_title, summarize
from core.transcriber import transcribe_all
from utils.audio_processor import cleanup_audio_files, process_input, validate_input


class AnalysisFailure(RuntimeError):
    """Analysis failed after a recoverable transcript was saved."""

    def __init__(self, session_id: str, cause: Exception):
        super().__init__("Transcript saved; analysis did not complete. Retry analysis using the session ID.")
        self.session_id = session_id
        self.cause = cause
        self.category = getattr(cause, "category", None)


def analyze_saved_transcript(session_id: str, on_step: Callable[[str, str], None] | None = None) -> dict[str, Any]:
    """Run AI analysis on a persisted transcript without media processing."""
    session = get_session(session_id)
    if session is None or not session.get("transcript"):
        raise KeyError("A saved transcript was not found for this session.")
    transcript = session["transcript"]
    def update(step: str, state: str) -> None:
        if on_step is not None:
            on_step(step, state)

    update_session_status(session_id, analysis_status="processing")
    try:
        update("title", "active")
        title = generate_title(transcript)
        update("title", "done")
        time.sleep(4)
        update("summary", "active")
        summary = summarize(transcript)
        update("summary", "done")
        time.sleep(4)
        update("extract", "active")
        action_items = extract_action_items(transcript)
        time.sleep(4)
        key_decisions = extract_key_decisions(transcript)
        time.sleep(4)
        open_questions = extract_questions(transcript)
        update("extract", "done")

        # Upsert stable document IDs into the existing session collection.
        update("rag", "active")
        rag_chain = build_rag_chain(transcript, session_id=session_id, session_title=title)
        save_analysis(session_id, title, summary, action_items, key_decisions, open_questions)
        update("rag", "done")
    except Exception as exc:
        category = getattr(exc, "category", None)
        status = "quota" if category == "quota" else "rate_limited" if category == "rate_limit" else "failed"
        logger.exception("Videxa analysis failed for session %s (category=%s)", session_id, category)
        # Store a safe, actionable message, never raw provider details or credentials.
        safe_error = str(exc) if category in {"quota", "rate_limit"} else "Analysis failed. Retry analysis for this saved transcript."
        update_session_status(session_id, analysis_status=status, analysis_error=safe_error)
        raise AnalysisFailure(session_id, exc) from exc

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": key_decisions,
        "open_questions": open_questions,
        "rag_chain": rag_chain,
        "session_id": session_id,
    }


def run_pipeline(
    source: str,
    language: str = "english",
    on_step: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Run the existing Videxa processing pipeline and retain its RAG session."""
    def update(step: str, state: str) -> None:
        if on_step is not None:
            on_step(step, state)

    validate_input(source)
    chunks: list[str] = []
    try:
        update("audio", "active")
        chunks = process_input(source)
        update("audio", "done")
        update("transcript", "active")
        transcript = transcribe_all(chunks, language)
        session_id = uuid.uuid4().hex
        save_transcript(session_id, transcript)
        update("transcript", "done")
        return analyze_saved_transcript(session_id, on_step=on_step)
    finally:
        cleanup_audio_files(chunks)
