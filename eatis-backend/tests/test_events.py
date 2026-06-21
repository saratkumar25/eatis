"""
tests/test_events.py
──────────────────────
End-to-end test of event creation through the full prediction pipeline.
NOTE: first run will train XGBoost models if not already cached, so this
test may take longer on a cold cache.
"""

from datetime import datetime, timedelta


def _auth_headers(client) -> dict:
    client.post("/api/v1/auth/register", json={
        "name": "Operator",
        "email": "op@eatis.gov",
        "password": "OperatorPass123",
        "role": "operator",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "op@eatis.gov",
        "password": "OperatorPass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_event_runs_full_pipeline(client):
    headers = _auth_headers(client)
    start = datetime.utcnow() + timedelta(days=3)
    end = start + timedelta(hours=4)

    resp = client.post("/api/v1/events", headers=headers, json={
        "name": "Test Rally",
        "event_type": "political_rally",
        "location_name": "Test Plaza",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "start_datetime": start.isoformat(),
        "end_datetime": end.isoformat(),
        "expected_crowd_size": 10000,
        "has_road_closure": True,
        "road_closure_details": "Main road closed",
    })
    assert resp.status_code == 201
    event = resp.json()
    event_id = event["id"]

    # Prediction should exist
    pred_resp = client.get(f"/api/v1/events/{event_id}/prediction", headers=headers)
    assert pred_resp.status_code == 200
    pred = pred_resp.json()
    assert pred["congestion_level"] in ("low", "medium", "high", "critical")
    assert 0 <= pred["risk_score"] <= 100

    # Resources should exist
    res_resp = client.get(f"/api/v1/events/{event_id}/resources", headers=headers)
    assert res_resp.status_code == 200
    assert res_resp.json()["officers_required"] > 0

    # Routes should exist
    route_resp = client.get(f"/api/v1/events/{event_id}/routes", headers=headers)
    assert route_resp.status_code == 200
    assert len(route_resp.json()) > 0

    # Heatmap should be generated
    heatmap_resp = client.get(f"/api/v1/heatmap/{event_id}", headers=headers)
    assert heatmap_resp.status_code == 200
    assert len(heatmap_resp.json()["points"]) > 0


def test_invalid_event_dates_rejected(client):
    headers = _auth_headers(client)
    start = datetime.utcnow() + timedelta(days=3)
    end = start - timedelta(hours=1)  # end before start

    resp = client.post("/api/v1/events", headers=headers, json={
        "name": "Invalid Event",
        "event_type": "sports_event",
        "location_name": "Stadium",
        "latitude": 28.5733,
        "longitude": 77.2497,
        "start_datetime": start.isoformat(),
        "end_datetime": end.isoformat(),
        "expected_crowd_size": 5000,
    })
    assert resp.status_code == 422
