"""
Phase 3 – Step 9: Admin Panel
app/routers/admin.py

All endpoints require is_admin=True on the User record.
Set first admin manually in DB:  UPDATE users SET is_admin=TRUE WHERE id=1;

Endpoints:
  GET  /admin/stats           — platform-wide statistics
  GET  /admin/users           — list all users
  PUT  /admin/users/{id}/deactivate — deactivate abusive account
  PUT  /admin/users/{id}/activate   — reactivate account
  GET  /admin/jobs            — list all jobs
  GET  /admin/matches         — list all matches
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import User, Job, Match
from app.dependencies import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: User = Depends(get_current_user)):
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(403, "Admin access required.")
    return current_user


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
def platform_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """GET /admin/stats — total users, jobs, matches, avg score."""
    total_users = db.query(User).count()
    total_candidates = db.query(User).filter(User.role == "candidate").count()
    total_recruiters = db.query(User).filter(User.role == "recruiter").count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.is_active == True).count()
    total_matches = db.query(Match).count()
    avg_score = db.query(func.avg(Match.score)).scalar()

    return {
        "total_users": total_users,
        "total_candidates": total_candidates,
        "total_recruiters": total_recruiters,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_matches": total_matches,
        "avg_match_score": round(float(avg_score or 0), 1),
    }


# ── User management ──────────────────────────────────────────────────────────

@router.get("/users")
def list_users(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_verified": u.is_verified,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
        }
        for u in users
    ]


@router.put("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(400, "Cannot deactivate yourself.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    user.is_active = False
    db.commit()
    return {"message": f"User {user.email} deactivated."}


@router.put("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    user.is_active = True
    db.commit()
    return {"message": f"User {user.email} activated."}


# ── Jobs & Matches ────────────────────────────────────────────────────────────

@router.get("/jobs")
def list_all_jobs(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    jobs = db.query(Job).order_by(Job.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return [{"id": j.id, "title": j.title, "company_name": j.company_name, "is_active": j.is_active} for j in jobs]


@router.delete("/jobs/{job_id}")
def admin_delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found.")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted."}


@router.get("/matches")
def list_all_matches(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    matches = db.query(Match).order_by(Match.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return [
        {
            "id": m.id,
            "candidate_id": m.candidate_id,
            "job_id": m.job_id,
            "score": m.score,
            "status": m.status,
        }
        for m in matches
    ]
