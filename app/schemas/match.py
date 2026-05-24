"""
app/schemas/match.py
─────────────────────
Pydantic v2 schemas for the matching engine endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.db.models import MatchStatus


# ── Match response ─────────────────────────────────────────────────────────────

class MatchResponse(BaseModel):
    id:                  int
    candidate_id:        int
    job_id:              int
    score:               int
    missing_skills:      list[str]
    recommended_project: str
    summary:             str
    status:              MatchStatus
    recruiter_notes:     Optional[str]
    created_at:          datetime

    model_config = {"from_attributes": True}


class MatchWithJobResponse(MatchResponse):
    """Match result including job details — shown to candidates."""
    job_title:   str
    job_company: str
    job_location: Optional[str]


class MatchWithCandidateResponse(MatchResponse):
    """Match result including candidate details — shown to recruiters."""
    candidate_name:  str
    candidate_email: str
    candidate_headline: Optional[str]


# ── Recruiter action ───────────────────────────────────────────────────────────

class MatchStatusUpdate(BaseModel):
    status:          MatchStatus
    recruiter_notes: Optional[str] = None


# ── Paginated ──────────────────────────────────────────────────────────────────

class PaginatedMatches(BaseModel):
    total:   int
    page:    int
    size:    int
    results: list[MatchResponse]