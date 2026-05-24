"""
app/services/pdf_exporter.py
────────────────────────────
PDF generation service for resume + cover letter export.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib import colors

from app.core.logging import get_logger

logger = get_logger(__name__)


def export_pdf(
    resume_text: str,
    cover_letter_text: str,
    candidate_name: str,
    job_title: str = "Application",
) -> bytes:
    """
    Generate professional PDF with resume and cover letter.

    Args:
        resume_text: Resume content
        cover_letter_text: Cover letter content
        candidate_name: Candidate's name for filename
        job_title: Job title for document header

    Returns:
        PDF file as bytes

    Raises:
        Exception: PDF generation failed
    """
    logger.info("Generating PDF for %s (%s)", candidate_name, job_title)

    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=16,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#16213e"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=10,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4,
        leading=12,
    )

    # Build content
    story = []

    # Header with candidate name
    story.append(Paragraph(candidate_name, title_style))
    story.append(Paragraph(f"Application for {job_title}", body_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Cover Letter Section
    story.append(Paragraph("COVER LETTER", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    # Format cover letter with proper spacing
    for paragraph in cover_letter_text.split("\n\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
            story.append(Spacer(1, 0.05 * inch))

    # Page break
    story.append(PageBreak())

    # Resume Section
    story.append(Paragraph(f"{candidate_name} - RESUME", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    # Format resume with section recognition
    for line in resume_text.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.05 * inch))
            continue

        # Detect section headers (all caps or bold patterns)
        if line.isupper() and len(line) < 50 and any(c.isalpha() for c in line):
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(line, heading_style))
            story.append(Spacer(1, 0.05 * inch))
        else:
            story.append(Paragraph(line, body_style))

    # Build PDF
    try:
        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        logger.info("PDF generated successfully, size: %d bytes", len(pdf_bytes))
        return pdf_bytes
    except Exception as exc:
        logger.error("Failed to generate PDF: %s", exc)
        raise Exception(f"PDF generation failed: {exc}") from exc
