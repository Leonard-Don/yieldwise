from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.watchlist import (
    WatchlistActionPayload,
    WatchlistAddPayload,
    WatchlistDecisionPayload,
    WatchlistEntry,
    WatchlistPatchPayload,
)
from ..service import get_building, get_community, list_districts

router = APIRouter(tags=["watchlist"])

WATCHLIST_FILE = "watchlist.json"
CANDIDATE_STATUS_LABELS = {
    "watching": "观察",
    "researching": "复核中",
    "shortlisted": "候选",
    "rejected": "搁置",
}
REVIEW_QUEUE_STATUS_RANK = {
    "pending_review": 0,
    "watch": 1,
    "reviewed": 2,
    "dismissed": 3,
}
REVIEW_QUEUE_PENDING_GROUPS = {
    "due_review",
    "target_rule",
    "changed",
    "evidence_missing",
    "shortlisted",
}
TASK_PRIORITY_RANK = {
    "high": 0,
    "medium": 1,
    "low": 2,
}
REVIEW_DIGEST_GROUP_META = {
    "due_review": {
        "label": "到期复核",
        "priority": "high",
        "next": "先重新检查价格、租金、楼层样本和备注。",
    },
    "target_rule": {
        "label": "目标触发",
        "priority": "high",
        "next": "先核对真实房源后决定是否进入候选或放弃。",
    },
    "evidence_missing": {
        "label": "证据缺口",
        "priority": "medium",
        "next": "先补齐公开样本、楼层配对或刷新快照。",
    },
    "changed": {
        "label": "变化复核",
        "priority": "medium",
        "next": "先展开变化提醒并更新本地备忘录。",
    },
    "shortlisted": {
        "label": "候选推进",
        "priority": "medium",
        "next": "先补齐反对理由和下一步动作，准备投决备忘录。",
    },
    "watch": {
        "label": "继续观察",
        "priority": "low",
        "next": "保留关注，下一轮看价格、租金和质量变化。",
    },
    "needs_review": {
        "label": "人工复核",
        "priority": "high",
        "next": "先检查候选状态和任务字段是否完整。",
    },
}
REVIEW_DIGEST_GROUP_RANK = {
    "due_review": 0,
    "target_rule": 1,
    "evidence_missing": 2,
    "changed": 3,
    "shortlisted": 4,
    "watch": 5,
    "needs_review": 6,
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


@router.get("/watchlist/review-queue")
def list_watchlist_review_queue() -> dict[str, Any]:
    queue = build_candidate_review_queue([_enrich_entry(item) for item in _load_entries()])
    return {
        "items": queue,
        "summary": _review_queue_summary(queue),
        "digest": build_candidate_review_digest(queue),
    }


@router.post("/watchlist")
def add_to_watchlist(payload: WatchlistAddPayload) -> dict[str, Any]:
    items = _load_entries()
    now = _now()

    # Idempotent: replace any existing entry with the same target_id, keeping
    # the original list position so the order stays stable.
    replaced = False
    for index, existing in enumerate(items):
        if not _same_target_id(existing.get("target_id"), payload.target_id):
            continue
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
        if not _same_target_id(existing.get("target_id"), target_id):
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
        if not _same_target_id(existing.get("target_id"), target_id):
            continue
        snapshot = _snapshot_for_entry(existing)
        next_entry = _apply_action(existing, payload, snapshot=snapshot, now=now, today=today)
        validated = WatchlistEntry.model_validate(next_entry).model_dump()
        items[index] = validated
        _save_entries(items)
        return _enrich_entry(validated)
    return {"updated": False}


@router.post("/watchlist/{target_id}/review-decision")
def apply_watchlist_review_decision(target_id: str, payload: WatchlistDecisionPayload) -> dict[str, Any]:
    items = _load_entries()
    now = _now()
    today = date.today()
    for index, existing in enumerate(items):
        if not _same_target_id(existing.get("target_id"), target_id):
            continue
        snapshot = _snapshot_for_entry(existing)
        next_entry = _apply_review_decision(existing, payload, snapshot=snapshot, now=now, today=today)
        validated = WatchlistEntry.model_validate(next_entry).model_dump()
        items[index] = validated
        _save_entries(items)
        return _enrich_entry(validated)
    return {"updated": False}


@router.delete("/watchlist/{target_id}")
def remove_from_watchlist(target_id: str) -> dict[str, Any]:
    items = _load_entries()
    next_items = [it for it in items if not _same_target_id(it.get("target_id"), target_id)]
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
            "review_decision": "reviewed",
            "review_decision_at": now,
            "review_decision_note": notes,
            "review_decision_superseded_at": None,
            "notes": notes,
        }
    if payload.action == "defer_review":
        return {
            **entry,
            "updated_at": now,
            "status": "researching" if entry.get("status") != "shortlisted" else entry.get("status"),
            "review_due_at": _date_after(payload.days or 7, today=today),
            "review_decision": None,
            "review_decision_at": None,
            "review_decision_note": None,
            "review_decision_superseded_at": now,
            "notes": notes,
        }
    if payload.action == "shortlist":
        return {
            **entry,
            "updated_at": now,
            "status": "shortlisted",
            "review_due_at": entry.get("review_due_at") or _date_after(payload.days or 7, today=today),
            "review_decision": None,
            "review_decision_at": None,
            "review_decision_note": None,
            "review_decision_superseded_at": now,
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
            "review_decision": "dismissed",
            "review_decision_at": now,
            "review_decision_note": notes,
            "review_decision_superseded_at": None,
            "notes": notes,
        }
    return entry


def _apply_review_decision(
    entry: dict[str, Any],
    payload: WatchlistDecisionPayload,
    *,
    snapshot: dict[str, Any] | None,
    now: str,
    today: date,
) -> dict[str, Any]:
    decision = payload.decision
    note = _clean_text(payload.note)
    record = {
        "decision": decision,
        "decided_at": now,
        "note": note,
    }
    next_entry = {
        **entry,
        "updated_at": now,
        "review_decision": decision,
        "review_decision_at": now,
        "review_decision_note": note,
        "review_decision_superseded_at": None,
        "decision_history": [*_decision_history(entry.get("decision_history")), record],
    }
    if note is not None:
        next_entry["notes"] = note

    if decision == "reviewed":
        return {
            **next_entry,
            "last_reviewed_at": now,
            "last_seen_snapshot": snapshot or entry.get("last_seen_snapshot"),
            "review_due_at": _date_after(14, today=today),
        }
    if decision == "dismissed":
        return {
            **next_entry,
            "status": "rejected",
            "review_due_at": None,
            "last_reviewed_at": now,
            "last_seen_snapshot": snapshot or entry.get("last_seen_snapshot"),
        }
    if decision == "watch":
        return {
            **next_entry,
            "status": "watching",
            "review_due_at": None,
        }
    return next_entry


def _decision_history(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        decision = _clean_text(item.get("decision"))
        decided_at = _clean_text(item.get("decided_at"))
        if decision not in {"reviewed", "dismissed", "watch"} or not decided_at:
            continue
        out.append(
            {
                "decision": decision,
                "decided_at": decided_at,
                "note": _clean_text(item.get("note")),
            }
        )
    return out


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
    target_id = _clean_text(entry.get("target_id")) or ""
    target_type = _clean_text(entry.get("target_type")) or ""
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
    decision = _latest_review_decision(entry)
    if decision == "reviewed" and not _is_due(entry.get("review_due_at")):
        return []
    if decision == "watch":
        return [
            {
                "group": "watch",
                "label": "继续观察",
                "priority": "low",
                "next": "保留关注，下一轮看价格、租金和质量变化。",
            }
        ]
    if decision == "dismissed":
        status = "rejected"
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


def build_candidate_review_queue(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Derive a deterministic decision queue from enriched watchlist candidates."""

    queue = [_candidate_review_queue_item(item) for item in items]
    queue.sort(key=_candidate_review_queue_sort_key)
    return queue


def build_candidate_review_digest(queue: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the review queue into deterministic reviewer next-action buckets."""

    buckets: dict[str, dict[str, Any]] = {}
    action_item_indexes: set[int] = set()
    for index, item in enumerate(queue):
        if not isinstance(item, dict):
            continue
        groups = _review_digest_groups(item)
        if not groups:
            continue
        action_item_indexes.add(index)
        target = _review_digest_target(item)
        target_id = _clean_text(item.get("target_id"))
        for group in groups:
            bucket = buckets.setdefault(group, _review_digest_bucket(group))
            bucket["count"] += 1
            if target_id:
                bucket["target_ids"].append(target_id)
            if len(bucket["top_targets"]) < 3:
                bucket["top_targets"].append(target)

    next_actions = sorted(
        buckets.values(),
        key=lambda bucket: (
            REVIEW_DIGEST_GROUP_RANK.get(str(bucket.get("group") or ""), 99),
            TASK_PRIORITY_RANK.get(str(bucket.get("priority") or "").lower(), 9),
            -int(bucket.get("count") or 0),
            str(bucket.get("group") or ""),
        ),
    )
    top_target = next_actions[0]["top_targets"][0] if next_actions and next_actions[0]["top_targets"] else None
    counts = _review_queue_summary(queue)
    return {
        "counts": counts,
        "open_count": counts["pending_review"] + counts["watch"],
        "next_action_count": len(action_item_indexes),
        "top_target": top_target,
        "next_actions": next_actions,
    }


def _review_digest_bucket(group: str) -> dict[str, Any]:
    meta = REVIEW_DIGEST_GROUP_META.get(group) or REVIEW_DIGEST_GROUP_META["needs_review"]
    return {
        "group": group,
        "label": meta["label"],
        "priority": meta["priority"],
        "next": meta["next"],
        "count": 0,
        "target_ids": [],
        "top_targets": [],
    }


def _review_digest_groups(item: dict[str, Any]) -> list[str]:
    status = str(item.get("status") or "").strip()
    if status in {"reviewed", "dismissed"}:
        return []
    groups: list[str] = []
    for group in _clean_strings(item.get("task_groups")):
        if group in REVIEW_DIGEST_GROUP_META and group not in {"needs_review"}:
            groups.append(group)
    if not groups:
        if status == "pending_review" or not status:
            groups.append("needs_review")
        elif status == "watch":
            groups.append("watch")
    return list(dict.fromkeys(groups))


def _review_digest_target(item: dict[str, Any]) -> dict[str, Any]:
    priority = _maybe_float(item.get("priority"))
    material_delta = _maybe_float(item.get("material_delta"))
    return {
        "target_id": _clean_text(item.get("target_id")),
        "target_name": _clean_text(item.get("target_name"))
        or _clean_text(item.get("target_id"))
        or "未命名候选",
        "target_type": _clean_text(item.get("target_type")) or "unknown",
        "status": _clean_text(item.get("status")) or "needs_review",
        "candidate_status": _clean_text(item.get("candidate_status")),
        "priority": int(priority) if priority is not None else 3,
        "review_date": _clean_text(item.get("review_date")),
        "action_level": _clean_text(item.get("action_level")),
        "task_labels": _clean_strings(item.get("task_labels"))[:3],
        "trigger_labels": _clean_strings(item.get("trigger_labels"))[:3],
        "yield_delta_pct": _round_optional(item.get("yield_delta_pct"), digits=2),
        "material_delta": _round_optional(material_delta, digits=4) or 0.0,
    }


def _candidate_review_queue_item(item: dict[str, Any]) -> dict[str, Any]:
    snapshot = item.get("current_snapshot") if isinstance(item.get("current_snapshot"), dict) else {}
    triggers = item.get("candidate_triggers") if isinstance(item.get("candidate_triggers"), list) else []
    tasks = item.get("candidate_tasks") if isinstance(item.get("candidate_tasks"), list) else []
    current_yield = _normalize_yield_pct(snapshot.get("yield"))
    target_yield = _maybe_float(item.get("target_yield_pct"))
    yield_delta = (
        round(current_yield - target_yield, 2)
        if current_yield is not None and target_yield is not None
        else None
    )
    return {
        "target_id": _clean_text(item.get("target_id")),
        "target_name": item.get("target_name") or snapshot.get("name") or item.get("target_id"),
        "target_type": item.get("target_type"),
        "status": _candidate_review_status(item, tasks),
        "candidate_status": item.get("status") or "watching",
        "review_decision": _latest_review_decision(item),
        "review_decision_at": item.get("review_decision_at"),
        "review_decision_note": item.get("review_decision_note"),
        "priority": int(_maybe_float(item.get("priority")) or 3),
        "review_date": item.get("review_due_at"),
        "reviewed_at": item.get("last_reviewed_at"),
        "current_yield_pct": current_yield,
        "target_yield_pct": target_yield,
        "yield_delta_pct": yield_delta,
        "trigger_labels": [str(trigger.get("label")) for trigger in triggers if trigger.get("label")],
        "trigger_reasons": [
            str(trigger.get("kind") or trigger.get("reason"))
            for trigger in triggers
            if trigger.get("kind") or trigger.get("reason")
        ],
        "task_labels": [str(task.get("label")) for task in tasks if task.get("label")],
        "task_groups": [str(task.get("group")) for task in tasks if task.get("group")],
        "task_priorities": [str(task.get("priority")) for task in tasks if task.get("priority")],
        "action_level": (item.get("candidate_action") or {}).get("level")
        if isinstance(item.get("candidate_action"), dict)
        else None,
        "material_delta": _candidate_material_delta(item, current_yield, target_yield),
        "added_at": item.get("added_at"),
        "updated_at": item.get("updated_at"),
    }


def _candidate_review_status(item: dict[str, Any], tasks: list[dict[str, Any]]) -> str:
    decision = _latest_review_decision(item)
    if decision == "dismissed":
        return "dismissed"
    if decision == "reviewed" and not _is_due(item.get("review_due_at")):
        return "reviewed"
    if decision == "watch":
        return "watch"
    candidate_status = str(item.get("status") or "watching")
    action = item.get("candidate_action") if isinstance(item.get("candidate_action"), dict) else {}
    action_level = str(action.get("level") or "")
    task_groups = {str(task.get("group") or "") for task in tasks}
    if candidate_status == "rejected" or action_level == "rejected" or "rejected" in task_groups:
        return "dismissed"
    if task_groups & REVIEW_QUEUE_PENDING_GROUPS:
        return "pending_review"
    if item.get("last_reviewed_at"):
        return "reviewed"
    return "watch"


def _candidate_material_delta(
    item: dict[str, Any],
    current_yield: float | None,
    target_yield: float | None,
) -> float:
    values: list[float] = []
    if current_yield is not None and target_yield is not None:
        values.append(abs(current_yield - target_yield))
    delta = item.get("snapshot_delta")
    if isinstance(delta, dict):
        for value in delta.values():
            number = _maybe_float(value)
            if number is not None:
                values.append(abs(number))
    triggers = item.get("candidate_triggers")
    if isinstance(triggers, list):
        for trigger in triggers:
            if not isinstance(trigger, dict):
                continue
            number = _maybe_float(trigger.get("delta"))
            if number is not None:
                values.append(abs(number))
    return round(max(values), 4) if values else 0.0


def _candidate_review_queue_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        REVIEW_QUEUE_STATUS_RANK.get(str(item.get("status") or ""), 9),
        _candidate_task_priority_rank(item),
        int(_maybe_float(item.get("priority")) or 3),
        -_candidate_sort_timestamp(item),
        -float(_maybe_float(item.get("material_delta")) or 0.0),
        _clean_text(item.get("target_type")) or "",
        _clean_text(item.get("target_id")) or "",
    )


def _candidate_task_priority_rank(item: dict[str, Any]) -> int:
    ranks = [
        TASK_PRIORITY_RANK.get(str(priority).lower(), 9)
        for priority in item.get("task_priorities", [])
        if priority
    ]
    if ranks:
        return min(ranks)
    return 2 if item.get("status") == "watch" else 9


def _candidate_sort_timestamp(item: dict[str, Any]) -> float:
    value = item.get("updated_at") or item.get("added_at") or item.get("review_date") or ""
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        try:
            return datetime.fromisoformat(f"{str(value)[:10]}T00:00:00").timestamp()
        except ValueError:
            return 0.0


def _review_queue_summary(queue: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "total": len(queue),
        "pending_review": 0,
        "watch": 0,
        "reviewed": 0,
        "dismissed": 0,
    }
    for item in queue:
        status = str(item.get("status") or "")
        if status in summary:
            summary[status] += 1
    return summary


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


def _round_optional(value: Any, *, digits: int) -> float | None:
    number = _maybe_float(value)
    if number is None:
        return None
    return round(number, digits)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, set):
        values = sorted(value, key=lambda item: str(item))
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        return []
    out: list[str] = []
    for item in values:
        text = _clean_text(item)
        if text:
            out.append(text)
    return out


def _same_target_id(left: Any, right: Any) -> bool:
    left_text = _clean_text(left)
    right_text = _clean_text(right)
    return left_text is not None and right_text is not None and left_text == right_text


def _latest_review_decision(entry: dict[str, Any]) -> str | None:
    decision = _clean_text(entry.get("review_decision"))
    if decision in {"reviewed", "dismissed", "watch"}:
        return decision
    history = _decision_history(entry.get("decision_history"))
    if not history:
        return None
    latest = max(history, key=lambda item: _candidate_sort_timestamp({"updated_at": item.get("decided_at")}))
    latest_decision = _clean_text(latest.get("decision"))
    if latest_decision not in {"reviewed", "dismissed", "watch"}:
        return None
    superseded_at = _clean_text(entry.get("review_decision_superseded_at"))
    if superseded_at and _candidate_sort_timestamp({"updated_at": superseded_at}) >= _candidate_sort_timestamp(
        {"updated_at": latest.get("decided_at")}
    ):
        return None
    return latest_decision


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
