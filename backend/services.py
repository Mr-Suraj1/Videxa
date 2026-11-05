"""Application services that adapt Videxa core functionality for the API."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

from core.pipeline import analyze_saved_transcript, run_pipeline as run_core_pipeline
from core.rag_engine import ask_question, build_rag_chain, load_multi_session_rag_chain, load_rag_chain
from core.session_catalog import get_session, delete_session as catalog_delete_session, update_session_title as catalog_update_title
from core.vector_store import delete_vector_store
from core.vector_store import VectorStoreUnavailableError

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
    """Load or recover the isolated transcript index and answer through RAG."""
    try:
        rag_chain = load_rag_chain(session_id)
    except VectorStoreUnavailableError:
        # Analysis can fail before its normal RAG-indexing step. The transcript
        # is already persisted, so recover the index from that session only.
        session = get_session(session_id)
        transcript = session.get("transcript") if session else None
        if not transcript:
            raise
        rag_chain = build_rag_chain(
            transcript,
            session_id=session_id,
            session_title=session.get("title"),
        )
    return ask_question(rag_chain, question)


def retry_analysis(session_id: str) -> dict[str, Any]:
    """Re-run analysis on the persisted transcript for one existing session."""
    return analyze_saved_transcript(session_id)


def delete_session(session_id: str) -> bool:
    """Remove a session from the catalog and delete its vector store."""
    deleted = catalog_delete_session(session_id)
    if deleted:
        delete_vector_store(session_id)
    return deleted


def update_session_title(session_id: str, title: str) -> bool:
    """Update the display title for a session."""
    return catalog_update_title(session_id, title)


def session_status(session_id: str) -> dict[str, Any] | None:
    """Return safe session metadata and statuses, excluding transcript contents."""
    session = get_session(session_id)
    if session is None:
        return None
    return {key: session[key] for key in (
        "session_id", "title", "created_at", "processing_status", "analysis_status", "analysis_error"
    )}


def session_content(session_id: str) -> dict[str, Any] | None:
    """Return persisted transcript and completed analysis for one session."""
    session = get_session(session_id)
    if session is None or not session.get("transcript"):
        return None
    analysis_fields = ("summary", "action_items", "key_decisions", "open_questions")
    analysis = None
    if session.get("analysis_status") == "completed" and all(session.get(field) is not None for field in analysis_fields):
        analysis = {
            "title": session["title"],
            "summary": session["summary"],
            "action_items": session["action_items"],
            "key_decisions": session["key_decisions"],
            "open_questions": session["open_questions"],
        }
    return {
        "session_id": session_id,
        "title": session["title"],
        "transcript": session["transcript"],
        "analysis": analysis,
    }


def answer_question_across_sessions(session_ids: list[str], question: str) -> str:
    """Answer a question using relevant context from several processed videos."""
    return ask_question(load_multi_session_rag_chain(session_ids), question)
