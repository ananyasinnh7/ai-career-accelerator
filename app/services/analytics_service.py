"""
app/services/analytics_service.py
────────────────────────────────
Analytics service for dashboards and metrics (STEP 7).
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.db.models import (
    User, JobPosting, Match, AutoMatch, ResumeVersion, Notification,
    UserRole, MatchStatus, JobMatchStatus
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Analytics service for recruiter and candidate dashboards."""

    # ── Recruiter Analytics ──────────────────────────────────────────────────

    @staticmethod
    def get_recruiter_dashboard(db: Session, recruiter_id: int) -> dict:
        """
        Get recruiter's dashboard overview.

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
        try:
            # Get recruiter's jobs
            jobs = db.query(JobPosting).filter_by(recruiter_id=recruiter_id).all()
            job_ids = [j.id for j in jobs]

            if not job_ids:
                return {
                    "total_jobs_posted": 0,
                    "active_jobs": 0,
                    "total_applicants": 0,
                    "total_shortlisted": 0,
                    "total_rejected": 0,
                    "avg_time_to_hire": 0,
                    "response_rate": 0,
                    "top_jobs": [],
                    "recent_matches": 0,
                    "matches_this_week": 0,
                    "notifications_unread": 0
                }

            # Count active jobs
            active_jobs = sum(1 for j in jobs if j.status.value == "active")

            # Get all matches for recruiter's jobs
            all_matches = db.query(Match).filter(Match.job_id.in_(job_ids)).all()
            total_applicants = len(all_matches)
            shortlisted = sum(1 for m in all_matches if m.status == MatchStatus.shortlisted)
            rejected = sum(1 for m in all_matches if m.status == MatchStatus.rejected)

            # Get auto-matches
            auto_matches = db.query(AutoMatch).filter(AutoMatch.job_id.in_(job_ids)).all()
            recent_matches = sum(1 for am in auto_matches if (
                datetime.utcnow() - am.created_at < timedelta(days=1)
            ))
            matches_this_week = sum(1 for am in auto_matches if (
                datetime.utcnow() - am.created_at < timedelta(days=7)
            ))

            # Calculate average time to hire (from job creation to shortlist)
            hire_times = []
            for match in all_matches:
                if match.status == MatchStatus.shortlisted and match.job:
                    time_to_hire = (match.updated_at - match.job.created_at).days
                    hire_times.append(time_to_hire)

            avg_time_to_hire = sum(hire_times) / len(hire_times) if hire_times else 0

            # Calculate response rate
            response_rate = (shortlisted / total_applicants * 100) if total_applicants > 0 else 0

            # Get top performing jobs
            top_jobs = AnalyticsService._get_top_jobs(db, job_ids)

            # Get unread notifications for recruiter
            unread_notifications = db.query(Notification).filter(
                Notification.user_id == recruiter_id,
                Notification.is_read == False
            ).count()

            return {
                "total_jobs_posted": len(jobs),
                "active_jobs": active_jobs,
                "total_applicants": total_applicants,
                "total_shortlisted": shortlisted,
                "total_rejected": rejected,
                "avg_time_to_hire": avg_time_to_hire,
                "response_rate": response_rate,
                "top_jobs": top_jobs,
                "recent_matches": recent_matches,
                "matches_this_week": matches_this_week,
                "notifications_unread": unread_notifications
            }

        except Exception as exc:
            logger.error(f"Error fetching recruiter dashboard for {recruiter_id}: {exc}")
            return {}

    @staticmethod
    def _get_top_jobs(db: Session, job_ids: List[int], limit: int = 5) -> List[dict]:
        """Get top performing jobs by applicant count."""
        try:
            top_jobs = []
            
            for job_id in job_ids[:limit]:
                job = db.query(JobPosting).filter_by(id=job_id).first()
                if not job:
                    continue

                matches = db.query(Match).filter_by(job_id=job_id).all()
                auto_matches = db.query(AutoMatch).filter_by(job_id=job_id).all()

                shortlisted = sum(1 for m in matches if m.status == MatchStatus.shortlisted)
                rejected = sum(1 for m in matches if m.status == MatchStatus.rejected)

                top_jobs.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "total_applicants": len(matches) + len(auto_matches),
                    "auto_matched": len(auto_matches),
                    "shortlisted": shortlisted,
                    "rejected": rejected,
                    "views": len(matches) + len(auto_matches),
                    "applications_per_day": (len(matches) + len(auto_matches)) / max(
                        (datetime.utcnow() - job.created_at).days, 1
                    )
                })

            return sorted(top_jobs, key=lambda x: x["total_applicants"], reverse=True)

        except Exception as exc:
            logger.error(f"Error getting top jobs: {exc}")
            return []

    @staticmethod
    def get_recruiter_metrics(db: Session, recruiter_id: int, period: str = "month") -> List[dict]:
        """
        Get detailed metrics for recruiter over a period.

        period: "week", "month", "all_time"
        """
        try:
            metrics = []

            # Determine date range
            if period == "week":
                days = 7
            elif period == "month":
                days = 30
            else:
                days = None

            start_date = (datetime.utcnow() - timedelta(days=days)) if days else None

            # Get recruiter's jobs
            jobs_query = db.query(JobPosting).filter_by(recruiter_id=recruiter_id)
            if start_date:
                jobs_query = jobs_query.filter(JobPosting.created_at >= start_date)

            jobs = jobs_query.all()
            job_ids = [j.id for j in jobs]

            if job_ids:
                # Total matches metric
                matches_count = db.query(func.count(Match.id)).filter(Match.job_id.in_(job_ids))
                if start_date:
                    matches_count = matches_count.filter(Match.created_at >= start_date)
                matches_count = matches_count.scalar()

                metrics.append({
                    "metric_name": "Total Matches",
                    "value": matches_count,
                    "change_percent": 0,
                    "period": period
                })

                # Shortlist rate metric
                shortlisted = db.query(func.count(Match.id)).filter(
                    Match.job_id.in_(job_ids),
                    Match.status == MatchStatus.shortlisted
                )
                if start_date:
                    shortlisted = shortlisted.filter(Match.created_at >= start_date)
                shortlisted = shortlisted.scalar()

                shortlist_rate = (shortlisted / matches_count * 100) if matches_count > 0 else 0
                metrics.append({
                    "metric_name": "Shortlist Rate",
                    "value": shortlist_rate,
                    "change_percent": 0,
                    "period": period
                })

            return metrics

        except Exception as exc:
            logger.error(f"Error fetching recruiter metrics: {exc}")
            return []

    # ── Candidate Analytics ──────────────────────────────────────────────────

    @staticmethod
    def get_candidate_dashboard(db: Session, candidate_id: int) -> dict:
        """
        Get candidate's dashboard overview.

        Returns application stats, resume info, recent matches, skill gaps.
        """
        try:
            # Get candidate
            candidate = db.query(User).filter_by(id=candidate_id).first()
            if not candidate or candidate.role != UserRole.candidate:
                return {}

            # Get applications (matches)
            matches = db.query(Match).filter_by(candidate_id=candidate_id).all()
            auto_matches = db.query(AutoMatch).filter_by(candidate_id=candidate_id).all()

            total_applications = len(matches) + len(auto_matches)
            shortlisted = sum(1 for m in matches if m.status == MatchStatus.shortlisted)
            rejected = sum(1 for m in matches if m.status == MatchStatus.rejected)

            response_rate = (shortlisted / total_applications * 100) if total_applications > 0 else 0

            # Calculate average match score
            all_scores = [m.score for m in matches] + [am.score for am in auto_matches]
            avg_match_score = sum(all_scores) / len(all_scores) if all_scores else 0

            # Get resumes
            resumes = db.query(ResumeVersion).filter_by(
                candidate_id=candidate_id,
                is_active=True
            ).all()

            primary_resume = next((r for r in resumes if r.is_primary), None)

            # Recent matches this week
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            recent_matches = sum(1 for am in auto_matches if am.created_at >= one_week_ago)

            # Unread notifications
            unread_notifications = db.query(Notification).filter(
                Notification.user_id == candidate_id,
                Notification.is_read == False
            ).count()

            # Get top missing skills
            top_missing_skills = AnalyticsService._extract_top_missing_skills(matches + auto_matches)

            return {
                "applications": {
                    "total_applications": total_applications,
                    "total_auto_matches": len(auto_matches),
                    "total_shortlisted": shortlisted,
                    "total_rejected": rejected,
                    "response_rate": response_rate,
                    "avg_match_score": avg_match_score
                },
                "resumes_count": len(resumes),
                "primary_resume_title": primary_resume.title if primary_resume else None,
                "new_matches_this_week": recent_matches,
                "unread_notifications": unread_notifications,
                "top_missing_skills": top_missing_skills,
                "skill_gaps_identified": len(top_missing_skills)
            }

        except Exception as exc:
            logger.error(f"Error fetching candidate dashboard for {candidate_id}: {exc}")
            return {}

    @staticmethod
    def _extract_top_missing_skills(matches: List, limit: int = 5) -> List[str]:
        """Extract and count top missing skills across matches."""
        try:
            skill_counts: Dict[str, int] = {}

            for match in matches:
                if hasattr(match, 'missing_skills') and match.missing_skills:
                    for skill in match.missing_skills:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1

            # Sort and return top skills
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            return [skill for skill, _ in sorted_skills[:limit]]

        except Exception as exc:
            logger.error(f"Error extracting top missing skills: {exc}")
            return []

    # ── Match Distribution ───────────────────────────────────────────────────

    @staticmethod
    def get_match_distribution(db: Session, recruiter_id: int) -> dict:
        """
        Get match score distribution for recruiter's jobs.
        """
        try:
            # Get recruiter's jobs
            jobs = db.query(JobPosting).filter_by(recruiter_id=recruiter_id).all()
            job_ids = [j.id for j in jobs]

            if not job_ids:
                return {
                    "total_matches": 0,
                    "score_ranges": {},
                    "avg_score": 0,
                    "median_score": 0
                }

            # Get all matches
            matches = db.query(Match).filter(Match.job_id.in_(job_ids)).all()
            auto_matches = db.query(AutoMatch).filter(AutoMatch.job_id.in_(job_ids)).all()

            all_matches = matches + auto_matches
            all_scores = [m.score for m in all_matches]

            if not all_scores:
                return {
                    "total_matches": 0,
                    "score_ranges": {},
                    "avg_score": 0,
                    "median_score": 0
                }

            # Distribute scores into ranges
            score_ranges = {
                "0-20": sum(1 for s in all_scores if 0 <= s <= 20),
                "21-40": sum(1 for s in all_scores if 21 <= s <= 40),
                "41-60": sum(1 for s in all_scores if 41 <= s <= 60),
                "61-80": sum(1 for s in all_scores if 61 <= s <= 80),
                "81-100": sum(1 for s in all_scores if 81 <= s <= 100),
            }

            avg_score = sum(all_scores) / len(all_scores)
            sorted_scores = sorted(all_scores)
            median_score = sorted_scores[len(sorted_scores) // 2]

            return {
                "total_matches": len(all_matches),
                "score_ranges": score_ranges,
                "avg_score": avg_score,
                "median_score": median_score
            }

        except Exception as exc:
            logger.error(f"Error getting match distribution: {exc}")
            return {}

    # ── Activity Feed ────────────────────────────────────────────────────────

    @staticmethod
    def get_activity_feed(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[dict], int]:
        """
        Get activity feed for a user (matches, shortlists, rejections).

        Returns (activities, total_count)
        """
        try:
            activities = []

            # Get user's notifications
            notifications_query = db.query(Notification).filter_by(user_id=user_id).order_by(
                Notification.created_at.desc()
            )

            total = notifications_query.count()
            notifications = notifications_query.offset(skip).limit(limit).all()

            for notif in notifications:
                activities.append({
                    "id": notif.id,
                    "event_type": notif.type.value,
                    "title": notif.title,
                    "description": notif.message,
                    "timestamp": notif.created_at,
                    "related_id": notif.related_id,
                    "is_read": notif.is_read
                })

            return activities, total

        except Exception as exc:
            logger.error(f"Error fetching activity feed for user {user_id}: {exc}")
            return [], 0

    # ── Time Series Data ────────────────────────────────────────────────────

    @staticmethod
    def get_time_series_data(
        db: Session,
        recruiter_id: int,
        metric: str,
        period: str = "7days"
    ) -> dict:
        """
        Get time series data for charts.

        metric: "applications", "shortlists", "matches"
        period: "7days", "30days", "90days"
        """
        try:
            # Determine date range
            if period == "7days":
                days = 7
            elif period == "30days":
                days = 30
            else:
                days = 90

            start_date = datetime.utcnow() - timedelta(days=days)

            # Get recruiter's jobs
            jobs = db.query(JobPosting).filter_by(recruiter_id=recruiter_id).all()
            job_ids = [j.id for j in jobs]

            data_points = []

            if job_ids:
                # Generate data for each day
                for i in range(days + 1):
                    current_date = start_date + timedelta(days=i)
                    day_str = current_date.strftime("%Y-%m-%d")

                    # Count based on metric
                    if metric == "applications":
                        count = db.query(func.count(Match.id)).filter(
                            Match.job_id.in_(job_ids),
                            func.date(Match.created_at) == current_date.date()
                        ).scalar()
                    elif metric == "shortlists":
                        count = db.query(func.count(Match.id)).filter(
                            Match.job_id.in_(job_ids),
                            Match.status == MatchStatus.shortlisted,
                            func.date(Match.updated_at) == current_date.date()
                        ).scalar()
                    else:  # matches
                        count = db.query(func.count(AutoMatch.id)).filter(
                            AutoMatch.job_id.in_(job_ids),
                            func.date(AutoMatch.created_at) == current_date.date()
                        ).scalar()

                    data_points.append({
                        "date": day_str,
                        "value": count or 0
                    })

            return {
                "metric_name": metric,
                "period": period,
                "data_points": data_points
            }

        except Exception as exc:
            logger.error(f"Error fetching time series data: {exc}")
            return {}

    # ── Skill Demand Analysis ────────────────────────────────────────────────

    @staticmethod
    def get_top_demanded_skills(db: Session, limit: int = 10) -> List[dict]:
        """
        Get top in-demand skills across all active jobs.
        """
        try:
            skill_demand: Dict[str, dict] = {}

            # Get all active jobs
            active_jobs = db.query(JobPosting).filter(
                JobPosting.status.in_(["active"])
            ).all()

            for job in active_jobs:
                if job.required_skills:
                    for skill in job.required_skills:
                        if skill not in skill_demand:
                            skill_demand[skill] = {
                                "skill": skill,
                                "demand_count": 0,
                                "job_count": 0,
                                "total_gap": 0,
                                "match_count": 0
                            }

                        skill_demand[skill]["job_count"] += 1
                        skill_demand[skill]["demand_count"] += 1

                        # Count candidates missing this skill
                        matches = db.query(Match).filter_by(job_id=job.id).all()
                        for match in matches:
                            if match.missing_skills and skill in match.missing_skills:
                                skill_demand[skill]["match_count"] += 1

            # Calculate averages and sort
            result = []
            for skill, data in skill_demand.items():
                avg_gap = (data["match_count"] / data["demand_count"] * 100) if data["demand_count"] > 0 else 0
                result.append({
                    "skill": skill,
                    "demand_count": data["demand_count"],
                    "job_count": data["job_count"],
                    "avg_match_gap": avg_gap
                })

            return sorted(result, key=lambda x: x["demand_count"], reverse=True)[:limit]

        except Exception as exc:
            logger.error(f"Error getting top demanded skills: {exc}")
            return []
