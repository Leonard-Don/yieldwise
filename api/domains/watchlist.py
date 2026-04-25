from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.watchlist import WatchlistAddPayload, WatchlistEntry

router = APIRouter(tags=["watchlist"])

WATCHLIST_FILE = "watchlist.json"


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
    return {"items": _load_entries()}


@router.post("/watchlist")
def add_to_watchlist(payload: WatchlistAddPayload) -> dict[str, Any]:
    items = _load_entries()
    new_entry = WatchlistEntry(
        target_id=payload.target_id,
        target_type=payload.target_type,
        added_at=datetime.now().isoformat(timespec="seconds"),
        last_seen_snapshot=None,
    ).model_dump()

    # Idempotent: replace any existing entry with the same target_id, keeping
    # the original list position so the order stays stable.
    replaced = False
    for index, existing in enumerate(items):
        if existing.get("target_id") == payload.target_id:
            items[index] = new_entry
            replaced = True
            break
    if not replaced:
        items.append(new_entry)

    _save_entries(items)
    return new_entry


@router.delete("/watchlist/{target_id}")
def remove_from_watchlist(target_id: str) -> dict[str, Any]:
    items = _load_entries()
    next_items = [it for it in items if it.get("target_id") != target_id]
    if len(next_items) == len(items):
        return {"removed": False}
    _save_entries(next_items)
    return {"removed": True}
