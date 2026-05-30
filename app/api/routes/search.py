"""
Phase 3 – Step 7: Search & Filters (Advanced)
app/routers/search.py

GET /search/jobs     — full-text + filters
GET /search/candidates — score range, skills, availability (recruiter only)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional

from app.database import get_db
from app.models import Job, User, Resume
from app.dependencies import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/jobs")
def search_jobs(
    q: Optional[str] = Query(None, description="Full-text search in title + description"),
    location: Optional[str] = Query(None),
    salary_min: Optional[int] = Query(None),
    salary_max: Optional[int] = Query(None),
    experience_level: Optional[str] = Query(None, description="entry|mid|senior|lead"),
    job_type: Optional[str] = Query(None, description="full-time|part-time|contract|remote"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Search jobs with optional filters.
    All parameters are optional – omitting them returns all active jobs.
    """
    query = db.query(Job).filter(Job.is_active == True)

    if q:
        search_term = f"%{q.lower()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                Job.description.ilike(search_term),
                Job.company_name.ilike(search_term),
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if salary_min is not None:
        query = query.filter(Job.salary_max >= salary_min)

    if salary_max is not None:
        query = query.filter(Job.salary_min <= salary_max)

    if experience_level:
        query = query.filter(Job.experience_level == experience_level)

    if job_type:
        query = query.filter(Job.job_type == job_type)

    total = query.count()
    jobs = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "results": [
            {
                "id": j.id,
                "title": j.title,
                "company_name": j.company_name,
                "location": j.location,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "experience_level": j.experience_level,
                "job_type": j.job_type,
                "created_at": str(j.created_at),
            }
            for j in jobs
        ],
    }


@router.get("/candidates")
def search_candidates(
    score_min: Optional[float] = Query(None, description="Min average match score"),
    score_max: Optional[float] = Query(None, description="Max average match score"),
    skills: Optional[str] = Query(None, description="Comma-separated skill keywords"),
    available: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recruiter-only: search candidates by score range and skills."""
    if current_user.role != "recruiter":
        from fastapi import HTTPException
        raise HTTPException(403, "Recruiter only.")

    from sqlalchemy import func
    from app.models import Match

    query = (
        db.query(User, func.avg(Match.score).label("avg_score"))
        .join(Match, Match.candidate_id == User.id, isouter=True)
        .filter(User.role == "candidate", User.is_active == True)
        .group_by(User.id)
    )

    if score_min is not None:
        query = query.having(func.avg(Match.score) >= score_min)
    if score_max is not None:
        query = query.having(func.avg(Match.score) <= score_max)

    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()

    results = []
    for user, avg_score in rows:
        # Skill filter (simple text search in resume content)
        if skills:
            skill_list = [s.strip().lower() for s in skills.split(",")]
            resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
            combined = " ".join(r.content or "" for r in resumes).lower()
            if not all(sk in combined for sk in skill_list):
                continue

        results.append({
            "id": user.id,
            "name": user.full_name or user.email,
            "email": user.email,
            "avg_score": round(float(avg_score or 0), 1),
        })

    return {"total": total, "page": page, "per_page": per_page, "results": results}
