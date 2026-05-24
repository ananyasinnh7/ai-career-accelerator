"""
app/db/models.py
─────────────────
SQLAlchemy ORM models for the career accelerator platform.

Phase 1: ResumeAnalysis
Phase 2: User, JobPosting, Match
"""

import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
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


class JobStatus(str, enum.Enum):
    active   = "active"
    closed   = "closed"
    draft    = "draft"


class MatchStatus(str, enum.Enum):
    pending  = "pending"
    reviewed = "reviewed"
    shortlisted = "shortlisted"
    rejected = "rejected"


# ── User ───────────────────────────────────────────────────────────────────────

class User(Base):
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
    analyses  = relationship("ResumeAnalysis", back_populates="user",      lazy="select")
    job_posts = relationship("JobPosting",     back_populates="recruiter",  lazy="select")
    matches   = relationship("Match",          back_populates="candidate",  lazy="select")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


# ── JobPosting ─────────────────────────────────────────────────────────────────

class JobPosting(Base):
    """A job posted by a recruiter."""

    __tablename__ = "job_postings"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── Content ────────────────────────────────────────────────────────────────
    title           = Column(String(255), nullable=False)
    company         = Column(String(255), nullable=False)
    location        = Column(String(255), nullable=True)
    description     = Column(Text,        nullable=False)
    required_skills = Column(JSON,        nullable=False, default=list)  # list[str]
    salary_range    = Column(String(100), nullable=True)
    job_type        = Column(String(50),  nullable=True)   # full-time, part-time, contract
    experience_level = Column(String(50), nullable=True)   # junior, mid, senior

    # ── Status ─────────────────────────────────────────────────────────────────
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.active)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    recruiter = relationship("User",  back_populates="job_posts", lazy="select")
    matches   = relationship("Match", back_populates="job",       lazy="select")

    def __repr__(self) -> str:
        return f"<JobPosting id={self.id} title={self.title!r} status={self.status}>"


# ── Match ──────────────────────────────────────────────────────────────────────

class Match(Base):
    """
    AI-generated match between a candidate and a job posting.
    Created when a candidate runs /jobs/{id}/match-me.
    """

    __tablename__ = "matches"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("users.id",        ondelete="CASCADE"), nullable=False, index=True)
    job_id       = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)

    # ── AI output ──────────────────────────────────────────────────────────────
    score               = Column(Integer, nullable=False)
    missing_skills      = Column(JSON,    nullable=False)
    recommended_project = Column(Text,    nullable=False)
    summary             = Column(Text,    nullable=False)

    # ── Recruiter action ───────────────────────────────────────────────────────
    status          = Column(Enum(MatchStatus), nullable=False, default=MatchStatus.pending)
    recruiter_notes = Column(Text, nullable=True)

    # ── Timestamps ─────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    candidate = relationship("User",       back_populates="matches", lazy="select")
    job       = relationship("JobPosting", back_populates="matches", lazy="select")

    def __repr__(self) -> str:
        return f"<Match id={self.id} candidate_id={self.candidate_id} job_id={self.job_id} score={self.score}>"


# ── ResumeAnalysis ─────────────────────────────────────────────────────────────

class ResumeAnalysis(Base):
    """Persists each /score-resume invocation."""

    __tablename__ = "resume_analyses"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user    = relationship("User", back_populates="analyses")

    original_filename   = Column(String(255), nullable=True)
    resume_text         = Column(Text,        nullable=False)
    job_description     = Column(Text,        nullable=False)
    score               = Column(Integer,     nullable=False)
    missing_skills      = Column(JSON,        nullable=False)
    recommended_project = Column(Text,        nullable=False)
    summary             = Column(Text,        nullable=False)
    gemini_model        = Column(String(64),  nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ResumeAnalysis id={self.id} score={self.score} user_id={self.user_id}>"