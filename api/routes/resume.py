"""
app/api/routes/resume.py
─────────────────────────
Route handler for POST /score-resume.

Flow
────
1.  Validate file type and read bytes.
2.  Extract text from PDF (runs in thread pool — pdfplumber is CPU-bound).
3.  Call Gemini for evaluation (runs in thread pool — network I/O).
4.  Persist the result to PostgreSQL.
5.  Return the structured JSON response.
"""

import asyncio
from functools import partial

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyPDFError,
    GeminiAPIError,
    GeminiParseError,
    PDFExtractionError,
    PDFTooLargeError,
)
from app.core.logging import get_logger
from app.db.models import ResumeAnalysis
from app.db.session import get_db
from app.schemas.resume import ResumeScoreResponse
from app.services.gemini_service import score_resume
from app.services.pdf_service import extract_text_from_pdf
from app.workers.tasks import score_resume_task

router = APIRouter(prefix="/api/v1", tags=["Resume Scoring"])
logger = get_logger(__name__)
settings = get_settings()

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",  # some browsers use this for PDF
}


@router.post(
    "/score-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score a resume against a job description",
    description=(
        "Upload a PDF resume and provide a job description. "
        "Returns an AI-generated match score, missing skills, and a recommended project."
    ),
)
async def score_resume_endpoint(
    resume: UploadFile = File(..., description="Candidate's resume in PDF format."),
    job_description: str = Form(
        ...,
        min_length=50,
        description="Full text of the target job description (min 50 characters).",
    ),
    db: Session = Depends(get_db),
) -> ResumeScoreResponse:
    """
    Evaluate how well a candidate's resume matches the target job description.
    """
    # ── 1. Basic file validation ───────────────────────────────────────────────
    if resume.content_type not in _ALLOWED_CONTENT_TYPES and not (
        resume.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Received content-type: {resume.content_type}",
        )

    file_bytes = await resume.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    logger.info(
        "Received resume '%s' (%d bytes) for scoring",
        resume.filename,
        len(file_bytes),
    )

    # ── 2. PDF text extraction (offloaded to thread pool) ─────────────────────
    try:
        resume_text: str = await asyncio.to_thread(
            extract_text_from_pdf, file_bytes
        )
    except PDFTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except EmptyPDFError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PDFExtractionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # ── 3. Gemini evaluation (offloaded to thread pool) ───────────────────────
    try:
        result: ResumeScoreResponse = await asyncio.to_thread(
            partial(score_resume, resume_text, job_description)
        )
    except GeminiAPIError as exc:
        logger.error("Gemini API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI evaluation service error: {exc}",
        )
    except GeminiParseError as exc:
        logger.error("Gemini parse error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response could not be parsed: {exc}",
        )

    # ── 4. Persist to database ─────────────────────────────────────────────────
    try:
        analysis = ResumeAnalysis(
            original_filename=resume.filename,
            resume_text=resume_text,
            job_description=job_description,
            score=result.score,
            missing_skills=result.missing_skills,
            recommended_project=result.recommended_project,
            summary=result.summary,
            gemini_model=settings.gemini_model,
        )
        db.add(analysis)
        db.commit()
        logger.info("Persisted ResumeAnalysis id=%d score=%d", analysis.id, analysis.score)
    except Exception as exc:
        # Non-fatal: log and continue — the response is still returned to the client
        logger.error("Failed to persist analysis to DB: %s", exc)
        db.rollback()

    # ── 5. Return structured response ─────────────────────────────────────────
    return result
