from __future__ import annotations


def test_dev_routes_are_hidden_from_openapi(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/dev/runtime-caches/clear" not in paths
    assert "/api/dev/browser-review-fixtures/review-current-task" not in paths
    assert "/api/dev/browser-review-fixtures/{fixture_id}" not in paths


def test_dev_routes_disabled_without_demo_or_explicit_flag(client, monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_ENABLE_DEMO_MOCK", raising=False)
    monkeypatch.delenv("ATLAS_ENABLE_DEV_ROUTES", raising=False)

    response = client.post("/api/dev/runtime-caches/clear", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "Development route is disabled"


def test_dev_routes_enabled_in_demo_mode(client, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_ENABLE_DEMO_MOCK", "1")
    monkeypatch.delenv("ATLAS_ENABLE_DEV_ROUTES", raising=False)

    response = client.post("/api/dev/runtime-caches/clear", json={})

    assert response.status_code == 200
    assert response.json() == {"cleared": True}


def test_dev_routes_enabled_by_explicit_flag(client, monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_ENABLE_DEMO_MOCK", raising=False)
    monkeypatch.setenv("ATLAS_ENABLE_DEV_ROUTES", "true")

    response = client.post("/api/dev/runtime-caches/clear", json={})

    assert response.status_code == 200
    assert response.json() == {"cleared": True}
