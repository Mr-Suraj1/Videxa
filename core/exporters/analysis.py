"""Markdown and JSON exports for Videxa's existing AI analysis fields."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Literal

from ._data import analysis_sections, exportable_analysis, require_report_mapping

AnalysisExportFormat = Literal["markdown", "json"]


def export_analysis(
    analysis: Mapping[str, Any], *, format: AnalysisExportFormat = "markdown"
) -> bytes:
    """Export current Videxa analysis fields as UTF-8 Markdown or JSON bytes.

    Runtime-only values such as a RAG chain and session identifier are never
    included, even when this function receives the full Streamlit result mapping.
    """
    require_report_mapping(analysis)
    if format == "json":
        return json.dumps(
            exportable_analysis(analysis), ensure_ascii=False, indent=2
        ).encode("utf-8")
    if format == "markdown":
        title = str(analysis.get("title") or "Videxa Analysis").strip()
        lines = [f"# {title}"]
        for heading, content in analysis_sections(analysis):
            lines.extend(("", f"## {heading}", "", content))
        return ("\n".join(lines).rstrip() + "\n").encode("utf-8")
    raise ValueError("format must be 'markdown' or 'json'.")
