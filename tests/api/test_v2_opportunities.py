from __future__ import annotations


def test_v2_opportunities_matches_legacy_default(client) -> None:
    legacy = client.get("/api/opportunities")
    v2 = client.get("/api/v2/opportunities")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_opportunities_matches_legacy_with_filters(client) -> None:
    params = {
        "district": "pudong",
        "min_yield": 3.5,
        "max_budget": 1500.0,
        "min_samples": 2,
        "min_score": 10,
    }
    legacy = client.get("/api/opportunities", params=params)
    v2 = client.get("/api/v2/opportunities", params=params)
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_opportunities_returns_items_key(client) -> None:
    response = client.get("/api/v2/opportunities")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    assert "items" in body
    assert isinstance(body["items"], list)
    if body["items"]:
        item = body["items"][0]
        assert item["quality"]["status"] in {"strong", "usable", "thin", "blocked"}
        assert item["qualityLabel"] == item["quality"]["label"]
        assert item["decisionBrief"]["stance"] in {"shortlist", "watch", "sample_first"}
        assert item["decisionBrief"]["nextAction"]
