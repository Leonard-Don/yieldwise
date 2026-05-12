from __future__ import annotations

from api.domains.watchlist import _candidate_triggers, build_candidate_review_queue


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
