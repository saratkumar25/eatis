"""
app/models/ai_query.py
───────────────────────
Logs every interaction with the Gemini AI Copilot.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIQuery(Base):
    __tablename__ = "ai_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    gemini_response: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    event = relationship("Event", back_populates="ai_queries")
    user = relationship("User", back_populates="ai_queries")

    def __repr__(self) -> str:
        return f"<AIQuery id={self.id} event_id={self.event_id}>"
