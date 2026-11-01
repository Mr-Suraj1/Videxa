"""Application services that adapt Videxa core functionality for the API."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

from core.pipeline import analyze_saved_transcript, run_pipeline as run_core_pipeline
from core.rag_engine import ask_question, load_multi_session_rag_chain, load_rag_chain
from core.session_catalog import get_session

logger = logging.getLogger(__name__)
load_dotenv()


def run_pipeline(
    source: str,
    language: str = "english",
    on_step: Callable[[str, str], None] | None = None,
) -> dict[str, Any]:
    """Delegate to the single shared Videxa pipeline implementation."""
    return run_core_pipeline(source, language, on_step=on_step)


def answer_question(session_id: str, question: str) -> str:
    """Load the isolated transcript index and answer through the existing RAG engine."""
    return ask_question(load_rag_chain(session_id), question)


def retry_analysis(session_id: str) -> dict[str, Any]:
    """Re-run analysis on the persisted transcript for one existing session."""
    return analyze_saved_transcript(session_id)


def session_status(session_id: str) -> dict[str, Any] | None:
    """Return safe session metadata and statuses, excluding transcript contents."""
    session = get_session(session_id)
    if session is None:
        return None
    return {key: session[key] for key in (
        "session_id", "title", "created_at", "processing_status", "analysis_status", "analysis_error"
    )}


def answer_question_across_sessions(session_ids: list[str], question: str) -> str:
    """Answer a question using relevant context from several processed videos."""
    return ask_question(load_multi_session_rag_chain(session_ids), question)
