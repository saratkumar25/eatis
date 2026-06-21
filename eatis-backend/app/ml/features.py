"""
app/ml/features.py
───────────────────
Feature engineering for the XGBoost congestion prediction model.
Converts raw event data into a numeric feature vector.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Ordered list of feature names — must match training column order.
FEATURE_NAMES = [
    "crowd_size_log",           # log(crowd_size + 1) — normalises scale
    "duration_hours",
    "has_road_closure",
    "day_of_week",              # 0=Mon … 6=Sun
    "hour_of_day",
    "is_weekend",
    # Event type one-hot (11 categories)
    "type_political_rally",
    "type_sports_event",
    "type_music_festival",
    "type_cultural_event",
    "type_religious_gathering",
    "type_construction",
    "type_public_demonstration",
    "type_marathon",
    "type_parade",
    "type_exhibition",
    "type_other",
]

# Map raw event_type strings to one-hot column names
EVENT_TYPE_MAP = {
    "political_rally":      "type_political_rally",
    "sports_event":         "type_sports_event",
    "music_festival":       "type_music_festival",
    "cultural_event":       "type_cultural_event",
    "religious_gathering":  "type_religious_gathering",
    "construction":         "type_construction",
    "public_demonstration": "type_public_demonstration",
    "marathon":             "type_marathon",
    "parade":               "type_parade",
    "exhibition":           "type_exhibition",
    "other":                "type_other",
}


def build_feature_vector(
    event_type: str,
    crowd_size: int,
    duration_hours: float,
    start_datetime,           # datetime-like
    has_road_closure: bool,
) -> np.ndarray:
    """
    Build a single (1 × n_features) numpy array from raw event inputs.
    This function must remain in sync with FEATURE_NAMES.
    """
    row: dict[str, float] = {name: 0.0 for name in FEATURE_NAMES}

    row["crowd_size_log"] = float(np.log1p(crowd_size))
    row["duration_hours"] = float(duration_hours)
    row["has_road_closure"] = float(has_road_closure)
    row["day_of_week"] = float(start_datetime.weekday())
    row["hour_of_day"] = float(start_datetime.hour)
    row["is_weekend"] = float(start_datetime.weekday() >= 5)

    # One-hot encode event type
    col = EVENT_TYPE_MAP.get(event_type.lower(), "type_other")
    row[col] = 1.0

    return np.array([row[name] for name in FEATURE_NAMES], dtype=np.float32).reshape(1, -1)


def build_training_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert a list of raw event dicts into a training DataFrame."""
    rows = []
    for r in records:
        vec = build_feature_vector(
            event_type=r["event_type"],
            crowd_size=r["crowd_size"],
            duration_hours=r["duration_hours"],
            start_datetime=r["start_datetime"],
            has_road_closure=r["has_road_closure"],
        )
        rows.append(vec.flatten())
    return pd.DataFrame(rows, columns=FEATURE_NAMES)
