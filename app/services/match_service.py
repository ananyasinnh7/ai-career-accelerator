"""
app/services/match_service.py
──────────────────────────────
Matching engine — scores a candidate's latest resume against a job posting
using the same AI service, then persists the result as a Match record.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import Match, MatchStatus, JobPosting, JobStatus, ResumeAnalysis, User
from app.schemas.match import MatchStatusUpdate
from app.services.gemini_service import score_resume

logger = get_logger(__name__)


def _get_latest_resume_text(db: Session, candidate: User) -> Optional[str]:
    """Return the resume text from the candidate's most recent analysis."""
    latest = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == candidate.id)
        .order_by(ResumeAnalysis.created_at.desc())
        .first()
    )
    return latest.resume_text if latest else None


def match_candidate_to_job(
    db: Session,
    candidate: User,
    job_id: int,
) -> Match:
    """
    Score the candidate's latest resume against the given job posting.
    Creates and returns a Match record.

    Raises
    ------
    InsufficientPermissionsError
        If job doesn't exist, is not active, or candidate has no resume on file.
    """
    # ── Fetch and validate job ─────────────────────────────────────────────────
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()

    if not job:
        raise InsufficientPermissionsError(f"Job {job_id} not found.")

    if job.status != JobStatus.active:
        raise InsufficientPermissionsError(
            f"Job {job_id} is no longer accepting applications."
        )

    # ── Check for existing match ───────────────────────────────────────────────
    existing = db.query(Match).filter(
        Match.candidate_id == candidate.id,
        Match.job_id == job_id,
    ).first()

    if existing:
        logger.info("Returning existing match id=%d", existing.id)
        return existing

    # ── Get candidate's resume ─────────────────────────────────────────────────
    resume_text = _get_latest_resume_text(db, candidate)
    if not resume_text:
        raise InsufficientPermissionsError(
            "No resume found. Please score your resume at least once via "
            "POST /api/v1/score-resume before matching against jobs."
        )

    # ── AI scoring ────────────────────────────────────────────────────────────
    logger.info(
        "Matching candidate id=%d against job id=%d (%r)",
        candidate.id, job.id, job.title,
    )
    result = score_resume(resume_text, job.description)

    # ── Persist match ──────────────────────────────────────────────────────────
    match = Match(
        candidate_id=candidate.id,
        job_id=job.id,
        score=result.score,
        missing_skills=result.missing_skills,
        recommended_project=result.recommended_project,
        summary=result.summary,
        status=MatchStatus.pending,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    logger.info(
        "Match created: id=%d score=%d candidate=%d job=%d",
        match.id, match.score, candidate.id, job.id,
    )
    return match


def get_candidate_matches(
    db: Session,
    candidate: User,
    page: int = 1,
    size: int = 10,
) -> tuple[int, list[Match]]:
    """Return all matches for a candidate, ordered by score descending."""
    query = (
        db.query(Match)
        .filter(Match.candidate_id == candidate.id)
        .order_by(Match.score.desc())
    )
    total   = query.count()
    results = query.offset((page - 1) * size).limit(size).all()
    return total, results


def get_job_matches(
    db: Session,
    recruiter: User,
    job_id: int,
    page: int = 1,
    size: int = 10,
) -> tuple[int, list[Match]]:
    """
    Return all candidate matches for a job posting.
    Only the owning recruiter can view.

    Raises
    ------
    InsufficientPermissionsError
    """
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.recruiter_id == recruiter.id,
    ).first()

    if not job:
        raise InsufficientPermissionsError(
            f"Job {job_id} not found or you do not own it."
        )

    query = (
        db.query(Match)
        .filter(Match.job_id == job_id)
        .order_by(Match.score.desc())
    )
    total   = query.count()
    results = query.offset((page - 1) * size).limit(size).all()
    return total, results


def update_match_status(
    db: Session,
    recruiter: User,
    match_id: int,
    payload: MatchStatusUpdate,
) -> Match:
    """
    Allow a recruiter to update the status of a match
    (e.g. shortlist or reject a candidate).

    Raises
    ------
    InsufficientPermissionsError
    """
    match = (
        db.query(Match)
        .join(JobPosting)
        .filter(
            Match.id == match_id,
            JobPosting.recruiter_id == recruiter.id,
        )
        .first()
    )

    if not match:
        raise InsufficientPermissionsError(
            f"Match {match_id} not found or you do not have permission."
        )

    match.status          = payload.status
    match.recruiter_notes = payload.recruiter_notes
    db.commit()
    db.refresh(match)
    logger.info("Match id=%d status updated to %s", match.id, payload.status)
    return match