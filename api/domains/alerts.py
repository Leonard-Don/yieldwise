from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.alerts import AlertRules, AlertRulesPatch, AlertsState
from ..schemas.watchlist import WatchlistEntry
from ..service import get_building, get_community, list_districts
from . import alerts_diff

router = APIRouter(tags=["alerts"])

ALERTS_STATE_FILE = "alerts_state.json"
ALERT_RULES_FILE = "alert_rules.json"
WATCHLIST_FILE = "watchlist.json"


def _load_watchlist() -> list[dict[str, Any]]:
    raw = personal_storage.read_json(WATCHLIST_FILE)
    if raw is None:
        return []
    if isinstance(raw, dict) and "items" in raw:
        candidates = raw["items"]
    else:
        candidates = raw
    if not isinstance(candidates, list):
        return []
    items: list[dict[str, Any]] = []
    for row in candidates:
        try:
            items.append(WatchlistEntry.model_validate(row).model_dump())
        except Exception:
            continue
    return items


def _save_watchlist(items: list[dict[str, Any]]) -> None:
    personal_storage.write_json(WATCHLIST_FILE, {"items": items})


def _load_state() -> AlertsState:
    raw = personal_storage.read_json(ALERTS_STATE_FILE)
    if raw is None:
        return AlertsState()
    try:
        return AlertsState.model_validate(raw)
    except Exception:
        return AlertsState()


def _load_rules() -> AlertRules:
    raw = personal_storage.read_json(ALERT_RULES_FILE)
    if raw is None:
        return AlertRules()
    try:
        return AlertRules.model_validate(raw)
    except Exception:
        return AlertRules()


def _snapshot(target_id: str, target_type: str) -> dict[str, Any] | None:
    if target_type == "building":
        record = get_building(target_id)
        if not record:
            return None
        return {
            "name": record.get("name"),
            "yield": record.get("yieldAvg"),
            "price": record.get("saleMedianWan"),
            "score": record.get("score"),
        }
    if target_type == "community":
        record = get_community(target_id)
        if not record:
            return None
        return {
            "name": record.get("name"),
            "yield": record.get("yield"),
            "price": record.get("avgPriceWan"),
            "score": record.get("score"),
        }
    return None


def _district_snapshots() -> dict[str, dict[str, Any]]:
    rows = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    snapshots: dict[str, dict[str, Any]] = {}
    for row in rows:
        district_id = row.get("id")
        if not district_id:
            continue
        snapshots[district_id] = {
            "name": row.get("name") or "",
            "yield": row.get("yield"),
        }
    return snapshots


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@router.get("/alerts/rules")
def get_rules() -> dict[str, Any]:
    return _load_rules().model_dump()


@router.patch("/alerts/rules")
def patch_rules(patch: AlertRulesPatch) -> dict[str, Any]:
    current = _load_rules().model_dump()
    update = patch.model_dump(exclude_unset=True)
    merged = {**current, **update}
    rules = AlertRules.model_validate(merged)
    personal_storage.write_json(ALERT_RULES_FILE, rules.model_dump())
    return rules.model_dump()


@router.get("/alerts/since-last-open")
def since_last_open() -> dict[str, Any]:
    state = _load_state()
    rules = _load_rules()
    watchlist_items = _load_watchlist()
    snapshots: dict[str, dict[str, Any] | None] = {}
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshots[target_id] = _snapshot(target_id, target_type)
    district_snapshots = _district_snapshots()
    alerts = alerts_diff.compute_alerts(
        watchlist_items=watchlist_items,
        baselines=state.baselines,
        snapshots=snapshots,
        rules=rules,
        district_snapshots=district_snapshots,
    )
    return {
        "items": [a.model_dump() for a in alerts],
        "last_open_at": state.last_open_at,
    }


@router.post("/alerts/mark-seen")
def mark_seen() -> dict[str, Any]:
    watchlist_items = _load_watchlist()
    baselines: dict[str, dict[str, Any]] = {}
    snapshots_by_target: dict[str, dict[str, Any]] = {}
    seen = 0
    for entry in watchlist_items:
        target_id = entry.get("target_id")
        target_type = entry.get("target_type")
        if not target_id or target_type not in ("building", "community"):
            continue
        snapshot = _snapshot(target_id, target_type)
        if snapshot is None:
            continue
        baselines[target_id] = snapshot
        snapshots_by_target[target_id] = snapshot
        seen += 1
    district_snapshots = _district_snapshots()
    for district_id, snap in district_snapshots.items():
        if snap.get("yield") is None:
            continue
        baselines[district_id] = {"yield": snap.get("yield"), "name": snap.get("name")}
        snapshots_by_target[district_id] = {"yield": snap.get("yield"), "name": snap.get("name")}
        seen += 1
    if watchlist_items:
        changed = False
        next_items: list[dict[str, Any]] = []
        for entry in watchlist_items:
            target_id = entry.get("target_id")
            if target_id in snapshots_by_target:
                entry = {**entry, "last_seen_snapshot": snapshots_by_target[target_id]}
                changed = True
            next_items.append(entry)
        if changed:
            _save_watchlist(next_items)
    state = AlertsState(baselines=baselines, last_open_at=_now())
    personal_storage.write_json(ALERTS_STATE_FILE, state.model_dump())
    return {"items_seen": seen, "last_open_at": state.last_open_at}
