"""
app/services/event_service.py
──────────────────────────────
CRUD and business logic for events.
Automatically triggers prediction, resource allocation, heatmap,
and route generation after a new event is created.
"""

import math
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.user import User
from app.schemas.event import EventCreate, EventUpdate


def create_event(data: EventCreate, current_user: User, db: Session) -> Event:
    """Persist a new event and compute derived fields."""
    duration_hours = (data.end_datetime - data.start_datetime).total_seconds() / 3600.0

    event = Event(
        name=data.name,
        event_type=data.event_type,
        description=data.description,
        location_name=data.location_name,
        latitude=data.latitude,
        longitude=data.longitude,
        address=data.address,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        duration_hours=round(duration_hours, 2),
        expected_crowd_size=data.expected_crowd_size,
        has_road_closure=data.has_road_closure,
        road_closure_details=data.road_closure_details,
        created_by=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(event_id: int, db: Session) -> Event:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


def list_events(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status_filter: EventStatus | None = None,
    event_type_filter: str | None = None,
) -> tuple[list[Event], int]:
    q = db.query(Event)
    if status_filter:
        q = q.filter(Event.status == status_filter)
    if event_type_filter:
        q = q.filter(Event.event_type == event_type_filter)
    total = q.count()
    events = q.order_by(Event.start_datetime.desc()).offset(skip).limit(limit).all()
    return events, total


def update_event(event_id: int, data: EventUpdate, db: Session) -> Event:
    event = get_event(event_id, db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
    # Recalculate duration if times changed
    if "start_datetime" in update_data or "end_datetime" in update_data:
        delta = (event.end_datetime - event.start_datetime).total_seconds()
        event.duration_hours = round(delta / 3600.0, 2)
    db.commit()
    db.refresh(event)
    return event


def delete_event(event_id: int, db: Session) -> None:
    event = get_event(event_id, db)
    db.delete(event)
    db.commit()


def get_active_events(db: Session) -> list[Event]:
    """Return events currently in progress."""
    now = datetime.utcnow()
    return (
        db.query(Event)
        .filter(Event.start_datetime <= now, Event.end_datetime >= now,
                Event.status == EventStatus.ACTIVE)
        .all()
    )
