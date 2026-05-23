"""
app/schemas/candidate.py
─────────────────────────
Pydantic v2 schemas for candidate profile and history endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Profile ────────────────────────────────────────────────────────────────────

class CandidateProfileUpdate(BaseModel):
    """Fields a candidate can update on their profile."""
    full_name:  Optional[str] = Field(None, min_length=2, max_length=255)
    headline:   Optional[str] = Field(None, max_length=255, description="e.g. 'Senior Python Developer'")
    bio:        Optional[str] = Field(None, max_length=1000)
    location:   Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url:   Optional[str] = Field(None, max_length=500)


class CandidateProfileResponse(BaseModel):
    """Full candidate profile returned to the client."""
    id:           int
    email:        str
    full_name:    str
    headline:     Optional[str]
    bio:          Optional[str]
    location:     Optional[str]
    linkedin_url: Optional[str]
    github_url:   Optional[str]
    is_verified:  bool
    created_at:   datetime

    model_config = {"from_attributes": True}


# ── History ────────────────────────────────────────────────────────────────────

class AnalysisSummary(BaseModel):
    """Lightweight summary shown in the history list."""
    id:                 int
    original_filename:  Optional[str]
    score:              int
    missing_skills:     list[str]
    recommended_project: str
    summary:            str
    created_at:         datetime

    model_config = {"from_attributes": True}


class AnalysisDetail(BaseModel):
    """Full analysis detail including the original resume text and JD."""
    id:                  int
    original_filename:   Optional[str]
    job_description:     str
    score:               int
    missing_skills:      list[str]
    recommended_project: str
    summary:             str
    gemini_model:        str
    created_at:          datetime

    model_config = {"from_attributes": True}


class PaginatedHistory(BaseModel):
    """Paginated list of past analyses."""
    total:   int
    page:    int
    size:    int
    results: list[AnalysisSummary]