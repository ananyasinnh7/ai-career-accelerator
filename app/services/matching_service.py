"""
app/services/matching_service.py
────────────────────────────────
Advanced matching engine with auto-match and AI scoring (STEP 6).
"""

import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import (
    User, JobPosting, ResumeVersion, AutoMatch, Notification, NotificationType,
    JobMatchStatus
)
from app.services.resume_service import ResumeService
from app.services.email_service import get_email_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class MatchingService:
    """Advanced matching engine for candidates and jobs."""

    @staticmethod
    def get_candidate_primary_resume(db: Session, candidate_id: int) -> Optional[ResumeVersion]:
        """
        Get candidate's primary resume for matching.
        Falls back to most recent if no primary set.
        """
        # Try to get primary resume
        primary = db.query(ResumeVersion).filter(
            ResumeVersion.candidate_id == candidate_id,
            ResumeVersion.is_primary == True,
            ResumeVersion.is_active == True,
        ).first()

        if primary:
            return primary

        # Fallback: get most recent active resume
        return db.query(ResumeVersion).filter(
            ResumeVersion.candidate_id == candidate_id,
            ResumeVersion.is_active == True,
        ).order_by(ResumeVersion.created_at.desc()).first()

    @staticmethod
    def score_candidate_for_job(
        db: Session,
        candidate_id: int,
        job_id: int,
        resume_text: Optional[str] = None
    ) -> Optional[dict]:
        """
        Score a candidate against a job using AI.

        Returns:
        {
            "score": int (0-100),
            "missing_skills": list,
            "summary": str,
            "match_percentage": int
        }
        Or None if candidate not eligible.
        """
        try:
            # Get candidate and job
            candidate = db.query(User).filter_by(id=candidate_id).first()
            job = db.query(JobPosting).filter_by(id=job_id).first()

            if not candidate or not job:
                logger.warning(f"Candidate {candidate_id} or Job {job_id} not found")
                return None

            # Get resume text
            if not resume_text:
                resume_version = MatchingService.get_candidate_primary_resume(db, candidate_id)
                if not resume_version:
                    logger.warning(f"No resume found for candidate {candidate_id}")
                    return None
                resume_text = resume_version.resume_text

            # Use existing resume scoring service
            score_result = ResumeService.score_resume(
                resume_text=resume_text,
                job_description=job.description,
                required_skills=job.required_skills
            )

            if not score_result:
                return None

            return {
                "score": score_result.get("score", 0),
                "missing_skills": score_result.get("missing_skills", []),
                "summary": score_result.get("summary", ""),
                "recommended_project": score_result.get("recommended_project", ""),
                "match_percentage": score_result.get("score", 0)
            }

        except Exception as exc:
            logger.error(f"Error scoring candidate {candidate_id} for job {job_id}: {exc}")
            return None

    @staticmethod
    def trigger_auto_match(db: Session, job_id: int) -> List[AutoMatch]:
        """
        Auto-match all candidates when a job is posted.

        1. Get all active candidates with resumes
        2. Score each candidate
        3. Filter by threshold
        4. Create AutoMatch records
        5. Send notifications to matched candidates
        """
        try:
            job = db.query(JobPosting).filter_by(id=job_id).first()
            if not job or not job.auto_match_enabled:
                logger.info(f"Auto-match disabled for job {job_id}")
                return []

            threshold = job.match_score_threshold  # Default 70

            # Get all candidates with active resumes
            candidates = db.query(User).filter(
                User.role == "candidate",
                User.is_active == True,
                User.is_verified == True,  # Only verified candidates
            ).all()

            matched_candidates = []
            email_service = get_email_service()

            for candidate in candidates:
                # Get candidate's primary resume
                resume = MatchingService.get_candidate_primary_resume(db, candidate.id)
                if not resume:
                    continue

                # Score candidate
                score_result = MatchingService.score_candidate_for_job(
                    db=db,
                    candidate_id=candidate.id,
                    job_id=job_id,
                    resume_text=resume.resume_text
                )

                if not score_result:
                    continue

                score = score_result["score"]

                # Check threshold
                if score < threshold:
                    logger.info(f"Candidate {candidate.id} score {score} below threshold {threshold} for job {job_id}")
                    continue

                # Create AutoMatch record
                auto_match = AutoMatch(
                    job_id=job_id,
                    candidate_id=candidate.id,
                    score=score,
                    missing_skills=score_result.get("missing_skills", []),
                    summary=score_result.get("summary", ""),
                    status=JobMatchStatus.pending
                )

                db.add(auto_match)
                matched_candidates.append(auto_match)

                # Create notification
                notification = Notification(
                    user_id=candidate.id,
                    type=NotificationType.new_match,
                    title=f"New Job Match: {job.title}",
                    message=f"You matched {score}% with {job.title} at {job.company}",
                    related_id=job_id
                )
                db.add(notification)

                # Send email notification
                try:
                    email_service.send_match_notification_email(
                        to_email=candidate.email,
                        full_name=candidate.full_name,
                        job_title=job.title,
                        company=job.company
                    )
                    auto_match.notification_sent_at = db.func.now()
                    auto_match.status = JobMatchStatus.notified
                except Exception as email_exc:
                    logger.warning(f"Failed to send email to {candidate.email}: {email_exc}")

            db.commit()
            logger.info(f"Auto-matched {len(matched_candidates)} candidates for job {job_id}")
            return matched_candidates

        except Exception as exc:
            logger.error(f"Error in auto-match for job {job_id}: {exc}")
            db.rollback()
            return []

    @staticmethod
    def get_job_auto_matches(
        db: Session,
        job_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[AutoMatch], int]:
        """
        Get all auto-matched candidates for a job with pagination.

        Returns:
            (list of AutoMatch, total count)
        """
        query = db.query(AutoMatch).filter_by(job_id=job_id).order_by(AutoMatch.score.desc())
        total = query.count()
        matches = query.offset(skip).limit(limit).all()
        return matches, total

    @staticmethod
    def get_candidate_matches(
        db: Session,
        candidate_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[AutoMatch], int]:
        """
        Get all jobs where candidate was auto-matched.

        Returns:
            (list of AutoMatch, total count)
        """
        query = db.query(AutoMatch).filter_by(
            candidate_id=candidate_id
        ).order_by(AutoMatch.score.desc(), AutoMatch.created_at.desc())

        total = query.count()
        matches = query.offset(skip).limit(limit).all()
        return matches, total

    @staticmethod
    def update_match_status(
        db: Session,
        match_id: int,
        new_status: JobMatchStatus
    ) -> Optional[AutoMatch]:
        """Update the status of an auto-match."""
        match = db.query(AutoMatch).filter_by(id=match_id).first()
        if not match:
            return None

        match.status = new_status
        db.commit()
        db.refresh(match)

        logger.info(f"Updated AutoMatch {match_id} status to {new_status}")
        return match

    @staticmethod
    def get_matching_stats(db: Session, job_id: int) -> dict:
        """Get matching statistics for a job."""
        matches = db.query(AutoMatch).filter_by(job_id=job_id).all()

        if not matches:
            return {
                "total_matches": 0,
                "notified": 0,
                "accepted": 0,
                "rejected": 0,
                "avg_score": 0,
                "highest_score": 0,
                "lowest_score": 0
            }

        scores = [m.score for m in matches]

        return {
            "total_matches": len(matches),
            "notified": sum(1 for m in matches if m.status == JobMatchStatus.notified),
            "accepted": sum(1 for m in matches if m.status == JobMatchStatus.accepted),
            "rejected": sum(1 for m in matches if m.status == JobMatchStatus.rejected),
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        }
