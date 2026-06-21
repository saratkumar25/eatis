"""
app/routers/analytics.py
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import AnalystOrAbove
from app.database import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsDashboard
from app.services.analytics_service import get_dashboard

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
def dashboard(
    current_user: User = Depends(AnalystOrAbove),
    db: Session = Depends(get_db),
):
    """Return aggregated analytics for the dashboard."""
    return get_dashboard(db)
