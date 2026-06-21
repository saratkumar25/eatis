"""
app/schemas/ai_query.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CopilotRequest(BaseModel):
    query: str
    event_id: Optional[int] = None  # optional context


class CopilotResponse(BaseModel):
    query_id: int
    user_query: str
    gemini_response: str
    event_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Heatmap ────────────────────────────────────────────────────────────────────

class HeatmapPoint(BaseModel):
    """Single point in the heatmap layer: [lat, lng, intensity 0-1]."""
    lat: float
    lng: float
    intensity: float   # 0.0 = no congestion, 1.0 = critical

    def to_list(self) -> list:
        return [self.lat, self.lng, self.intensity]


class HeatmapResponse(BaseModel):
    event_id: int
    points: list[HeatmapPoint]
    congestion_level: str
    risk_score: float
    impact_radius_km: float
    zones: list[dict]   # coloured zone summaries for legend
