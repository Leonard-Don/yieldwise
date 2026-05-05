from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_items_when_no_file(client) -> None:
    response = client.get("/api/v2/watchlist")
    assert response.status_code == 200, response.text
    assert response.json() == {
        "items": [],
        "summary": {"total": 0, "shortlisted": 0, "due": 0, "changed": 0, "ready": 0},
    }


def test_post_adds_entry_with_added_at(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "daning-jinmaofu-b1", "target_type": "building"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_id"] == "daning-jinmaofu-b1"
    assert body["target_type"] == "building"
    assert body["added_at"] is not None
    assert body["status"] == "watching"
    assert body["priority"] == 3
    assert body["target_name"]
    assert body["current_snapshot"]["name"]
    assert body["last_seen_snapshot"] is None

    follow = client.get("/api/v2/watchlist").json()
    assert len(follow["items"]) == 1
    assert follow["items"][0]["target_id"] == "daning-jinmaofu-b1"


def test_post_is_idempotent_replaces_existing(client) -> None:
    first = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    ).json()
    second = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    ).json()
    items = client.get("/api/v2/watchlist").json()["items"]
    assert len(items) == 1
    # added_at refreshed (or at least preserved as not-null)
    assert second["added_at"] is not None
    assert first["target_id"] == second["target_id"]


def test_delete_removes_entry(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    )
    response = client.delete("/api/v2/watchlist/x")
    assert response.status_code == 200, response.text
    assert response.json() == {"removed": True}
    assert client.get("/api/v2/watchlist").json()["items"] == []


def test_delete_missing_id_returns_removed_false(client) -> None:
    response = client.delete("/api/v2/watchlist/never-existed")
    assert response.status_code == 200
    assert response.json() == {"removed": False}


def test_post_accepts_district_target_type(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "pudong", "target_type": "district"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_type"] == "district"
    assert body["current_snapshot"]["name"]


def test_post_rejects_invalid_target_type_with_422(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "listing"},
    )
    assert response.status_code == 422


def test_patch_updates_candidate_research_fields(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    response = client.patch(
        "/api/v2/watchlist/zhangjiang-park-b1",
        json={
            "status": "shortlisted",
            "priority": 1,
            "thesis": "楼层收益高于小区均值",
            "target_price_wan": 780,
            "target_monthly_rent": 22000,
            "review_due_at": "2026-05-10",
            "notes": "复核 17 层样本",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "shortlisted"
    assert body["status_label"] == "候选"
    assert body["priority"] == 1
    assert body["target_price_wan"] == 780
    assert body["candidate_action"]["level"] == "due"


def test_post_then_get_preserves_order_oldest_first(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "first", "target_type": "building"},
    )
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "second", "target_type": "community"},
    )
    items = client.get("/api/v2/watchlist").json()["items"]
    assert [it["target_id"] for it in items] == ["first", "second"]
