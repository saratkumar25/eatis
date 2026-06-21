"""
app/routers/copilot.py
───────────────────────
Gemini AI Copilot endpoint.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.ai_query import CopilotRequest, CopilotResponse
from app.services.copilot_service import ask_copilot

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/ask", response_model=CopilotResponse)
def ask(
    body: CopilotRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a natural language question to the Gemini AI Copilot.
    Optionally attach an event_id for contextual responses.
    """
    record = ask_copilot(
        query=body.query,
        event_id=body.event_id,
        user_id=current_user.id,
        db=db,
    )
    return CopilotResponse(
        query_id=record.id,
        user_query=record.user_query,
        gemini_response=record.gemini_response,
        event_id=record.event_id,
        created_at=record.created_at,
    )


@router.get("/history", response_model=list[CopilotResponse])
def history(
    event_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return AI Copilot query history for the current user."""
    from app.models.ai_query import AIQuery
    q = db.query(AIQuery).filter(AIQuery.user_id == current_user.id)
    if event_id:
        q = q.filter(AIQuery.event_id == event_id)
    records = q.order_by(AIQuery.created_at.desc()).limit(limit).all()
    return [
        CopilotResponse(
            query_id=r.id,
            user_query=r.user_query,
            gemini_response=r.gemini_response,
            event_id=r.event_id,
            created_at=r.created_at,
        )
        for r in records
    ]
