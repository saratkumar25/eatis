"""
app/models/post_event.py
─────────────────────────
Post-event analysis: compares predicted vs actual impact.
Used for model accuracy tracking and continuous improvement.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PostEventAnalysis(Base):
    __tablename__ = "post_event_analysis"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), unique=True, index=True
    )

    # Predicted values (copied from Prediction at time of analysis)
    predicted_congestion_level: Mapped[str] = mapped_column(String(20), nullable=False)
    predicted_risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_delay_minutes: Mapped[float] = mapped_column(Float, nullable=False)

    # Actual recorded values (entered by operators post-event)
    actual_congestion_level: Mapped[str] = mapped_column(String(20), nullable=False)
    actual_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_delay_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_crowd_size: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Accuracy metrics
    prediction_accuracy_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    congestion_match: Mapped[bool | None] = mapped_column(nullable=True)

    # AI-generated insights
    performance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    analyzed_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    event = relationship("Event", back_populates="post_event_analysis")

    def __repr__(self) -> str:
        return f"<PostEventAnalysis id={self.id} event_id={self.event_id} accuracy={self.prediction_accuracy_pct}>"
