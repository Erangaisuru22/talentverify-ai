"""Normalized work experience data model."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ExperienceModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: Optional[str] = None
    candidate_id: str
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = 0
    duration_years: float = 0.0
    description: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    skills_used: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    job_relevance: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    source: str = "cv"
