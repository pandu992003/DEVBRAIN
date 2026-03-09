"""
Pydantic schemas for Knowledge Events.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.event import EventSource, EventDepth, ActivityType


class EventCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., min_length=1, max_length=100)
    technology: str | None = Field(None, max_length=100)
    concept: str | None = Field(None, max_length=200)
    source: EventSource = EventSource.MANUAL
    source_url: str | None = None
    source_title: str | None = None
    depth: EventDepth = EventDepth.BEGINNER
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    activity_type: ActivityType = ActivityType.BROWSING
    engagement_score: float = Field(default=0.5, ge=0.0, le=1.0)
    raw_data: dict | None = None


class EventResponse(BaseModel):
    id: int
    user_id: int
    topic: str
    domain: str
    technology: str | None
    concept: str | None
    source: EventSource
    source_url: str | None
    source_title: str | None
    depth: EventDepth
    confidence_score: float
    activity_type: ActivityType
    engagement_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    total: int
    items: list[EventResponse]
