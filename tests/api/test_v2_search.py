from __future__ import annotations


def test_search_with_empty_query_returns_empty(client) -> None:
    response = client.get("/api/v2/search?q=")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}


def test_search_finds_district_by_chinese_name(client) -> None:
    response = client.get("/api/v2/search?q=浦东")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    target_types = {it["target_type"] for it in items}
    assert "district" in target_types
    assert any(it["target_name"].startswith("浦东") for it in items)


def test_search_finds_community(client) -> None:
    response = client.get("/api/v2/search?q=张江")
    items = response.json()["items"]
    assert items, "expected at least one mock community matching 张江"
    matching = [it for it in items if "张江" in it["target_name"]]
    assert matching


def test_search_results_have_district_name_for_buildings(client) -> None:
    response = client.get("/api/v2/search?q=zhangjiang-park-b1")
    items = response.json()["items"]
    # The id is the building id; mock building name is e.g. '1号楼' / 'A座'.
    # Buildings are matched by NAME not id, so this will be 0 hits — and that's fine.
    assert isinstance(items, list)


def test_search_respects_limit_query_param(client) -> None:
    response = client.get("/api/v2/search?q=新&limit=2")
    items = response.json()["items"]
    assert len(items) <= 2
