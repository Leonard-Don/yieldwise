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
        "summary": {
            "total": 0,
            "shortlisted": 0,
            "due": 0,
            "changed": 0,
            "ready": 0,
            "target_rule": 0,
            "evidence_missing": 0,
            "task_groups": {
                "due_review": 0,
                "target_rule": 0,
                "changed": 0,
                "evidence_missing": 0,
                "shortlisted": 0,
            },
        },
    }


def test_review_queue_returns_deterministic_candidate_tasks(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_yield_pct": 0.1,
            "review_due_at": "2000-01-01",
        },
    )
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "pudong",
            "target_type": "district",
            "status": "rejected",
            "target_yield_pct": 0.1,
        },
    )

    response = client.get("/api/v2/watchlist/review-queue")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"] == {
        "total": 2,
        "pending_review": 1,
        "watch": 0,
        "reviewed": 0,
        "dismissed": 1,
    }

    first = body["items"][0]
    assert first["target_id"] == "zhangjiang-park-b1"
    assert first["target_name"]
    assert first["target_type"] == "building"
    assert first["status"] == "pending_review"
    assert first["candidate_status"] == "watching"
    assert first["priority"] == 3
    assert first["current_yield_pct"] > 1
    assert first["target_yield_pct"] == 0.1
    assert first["yield_delta_pct"] == round(first["current_yield_pct"] - 0.1, 2)
    assert "收益率达到目标" in first["trigger_labels"]
    assert first["review_date"] == "2000-01-01"

    assert body["items"][1]["target_id"] == "pudong"
    assert body["items"][1]["status"] == "dismissed"


def test_review_queue_includes_deterministic_reviewer_digest(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_yield_pct": 0.1,
            "review_due_at": "2000-01-01",
        },
    )
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "pudong",
            "target_type": "district",
            "status": "rejected",
            "target_yield_pct": 0.1,
        },
    )

    response = client.get("/api/v2/watchlist/review-queue")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"] == body["digest"]["counts"]
    assert body["digest"]["open_count"] == 1
    assert body["digest"]["next_action_count"] == 1
    assert body["digest"]["top_target"]["target_id"] == "zhangjiang-park-b1"
    assert [action["group"] for action in body["digest"]["next_actions"]] == [
        "due_review",
        "target_rule",
    ]
    assert body["digest"]["next_actions"][0]["count"] == 1
    assert body["digest"]["next_actions"][0]["target_ids"] == ["zhangjiang-park-b1"]
    assert body["digest"]["next_actions"][0]["top_targets"][0]["task_labels"]


def test_review_decision_reviewed_persists_audit_and_closes_open_actions(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_yield_pct": 0.1,
            "review_due_at": "2000-01-01",
        },
    )

    response = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "reviewed", "note": "真实挂牌和租金已复核"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["review_decision"] == "reviewed"
    assert body["review_decision_at"]
    assert body["review_decision_note"] == "真实挂牌和租金已复核"
    assert body["decision_history"][-1]["decision"] == "reviewed"
    assert body["decision_history"][-1]["note"] == "真实挂牌和租金已复核"
    assert body["decision_history"][-1]["decided_at"] == body["review_decision_at"]
    assert body["last_reviewed_at"] == body["review_decision_at"]
    assert body["last_seen_snapshot"]["name"]
    assert body["notes"] == "真实挂牌和租金已复核"

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["summary"] == {
        "total": 1,
        "pending_review": 0,
        "watch": 0,
        "reviewed": 1,
        "dismissed": 0,
    }
    assert queue["digest"]["open_count"] == 0
    assert queue["digest"]["next_action_count"] == 0
    assert queue["digest"]["next_actions"] == []
    assert queue["items"][0]["status"] == "reviewed"
    assert queue["items"][0]["review_decision"] == "reviewed"
    assert "target_rule" not in queue["items"][0]["task_groups"]


def test_review_decision_watch_keeps_candidate_visible_as_watch(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_yield_pct": 0.1,
            "review_due_at": "2000-01-01",
        },
    )

    response = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "watch", "note": "暂不推进，保留观察"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["review_decision"] == "watch"
    assert body["review_decision_at"]
    assert body["review_decision_note"] == "暂不推进，保留观察"
    assert body["status"] == "watching"
    assert body["review_due_at"] is None

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["summary"] == {
        "total": 1,
        "pending_review": 0,
        "watch": 1,
        "reviewed": 0,
        "dismissed": 0,
    }
    assert queue["digest"]["open_count"] == 1
    assert queue["digest"]["next_action_count"] == 1
    assert [action["group"] for action in queue["digest"]["next_actions"]] == ["watch"]
    assert queue["items"][0]["status"] == "watch"
    assert queue["items"][0]["review_decision"] == "watch"
    assert queue["items"][0]["task_groups"] == ["watch"]


def test_review_decision_dismissed_moves_to_dismissed_without_open_actions(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_yield_pct": 0.1,
        },
    )

    response = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "dismissed"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "rejected"
    assert body["review_decision"] == "dismissed"
    assert body["review_decision_at"]
    assert body["review_decision_note"] is None
    assert body["decision_history"][-1]["decision"] == "dismissed"
    assert body["last_reviewed_at"] == body["review_decision_at"]

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["summary"] == {
        "total": 1,
        "pending_review": 0,
        "watch": 0,
        "reviewed": 0,
        "dismissed": 1,
    }
    assert queue["digest"]["open_count"] == 0
    assert queue["digest"]["next_action_count"] == 0
    assert queue["items"][0]["status"] == "dismissed"


def test_review_decision_preserves_string_zero_target_id(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "0", "target_type": "building", "review_due_at": "2000-01-01"},
    )

    response = client.post(
        "/api/v2/watchlist/0/review-decision",
        json={"decision": "watch", "note": "0 号占位候选继续观察"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_id"] == "0"
    assert body["review_decision"] == "watch"
    assert body["decision_history"][-1]["note"] == "0 号占位候选继续观察"

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["items"][0]["target_id"] == "0"
    assert queue["items"][0]["status"] == "watch"
    assert queue["digest"]["next_actions"][0]["target_ids"] == ["0"]


def test_review_decision_preserves_numeric_zero_target_id_through_storage(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": 0, "target_type": "building", "review_due_at": "2000-01-01"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["target_id"] == 0

    decision = client.post(
        "/api/v2/watchlist/0/review-decision",
        json={"decision": "watch", "note": "numeric zero"},
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["target_id"] == 0
    assert decision.json()["review_decision"] == "watch"

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["items"][0]["target_id"] == "0"
    assert queue["digest"]["next_actions"][0]["target_ids"] == ["0"]


def test_reviewed_decision_reenters_queue_when_due_again(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    reviewed = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "reviewed"},
    )
    assert reviewed.status_code == 200, reviewed.text

    patched = client.patch(
        "/api/v2/watchlist/zhangjiang-park-b1",
        json={"review_due_at": "2000-01-01"},
    )
    assert patched.status_code == 200, patched.text

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["summary"]["pending_review"] == 1
    assert queue["items"][0]["status"] == "pending_review"
    assert "due_review" in queue["items"][0]["task_groups"]
    assert queue["digest"]["open_count"] == 1


def test_legacy_action_overrides_prior_review_decision(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    watched = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "watch"},
    )
    assert watched.status_code == 200, watched.text

    rejected = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/actions",
        json={"action": "reject", "notes": "旧动作仍然是权威操作"},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["review_decision"] == "dismissed"

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["summary"]["dismissed"] == 1
    assert queue["items"][0]["status"] == "dismissed"
    assert queue["digest"]["open_count"] == 0


def test_legacy_shortlist_action_supersedes_prior_watch_decision(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    watched = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/review-decision",
        json={"decision": "watch"},
    )
    assert watched.status_code == 200, watched.text

    shortlisted = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/actions",
        json={"action": "shortlist", "notes": "旧按钮提升为候选"},
    )
    assert shortlisted.status_code == 200, shortlisted.text
    body = shortlisted.json()
    assert body["status"] == "shortlisted"
    assert body["review_decision"] is None
    assert body["review_decision_superseded_at"] == body["updated_at"]

    queue = client.get("/api/v2/watchlist/review-queue").json()
    assert queue["items"][0]["candidate_status"] == "shortlisted"
    assert queue["items"][0]["status"] != "watch"
    assert "watch" not in queue["items"][0]["task_groups"]
    assert "shortlisted" in queue["items"][0]["task_groups"]


def test_post_adds_entry_with_added_at(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_id"] == "zhangjiang-park-b1"
    assert body["target_type"] == "building"
    assert body["added_at"] is not None
    assert body["status"] == "watching"
    assert body["priority"] == 3
    assert body["target_name"]
    assert body["current_snapshot"]["name"]
    assert body["last_seen_snapshot"] is None

    follow = client.get("/api/v2/watchlist").json()
    assert len(follow["items"]) == 1
    assert follow["items"][0]["target_id"] == "zhangjiang-park-b1"


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
            "target_yield_pct": 3.0,
            "review_due_at": "2000-01-01",
            "notes": "复核 17 层样本",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "shortlisted"
    assert body["status_label"] == "候选"
    assert body["priority"] == 1
    assert body["target_price_wan"] == 780
    assert body["target_yield_pct"] == 3.0
    assert body["candidate_action"]["level"] == "due_review"
    assert any(task["group"] == "due_review" for task in body["candidate_tasks"])


def test_candidate_target_rules_create_tasks(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "target_price_wan": 99999,
            "target_monthly_rent": 1,
            "target_yield_pct": 0.1,
        },
    )
    item = client.get("/api/v2/watchlist").json()["items"][0]
    kinds = {trigger["kind"] for trigger in item["candidate_triggers"]}
    assert {"target_price_hit", "target_rent_hit", "target_yield_hit"} <= kinds
    assert any(task["group"] == "target_rule" for task in item["candidate_tasks"])


def test_action_complete_review_updates_baseline_and_next_due(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={
            "target_id": "zhangjiang-park-b1",
            "target_type": "building",
            "review_due_at": "2000-01-01",
        },
    )
    response = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/actions",
        json={"action": "complete_review", "days": 10, "notes": "已复核真实样本"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["last_reviewed_at"] is not None
    assert body["last_seen_snapshot"]["name"]
    assert body["review_due_at"] > "2000-01-01"
    assert body["notes"] == "已复核真实样本"
    assert not any(task["group"] == "due_review" for task in body["candidate_tasks"])


def test_action_reject_removes_from_active_queue(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "zhangjiang-park-b1", "target_type": "building"},
    )
    response = client.post(
        "/api/v2/watchlist/zhangjiang-park-b1/actions",
        json={"action": "reject"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "rejected"
    assert body["review_due_at"] is None
    assert body["candidate_action"]["level"] == "rejected"


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
