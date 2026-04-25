from __future__ import annotations

from typing import Any

from ..schemas.alerts import Alert, AlertRules


def compute_alerts(
    watchlist_items: list[dict[str, Any]],
    baselines: dict[str, dict[str, Any]],
    snapshots: dict[str, dict[str, Any] | None],
    rules: AlertRules,
) -> list[Alert]:
    out: list[Alert] = []
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if target_type not in ("building", "community"):
            continue
        baseline = baselines.get(target_id)
        if not baseline:
            continue
        snapshot = snapshots.get(target_id)
        if not snapshot:
            continue
        out.extend(_diff_target(target_id, target_type, baseline, snapshot, rules))
    return out


def _diff_target(
    target_id: str,
    target_type: str,
    baseline: dict[str, Any],
    snapshot: dict[str, Any],
    rules: AlertRules,
) -> list[Alert]:
    out: list[Alert] = []
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None

    base_yield = _normalize_yield(baseline.get("yield"))
    snap_yield = _normalize_yield(snapshot.get("yield"))
    if base_yield is not None and snap_yield is not None:
        delta = snap_yield - base_yield
        if delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_up", base_yield, snap_yield, delta, target_name))
        elif -delta >= rules.yield_delta_abs:
            out.append(_alert(target_id, target_type, "yield_down", base_yield, snap_yield, delta, target_name))

    base_price = _maybe_float(baseline.get("price"))
    snap_price = _maybe_float(snapshot.get("price"))
    if base_price is not None and snap_price is not None and base_price > 0:
        drop_pct = ((base_price - snap_price) / base_price) * 100.0
        if drop_pct >= rules.price_drop_pct:
            out.append(
                _alert(
                    target_id,
                    target_type,
                    "price_drop",
                    base_price,
                    snap_price,
                    snap_price - base_price,
                    target_name,
                )
            )

    base_score = _maybe_float(baseline.get("score"))
    snap_score = _maybe_float(snapshot.get("score"))
    if base_score is not None and snap_score is not None:
        delta = snap_score - base_score
        if abs(delta) >= rules.score_delta_abs:
            out.append(
                _alert(target_id, target_type, "score_jump", base_score, snap_score, delta, target_name)
            )

    return out


def _normalize_yield(value: Any) -> float | None:
    num = _maybe_float(value)
    if num is None:
        return None
    # Frontend mirror: a value < 1 is a fraction (e.g. 0.04 = 4%); scale up.
    return num * 100.0 if num < 1 else num


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def _alert(
    target_id: str,
    target_type: str,
    kind: str,
    base: float,
    snap: float,
    delta: float,
    target_name: str | None = None,
) -> Alert:
    return Alert(
        target_id=target_id,
        target_name=target_name,
        target_type=target_type,
        kind=kind,
        from_value=base,
        to_value=snap,
        delta=delta,
    )
