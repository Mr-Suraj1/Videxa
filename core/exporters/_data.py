"""Validation and formatting helpers shared by Videxa exporters."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

# A practical guardrail for in-memory exports. It still accommodates lengthy
# meeting transcripts while preventing unbounded user-controlled allocations.
MAX_EXPORT_TEXT_CHARACTERS = 2_000_000

ANALYSIS_FIELDS = (
    ("summary", "Summary"),
    ("action_items", "Action Items"),
    ("key_decisions", "Key Decisions"),
    ("open_questions", "Open Questions"),
)


class ExportValidationError(ValueError):
    """Raised when export input is not a supported, safe in-memory value."""


def ensure_text(value: Any, *, field_name: str = "text") -> str:
    """Convert supported plain Python values to readable text safely."""
    if value is None:
        return ""
    if isinstance(value, str):
        text = value
    elif isinstance(value, Mapping):
        text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        text = "\n".join(ensure_text(item, field_name=field_name) for item in value)
    else:
        text = str(value)

    if len(text) > MAX_EXPORT_TEXT_CHARACTERS:
        raise ExportValidationError(
            f"{field_name} exceeds the {MAX_EXPORT_TEXT_CHARACTERS:,}-character export limit."
        )
    return text


def require_report_mapping(report_data: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(report_data, Mapping):
        raise ExportValidationError("report_data must be a mapping of Videxa result fields.")
    return report_data


def exportable_analysis(report_data: Mapping[str, Any]) -> dict[str, Any]:
    """Return only user-facing analysis values, never runtime/session objects."""
    data = require_report_mapping(report_data)
    return {
        key: data[key]
        for key, _ in ANALYSIS_FIELDS
        if key in data and data[key] not in (None, "", [], ())
    }


def analysis_sections(report_data: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Build present, non-empty analysis sections in application display order."""
    data = require_report_mapping(report_data)
    sections: list[tuple[str, str]] = []
    for key, label in ANALYSIS_FIELDS:
        text = ensure_text(data.get(key), field_name=key).strip()
        if text:
            sections.append((label, text))
    return sections
