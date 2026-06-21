"""
app/main.py
────────────
FastAPI application factory.

Startup sequence:
  1. Create all DB tables (idempotent via CREATE IF NOT EXISTS).
  2. Seed admin user.
  3. Load (or train) XGBoost models.
  4. Mount all API routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, SessionLocal, check_db_connection, engine
from app.models import (  # noqa: F401 — register models with Base.metadata
    AIQuery, Event, PostEventAnalysis, Prediction, Resource, Route, User,
)
from app.routers import (
    analytics, auth, copilot, events, heatmap, post_event,
)
from app.services.auth_service import seed_admin_user

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("▶  EATIS backend starting up (env=%s)", settings.ENVIRONMENT)

    # 1. Verify DB connection
    if not check_db_connection():
        logger.error("❌  Cannot connect to PostgreSQL — check DATABASE_URL")
    else:
        logger.info("✅  Database connection verified")

    # 2. Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅  Database schema synchronised")

    # 3. Seed admin user
    with SessionLocal() as db:
        seed_admin_user(db)

    # 4. Load / train ML models
    from app.ml.predictor import predictor
    from app.ml.trainer import models_exist
    if settings.MODEL_RETRAIN_ON_STARTUP or not models_exist():
        logger.info("🧠  Training XGBoost models…")
        from app.ml.trainer import train_and_save
        train_and_save()
    predictor.load()
    logger.info("✅  XGBoost models ready")

    yield  # ←— app is now running

    logger.info("⏹  EATIS backend shutting down")


# ── Application factory ────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-Powered Event Traffic Intelligence System — "
            "predicts and manages congestion caused by public events."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(auth.router,       prefix=API_PREFIX)
    app.include_router(events.router,     prefix=API_PREFIX)
    app.include_router(heatmap.router,    prefix=API_PREFIX)
    app.include_router(copilot.router,    prefix=API_PREFIX)
    app.include_router(analytics.router,  prefix=API_PREFIX)
    app.include_router(post_event.router, prefix=API_PREFIX)

    # ── Health check ────────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    def health():
        db_ok = check_db_connection()
        return JSONResponse(
            status_code=200 if db_ok else 503,
            content={
                "status": "healthy" if db_ok else "degraded",
                "version": settings.APP_VERSION,
                "database": "connected" if db_ok else "unreachable",
            },
        )

    @app.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
        }

    return app


app = create_app()
