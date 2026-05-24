"""
app/schemas/jobs.py
────────────────────
Pydantic v2 schemas for job posting endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.db.models import JobStatus


# ── Create ─────────────────────────────────────────────────────────────────────

class JobPostingCreate(BaseModel):
    title:            str       = Field(..., min_length=3,  max_length=255)
    company:          str       = Field(..., min_length=2,  max_length=255)
    location:         Optional[str] = Field(None, max_length=255)
    description:      str       = Field(..., min_length=50)
    required_skills:  list[str] = Field(..., min_length=1)
    salary_range:     Optional[str] = Field(None, max_length=100)
    job_type:         Optional[str] = Field(None, max_length=50)
    experience_level: Optional[str] = Field(None, max_length=50)


# ── Update ─────────────────────────────────────────────────────────────────────

class JobPostingUpdate(BaseModel):
    title:            Optional[str]       = Field(None, min_length=3, max_length=255)
    company:          Optional[str]       = Field(None, min_length=2, max_length=255)
    location:         Optional[str]       = Field(None, max_length=255)
    description:      Optional[str]       = Field(None, min_length=50)
    required_skills:  Optional[list[str]] = None
    salary_range:     Optional[str]       = Field(None, max_length=100)
    job_type:         Optional[str]       = Field(None, max_length=50)
    experience_level: Optional[str]       = Field(None, max_length=50)
    status:           Optional[JobStatus] = None


# ── Response ───────────────────────────────────────────────────────────────────

class JobPostingResponse(BaseModel):
    id:               int
    recruiter_id:     int
    title:            str
    company:          str
    location:         Optional[str]
    description:      str
    required_skills:  list[str]
    salary_range:     Optional[str]
    job_type:         Optional[str]
    experience_level: Optional[str]
    status:           JobStatus
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}


class JobPostingSummary(BaseModel):
    """Lightweight version for list views."""
    id:               int
    recruiter_id:     int
    title:            str
    company:          str
    location:         Optional[str]
    required_skills:  list[str]
    salary_range:     Optional[str]
    job_type:         Optional[str]
    experience_level: Optional[str]
    status:           JobStatus
    created_at:       datetime

    model_config = {"from_attributes": True}


class PaginatedJobs(BaseModel):
    total:   int
    page:    int
    size:    int
    results: list[JobPostingSummary]