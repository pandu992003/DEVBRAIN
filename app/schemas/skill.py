"""
Pydantic schemas for Skill Graph.
"""
from datetime import datetime
from pydantic import BaseModel


class SkillResponse(BaseModel):
    id: int
    user_id: int
    domain: str
    technology: str
    concept: str | None
    score: float
    level: str
    event_count: int
    last_activity: datetime

    model_config = {"from_attributes": True}


class SkillGraphResponse(BaseModel):
    """Returns grouped skill graph by domain."""
    domains: list["DomainNode"]
    total_skills: int
    overall_score: float


class DomainNode(BaseModel):
    domain: str
    technologies: list["TechNode"]
    domain_score: float


class TechNode(BaseModel):
    technology: str
    score: float
    level: str
    event_count: int
    last_activity: datetime


class GapAnalysis(BaseModel):
    technology: str
    domain: str
    current_score: float
    recommended_topics: list[str]
    priority: str  # high / medium / low


class GapsResponse(BaseModel):
    gaps: list[GapAnalysis]
    total_gaps: int
