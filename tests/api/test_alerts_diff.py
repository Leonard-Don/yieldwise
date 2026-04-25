from __future__ import annotations

from api.domains.alerts_diff import compute_alerts
from api.schemas.alerts import AlertRules


def _watchlist(target_ids: list[tuple[str, str]]) -> list[dict]:
    return [{"target_id": tid, "target_type": ttype} for tid, ttype in target_ids]


def test_no_baselines_returns_empty() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={},
        snapshots={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        rules=AlertRules(),
    )
    assert items == []


def test_no_snapshot_skips_target() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": None},
        rules=AlertRules(),
    )
    assert items == []


def test_yield_up_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 4.6, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_up"
    assert abs(items[0].delta - 0.6) < 0.001
    assert items[0].from_value == 4.0
    assert items[0].to_value == 4.6


def test_yield_down_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 3.4, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_down"
    assert abs(items[0].delta - (-0.6)) < 0.001


def test_yield_within_deadzone_no_alert() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 4.3, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert items == []


def test_price_drop_crosses_threshold() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 950.0, "score": 60}},
        rules=AlertRules(price_drop_pct=3.0),
    )
    assert len(items) == 1
    assert items[0].kind == "price_drop"
    # 1000 → 950 is a 5% drop
    assert items[0].delta == -50.0
    assert items[0].from_value == 1000.0
    assert items[0].to_value == 950.0


def test_price_increase_does_not_alert() -> None:
    # spec only flags drops, not increases
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1100.0, "score": 60}},
        rules=AlertRules(price_drop_pct=3.0),
    )
    assert items == []


def test_score_jump_either_direction() -> None:
    # Spec yield mode: 机会分跳变 ≥5 — symmetric.
    rules = AlertRules(score_delta_abs=5)
    up = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1000.0, "score": 70}},
        rules=rules,
    )
    assert len(up) == 1
    assert up[0].kind == "score_jump"
    assert up[0].delta == 10
    down = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.0, "price": 1000.0, "score": 50}},
        rules=rules,
    )
    assert len(down) == 1
    assert down[0].delta == -10


def test_yield_unit_normalisation_fraction_input() -> None:
    # baseline is 0.04 (fraction = 4%); snapshot is 0.05 (= 5%); diff = 1.0 pp > 0.5
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 0.04, "price": 800.0, "score": 60}},
        snapshots={"x": {"yield": 0.05, "price": 800.0, "score": 60}},
        rules=AlertRules(yield_delta_abs=0.5),
    )
    assert len(items) == 1
    assert items[0].kind == "yield_up"
    # Reported in percentage points using the larger of the two
    assert abs(items[0].delta - 1.0) < 0.001


def test_multiple_alerts_per_target() -> None:
    items = compute_alerts(
        watchlist_items=_watchlist([("x", "building")]),
        baselines={"x": {"yield": 4.0, "price": 1000.0, "score": 60}},
        snapshots={"x": {"yield": 4.6, "price": 950.0, "score": 70}},
        rules=AlertRules(),
    )
    kinds = sorted(a.kind for a in items)
    assert kinds == ["price_drop", "score_jump", "yield_up"]
