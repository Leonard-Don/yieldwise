from __future__ import annotations

from api.domains.watchlist import _candidate_triggers, build_candidate_review_digest, build_candidate_review_queue


def test_candidate_yield_rule_normalizes_fraction_snapshot_to_percent() -> None:
    triggers = _candidate_triggers(
        {"target_id": "x", "target_yield_pct": 4.0},
        {"yield": 0.045},
    )

    assert triggers == [
        {
            "kind": "target_yield_hit",
            "label": "收益率达到目标",
            "current": 4.5,
            "target": 4.0,
            "delta": 0.5,
        }
    ]


def test_candidate_review_queue_derives_fields_and_sorts_deterministically() -> None:
    queue = build_candidate_review_queue(
        [
            {
                "target_id": "watch",
                "target_type": "community",
                "target_name": "Watch Only",
                "status": "watching",
                "priority": 1,
                "added_at": "2026-05-12T09:00:00",
                "current_snapshot": {"yield": 4.1},
                "candidate_tasks": [],
                "candidate_triggers": [],
                "candidate_action": {"level": "ready"},
            },
            {
                "target_id": "pending-old-material",
                "target_type": "building",
                "target_name": "Older Material",
                "status": "watching",
                "priority": 2,
                "added_at": "2026-05-12T08:00:00",
                "updated_at": "2026-05-12T08:10:00",
                "target_yield_pct": 4.0,
                "review_due_at": "2026-05-12",
                "current_snapshot": {"yield": 0.049},
                "snapshot_delta": {"yieldDeltaPct": 1.8, "priceDeltaWan": -120},
                "candidate_tasks": [{"group": "target_rule", "label": "收益率达到目标", "priority": "high"}],
                "candidate_triggers": [
                    {
                        "kind": "target_yield_hit",
                        "label": "收益率达到目标",
                        "delta": 0.9,
                    }
                ],
                "candidate_action": {"level": "target_rule"},
            },
            {
                "target_id": "pending-newer",
                "target_type": "building",
                "target_name": "Newer Pending",
                "status": "researching",
                "priority": 2,
                "added_at": "2026-05-12T08:00:00",
                "updated_at": "2026-05-12T10:00:00",
                "target_yield_pct": 4.0,
                "current_snapshot": {"yield": 0.045},
                "snapshot_delta": {"yieldDeltaPct": 0.2},
                "candidate_tasks": [{"group": "target_rule", "label": "收益率达到目标", "priority": "high"}],
                "candidate_triggers": [{"kind": "target_yield_hit", "label": "收益率达到目标"}],
                "candidate_action": {"level": "target_rule"},
            },
            {
                "target_id": "reviewed",
                "target_type": "district",
                "target_name": "Reviewed District",
                "status": "watching",
                "priority": 1,
                "added_at": "2026-05-12T11:00:00",
                "last_reviewed_at": "2026-05-12T11:30:00",
                "current_snapshot": {"yield": 4.0},
                "candidate_tasks": [],
                "candidate_triggers": [],
                "candidate_action": {"level": "ready"},
            },
            {
                "target_id": "dismissed",
                "target_type": "building",
                "target_name": "Dismissed",
                "status": "rejected",
                "priority": 1,
                "added_at": "2026-05-12T12:00:00",
                "current_snapshot": {"yield": 9.0},
                "candidate_tasks": [{"group": "rejected", "label": "已放弃", "priority": "low"}],
                "candidate_triggers": [{"kind": "target_yield_hit", "label": "收益率达到目标"}],
                "candidate_action": {"level": "rejected"},
            },
        ]
    )

    assert [item["target_id"] for item in queue] == [
        "pending-newer",
        "pending-old-material",
        "watch",
        "reviewed",
        "dismissed",
    ]
    first = queue[0]
    assert first["status"] == "pending_review"
    assert first["candidate_status"] == "researching"
    assert first["current_yield_pct"] == 4.5
    assert first["target_yield_pct"] == 4.0
    assert first["yield_delta_pct"] == 0.5
    assert first["trigger_labels"] == ["收益率达到目标"]
    assert first["trigger_reasons"] == ["target_yield_hit"]
    assert first["task_labels"] == ["收益率达到目标"]
    assert first["review_date"] is None
    assert queue[1]["material_delta"] > queue[0]["material_delta"]
    assert queue[2]["status"] == "watch"
    assert queue[3]["status"] == "reviewed"
    assert queue[4]["status"] == "dismissed"


def test_candidate_review_digest_handles_sparse_queue_items_deterministically() -> None:
    digest = build_candidate_review_digest(
        [
            {
                "target_id": "watch",
                "target_name": "Watch",
                "target_type": "community",
                "status": "watch",
                "priority": "",
                "task_groups": None,
            },
            {
                "target_id": "due",
                "target_name": "Due",
                "target_type": "building",
                "status": "pending_review",
                "priority": 1,
                "review_date": "2026-05-12",
                "task_groups": ["due_review", "due_review", "", None],
                "task_labels": ["到期复核", None, ""],
                "task_priorities": ["high", ""],
                "trigger_labels": [None, "收益率达到目标"],
                "material_delta": 2.34567,
            },
            {
                "target_id": "evidence",
                "target_name": "Evidence",
                "target_type": "building",
                "status": "pending_review",
                "priority": 2,
                "task_groups": ["evidence_missing"],
                "task_labels": ["证据不足"],
                "task_priorities": ["medium"],
            },
            {
                "target_name": "",
                "target_type": "",
                "status": "",
                "priority": None,
                "task_groups": [],
            },
            {
                "target_id": "dismissed",
                "status": "dismissed",
                "task_groups": ["rejected"],
            },
        ]
    )

    assert digest["counts"] == {
        "total": 5,
        "pending_review": 2,
        "watch": 1,
        "reviewed": 0,
        "dismissed": 1,
    }
    assert digest["open_count"] == 3
    assert digest["next_action_count"] == 4
    assert [action["group"] for action in digest["next_actions"]] == [
        "due_review",
        "evidence_missing",
        "watch",
        "needs_review",
    ]
    due_action = digest["next_actions"][0]
    assert due_action["count"] == 1
    assert due_action["target_ids"] == ["due"]
    assert due_action["top_targets"][0] == {
        "target_id": "due",
        "target_name": "Due",
        "target_type": "building",
        "status": "pending_review",
        "candidate_status": None,
        "priority": 1,
        "review_date": "2026-05-12",
        "action_level": None,
        "task_labels": ["到期复核"],
        "trigger_labels": ["收益率达到目标"],
        "yield_delta_pct": None,
        "material_delta": 2.3457,
    }
    assert digest["top_target"]["target_id"] == "due"
    assert digest["next_actions"][-1]["top_targets"][0]["target_name"] == "未命名候选"


def test_candidate_review_queue_and_digest_preserve_numeric_zero_ids() -> None:
    queue = build_candidate_review_queue(
        [
            {
                "target_id": 0,
                "target_type": "building",
                "target_name": "Zero Candidate",
                "status": "watching",
                "priority": 1,
                "current_snapshot": {"yield": 4.2},
                "candidate_tasks": [{"group": "target_rule", "label": "收益率达到目标", "priority": "high"}],
                "candidate_triggers": [{"kind": "target_yield_hit", "label": "收益率达到目标"}],
                "candidate_action": {"level": "target_rule"},
            }
        ]
    )

    assert queue[0]["target_id"] == "0"
    digest = build_candidate_review_digest(queue)
    assert digest["next_actions"][0]["target_ids"] == ["0"]
    assert digest["next_actions"][0]["top_targets"][0]["target_id"] == "0"
