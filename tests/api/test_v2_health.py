from __future__ import annotations


def test_v2_health_returns_ok(client) -> None:
    response = client.get("/api/v2/health")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok", "surface": "user-platform-v2"}


def test_v2_health_is_independent_of_legacy_health(client) -> None:
    legacy = client.get("/api/health")
    v2 = client.get("/api/v2/health")
    assert legacy.status_code == 200
    assert v2.status_code == 200
    assert legacy.json() != v2.json(), "v2 health must be distinguishable from legacy health"
