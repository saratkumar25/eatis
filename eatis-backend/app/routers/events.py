"""
app/routers/events.py
──────────────────────
Event CRUD + simulation endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    AnalystOrAbove, OperatorOrAbove, get_current_user, require_role,
)
from app.database import get_db
from app.models.event import EventStatus, EventType
from app.models.user import User, UserRole
from app.schemas.event import EventCreate, EventResponse, EventSimulateRequest, EventUpdate
from app.services import event_service, prediction_service, resource_service, route_service
from app.schemas.prediction import PredictionResponse
from app.schemas.resource import ResourceResponse
from app.schemas.route import RouteResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new event and automatically generate prediction + resources + routes."""
    event = event_service.create_event(data, current_user, db)

    # Auto-run the full pipeline
    pred = prediction_service.run_prediction(event, db)
    resource_service.allocate_resources(event.id, db)
    route_service.generate_routes(event.id, db)

    return event


@router.get("", response_model=dict)
def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[EventStatus] = Query(None, alias="status"),
    event_type: Optional[EventType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List events with optional filters and pagination."""
    events, total = event_service.list_events(db, skip, limit, status_filter,
                                               event_type.value if event_type else None)
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [EventResponse.model_validate(e) for e in events],
    }


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return event_service.get_event(event_id, db)


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    data: EventUpdate,
    current_user: User = Depends(OperatorOrAbove),
    db: Session = Depends(get_db),
):
    return event_service.update_event(event_id, data, db)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    event_service.delete_event(event_id, db)


# ── Nested resource endpoints ───────────────────────────────────────────────────

@router.get("/{event_id}/prediction", response_model=PredictionResponse)
def get_prediction(event_id: int, current_user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    return prediction_service.get_prediction(event_id, db)


@router.post("/{event_id}/predict", response_model=PredictionResponse)
def run_prediction(event_id: int, current_user: User = Depends(OperatorOrAbove),
                   db: Session = Depends(get_db)):
    """Re-run the XGBoost prediction for an existing event."""
    event = event_service.get_event(event_id, db)
    return prediction_service.run_prediction(event, db)


@router.get("/{event_id}/resources", response_model=ResourceResponse)
def get_resources(event_id: int, current_user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return resource_service.get_resources(event_id, db)


@router.post("/{event_id}/resources/allocate", response_model=ResourceResponse)
def allocate_resources(event_id: int, current_user: User = Depends(OperatorOrAbove),
                       db: Session = Depends(get_db)):
    """Re-compute resource allocation for an event."""
    return resource_service.allocate_resources(event_id, db)


@router.get("/{event_id}/routes", response_model=list[RouteResponse])
def get_routes(event_id: int, current_user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    return route_service.get_routes(event_id, db)


@router.post("/{event_id}/routes/generate", response_model=list[RouteResponse])
def generate_routes(event_id: int, current_user: User = Depends(OperatorOrAbove),
                    db: Session = Depends(get_db)):
    """Re-generate diversion routes for an event."""
    return route_service.generate_routes(event_id, db)


# ── Simulation endpoint ────────────────────────────────────────────────────────

@router.post("/simulate", response_model=dict)
def simulate_event(
    data: EventSimulateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Simulate an event WITHOUT persisting it.
    Returns prediction, resource estimate, and heatmap preview data.
    """
    from app.ml.predictor import predictor
    from app.services.resource_service import _compute_resources
    from app.models.event import Event as EventModel, EventType as ET
    from app.models.prediction import Prediction as PredModel, CongestionLevel

    result = predictor.predict(
        event_type=data.event_type.value,
        crowd_size=data.expected_crowd_size,
        duration_hours=data.duration_hours,
        start_datetime=data.start_datetime,
        has_road_closure=data.has_road_closure,
    )

    # Build a transient event/prediction for resource calc
    mock_event = EventModel(
        event_type=data.event_type,
        expected_crowd_size=data.expected_crowd_size,
        duration_hours=data.duration_hours,
        has_road_closure=data.has_road_closure,
        location_name="Simulation",
        latitude=data.latitude,
        longitude=data.longitude,
    )
    mock_pred = PredModel(
        congestion_level=CongestionLevel(result.congestion_level),
        risk_score=result.risk_score,
        impact_radius_km=result.impact_radius_km,
    )
    resources = _compute_resources(mock_event, mock_pred)

    return {
        "simulation": True,
        "input": data.model_dump(),
        "prediction": {
            "congestion_level": result.congestion_level,
            "risk_score": result.risk_score,
            "delay_time_minutes": result.delay_time_minutes,
            "impact_radius_km": result.impact_radius_km,
            "traffic_volume_increase_pct": result.traffic_volume_increase_pct,
            "confidence_score": result.confidence_score,
        },
        "recommended_resources": resources,
    }
