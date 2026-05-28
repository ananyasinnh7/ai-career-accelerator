"""
app/schemas/analytics.py
────────────────────────
Pydantic schemas for analytics dashboards (STEP 7).
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ── Recruiter Analytics ──────────────────────────────────────────────────────

class JobStats(BaseModel):
    """Statistics for a single job posting."""
    job_id: int
    job_title: str
    total_applicants: int
    auto_matched: int
    shortlisted: int
    rejected: int
    views: int
    applications_per_day: float


class RecruiterDashboardResponse(BaseModel):
    """Recruiter's dashboard overview."""
    total_jobs_posted: int
    active_jobs: int
    total_applicants: int
    total_shortlisted: int
    total_rejected: int
    avg_time_to_hire: Optional[float] = None  # days
    response_rate: float  # percentage (0-100)
    
    # Top performing jobs
    top_jobs: List[JobStats] = Field(default_factory=list)
    
    # Recent activity
    recent_matches: int
    matches_this_week: int
    notifications_unread: int


class RecruiterMetricsResponse(BaseModel):
    """Detailed metrics for recruiter."""
    metric_name: str
    value: float
    change_percent: float  # percentage change from last period
    period: str  # "week", "month", "all_time"


# ── Candidate Analytics ──────────────────────────────────────────────────────

class ApplicationStats(BaseModel):
    """Statistics for candidate applications."""
    total_applications: int
    total_auto_matches: int
    total_shortlisted: int
    total_rejected: int
    response_rate: float  # percentage (0-100)
    avg_match_score: float  # 0-100


class CandidateDashboardResponse(BaseModel):
    """Candidate's dashboard overview."""
    applications: ApplicationStats
    
    # Resume info
    resumes_count: int
    primary_resume_title: Optional[str] = None
    
    # Recent matches
    new_matches_this_week: int
    unread_notifications: int
    
    # Skills analysis
    top_missing_skills: List[str] = Field(default_factory=list)
    skill_gaps_identified: int


class CandidateMatchResponse(BaseModel):
    """Match details for candidate dashboard."""
    match_id: int
    job_id: int
    job_title: str
    company_name: str
    score: int
    status: str
    matched_at: datetime
    recruiter_feedback: Optional[str] = None


# ── Activity Feed ────────────────────────────────────────────────────────────

class ActivityEventResponse(BaseModel):
    """Single activity event."""
    id: int
    event_type: str  # "match", "shortlist", "rejection", "application"
    title: str
    description: str
    timestamp: datetime
    related_id: Optional[int] = None  # job_id, match_id, etc
    is_read: bool


class ActivityFeedResponse(BaseModel):
    """Paginated activity feed."""
    total: int
    page: int
    size: int
    results: List[ActivityEventResponse]


# ── Performance Metrics ──────────────────────────────────────────────────────

class ConversionFunnelStep(BaseModel):
    """Single step in conversion funnel."""
    step_name: str
    count: int
    percentage: float  # percentage of previous step


class ConversionFunnelResponse(BaseModel):
    """Conversion funnel for recruiters."""
    job_id: int
    job_title: str
    steps: List[ConversionFunnelStep]
    
    # Summary
    total_applicants: int
    final_hires: int
    conversion_rate: float  # percentage


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series."""
    date: str  # "YYYY-MM-DD"
    value: int


class TimeSeriesResponse(BaseModel):
    """Time series data for charts."""
    metric_name: str
    period: str  # "7days", "30days", "90days"
    data_points: List[TimeSeriesDataPoint]


# ── Comparison Analytics ─────────────────────────────────────────────────────

class MatchDistributionResponse(BaseModel):
    """Match score distribution."""
    total_matches: int
    score_ranges: dict  # {"0-20": 5, "21-40": 10, "41-60": 15, "61-80": 20, "81-100": 30}
    avg_score: float
    median_score: float


class SkillDemandResponse(BaseModel):
    """Top in-demand skills across all jobs."""
    skill: str
    demand_count: int
    job_count: int
    avg_match_gap: float  # how many candidates are missing this skill


class RecruiterComparisonResponse(BaseModel):
    """Benchmark metrics compared to other recruiters (anonymized)."""
    your_avg_response_time: float
    platform_avg_response_time: float
    your_shortlist_rate: float
    platform_avg_shortlist_rate: float
    your_hire_rate: float
    platform_avg_hire_rate: float


# ── Advanced Analytics ───────────────────────────────────────────────────────

class SkillAnalysisResponse(BaseModel):
    """Candidate's skill analysis."""
    skill_name: str
    proficiency: str  # "beginner", "intermediate", "advanced"
    gap_from_requirement: float  # how far from job requirement (0-100)
    recommendations: List[str]  # suggestions to improve


class CareerPathRecommendation(BaseModel):
    """Career path recommendations for candidates."""
    recommended_job_title: str
    reasoning: str
    match_percentage: int
    companies_hiring: int
    avg_salary_range: Optional[str] = None


# ── Export Analytics ─────────────────────────────────────────────────────────

class ExportAnalyticsRequest(BaseModel):
    """Request to export analytics data."""
    format: str = Field("csv", pattern="^(csv|pdf|json)$")
    metrics: List[str] = Field(...)  # which metrics to include
    date_range: str = Field("all_time")  # "7days", "30days", "90days", "all_time"


class ExportAnalyticsResponse(BaseModel):
    """Response with export link."""
    export_id: str
    file_url: str
    expires_in: int  # seconds
    created_at: datetime
