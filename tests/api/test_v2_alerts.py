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
    watchlist = json.loads(
        (isolated_personal_dir / "watchlist.json").read_text(encoding="utf-8")
    )
    assert watchlist["items"][0]["last_seen_snapshot"]["name"]
    assert watchlist["items"][0]["last_seen_snapshot"]["yield"] is not None


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


def test_since_last_open_emits_candidate_target_rule_alerts(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_price_wan": 99999,
            "target_monthly_rent": 1,
            "target_yield_pct": 1.0,
        },
    )
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200, response.text
    kinds = {item["kind"] for item in response.json()["items"]}
    assert {"target_price_hit", "target_rent_hit", "target_yield_hit"} <= kinds


def test_since_last_open_emits_review_due_alert(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "review_due_at": "2000-01-01",
        },
    )
    response = client.get("/api/v2/alerts/since-last-open")
    assert response.status_code == 200, response.text
    assert any(item["kind"] == "review_due" for item in response.json()["items"])


def test_since_last_open_includes_target_name(
    client, isolated_personal_dir: Path
) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    state = {
        "baselines": {
            "zhangjiang-park-b1": {"yield": 1.0, "price": 100.0, "score": 30}
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open").json()
    assert len(response["items"]) >= 1
    for item in response["items"]:
        assert item["target_id"] == "zhangjiang-park-b1"
        # mock data exposes a building name distinct from the slug id
        assert item.get("target_name")
        assert item["target_name"] != item["target_id"]


def test_since_last_open_emits_district_delta_alerts(
    client, isolated_personal_dir: Path
) -> None:
    # No watchlist needed for district alerts; plant a stale district baseline.
    state = {
        "baselines": {
            "pudong": {"yield": 0.5},
        },
        "last_open_at": "2026-04-20T10:00:00",
    }
    (isolated_personal_dir / "alerts_state.json").write_text(
        json.dumps(state), encoding="utf-8"
    )
    response = client.get("/api/v2/alerts/since-last-open").json()
    district_alerts = [it for it in response["items"] if it["target_type"] == "district"]
    assert any(a["target_id"] == "pudong" for a in district_alerts)
    pudong = next(a for a in district_alerts if a["target_id"] == "pudong")
    assert pudong["kind"] in ("district_delta_up", "district_delta_down")
    assert pudong.get("target_name")
    assert pudong["target_name"] != pudong["target_id"]


def test_mark_seen_captures_district_baselines(
    client, isolated_personal_dir: Path
) -> None:
    response = client.post("/api/v2/alerts/mark-seen", json={})
    assert response.status_code == 200
    on_disk = json.loads(
        (isolated_personal_dir / "alerts_state.json").read_text(encoding="utf-8")
    )
    # Districts get baselines even with empty watchlist
    assert "pudong" in on_disk["baselines"]
    # Following GET should produce no alerts because baselines == current
    follow = client.get("/api/v2/alerts/since-last-open").json()
    district_alerts = [it for it in follow["items"] if it["target_type"] == "district"]
    assert district_alerts == []
