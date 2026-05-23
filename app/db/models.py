"""
app/db/models.py
─────────────────
SQLAlchemy ORM models for the career accelerator platform.

Phase 1: ResumeAnalysis
Phase 2: User (role-based) + extended CandidateProfile fields on User
"""

import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    candidate = "candidate"
    recruiter = "recruiter"
    admin     = "admin"


# ── User ───────────────────────────────────────────────────────────────────────

class User(Base):
    """
    Platform user. Can be a candidate (job seeker) or recruiter (employer).
    Candidate-specific profile fields are stored directly on this model
    to keep queries simple for Phase 2. They are nullable for recruiters.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Identity ───────────────────────────────────────────────────────────────
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name       = Column(String(255), nullable=False)
    role            = Column(Enum(UserRole), nullable=False, default=UserRole.candidate)

    # ── Candidate profile fields (nullable for recruiters) ─────────────────────
    headline     = Column(String(255), nullable=True)
    bio          = Column(Text,        nullable=True)
    location     = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url   = Column(String(500), nullable=True)

    # ── Status ─────────────────────────────────────────────────────────────────
    is_active   = Column(Boolean, default=True,  nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    analyses = relationship("ResumeAnalysis", back_populates="user", lazy="select")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


# ── ResumeAnalysis ─────────────────────────────────────────────────────────────

class ResumeAnalysis(Base):
    """
    Persists each /score-resume invocation.
    Linked to a User so candidates have a history dashboard.
    user_id is nullable so unauthenticated Phase 1 requests still work.
    """

    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Owner ──────────────────────────────────────────────────────────────────
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user = relationship("User", back_populates="analyses")

    # ── Input snapshot ─────────────────────────────────────────────────────────
    original_filename = Column(String(255), nullable=True)
    resume_text       = Column(Text,        nullable=False)
    job_description   = Column(Text,        nullable=False)

    # ── AI output ──────────────────────────────────────────────────────────────
    score               = Column(Integer, nullable=False)
    missing_skills      = Column(JSON,    nullable=False)
    recommended_project = Column(Text,    nullable=False)
    summary             = Column(Text,    nullable=False)

    # ── Metadata ───────────────────────────────────────────────────────────────
    gemini_model = Column(String(64), nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<ResumeAnalysis id={self.id} score={self.score} "
            f"user_id={self.user_id} file={self.original_filename!r}>"
        )