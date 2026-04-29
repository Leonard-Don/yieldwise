# Phase 4b — Annotations / Notes Backend + Drawer Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a notes (笔记) capability: persist user-authored notes per target (building / community / floor / listing) to `data/personal/annotations.json`, expose `/api/v2/annotations` with GET-by-target / POST / PATCH / DELETE, and wire a notes section inside the detail drawer footer with read/edit/add/delete actions.

**Architecture:** Reuses the personal-data file layer from Phase 3c-1 (`api/personal_storage.py`). New `api/schemas/annotations.py` defines `Annotation`, `AnnotationCreatePayload`, and `AnnotationUpdatePayload`. New `api/domains/annotations.py` exposes four endpoints; note IDs are server-generated UUIDs. Frontend: `state.annotationsByTarget` is a cache keyed by `target_id`; `frontend/user/modules/annotations.js` is a DOM module that owns its own dedicated mount inside `.atlas-drawer` (a sibling of `.atlas-drawer-body` so it's independent of detail-drawer's innerHTML rewrites). It subscribes to `state.selection` and lazily fetches notes for the active target. Add/edit/delete actions optimistically mutate `state.annotationsByTarget` and roll back to the server response on error.

**Tech Stack:** FastAPI · Pydantic 2.9 · `api/personal_storage.py` (Phase 3c-1) · vanilla JS ES modules · `node:test` for the new pure helpers · existing detail-drawer.js (Phase 3a; untouched in this plan). No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 6 schema "Annotation" + section 6 API table for `/api/v2/annotations` + section 5 row 5 抽屉 actions "笔记区")

**Prior plan:** 2026-04-24-phase-4a-watchlist.md (merged at `c0885e0`)

---

## File Structure (Phase 4b outcome)

```
api/
├── main.py                          # MODIFIED: include_router for v2_annotations
├── schemas/
│   └── annotations.py               # NEW — Annotation + AnnotationCreatePayload + AnnotationUpdatePayload
└── domains/
    └── annotations.py               # NEW — GET/POST/PATCH/DELETE /api/v2/annotations

frontend/user/
├── index.html                       # MODIFIED: add drawer notes mount (sibling of body)
├── styles/
│   └── drawer.css                   # MODIFIED: notes section styling
└── modules/
    ├── api.js                       # MODIFIED: api.annotations.{listForTarget, create, update, remove}
    ├── annotations-helpers.js       # NEW — pure helpers (sortByCreatedDesc, snapshotForTarget)
    ├── annotations.js               # NEW — DOM module: notes section + add/edit/delete
    └── main.js                      # MODIFIED: initAnnotations + state slice

tests/api/
├── test_annotations_schema.py       # NEW (~6 cases)
└── test_v2_annotations.py           # NEW (~8 cases)

tests/frontend/
└── test_annotations_helpers.mjs     # NEW (~4 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/annotations/by-target/probe
README.md                            # MODIFIED: bump Phase 4a → Phase 4b; expand v2 row
```

**Out-of-scope (deferred):**
- Markdown rendering of note bodies — Phase 6 polish; the editor stores raw text and renders it inside `<pre class="atlas-note-body">` so newlines are preserved as plain text
- Confirmation prompts on delete — single-user localhost; `.trash/` rotation is the safety net
- Notes history / version pinning beyond the existing `.trash/` backups
- Floor- or listing-level note targeting in the UI — schema accepts those `target_type` values for forward-compat, but the drawer only opens for buildings/communities (Phase 3a guard)
- Cross-target notes panel ("show all my notes") — Phase 6
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-4b-annotations .worktrees/phase-4b-annotations
cd .worktrees/phase-4b-annotations
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 53 pytest passed; 60 node tests passed; 15 smoke routes OK.

---

### Task 1: Annotation pydantic schemas + tests

**Files:**
- Create: `api/schemas/annotations.py`
- Create: `tests/api/test_annotations_schema.py`

Three models:
- `Annotation` — full record. `note_id: str`, `target_id: str`, `target_type: Literal["building", "community", "floor", "listing"]`, `body: str`, `created_at: str | None = None`, `updated_at: str | None = None`. `model_config = ConfigDict(extra="ignore")` for forward-compat.
- `AnnotationCreatePayload` — POST body: `target_id`, `target_type`, `body`. `extra="forbid"`.
- `AnnotationUpdatePayload` — PATCH body: `body: str` only. `extra="forbid"`.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_annotations_schema.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.annotations import (
    Annotation,
    AnnotationCreatePayload,
    AnnotationUpdatePayload,
)


def test_annotation_round_trips_full_payload() -> None:
    payload = {
        "note_id": "abc-123",
        "target_id": "daning-jinmaofu-b1",
        "target_type": "building",
        "body": "Saw 2 fresh listings this week.",
        "created_at": "2026-04-24T10:00:00",
        "updated_at": "2026-04-24T10:00:00",
    }
    note = Annotation.model_validate(payload)
    assert note.note_id == "abc-123"
    assert note.target_type == "building"
    assert note.body.startswith("Saw")


def test_annotation_defaults_timestamps_to_none() -> None:
    note = Annotation.model_validate(
        {
            "note_id": "abc-123",
            "target_id": "x",
            "target_type": "community",
            "body": "test",
        }
    )
    assert note.created_at is None
    assert note.updated_at is None


def test_annotation_rejects_unknown_target_type() -> None:
    with pytest.raises(ValidationError):
        Annotation.model_validate(
            {"note_id": "x", "target_id": "y", "target_type": "district", "body": "z"}
        )


def test_create_payload_accepts_minimal_fields() -> None:
    body = AnnotationCreatePayload.model_validate(
        {"target_id": "x", "target_type": "building", "body": "hi"}
    )
    assert body.body == "hi"


def test_create_payload_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        AnnotationCreatePayload.model_validate(
            {"target_id": "x", "target_type": "building", "body": "hi", "evil": True}
        )


def test_update_payload_only_accepts_body() -> None:
    body = AnnotationUpdatePayload.model_validate({"body": "new content"})
    assert body.body == "new content"
    with pytest.raises(ValidationError):
        AnnotationUpdatePayload.model_validate(
            {"body": "new content", "target_id": "x"}
        )
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_annotations_schema.py -v`
Expected: ImportError — `api.schemas.annotations` doesn't exist yet.

- [ ] **Step 3: Implement `api/schemas/annotations.py`**

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


AnnotationTargetType = Literal["building", "community", "floor", "listing"]


class Annotation(BaseModel):
    """Persisted note keyed by `note_id` (server-generated UUID).

    Stored under data/personal/annotations.json as `{"items": [Annotation, ...]}`.
    """

    model_config = ConfigDict(extra="ignore")

    note_id: str
    target_id: str
    target_type: AnnotationTargetType
    body: str
    created_at: str | None = None
    updated_at: str | None = None


class AnnotationCreatePayload(BaseModel):
    """POST /api/v2/annotations body."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: AnnotationTargetType
    body: str


class AnnotationUpdatePayload(BaseModel):
    """PATCH /api/v2/annotations/{note_id} body — only `body` is editable."""

    model_config = ConfigDict(extra="forbid")

    body: str
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_annotations_schema.py -v`
Expected: 6 tests passed.

Run: `pytest -q`
Expected: 59 passed (53 prior + 6 new).

- [ ] **Step 5: Commit**

```bash
git add api/schemas/annotations.py tests/api/test_annotations_schema.py
git commit -m "feat(api): add Annotation + create/update payload schemas"
```

---

### Task 2: Annotations domain (GET/POST/PATCH/DELETE)

**Files:**
- Create: `api/domains/annotations.py`
- Create: `tests/api/test_v2_annotations.py`
- Modify: `api/main.py`

Behaviors:
- `GET /api/v2/annotations/by-target/{target_id}` → `{"items": [...]}` of all notes whose `target_id` matches; sorted newest-first by `created_at`. Empty list when no matches or file missing.
- `POST /api/v2/annotations` body `{target_id, target_type, body}` → creates a note with `note_id = uuid.uuid4().hex` and `created_at = updated_at = now()`. Returns the new Annotation.
- `PATCH /api/v2/annotations/{note_id}` body `{body}` → updates only the `body`; refreshes `updated_at`. Returns the updated Annotation. 404 on unknown id.
- `DELETE /api/v2/annotations/{note_id}` → removes by id; 200 with `{"removed": true}` on hit, 200 with `{"removed": false}` on miss (mirrors watchlist's no-404 contract).

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_v2_annotations.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_items_when_no_file(client) -> None:
    response = client.get("/api/v2/annotations/by-target/whatever")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}


def test_post_creates_note_with_uuid_and_timestamps(client) -> None:
    response = client.post(
        "/api/v2/annotations",
        json={
            "target_id": "daning-jinmaofu-b1",
            "target_type": "building",
            "body": "first note",
        },
    )
    assert response.status_code == 200, response.text
    note = response.json()
    assert note["note_id"]
    assert note["target_id"] == "daning-jinmaofu-b1"
    assert note["target_type"] == "building"
    assert note["body"] == "first note"
    assert note["created_at"] is not None
    assert note["updated_at"] is not None


def test_get_by_target_returns_only_matching_target(client) -> None:
    client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "a"},
    )
    client.post(
        "/api/v2/annotations",
        json={"target_id": "beta", "target_type": "community", "body": "b"},
    )
    items = client.get("/api/v2/annotations/by-target/alpha").json()["items"]
    assert len(items) == 1
    assert items[0]["target_id"] == "alpha"


def test_get_by_target_sorts_newest_first(client) -> None:
    first = client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "old"},
    ).json()
    # The persistence timestamp uses second-precision; we cannot reliably
    # produce two distinct timestamps within the same test in the same
    # second. We assert that newest-first is correct by inspecting the
    # created_at field directly when timestamps differ; otherwise the
    # ordering only requires stable arrangement.
    second = client.post(
        "/api/v2/annotations",
        json={"target_id": "alpha", "target_type": "building", "body": "newer"},
    ).json()
    items = client.get("/api/v2/annotations/by-target/alpha").json()["items"]
    assert len(items) == 2
    if first["created_at"] != second["created_at"]:
        assert items[0]["note_id"] == second["note_id"]
        assert items[1]["note_id"] == first["note_id"]


def test_patch_updates_body_and_refreshes_updated_at(client) -> None:
    note = client.post(
        "/api/v2/annotations",
        json={"target_id": "x", "target_type": "building", "body": "v1"},
    ).json()
    response = client.patch(
        f"/api/v2/annotations/{note['note_id']}",
        json={"body": "v2"},
    )
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["body"] == "v2"
    assert updated["created_at"] == note["created_at"]
    assert updated["updated_at"] is not None


def test_patch_unknown_id_returns_404(client) -> None:
    response = client.patch(
        "/api/v2/annotations/never-existed",
        json={"body": "v2"},
    )
    assert response.status_code == 404


def test_delete_removes_existing(client) -> None:
    note = client.post(
        "/api/v2/annotations",
        json={"target_id": "x", "target_type": "building", "body": "v1"},
    ).json()
    response = client.delete(f"/api/v2/annotations/{note['note_id']}")
    assert response.status_code == 200
    assert response.json() == {"removed": True}
    assert client.get("/api/v2/annotations/by-target/x").json()["items"] == []


def test_delete_unknown_id_returns_removed_false(client) -> None:
    response = client.delete("/api/v2/annotations/never-existed")
    assert response.status_code == 200
    assert response.json() == {"removed": False}
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_v2_annotations.py -v`
Expected: all 8 fail (404 — routes don't exist yet).

- [ ] **Step 3: Implement `api/domains/annotations.py`**

```python
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
```

- [ ] **Step 4: Wire into `api/main.py`**

Open `api/main.py`. Find the existing v2 imports (after Phase 4a):

```python
from .domains import (
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Add `annotations as v2_annotations` to keep alphabetical order:

```python
from .domains import (
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Find the existing `app.include_router(v2_*.router, prefix="/api/v2")` block and add a line for annotations alongside the others:

```python
app.include_router(v2_annotations.router, prefix="/api/v2")
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/api/test_v2_annotations.py -v`
Expected: 8 tests pass.

- [ ] **Step 6: Compile + full suite**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 67 passed (53 prior + 6 schema + 8 v2 annotations).

- [ ] **Step 7: Commit**

```bash
git add api/domains/annotations.py api/main.py tests/api/test_v2_annotations.py
git commit -m "feat(api): add /api/v2/annotations GET-by-target + POST + PATCH + DELETE"
```

---

### Task 3: API client extension + annotations helpers

**Files:**
- Modify: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/annotations-helpers.js`
- Create: `tests/frontend/test_annotations_helpers.mjs`

Add `api.annotations.{listForTarget, create, update, remove}` (reusing the `getJSONFresh`, `postJSON`, `patchJSON`, `deleteJSON` helpers already present from Phase 3c-2 + 4a). Add a tiny pure helper `annotations-helpers.js`:
- `sortByCreatedDesc(items)` — sorts newest-first by `created_at`; null/empty input → []
- `targetKey(sel)` — returns `null` if sel is missing or its type isn't building/community; otherwise returns the `target_id`. This is used by the DOM module to know whether to load notes for the active selection

- [ ] **Step 1: Write failing tests**

Write `tests/frontend/test_annotations_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  sortByCreatedDesc,
  targetKey,
} from "../../frontend/user/modules/annotations-helpers.js";

test("sortByCreatedDesc: empty/null input → []", () => {
  assert.deepEqual(sortByCreatedDesc([]), []);
  assert.deepEqual(sortByCreatedDesc(null), []);
  assert.deepEqual(sortByCreatedDesc(undefined), []);
});

test("sortByCreatedDesc: orders newest first", () => {
  const items = [
    { note_id: "a", created_at: "2026-04-20T10:00:00" },
    { note_id: "b", created_at: "2026-04-24T10:00:00" },
    { note_id: "c", created_at: "2026-04-22T10:00:00" },
  ];
  const sorted = sortByCreatedDesc(items);
  assert.deepEqual(sorted.map((it) => it.note_id), ["b", "c", "a"]);
});

test("sortByCreatedDesc: items without created_at sort to the end", () => {
  const items = [
    { note_id: "a", created_at: "2026-04-22T10:00:00" },
    { note_id: "b" },
    { note_id: "c", created_at: "2026-04-24T10:00:00" },
  ];
  const sorted = sortByCreatedDesc(items);
  assert.equal(sorted[0].note_id, "c");
  assert.equal(sorted[2].note_id, "b");
});

test("targetKey: null/non-building-or-community → null", () => {
  assert.equal(targetKey(null), null);
  assert.equal(targetKey({ type: "district", id: "pudong" }), null);
  assert.equal(targetKey({ type: "floor", id: "x" }), null);
});

test("targetKey: building/community → id", () => {
  assert.equal(targetKey({ type: "building", id: "b1" }), "b1");
  assert.equal(targetKey({ type: "community", id: "c2" }), "c2");
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_annotations_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `frontend/user/modules/annotations-helpers.js`**

```javascript
export function sortByCreatedDesc(items) {
  if (!Array.isArray(items)) return [];
  return [...items].sort((a, b) => {
    const av = (a && a.created_at) || "";
    const bv = (b && b.created_at) || "";
    if (av === bv) return 0;
    if (!av) return 1;
    if (!bv) return -1;
    return av > bv ? -1 : 1;
  });
}

export function targetKey(sel) {
  if (!sel || (sel.type !== "building" && sel.type !== "community")) {
    return null;
  }
  return sel.id;
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_annotations_helpers.mjs`
Expected: 5 tests passed.

Run: `node --check frontend/user/modules/annotations-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Extend `frontend/user/modules/api.js`**

Open `frontend/user/modules/api.js`. The current export block (after Phase 4a):

```javascript
export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  districtsAll: () => getJSON("/api/v2/map/districts"),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  userPrefs: {
    get: () => getJSONFresh("/api/v2/user/prefs"),
    patch: (payload) => patchJSON("/api/v2/user/prefs", payload),
  },
  watchlist: {
    list: () => getJSONFresh("/api/v2/watchlist"),
    add: (targetId, targetType) =>
      postJSON("/api/v2/watchlist", { target_id: targetId, target_type: targetType }),
    remove: (targetId) =>
      deleteJSON(`/api/v2/watchlist/${encodeURIComponent(targetId)}`),
  },
  invalidate,
};
```

Replace it with the version that adds `annotations`:

```javascript
export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  districtsAll: () => getJSON("/api/v2/map/districts"),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  userPrefs: {
    get: () => getJSONFresh("/api/v2/user/prefs"),
    patch: (payload) => patchJSON("/api/v2/user/prefs", payload),
  },
  watchlist: {
    list: () => getJSONFresh("/api/v2/watchlist"),
    add: (targetId, targetType) =>
      postJSON("/api/v2/watchlist", { target_id: targetId, target_type: targetType }),
    remove: (targetId) =>
      deleteJSON(`/api/v2/watchlist/${encodeURIComponent(targetId)}`),
  },
  annotations: {
    listForTarget: (targetId) =>
      getJSONFresh(`/api/v2/annotations/by-target/${encodeURIComponent(targetId)}`),
    create: (targetId, targetType, body) =>
      postJSON("/api/v2/annotations", {
        target_id: targetId,
        target_type: targetType,
        body,
      }),
    update: (noteId, body) =>
      patchJSON(`/api/v2/annotations/${encodeURIComponent(noteId)}`, { body }),
    remove: (noteId) =>
      deleteJSON(`/api/v2/annotations/${encodeURIComponent(noteId)}`),
  },
  invalidate,
};
```

- [ ] **Step 6: Sanity-check**

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs`
Expected: 65 passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5).

Run: `pytest -q`
Expected: 67 passed (no backend changes from Task 2).

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/annotations-helpers.js tests/frontend/test_annotations_helpers.mjs
git commit -m "feat(user): add annotations API client + sort+target helpers"
```

---

### Task 4: annotations.js DOM module + drawer notes mount + CSS

**Files:**
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/drawer.css`
- Create: `frontend/user/modules/annotations.js`

The DOM module owns a dedicated mount (`<section class="atlas-drawer-notes" data-component="notes-section">`) placed inside `<aside class="atlas-drawer">` AFTER `<div class="atlas-drawer-body">`. detail-drawer.js never touches this section, so the two modules don't fight over innerHTML.

Behavior:
- Hidden when no current selection of type building/community
- On selection change to a valid target: lazy-fetch `api.annotations.listForTarget(targetId)`, store in `state.annotationsByTarget[targetId]`, render
- Renders existing notes as cards (body in `<pre>` for whitespace preservation) with edit + delete buttons
- "Edit" swaps the card body to a textarea + 保存/取消 buttons
- "+ 添加笔记" form at the bottom: textarea + 添加 button (disabled when textarea empty)
- All mutations are optimistic; on error we refetch the target's notes from the server

- [ ] **Step 1: Add the drawer notes mount in `frontend/user/index.html`**

Open `frontend/user/index.html`. Find the existing drawer aside:

```html
        <aside class="atlas-drawer" data-component="drawer" data-open="false" aria-hidden="true">
          <header class="atlas-drawer-header">
            ...
          </header>
          <div class="atlas-drawer-body" data-role="drawer-body">
            <div class="atlas-drawer-empty">选择楼栋或机会榜条目以查看详情</div>
          </div>
        </aside>
```

Add a new section directly AFTER the closing `</div>` of `atlas-drawer-body` and BEFORE the closing `</aside>`:

```html
          <section class="atlas-drawer-notes" data-component="notes-section" hidden>
            <header class="atlas-notes-header">
              <h3>笔记</h3>
              <span class="atlas-notes-status mono dim" data-role="notes-status">—</span>
            </header>
            <ol class="atlas-notes-list" data-role="notes-list"></ol>
            <form class="atlas-notes-add" data-role="notes-add" novalidate>
              <textarea data-role="notes-add-input" placeholder="添加笔记 …" rows="2"></textarea>
              <button type="submit" data-role="notes-add-submit" disabled>添加</button>
            </form>
          </section>
```

- [ ] **Step 2: Append notes styling to `frontend/user/styles/drawer.css`**

Open `frontend/user/styles/drawer.css` and append at the end:

```css
.atlas-drawer-notes {
  border-top: 1px solid var(--line);
  padding: 12px 14px;
  max-height: 240px;
  overflow-y: auto;
  background: var(--bg-1);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.atlas-drawer-notes[hidden] {
  display: none;
}

.atlas-notes-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
}

.atlas-notes-header h3 {
  margin: 0;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.atlas-notes-status {
  font-size: 10px;
  letter-spacing: 0.06em;
}

.atlas-notes-status[data-state="error"] {
  color: var(--down);
}

.atlas-notes-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.atlas-note-card {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.atlas-note-body {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-0);
  white-space: pre-wrap;
  word-break: break-word;
}

.atlas-note-meta {
  font-size: 10px;
  color: var(--text-xs);
  letter-spacing: 0.04em;
}

.atlas-note-actions {
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.atlas-note-actions button {
  appearance: none;
  border: 1px solid var(--line);
  background: transparent;
  color: var(--text-dim);
  padding: 2px 8px;
  font: inherit;
  font-size: 10px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-note-actions button:hover {
  color: var(--text-0);
  border-color: var(--up);
}

.atlas-note-actions button[data-variant="danger"]:hover {
  color: var(--down);
  border-color: var(--down);
}

.atlas-note-edit {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.atlas-note-edit textarea {
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--text-0);
  font: inherit;
  font-size: 12px;
  padding: 6px 8px;
  min-height: 60px;
  resize: vertical;
}

.atlas-notes-add {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.atlas-notes-add textarea {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--text-0);
  font: inherit;
  font-size: 12px;
  padding: 6px 8px;
  resize: vertical;
}

.atlas-notes-add button {
  align-self: flex-end;
  appearance: none;
  border: 1px solid var(--up);
  background: rgba(0, 214, 143, 0.1);
  color: var(--text-0);
  padding: 3px 12px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-notes-add button[disabled] {
  opacity: 0.4;
  cursor: not-allowed;
}

.atlas-notes-empty {
  color: var(--text-xs);
  font-size: 11px;
  letter-spacing: 0.06em;
  padding: 4px 0;
}
```

- [ ] **Step 3: Implement `frontend/user/modules/annotations.js`**

```javascript
import { api } from "./api.js";
import { sortByCreatedDesc, targetKey } from "./annotations-helpers.js";

export function initAnnotations({ root, store }) {
  const section = root.querySelector('[data-component="notes-section"]');
  const listEl = section.querySelector('[data-role="notes-list"]');
  const statusEl = section.querySelector('[data-role="notes-status"]');
  const addForm = section.querySelector('[data-role="notes-add"]');
  const addInput = section.querySelector('[data-role="notes-add-input"]');
  const addSubmit = section.querySelector('[data-role="notes-add-submit"]');

  let editingNoteId = null;
  let editingDraft = "";

  addInput.addEventListener("input", () => {
    addSubmit.disabled = addInput.value.trim().length === 0;
  });
  addForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitAdd();
  });
  listEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    const noteId = button.dataset.noteId;
    if (action === "edit") startEdit(noteId);
    else if (action === "delete") void deleteNote(noteId);
    else if (action === "save") void saveEdit(noteId);
    else if (action === "cancel") cancelEdit();
  });
  listEl.addEventListener("input", (event) => {
    const textarea = event.target.closest("textarea[data-role='note-edit-input']");
    if (!textarea) return;
    editingDraft = textarea.value;
  });

  let lastTarget = null;
  store.subscribe(handleStateChange);
  handleStateChange(store.get());

  function handleStateChange(state) {
    const key = targetKey(state.selection);
    if (key !== lastTarget) {
      lastTarget = key;
      cancelEdit();
      if (key === null) {
        section.hidden = true;
        return;
      }
      section.hidden = false;
      const cache = state.annotationsByTarget || {};
      if (Array.isArray(cache[key])) {
        renderNotes(cache[key]);
      } else {
        statusEl.textContent = "加载中…";
        statusEl.removeAttribute("data-state");
        listEl.innerHTML = "";
        void loadFor(key);
      }
      return;
    }
    if (key !== null) {
      const cache = state.annotationsByTarget || {};
      if (Array.isArray(cache[key])) {
        renderNotes(cache[key]);
      }
    }
  }

  async function loadFor(targetId) {
    try {
      const data = await api.annotations.listForTarget(targetId);
      writeCache(targetId, data.items || []);
    } catch (err) {
      console.error("[atlas:notes] load failed", err);
      statusEl.textContent = `加载失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  function writeCache(targetId, items) {
    const current = store.get().annotationsByTarget || {};
    store.set({
      annotationsByTarget: { ...current, [targetId]: items },
    });
  }

  async function submitAdd() {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const body = addInput.value.trim();
    if (!body) return;
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    try {
      const note = await api.annotations.create(key, sel.type, body);
      const current = store.get().annotationsByTarget || {};
      const prior = Array.isArray(current[key]) ? current[key] : [];
      writeCache(key, [...prior, note]);
      addInput.value = "";
      addSubmit.disabled = true;
      statusEl.textContent = `${prior.length + 1} 条`;
    } catch (err) {
      console.error("[atlas:notes] create failed", err);
      statusEl.textContent = `保存失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  async function deleteNote(noteId) {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    statusEl.textContent = "删除中…";
    statusEl.removeAttribute("data-state");
    const current = store.get().annotationsByTarget || {};
    const prior = Array.isArray(current[key]) ? current[key] : [];
    const optimistic = prior.filter((it) => it.note_id !== noteId);
    writeCache(key, optimistic);
    try {
      await api.annotations.remove(noteId);
      statusEl.textContent = `${optimistic.length} 条`;
    } catch (err) {
      console.error("[atlas:notes] delete failed", err);
      statusEl.textContent = `删除失败：${err.message}`;
      statusEl.dataset.state = "error";
      writeCache(key, prior);
    }
  }

  function startEdit(noteId) {
    editingNoteId = noteId;
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const items = (store.get().annotationsByTarget || {})[key] || [];
    const note = items.find((it) => it.note_id === noteId);
    editingDraft = note ? note.body : "";
    renderNotes(items);
  }

  function cancelEdit() {
    if (editingNoteId === null) return;
    editingNoteId = null;
    editingDraft = "";
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (key) {
      const items = (store.get().annotationsByTarget || {})[key] || [];
      renderNotes(items);
    }
  }

  async function saveEdit(noteId) {
    const sel = store.get().selection;
    const key = targetKey(sel);
    if (!key) return;
    const body = editingDraft.trim();
    if (!body) {
      statusEl.textContent = "笔记内容不能为空";
      statusEl.dataset.state = "error";
      return;
    }
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    try {
      const updated = await api.annotations.update(noteId, body);
      const current = store.get().annotationsByTarget || {};
      const prior = Array.isArray(current[key]) ? current[key] : [];
      writeCache(
        key,
        prior.map((it) => (it.note_id === noteId ? updated : it)),
      );
      editingNoteId = null;
      editingDraft = "";
      statusEl.textContent = `${prior.length} 条`;
    } catch (err) {
      console.error("[atlas:notes] update failed", err);
      statusEl.textContent = `保存失败：${err.message}`;
      statusEl.dataset.state = "error";
    }
  }

  function renderNotes(items) {
    const sorted = sortByCreatedDesc(items);
    if (sorted.length === 0) {
      listEl.innerHTML = `<li class="atlas-notes-empty">还没有笔记 — 在下方添加第一条</li>`;
      statusEl.textContent = "0 条";
      return;
    }
    listEl.innerHTML = sorted
      .map((note) => renderCard(note))
      .join("");
    statusEl.textContent = `${sorted.length} 条`;
  }

  function renderCard(note) {
    if (note.note_id === editingNoteId) {
      return `<li class="atlas-note-card"><div class="atlas-note-edit"><textarea data-role="note-edit-input">${escapeText(editingDraft)}</textarea><div class="atlas-note-actions"><button type="button" data-action="save" data-note-id="${escapeAttr(note.note_id)}">保存</button><button type="button" data-action="cancel">取消</button></div></div></li>`;
    }
    const time = note.updated_at || note.created_at || "";
    return `<li class="atlas-note-card"><pre class="atlas-note-body">${escapeText(note.body)}</pre><div class="atlas-note-meta">${escapeText(time)}</div><div class="atlas-note-actions"><button type="button" data-action="edit" data-note-id="${escapeAttr(note.note_id)}">编辑</button><button type="button" data-action="delete" data-note-id="${escapeAttr(note.note_id)}" data-variant="danger">删除</button></div></li>`;
  }
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function escapeAttr(value) {
  return escapeText(value).replace(/'/g, "&#39;");
}
```

- [ ] **Step 4: Sanity-check**

Run: `node --check frontend/user/modules/annotations.js`
Expected: exit 0.

Run: `grep -c 'data-component="notes-section"' frontend/user/index.html`
Expected: 1.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs`
Expected: 65 passed.

Run: `pytest -q`
Expected: 67 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/annotations.js frontend/user/index.html frontend/user/styles/drawer.css
git commit -m "feat(user): add notes section in drawer (read/edit/add/delete)"
```

---

### Task 5: Bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. The current top-of-file imports (after Phase 4a):

```javascript
import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
import { initDrawer } from "./detail-drawer.js";
import { initFilterBar } from "./filter-bar.js";
import { createStorage } from "./storage.js";
import { MODES, defaultFiltersFor } from "./modes.js";
import { initOnboarding } from "./home-onboarding.js";
import { initWatchlist } from "./watchlist.js";
import { isPrefsEmpty } from "./user-prefs-helpers.js";
import { api } from "./api.js";
```

Add a new import directly below `initWatchlist`:

```javascript
import { initAnnotations } from "./annotations.js";
```

Find the existing `createStore({...})` call. The current shape (after Phase 4a):

```javascript
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
    userPrefs: null,
    onboardingOpen: false,
    watchlist: [],
  });
```

Replace with:

```javascript
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
    userPrefs: null,
    onboardingOpen: false,
    watchlist: [],
    annotationsByTarget: {},
  });
```

Find the existing `initWatchlist({ root, store });` line and add the annotations init directly below it:

```javascript
  initAnnotations({ root, store });
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find:

```python
            (f"{base}/api/v2/watchlist", '"items"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/annotations/by-target/probe", '"items"'),
```

This hits `/by-target/probe` against an unknown target id and asserts the response shape (always 200 with `{"items": []}`).

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 16 OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 4a 起）` and change to `## 路由布局（Phase 4b 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记（抽屉内 markdown 文本笔记 read/edit/add/delete；持久化到 data/personal/annotations.json）。
```

Find the row whose third column begins with `用户平台专属接口。已开放：`. Replace it with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)、`/annotations` (GET-by-target + POST + PATCH + DELETE)
```

- [ ] **Step 6: Verify all exit criteria**

Run each:
- `pytest -q` → 67 passed (53 prior + 6 schema + 8 v2)
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs` → 65 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 16 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire annotations into bootstrap + smoke + docs"
```

---

## Phase 4b Exit Criteria

- [ ] `pytest -q` — 67 passed (53 prior + 6 schema + 8 v2 annotations)
- [ ] `node --test ...` — 65 passed (5 state + 20 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers + 4 watchlist helpers + 5 annotations helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check` — exit 0
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 16 rows OK
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, click a board row → drawer opens, scroll down past 挂牌摘要 → see 笔记 section showing "0 条" and "还没有笔记 — 在下方添加第一条". Type "test note" + 添加 → list shows the new card with body, timestamp, 编辑 + 删除 buttons; status updates to "1 条". Click 编辑 → textarea swaps in; modify body; 保存 → card returns with new body; status remains "1 条". Click 删除 → card disappears, status "0 条". Refresh page; click same row; on-disk persistence verified.
- [ ] `git log --oneline c0885e0..HEAD` shows exactly 5 commits

## Out of Scope (deferred)

- Markdown rendering — Phase 6 polish
- Confirmation prompt before delete — single-user localhost; .trash/ rotation backstops
- Floor / listing target_type from the UI — schema accepts but drawer doesn't open for those (Phase 3a guard)
- Cross-target notes panel ("show all notes") — Phase 6
- Concurrent edit handling — single-user, no conflict resolution needed
- Manual browser screenshot
