"""GitHub profile, repository, and skill evidence data models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GithubSkillEvidenceModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill: str
    claimed: bool = True
    verified: bool = True
    evidence_source: str = "github"
    repository: Optional[str] = None
    repositories: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.9, ge=0, le=1)


class GithubRepositoryModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    repository_name: str
    repository_url: str
    description: Optional[str] = ""
    primary_language: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    languages_breakdown: Dict[str, int] = Field(default_factory=dict)
    technologies_detected: List[str] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    stars: int = 0
    forks: int = 0
    pushed_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    code_quality_score: float = 0.0
    readme_evidence: Dict[str, Any] = Field(default_factory=dict)
    testing_evidence: Dict[str, Any] = Field(default_factory=dict)
    deployment_evidence: Dict[str, Any] = Field(default_factory=dict)


class GithubProfileModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    candidate_id: str
    github_url: str
    username: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    repositories: List[GithubRepositoryModel] = Field(default_factory=list)
    detected_skills: List[str] = Field(default_factory=list)
    skill_evidence: List[GithubSkillEvidenceModel] = Field(default_factory=list)
    verification_status: str = "verified"
    last_verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
