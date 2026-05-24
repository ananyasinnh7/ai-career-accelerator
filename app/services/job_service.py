"""
app/services/job_service.py
────────────────────────────
Business logic for job posting CRUD operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientPermissionsError
from app.core.logging import get_logger
from app.db.models import JobPosting, JobStatus, User, UserRole
from app.schemas.jobs import JobPostingCreate, JobPostingUpdate

logger = get_logger(__name__)


def create_job(db: Session, recruiter: User, payload: JobPostingCreate) -> JobPosting:
    """Create a new job posting for a recruiter."""
    job = JobPosting(
        recruiter_id=recruiter.id,
        title=payload.title.strip(),
        company=payload.company.strip(),
        location=payload.location,
        description=payload.description.strip(),
        required_skills=payload.required_skills,
        salary_range=payload.salary_range,
        job_type=payload.job_type,
        experience_level=payload.experience_level,
        status=JobStatus.active,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("Job created: id=%d title=%r recruiter_id=%d", job.id, job.title, recruiter.id)
    return job


def get_jobs(
    db: Session,
    page: int = 1,
    size: int = 10,
    status: Optional[JobStatus] = JobStatus.active,
    search: Optional[str] = None,
) -> tuple[int, list[JobPosting]]:
    """Return paginated list of job postings. Public — no auth required."""
    query = db.query(JobPosting)

    if status:
        query = query.filter(JobPosting.status == status)

    if search:
        term = f"%{search.lower()}%"
        query = query.filter(
            JobPosting.title.ilike(term) |
            JobPosting.company.ilike(term) |
            JobPosting.description.ilike(term)
        )

    query = query.order_by(JobPosting.created_at.desc())
    total   = query.count()
    results = query.offset((page - 1) * size).limit(size).all()
    return total, results


def get_job_by_id(db: Session, job_id: int) -> Optional[JobPosting]:
    """Return a single job posting by ID."""
    return db.query(JobPosting).filter(JobPosting.id == job_id).first()


def get_recruiter_jobs(
    db: Session,
    recruiter: User,
    page: int = 1,
    size: int = 10,
) -> tuple[int, list[JobPosting]]:
    """Return all jobs posted by a specific recruiter."""
    query = (
        db.query(JobPosting)
        .filter(JobPosting.recruiter_id == recruiter.id)
        .order_by(JobPosting.created_at.desc())
    )
    total   = query.count()
    results = query.offset((page - 1) * size).limit(size).all()
    return total, results


def update_job(
    db: Session,
    recruiter: User,
    job_id: int,
    payload: JobPostingUpdate,
) -> JobPosting:
    """
    Update a job posting. Only the owning recruiter can update.

    Raises
    ------
    InsufficientPermissionsError — job not found or not owned by this recruiter.
    """
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.recruiter_id == recruiter.id,
    ).first()

    if not job:
        raise InsufficientPermissionsError(
            f"Job {job_id} not found or you do not have permission to edit it."
        )

    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    logger.info("Job updated: id=%d fields=%s", job.id, list(update_data.keys()))
    return job


def delete_job(db: Session, recruiter: User, job_id: int) -> None:
    """
    Close (soft-delete) a job posting.

    Raises
    ------
    InsufficientPermissionsError — job not found or not owned by this recruiter.
    """
    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.recruiter_id == recruiter.id,
    ).first()

    if not job:
        raise InsufficientPermissionsError(
            f"Job {job_id} not found or you do not have permission to delete it."
        )

    job.status = JobStatus.closed
    db.commit()
    logger.info("Job closed: id=%d", job.id)