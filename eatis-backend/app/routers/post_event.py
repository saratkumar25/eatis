"""
app/routers/post_event.py
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import OperatorOrAbove, get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.post_event import PostEventCreate, PostEventResponse
from app.services.post_event_service import get_post_event, submit_post_event

router = APIRouter(prefix="/post-event", tags=["Post-Event Analysis"])


@router.post("/{event_id}", response_model=PostEventResponse, status_code=status.HTTP_201_CREATED)
def submit(
    event_id: int,
    data: PostEventCreate,
    current_user: User = Depends(OperatorOrAbove),
    db: Session = Depends(get_db),
):
    """Submit actual event outcome data for post-event analysis."""
    return submit_post_event(event_id, data, db)


@router.get("/{event_id}", response_model=PostEventResponse)
def get_analysis(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the post-event analysis for a completed event."""
    return get_post_event(event_id, db)
