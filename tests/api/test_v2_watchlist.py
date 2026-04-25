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
    assert response.json() == {"items": []}


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


def test_post_rejects_invalid_target_type_with_422(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "district"},
    )
    assert response.status_code == 422


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
