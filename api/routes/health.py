"""
app/api/routes/health.py
─────────────────────────
Lightweight health-check endpoints for load-balancer / k8s probes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", summary="Liveness probe")
def liveness() -> dict:
    return {"status": "ok", "env": settings.app_env}


@router.get("/health/db", summary="Readiness probe — checks DB connectivity")
def readiness(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }
