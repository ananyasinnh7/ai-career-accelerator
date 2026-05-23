"""
app/api/routes/candidates.py
─────────────────────────────
Candidate-facing endpoints:

    GET  /candidates/me              → my profile
    PUT  /candidates/me              → update my profile
    GET  /candidates/me/history      → paginated scoring history
    GET  /candidates/me/history/{id} → single analysis detail
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.exceptions import InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.candidate import (
    AnalysisDetail,
    AnalysisSummary,
    CandidateProfileResponse,
    CandidateProfileUpdate,
    PaginatedHistory,
)
from app.services.candidate_service import (
    get_analysis_by_id,
    get_analysis_history,
    get_candidate_profile,
    update_candidate_profile,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])
logger = get_logger(__name__)

# Shorthand dependency — only candidates can access these routes
_candidate = Depends(require_role(UserRole.candidate))


# ── GET /candidates/me ─────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Get my candidate profile",
)
def get_my_profile(
    current_user: User = _candidate,
) -> CandidateProfileResponse:
    """Return the authenticated candidate's full profile."""
    try:
        user = get_candidate_profile(current_user)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return CandidateProfileResponse.model_validate(user)


# ── PUT /candidates/me ─────────────────────────────────────────────────────────

@router.put(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Update my candidate profile",
)
def update_my_profile(
    payload: CandidateProfileUpdate,
    current_user: User = _candidate,
    db: Session = Depends(get_db),
) -> CandidateProfileResponse:
    """
    Update one or more profile fields.
    Only provided fields are changed — omitted fields stay as-is.
    """
    try:
        user = update_candidate_profile(db, current_user, payload)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return CandidateProfileResponse.model_validate(user)


# ── GET /candidates/me/history ─────────────────────────────────────────────────

@router.get(
    "/me/history",
    response_model=PaginatedHistory,
    summary="Get my resume scoring history",
)
def get_my_history(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=10, ge=1, le=50, description="Results per page (max 50)"),
    current_user: User = _candidate,
    db: Session = Depends(get_db),
) -> PaginatedHistory:
    """
    Return a paginated list of all past resume analyses for the
    authenticated candidate, ordered by most recent first.
    """
    try:
        total, analyses = get_analysis_history(db, current_user, page, size)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return PaginatedHistory(
        total=total,
        page=page,
        size=size,
        results=[AnalysisSummary.model_validate(a) for a in analyses],
    )


# ── GET /candidates/me/history/{analysis_id} ───────────────────────────────────

@router.get(
    "/me/history/{analysis_id}",
    response_model=AnalysisDetail,
    summary="Get a single analysis in detail",
)
def get_analysis_detail(
    analysis_id: int,
    current_user: User = _candidate,
    db: Session = Depends(get_db),
) -> AnalysisDetail:
    """
    Return the full detail of a single past analysis including
    the original job description submitted.
    """
    try:
        analysis = get_analysis_by_id(db, current_user, analysis_id)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return AnalysisDetail.model_validate(analysis)