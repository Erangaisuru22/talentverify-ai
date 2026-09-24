"""Analysis run audit models for historical candidate evaluations."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalysisRunModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    candidate_id: str
    job_id: Optional[str] = None
    cv_document_id: Optional[str] = None
    document_version: int = 1
    extracted_data_snapshot: Dict[str, Any] = Field(default_factory=dict)
    verification_results: Dict[str, Any] = Field(default_factory=dict)
    scoring_rules_version: str = "2.5"
    model_version: str = "gemini-3.5-flash-lite"
    candidate_profile_score: float = 0.0
    job_match_score: Optional[float] = None
    individual_score_components: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    analysis_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
