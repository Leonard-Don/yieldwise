from __future__ import annotations


def test_v2_map_districts_matches_legacy(client) -> None:
    legacy = client.get("/api/map/districts")
    v2 = client.get("/api/v2/map/districts")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_districts_with_filters(client) -> None:
    params = {"district": "pudong", "min_yield": 3.0, "max_budget": 1500.0, "min_samples": 1}
    legacy = client.get("/api/map/districts", params=params)
    v2 = client.get("/api/v2/map/districts", params=params)
    assert v2.json() == legacy.json()


def test_v2_map_communities_matches_legacy(client) -> None:
    legacy = client.get("/api/map/communities")
    v2 = client.get("/api/v2/map/communities")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_communities_with_filters(client) -> None:
    params = {
        "district": "pudong",
        "sample_status": "active_metrics",
        "focus_scope": "priority",
    }
    legacy = client.get("/api/map/communities", params=params)
    v2 = client.get("/api/v2/map/communities", params=params)
    assert v2.json() == legacy.json()


def test_v2_map_buildings_matches_legacy(client) -> None:
    legacy = client.get("/api/map/buildings")
    v2 = client.get("/api/v2/map/buildings")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_buildings_with_filters(client) -> None:
    params = {"district": "pudong", "focus_scope": "priority", "geometry_quality": "all"}
    legacy = client.get("/api/map/buildings", params=params)
    v2 = client.get("/api/v2/map/buildings", params=params)
    assert v2.json() == legacy.json()
