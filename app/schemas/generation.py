"""
app/schemas/generation.py
─────────────────────────
Pydantic models for Phase 3 generation endpoints.
"""

from pydantic import BaseModel, Field


class RewriteResumeRequest(BaseModel):
    """Request to rewrite resume bullets based on JD."""
    resume_text: str = Field(..., min_length=10, description="Original resume text")
    job_description: str = Field(..., min_length=50, description="Target job description")
    missing_skills: list[str] = Field(default_factory=list, description="Skills to address")


class RewriteResumeResponse(BaseModel):
    """Response with rewritten resume."""
    rewritten_resume: str = Field(..., description="Optimized resume text")
    key_improvements: list[str] = Field(..., description="List of improvements made")


class GenerateCoverLetterRequest(BaseModel):
    """Request to generate a cover letter."""
    candidate_name: str = Field(..., min_length=2, description="Candidate's full name")
    company_name: str = Field(..., min_length=2, description="Target company name")
    job_title: str = Field(..., min_length=2, description="Target job title")
    resume_text: str = Field(..., min_length=10, description="Resume text for context")
    job_description: str = Field(..., min_length=50, description="Job description")
    match_score: int = Field(..., ge=1, le=100, description="AI match score (1-100)")


class GenerateCoverLetterResponse(BaseModel):
    """Response with generated cover letter."""
    cover_letter: str = Field(..., description="Full cover letter text")
    tone: str = Field(default="professional", description="Tone used (professional/enthusiastic/analytical)")


class ExportPDFRequest(BaseModel):
    """Request to export resume + cover letter as PDF."""
    resume_text: str = Field(..., min_length=10, description="Resume text")
    cover_letter_text: str = Field(..., min_length=50, description="Cover letter text")
    candidate_name: str = Field(..., min_length=2, description="Candidate name for filename")
    job_title: str = Field(default="Resume", description="Job title for document header")


class ExportPDFResponse(BaseModel):
    """Response with PDF download info."""
    filename: str = Field(..., description="PDF filename")
    url: str = Field(..., description="Download URL")
    size_bytes: int = Field(..., description="File size in bytes")
