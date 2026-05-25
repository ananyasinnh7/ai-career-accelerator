"""
app/schemas/resume.py
──────────────────────
Pydantic v2 schemas for resume-related endpoints.
These are the API's public contract — keep them stable.
"""

from pydantic import BaseModel, Field, field_validator


class ResumeScoreResponse(BaseModel):
    """Structured response returned by the /score-resume endpoint."""

    score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Overall match score between the resume and the job description (1–100).",
    )
    missing_skills: list[str] = Field(
        ...,
        description="Skills present in the JD that are absent or weak in the resume.",
    )
    recommended_project: str = Field(
        ...,
        description="A concrete project the candidate should build to close skill gaps.",
    )
    summary: str = Field(
        ...,
        description="A brief narrative explaining the score and key observations.",
    )

    @field_validator("score", mode="before")
    @classmethod
    def coerce_score(cls, v: object) -> int:
        """Accept numeric strings from Gemini JSON responses."""
        try:
            return int(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"score must be an integer, got {v!r}") from exc

    @field_validator("missing_skills", mode="before")
    @classmethod
    def non_empty_skills(cls, v: object) -> list[str]:
        if not isinstance(v, list):
            raise ValueError("missing_skills must be a list")
        return [str(s).strip() for s in v if str(s).strip()]


class ResumeRewriteResponse(BaseModel):
    """Structured response returned by the /rewrite-resume endpoint."""

    rewritten_resume: str = Field(
        ...,
        description="The improved resume text tailored to the job description.",
    )
    key_improvements: list[str] = Field(
        ...,
        description="List of specific improvements made to the resume.",
    )
    summary: str = Field(
        ...,
        description="Brief summary of the improvement strategy applied.",
    )

    @field_validator("key_improvements", mode="before")
    @classmethod
    def non_empty_improvements(cls, v: object) -> list[str]:
        if not isinstance(v, list):
            raise ValueError("key_improvements must be a list")
        return [str(s).strip() for s in v if str(s).strip()]


class CoverLetterResponse(BaseModel):
    """Structured response returned by the /generate-cover-letter endpoint."""

    cover_letter: str = Field(
        ...,
        description="The generated professional cover letter.",
    )
    key_highlights: list[str] = Field(
        ...,
        description="Key strengths highlighted in the cover letter.",
    )
    tone: str = Field(
        ...,
        description="The tone of the cover letter (e.g., professional, enthusiastic).",
    )

    @field_validator("key_highlights", mode="before")
    @classmethod
    def non_empty_highlights(cls, v: object) -> list[str]:
        if not isinstance(v, list):
            raise ValueError("key_highlights must be a list")
        return [str(s).strip() for s in v if str(s).strip()]


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    error_type: str
