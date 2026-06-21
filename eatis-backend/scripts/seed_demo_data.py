#!/usr/bin/env python
"""
scripts/seed_demo_data.py
────────────────────────────
Populates the database with a handful of realistic demo events,
running the full prediction → resource → route pipeline for each.
Useful for hackathon demos and frontend development.

Usage:
    python scripts/seed_demo_data.py
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.ml.predictor import predictor
from app.models.event import Event, EventType
from app.models.user import User, UserRole
from app.services import event_service, prediction_service, resource_service, route_service
from app.services.auth_service import seed_admin_user
from app.schemas.event import EventCreate

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)

DEMO_EVENTS = [
    dict(
        name="City Marathon 2026",
        event_type=EventType.MARATHON,
        location_name="Downtown Riverside Park",
        latitude=28.6139, longitude=77.2090,
        start_datetime=datetime.utcnow() + timedelta(days=5, hours=2),
        end_datetime=datetime.utcnow() + timedelta(days=5, hours=7),
        expected_crowd_size=25000,
        has_road_closure=True,
        road_closure_details="Main Street closed from 6 AM to 1 PM",
    ),
    dict(
        name="Independence Day Political Rally",
        event_type=EventType.POLITICAL_RALLY,
        location_name="Central Plaza",
        latitude=28.6304, longitude=77.2177,
        start_datetime=datetime.utcnow() + timedelta(days=10, hours=4),
        end_datetime=datetime.utcnow() + timedelta(days=10, hours=8),
        expected_crowd_size=10000,
        has_road_closure=True,
        road_closure_details="Plaza approach roads closed 2 hrs before event",
    ),
    dict(
        name="Summer Music Festival",
        event_type=EventType.MUSIC_FESTIVAL,
        location_name="Lakeside Amphitheatre",
        latitude=28.5921, longitude=77.0460,
        start_datetime=datetime.utcnow() + timedelta(days=14, hours=6),
        end_datetime=datetime.utcnow() + timedelta(days=14, hours=14),
        expected_crowd_size=50000,
        has_road_closure=False,
    ),
    dict(
        name="Metro Bridge Construction Phase 2",
        event_type=EventType.CONSTRUCTION,
        location_name="5th Avenue Bridge",
        latitude=28.6448, longitude=77.2167,
        start_datetime=datetime.utcnow() + timedelta(days=2),
        end_datetime=datetime.utcnow() + timedelta(days=32),
        expected_crowd_size=200,
        has_road_closure=True,
        road_closure_details="One lane closed for 30 days",
    ),
    dict(
        name="Inter-City Football Final",
        event_type=EventType.SPORTS_EVENT,
        location_name="National Stadium",
        latitude=28.5733, longitude=77.2497,
        start_datetime=datetime.utcnow() + timedelta(days=7, hours=5),
        end_datetime=datetime.utcnow() + timedelta(days=7, hours=8),
        expected_crowd_size=60000,
        has_road_closure=False,
    ),
]


def main():
    predictor.load()
    db = SessionLocal()
    try:
        seed_admin_user(db)
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()

        for raw in DEMO_EVENTS:
            existing = db.query(Event).filter(Event.name == raw["name"]).first()
            if existing:
                logger.info("Skipping existing event: %s", raw["name"])
                continue

            data = EventCreate(**raw)
            event = event_service.create_event(data, admin, db)
            prediction_service.run_prediction(event, db)
            resource_service.allocate_resources(event.id, db)
            route_service.generate_routes(event.id, db)
            logger.info("Seeded event #%d: %s", event.id, event.name)

        logger.info("Demo data seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
