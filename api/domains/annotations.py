from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from .. import personal_storage
from ..schemas.annotations import (
    Annotation,
    AnnotationCreatePayload,
    AnnotationUpdatePayload,
)

router = APIRouter(tags=["annotations"])

ANNOTATIONS_FILE = "annotations.json"


def _load_entries() -> list[dict[str, Any]]:
    raw = personal_storage.read_json(ANNOTATIONS_FILE)
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
            items.append(Annotation.model_validate(row).model_dump())
        except Exception:
            continue
    return items


def _save_entries(items: list[dict[str, Any]]) -> None:
    personal_storage.write_json(ANNOTATIONS_FILE, {"items": items})


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


@router.get("/annotations/by-target/{target_id}")
def list_annotations_for_target(target_id: str) -> dict[str, Any]:
    items = [it for it in _load_entries() if it.get("target_id") == target_id]
    items.sort(key=lambda row: row.get("created_at") or "", reverse=True)
    return {"items": items}


@router.post("/annotations")
def create_annotation(payload: AnnotationCreatePayload) -> dict[str, Any]:
    items = _load_entries()
    timestamp = _now()
    note = Annotation(
        note_id=uuid.uuid4().hex,
        target_id=payload.target_id,
        target_type=payload.target_type,
        body=payload.body,
        created_at=timestamp,
        updated_at=timestamp,
    ).model_dump()
    items.append(note)
    _save_entries(items)
    return note


@router.patch("/annotations/{note_id}")
def update_annotation(note_id: str, payload: AnnotationUpdatePayload) -> dict[str, Any]:
    items = _load_entries()
    for index, existing in enumerate(items):
        if existing.get("note_id") == note_id:
            existing["body"] = payload.body
            existing["updated_at"] = _now()
            items[index] = Annotation.model_validate(existing).model_dump()
            _save_entries(items)
            return items[index]
    raise HTTPException(status_code=404, detail="Annotation not found")


@router.delete("/annotations/{note_id}")
def delete_annotation(note_id: str) -> dict[str, Any]:
    items = _load_entries()
    next_items = [it for it in items if it.get("note_id") != note_id]
    if len(next_items) == len(items):
        return {"removed": False}
    _save_entries(next_items)
    return {"removed": True}
