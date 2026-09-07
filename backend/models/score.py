"""Scoring and evidence level data models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceLevel(str, Enum):
    VERIFIED = "VERIFIED"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    UNVERIFIED = "UNVERIFIED"


class RecommendedDecision(str, Enum):
    STRONG_MATCH = "STRONG_MATCH"
    GOOD_MATCH = "GOOD_MATCH"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    WEAK_MATCH = "WEAK_MATCH"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ScoreComponentItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: float
    max_score: float
    reason: str
    evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0, le=1)
    evidence_level: Optional[EvidenceLevel] = EvidenceLevel.UNVERIFIED


class ProfileScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skills: ScoreComponentItem
    experience: ScoreComponentItem
    github: ScoreComponentItem
    projects: ScoreComponentItem
    education: ScoreComponentItem
    languages: ScoreComponentItem
    certifications: ScoreComponentItem
    profile_quality: ScoreComponentItem


class CandidateProfileScoreModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    overall_score: float
    score_breakdown: ProfileScoreBreakdown


class JobMatchScoreModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_id: str
    match_score: float
    recommended_decision: RecommendedDecision
    score_breakdown: Dict[str, Any]
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    verified_skills: List[str] = Field(default_factory=list)
    unverified_claims: List[str] = Field(default_factory=list)
    interview_focus: Optional[str] = None
