"""
app/schemas/resume.py
──────────────────────
Pydantic v2 schemas for the /score-resume endpoint.
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


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    error_type: str