"""
app/api/routes/jobs.py
───────────────────────
Job posting endpoints:

    POST   /jobs                    → recruiter creates a job
    GET    /jobs                    → anyone browses active jobs
    GET    /jobs/mine               → recruiter sees their own jobs
    GET    /jobs/{id}               → single job detail
    PUT    /jobs/{id}               → recruiter updates their job
    DELETE /jobs/{id}               → recruiter closes their job
    POST   /jobs/{id}/match-me      → candidate matches themselves to a job
    GET    /jobs/{id}/candidates    → recruiter sees ranked candidate list
    PUT    /jobs/{id}/matches/{mid} → recruiter updates a match status
"""

import asyncio
from functools import partial
from typing import Optional

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

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger(__name__)

_recruiter = Depends(require_role(UserRole.recruiter))
_candidate = Depends(require_role(UserRole.candidate))


# ── POST /jobs ─────────────────────────────────────────────────────────────────

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
    job = create_job(db, recruiter, payload)
    return JobPostingResponse.model_validate(job)


# ── GET /jobs ──────────────────────────────────────────────────────────────────

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


# ── GET /jobs/mine ─────────────────────────────────────────────────────────────

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


# ── GET /jobs/{id} ─────────────────────────────────────────────────────────────

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


# ── PUT /jobs/{id} ─────────────────────────────────────────────────────────────

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


# ── DELETE /jobs/{id} ──────────────────────────────────────────────────────────

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


# ── POST /jobs/{id}/match-me ───────────────────────────────────────────────────

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


# ── GET /jobs/{id}/candidates ──────────────────────────────────────────────────

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


# ── PUT /jobs/{id}/matches/{mid} ───────────────────────────────────────────────

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


# ── GET /jobs/matches/mine ─────────────────────────────────────────────────────

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