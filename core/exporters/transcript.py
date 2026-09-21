"""Plain-text transcript exports."""

from typing import Any

from ._data import ensure_text


def export_transcript(transcript: Any) -> bytes:
    """Return a UTF-8 text export for a transcript without writing to disk."""
    return ensure_text(transcript, field_name="transcript").encode("utf-8")
