from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.watchlist import WatchlistActionPayload, WatchlistAddPayload, WatchlistEntry, WatchlistPatchPayload
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


@router.post("/watchlist/{target_id}/actions")
def apply_watchlist_action(target_id: str, payload: WatchlistActionPayload) -> dict[str, Any]:
    items = _load_entries()
    now = _now()
    today = date.today()
    for index, existing in enumerate(items):
        if existing.get("target_id") != target_id:
            continue
        snapshot = _snapshot_for_entry(existing)
        next_entry = _apply_action(existing, payload, snapshot=snapshot, now=now, today=today)
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


def _date_after(days: int, *, today: date) -> str:
    return (today + timedelta(days=days)).isoformat()


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


def _apply_action(
    entry: dict[str, Any],
    payload: WatchlistActionPayload,
    *,
    snapshot: dict[str, Any] | None,
    now: str,
    today: date,
) -> dict[str, Any]:
    notes = payload.notes if payload.notes is not None else entry.get("notes")
    if payload.action == "complete_review":
        return {
            **entry,
            "updated_at": now,
            "last_reviewed_at": now,
            "last_seen_snapshot": snapshot or entry.get("last_seen_snapshot"),
            "review_due_at": _date_after(payload.days or 14, today=today),
            "notes": notes,
        }
    if payload.action == "defer_review":
        return {
            **entry,
            "updated_at": now,
            "status": "researching" if entry.get("status") != "shortlisted" else entry.get("status"),
            "review_due_at": _date_after(payload.days or 7, today=today),
            "notes": notes,
        }
    if payload.action == "shortlist":
        return {
            **entry,
            "updated_at": now,
            "status": "shortlisted",
            "review_due_at": entry.get("review_due_at") or _date_after(payload.days or 7, today=today),
            "notes": notes,
        }
    if payload.action == "reject":
        return {
            **entry,
            "updated_at": now,
            "status": "rejected",
            "review_due_at": None,
            "last_reviewed_at": now,
            "last_seen_snapshot": snapshot or entry.get("last_seen_snapshot"),
            "notes": notes,
        }
    return entry


def _enrich_entry(entry: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot_for_entry(entry)
    delta = _snapshot_delta(entry.get("last_seen_snapshot"), snapshot)
    triggers = _candidate_triggers(entry, snapshot)
    tasks = _candidate_tasks(entry, snapshot, delta, triggers)
    target_name = (snapshot or {}).get("name") or entry.get("target_id")
    return {
        **entry,
        "status_label": CANDIDATE_STATUS_LABELS.get(str(entry.get("status") or ""), "观察"),
        "target_name": target_name,
        "current_snapshot": snapshot,
        "snapshot_delta": delta,
        "candidate_triggers": triggers,
        "candidate_tasks": tasks,
        "candidate_action": _candidate_action(entry, snapshot, delta, triggers, tasks),
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
            "price": record.get("saleMedianWan") or record.get("avgPriceWanEstimate"),
            "rent": record.get("rentMedianMonthly") or record.get("monthlyRentEstimate"),
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
        "topFloorPairCountDelta": _round_delta(
            current.get("topFloorPairCount"),
            previous.get("topFloorPairCount"),
        ),
    }


def _round_delta(current: Any, previous: Any) -> float | None:
    try:
        cur = float(current)
        prev = float(previous)
    except (TypeError, ValueError):
        return None
    return round(cur - prev, 2)


def _candidate_triggers(
    entry: dict[str, Any],
    snapshot: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not snapshot:
        return []
    out: list[dict[str, Any]] = []
    price = _maybe_float(snapshot.get("price"))
    target_price = _maybe_float(entry.get("target_price_wan"))
    if price is not None and target_price is not None and price <= target_price:
        out.append(
            {
                "kind": "target_price_hit",
                "label": "总价低于目标",
                "current": price,
                "target": target_price,
                "delta": round(price - target_price, 2),
            }
        )
    rent = _maybe_float(snapshot.get("rent"))
    target_rent = _maybe_float(entry.get("target_monthly_rent"))
    if rent is not None and target_rent is not None and rent >= target_rent:
        out.append(
            {
                "kind": "target_rent_hit",
                "label": "租金达到目标",
                "current": rent,
                "target": target_rent,
                "delta": round(rent - target_rent, 2),
            }
        )
    yield_pct = _normalize_yield_pct(snapshot.get("yield"))
    target_yield = _maybe_float(entry.get("target_yield_pct"))
    if yield_pct is not None and target_yield is not None and yield_pct >= target_yield:
        out.append(
            {
                "kind": "target_yield_hit",
                "label": "收益率达到目标",
                "current": yield_pct,
                "target": target_yield,
                "delta": round(yield_pct - target_yield, 2),
            }
        )
    return out


def _candidate_tasks(
    entry: dict[str, Any],
    snapshot: dict[str, Any] | None,
    delta: dict[str, Any] | None,
    triggers: list[dict[str, Any]],
) -> list[dict[str, str]]:
    status = str(entry.get("status") or "watching")
    if status == "rejected":
        return [
            {
                "group": "rejected",
                "label": "已放弃",
                "priority": "low",
                "next": "保留记录即可；重新启用前不进入今日队列。",
            }
        ]
    if not snapshot:
        return [
            {
                "group": "evidence_missing",
                "label": "缺当前快照",
                "priority": "high",
                "next": "刷新数据或移出候选。",
            }
        ]

    tasks: list[dict[str, str]] = []
    if _is_due(entry.get("review_due_at")):
        tasks.append(
            {
                "group": "due_review",
                "label": "到期复核",
                "priority": "high",
                "next": "重新检查价格、租金、楼层样本和备注。",
            }
        )
    for trigger in triggers:
        tasks.append(
            {
                "group": "target_rule",
                "label": str(trigger.get("label") or "目标触发"),
                "priority": "high",
                "next": "核对真实房源后决定是否进入候选或放弃。",
            }
        )
    if _has_material_delta(delta):
        label = "同楼层新样本" if _delta_value(delta, "topFloorPairCountDelta") > 0 else "价格/收益变化"
        tasks.append(
            {
                "group": "changed",
                "label": label,
                "priority": "medium",
                "next": "展开变化提醒并更新本地备忘录。",
            }
        )
    if snapshot.get("qualityStatus") in {"blocked", "thin"}:
        tasks.append(
            {
                "group": "evidence_missing",
                "label": "证据不足",
                "priority": "medium",
                "next": snapshot.get("decisionNextAction") or "先补齐公开样本和楼层配对。",
            }
        )
    if status == "shortlisted":
        tasks.append(
            {
                "group": "shortlisted",
                "label": "已 shortlist",
                "priority": "medium",
                "next": "补齐反对理由和下一步动作，准备投决备忘录。",
            }
        )
    if not tasks and snapshot.get("qualityStatus") in {"strong", "usable"}:
        tasks.append(
            {
                "group": "ready",
                "label": "可比较",
                "priority": "low",
                "next": snapshot.get("decisionNextAction") or "加入对比并生成备忘录。",
            }
        )
    return tasks


def _candidate_action(
    entry: dict[str, Any],
    snapshot: dict[str, Any] | None,
    delta: dict[str, Any] | None,
    triggers: list[dict[str, Any]],
    tasks: list[dict[str, str]],
) -> dict[str, str]:
    del delta, triggers
    if tasks:
        first = tasks[0]
        return {
            "level": first.get("group") or "ready",
            "label": first.get("label") or "观察",
            "next": first.get("next") or "继续观察。",
        }
    if not snapshot:
        return {"level": "blocked", "label": "缺当前快照", "next": "先刷新数据或移出候选。"}
    return {"level": "ready", "label": "可比较", "next": snapshot.get("decisionNextAction") or "加入对比并生成备忘录。"}


def _research_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    task_counts: dict[str, int] = {
        "due_review": 0,
        "target_rule": 0,
        "changed": 0,
        "evidence_missing": 0,
        "shortlisted": 0,
    }
    for item in items:
        seen_groups: set[str] = set()
        for task in item.get("candidate_tasks") or []:
            group = str(task.get("group") or "")
            if group in task_counts and group not in seen_groups:
                task_counts[group] += 1
                seen_groups.add(group)
    return {
        "total": len(items),
        "shortlisted": sum(1 for item in items if item.get("status") == "shortlisted"),
        "due": task_counts["due_review"],
        "changed": task_counts["changed"],
        "ready": sum(1 for item in items if (item.get("candidate_action") or {}).get("level") == "ready"),
        "target_rule": task_counts["target_rule"],
        "evidence_missing": task_counts["evidence_missing"],
        "task_groups": task_counts,
    }


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _normalize_yield_pct(value: Any) -> float | None:
    number = _maybe_float(value)
    if number is None:
        return None
    return number * 100.0 if number < 1 else number


def _is_due(value: Any) -> bool:
    if not value:
        return False
    try:
        due_date = date.fromisoformat(str(value)[:10])
    except ValueError:
        return False
    return due_date <= date.today()


def _has_material_delta(delta: dict[str, Any] | None) -> bool:
    if not delta:
        return False
    thresholds = {
        "yieldDeltaPct": 0.01,
        "priceDeltaWan": 0.01,
        "rentDeltaMonthly": 0.01,
        "scoreDelta": 0.01,
        "topFloorPairCountDelta": 1.0,
    }
    for key, threshold in thresholds.items():
        value = _maybe_float(delta.get(key))
        if value is not None and abs(value) >= threshold:
            return True
    return False


def _delta_value(delta: dict[str, Any] | None, key: str) -> float:
    if not delta:
        return 0.0
    return _maybe_float(delta.get(key)) or 0.0
