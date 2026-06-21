"""
scripts/train_from_csv.py
─────────────────────────
Trains the EATIS XGBoost models from the Astram real-world event CSV.

Usage (from the eatis-backend directory):
    python scripts/train_from_csv.py

Or inside Docker:
    docker exec -it eatis-backend-web-1 python scripts/train_from_csv.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier, XGBRegressor

# ── Path bootstrap so we can import app modules ────────────────────────────────
BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.features import FEATURE_NAMES, build_training_dataframe  # noqa: E402
from app.ml.trainer import (  # noqa: E402
    MODEL_DIR, CLF_PATH, REG_RISK_PATH, REG_DELAY_PATH, REG_RADIUS_PATH,
    SCALER_PATH, METADATA_PATH, _simulate_raw_score,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Map CSV event_cause → our internal EventType enum ─────────────────────────
CAUSE_TO_EVENT_TYPE = {
    "public_event":       "cultural_event",
    "accident":           "other",
    "vehicle_breakdown":  "construction",   # road blockage, similar impact
    "tree_fall":          "other",
    "water_logging":      "construction",
    "pot_holes":          "construction",
    "others":             "other",
    "traffic_jam":        "other",
    "road_work":          "construction",
    "vip_movement":       "political_rally",
    "protest":            "public_demonstration",
    "marathon":           "marathon",
    "parade":             "parade",
    "festival":           "music_festival",
    "religious":          "religious_gathering",
    "sports":             "sports_event",
    "exhibition":         "exhibition",
}

# Crowd-size estimates: priority × corridor tier
PRIORITY_CROWD = {
    "high":   (15_000, 80_000),
    "medium": (3_000,  15_000),
    "low":    (500,    3_000),
}

CORRIDOR_CROWD_BOOST = {
    # Major corridors → bigger crowd estimates
    "cbd":         2.5,
    "orr":         1.8,
    "tumkur":      1.5,
    "bellary":     1.5,
    "hosur":       1.4,
    "mysore":      1.4,
    "whitefield":  1.3,
    "old madras":  1.3,
}


def estimate_crowd(row: pd.Series) -> int:
    priority = str(row.get("priority", "low")).lower().strip()
    corridor = str(row.get("corridor", "")).lower()

    lo, hi = PRIORITY_CROWD.get(priority, PRIORITY_CROWD["low"])

    # Check corridor for boost
    boost = 1.0
    for kw, mult in CORRIDOR_CROWD_BOOST.items():
        if kw in corridor:
            boost = mult
            break

    # Use mid-point + noise
    base = (lo + hi) / 2 * boost
    crowd = int(np.clip(np.random.normal(base, base * 0.15), lo, hi * boost))
    return max(100, crowd)


def parse_dt(val) -> datetime | None:
    if not val or str(val).strip().upper() in ("NULL", "NAN", "NAT", ""):
        return None
    try:
        s = str(val).strip()
        # Remove timezone offset for simplicity
        for fmt in [
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                dt = datetime.strptime(s[:26], fmt[:len(fmt)])
                return dt.replace(tzinfo=None)
            except ValueError:
                continue
        return pd.to_datetime(val, utc=True).tz_localize(None).to_pydatetime()
    except Exception:
        return None


def load_and_clean(csv_path: str) -> list[dict]:
    logger.info("Loading CSV: %s", csv_path)
    df = pd.read_csv(csv_path, low_memory=False)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))

    records = []
    skipped = 0
    np.random.seed(42)

    for _, row in df.iterrows():
        # Parse start_datetime (required)
        start_dt = parse_dt(row.get("start_datetime"))
        if start_dt is None:
            skipped += 1
            continue

        # Parse end_datetime for duration
        end_dt = parse_dt(row.get("end_datetime"))
        if end_dt and end_dt > start_dt:
            duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
        else:
            # Default to 2 hrs for unplanned events with no end time
            duration_hours = 2.0
        # Clip to sensible range
        duration_hours = float(np.clip(duration_hours, 0.25, 24.0))

        # Map event_cause → event_type
        cause = str(row.get("event_cause", "others")).lower().strip()
        event_type = CAUSE_TO_EVENT_TYPE.get(cause, "other")

        # Road closure
        rc_raw = str(row.get("requires_road_closure", "FALSE")).upper().strip()
        has_road_closure = rc_raw in ("TRUE", "1", "YES")

        # Estimate crowd size
        crowd_size = estimate_crowd(row)

        records.append({
            "event_type":       event_type,
            "crowd_size":       crowd_size,
            "duration_hours":   duration_hours,
            "has_road_closure": has_road_closure,
            "start_datetime":   start_dt,
        })

    logger.info("Clean records: %d  (skipped %d with no start_datetime)", len(records), skipped)
    return records


def train_from_csv(csv_path: str) -> dict:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    records = load_and_clean(csv_path)

    if len(records) < 100:
        raise ValueError(f"Not enough valid records to train: {len(records)}")

    logger.info("Building feature matrix…")
    X_df = build_training_dataframe(records)

    # Derive targets using the same heuristic as synthetic training
    # (this bakes Bangalore traffic knowledge into the labels)
    logger.info("Computing training targets…")
    targets = [_simulate_raw_score(r) for r in records]
    y_cls, y_risk, y_delay, y_radius = zip(*targets)

    X = X_df[FEATURE_NAMES].values
    y_cls   = np.array(y_cls).astype(int)
    y_risk  = np.array(y_risk)
    y_delay = np.array(y_delay)
    y_radius = np.array(y_radius)

    logger.info("Splitting train/test (85/15)…")
    X_tr, X_te, yc_tr, yc_te, yr_tr, yr_te, yd_tr, yd_te, yrad_tr, yrad_te = \
        train_test_split(X, y_cls, y_risk, y_delay, y_radius,
                         test_size=0.15, random_state=42)

    logger.info("Scaling features…")
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)
    joblib.dump(scaler, SCALER_PATH)

    logger.info("Training congestion classifier…")
    clf = XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.08,
        subsample=0.85, colsample_bytree=0.85,
        use_label_encoder=False, eval_metric="mlogloss",
        random_state=42, n_jobs=-1,
    )
    clf.fit(X_tr_s, yc_tr, eval_set=[(X_te_s, yc_te)], verbose=False)
    clf.save_model(str(CLF_PATH))
    clf_acc = float((clf.predict(X_te_s) == yc_te).mean())
    logger.info("Classifier accuracy: %.2f%%", clf_acc * 100)

    logger.info("Training risk score regressor…")
    reg_risk = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.08, random_state=42, n_jobs=-1)
    reg_risk.fit(X_tr_s, yr_tr)
    reg_risk.save_model(str(REG_RISK_PATH))

    logger.info("Training delay regressor…")
    reg_delay = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.08, random_state=42, n_jobs=-1)
    reg_delay.fit(X_tr_s, yd_tr)
    reg_delay.save_model(str(REG_DELAY_PATH))

    logger.info("Training impact radius regressor…")
    reg_radius = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.08, random_state=42, n_jobs=-1)
    reg_radius.fit(X_tr_s, yrad_tr)
    reg_radius.save_model(str(REG_RADIUS_PATH))

    metadata = {
        "model_version": "2.0.0-astram",
        "trained_at": datetime.utcnow().isoformat(),
        "source": "Astram real-world Bangalore traffic CSV",
        "n_samples": len(records),
        "classifier_accuracy": clf_acc,
        "feature_names": FEATURE_NAMES,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2))

    logger.info("✅ All models saved to %s", MODEL_DIR)
    logger.info("   Classifier accuracy: %.2f%%", clf_acc * 100)
    logger.info("   Samples used:        %d", len(records))
    return metadata


if __name__ == "__main__":
    # Auto-detect the CSV in the backend root directory
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Find any .csv in the backend root
        backend_dir = BACKEND_ROOT
        csvs = sorted(backend_dir.glob("*.csv"))
        if not csvs:
            logger.error("No CSV file found in %s. Pass the path as an argument.", backend_dir)
            sys.exit(1)
        csv_file = str(csvs[0])
        logger.info("Auto-detected CSV: %s", csv_file)

    result = train_from_csv(csv_file)
    print("\n=== Training Complete ===")
    print(json.dumps(result, indent=2))
