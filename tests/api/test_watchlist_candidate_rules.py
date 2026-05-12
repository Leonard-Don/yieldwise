from __future__ import annotations

from api.domains.watchlist import _candidate_triggers


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
