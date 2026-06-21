"""
app/ml/predictor.py
────────────────────
Loads trained XGBoost models from disk and exposes a single
`predict()` function for runtime inference.

The predictor is a module-level singleton; models are loaded once
on first import and cached for the application lifetime.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from xgboost import XGBClassifier, XGBRegressor

from app.ml.features import build_feature_vector
from app.ml.trainer import (
    CLF_PATH, REG_RISK_PATH, REG_DELAY_PATH, REG_RADIUS_PATH,
    SCALER_PATH, METADATA_PATH, models_exist, train_and_save,
)

logger = logging.getLogger(__name__)

_CLASS_LABELS = ["low", "medium", "high", "critical"]


@dataclass
class PredictionResult:
    congestion_level: str       # low / medium / high / critical
    congestion_class: int       # 0-3
    risk_score: float           # 0-100
    delay_time_minutes: float
    impact_radius_km: float
    traffic_volume_increase_pct: float
    confidence_score: float     # 0-1
    model_version: str


class CongestionPredictor:
    """
    Wraps the four XGBoost models and exposes a single `predict()` method.
    Thread-safe for read-only prediction workloads (models are never mutated).
    """

    def __init__(self) -> None:
        self._loaded = False
        self._clf: XGBClassifier | None = None
        self._reg_risk: XGBRegressor | None = None
        self._reg_delay: XGBRegressor | None = None
        self._reg_radius: XGBRegressor | None = None
        self._scaler = None
        self._version = "1.0.0"

    def load(self) -> None:
        """Load (or lazily train) the models."""
        if not models_exist():
            logger.warning("No trained models found — training from scratch…")
            meta = train_and_save()
            self._version = meta.get("model_version", "1.0.0")

        logger.info("Loading XGBoost models from disk…")
        self._clf = XGBClassifier()
        self._clf.load_model(str(CLF_PATH))

        self._reg_risk = XGBRegressor()
        self._reg_risk.load_model(str(REG_RISK_PATH))

        self._reg_delay = XGBRegressor()
        self._reg_delay.load_model(str(REG_DELAY_PATH))

        self._reg_radius = XGBRegressor()
        self._reg_radius.load_model(str(REG_RADIUS_PATH))

        self._scaler = joblib.load(SCALER_PATH)

        if METADATA_PATH.exists():
            meta = json.loads(METADATA_PATH.read_text())
            self._version = meta.get("model_version", "1.0.0")

        self._loaded = True
        logger.info("All models loaded successfully (version=%s)", self._version)

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def predict(
        self,
        event_type: str,
        crowd_size: int,
        duration_hours: float,
        start_datetime: datetime,
        has_road_closure: bool,
    ) -> PredictionResult:
        """
        Run inference on a single event and return a PredictionResult.
        """
        self._ensure_loaded()

        X = build_feature_vector(
            event_type=event_type,
            crowd_size=crowd_size,
            duration_hours=duration_hours,
            start_datetime=start_datetime,
            has_road_closure=has_road_closure,
        )
        X_scaled = self._scaler.transform(X)

        # Classification
        cls_proba = self._clf.predict_proba(X_scaled)[0]  # shape (4,)
        cls_idx = int(np.argmax(cls_proba))
        confidence = float(cls_proba[cls_idx])
        congestion_level = _CLASS_LABELS[cls_idx]

        # Regression outputs — clip to sensible bounds
        risk = float(np.clip(self._reg_risk.predict(X_scaled)[0], 0, 100))
        delay = float(np.clip(self._reg_delay.predict(X_scaled)[0], 0, 180))
        radius = float(np.clip(self._reg_radius.predict(X_scaled)[0], 0.1, 15))

        # Derived: traffic volume increase (heuristic)
        volume_pct = risk * 1.5  # rough linear approximation

        return PredictionResult(
            congestion_level=congestion_level,
            congestion_class=cls_idx,
            risk_score=round(risk, 2),
            delay_time_minutes=round(delay, 1),
            impact_radius_km=round(radius, 2),
            traffic_volume_increase_pct=round(volume_pct, 1),
            confidence_score=round(confidence, 4),
            model_version=self._version,
        )


# ── Module-level singleton ──────────────────────────────────────────────────────
predictor = CongestionPredictor()
