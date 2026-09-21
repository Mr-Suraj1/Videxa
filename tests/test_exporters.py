"""Offline tests for reusable, frontend-agnostic Videxa export services."""

import json

import pytest

from core.exporters import export_analysis, export_transcript, generate_pdf_report
from core.exporters._data import ExportValidationError, MAX_EXPORT_TEXT_CHARACTERS


def test_transcript_export_is_utf8_and_preserves_hinglish():
    transcript = "Namaste team, kal deployment hai - let's ship it."
    assert export_transcript(transcript).decode("utf-8") == transcript


def test_transcript_export_handles_empty_and_long_text():
    assert export_transcript("") == b""
    transcript = "meeting notes " * 20_000
    assert export_transcript(transcript).decode("utf-8") == transcript


def test_transcript_export_rejects_unbounded_input():
    with pytest.raises(ExportValidationError):
        export_transcript("x" * (MAX_EXPORT_TEXT_CHARACTERS + 1))


def test_analysis_markdown_exports_existing_complete_fields():
    payload = {
        "title": "Sprint Review",
        "summary": "The team reviewed progress.",
        "action_items": ["Ship release", "Update notes"],
        "key_decisions": "Deploy on Friday.",
        "open_questions": "Who owns support?",
        "session_id": "not-for-export",
        "rag_chain": object(),
    }
    text = export_analysis(payload).decode("utf-8")
    assert "# Sprint Review" in text
    assert "## Action Items" in text
    assert "Ship release" in text
    assert "not-for-export" not in text


def test_analysis_export_handles_missing_empty_and_unicode_sections():
    payload = {"summary": "", "action_items": ["कल follow-up करना है"], "open_questions": None}
    assert "कल follow-up करना है" in export_analysis(payload).decode("utf-8")
    assert json.loads(export_analysis(payload, format="json")) == {"action_items": ["कल follow-up करना है"]}
    assert export_analysis({}).decode("utf-8") == "# Videxa Analysis\n"


def test_analysis_rejects_unknown_format():
    with pytest.raises(ValueError):
        export_analysis({}, format="txt")


def test_pdf_report_is_valid_and_contains_basic_content():
    pdf = generate_pdf_report({"title": "Planning", "summary": "Roadmap reviewed.", "transcript": "Hello team."})
    assert pdf.startswith(b"%PDF-")
    assert b"Planning" in pdf


@pytest.mark.parametrize("payload", [
    {},
    {"transcript": "word " * 30_000},
    {"summary": "नमस्ते team - action item तय हुआ"},
])
def test_pdf_handles_missing_long_and_unicode_content(payload):
    assert generate_pdf_report(payload).startswith(b"%PDF-")


def test_export_modules_do_not_depend_on_streamlit():
    import ast
    from pathlib import Path

    exporters_dir = Path(__file__).parents[1] / "core" / "exporters"
    imported_modules = []
    for path in exporters_dir.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
    assert not any(module == "streamlit" or module.startswith("streamlit.") for module in imported_modules)
