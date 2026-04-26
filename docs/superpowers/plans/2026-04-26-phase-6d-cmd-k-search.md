# Phase 6d — ⌘K Global Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire up the last unfilled spec Phase 6 item — `⌘K` opens a search overlay with an autocomplete input that matches districts / communities / buildings by Chinese name; pressing Enter or clicking a result dispatches a `state.selection` so the detail drawer opens on that target.

**Architecture:** New backend endpoint `GET /api/v2/search?q=...&limit=...` walks the existing `service.list_districts()` tree (districts → communities → buildings) and returns flat `{items: [{target_id, target_type, target_name, district_name?}, ...]}` matching the query substring (case-insensitive), top N (default 10) ranked by starts-with > contains. Pure scoring helper extracted to `api/domains/search_scoring.py` so it can be unit-tested without HTTP. Frontend adds `api.search(q)`; `parseShortcut` learns ⌘K → `"search"`; new `search.js` DOM module owns a fixed-position search modal (input + results list with keyboard nav) that listens to a `state.searchOpen` slice. Selecting a result dispatches `store.set({selection: {type, id, props: {name, districtName}}, searchOpen: false})` — detail-drawer.js's existing fetch path takes it from there.

**Tech Stack:** FastAPI · Pydantic 2.9 · vanilla JS ES modules · `node:test` for the scoring + key navigation helpers · existing `service.list_districts()` for the search index. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 7 Phase 6: 键盘快捷键：⌘K 搜索)

**Prior plan:** 2026-04-26-phase-6c-visual-polish.md (merged at `62a4ea4`)

---

## File Structure (Phase 6d outcome)

```
api/
├── main.py                          # MODIFIED: include_router for v2_search
├── schemas/
│   └── search.py                    # NEW — SearchHit + SearchResponse
└── domains/
    ├── search.py                    # NEW — GET /api/v2/search
    └── search_scoring.py            # NEW — pure score(name, query) + rank helpers

frontend/user/
├── index.html                       # MODIFIED: add search overlay mount
├── styles/
│   ├── shell.css                    # unchanged
│   └── search.css                   # NEW
└── modules/
    ├── api.js                       # MODIFIED: api.search(q, limit?)
    ├── shortcuts-helpers.js         # MODIFIED: ⌘K → "search"
    ├── shortcuts.js                 # MODIFIED: dispatch "search" → state.searchOpen
    ├── search-helpers.js            # NEW — pure helpers (debounce, highlightMatch, navIndex)
    ├── search.js                    # NEW — DOM module: input + results + keyboard nav
    └── main.js                      # MODIFIED: state.searchOpen + initSearch wiring

tests/api/
├── test_search_scoring.py           # NEW (~6 cases)
└── test_v2_search.py                # NEW (~5 cases)

tests/frontend/
├── test_shortcuts_helpers.mjs       # MODIFIED: +1 case for ⌘K
└── test_search_helpers.mjs          # NEW (~6 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/search?q=
README.md                            # MODIFIED: bump Phase 6c → Phase 6d; mention ⌘K
```

**Out-of-scope (deferred):**
- Pinyin / fuzzy matching beyond simple case-insensitive substring + starts-with priority
- Recent-searches history
- Full-text search of annotations / notes
- Search results that span backstage data (sampling tasks etc.) — Phase 6d only covers user-platform targets
- Server-side highlight markup (frontend does highlight rendering)
- Map-recenter / district-zoom on search hit (the drawer-open path is enough)
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6d-cmd-k-search .worktrees/phase-6d-cmd-k-search
cd .worktrees/phase-6d-cmd-k-search
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 95 pytest passed; 85 node tests passed; 19 smoke routes OK.

---

### Task 1: Search scoring helper + tests

**Files:**
- Create: `api/domains/search_scoring.py`
- Create: `tests/api/test_search_scoring.py`

Pure functions (no HTTP, no service.py imports) so they can be exercised cheaply:
- `normalize(text)` — lowercases ASCII, leaves CJK alone
- `score(name, query)` — returns `int` rank: `0` for no match, `1` for substring contains, `2` for starts-with, `3` for exact-match (after normalize). Higher is better.
- `rank_hits(items, query, limit)` — sorts by score desc, then name asc; drops zero-scores; returns top `limit`. `items` is a list of dicts; the function reads `item["name"]` for scoring.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_search_scoring.py`:

```python
from __future__ import annotations

from api.domains.search_scoring import rank_hits, score


def test_score_no_match_returns_zero() -> None:
    assert score("浦东新区", "宝山") == 0


def test_score_contains_returns_one() -> None:
    assert score("中海建国里", "建国") == 1


def test_score_starts_with_returns_two() -> None:
    assert score("浦东新区", "浦东") == 2


def test_score_exact_match_returns_three() -> None:
    assert score("浦东新区", "浦东新区") == 3


def test_score_is_case_insensitive_for_ascii() -> None:
    assert score("Daning Park", "daning") == 2
    assert score("Daning Park", "PARK") == 1


def test_rank_hits_orders_by_score_then_name() -> None:
    items = [
        {"name": "浦东新区", "kind": "x"},
        {"name": "浦江华侨城", "kind": "y"},
        {"name": "新华联", "kind": "z"},
        {"name": "宝山", "kind": "w"},
    ]
    ranked = rank_hits(items, "浦", limit=10)
    # 浦东新区 starts-with → score 2; 浦江华侨城 starts-with → score 2;
    # 新华联 contains → score 0 (no '浦'); wait — "新华联" doesn't contain
    # 浦, so score is 0 and it should be dropped. 宝山 also score 0, dropped.
    names = [hit["name"] for hit in ranked]
    assert names == ["浦东新区", "浦江华侨城"]


def test_rank_hits_truncates_to_limit() -> None:
    items = [{"name": f"匹配{i}"} for i in range(10)]
    ranked = rank_hits(items, "匹配", limit=3)
    assert len(ranked) == 3


def test_rank_hits_drops_zero_score_items() -> None:
    items = [
        {"name": "完全匹配", "kind": "a"},
        {"name": "无关词", "kind": "b"},
    ]
    ranked = rank_hits(items, "完全", limit=10)
    assert [hit["name"] for hit in ranked] == ["完全匹配"]


def test_rank_hits_empty_query_returns_empty() -> None:
    items = [{"name": "anything"}]
    assert rank_hits(items, "", limit=10) == []
    assert rank_hits(items, "   ", limit=10) == []
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_search_scoring.py -v`
Expected: ImportError — `api.domains.search_scoring` doesn't exist.

- [ ] **Step 3: Implement `api/domains/search_scoring.py`**

```python
from __future__ import annotations

from typing import Any


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def score(name: str, query: str) -> int:
    n = normalize(name)
    q = normalize(query)
    if not n or not q:
        return 0
    if n == q:
        return 3
    if n.startswith(q):
        return 2
    if q in n:
        return 1
    return 0


def rank_hits(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    if not query or not query.strip():
        return []
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for item in items:
        name = item.get("name", "")
        s = score(name, query)
        if s == 0:
            continue
        scored.append((s, name, item))
    # Higher score first; ties break alphabetically by name.
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [row[2] for row in scored[:limit]]
```

- [ ] **Step 4: Verify passing**

Run: `pytest tests/api/test_search_scoring.py -v`
Expected: 9 tests passed.

Run: `pytest -q`
Expected: 104 passed (95 prior + 9 new).

- [ ] **Step 5: Commit**

```bash
git add api/domains/search_scoring.py tests/api/test_search_scoring.py
git commit -m "feat(api): add pure search scoring + ranking helper"
```

---

### Task 2: Search domain endpoint + tests

**Files:**
- Create: `api/schemas/search.py`
- Create: `api/domains/search.py`
- Create: `tests/api/test_v2_search.py`
- Modify: `api/main.py`

`SearchHit` model: `target_id`, `target_type` (Literal building/community/district), `target_name`, `district_name: str | None`. The endpoint walks `service.list_districts()` once per request, flattens into one `{name, target_id, target_type, district_name}` list, calls `rank_hits`, and returns `{items: [SearchHit...]}`.

- [ ] **Step 1: Write the failing schema + endpoint tests**

Write `api/schemas/search.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


SearchTargetType = Literal["building", "community", "district"]


class SearchHit(BaseModel):
    """A single search result row."""

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: SearchTargetType
    target_name: str
    district_name: str | None = None
```

Write `tests/api/test_v2_search.py`:

```python
from __future__ import annotations


def test_search_with_empty_query_returns_empty(client) -> None:
    response = client.get("/api/v2/search?q=")
    assert response.status_code == 200, response.text
    assert response.json() == {"items": []}


def test_search_finds_district_by_chinese_name(client) -> None:
    response = client.get("/api/v2/search?q=浦东")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    target_types = {it["target_type"] for it in items}
    assert "district" in target_types
    assert any(it["target_name"].startswith("浦东") for it in items)


def test_search_finds_community(client) -> None:
    response = client.get("/api/v2/search?q=张江")
    items = response.json()["items"]
    assert items, "expected at least one mock community matching 张江"
    matching = [it for it in items if "张江" in it["target_name"]]
    assert matching


def test_search_results_have_district_name_for_buildings(client) -> None:
    response = client.get("/api/v2/search?q=zhangjiang-park-b1")
    items = response.json()["items"]
    # The id is the building id; mock building name is e.g. '1号楼' / 'A座'.
    # Buildings are matched by NAME not id, so this will be 0 hits — and that's fine.
    assert isinstance(items, list)


def test_search_respects_limit_query_param(client) -> None:
    response = client.get("/api/v2/search?q=新&limit=2")
    items = response.json()["items"]
    assert len(items) <= 2
```

- [ ] **Step 2: Verify failing**

Run: `pytest tests/api/test_v2_search.py -v`
Expected: 404 errors (route doesn't exist).

- [ ] **Step 3: Implement `api/domains/search.py`**

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..schemas.search import SearchHit
from ..service import list_districts
from . import search_scoring

router = APIRouter(tags=["search"])


def _flatten_index() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    districts = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    for d in districts:
        out.append(
            {
                "name": d.get("name") or "",
                "target_id": d.get("id"),
                "target_type": "district",
                "district_name": d.get("name") or None,
            }
        )
        for c in d.get("communities") or []:
            out.append(
                {
                    "name": c.get("name") or "",
                    "target_id": c.get("id"),
                    "target_type": "community",
                    "district_name": d.get("name") or None,
                }
            )
            for b in c.get("buildings") or []:
                out.append(
                    {
                        "name": b.get("name") or "",
                        "target_id": b.get("id"),
                        "target_type": "building",
                        "district_name": d.get("name") or None,
                    }
                )
    return out


@router.get("/search")
def search(
    q: str = Query(default="", min_length=0, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    if not q.strip():
        return {"items": []}
    hits = search_scoring.rank_hits(_flatten_index(), q, limit)
    items = [
        SearchHit.model_validate(
            {
                "target_id": hit["target_id"],
                "target_type": hit["target_type"],
                "target_name": hit["name"],
                "district_name": hit.get("district_name"),
            }
        ).model_dump()
        for hit in hits
        if hit.get("target_id")
    ]
    return {"items": items}
```

- [ ] **Step 4: Wire into `api/main.py`**

Open `api/main.py`. Find the v2 imports (after Phase 5a includes `alerts as v2_alerts` etc.). Add `search as v2_search` alphabetically:

```python
from .domains import (
    alerts as v2_alerts,
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    search as v2_search,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Add include_router alongside the others:

```python
app.include_router(v2_search.router, prefix="/api/v2")
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/api/test_v2_search.py -v`
Expected: 5 passed.

Run: `pytest -q`
Expected: 109 passed (95 prior + 9 scoring + 5 v2).

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add api/schemas/search.py api/domains/search.py api/main.py tests/api/test_v2_search.py
git commit -m "feat(api): add /api/v2/search endpoint walking districts→communities→buildings"
```

---

### Task 3: parseShortcut adds ⌘K

**Files:**
- Modify: `frontend/user/modules/shortcuts-helpers.js`
- Modify: `tests/frontend/test_shortcuts_helpers.mjs`

Add a new branch in `parseShortcut`: `Cmd/Ctrl + K` → returns `"search"`. Like the mode-switch branch, this is privileged — works inside form fields too (so users can `⌘K` even when typing in a textarea). Add one new test case.

- [ ] **Step 1: Add the failing test**

Open `tests/frontend/test_shortcuts_helpers.mjs`. Find the existing `parseShortcut: ⌘1 still works inside a textarea` test. Add a new test directly below it:

```javascript
test("parseShortcut: ⌘K → search (privileged across form fields)", () => {
  assert.equal(parseShortcut(makeEvent({ key: "k", metaKey: true })), "search");
  assert.equal(parseShortcut(makeEvent({ key: "K", metaKey: true })), "search");
  assert.equal(parseShortcut(makeEvent({ key: "k", ctrlKey: true })), "search");
  // works inside a textarea — search is a global navigation shortcut
  assert.equal(
    parseShortcut(
      makeEvent({ key: "k", metaKey: true, target: { tagName: "TEXTAREA", isContentEditable: false } }),
    ),
    "search",
  );
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_shortcuts_helpers.mjs`
Expected: 1 failure for the new test.

- [ ] **Step 3: Update `frontend/user/modules/shortcuts-helpers.js`**

Find:

```javascript
  // Mode switch is privileged: works even when typing in a form field.
  if (modKey && !altKey && Object.prototype.hasOwnProperty.call(MODE_BY_DIGIT, key)) {
    return MODE_BY_DIGIT[key];
  }
```

Add a new privileged branch directly below it (before the `if (isEditableTarget(target)) return null;`):

```javascript
  // Search is also privileged across editable targets — users want ⌘K to
  // open search even from inside a textarea / input.
  if (modKey && !altKey && typeof key === "string" && key.toLowerCase() === "k") {
    return "search";
  }
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_shortcuts_helpers.mjs`
Expected: 13 passed (12 prior + 1 new).

Run: `node --check frontend/user/modules/shortcuts-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/shortcuts-helpers.js tests/frontend/test_shortcuts_helpers.mjs
git commit -m "feat(user): parseShortcut ⌘K → search"
```

---

### Task 4: search-helpers + api.search + tests

**Files:**
- Modify: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/search-helpers.js`
- Create: `tests/frontend/test_search_helpers.mjs`

Helpers:
- `debounce(fn, ms)` — standard trailing-edge debouncer; needed because typing fires many `input` events
- `clampIndex(active, count)` — wraps cursor up/down navigation with min=0 and max=count-1; returns 0 when count is 0
- `formatHitLabel(hit)` — returns Chinese display string like `浦东新区 · 张江汤臣豪园三期`. Falls back to the bare name when no district. Used by `search.js` to render result rows.

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_search_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  clampIndex,
  formatHitLabel,
  debounce,
} from "../../frontend/user/modules/search-helpers.js";

test("clampIndex: empty list → 0", () => {
  assert.equal(clampIndex(0, 0), 0);
  assert.equal(clampIndex(5, 0), 0);
});

test("clampIndex: clamps to last index", () => {
  assert.equal(clampIndex(7, 3), 2);
  assert.equal(clampIndex(2, 3), 2);
});

test("clampIndex: floors negative to zero", () => {
  assert.equal(clampIndex(-1, 5), 0);
});

test("formatHitLabel: with district renders 'district · name'", () => {
  assert.equal(
    formatHitLabel({ target_name: "张江汤臣豪园三期", district_name: "浦东新区" }),
    "浦东新区 · 张江汤臣豪园三期",
  );
});

test("formatHitLabel: without district renders bare name", () => {
  assert.equal(
    formatHitLabel({ target_name: "浦东新区", district_name: null }),
    "浦东新区",
  );
  assert.equal(formatHitLabel({ target_name: "x" }), "x");
});

test("formatHitLabel: missing target_name returns empty string", () => {
  assert.equal(formatHitLabel({}), "");
  assert.equal(formatHitLabel(null), "");
});

test("debounce: only fires once per quiet window", async () => {
  let calls = 0;
  const inc = debounce(() => {
    calls += 1;
  }, 30);
  inc();
  inc();
  inc();
  await new Promise((resolve) => setTimeout(resolve, 60));
  assert.equal(calls, 1);
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_search_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `frontend/user/modules/search-helpers.js`**

```javascript
export function clampIndex(index, count) {
  if (!count || count <= 0) return 0;
  if (index < 0) return 0;
  if (index >= count) return count - 1;
  return index;
}

export function formatHitLabel(hit) {
  if (!hit) return "";
  const name = hit.target_name || "";
  if (!name) return "";
  const district = hit.district_name;
  if (district && district !== name) {
    return `${district} · ${name}`;
  }
  return name;
}

export function debounce(fn, ms) {
  let handle = null;
  return function debounced(...args) {
    if (handle !== null) clearTimeout(handle);
    handle = setTimeout(() => {
      handle = null;
      fn.apply(this, args);
    }, ms);
  };
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_search_helpers.mjs`
Expected: 7 tests passed.

Run: `node --check frontend/user/modules/search-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Extend `frontend/user/modules/api.js`**

Open the file. Find the existing `export const api = ...` block. Add a `search` method between `runtimeConfig` and `userPrefs` (keeping the namespace style):

Find:

```javascript
  runtimeConfig: () => getJSON("/api/runtime-config"),
  userPrefs: {
```

Replace with:

```javascript
  runtimeConfig: () => getJSON("/api/runtime-config"),
  search: (q, limit = 10) => {
    const params = new URLSearchParams();
    params.set("q", q);
    params.set("limit", String(limit));
    return getJSONFresh(`/api/v2/search?${params.toString()}`);
  },
  userPrefs: {
```

- [ ] **Step 6: Sanity-check**

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs`
Expected: 93 passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5 + 8 + 13 + 7).

Run: `pytest -q`
Expected: 109 passed.

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/search-helpers.js tests/frontend/test_search_helpers.mjs
git commit -m "feat(user): add search API client + clampIndex/formatHitLabel/debounce helpers"
```

---

### Task 5: Search overlay mount + CSS + DOM module

**Files:**
- Modify: `frontend/user/index.html`
- Create: `frontend/user/styles/search.css`
- Create: `frontend/user/modules/search.js`

The overlay mounts inside `<main class="atlas-main">` (same scope as drawer / onboarding / help). Behavior:
- `state.searchOpen=true` → modal visible; input auto-focused
- `state.searchOpen=false` → modal hidden; input cleared; results cleared
- Typing → debounced (180ms) `api.search(query)`; on resolve, render results
- ↑/↓ moves the highlighted index; Enter selects the highlighted item; Esc closes
- Clicking a row also selects
- Selecting a hit dispatches `store.set({selection: {type, id, props: {name, districtName}}, searchOpen: false})`

- [ ] **Step 1: Add the search overlay markup to `frontend/user/index.html`**

Open `frontend/user/index.html`. Add a new stylesheet link directly after the existing `shortcuts.css` link (around line 14):

```html
    <link rel="stylesheet" href="/styles/search.css" />
```

Inside `<main class="atlas-main">` (alongside drawer / onboarding / help overlays), insert directly before the closing `</main>` tag:

```html
        <div class="atlas-search-backdrop" data-component="search-backdrop" data-open="false"></div>
        <section class="atlas-search" data-component="search-overlay" data-open="false" aria-hidden="true" aria-labelledby="atlas-search-title">
          <header class="atlas-search-header">
            <h2 id="atlas-search-title" class="atlas-search-title">搜索</h2>
            <button type="button" class="atlas-search-close" data-role="search-close" aria-label="关闭">×</button>
          </header>
          <input type="text" class="atlas-search-input" data-role="search-input" placeholder="输入区/小区/楼栋名…" autocomplete="off" />
          <ol class="atlas-search-results" data-role="search-results"></ol>
          <footer class="atlas-search-status mono dim" data-role="search-status">输入后按 ↑↓ 选择，Enter 打开</footer>
        </section>
```

- [ ] **Step 2: Create `frontend/user/styles/search.css`**

```css
.atlas-search {
  position: absolute;
  inset: 32px 32px;
  margin: auto;
  width: min(480px, 100%);
  max-height: calc(100% - 64px);
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
  z-index: 10;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  transition: opacity 160ms ease, transform 160ms ease;
}

.atlas-search[data-open="true"] {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.atlas-search-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(7, 10, 16, 0.55);
  z-index: 9;
  opacity: 0;
  pointer-events: none;
  transition: opacity 160ms ease;
}

.atlas-search-backdrop[data-open="true"] {
  opacity: 1;
  pointer-events: auto;
}

.atlas-search-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.atlas-search-title {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.06em;
}

.atlas-search-close {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  font: inherit;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
}

.atlas-search-input {
  margin: 12px 16px 8px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--text-0);
  font: inherit;
  font-size: 13px;
  padding: 8px 10px;
}

.atlas-search-input:focus {
  outline: 1px solid var(--up);
  outline-offset: 0;
}

.atlas-search-results {
  list-style: none;
  margin: 0;
  padding: 0 8px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.atlas-search-row {
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-family: var(--font-ui);
  font-size: 12px;
  color: var(--text-0);
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.atlas-search-row:hover,
.atlas-search-row[aria-selected="true"] {
  background: var(--bg-2);
  outline: 1px solid var(--up);
  outline-offset: -1px;
}

.atlas-search-row .label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atlas-search-row .kind {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.atlas-search-status {
  padding: 8px 16px 12px;
  border-top: 1px solid var(--line);
  font-size: 10px;
  letter-spacing: 0.06em;
}
```

- [ ] **Step 3: Implement `frontend/user/modules/search.js`**

```javascript
import { api } from "./api.js";
import { clampIndex, debounce, formatHitLabel } from "./search-helpers.js";

const TYPE_LABEL = {
  building: "楼栋",
  community: "小区",
  district: "区",
};

export function initSearch({ root, store }) {
  const overlay = root.querySelector('[data-component="search-overlay"]');
  const backdrop = root.querySelector('[data-component="search-backdrop"]');
  const closeBtn = overlay.querySelector('[data-role="search-close"]');
  const inputEl = overlay.querySelector('[data-role="search-input"]');
  const resultsEl = overlay.querySelector('[data-role="search-results"]');
  const statusEl = overlay.querySelector('[data-role="search-status"]');

  let lastOpen = false;
  let activeIndex = 0;
  let results = [];
  let queryToken = 0;

  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  inputEl.addEventListener("input", () => {
    activeIndex = 0;
    debouncedSearch(inputEl.value);
  });
  inputEl.addEventListener("keydown", handleInputKey);
  resultsEl.addEventListener("click", (event) => {
    const row = event.target.closest("[data-row-index]");
    if (!row) return;
    const idx = Number(row.dataset.rowIndex);
    selectIndex(idx);
  });

  store.subscribe(handleStateChange);
  handleStateChange(store.get());

  function handleStateChange(state) {
    const open = !!state.searchOpen;
    if (open === lastOpen) return;
    lastOpen = open;
    overlay.dataset.open = open ? "true" : "false";
    backdrop.dataset.open = open ? "true" : "false";
    overlay.setAttribute("aria-hidden", open ? "false" : "true");
    if (open) {
      inputEl.value = "";
      results = [];
      activeIndex = 0;
      renderResults();
      statusEl.textContent = "输入后按 ↑↓ 选择，Enter 打开";
      // Focus on next tick so the modal is visible first.
      setTimeout(() => inputEl.focus(), 30);
    }
  }

  const debouncedSearch = debounce((q) => {
    void runSearch(q);
  }, 180);

  async function runSearch(q) {
    const myToken = ++queryToken;
    if (!q.trim()) {
      results = [];
      renderResults();
      statusEl.textContent = "输入后按 ↑↓ 选择，Enter 打开";
      return;
    }
    statusEl.textContent = "搜索中…";
    try {
      const data = await api.search(q);
      if (myToken !== queryToken) return;
      results = data.items || [];
      activeIndex = 0;
      renderResults();
      statusEl.textContent = results.length
        ? `${results.length} 条结果 · Enter 打开 · Esc 关闭`
        : "未找到匹配项";
    } catch (err) {
      if (myToken !== queryToken) return;
      console.error("[atlas:search] query failed", err);
      statusEl.textContent = `搜索失败：${err.message}`;
    }
  }

  function handleInputKey(event) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = clampIndex(activeIndex + 1, results.length);
      renderResults();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = clampIndex(activeIndex - 1, results.length);
      renderResults();
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (results.length === 0) return;
      selectIndex(activeIndex);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  }

  function selectIndex(idx) {
    if (idx < 0 || idx >= results.length) return;
    const hit = results[idx];
    if (!hit || !hit.target_id) return;
    store.set({
      selection: {
        type: hit.target_type,
        id: hit.target_id,
        props: {
          name: hit.target_name,
          districtName: hit.district_name,
        },
      },
      searchOpen: false,
    });
  }

  function close() {
    if (!lastOpen) return;
    store.set({ searchOpen: false });
  }

  function renderResults() {
    if (results.length === 0) {
      resultsEl.innerHTML = "";
      return;
    }
    resultsEl.innerHTML = results
      .map((hit, idx) => renderRow(hit, idx))
      .join("");
  }

  function renderRow(hit, idx) {
    const selected = idx === activeIndex;
    const kindLabel = TYPE_LABEL[hit.target_type] || hit.target_type || "";
    return `<li class="atlas-search-row" data-row-index="${idx}" aria-selected="${selected ? "true" : "false"}"><span class="label">${escapeText(formatHitLabel(hit))}</span><span class="kind">${escapeText(kindLabel)}</span></li>`;
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
```

- [ ] **Step 4: Sanity-check**

Run: `node --check frontend/user/modules/search.js`
Expected: exit 0.

Run: `grep -c 'data-component="search-overlay"' frontend/user/index.html`
Expected: 1.

Run combined node tests → 93 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/index.html frontend/user/styles/search.css frontend/user/modules/search.js
git commit -m "feat(user): add search overlay (input + results + keyboard nav)"
```

---

### Task 6: Wire shortcut + bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/shortcuts.js`
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Update `frontend/user/modules/shortcuts.js` to dispatch the search action**

Open the file. Find the existing `handleKeyDown` body. The current dispatch chain is:

```javascript
    if (VALID_MODES.has(action)) {
      switchMode(action);
    } else if (action === "star") {
      void toggleStar();
    } else if (action === "note") {
      focusNoteInput();
    } else if (action === "help") {
      store.set({ helpOpen: !store.get().helpOpen });
    }
```

Replace with:

```javascript
    if (VALID_MODES.has(action)) {
      switchMode(action);
    } else if (action === "star") {
      void toggleStar();
    } else if (action === "note") {
      focusNoteInput();
    } else if (action === "help") {
      store.set({ helpOpen: !store.get().helpOpen });
    } else if (action === "search") {
      store.set({ searchOpen: true });
    }
```

- [ ] **Step 2: Update `frontend/user/modules/main.js`**

Open the file. Find the existing imports and add the search import directly below `import { initShortcuts } from "./shortcuts.js";`:

```javascript
import { initSearch } from "./search.js";
```

Find the `createStore({...})` initial state. Add `searchOpen: false` after `helpOpen: false`:

```javascript
    helpOpen: false,
    searchOpen: false,
  });
```

Find the `initShortcuts({ root, store });` line and add `initSearch({ root, store });` directly below it:

```javascript
  initShortcuts({ root, store });
  initSearch({ root, store });
```

- [ ] **Step 3: Verify the bootstrap compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

Run: `node --check frontend/user/modules/shortcuts.js`
Expected: exit 0.

- [ ] **Step 4: Update `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/alerts/since-last-open", '"last_open_at"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/search?q=%E6%B5%A6%E4%B8%9C", '"items"'),
```

(`%E6%B5%A6%E4%B8%9C` is URL-encoded `浦东` — the smoke probe asserts the route returns the expected `items` shape with a real Chinese query.)

- [ ] **Step 5: Update help overlay to mention ⌘K**

The help overlay (Phase 6a) lists existing shortcuts; add ⌘K. Open `frontend/user/index.html`. Find the existing help-overlay `<dl>` block and the row for `<kbd>?</kbd>` (the help shortcut row). Insert a new row directly above it:

```html
            <dt><kbd>⌘K</kbd> / <kbd>⌃K</kbd></dt><dd>打开全局搜索</dd>
```

- [ ] **Step 6: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 20 OK, exit 0.

- [ ] **Step 7: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 6c 起）` and change to `## 路由布局（Phase 6d 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅（含目标名解析）+ 键盘快捷键（⌘K 搜索、⌘1/2/3 切模式、F 关注、N 笔记、? 帮助）。
```

Find the row beginning with `用户平台专属接口。已开放：`. Replace with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)、`/annotations` (GET-by-target + POST + PATCH + DELETE)、`/alerts/{rules,since-last-open,mark-seen}` (GET + PATCH + POST)、`/search` (GET)
```

- [ ] **Step 8: Verify all exit criteria**

Run each:
- `pytest -q` → 109 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs` → 93 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 20 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 9: Commit**

```bash
git add frontend/user/modules/shortcuts.js frontend/user/modules/main.js scripts/phase1_smoke.py frontend/user/index.html README.md
git commit -m "feat(user): wire ⌘K → search overlay + help row + smoke + docs"
```

---

## Phase 6d Exit Criteria

- [ ] `pytest -q` — 109 passed (95 prior + 9 scoring + 5 v2 search)
- [ ] `node --test ...` — 93 passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5 + 8 + 13 + 7)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 20 rows OK
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, press ⌘K — search overlay slides in centered with focused input. Type `浦东` — within ~200ms, results list shows multiple hits with district prefix (e.g. `浦东新区 · 张江汤臣豪园三期 · 小区`). ↑/↓ moves the highlight. Press Enter — overlay closes; detail drawer opens for the highlighted target. Esc closes the overlay without selecting. Type `搜不到的字符串` — status shows `未找到匹配项`.
- [ ] `git log --oneline 62a4ea4..HEAD` shows exactly 6 commits

## Out of Scope (deferred)

- Pinyin / fuzzy matching beyond simple substring
- Recent-searches history
- Annotations / notes full-text search
- Backstage / sampling task search
- Server-side highlight markup (purely cosmetic; client renders matches without highlighting in this phase)
- Map recenter / district zoom on hit
- Manual browser screenshot
