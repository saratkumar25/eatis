"""
app/schemas/analytics.py
"""
from typing import Any
from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_events: int
    active_events: int
    completed_events: int
    scheduled_events: int
    cancelled_events: int
    events_by_type: dict[str, int]
    congestion_distribution: dict[str, int]
    high_risk_events: int
    avg_risk_score: float
    avg_prediction_accuracy: float | None
    total_officers_deployed: int
    total_resources_allocated: dict[str, int]


class TrendPoint(BaseModel):
    period: str
    event_count: int
    avg_risk_score: float


class HighRiskZone(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    event_count: int
    avg_risk_score: float


class AnalyticsDashboard(BaseModel):
    summary: AnalyticsSummary
    trends: list[TrendPoint]
    high_risk_zones: list[HighRiskZone]
