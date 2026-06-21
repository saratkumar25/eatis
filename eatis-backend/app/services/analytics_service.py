"""
app/services/analytics_service.py
───────────────────────────────────
Aggregation queries for the analytics dashboard.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.post_event import PostEventAnalysis
from app.models.prediction import Prediction
from app.models.resource import Resource
from app.schemas.analytics import AnalyticsDashboard, AnalyticsSummary, HighRiskZone, TrendPoint


def get_dashboard(db: Session) -> AnalyticsDashboard:
    # ── Event counts ───────────────────────────────────────────────────────────
    total = db.query(func.count(Event.id)).scalar() or 0
    active = db.query(func.count(Event.id)).filter(Event.status == EventStatus.ACTIVE).scalar() or 0
    completed = db.query(func.count(Event.id)).filter(Event.status == EventStatus.COMPLETED).scalar() or 0
    scheduled = db.query(func.count(Event.id)).filter(Event.status == EventStatus.SCHEDULED).scalar() or 0
    cancelled = db.query(func.count(Event.id)).filter(Event.status == EventStatus.CANCELLED).scalar() or 0

    # ── Events by type ─────────────────────────────────────────────────────────
    type_rows = db.query(Event.event_type, func.count(Event.id)).group_by(Event.event_type).all()
    events_by_type = {str(r[0].value): r[1] for r in type_rows}

    # ── Congestion distribution ────────────────────────────────────────────────
    level_rows = (
        db.query(Prediction.congestion_level, func.count(Prediction.id))
        .group_by(Prediction.congestion_level)
        .all()
    )
    congestion_dist = {str(r[0].value): r[1] for r in level_rows}

    # ── Risk scores ────────────────────────────────────────────────────────────
    high_risk = db.query(func.count(Prediction.id)).filter(Prediction.risk_score >= 70).scalar() or 0
    avg_risk = db.query(func.avg(Prediction.risk_score)).scalar() or 0.0

    # ── Prediction accuracy ────────────────────────────────────────────────────
    avg_acc = db.query(func.avg(PostEventAnalysis.prediction_accuracy_pct)).scalar()

    # ── Resource totals ────────────────────────────────────────────────────────
    totals = db.query(
        func.sum(Resource.officers_required),
        func.sum(Resource.barricades_required),
        func.sum(Resource.patrol_vehicles),
        func.sum(Resource.emergency_units),
    ).first()
    total_officers = int(totals[0] or 0)
    resources_allocated = {
        "officers": int(totals[0] or 0),
        "barricades": int(totals[1] or 0),
        "patrol_vehicles": int(totals[2] or 0),
        "emergency_units": int(totals[3] or 0),
    }

    summary = AnalyticsSummary(
        total_events=total,
        active_events=active,
        completed_events=completed,
        scheduled_events=scheduled,
        cancelled_events=cancelled,
        events_by_type=events_by_type,
        congestion_distribution=congestion_dist,
        high_risk_events=high_risk,
        avg_risk_score=round(float(avg_risk), 2),
        avg_prediction_accuracy=round(float(avg_acc), 2) if avg_acc else None,
        total_officers_deployed=total_officers,
        total_resources_allocated=resources_allocated,
    )

    # ── Trends (last 12 months, monthly) ──────────────────────────────────────
    trends: list[TrendPoint] = []
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = (
            db.query(func.count(Event.id))
            .filter(Event.start_datetime >= month_start, Event.start_datetime < month_end)
            .scalar()
            or 0
        )
        avg = (
            db.query(func.avg(Prediction.risk_score))
            .join(Event, Event.id == Prediction.event_id)
            .filter(Event.start_datetime >= month_start, Event.start_datetime < month_end)
            .scalar()
            or 0.0
        )
        trends.append(TrendPoint(
            period=month_start.strftime("%Y-%m"),
            event_count=count,
            avg_risk_score=round(float(avg), 2),
        ))

    # ── High-risk zones ────────────────────────────────────────────────────────
    zone_rows = (
        db.query(
            Event.location_name,
            func.avg(Event.latitude),
            func.avg(Event.longitude),
            func.count(Event.id),
            func.avg(Prediction.risk_score),
        )
        .join(Prediction, Prediction.event_id == Event.id)
        .group_by(Event.location_name)
        .having(func.avg(Prediction.risk_score) >= 60)
        .order_by(func.avg(Prediction.risk_score).desc())
        .limit(10)
        .all()
    )
    high_risk_zones = [
        HighRiskZone(
            location_name=r[0],
            latitude=round(r[1], 6),
            longitude=round(r[2], 6),
            event_count=r[3],
            avg_risk_score=round(r[4], 2),
        )
        for r in zone_rows
    ]

    return AnalyticsDashboard(
        summary=summary,
        trends=trends,
        high_risk_zones=high_risk_zones,
    )
