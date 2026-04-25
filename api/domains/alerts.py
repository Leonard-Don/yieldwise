from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.alerts import AlertRules, AlertRulesPatch, AlertsState
from ..schemas.watchlist import WatchlistEntry
from ..service import get_building, get_community
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
    alerts = alerts_diff.compute_alerts(
        watchlist_items=watchlist_items,
        baselines=state.baselines,
        snapshots=snapshots,
        rules=rules,
    )
    return {
        "items": [a.model_dump() for a in alerts],
        "last_open_at": state.last_open_at,
    }


@router.post("/alerts/mark-seen")
def mark_seen() -> dict[str, Any]:
    watchlist_items = _load_watchlist()
    baselines: dict[str, dict[str, Any]] = {}
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
        seen += 1
    state = AlertsState(baselines=baselines, last_open_at=_now())
    personal_storage.write_json(ALERTS_STATE_FILE, state.model_dump())
    return {"items_seen": seen, "last_open_at": state.last_open_at}
