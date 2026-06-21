"""
app/schemas/prediction.py
──────────────────────────
"""
from datetime import datetime
from pydantic import BaseModel
from app.models.prediction import CongestionLevel


class PredictionResponse(BaseModel):
    id: int
    event_id: int
    congestion_level: CongestionLevel
    risk_score: float
    delay_time_minutes: float
    impact_radius_km: float
    traffic_volume_increase_pct: float
    confidence_score: float
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}
