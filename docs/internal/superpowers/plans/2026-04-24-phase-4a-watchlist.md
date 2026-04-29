# Phase 4a — Watchlist (★) Backend + Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a watchlist (★) capability: persist a list of starred buildings/communities to `data/personal/watchlist.json`, expose `/api/v2/watchlist` with GET/POST/DELETE, and wire a star toggle inside the detail drawer plus a topbar count chip.

**Architecture:** Reuses the personal-data file layer shipped in Phase 3c-1 (`api/personal_storage.py`). New `api/schemas/watchlist.py` defines `WatchlistEntry` (Pydantic) and `WatchlistAddPayload` (POST body). New `api/domains/watchlist.py` exposes `GET /api/v2/watchlist` (list), `POST /api/v2/watchlist` (idempotent add — duplicate target_id replaces same entry), and `DELETE /api/v2/watchlist/{target_id}` (no-op on missing). Frontend: `state.watchlist` slice holds the entries; `frontend/user/modules/watchlist.js` renders the ★ button inside the drawer header (toggling on click) and a topbar `★ N` chip. Drawer integration is additive — the existing detail-drawer body is untouched.

**Tech Stack:** FastAPI · Pydantic 2.9 · `api/personal_storage.py` (Phase 3c-1) · vanilla JS ES modules · `node:test` for the new pure helpers · existing `/api/v2/buildings/{id}` and `/api/v2/communities/{id}` for selection context. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 6 schema "WatchlistEntry" + section 6 API table for `/api/v2/watchlist` + section 5 row 5 抽屉 actions "★" + section 5 row 2 顶栏 "关注计数")

**Prior plan:** 2026-04-24-phase-3d-city-mode.md (merged at `f3995ea`)

---

## File Structure (Phase 4a outcome)

```
api/
├── main.py                          # MODIFIED: include_router for v2_watchlist
├── schemas/
│   └── watchlist.py                 # NEW — WatchlistEntry + WatchlistAddPayload
└── domains/
    └── watchlist.py                 # NEW — GET + POST + DELETE /api/v2/watchlist

frontend/user/
├── index.html                       # MODIFIED: add topbar ★ chip + drawer ★ button mount
├── styles/
│   ├── shell.css                    # MODIFIED: ★ chip + button styling
│   └── drawer.css                   # MODIFIED: ★ button position in header
└── modules/
    ├── api.js                       # MODIFIED: add api.watchlist.{list,add,remove}
    ├── watchlist-helpers.js         # NEW — pure helpers (isStarred, sameEntry)
    ├── watchlist.js                 # NEW — DOM module: ★ toggle + topbar chip
    └── main.js                      # MODIFIED: prefetch watchlist + initWatchlist

tests/api/
├── test_watchlist_schema.py         # NEW (~5 cases)
└── test_v2_watchlist.py             # NEW (~7 cases — list/add/remove/idempotency/persistence)

tests/frontend/
└── test_watchlist_helpers.mjs       # NEW (~4 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/watchlist returns 200
README.md                            # MODIFIED: bump Phase 3d → Phase 4a
```

**Out-of-scope (deferred):**
- Annotations / notes — Phase 4b
- Watchlist panel on topbar click (showing the list) — Phase 6 polish; click currently is a no-op besides displaying count
- `last_seen_snapshot` populated on add — Phase 5 (alerts) needs the baseline; for Phase 4a we always store `null`
- Bulk operations (multi-add, clear-all) — out of scope; one-at-a-time CRUD is sufficient
- ★ glyph on map polygons / board rows — Phase 6 polish; Phase 4a only places it in the drawer header

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-4a-watchlist .worktrees/phase-4a-watchlist
cd .worktrees/phase-4a-watchlist
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 40 pytest passed; 56 node tests passed; 14 smoke routes OK.

---

### Task 1: WatchlistEntry pydantic schemas + tests

**Files:**
- Create: `api/schemas/watchlist.py`
- Create: `tests/api/test_watchlist_schema.py`

Two models:
- `WatchlistEntry` — `target_id: str`, `target_type: Literal["building", "community"]`, `added_at: str | None = None` (ISO timestamp), `last_seen_snapshot: dict | None = None`. `model_config = ConfigDict(extra="ignore")` so old serialized rows survive future field additions.
- `WatchlistAddPayload` — POST body with `target_id` and `target_type` only. `extra="forbid"` so unknown fields 422.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_watchlist_schema.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.watchlist import WatchlistAddPayload, WatchlistEntry


def test_entry_round_trips_full_payload() -> None:
    payload = {
        "target_id": "daning-jinmaofu-b1",
        "target_type": "building",
        "added_at": "2026-04-24T10:00:00",
        "last_seen_snapshot": {"yieldAvg": 0.04, "score": 66},
    }
    entry = WatchlistEntry.model_validate(payload)
    assert entry.target_id == "daning-jinmaofu-b1"
    assert entry.target_type == "building"
    assert entry.last_seen_snapshot == {"yieldAvg": 0.04, "score": 66}


def test_entry_defaults_optional_fields_to_none() -> None:
    entry = WatchlistEntry.model_validate(
        {"target_id": "pudong-xyz", "target_type": "community"}
    )
    assert entry.added_at is None
    assert entry.last_seen_snapshot is None


def test_entry_rejects_invalid_target_type() -> None:
    with pytest.raises(ValidationError):
        WatchlistEntry.model_validate({"target_id": "x", "target_type": "district"})


def test_add_payload_accepts_minimal() -> None:
    body = WatchlistAddPayload.model_validate(
        {"target_id": "daning-jinmaofu-b1", "target_type": "building"}
    )
    assert body.target_id == "daning-jinmaofu-b1"


def test_add_payload_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        WatchlistAddPayload.model_validate(
            {"target_id": "x", "target_type": "building", "evil": True}
        )


def test_add_payload_rejects_missing_required() -> None:
    with pytest.raises(ValidationError):
        WatchlistAddPayload.model_validate({"target_id": "x"})
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_watchlist_schema.py -v`
Expected: ImportError — `api.schemas.watchlist` doesn't exist yet.

- [ ] **Step 3: Implement `api/schemas/watchlist.py`**

```python
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


TargetType = Literal["building", "community"]


class WatchlistEntry(BaseModel):
    """A single watchlist row persisted under data/personal/watchlist.json.

    `last_seen_snapshot` is reserved for Phase 5 (alerts) — Phase 4a always
    writes None. Existing rows with stored snapshots are preserved on read
    via the existing pydantic round-trip.
    """

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: TargetType
    added_at: str | None = None
    last_seen_snapshot: dict[str, Any] | None = None


class WatchlistAddPayload(BaseModel):
    """POST body for /api/v2/watchlist."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: TargetType
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_watchlist_schema.py -v`
Expected: 6 tests passed.

Run: `pytest -q`
Expected: 46 passed (40 prior + 6 new).

- [ ] **Step 5: Commit**

```bash
git add api/schemas/watchlist.py tests/api/test_watchlist_schema.py
git commit -m "feat(api): add WatchlistEntry and WatchlistAddPayload schemas"
```

---

### Task 2: Watchlist domain (GET / POST / DELETE)

**Files:**
- Create: `api/domains/watchlist.py`
- Create: `tests/api/test_v2_watchlist.py`
- Modify: `api/main.py`

Behaviors:
- `GET /api/v2/watchlist` → `{"items": [...]}` (list of WatchlistEntry dumps); empty list when file missing or corrupt.
- `POST /api/v2/watchlist` body `{target_id, target_type}` → adds new entry with `added_at = now()` and `last_seen_snapshot = null`. **Idempotent**: if `target_id` already exists, replace the existing entry (refreshing `added_at`). Returns the new entry.
- `DELETE /api/v2/watchlist/{target_id}` → removes by id; 200 with `{"removed": true}` on hit, 200 with `{"removed": false}` on miss (no 404 — keeps the frontend re-render simple).

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_v2_watchlist.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_items_when_no_file(client) -> None:
    response = client.get("/api/v2/watchlist")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}


def test_post_adds_entry_with_added_at(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "daning-jinmaofu-b1", "target_type": "building"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["target_id"] == "daning-jinmaofu-b1"
    assert body["target_type"] == "building"
    assert body["added_at"] is not None
    assert body["last_seen_snapshot"] is None

    follow = client.get("/api/v2/watchlist").json()
    assert len(follow["items"]) == 1
    assert follow["items"][0]["target_id"] == "daning-jinmaofu-b1"


def test_post_is_idempotent_replaces_existing(client) -> None:
    first = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    ).json()
    second = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    ).json()
    items = client.get("/api/v2/watchlist").json()["items"]
    assert len(items) == 1
    # added_at refreshed (or at least preserved as not-null)
    assert second["added_at"] is not None
    assert first["target_id"] == second["target_id"]


def test_delete_removes_entry(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "building"},
    )
    response = client.delete("/api/v2/watchlist/x")
    assert response.status_code == 200, response.text
    assert response.json() == {"removed": True}
    assert client.get("/api/v2/watchlist").json()["items"] == []


def test_delete_missing_id_returns_removed_false(client) -> None:
    response = client.delete("/api/v2/watchlist/never-existed")
    assert response.status_code == 200
    assert response.json() == {"removed": False}


def test_post_rejects_invalid_target_type_with_422(client) -> None:
    response = client.post(
        "/api/v2/watchlist",
        json={"target_id": "x", "target_type": "district"},
    )
    assert response.status_code == 422


def test_post_then_get_preserves_order_oldest_first(client) -> None:
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "first", "target_type": "building"},
    )
    client.post(
        "/api/v2/watchlist",
        json={"target_id": "second", "target_type": "community"},
    )
    items = client.get("/api/v2/watchlist").json()["items"]
    assert [it["target_id"] for it in items] == ["first", "second"]
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_v2_watchlist.py -v`
Expected: all 7 tests fail (404 — route does not exist).

- [ ] **Step 3: Implement `api/domains/watchlist.py`**

```python
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
```

- [ ] **Step 4: Wire into `api/main.py`**

Open `api/main.py`. Find the existing v2 imports — they currently look like:

```python
from .domains import (
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
)
```

Add `watchlist as v2_watchlist` to keep alphabetical order:

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

Find the existing block of `app.include_router(v2_*.router, prefix="/api/v2")` lines and add a new line at the end (or alongside the user_prefs include — order does not matter to FastAPI as long as no path conflicts):

```python
app.include_router(v2_watchlist.router, prefix="/api/v2")
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/api/test_v2_watchlist.py -v`
Expected: 7 tests pass.

- [ ] **Step 6: Compile + full suite**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 53 passed (40 prior + 6 schema + 7 v2 watchlist).

- [ ] **Step 7: Commit**

```bash
git add api/domains/watchlist.py api/main.py tests/api/test_v2_watchlist.py
git commit -m "feat(api): add /api/v2/watchlist GET + POST + DELETE"
```

---

### Task 3: API client extension + watchlist helpers

**Files:**
- Modify: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/watchlist-helpers.js`
- Create: `tests/frontend/test_watchlist_helpers.mjs`

We add `api.watchlist.{list, add, remove}` and a tiny pure helper module `watchlist-helpers.js` exporting `isStarred(items, targetId)`.

- [ ] **Step 1: Write failing tests for the helper**

Write `tests/frontend/test_watchlist_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  isStarred,
  watchlistCount,
} from "../../frontend/user/modules/watchlist-helpers.js";

test("isStarred: empty list → false", () => {
  assert.equal(isStarred([], "abc"), false);
  assert.equal(isStarred(null, "abc"), false);
  assert.equal(isStarred(undefined, "abc"), false);
});

test("isStarred: matching target_id → true", () => {
  const items = [{ target_id: "abc", target_type: "building" }];
  assert.equal(isStarred(items, "abc"), true);
});

test("isStarred: non-matching id → false", () => {
  const items = [{ target_id: "abc", target_type: "building" }];
  assert.equal(isStarred(items, "xyz"), false);
});

test("watchlistCount: returns array length, defaults to 0", () => {
  assert.equal(watchlistCount([]), 0);
  assert.equal(watchlistCount(null), 0);
  assert.equal(watchlistCount([{ target_id: "a" }, { target_id: "b" }]), 2);
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_watchlist_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `frontend/user/modules/watchlist-helpers.js`**

```javascript
export function isStarred(items, targetId) {
  if (!Array.isArray(items)) return false;
  for (const entry of items) {
    if (entry && entry.target_id === targetId) return true;
  }
  return false;
}

export function watchlistCount(items) {
  return Array.isArray(items) ? items.length : 0;
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_watchlist_helpers.mjs`
Expected: 4 tests passed.

Run: `node --check frontend/user/modules/watchlist-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Extend `frontend/user/modules/api.js`**

Open `frontend/user/modules/api.js`. The current export block (after Phase 3c-2) is:

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
  invalidate,
};
```

We need a `DELETE` helper too. Add directly above the `export const api`:

```javascript
async function deleteJSON(url) {
  const response = await fetch(url, { method: "DELETE" });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}

async function postJSON(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}
```

Then expand the `api` object to include the watchlist namespace. Replace the existing block with:

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

- [ ] **Step 6: Sanity-check**

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs`
Expected: 60 passed (5 + 20 + 11 + 6 + 9 + 5 + 4).

Run: `pytest -q`
Expected: 53 passed (no backend changes from Task 2).

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/watchlist-helpers.js tests/frontend/test_watchlist_helpers.mjs
git commit -m "feat(user): add watchlist API client + emptiness helpers"
```

---

### Task 4: watchlist.js DOM module + drawer ★ button + topbar chip

**Files:**
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/shell.css`
- Modify: `frontend/user/styles/drawer.css`
- Create: `frontend/user/modules/watchlist.js`

The DOM module:
- Renders the topbar chip (text: `★ N` or `★ —` while loading)
- Maintains a star button inside the existing drawer header (added via index.html)
- On star click: optimistic update of `state.watchlist`, then call API; on failure roll back
- The button is shown only when `state.selection.type` is `building` or `community`

- [ ] **Step 1: Add the topbar ★ chip + drawer ★ button mount in `frontend/user/index.html`**

Open `frontend/user/index.html`. Find the topbar block:

```html
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
        <nav class="atlas-modes" data-component="mode-chips" aria-label="模式切换"></nav>
        <div class="atlas-topbar-spacer"></div>
        <button type="button" class="atlas-prefs-button" data-component="prefs-button">偏好</button>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
      </header>
```

Replace with (insert ★ chip BEFORE the prefs button so the order is `chips · spacer · star · prefs · runtime`):

```html
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
        <nav class="atlas-modes" data-component="mode-chips" aria-label="模式切换"></nav>
        <div class="atlas-topbar-spacer"></div>
        <span class="atlas-star-tag mono" data-component="watchlist-count" title="关注数">★ —</span>
        <button type="button" class="atlas-prefs-button" data-component="prefs-button">偏好</button>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
      </header>
```

Find the existing drawer header inside `<aside class="atlas-drawer">`:

```html
          <header class="atlas-drawer-header">
            <div>
              <h2 class="atlas-drawer-title" data-role="drawer-title">—</h2>
              <span class="atlas-drawer-subtitle mono" data-role="drawer-subtitle">—</span>
            </div>
            <button type="button" class="atlas-drawer-close" data-role="drawer-close" aria-label="关闭">×</button>
          </header>
```

Replace with (add ★ button between the title block and the × close):

```html
          <header class="atlas-drawer-header">
            <div>
              <h2 class="atlas-drawer-title" data-role="drawer-title">—</h2>
              <span class="atlas-drawer-subtitle mono" data-role="drawer-subtitle">—</span>
            </div>
            <div class="atlas-drawer-actions">
              <button type="button" class="atlas-drawer-star" data-component="drawer-star" aria-pressed="false" hidden>★</button>
              <button type="button" class="atlas-drawer-close" data-role="drawer-close" aria-label="关闭">×</button>
            </div>
          </header>
```

- [ ] **Step 2: Append topbar ★ chip styling to `frontend/user/styles/shell.css`**

Open the file and append at the end:

```css
.atlas-star-tag {
  font-size: 11px;
  letter-spacing: 0.06em;
  color: var(--text-dim);
  padding: 4px 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--bg-2);
}

.atlas-star-tag[data-active="true"] {
  color: var(--warn);
  border-color: var(--warn);
}
```

- [ ] **Step 3: Append drawer ★ button styling to `frontend/user/styles/drawer.css`**

Open the file and append at the end:

```css
.atlas-drawer-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.atlas-drawer-star {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 14px;
  width: 28px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
}

.atlas-drawer-star[aria-pressed="true"] {
  color: var(--warn);
  border-color: var(--warn);
  background: rgba(255, 176, 32, 0.08);
}

.atlas-drawer-star:hover {
  color: var(--warn);
}

.atlas-drawer-star[disabled] {
  opacity: 0.5;
  cursor: progress;
}
```

- [ ] **Step 4: Implement `frontend/user/modules/watchlist.js`**

```javascript
import { api } from "./api.js";
import { isStarred, watchlistCount } from "./watchlist-helpers.js";

export function initWatchlist({ root, store }) {
  const countEl = root.querySelector('[data-component="watchlist-count"]');
  const starButton = root.querySelector('[data-component="drawer-star"]');

  starButton.addEventListener("click", () => {
    void toggleStar();
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const items = state.watchlist;
    if (!Array.isArray(items)) {
      countEl.textContent = "★ —";
      countEl.removeAttribute("data-active");
    } else {
      countEl.textContent = `★ ${watchlistCount(items)}`;
      countEl.setAttribute("data-active", items.length > 0 ? "true" : "false");
    }
    syncStarButton(state);
  }

  function syncStarButton(state) {
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) {
      starButton.hidden = true;
      starButton.setAttribute("aria-pressed", "false");
      return;
    }
    starButton.hidden = false;
    starButton.disabled = false;
    starButton.setAttribute(
      "aria-pressed",
      isStarred(state.watchlist, sel.id) ? "true" : "false",
    );
  }

  async function toggleStar() {
    const state = store.get();
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) return;
    const items = Array.isArray(state.watchlist) ? state.watchlist : [];
    const currentlyStarred = isStarred(items, sel.id);
    starButton.disabled = true;
    try {
      if (currentlyStarred) {
        const next = items.filter((it) => it.target_id !== sel.id);
        store.set({ watchlist: next });
        await api.watchlist.remove(sel.id);
      } else {
        const optimistic = {
          target_id: sel.id,
          target_type: sel.type,
          added_at: new Date().toISOString().slice(0, 19),
          last_seen_snapshot: null,
        };
        store.set({ watchlist: [...items, optimistic] });
        const saved = await api.watchlist.add(sel.id, sel.type);
        const next = store
          .get()
          .watchlist.map((it) => (it.target_id === sel.id ? saved : it));
        store.set({ watchlist: next });
      }
    } catch (err) {
      console.error("[atlas:watchlist] toggle failed", err);
      // Roll back to whatever the server says.
      try {
        const fresh = await api.watchlist.list();
        store.set({ watchlist: fresh.items || [] });
      } catch (refetchErr) {
        console.error("[atlas:watchlist] refetch failed", refetchErr);
      }
    } finally {
      starButton.disabled = false;
    }
  }
}
```

- [ ] **Step 5: Sanity-check**

Run: `node --check frontend/user/modules/watchlist.js`
Expected: exit 0.

Run: `grep -c 'data-component="watchlist-count"' frontend/user/index.html`
Expected: 1.

Run: `grep -c 'data-component="drawer-star"' frontend/user/index.html`
Expected: 1.

- [ ] **Step 6: Commit**

```bash
git add frontend/user/modules/watchlist.js frontend/user/index.html frontend/user/styles/shell.css frontend/user/styles/drawer.css
git commit -m "feat(user): add watchlist module + drawer star + topbar count chip"
```

---

### Task 5: Bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

We:
1. Initialize `state.watchlist = []` in the createStore call
2. Prefetch via `api.watchlist.list()` and stash in store
3. Wire `initWatchlist({ root, store })` after the existing module initializations

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. The current top of the file (after Phase 3c-2):

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
import { isPrefsEmpty } from "./user-prefs-helpers.js";
import { api } from "./api.js";
```

Add a new import directly below the `initOnboarding` import (alphabetical-ish):

```javascript
import { initWatchlist } from "./watchlist.js";
```

Find the `createStore({...})` call. The current shape is:

```javascript
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
    userPrefs: null,
    onboardingOpen: false,
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
  });
```

Find the existing `api.userPrefs.get().then(...)` block. After it, add another fire-and-forget block for the watchlist:

```javascript
  api.watchlist
    .list()
    .then((data) => store.set({ watchlist: data.items || [] }))
    .catch((err) => console.warn("[atlas] watchlist prefetch failed", err));
```

Find the existing `initOnboarding({ root, store });` line. Add the watchlist init directly below it:

```javascript
  initWatchlist({ root, store });
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find:

```python
            (f"{base}/api/v2/user/prefs", '"districts"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/watchlist", '"items"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 15 OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 3d 起）` and change to `## 路由布局（Phase 4a 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★：抽屉内 ★ 按钮 + 顶栏 ★ 计数；持久化到 data/personal/watchlist.json）。
```

Find the row whose third column begins with `用户平台专属接口。已开放：`. The full current text is:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)
```

Replace with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)
```

- [ ] **Step 6: Verify all exit criteria**

Run each:
- `pytest -q` → 53 passed (40 prior + 6 schema + 7 v2)
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs` → 60 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 15 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire watchlist into bootstrap + smoke + docs"
```

---

## Phase 4a Exit Criteria

- [ ] `pytest -q` — 53 passed (40 prior + 6 schema + 7 v2 watchlist)
- [ ] `node --test ...` — 60 passed (5 state + 20 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers + 4 watchlist helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check` — exit 0 each
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 15 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running. Click a board row → drawer opens, ★ button shows pressed=false; click ★ → button flips to pressed=true; topbar ★ count increments. Click ★ again → flips back. Refresh page → state persists; topbar count reflects on-disk file. `data/personal/watchlist.json` exists.
- [ ] `git log --oneline f3995ea..HEAD` shows exactly 5 commits

## Out of Scope (deferred)

- Annotations / notes — Phase 4b
- Watchlist panel popover on topbar click — Phase 6
- `last_seen_snapshot` populated on POST — Phase 5 (alerts baseline)
- ★ markers on map polygons / board rows — Phase 6
- Bulk operations (multi-add, clear-all) — out of scope
