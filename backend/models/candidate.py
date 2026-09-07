"""Candidate profile and personal details data models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PersonalInfoModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    headline: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    professional_summary: Optional[str] = None
    experience_years: float = 0.0


class SocialLinksModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class HumanLanguageModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    language: str
    level: Optional[str] = "Proficient"
    evidence: Optional[str] = None


class CertificationModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_url: Optional[str] = None
    credential_id: Optional[str] = None
    relevant_skills: List[str] = Field(default_factory=list)
    verification_status: str = "unverified"
    confidence: float = Field(default=0.5, ge=0, le=1)


class CandidateProfileModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    personal_info: PersonalInfoModel = Field(default_factory=PersonalInfoModel)
    social_links: SocialLinksModel = Field(default_factory=SocialLinksModel)
    professional_summary: Optional[str] = ""
    programming_languages: List[str] = Field(default_factory=list)
    human_languages: List[HumanLanguageModel] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[CertificationModel] = Field(default_factory=list)
    github_summary: Optional[Dict[str, Any]] = None
    profile_score: float = 0.0
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
