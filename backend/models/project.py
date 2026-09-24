"""Project data model with repository linkage."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProjectModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    id: Optional[str] = None
    candidate_id: str
    name: str
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    demo_url: Optional[str] = None
    candidate_contribution: Optional[str] = None
    project_type: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    linked_repository: Optional[str] = None
    github_verified: bool = False
    confidence: float = Field(default=0.5, ge=0, le=1)
    source: str = "cv"
