"""In-memory PDF reports for Videxa results."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ._data import analysis_sections, ensure_text, require_report_mapping


def _pdf_safe_text(value: Any, *, field_name: str) -> str:
    """Avoid font-encoding crashes when no Unicode TTF font is configured.

    Standard ReportLab fonts support a limited character set. This keeps report
    generation reliable while retaining text supported by Helvetica; the source
    transcript and Markdown/JSON exports always preserve full UTF-8 Unicode.
    """
    text = ensure_text(value, field_name=field_name)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def _page_number(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(letter[0] - 0.6 * inch, 0.4 * inch, f"Page {document.page}")
    canvas.restoreState()


def generate_pdf_report(report_data: Mapping[str, Any]) -> bytes:
    """Generate a professional Videxa report PDF in memory.

    Accepted data is a normal mapping such as the application's result payload.
    Missing optional analysis values are omitted, and no files are written.
    """
    data = require_report_mapping(report_data)
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.65 * inch,
        title=_pdf_safe_text(data.get("title") or "Videxa Report", field_name="title"),
        author="Videxa",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "VidexaTitle", parent=styles["Title"], alignment=TA_CENTER,
        textColor=colors.HexColor("#342F6B"), spaceAfter=16,
    )
    heading_style = ParagraphStyle(
        "VidexaHeading", parent=styles["Heading2"], textColor=colors.HexColor("#342F6B"),
        spaceBefore=12, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "VidexaBody", parent=styles["BodyText"], fontSize=9.5, leading=13,
        wordWrap="CJK", spaceAfter=6,
    )
    story = [_paragraph(_pdf_safe_text(data.get("title") or "Videxa Report", field_name="title"), title_style)]

    source = data.get("source") or data.get("source_url") or data.get("video_url")
    if source not in (None, ""):
        story.extend((_paragraph("Source", heading_style), _paragraph(_pdf_safe_text(source, field_name="source"), body_style)))

    for heading, content in analysis_sections(data):
        story.extend((_paragraph(heading, heading_style), _paragraph(_pdf_safe_text(content, field_name=heading), body_style)))

    transcript = _pdf_safe_text(data.get("transcript"), field_name="transcript").strip()
    if transcript:
        story.extend((Spacer(1, 4), _paragraph("Transcript", heading_style), _paragraph(transcript, body_style)))

    document.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return output.getvalue()
