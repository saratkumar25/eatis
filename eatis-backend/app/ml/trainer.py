"""
app/ml/trainer.py
──────────────────
Trains an XGBoost multi-output regression model for congestion prediction.

Because no real historical dataset ships with the codebase, a realistic
synthetic dataset is generated first.  When actual post-event records
accumulate in the database, call `retrain_from_db()` to update the model.

Outputs (4 regression targets):
  • congestion_class  (0=Low, 1=Medium, 2=High, 3=Critical)
  • risk_score        (0–100)
  • delay_minutes     (0–180)
  • impact_radius_km  (0.1–15)
"""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier, XGBRegressor

from app.ml.features import (
    FEATURE_NAMES,
    EVENT_TYPE_MAP,
    build_feature_vector,
    build_training_dataframe,
)

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_DIR = Path(os.getenv("MODEL_DIR", "./models"))
CLF_PATH = MODEL_DIR / "congestion_classifier.json"
REG_RISK_PATH = MODEL_DIR / "risk_score_regressor.json"
REG_DELAY_PATH = MODEL_DIR / "delay_regressor.json"
REG_RADIUS_PATH = MODEL_DIR / "radius_regressor.json"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
METADATA_PATH = MODEL_DIR / "metadata.json"

# ── Synthetic data generation ──────────────────────────────────────────────────

_EVENT_TYPES = list(EVENT_TYPE_MAP.keys())

# Base congestion tendencies per event type (crowd multiplier, road-impact multiplier)
_TYPE_RISK_BASE = {
    "political_rally":      (0.8, 0.9),
    "sports_event":         (0.75, 0.85),
    "music_festival":       (0.70, 0.80),
    "cultural_event":       (0.50, 0.60),
    "religious_gathering":  (0.65, 0.70),
    "construction":         (0.40, 0.85),
    "public_demonstration": (0.80, 0.90),
    "marathon":             (0.60, 0.95),  # road closure high
    "parade":               (0.55, 0.90),
    "exhibition":           (0.45, 0.50),
    "other":                (0.50, 0.55),
}


def _simulate_raw_score(row: dict) -> tuple[float, float, float, float]:
    """
    Deterministic heuristic that maps raw event features to
    (congestion_class, risk_score, delay_minutes, impact_radius_km).
    Used during synthetic dataset generation.
    """
    crowd = row["crowd_size"]
    dur = row["duration_hours"]
    closure = row["has_road_closure"]
    etype = row["event_type"]
    dow = row["start_datetime"].weekday()
    hour = row["start_datetime"].hour

    crowd_m, road_m = _TYPE_RISK_BASE.get(etype, (0.5, 0.6))

    # Normalise crowd to 0–1 (logistic scale)
    crowd_norm = min(1.0, np.log1p(crowd) / np.log1p(500_000))

    # Weekend & peak hour boosts
    weekend_boost = 0.10 if dow >= 5 else 0.0
    peak_boost = 0.10 if 7 <= hour <= 9 or 17 <= hour <= 20 else 0.0
    closure_boost = 0.20 if closure else 0.0
    duration_boost = min(0.15, dur / 24.0)

    base_score = (crowd_norm * crowd_m * 0.50 + road_m * 0.20 +
                  weekend_boost + peak_boost + closure_boost + duration_boost)
    base_score = np.clip(base_score + np.random.normal(0, 0.05), 0, 1)

    # Congestion class
    if base_score < 0.25:
        cls = 0
    elif base_score < 0.50:
        cls = 1
    elif base_score < 0.75:
        cls = 2
    else:
        cls = 3

    risk = base_score * 100.0
    delay = base_score * 90.0 + (crowd / 10_000) * 5.0
    radius = 0.5 + base_score * 12.0 + (crowd / 100_000) * 3.0

    return float(cls), float(np.clip(risk, 0, 100)), float(np.clip(delay, 0, 180)), float(np.clip(radius, 0.1, 15))


def generate_synthetic_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """
    Produce a synthetic training dataset of historical events.
    """
    logger.info("Generating synthetic training dataset (%d samples)…", n_samples)
    random.seed(42)
    np.random.seed(42)

    base_date = datetime(2021, 1, 1)
    records = []
    for _ in range(n_samples):
        etype = random.choice(_EVENT_TYPES)
        crowd = int(np.random.lognormal(mean=8.0, sigma=1.5))
        crowd = max(100, min(crowd, 1_000_000))
        dur = round(random.uniform(1.0, 12.0), 1)
        closure = random.random() < 0.35
        dt_offset = timedelta(days=random.randint(0, 730),
                              hours=random.randint(6, 22))
        dt = base_date + dt_offset
        records.append({
            "event_type": etype,
            "crowd_size": crowd,
            "duration_hours": dur,
            "has_road_closure": closure,
            "start_datetime": dt,
        })

    X = build_training_dataframe(records)

    # Compute targets
    targets = [_simulate_raw_score(r) for r in records]
    y_cls, y_risk, y_delay, y_radius = zip(*targets)

    df = X.copy()
    df["congestion_class"] = list(y_cls)
    df["risk_score"] = list(y_risk)
    df["delay_minutes"] = list(y_delay)
    df["impact_radius_km"] = list(y_radius)
    return df


# ── Training ───────────────────────────────────────────────────────────────────

def train_and_save(n_samples: int = 5000) -> dict:
    """
    Train all models on synthetic data, persist to MODEL_DIR.
    Returns a dict of evaluation metrics.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_dataset(n_samples)

    feature_cols = FEATURE_NAMES
    X = df[feature_cols].values
    y_cls = df["congestion_class"].values.astype(int)
    y_risk = df["risk_score"].values
    y_delay = df["delay_minutes"].values
    y_radius = df["impact_radius_km"].values

    X_tr, X_te, yc_tr, yc_te, yr_tr, yr_te, yd_tr, yd_te, yrad_tr, yrad_te = \
        train_test_split(X, y_cls, y_risk, y_delay, y_radius,
                         test_size=0.15, random_state=42)

    # Scale features
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    joblib.dump(scaler, SCALER_PATH)

    # 1. Classifier — congestion level
    clf = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="mlogloss",
        random_state=42, n_jobs=-1,
    )
    clf.fit(X_tr_s, yc_tr, eval_set=[(X_te_s, yc_te)], verbose=False)
    clf.save_model(str(CLF_PATH))
    clf_acc = float((clf.predict(X_te_s) == yc_te).mean())

    # 2. Risk score regressor
    reg_risk = XGBRegressor(n_estimators=200, max_depth=6, random_state=42, n_jobs=-1)
    reg_risk.fit(X_tr_s, yr_tr)
    reg_risk.save_model(str(REG_RISK_PATH))

    # 3. Delay regressor
    reg_delay = XGBRegressor(n_estimators=150, max_depth=5, random_state=42, n_jobs=-1)
    reg_delay.fit(X_tr_s, yd_tr)
    reg_delay.save_model(str(REG_DELAY_PATH))

    # 4. Radius regressor
    reg_radius = XGBRegressor(n_estimators=150, max_depth=5, random_state=42, n_jobs=-1)
    reg_radius.fit(X_tr_s, yrad_tr)
    reg_radius.save_model(str(REG_RADIUS_PATH))

    import json
    metadata = {
        "model_version": "1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "n_samples": n_samples,
        "classifier_accuracy": clf_acc,
        "feature_names": feature_cols,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))
    logger.info("Models saved to %s — classifier accuracy: %.2f%%", MODEL_DIR, clf_acc * 100)
    return metadata


def models_exist() -> bool:
    return all(p.exists() for p in [CLF_PATH, REG_RISK_PATH, REG_DELAY_PATH, REG_RADIUS_PATH, SCALER_PATH])
