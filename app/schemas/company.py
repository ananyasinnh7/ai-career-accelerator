"""
app/schemas/company.py
──────────────────────
Pydantic v2 schemas for company profile endpoints.
"""

from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional


class CompanyProfileCreate(BaseModel):
    """Request schema for creating a company profile."""

    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    description: Optional[str] = Field(None, max_length=5000, description="Company description")
    logo_url: Optional[HttpUrl] = Field(None, description="Company logo URL")
    website: Optional[HttpUrl] = Field(None, description="Company website")
    location: Optional[str] = Field(None, max_length=255, description="Company location")
    industry: Optional[str] = Field(None, max_length=100, description="Industry (e.g., Tech, Finance)")
    company_size: Optional[str] = Field(
        None,
        description="Company size: 1-10, 11-50, 51-200, 201-500, 500+"
    )


class CompanyProfileUpdate(BaseModel):
    """Request schema for updating a company profile."""

    company_name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    logo_url: Optional[HttpUrl] = Field(None)
    website: Optional[HttpUrl] = Field(None)
    location: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None)


class CompanyProfileResponse(BaseModel):
    """Response schema for company profile."""

    id: int = Field(..., description="Company profile ID")
    recruiter_id: int = Field(..., description="Recruiter's user ID")
    company_name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyPublicResponse(BaseModel):
    """Public company profile (limited info)."""

    id: int
    company_name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_type: str
