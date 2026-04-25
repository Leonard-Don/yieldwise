from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_rules_default_when_no_file(client) -> None:
    response = client.get("/api/v2/alerts/rules")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["yield_delta_abs"] == 0.5
    assert body["price_drop_pct"] == 3.0
    assert body["score_delta_abs"] == 5


def test_rules_patch_merges_and_persists(client) -> None:
    response = client.patch(
        "/api/v2/alerts/rules", json={"yield_delta_abs": 1.0}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["yield_delta_abs"] == 1.0
    # other fields preserved at defaults
    assert body["price_drop_pct"] == 3.0
    follow = client.get("/api/v2/alerts/rules").json()
    assert follow["yield_delta_abs"] == 1.0


def test_rules_patch_rejects_unknown_field_with_422(client) -> None:
    response = client.patch("/api/v2/alerts/rules", json={"evil": True})
    assert response.status_code == 422


def test_since_last_open_returns_empty_with_no_state(client) -> None:
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {"items": [], "last_open_at": None}


def test_since_last_open_emits_yield_alert(client, isolated_personal_dir: Path) -> None:
    # Add a real mock building to the watchlist
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    # Plant a stale baseline directly on disk
    state = {
        "baselines": {
            "zhangjiang-park-b1": {"yield": 1.0, "price": 100.0, "score": 30}
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200
    body = response.json()
    assert body["last_open_at"] == "2026-04-20T10:00:00"
    kinds = {item["kind"] for item in body["items"]}
    # The mock yieldAvg/score are far enough from baseline to trigger
    assert "yield_up" in kinds or "yield_down" in kinds
    assert "score_jump" in kinds


def test_mark_seen_creates_baselines_for_watchlist_targets(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    response = client.post("/api/v2/alerts/mark-seen", json={})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items_seen"] >= 1
    assert body["last_open_at"] is not None

    on_disk = json.loads(
        (isolated_personal_dir / "alerts_state.json").read_text(encoding="utf-8")
    )
    assert "zhangjiang-park-b1" in on_disk["baselines"]


def test_mark_seen_then_since_last_open_returns_no_alerts(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    client.post("/api/v2/alerts/mark-seen", json={})
    response = client.get("/api/v2/alerts/since-last-open").json()
    # baselines == current → no alerts
    assert response["items"] == []
    assert response["last_open_at"] is not None
