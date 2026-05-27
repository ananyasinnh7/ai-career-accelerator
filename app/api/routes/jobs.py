"""
app/api/routes/jobs.py
───────────────────────
Job posting endpoints:

    POST   /jobs                      → recruiter creates a job
    GET    /jobs                      → anyone browses active jobs
    GET    /jobs/mine                 → recruiter sees their own jobs
    GET    /jobs/{id}                 → single job detail
    PUT    /jobs/{id}                 → recruiter updates their job
    DELETE /jobs/{id}                 → recruiter closes their job
    POST   /jobs/{id}/match-me        → candidate matches themselves to a job
    GET    /jobs/{id}/candidates      → recruiter sees ranked candidate list
    PUT    /jobs/{id}/matches/{mid}   → recruiter updates a match status
    GET    /jobs/{id}/auto-matches    → recruiter sees auto-matched candidates (STEP 6)
    GET    /jobs/{id}/auto-matches-stats → auto-match statistics (STEP 6)
"""

import asyncio
from functools import partial
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.exceptions import GeminiAPIError, GeminiParseError, InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import JobStatus, User, UserRole
from app.db.session import get_db
from app.schemas.jobs import (
    JobPostingCreate,
    JobPostingResponse,
    JobPostingSummary,
    JobPostingUpdate,
    PaginatedJobs,
)
from app.schemas.match import (
    MatchResponse,
    MatchStatusUpdate,
    MatchWithCandidateResponse,
    MatchWithJobResponse,
    PaginatedMatches,
)
from app.schemas.resume_version import AutoMatchResponse, AutoMatchListResponse
from app.services.job_service import (
    create_job,
    delete_job,
    get_job_by_id,
    get_jobs,
    get_recruiter_jobs,
    update_job,
)
from app.services.match_service import (
    get_candidate_matches,
    get_job_matches,
    match_candidate_to_job,
    update_match_status,
)
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger(__name__)

_recruiter = Depends(require_role(UserRole.recruiter))
_candidate = Depends(require_role(UserRole.candidate))


# ── POST /jobs ──────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=JobPostingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job posting (recruiter only)",
)
def create_job_posting(
    payload: JobPostingCreate,
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> JobPostingResponse:
    """Create a new job posting and trigger auto-matching (STEP 6)."""
    job = create_job(db, recruiter, payload)
    
    # Trigger auto-match (STEP 6)
    try:
        MatchingService.trigger_auto_match(db, job.id)
        logger.info(f"Auto-match triggered for job {job.id}")
    except Exception as exc:
        logger.warning(f"Auto-match failed for job {job.id}: {exc}")
        # Don't fail the request, just log the error
    
    return JobPostingResponse.model_validate(job)


# ── GET /jobs ───────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedJobs,
    summary="Browse all active job postings (public)",
)
def list_jobs(
    page:   int            = Query(default=1,  ge=1),
    size:   int            = Query(default=10, ge=1, le=50),
    search: Optional[str]  = Query(default=None, description="Search title, company, or description"),
    db:     Session        = Depends(get_db),
) -> PaginatedJobs:
    total, jobs = get_jobs(db, page, size, JobStatus.active, search)
    return PaginatedJobs(
        total=total, page=page, size=size,
        results=[JobPostingSummary.model_validate(j) for j in jobs],
    )


# ── GET /jobs/mine ─────────────────────────────────────────────────────────

@router.get(
    "/mine",
    response_model=PaginatedJobs,
    summary="Get my job postings (recruiter only)",
)
def list_my_jobs(
    page:     int     = Query(default=1,  ge=1),
    size:     int     = Query(default=10, ge=1, le=50),
    recruiter: User   = _recruiter,
    db:       Session = Depends(get_db),
) -> PaginatedJobs:
    total, jobs = get_recruiter_jobs(db, recruiter, page, size)
    return PaginatedJobs(
        total=total, page=page, size=size,
        results=[JobPostingSummary.model_validate(j) for j in jobs],
    )


# ── GET /jobs/{id} ─────────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    response_model=JobPostingResponse,
    summary="Get a single job posting",
)
def get_job(
    job_id: int,
    db:     Session = Depends(get_db),
) -> JobPostingResponse:
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found.")
    return JobPostingResponse.model_validate(job)


# ── PUT /jobs/{id} ─────────────────────────────────────────────────────────

@router.put(
    "/{job_id}",
    response_model=JobPostingResponse,
    summary="Update a job posting (recruiter only)",
)
def update_job_posting(
    job_id:    int,
    payload:   JobPostingUpdate,
    recruiter: User    = _recruiter,
    db:        Session = Depends(get_db),
) -> JobPostingResponse:
    try:
        job = update_job(db, recruiter, job_id, payload)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return JobPostingResponse.model_validate(job)


# ── DELETE /jobs/{id} ────────────────────────────────────────────────────────

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Close a job posting (recruiter only)",
)
def close_job_posting(
    job_id:    int,
    recruiter: User    = _recruiter,
    db:        Session = Depends(get_db),
) -> dict:
    try:
        delete_job(db, recruiter, job_id)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return {"message": f"Job {job_id} has been closed successfully."}


# ── POST /jobs/{id}/match-me ────────────────────────────────────────────────

@router.post(
    "/{job_id}/match-me",
    response_model=MatchWithJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Match my resume to a job (candidate only)",
)
async def match_me_to_job(
    job_id:    int,
    candidate: User    = _candidate,
    db:        Session = Depends(get_db),
) -> MatchWithJobResponse:
    """
    Score the candidate's latest resume against this job using AI.
    Returns the match score, missing skills, and a recommended project.
    If already matched, returns the existing match.
    """
    try:
        match = await asyncio.to_thread(
            partial(match_candidate_to_job, db, candidate, job_id)
        )
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except (GeminiAPIError, GeminiParseError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return MatchWithJobResponse(
        id=match.id,
        candidate_id=match.candidate_id,
        job_id=match.job_id,
        score=match.score,
        missing_skills=match.missing_skills,
        recommended_project=match.recommended_project,
        summary=match.summary,
        status=match.status,
        recruiter_notes=match.recruiter_notes,
        created_at=match.created_at,
        job_title=match.job.title,
        job_company=match.job.company,
        job_location=match.job.location,
    )


# ── GET /jobs/{id}/candidates ──────────────────────────────────────────────

@router.get(
    "/{job_id}/candidates",
    response_model=PaginatedMatches,
    summary="Get ranked candidates for a job (recruiter only)",
)
def get_job_candidates(
    job_id:    int,
    page:      int     = Query(default=1,  ge=1),
    size:      int     = Query(default=10, ge=1, le=50),
    recruiter: User    = _recruiter,
    db:        Session = Depends(get_db),
) -> PaginatedMatches:
    try:
        total, matches = get_job_matches(db, recruiter, job_id, page, size)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return PaginatedMatches(
        total=total, page=page, size=size,
        results=[MatchResponse.model_validate(m) for m in matches],
    )


# ── PUT /jobs/{id}/matches/{mid} ───────────────────────────────────────────

@router.put(
    "/{job_id}/matches/{match_id}",
    response_model=MatchResponse,
    summary="Update match status (recruiter only) — shortlist or reject",
)
def update_candidate_match_status(
    job_id:    int,
    match_id:  int,
    payload:   MatchStatusUpdate,
    recruiter: User    = _recruiter,
    db:        Session = Depends(get_db),
) -> MatchResponse:
    try:
        match = update_match_status(db, recruiter, match_id, payload)
    except InsufficientPermissionsError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return MatchResponse.model_validate(match)


# ── GET /jobs/matches/mine ────────────────────────────────────────────────

@router.get(
    "/matches/mine",
    response_model=PaginatedMatches,
    summary="Get all my job matches (candidate only)",
)
def get_my_matches(
    page:      int     = Query(default=1,  ge=1),
    size:      int     = Query(default=10, ge=1, le=50),
    candidate: User    = _candidate,
    db:        Session = Depends(get_db),
) -> PaginatedMatches:
    total, matches = get_candidate_matches(db, candidate, page, size)
    return PaginatedMatches(
        total=total, page=page, size=size,
        results=[MatchResponse.model_validate(m) for m in matches],
    )


# ── GET /jobs/{id}/auto-matches ────────────────────────────────────────────
# STEP 6: Advanced Matching Engine

@router.get(
    "/{job_id}/auto-matches",
    response_model=dict,
    summary="Get auto-matched candidates (recruiter only) — STEP 6",
    description="Get all candidates that were auto-matched when this job was posted.",
)
def get_job_auto_matches(
    job_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get auto-matched candidates for a job with pagination.

    **Requirements:**
    - User must be authenticated and be a recruiter
    - User must own the job

    Returns paginated list of auto-matched candidates with scores.
    """
    # Check if recruiter owns the job
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view auto-matches for your own jobs"
        )

    # Get auto-matches
    matches, total = MatchingService.get_job_auto_matches(db, job_id, skip=(page - 1) * size, limit=size)

    # Enrich with candidate info
    results = []
    for match in matches:
        candidate = db.query(User).filter_by(id=match.candidate_id).first()
        results.append({
            "id": match.id,
            "job_id": match.job_id,
            "candidate_id": match.candidate_id,
            "candidate_email": candidate.email if candidate else None,
            "candidate_name": candidate.full_name if candidate else None,
            "score": match.score,
            "missing_skills": match.missing_skills,
            "summary": match.summary,
            "status": match.status,
            "created_at": match.created_at,
        })

    return {
        "total": total,
        "page": page,
        "size": size,
        "results": results
    }


@router.get(
    "/{job_id}/auto-matches-stats",
    response_model=dict,
    summary="Get auto-match statistics (recruiter only) — STEP 6",
    description="Get matching statistics for a job posting.",
)
def get_auto_match_stats(
    job_id: int,
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get auto-matching statistics for a job.

    **Requirements:**
    - User must be authenticated and be a recruiter
    - User must own the job

    Returns:
    {
        "total_matches": int,
        "notified": int,
        "accepted": int,
        "rejected": int,
        "avg_score": float,
        "highest_score": int,
        "lowest_score": int
    }
    """
    # Check if recruiter owns the job
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.recruiter_id != recruiter.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view stats for your own jobs"
        )

    stats = MatchingService.get_matching_stats(db, job_id)
    return stats
