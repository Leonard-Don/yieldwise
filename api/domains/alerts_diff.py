from __future__ import annotations

from datetime import date
from typing import Any

from ..schemas.alerts import Alert, AlertRules


def compute_alerts(
    watchlist_items: list[dict[str, Any]],
    baselines: dict[str, dict[str, Any]],
    snapshots: dict[str, dict[str, Any] | None],
    rules: AlertRules,
    district_snapshots: dict[str, dict[str, Any] | None] | None = None,
) -> list[Alert]:
    out: list[Alert] = []
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if target_type not in ("building", "community", "district"):
            continue
        if _is_due(entry.get("review_due_at")):
            out.append(
                _alert(
                    target_id,
                    target_type,
                    "review_due",
                    None,
                    None,
                    None,
                    str(entry.get("target_name") or target_id),
                )
            )
        snapshot = snapshots.get(target_id)
        if snapshot:
            out.extend(_candidate_rule_alerts(entry, target_type, snapshot))
            evidence_alert = _evidence_alert(target_id, target_type, snapshot)
            if evidence_alert is not None:
                out.append(evidence_alert)
        baseline = baselines.get(target_id)
        if not baseline:
            continue
        if not snapshot:
            continue
        if target_type in ("building", "community"):
            out.extend(_diff_target(target_id, target_type, baseline, snapshot, rules))

    if district_snapshots:
        for district_id, district_snap in district_snapshots.items():
            if not district_snap:
                continue
            baseline = baselines.get(district_id)
            if not baseline:
                continue
            alert = _diff_district(district_id, baseline, district_snap, rules)
            if alert is not None:
                out.append(alert)

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

    base_floor_pairs = _maybe_float(baseline.get("topFloorPairCount"))
    snap_floor_pairs = _maybe_float(snapshot.get("topFloorPairCount"))
    if rules.listing_new and base_floor_pairs is not None and snap_floor_pairs is not None:
        delta = snap_floor_pairs - base_floor_pairs
        if delta >= 1:
            out.append(
                _alert(
                    target_id,
                    target_type,
                    "floor_sample_change",
                    base_floor_pairs,
                    snap_floor_pairs,
                    delta,
                    target_name,
                )
            )

    return out


def _candidate_rule_alerts(
    entry: dict[str, Any],
    target_type: str,
    snapshot: dict[str, Any],
) -> list[Alert]:
    if entry.get("status") == "rejected":
        return []
    target_id = str(entry.get("target_id") or "")
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None
    out: list[Alert] = []

    price = _maybe_float(snapshot.get("price"))
    target_price = _maybe_float(entry.get("target_price_wan"))
    if price is not None and target_price is not None and price <= target_price:
        out.append(_alert(target_id, target_type, "target_price_hit", target_price, price, price - target_price, target_name))

    rent = _maybe_float(snapshot.get("rent"))
    target_rent = _maybe_float(entry.get("target_monthly_rent"))
    if rent is not None and target_rent is not None and rent >= target_rent:
        out.append(_alert(target_id, target_type, "target_rent_hit", target_rent, rent, rent - target_rent, target_name))

    yield_pct = _normalize_yield(snapshot.get("yield"))
    target_yield = _maybe_float(entry.get("target_yield_pct"))
    if yield_pct is not None and target_yield is not None and yield_pct >= target_yield:
        out.append(_alert(target_id, target_type, "target_yield_hit", target_yield, yield_pct, yield_pct - target_yield, target_name))

    return out


def _evidence_alert(
    target_id: str,
    target_type: str,
    snapshot: dict[str, Any],
) -> Alert | None:
    if snapshot.get("qualityStatus") not in {"blocked", "thin"}:
        return None
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None
    return _alert(target_id, target_type, "evidence_missing", None, None, None, target_name)


def _diff_district(
    district_id: str,
    baseline: dict[str, Any],
    snapshot: dict[str, Any],
    rules: AlertRules,
) -> Alert | None:
    base = _normalize_yield(baseline.get("yield"))
    snap = _normalize_yield(snapshot.get("yield"))
    if base is None or snap is None:
        return None
    delta = snap - base
    if abs(delta) < rules.district_delta_abs:
        return None
    name_raw = snapshot.get("name")
    target_name = str(name_raw) if name_raw else None
    kind = "district_delta_up" if delta > 0 else "district_delta_down"
    return Alert(
        target_id=district_id,
        target_name=target_name,
        target_type="district",
        kind=kind,
        from_value=base,
        to_value=snap,
        delta=delta,
    )


def _normalize_yield(value: Any) -> float | None:
    num = _maybe_float(value)
    if num is None:
        return None
    # Frontend mirror: a value < 1 is a fraction (e.g. 0.04 = 4%); scale up.
    return num * 100.0 if num < 1 else num


def _is_due(value: Any) -> bool:
    if not value:
        return False
    try:
        due_date = date.fromisoformat(str(value)[:10])
    except ValueError:
        return False
    return due_date <= date.today()


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
