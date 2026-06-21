"""
app/models/prediction.py
─────────────────────────
XGBoost congestion prediction results stored per event.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CongestionLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Core prediction outputs
    congestion_level: Mapped[CongestionLevel] = mapped_column(Enum(CongestionLevel), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)          # 0–100
    delay_time_minutes: Mapped[float] = mapped_column(Float, nullable=False)  # expected delay
    impact_radius_km: Mapped[float] = mapped_column(Float, nullable=False)    # affected radius
    traffic_volume_increase_pct: Mapped[float] = mapped_column(Float, nullable=False)  # %

    # Model metadata
    model_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)    # 0–1

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    event = relationship("Event", back_populates="prediction")

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} event_id={self.event_id} level={self.congestion_level}>"
