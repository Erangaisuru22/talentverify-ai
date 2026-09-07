"""Normalized education data model."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EducationModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: Optional[str] = None
    candidate_id: str
    qualification: Optional[str] = None
    institution: Optional[str] = None
    field: Optional[str] = None
    degree_level: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    grade: Optional[str] = None
    relevant_subjects: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    source: str = "cv"
