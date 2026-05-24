"""
app/api/routes/generation.py
────────────────────────────
Phase 3 generation endpoints: resume rewriting, cover letters, PDF export.
"""

import asyncio
from functools import partial

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.exceptions import GeminiAPIError, GeminiParseError
from app.core.logging import get_logger
from app.schemas.generation import (
    RewriteResumeRequest,
    RewriteResumeResponse,
    GenerateCoverLetterRequest,
    GenerateCoverLetterResponse,
    ExportPDFRequest,
    ExportPDFResponse,
)
from app.services.resume_rewriter import rewrite_resume
from app.services.cover_letter_generator import generate_cover_letter
from app.services.pdf_exporter import export_pdf

router = APIRouter(prefix="/api/v1", tags=["Generation"])
logger = get_logger(__name__)


@router.post(
    "/rewrite-resume",
    response_model=RewriteResumeResponse,
    status_code=status.HTTP_200_OK,
    summary="Rewrite resume to match job description",
    description="Use AI to rewrite resume bullets without fabricating experience.",
)
async def rewrite_resume_endpoint(request: RewriteResumeRequest) -> RewriteResumeResponse:
    """Rewrite resume bullets to better align with job description."""
    try:
        result = await asyncio.to_thread(
            partial(
                rewrite_resume,
                request.resume_text,
                request.job_description,
                request.missing_skills,
            )
        )
        return RewriteResumeResponse(**result)
    except GeminiAPIError as exc:
        logger.error("AI API error during resume rewriting: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {exc}",
        )
    except GeminiParseError as exc:
        logger.error("Parse error during resume rewriting: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response parse error: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during resume rewriting")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during resume rewriting",
        )


@router.post(
    "/generate-cover-letter",
    response_model=GenerateCoverLetterResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized cover letter",
    description="Auto-generate a tailored, non-generic cover letter.",
)
async def generate_cover_letter_endpoint(
    request: GenerateCoverLetterRequest,
) -> GenerateCoverLetterResponse:
    """Generate a personalized cover letter."""
    try:
        result = await asyncio.to_thread(
            partial(
                generate_cover_letter,
                request.candidate_name,
                request.company_name,
                request.job_title,
                request.resume_text,
                request.job_description,
                request.match_score,
            )
        )
        return GenerateCoverLetterResponse(**result)
    except GeminiAPIError as exc:
        logger.error("AI API error during cover letter generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI service error: {exc}",
        )
    except GeminiParseError as exc:
        logger.error("Parse error during cover letter generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response parse error: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during cover letter generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during cover letter generation",
        )


@router.post(
    "/export-pdf",
    response_class=FileResponse,
    status_code=status.HTTP_200_OK,
    summary="Export resume and cover letter as PDF",
    description="Download resume + cover letter combined into one professional PDF.",
)
async def export_pdf_endpoint(request: ExportPDFRequest) -> FileResponse:
    """Export resume + cover letter as PDF."""
    try:
        pdf_bytes = await asyncio.to_thread(
            partial(
                export_pdf,
                request.resume_text,
                request.cover_letter_text,
                request.candidate_name,
                request.job_title,
            )
        )

        filename = f"{request.candidate_name.replace(' ', '_')}_application.pdf"

        logger.info("PDF exported for %s, size: %d bytes", request.candidate_name, len(pdf_bytes))

        return FileResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            filename=filename,
        )
    except Exception as exc:
        logger.exception("Error exporting PDF: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF",
        )
