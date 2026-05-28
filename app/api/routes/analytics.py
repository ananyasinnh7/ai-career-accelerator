"""
app/api/routes/analytics.py
──────────────────────────
Analytics endpoints for dashboards and metrics (STEP 7).

Routes:
- GET /analytics/recruiter/dashboard      → recruiter dashboard overview
- GET /analytics/recruiter/metrics         → detailed recruiter metrics
- GET /analytics/recruiter/match-distribution → match score distribution
- GET /analytics/recruiter/skills-demand   → top in-demand skills
- GET /analytics/recruiter/time-series     → time series data for charts
- GET /analytics/candidate/dashboard       → candidate dashboard overview
- GET /analytics/activity-feed             → activity feed for user
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.logging import get_logger
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.analytics import (
    RecruiterDashboardResponse,
    RecruiterMetricsResponse,
    CandidateDashboardResponse,
    ActivityFeedResponse,
    MatchDistributionResponse,
    SkillDemandResponse,
    TimeSeriesResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
logger = get_logger(__name__)

_recruiter = Depends(require_role(UserRole.recruiter))
_candidate = Depends(require_role(UserRole.candidate))
_authenticated = Depends(get_current_user)


# ── Recruiter Dashboard ──────────────────────────────────────────────────────

@router.get(
    "/recruiter/dashboard",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get recruiter dashboard (recruiter only)",
    description="Get recruiter's dashboard with key metrics and overview.",
)
def get_recruiter_dashboard(
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get recruiter's dashboard overview.

    **Requirements:**
    - User must be authenticated and be a recruiter

    Returns:
    {
        "total_jobs_posted": int,
        "active_jobs": int,
        "total_applicants": int,
        "total_shortlisted": int,
        "total_rejected": int,
        "avg_time_to_hire": float,
        "response_rate": float,
        "top_jobs": [],
        "recent_matches": int,
        "matches_this_week": int,
        "notifications_unread": int
    }
    """
    dashboard = AnalyticsService.get_recruiter_dashboard(db, recruiter.id)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard"
        )

    logger.info(f"Recruiter {recruiter.id} accessed dashboard")
    return dashboard


@router.get(
    "/recruiter/metrics",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="Get recruiter metrics (recruiter only)",
    description="Get detailed metrics for recruiter.",
)
def get_recruiter_metrics(
    period: str = Query("month", regex="^(week|month|all_time)$"),
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> list:
    """
    Get detailed metrics for recruiter.

    **Parameters:**
    - period: "week", "month", or "all_time"

    **Requirements:**
    - User must be authenticated and be a recruiter
    """
    metrics = AnalyticsService.get_recruiter_metrics(db, recruiter.id, period)

    logger.info(f"Recruiter {recruiter.id} accessed metrics for period {period}")
    return metrics


@router.get(
    "/recruiter/match-distribution",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get match score distribution (recruiter only)",
    description="Get distribution of match scores for recruiter's jobs.",
)
def get_match_distribution(
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get match score distribution.

    Shows how matches are distributed across score ranges.

    **Requirements:**
    - User must be authenticated and be a recruiter
    """
    distribution = AnalyticsService.get_match_distribution(db, recruiter.id)

    logger.info(f"Recruiter {recruiter.id} accessed match distribution")
    return distribution


@router.get(
    "/recruiter/skills-demand",
    response_model=list,
    status_code=status.HTTP_200_OK,
    summary="Get top in-demand skills (recruiter only)",
    description="Get top in-demand skills across all jobs.",
)
def get_skills_demand(
    limit: int = Query(10, ge=1, le=50),
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> list:
    """
    Get top in-demand skills across all jobs.

    **Parameters:**
    - limit: Number of top skills to return (1-50, default 10)

    **Requirements:**
    - User must be authenticated and be a recruiter
    """
    skills = AnalyticsService.get_top_demanded_skills(db, limit)

    logger.info(f"Recruiter {recruiter.id} accessed skills demand")
    return skills


@router.get(
    "/recruiter/time-series",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get time series data (recruiter only)",
    description="Get time series data for charts.",
)
def get_time_series(
    metric: str = Query(..., regex="^(applications|shortlists|matches)$"),
    period: str = Query("7days", regex="^(7days|30days|90days)$"),
    recruiter: User = _recruiter,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get time series data for charts.

    **Parameters:**
    - metric: "applications", "shortlists", or "matches"
    - period: "7days", "30days", or "90days"

    **Requirements:**
    - User must be authenticated and be a recruiter
    """
    time_series = AnalyticsService.get_time_series_data(db, recruiter.id, metric, period)

    logger.info(f"Recruiter {recruiter.id} accessed time series for {metric} ({period})")
    return time_series


# ── Candidate Dashboard ──────────────────────────────────────────────────────

@router.get(
    "/candidate/dashboard",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get candidate dashboard (candidate only)",
    description="Get candidate's dashboard with applications and stats.",
)
def get_candidate_dashboard(
    candidate: User = _candidate,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get candidate's dashboard overview.

    **Requirements:**
    - User must be authenticated and be a candidate

    Returns:
    {
        "applications": {
            "total_applications": int,
            "total_auto_matches": int,
            "total_shortlisted": int,
            "total_rejected": int,
            "response_rate": float,
            "avg_match_score": float
        },
        "resumes_count": int,
        "primary_resume_title": str,
        "new_matches_this_week": int,
        "unread_notifications": int,
        "top_missing_skills": [],
        "skill_gaps_identified": int
    }
    """
    dashboard = AnalyticsService.get_candidate_dashboard(db, candidate.id)

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard"
        )

    logger.info(f"Candidate {candidate.id} accessed dashboard")
    return dashboard


# ── Activity Feed ────────────────────────────────────────────────────────────

@router.get(
    "/activity-feed",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get activity feed",
    description="Get activity feed for authenticated user.",
)
def get_activity_feed(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user: User = _authenticated,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get activity feed for authenticated user.

    Shows recent matches, shortlists, rejections, and notifications.

    **Parameters:**
    - page: Page number (1-indexed)
    - size: Items per page (1-50, default 20)

    **Requirements:**
    - User must be authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    activities, total = AnalyticsService.get_activity_feed(
        db,
        user.id,
        skip=(page - 1) * size,
        limit=size
    )

    logger.info(f"User {user.id} accessed activity feed (page {page})")

    return {
        "total": total,
        "page": page,
        "size": size,
        "results": activities
    }


# ── Bulk Analytics (for comparison) ──────────────────────────────────────────

@router.get(
    "/platform-stats",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get platform statistics",
    description="Get anonymized platform-wide statistics.",
)
def get_platform_stats(
    db: Session = Depends(get_db),
) -> dict:
    """
    Get platform-wide statistics.

    Returns anonymized stats about total jobs, matches, etc.
    """
    try:
        from sqlalchemy import func
        from app.db.models import User, JobPosting, Match, AutoMatch

        # Count users
        total_candidates = db.query(func.count(User.id)).filter(
            User.role == UserRole.candidate,
            User.is_verified == True
        ).scalar()

        total_recruiters = db.query(func.count(User.id)).filter(
            User.role == UserRole.recruiter
        ).scalar()

        # Count jobs and matches
        total_jobs = db.query(func.count(JobPosting.id)).filter(
            JobPosting.status == "active"
        ).scalar()

        total_matches = db.query(func.count(Match.id)).scalar()
        total_auto_matches = db.query(func.count(AutoMatch.id)).scalar()

        # Average metrics
        avg_matches_per_job = (
            (total_matches + total_auto_matches) / total_jobs
            if total_jobs > 0 else 0
        )

        return {
            "total_candidates": total_candidates or 0,
            "total_recruiters": total_recruiters or 0,
            "total_jobs_active": total_jobs or 0,
            "total_matches": total_matches or 0,
            "total_auto_matches": total_auto_matches or 0,
            "avg_matches_per_job": avg_matches_per_job,
            "timestamp": str(__import__('datetime').datetime.utcnow())
        }

    except Exception as exc:
        logger.error(f"Error fetching platform stats: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch statistics"
        )
