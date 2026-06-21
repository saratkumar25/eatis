"""
app/models/resource.py
───────────────────────
Recommended resource allocation per event.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Recommended units
    officers_required: Mapped[int] = mapped_column(Integer, default=0)
    barricades_required: Mapped[int] = mapped_column(Integer, default=0)
    patrol_vehicles: Mapped[int] = mapped_column(Integer, default=0)
    emergency_units: Mapped[int] = mapped_column(Integer, default=0)
    tow_vehicles: Mapped[int] = mapped_column(Integer, default=0)

    # Deployment zones (JSON-like text for simplicity)
    deployment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    event = relationship("Event", back_populates="resources")

    def __repr__(self) -> str:
        return f"<Resource event_id={self.event_id} officers={self.officers_required}>"
