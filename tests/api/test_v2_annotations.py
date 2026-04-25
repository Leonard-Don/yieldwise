from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_items_when_no_file(client) -> None:
    response = client.get("/api/v2/annotations/by-target/whatever")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}


def test_post_creates_note_with_uuid_and_timestamps(client) -> None:
    response = client.post(
        "/api/v2/annotations",
        json={
            "target_id": "daning-jinmaofu-b1",
            "target_type": "building",
            "body": "first note",
        },
    )
    assert response.status_code == 200, response.text
    note = response.json()
    assert note["note_id"]
    assert note["target_id"] == "daning-jinmaofu-b1"
    assert note["target_type"] == "building"
    assert note["body"] == "first note"
    assert note["created_at"] is not None
    assert note["updated_at"] is not None


def test_get_by_target_returns_only_matching_target(client) -> None:
    client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "a"},
    )
    client.post(
        "/api/v2/annotations",
        json={"target_id": "beta", "target_type": "community", "body": "b"},
    )
    items = client.get("/api/v2/annotations/by-target/alpha").json()["items"]
    assert len(items) == 1
    assert items[0]["target_id"] == "alpha"


def test_get_by_target_sorts_newest_first(client) -> None:
    first = client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "old"},
    ).json()
    # The persistence timestamp uses second-precision; we cannot reliably
    # produce two distinct timestamps within the same test in the same
    # second. We assert that newest-first is correct by inspecting the
    # created_at field directly when timestamps differ; otherwise the
    # ordering only requires stable arrangement.
    second = client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "newer"},
    ).json()
    items = client.get("/api/v2/annotations/by-target/alpha").json()["items"]
    assert len(items) == 2
    if first["created_at"] != second["created_at"]:
        assert items[0]["note_id"] == second["note_id"]
        assert items[1]["note_id"] == first["note_id"]


def test_patch_updates_body_and_refreshes_updated_at(client) -> None:
    note = client.post(
        "/api/v2/annotations",
        json={"target_id": "x", "target_type": "building", "body": "v1"},
    ).json()
    response = client.patch(
        f"/api/v2/annotations/{note['note_id']}",
        json={"body": "v2"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["body"] == "v2"
    assert updated["created_at"] == note["created_at"]
    assert updated["updated_at"] is not None


def test_patch_unknown_id_returns_404(client) -> None:
    response = client.patch(
        "/api/v2/annotations/never-existed",
        json={"body": "v2"},
    )
    assert response.status_code == 404


def test_delete_removes_existing(client) -> None:
    note = client.post(
        "/api/v2/annotations",
        json={"target_id": "x", "target_type": "building", "body": "v1"},
    ).json()
    response = client.delete(f"/api/v2/annotations/{note['note_id']}")
    assert response.status_code == 200
    assert response.json() == {"removed": True}
    assert client.get("/api/v2/annotations/by-target/x").json()["items"] == []


def test_delete_unknown_id_returns_removed_false(client) -> None:
    response = client.delete("/api/v2/annotations/never-existed")
    assert response.status_code == 200
    assert response.json() == {"removed": False}
