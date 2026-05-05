from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.watchlist import WatchlistAddPayload, WatchlistEntry, WatchlistPatchPayload
from ..service import get_building, get_community, list_districts

router = APIRouter(tags=["watchlist"])

WATCHLIST_FILE = "watchlist.json"
CANDIDATE_STATUS_LABELS = {
    "watching": "观察",
    "researching": "复核中",
    "shortlisted": "候选",
    "rejected": "搁置",
}


def _load_entries() -> list[dict[str, Any]]:
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
            # Skip rows that no longer match the schema; don't fail the
            # whole list for one bad row.
            continue
    return items


def _save_entries(items: list[dict[str, Any]]) -> None:
    personal_storage.write_json(WATCHLIST_FILE, {"items": items})


@router.get("/watchlist")
def list_watchlist() -> dict[str, Any]:
    items = [_enrich_entry(item) for item in _load_entries()]
    return {
        "items": items,
        "summary": _research_summary(items),
    }


@router.post("/watchlist")
def add_to_watchlist(payload: WatchlistAddPayload) -> dict[str, Any]:
    items = _load_entries()
    now = _now()

    # Idempotent: replace any existing entry with the same target_id, keeping
    # the original list position so the order stays stable.
    replaced = False
    for index, existing in enumerate(items):
        if existing.get("target_id") == payload.target_id:
            new_entry = _entry_from_payload(payload, existing=existing, now=now)
            items[index] = new_entry
            replaced = True
            break
    if not replaced:
        new_entry = _entry_from_payload(payload, existing=None, now=now)
        items.append(new_entry)

    _save_entries(items)
    return _enrich_entry(new_entry)


@router.patch("/watchlist/{target_id}")
def update_watchlist_entry(target_id: str, payload: WatchlistPatchPayload) -> dict[str, Any]:
    items = _load_entries()
    update = payload.model_dump(exclude_unset=True)
    for index, existing in enumerate(items):
        if existing.get("target_id") != target_id:
            continue
        next_entry = {
            **existing,
            **update,
            "updated_at": _now(),
        }
        validated = WatchlistEntry.model_validate(next_entry).model_dump()
        items[index] = validated
        _save_entries(items)
        return _enrich_entry(validated)
    return {"updated": False}


@router.delete("/watchlist/{target_id}")
def remove_from_watchlist(target_id: str) -> dict[str, Any]:
    items = _load_entries()
    next_items = [it for it in items if it.get("target_id") != target_id]
    if len(next_items) == len(items):
        return {"removed": False}
    _save_entries(next_items)
    return {"removed": True}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _entry_from_payload(
    payload: WatchlistAddPayload,
    *,
    existing: dict[str, Any] | None,
    now: str,
) -> dict[str, Any]:
    existing = existing or {}
    update = payload.model_dump(exclude_unset=True)
    entry = {
        **existing,
        **update,
        "target_id": payload.target_id,
        "target_type": payload.target_type,
        "added_at": existing.get("added_at") or now,
        "updated_at": now,
        "status": update.get("status") or existing.get("status") or "watching",
        "priority": update.get("priority") or existing.get("priority") or 3,
        "last_seen_snapshot": existing.get("last_seen_snapshot"),
    }
    return WatchlistEntry.model_validate(entry).model_dump()


def _enrich_entry(entry: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot_for_entry(entry)
    delta = _snapshot_delta(entry.get("last_seen_snapshot"), snapshot)
    target_name = (snapshot or {}).get("name") or entry.get("target_id")
    return {
        **entry,
        "status_label": CANDIDATE_STATUS_LABELS.get(str(entry.get("status") or ""), "观察"),
        "target_name": target_name,
        "current_snapshot": snapshot,
        "snapshot_delta": delta,
        "candidate_action": _candidate_action(entry, snapshot, delta),
    }


def _snapshot_for_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    target_id = str(entry.get("target_id") or "")
    target_type = str(entry.get("target_type") or "")
    if not target_id:
        return None

    if target_type == "building":
        record = get_building(target_id)
        if not record:
            return None
        top_floor = (record.get("topFloors") or [None])[0] or {}
        quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
        brief = record.get("decisionBrief") if isinstance(record.get("decisionBrief"), dict) else {}
        return {
            "name": record.get("name") or target_id,
            "targetType": "building",
            "districtName": record.get("districtName"),
            "communityName": record.get("communityName"),
            "yield": record.get("yieldAvg"),
            "price": record.get("saleMedianWan"),
            "rent": record.get("rentMedianMonthly"),
            "score": record.get("score"),
            "qualityLabel": quality.get("label"),
            "qualityStatus": quality.get("status"),
            "decisionLabel": brief.get("label"),
            "decisionNextAction": brief.get("nextAction"),
            "sampleLabel": quality.get("sampleLabel") or f"样本 {record.get('sampleSize') or record.get('sample') or 0}",
            "focusFloorNo": record.get("focusFloorNo"),
            "topFloorNo": top_floor.get("floorNo"),
            "topFloorYield": top_floor.get("yieldPct"),
            "topFloorPairCount": top_floor.get("pairCount") or top_floor.get("latestPairCount"),
        }

    if target_type == "community":
        record = get_community(target_id)
        if not record:
            return None
        quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
        brief = record.get("decisionBrief") if isinstance(record.get("decisionBrief"), dict) else {}
        return {
            "name": record.get("name") or target_id,
            "targetType": "community",
            "districtName": record.get("districtName"),
            "communityName": record.get("name"),
            "yield": record.get("yield"),
            "price": record.get("avgPriceWan"),
            "rent": record.get("monthlyRent"),
            "score": record.get("score"),
            "qualityLabel": quality.get("label"),
            "qualityStatus": quality.get("status"),
            "decisionLabel": brief.get("label"),
            "decisionNextAction": brief.get("nextAction"),
            "sampleLabel": quality.get("sampleLabel") or f"售 {record.get('saleSample') or 0} / 租 {record.get('rentSample') or 0}",
            "primaryBuildingId": record.get("primaryBuildingId"),
            "buildingFocus": record.get("buildingFocus"),
        }

    if target_type == "district":
        row = next(
            (
                item
                for item in list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
                if str(item.get("id")) == target_id
            ),
            None,
        )
        if not row:
            return None
        return {
            "name": row.get("name") or target_id,
            "targetType": "district",
            "districtName": row.get("name"),
            "yield": row.get("yield"),
            "price": row.get("avgBudget") or row.get("avgPriceWan"),
            "rent": row.get("avgMonthlyRent") or row.get("monthlyRent"),
            "score": row.get("score"),
            "sampleLabel": f"样本 {row.get('sample') or row.get('sampleSize') or 0}",
        }

    return None


def _snapshot_delta(
    previous: dict[str, Any] | None,
    current: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not previous or not current:
        return None
    return {
        "yieldDeltaPct": _round_delta(current.get("yield"), previous.get("yield")),
        "priceDeltaWan": _round_delta(current.get("price"), previous.get("price")),
        "rentDeltaMonthly": _round_delta(current.get("rent"), previous.get("rent")),
        "scoreDelta": _round_delta(current.get("score"), previous.get("score")),
    }


def _round_delta(current: Any, previous: Any) -> float | None:
    try:
        cur = float(current)
        prev = float(previous)
    except (TypeError, ValueError):
        return None
    return round(cur - prev, 2)


def _candidate_action(
    entry: dict[str, Any],
    snapshot: dict[str, Any] | None,
    delta: dict[str, Any] | None,
) -> dict[str, str]:
    if not snapshot:
        return {"level": "blocked", "label": "缺当前快照", "next": "先刷新数据或移出候选。"}
    if entry.get("review_due_at"):
        return {"level": "due", "label": "待复核", "next": "按复核日期重新检查价格、租金和样本。"}
    if delta and any(abs(float(value)) >= 0.01 for value in delta.values() if isinstance(value, int | float)):
        return {"level": "changed", "label": "有变化", "next": "展开变化提醒并更新本地备忘录。"}
    if snapshot.get("qualityStatus") in {"strong", "usable"}:
        return {"level": "ready", "label": "可比较", "next": snapshot.get("decisionNextAction") or "加入对比并生成备忘录。"}
    return {"level": "sample", "label": "先补样", "next": snapshot.get("decisionNextAction") or "优先补齐公开样本。"}


def _research_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(items),
        "shortlisted": sum(1 for item in items if item.get("status") == "shortlisted"),
        "due": sum(1 for item in items if (item.get("candidate_action") or {}).get("level") == "due"),
        "changed": sum(1 for item in items if (item.get("candidate_action") or {}).get("level") == "changed"),
        "ready": sum(1 for item in items if (item.get("candidate_action") or {}).get("level") == "ready"),
    }
