"""
app/services/prediction_service.py
────────────────────────────────────
Orchestrates XGBoost inference and persists the results.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ml.predictor import predictor
from app.models.event import Event
from app.models.prediction import CongestionLevel, Prediction


def run_prediction(event: Event, db: Session) -> Prediction:
    """
    Run XGBoost inference for the given event, upsert the Prediction row,
    and return the persisted ORM object.
    """
    result = predictor.predict(
        event_type=event.event_type.value,
        crowd_size=event.expected_crowd_size,
        duration_hours=event.duration_hours,
        start_datetime=event.start_datetime,
        has_road_closure=event.has_road_closure,
    )

    pred = db.query(Prediction).filter(Prediction.event_id == event.id).first()
    if pred is None:
        pred = Prediction(event_id=event.id)
        db.add(pred)

    pred.congestion_level = CongestionLevel(result.congestion_level)
    pred.risk_score = result.risk_score
    pred.delay_time_minutes = result.delay_time_minutes
    pred.impact_radius_km = result.impact_radius_km
    pred.traffic_volume_increase_pct = result.traffic_volume_increase_pct
    pred.confidence_score = result.confidence_score
    pred.model_version = result.model_version

    db.commit()
    db.refresh(pred)
    return pred


def get_prediction(event_id: int, db: Session) -> Prediction:
    pred = db.query(Prediction).filter(Prediction.event_id == event_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found for this event. Run /predict first.",
        )
    return pred
