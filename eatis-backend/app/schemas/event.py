"""
app/schemas/event.py
─────────────────────
Pydantic schemas for the Event resource.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator

from app.models.event import EventStatus, EventType


class EventCreate(BaseModel):
    name: str
    event_type: EventType
    description: Optional[str] = None

    # Location
    location_name: str
    latitude: float
    longitude: float
    address: Optional[str] = None

    # Timing
    start_datetime: datetime
    end_datetime: datetime

    # Characteristics
    expected_crowd_size: int
    has_road_closure: bool = False
    road_closure_details: Optional[str] = None

    @field_validator("expected_crowd_size")
    @classmethod
    def validate_crowd(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Crowd size must be positive")
        if v > 10_000_000:
            raise ValueError("Crowd size exceeds maximum allowed")
        return v

    @field_validator("latitude")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "EventCreate":
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")
        return self


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[EventType] = None
    location_name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    expected_crowd_size: Optional[int] = None
    has_road_closure: Optional[bool] = None
    road_closure_details: Optional[str] = None
    status: Optional[EventStatus] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


class EventResponse(BaseModel):
    id: int
    name: str
    event_type: EventType
    description: Optional[str]
    location_name: str
    latitude: float
    longitude: float
    address: Optional[str]
    start_datetime: datetime
    end_datetime: datetime
    duration_hours: float
    expected_crowd_size: int
    has_road_closure: bool
    road_closure_details: Optional[str]
    status: EventStatus
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EventSimulateRequest(BaseModel):
    """Schema for simulating an event without persisting it."""
    event_type: EventType
    latitude: float
    longitude: float
    start_datetime: datetime
    expected_crowd_size: int
    duration_hours: float = 4.0
    has_road_closure: bool = False
