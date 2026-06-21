"""
app/services/heatmap_service.py
────────────────────────────────
Generates congestion heatmap data for Leaflet.heat consumption.

Strategy:
  1. Use the event's lat/lng as the epicentre.
  2. Spread points outward using a Gaussian decay based on impact_radius_km.
  3. Weight each point by the overall risk_score.
  4. Return coloured zone boundaries for the map legend.

One degree of latitude ≈ 111 km; longitude varies by cos(lat).
"""

from __future__ import annotations

import math
import random
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.prediction import Prediction
from app.schemas.ai_query import HeatmapPoint, HeatmapResponse

# Number of heatmap sample points to generate
_N_POINTS = 120

# Congestion zone thresholds (intensity 0-1)
_ZONES = [
    {"label": "Low",      "color": "green",  "min_intensity": 0.00, "max_intensity": 0.25},
    {"label": "Moderate", "color": "yellow", "min_intensity": 0.25, "max_intensity": 0.50},
    {"label": "High",     "color": "orange", "min_intensity": 0.50, "max_intensity": 0.75},
    {"label": "Critical", "color": "red",    "min_intensity": 0.75, "max_intensity": 1.00},
]

_LEVEL_TO_PEAK = {
    "low": 0.30,
    "medium": 0.55,
    "high": 0.78,
    "critical": 0.96,
}


def _km_to_deg_lat(km: float) -> float:
    return km / 111.0


def _km_to_deg_lon(km: float, lat: float) -> float:
    return km / (111.0 * math.cos(math.radians(lat)))


def generate_heatmap(event_id: int, db: Session) -> HeatmapResponse:
    event: Event | None = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    pred: Prediction | None = db.query(Prediction).filter(Prediction.event_id == event_id).first()
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction exists for this event. Call /predict first.",
        )

    peak_intensity = _LEVEL_TO_PEAK.get(pred.congestion_level.value, 0.5)
    radius_km = pred.impact_radius_km
    lat0, lon0 = event.latitude, event.longitude

    random.seed(event_id * 31337)
    points: list[HeatmapPoint] = []

    for _ in range(_N_POINTS):
        # Random distance and angle from epicentre
        dist_km = random.gauss(0, radius_km * 0.4)
        angle = random.uniform(0, 2 * math.pi)
        d_lat = _km_to_deg_lat(dist_km * math.sin(angle))
        d_lon = _km_to_deg_lon(dist_km * math.cos(angle), lat0)

        lat = lat0 + d_lat
        lon = lon0 + d_lon

        # Gaussian decay of intensity with distance
        norm_dist = abs(dist_km) / radius_km
        intensity = peak_intensity * math.exp(-2.5 * norm_dist ** 2)
        intensity = max(0.0, min(1.0, intensity + random.gauss(0, 0.03)))

        points.append(HeatmapPoint(lat=round(lat, 6), lng=round(lon, 6),
                                   intensity=round(intensity, 4)))

    # Epicentre point at max intensity
    points.append(HeatmapPoint(lat=lat0, lng=lon0, intensity=round(peak_intensity, 4)))

    return HeatmapResponse(
        event_id=event_id,
        points=points,
        congestion_level=pred.congestion_level.value,
        risk_score=pred.risk_score,
        impact_radius_km=radius_km,
        zones=_ZONES,
    )
