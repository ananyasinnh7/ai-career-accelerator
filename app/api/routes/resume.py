"""
app/api/routes/resume.py
─────────────────────────
Route handler for POST /api/v1/score-resume.

Flow
────
1.  Validate file type and read bytes.
2.  Extract text from PDF (runs in thread pool).
3.  Call Gemini for evaluation (runs in thread pool).
4.  Persist the result — linked to the user if authenticated.
5.  Return the structured JSON response.

Authentication is OPTIONAL on this endpoint:
  - Authenticated candidates → analysis saved under their account.
  - Anonymous requests       → analysis saved with user_id=None (Phase 1 compat).
"""

import asyncio
from functools import partial
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    EmptyPDFError,
    GeminiAPIError,
    GeminiParseError,
    InvalidTokenError,
    PDFExtractionError,
    PDFTooLargeError,
)
from app.core.logging import get_logger
from app.db.models import ResumeAnalysis, User
from app.db.session import get_db
from app.schemas.resume import ResumeScoreResponse
from app.services.auth_service import decode_access_token, get_user_by_id
from app.services.gemini_service import score_resume
from app.services.pdf_service import extract_text_from_pdf

router   = APIRouter(prefix="/api/v1", tags=["Resume Scoring"])
logger   = get_logger(__name__)
settings = get_settings()

_bearer = HTTPBearer(auto_error=False)

_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}


def _get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Attempt to resolve the current user from the Bearer token.
    Returns None (without raising) if no token is provided or it is invalid.
    This keeps the endpoint usable anonymously.
    """
    if not credentials:
        return None
    try:
        payload = decode_access_token(credentials.credentials)
        return get_user_by_id(db, int(payload["sub"]))
    except (InvalidTokenError, Exception):
        return None


@router.post(
    "/score-resume",
    response_model=ResumeScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Score a resume against a job description",
    description=(
        "Upload a PDF resume and provide a job description. "
        "Authenticated candidates have the result saved to their history. "
        "Anonymous use is still supported."
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
    current_user: Optional[User] = Depends(_get_optional_user),
) -> ResumeScoreResponse:
    """
    Evaluate how well a candidate's resume matches the target job description.
    """
    # ── 1. File validation ─────────────────────────────────────────────────────
    if resume.content_type not in _ALLOWED_CONTENT_TYPES and not (
        resume.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Received: {resume.content_type}",
        )

    file_bytes = await resume.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    logger.info(
        "Resume scoring request — file='%s' size=%d user=%s",
        resume.filename,
        len(file_bytes),
        current_user.email if current_user else "anonymous",
    )

    # ── 2. PDF text extraction ─────────────────────────────────────────────────
    try:
        resume_text: str = await asyncio.to_thread(extract_text_from_pdf, file_bytes)
    except PDFTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except (EmptyPDFError, PDFExtractionError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # ── 3. Gemini evaluation ───────────────────────────────────────────────────
    try:
        result: ResumeScoreResponse = await asyncio.to_thread(
            partial(score_resume, resume_text, job_description)
        )
    except GeminiAPIError as exc:
        logger.error("Gemini API error: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI service error: {exc}")
    except GeminiParseError as exc:
        logger.error("Gemini parse error: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI response parse error: {exc}")

    # ── 4. Persist — link to user if authenticated ─────────────────────────────
    try:
        analysis = ResumeAnalysis(
            user_id=current_user.id if current_user else None,
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
        logger.info(
            "Persisted ResumeAnalysis id=%d score=%d user_id=%s",
            analysis.id,
            analysis.score,
            current_user.id if current_user else "anonymous",
        )
    except Exception as exc:
        logger.error("Failed to persist analysis: %s", exc)
        db.rollback()

    # ── 5. Return response ─────────────────────────────────────────────────────
    return result