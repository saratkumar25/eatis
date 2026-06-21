"""
app/schemas/route.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.route import RouteType


class RouteResponse(BaseModel):
    id: int
    event_id: int
    route_type: RouteType
    route_name: str
    description: Optional[str]
    geojson_coordinates: Optional[str]
    distance_km: Optional[float]
    estimated_time_minutes: Optional[int]
    diversion_benefit: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
