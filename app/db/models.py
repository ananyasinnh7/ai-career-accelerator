"""
app/db/models.py
─────────────────
SQLAlchemy ORM models for the career accelerator platform.

Phase 1 includes:
  * ResumeAnalysis — persists every scoring request and its result.
"""

import datetime
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ResumeAnalysis(Base):
    """
    Persists each /score-resume invocation so results are auditable and
    can be surfaced in a candidate history dashboard in later phases.
    """

    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Input snapshot ─────────────────────────────────────────────────────────
    original_filename = Column(String(255), nullable=True)
    resume_text = Column(Text, nullable=False)
    job_description = Column(Text, nullable=False)

    # ── AI output ─────────────────────────────────────────────────────────────
    score = Column(Integer, nullable=False)
    missing_skills = Column(JSON, nullable=False)   # list[str]
    recommended_project = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)

    # ── Metadata ───────────────────────────────────────────────────────────────
    gemini_model = Column(String(64), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ResumeAnalysis id={self.id} score={self.score} "
            f"file={self.original_filename!r}>"
        )