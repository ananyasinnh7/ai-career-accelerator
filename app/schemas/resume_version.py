"""
app/schemas/resume_version.py
─────────────────────────────
Pydantic schemas for multiple resume versions (STEP 6).
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ResumeVersionCreate(BaseModel):
    """Request schema for uploading a new resume version."""

    title: str = Field(..., min_length=2, max_length=255, description="Resume title (e.g., 'Backend Engineer', 'Full-stack')")
    resume_text: str = Field(..., min_length=50, description="Resume content (minimum 50 characters)")
    file_url: Optional[str] = Field(None, description="URL to resume file (PDF/DOCX) if stored in cloud")


class ResumeVersionUpdate(BaseModel):
    """Request schema for updating a resume version."""

    title: Optional[str] = Field(None, min_length=2, max_length=255)
    resume_text: Optional[str] = Field(None, min_length=50)
    is_active: Optional[bool] = Field(None, description="Activate/deactivate resume")


class ResumeVersionResponse(BaseModel):
    """Response schema for a resume version."""

    id: int
    candidate_id: int
    title: str
    resume_text: str
    file_url: Optional[str] = None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeVersionListResponse(BaseModel):
    """Response schema for listing resume versions."""

    id: int
    title: str
    is_primary: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SetPrimaryResumeRequest(BaseModel):
    """Request schema for setting a resume as primary."""

    resume_id: int = Field(..., description="ID of resume to set as primary")


class AutoMatchResponse(BaseModel):
    """Response schema for auto-matched candidates."""

    id: int
    job_id: int
    candidate_id: int
    score: int
    missing_skills: list
    summary: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AutoMatchListResponse(BaseModel):
    """Response for listing auto-matches with candidate info."""

    id: int
    job_id: int
    candidate_id: int
    candidate_email: Optional[str] = None
    candidate_name: Optional[str] = None
    score: int
    missing_skills: list
    summary: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
