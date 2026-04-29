from __future__ import annotations

import pytest


@pytest.fixture()
def sample_building_id(client) -> str:
    """Pull a real building id from the legacy map/buildings GeoJSON FeatureCollection."""
    response = client.get("/api/map/buildings")
    assert response.status_code == 200, response.text
    body = response.json()
    features = body.get("features") or []
    assert features, "no building features in staged data; cannot run detail tests"
    props = features[0].get("properties") or {}
    building_id = props.get("building_id")
    assert building_id, f"first feature has no building_id in properties: {props!r}"
    return str(building_id)


def test_v2_building_detail_matches_legacy(client, sample_building_id) -> None:
    legacy = client.get(f"/api/buildings/{sample_building_id}")
    v2 = client.get(f"/api/v2/buildings/{sample_building_id}")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_building_detail_404_for_unknown(client) -> None:
    response = client.get("/api/v2/buildings/does-not-exist-xyz-123")
    assert response.status_code == 404
