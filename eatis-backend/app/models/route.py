"""
app/models/route.py
────────────────────
Alternate route / diversion recommendations per event.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RouteType(str, enum.Enum):
    ALTERNATE = "alternate"
    EMERGENCY_ACCESS = "emergency_access"
    CLOSURE = "road_closure"


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True
    )

    route_type: Mapped[RouteType] = mapped_column(Enum(RouteType), default=RouteType.ALTERNATE)
    route_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # GeoJSON-encoded polyline for Leaflet rendering (stored as text)
    geojson_coordinates: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Estimated properties
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diversion_benefit: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event = relationship("Event", back_populates="routes")

    def __repr__(self) -> str:
        return f"<Route id={self.id} event_id={self.event_id} type={self.route_type}>"
