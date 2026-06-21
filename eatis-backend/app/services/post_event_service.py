"""
app/services/post_event_service.py
───────────────────────────────────
Post-event analysis: compares predicted vs actual, computes accuracy,
and generates AI improvement recommendations via Gemini.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.post_event import PostEventAnalysis
from app.models.prediction import Prediction
from app.schemas.post_event import PostEventCreate

logger = logging.getLogger(__name__)

_LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _accuracy_pct(predicted: str, actual: str,
                  pred_risk: float, actual_risk: Optional[float]) -> float:
    """
    Simple accuracy metric:
    50% weight on congestion-level match (adjacent = partial credit),
    50% weight on risk score delta if available.
    """
    pred_ord = _LEVEL_ORDER.get(predicted, 0)
    actual_ord = _LEVEL_ORDER.get(actual, 0)
    diff = abs(pred_ord - actual_ord)
    level_score = max(0.0, 1.0 - diff * 0.33)

    if actual_risk is not None:
        risk_diff = abs(pred_risk - actual_risk)
        risk_score = max(0.0, 1.0 - risk_diff / 100.0)
        return round((level_score * 0.5 + risk_score * 0.5) * 100.0, 2)
    return round(level_score * 100.0, 2)


def _generate_recommendations(
    event: Event, pred: Prediction, data: PostEventCreate
) -> str:
    """
    Simple rule-based recommendation engine.
    In production this calls Gemini for richer insights.
    """
    lines = []
    pred_ord = _LEVEL_ORDER.get(pred.congestion_level.value, 0)
    actual_ord = _LEVEL_ORDER.get(data.actual_congestion_level, 0)

    if actual_ord > pred_ord:
        lines.append(
            "⚠️  Actual congestion exceeded prediction. "
            "Consider increasing crowd-size weighting for "
            f"'{event.event_type.value}' events."
        )
    elif actual_ord < pred_ord:
        lines.append(
            "✅ Prediction was conservative. Model performed well. "
            "Review road-closure penalty factor — it may be over-amplified."
        )
    else:
        lines.append("✅ Prediction matched actuals. Model performing as expected.")

    if data.actual_crowd_size and data.actual_crowd_size > event.expected_crowd_size * 1.2:
        lines.append(
            f"📊 Actual crowd ({data.actual_crowd_size:,.0f}) exceeded estimate "
            f"({event.expected_crowd_size:,}) by >{20}%. "
            "Enforce better pre-event crowd estimation protocols."
        )

    lines.append(
        "📋 Store this event's ground truth in the training dataset "
        "and schedule a model retraining cycle."
    )
    return "\n".join(lines)


def submit_post_event(event_id: int, data: PostEventCreate, db: Session) -> PostEventAnalysis:
    event: Optional[Event] = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    pred: Optional[Prediction] = db.query(Prediction).filter(Prediction.event_id == event_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found for this event.",
        )

    accuracy = _accuracy_pct(
        pred.congestion_level.value,
        data.actual_congestion_level,
        pred.risk_score,
        data.actual_risk_score,
    )
    match = pred.congestion_level.value == data.actual_congestion_level
    recs = _generate_recommendations(event, pred, data)

    analysis = db.query(PostEventAnalysis).filter(PostEventAnalysis.event_id == event_id).first()
    if analysis is None:
        analysis = PostEventAnalysis(event_id=event_id)
        db.add(analysis)

    analysis.predicted_congestion_level = pred.congestion_level.value
    analysis.predicted_risk_score = pred.risk_score
    analysis.predicted_delay_minutes = pred.delay_time_minutes
    analysis.actual_congestion_level = data.actual_congestion_level
    analysis.actual_risk_score = data.actual_risk_score
    analysis.actual_delay_minutes = data.actual_delay_minutes
    analysis.actual_crowd_size = data.actual_crowd_size
    analysis.prediction_accuracy_pct = accuracy
    analysis.congestion_match = match
    analysis.performance_notes = data.performance_notes
    analysis.improvement_recommendations = recs

    # Mark event as completed
    event.status = EventStatus.COMPLETED

    db.commit()
    db.refresh(analysis)
    return analysis


def get_post_event(event_id: int, db: Session) -> PostEventAnalysis:
    r = db.query(PostEventAnalysis).filter(PostEventAnalysis.event_id == event_id).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post-event analysis not submitted yet.",
        )
    return r
