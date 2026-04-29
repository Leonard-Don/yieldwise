from __future__ import annotations

import pytest


@pytest.fixture()
def sample_community_id(client) -> str:
    """Derive a real community id from the legacy map/buildings GeoJSON properties.

    /api/map/communities returns no items in demo-mock mode, so we extract a
    community_id from a building feature's properties — every building belongs
    to a community, and /api/communities/{id} is keyed by the same id space.
    """
    response = client.get("/api/map/buildings")
    assert response.status_code == 200, response.text
    body = response.json()
    features = body.get("features") or []
    assert features, "no building features in staged data; cannot run detail tests"
    for feature in features:
        cid = (feature.get("properties") or {}).get("community_id")
        if cid:
            return str(cid)
    raise AssertionError("no community_id found in any building feature")


def test_v2_community_detail_matches_legacy(client, sample_community_id) -> None:
    legacy = client.get(f"/api/communities/{sample_community_id}")
    v2 = client.get(f"/api/v2/communities/{sample_community_id}")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_community_detail_404_for_unknown(client) -> None:
    response = client.get("/api/v2/communities/does-not-exist-xyz-123")
    assert response.status_code == 404
