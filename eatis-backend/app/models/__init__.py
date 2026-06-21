"""
app/models/__init__.py
───────────────────────
Import all models here so Alembic can discover them via Base.metadata.
"""

from app.models.user import User, UserRole
from app.models.event import Event, EventType, EventStatus
from app.models.prediction import Prediction, CongestionLevel
from app.models.resource import Resource
from app.models.route import Route, RouteType
from app.models.ai_query import AIQuery
from app.models.post_event import PostEventAnalysis

__all__ = [
    "User", "UserRole",
    "Event", "EventType", "EventStatus",
    "Prediction", "CongestionLevel",
    "Resource",
    "Route", "RouteType",
    "AIQuery",
    "PostEventAnalysis",
]
