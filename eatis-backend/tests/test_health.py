"""
tests/test_health.py
────────────────────────
Basic health check and root endpoint tests.
"""


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code in (200, 503)
    assert "status" in resp.json()


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "name" in body
    assert "version" in body
