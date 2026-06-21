"""
app/services/copilot_service.py
────────────────────────────────
Gemini 2.5 Flash integration for the AI Traffic Copilot.

The service:
  1. Builds a rich system prompt with EATIS context.
  2. Optionally injects event + prediction data as context.
  3. Calls the Gemini API.
  4. Persists the Q&A pair to ai_queries for auditing.
"""

from __future__ import annotations

import logging
from typing import Optional

import google.generativeai as genai
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.ai_query import AIQuery
from app.models.event import Event
from app.models.prediction import Prediction
from app.models.resource import Resource

logger = logging.getLogger(__name__)

# Initialise Gemini client once at import time
_gemini_configured = False


def _configure_gemini() -> None:
    global _gemini_configured
    if not _gemini_configured:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GEMINI_API_KEY is not configured. Please set it in your environment.",
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_configured = True


_SYSTEM_PROMPT = """You are EATIS Copilot — an expert AI assistant for traffic authorities managing
public event congestion.

Your role is to:
• Analyse traffic congestion caused by public events.
• Recommend optimal resource deployment (officers, barricades, patrol vehicles, emergency units).
• Suggest route diversions and traffic flow management strategies.
• Explain AI prediction results in plain, actionable language.
• Generate concise event traffic management reports.
• Answer operational questions from traffic control officers and planners.

Your tone: professional, precise, and actionable. Use bullet points for recommendations.
Always prioritise public safety and emergency vehicle access.
"""


def _build_context_block(event: Optional[Event], pred: Optional[Prediction],
                         resource: Optional[Resource]) -> str:
    if not event:
        return ""
    lines = [
        f"\n## Active Event Context",
        f"- **Event:** {event.name} ({event.event_type.value.replace('_', ' ').title()})",
        f"- **Location:** {event.location_name} ({event.latitude:.4f}, {event.longitude:.4f})",
        f"- **Date/Time:** {event.start_datetime.strftime('%Y-%m-%d %H:%M')} → {event.end_datetime.strftime('%H:%M')}",
        f"- **Expected Crowd:** {event.expected_crowd_size:,} people",
        f"- **Duration:** {event.duration_hours:.1f} hours",
        f"- **Road Closure:** {'Yes — ' + (event.road_closure_details or 'details not provided') if event.has_road_closure else 'No'}",
    ]
    if pred:
        lines += [
            f"\n## AI Prediction Results",
            f"- **Congestion Level:** {pred.congestion_level.value.upper()}",
            f"- **Risk Score:** {pred.risk_score:.1f}/100",
            f"- **Expected Delay:** {pred.delay_time_minutes:.0f} minutes",
            f"- **Impact Radius:** {pred.impact_radius_km:.1f} km",
            f"- **Traffic Volume Increase:** +{pred.traffic_volume_increase_pct:.0f}%",
            f"- **Model Confidence:** {pred.confidence_score * 100:.1f}%",
        ]
    if resource:
        lines += [
            f"\n## Resource Allocation Recommendation",
            f"- Officers: {resource.officers_required}",
            f"- Barricades: {resource.barricades_required}",
            f"- Patrol Vehicles: {resource.patrol_vehicles}",
            f"- Emergency Units: {resource.emergency_units}",
            f"- Tow Vehicles: {resource.tow_vehicles}",
        ]
    return "\n".join(lines)


def ask_copilot(
    query: str,
    event_id: Optional[int],
    user_id: Optional[int],
    db: Session,
) -> AIQuery:
    _configure_gemini()

    # Load context if event_id provided
    event = pred = resource = None
    if event_id:
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            pred = db.query(Prediction).filter(Prediction.event_id == event_id).first()
            resource = db.query(Resource).filter(Resource.event_id == event_id).first()

    context_block = _build_context_block(event, pred, resource)

    if not event_id:
        from app.models.event import EventStatus
        recent_events = (
            db.query(Event)
            .filter(Event.status.in_([EventStatus.ACTIVE, EventStatus.SCHEDULED]))
            .order_by(Event.start_datetime)
            .limit(10)
            .all()
        )
        if recent_events:
            context_block += "\n## Global Context: Active & Upcoming Events in the System\n"
            context_block += "IMPORTANT: The following events are currently active or scheduled. If the user asks for a list or details of events, ALWAYS provide them directly from this list. Do NOT tell them to check the dashboard.\n"
            for e in recent_events:
                context_block += f"- ID {e.id}: '{e.name}' ({e.event_type.value}) at {e.location_name} (Starts: {e.start_datetime.strftime('%Y-%m-%d %H:%M')}, Status: {e.status.value.upper()})\n"

    full_prompt = f"{_SYSTEM_PROMPT}\n{context_block}\n\n## User Query\n{query}"

    try:
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(full_prompt)
        answer = response.text
        # Count tokens if available
        tokens_used = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens_used = getattr(response.usage_metadata, "total_token_count", None)
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error: {str(exc)}",
        )

    record = AIQuery(
        event_id=event_id,
        user_id=user_id,
        user_query=query,
        gemini_response=answer,
        tokens_used=tokens_used,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
