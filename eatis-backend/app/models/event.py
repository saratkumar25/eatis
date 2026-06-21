"""
app/models/event.py
────────────────────
Core event model — the central entity for the EATIS system.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EventType(str, enum.Enum):
    POLITICAL_RALLY = "political_rally"
    SPORTS_EVENT = "sports_event"
    MUSIC_FESTIVAL = "music_festival"
    CULTURAL_EVENT = "cultural_event"
    RELIGIOUS_GATHERING = "religious_gathering"
    CONSTRUCTION = "construction"
    PUBLIC_DEMONSTRATION = "public_demonstration"
    MARATHON = "marathon"
    PARADE = "parade"
    EXHIBITION = "exhibition"
    OTHER = "other"


class EventStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    location_name: Mapped[str] = mapped_column(String(300), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timing
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)

    # Event characteristics
    expected_crowd_size: Mapped[int] = mapped_column(Integer, nullable=False)
    has_road_closure: Mapped[bool] = mapped_column(Boolean, default=False)
    road_closure_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status & metadata
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus), default=EventStatus.SCHEDULED, index=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    created_by_user = relationship("User", back_populates="events", foreign_keys=[created_by])
    prediction = relationship("Prediction", back_populates="event", uselist=False, lazy="select", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="event", uselist=False, lazy="select", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="event", lazy="select", cascade="all, delete-orphan")
    ai_queries = relationship("AIQuery", back_populates="event", lazy="select", cascade="all, delete-orphan")
    post_event_analysis = relationship("PostEventAnalysis", back_populates="event", uselist=False, lazy="select", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Event id={self.id} name={self.name} type={self.event_type}>"
