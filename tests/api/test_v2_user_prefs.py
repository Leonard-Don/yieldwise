from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_defaults_when_no_file(client) -> None:
    response = client.get("/api/v2/user/prefs")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] is None
    assert body["districts"] == []
    assert body["updated_at"] is None


def test_patch_writes_and_get_round_trips(client, isolated_personal_dir: Path) -> None:
    response = client.patch(
        "/api/v2/user/prefs",
        json={"budget_max_wan": 1500, "districts": ["pudong"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] == 1500
    assert body["districts"] == ["pudong"]
    assert body["updated_at"] is not None

    # Followup GET sees the persisted state.
    follow = client.get("/api/v2/user/prefs").json()
    assert follow["budget_max_wan"] == 1500
    assert follow["districts"] == ["pudong"]

    # File actually exists on disk.
    assert (isolated_personal_dir / "user_prefs.json").is_file()


def test_patch_merges_partial_updates(client) -> None:
    client.patch("/api/v2/user/prefs", json={"budget_max_wan": 1500, "districts": ["pudong"]})
    response = client.patch("/api/v2/user/prefs", json={"area_min_sqm": 60})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] == 1500
    assert body["districts"] == ["pudong"]
    assert body["area_min_sqm"] == 60


def test_patch_rejects_unknown_field_with_422(client) -> None:
    response = client.patch("/api/v2/user/prefs", json={"evil": True})
    assert response.status_code == 422


def test_patch_rejects_negative_budget_with_422(client) -> None:
    response = client.patch("/api/v2/user/prefs", json={"budget_max_wan": -10})
    assert response.status_code == 422


def test_get_returns_defaults_when_stored_file_is_corrupt(
    client, isolated_personal_dir: Path
) -> None:
    (isolated_personal_dir / "user_prefs.json").write_text("{not json", encoding="utf-8")
    response = client.get("/api/v2/user/prefs")
    assert response.status_code == 200
    assert response.json()["budget_max_wan"] is None
