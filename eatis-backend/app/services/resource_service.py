"""
app/services/resource_service.py
──────────────────────────────────
Deterministic resource allocation engine.

Formula basis (customisable by traffic authority):
  Officers       = base × crowd_factor × closure_factor × level_multiplier
  Barricades     = officers × 0.60
  Patrol vehicles= ceil(officers / 6)
  Emergency units= ceil(officers / 10)
  Tow vehicles   = base depending on duration/closure
"""

import math
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.prediction import Prediction
from app.models.resource import Resource

# Minimum resources regardless of prediction
_MIN_OFFICERS = 2
_MIN_BARRICADES = 4
_MIN_PATROL = 1

# Level multipliers — calibrated to real Bangalore BBMP/police deployments
_LEVEL_MULT = {
    "low":      1.0,
    "medium":   1.3,
    "high":     1.7,
    "critical": 2.2,
}

# Officers per 1,000 attendees (base rate before multipliers)
# Source: Bangalore Police deployment guidelines for public events
_TYPE_OFFICER_RATE = {
    "political_rally":      2.5,
    "sports_event":         1.8,   # stadium has own security
    "music_festival":       1.5,
    "cultural_event":       1.0,
    "religious_gathering":  1.2,
    "construction":         0.8,
    "public_demonstration": 3.0,
    "marathon":             1.0,
    "parade":               1.2,
    "exhibition":           0.8,
    "other":                1.0,
}

# Absolute caps to prevent unrealistic numbers
_MAX_OFFICERS = 400
_MAX_BARRICADES = 250


def _compute_resources(event: Event, pred: Prediction) -> dict:
    crowd_k = event.expected_crowd_size / 1000.0
    rate = _TYPE_OFFICER_RATE.get(event.event_type.value, 1.0)
    level_mult = _LEVEL_MULT.get(pred.congestion_level.value, 1.0)
    closure_mult = 1.15 if event.has_road_closure else 1.0

    raw_officers = crowd_k * rate * level_mult * closure_mult
    officers  = max(_MIN_OFFICERS, min(_MAX_OFFICERS, math.ceil(raw_officers)))
    barricades = max(_MIN_BARRICADES, min(_MAX_BARRICADES, math.ceil(officers * 0.55)))
    patrol    = max(_MIN_PATROL, math.ceil(officers / 8))
    emergency = max(1, math.ceil(officers / 15))
    tow       = max(1, math.ceil(patrol * 0.4))

    notes_parts = [
        f"Deploy {officers} officers around {event.location_name}.",
        f"Install {barricades} barricades on approach roads.",
        f"{patrol} patrol vehicles to cover {pred.impact_radius_km:.1f} km radius.",
        f"{emergency} emergency response unit(s) on standby.",
    ]
    if event.has_road_closure:
        notes_parts.append("Coordinate with road-closure authorities for detour signage.")
    if pred.congestion_level.value in ("high", "critical"):
        notes_parts.append("Activate emergency traffic management protocol.")

    return {
        "officers_required": officers,
        "barricades_required": barricades,
        "patrol_vehicles": patrol,
        "emergency_units": emergency,
        "tow_vehicles": tow,
        "deployment_notes": " ".join(notes_parts),
    }


def allocate_resources(event_id: int, db: Session) -> Resource:
    event: Optional[Event] = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    pred: Optional[Prediction] = db.query(Prediction).filter(Prediction.event_id == event_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found. Run /predict first.",
        )

    values = _compute_resources(event, pred)

    resource = db.query(Resource).filter(Resource.event_id == event_id).first()
    if resource is None:
        resource = Resource(event_id=event_id)
        db.add(resource)

    for key, val in values.items():
        setattr(resource, key, val)

    db.commit()
    db.refresh(resource)
    return resource


def get_resources(event_id: int, db: Session) -> Resource:
    r = db.query(Resource).filter(Resource.event_id == event_id).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource allocation not found for this event.",
        )
    return r
