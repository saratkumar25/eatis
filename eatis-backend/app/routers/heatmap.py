"""
app/routers/heatmap.py
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.ai_query import HeatmapResponse
from app.services.heatmap_service import generate_heatmap

router = APIRouter(prefix="/heatmap", tags=["Heatmap"])


@router.get("/{event_id}", response_model=HeatmapResponse)
def get_heatmap(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return congestion heatmap data for a specific event.
    Format: list of [lat, lng, intensity] points consumed by Leaflet.heat.
    """
    return generate_heatmap(event_id, db)
