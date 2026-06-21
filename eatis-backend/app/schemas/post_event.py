"""
app/schemas/post_event.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class PostEventCreate(BaseModel):
    actual_congestion_level: str
    actual_risk_score: Optional[float] = None
    actual_delay_minutes: Optional[float] = None
    actual_crowd_size: Optional[float] = None
    performance_notes: Optional[str] = None

    @field_validator("actual_congestion_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid = {"low", "medium", "high", "critical"}
        if v.lower() not in valid:
            raise ValueError(f"congestion_level must be one of {valid}")
        return v.lower()


class PostEventResponse(BaseModel):
    id: int
    event_id: int
    predicted_congestion_level: str
    predicted_risk_score: float
    predicted_delay_minutes: float
    actual_congestion_level: str
    actual_risk_score: Optional[float]
    actual_delay_minutes: Optional[float]
    actual_crowd_size: Optional[float]
    prediction_accuracy_pct: Optional[float]
    congestion_match: Optional[bool]
    performance_notes: Optional[str]
    improvement_recommendations: Optional[str]
    analyzed_at: datetime

    model_config = {"from_attributes": True}
