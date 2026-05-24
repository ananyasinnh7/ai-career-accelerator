"""
app/services/candidate_service.py
───────────────────────────────────
Business logic for candidate profile and history operations.
All functions are synchronous — call via asyncio.to_thread if needed.
"""

from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import ResumeAnalysis, User, UserRole
from app.schemas.candidate import CandidateProfileUpdate

logger = get_logger(__name__)


# ── Profile ────────────────────────────────────────────────────────────────────

def get_candidate_profile(user: User) -> User:
    """
    Return the user object (acts as the profile).

    Raises
    ------
    InsufficientPermissionsError
        If the user is not a candidate.
    """
    if user.role != UserRole.candidate:
        raise InsufficientPermissionsError(
            "Only candidates have a candidate profile."
        )
    return user


def update_candidate_profile(
    db: Session,
    user: User,
    payload: CandidateProfileUpdate,
) -> User:
    """
    Update editable profile fields for a candidate.

    Only fields explicitly provided (non-None) are updated.

    Raises
    ------
    InsufficientPermissionsError
        If the user is not a candidate.
    """
    if user.role != UserRole.candidate:
        raise InsufficientPermissionsError(
            "Only candidates can update a candidate profile."
        )

    update_data = payload.model_dump(exclude_none=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    logger.info("Candidate profile updated for user id=%d fields=%s", user.id, list(update_data.keys()))
    return user


# ── History ────────────────────────────────────────────────────────────────────

def get_analysis_history(
    db: Session,
    user: User,
    page: int = 1,
    size: int = 10,
) -> tuple[int, list[ResumeAnalysis]]:
    """
    Return paginated resume analysis history for a candidate.

    Returns
    -------
    tuple[total_count, analyses_for_this_page]

    Raises
    ------
    InsufficientPermissionsError
        If the user is not a candidate.
    """
    if user.role != UserRole.candidate:
        raise InsufficientPermissionsError(
            "Only candidates have analysis history."
        )

    query = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.user_id == user.id)
        .order_by(ResumeAnalysis.created_at.desc())
    )

    total   = query.count()
    results = query.offset((page - 1) * size).limit(size).all()

    logger.info(
        "History fetch for user id=%d: page=%d size=%d total=%d",
        user.id, page, size, total,
    )
    return total, results


def get_analysis_by_id(
    db: Session,
    user: User,
    analysis_id: int,
) -> ResumeAnalysis:
    """
    Return a single analysis that belongs to the requesting candidate.

    Raises
    ------
    InsufficientPermissionsError
        If the analysis doesn't exist or belongs to another user.
    """
    analysis = (
        db.query(ResumeAnalysis)
        .filter(
            ResumeAnalysis.id == analysis_id,
            ResumeAnalysis.user_id == user.id,
        )
        .first()
    )

    if not analysis:
        raise InsufficientPermissionsError(
            f"Analysis {analysis_id} not found or does not belong to you."
        )

    return analysis