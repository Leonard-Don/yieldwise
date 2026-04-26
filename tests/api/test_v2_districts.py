from __future__ import annotations


def test_get_district_404_for_unknown_id(client) -> None:
    response = client.get("/api/v2/districts/nope")
    assert response.status_code == 404


def test_get_district_returns_pudong(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == "pudong"
    assert body["name"] == "浦东新区"
    assert "yield" in body
    assert "communities" in body
    assert isinstance(body["communities"], list)


def test_get_district_includes_community_count(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    body = response.json()
    assert body["community_count"] == len(body["communities"])


def test_get_district_communities_sorted_yield_desc(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    body = response.json()
    yields = [
        c.get("yield") for c in body["communities"] if c.get("yield") is not None
    ]
    assert yields == sorted(yields, reverse=True)


def test_get_district_works_for_huangpu(client) -> None:
    # Sanity check on a different district id
    response = client.get("/api/v2/districts/huangpu")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["id"] == "huangpu"
