# Phase 3b — Filter Bar + Per-Mode Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing filter-bar placeholder live: each mode gets a default filter set (e.g. yield → `租售比 ≥ 4% / 总价 ≤ 1500 万`), filters are sent to `/api/v2/opportunities`, displayed as removable chips, persisted per mode in `localStorage`, and the right end of the bar shows the current match count.

**Architecture:** Pure frontend addition. A new `filters` slice on the existing pub/sub store holds `{[modeId]: filterObject}`. A new `frontend/user/modules/filter-bar.js` renders the chip UI from `state.filters[state.mode]` and dispatches `store.set({filters: {...}})` on remove. `frontend/user/modules/storage.js` handles localStorage round-trips (with safe fallback when storage is blocked). `modes.js` learns a `defaultFilters` field per mode. `opportunity-board.js` reads filters out of state and passes them to the API. URL `?mode=` already round-trips from Phase 2b — filters live only in localStorage for this phase (URL filter sync deferred).

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for store/storage/filter helpers · existing `/api/v2/opportunities` endpoint (already accepts `min_yield`, `max_budget`, `min_samples`, `min_score` — no backend changes). No new deps.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (Phase 3 — section 7; section 5 三模式语义 row "默认筛选"; section 5 row 3 "筛选条")

**Prior plans:** 2026-04-24-phase-2b-frontend-map-board.md (merged at `3acc392`), 2026-04-24-phase-3a-detail-drawer.md (merged at `8c49a0c` plus follow-up `b7cd2d6`)

---

## File Structure (Phase 3b outcome)

```
frontend/user/
├── index.html                       # MODIFIED: replace filter-bar placeholder with mount slots
├── styles/
│   └── shell.css                    # MODIFIED: add filter chip styling
└── modules/
    ├── modes.js                     # MODIFIED: add defaultFilters per mode
    ├── storage.js                   # NEW — safe localStorage wrapper
    ├── filter-bar.js                # NEW — chip rendering + remove + count
    ├── opportunity-board.js         # MODIFIED: pass filters to api.opportunities
    └── main.js                      # MODIFIED: wire initFilterBar + rehydrate from storage

tests/frontend/
├── test_modes.mjs                   # MODIFIED: add defaultFilters cases
├── test_storage.mjs                 # NEW (~6 cases — get/set/missing/corrupt)
└── test_filter_helpers.mjs          # NEW (~7 cases — filter→params, chip labels)

scripts/phase1_smoke.py              # MODIFIED: +1 substring assertion for filter-bar mount
README.md                            # MODIFIED: bump Phase 3a → Phase 3b section header
```

**Out-of-scope (deferred):**
- Filter editor / "+ add filter" popover — for Phase 3b chips are READ-ONLY (display + remove). Adding new filter dimensions interactively is Phase 3c or later.
- URL `?filters=...` round-trip — for Phase 3b filters persist only in localStorage; URL only carries `?mode=`.
- Home mode default filters that depend on user budget/area — needs onboarding (Phase 3c).
- City mode district map color band — separate Phase 3d.
- Per-mode viewport memory — Phase 6 polish.
- Backend filter parameters beyond what `/api/v2/opportunities` already accepts.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-3b-filter-bar .worktrees/phase-3b-filter-bar
cd .worktrees/phase-3b-filter-bar
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs
python3 scripts/phase1_smoke.py
```

Expected: 20 pytest passed; 23 node tests passed; 10 smoke routes OK. If any check fails, stop — Phase 3a follow-up `b7cd2d6` should be on main.

---

### Task 1: storage.js — safe localStorage wrapper

**Files:**
- Create: `frontend/user/modules/storage.js`
- Create: `tests/frontend/test_storage.mjs`

The store needs to read/write a JSON blob to localStorage. We wrap it so the rest of the codebase doesn't need to handle browser-storage edge cases (Safari private mode throws on `localStorage.setItem`; corrupt JSON returns null).

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_storage.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import { createStorage } from "../../frontend/user/modules/storage.js";

function makeFakeLocalStorage(initial = {}) {
  const data = { ...initial };
  return {
    getItem(key) {
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      data[key] = String(value);
    },
    removeItem(key) {
      delete data[key];
    },
    _data: data,
  };
}

test("createStorage: read returns parsed JSON when present", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": '{"yield":{"minYield":4}}' });
  const store = createStorage("atlas:filters", { backend: fake });
  assert.deepEqual(store.read(), { yield: { minYield: 4 } });
});

test("createStorage: read returns null when key missing", () => {
  const fake = makeFakeLocalStorage();
  const store = createStorage("atlas:filters", { backend: fake });
  assert.equal(store.read(), null);
});

test("createStorage: read returns null when JSON is corrupt", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": "{not valid json" });
  const store = createStorage("atlas:filters", { backend: fake });
  assert.equal(store.read(), null);
});

test("createStorage: write serializes and stores", () => {
  const fake = makeFakeLocalStorage();
  const store = createStorage("atlas:filters", { backend: fake });
  store.write({ yield: { minYield: 4.5 } });
  assert.equal(fake._data["atlas:filters"], '{"yield":{"minYield":4.5}}');
});

test("createStorage: write swallows backend errors gracefully", () => {
  const failing = {
    getItem: () => null,
    setItem: () => {
      throw new Error("QuotaExceededError");
    },
    removeItem: () => {},
  };
  const store = createStorage("atlas:filters", { backend: failing });
  // Must not throw.
  store.write({ yield: { minYield: 4 } });
});

test("createStorage: clear removes the key", () => {
  const fake = makeFakeLocalStorage({ "atlas:filters": "{}" });
  const store = createStorage("atlas:filters", { backend: fake });
  store.clear();
  assert.equal(fake.getItem("atlas:filters"), null);
});
```

- [ ] **Step 2: Verify it fails**

Run: `node --test tests/frontend/test_storage.mjs`
Expected: ERR_MODULE_NOT_FOUND for `storage.js`.

- [ ] **Step 3: Implement `storage.js`**

Write `frontend/user/modules/storage.js`:

```javascript
function defaultBackend() {
  if (typeof window === "undefined" || !window.localStorage) {
    return null;
  }
  try {
    // Probe — Safari private mode throws here.
    window.localStorage.setItem("__atlas_probe__", "1");
    window.localStorage.removeItem("__atlas_probe__");
    return window.localStorage;
  } catch {
    return null;
  }
}

export function createStorage(key, { backend } = {}) {
  const target = backend === undefined ? defaultBackend() : backend;

  function read() {
    if (!target) return null;
    let raw;
    try {
      raw = target.getItem(key);
    } catch {
      return null;
    }
    if (raw === null || raw === undefined) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  function write(value) {
    if (!target) return;
    try {
      target.setItem(key, JSON.stringify(value));
    } catch {
      /* quota / private-mode — silently drop */
    }
  }

  function clear() {
    if (!target) return;
    try {
      target.removeItem(key);
    } catch {
      /* nothing to do */
    }
  }

  return { read, write, clear };
}
```

- [ ] **Step 4: Verify it passes**

Run: `node --test tests/frontend/test_storage.mjs`
Expected: 6 tests passed.

Run: `node --check frontend/user/modules/storage.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/storage.js tests/frontend/test_storage.mjs
git commit -m "feat(user): add safe localStorage wrapper"
```

---

### Task 2: modes.js — add defaultFilters + filter helpers

**Files:**
- Modify: `frontend/user/modules/modes.js`
- Modify: `tests/frontend/test_modes.mjs`
- Create: `tests/frontend/test_filter_helpers.mjs`

We extend `MODES` so each mode declares its default filters and chip labels. We also add two pure helpers used by both the filter bar and the board:

- `filtersToApiParams(filters)` — convert internal filter object to the URL params accepted by `/api/v2/opportunities`
- `describeFilter(key, value)` — render a chip label like `租售比 ≥ 4%`

- [ ] **Step 1: Add tests for defaultFilters in `tests/frontend/test_modes.mjs`**

Open `tests/frontend/test_modes.mjs`. Add the import line at the top — change:

```javascript
import { MODES, getMode, yieldColorFor } from "../../frontend/user/modules/modes.js";
```

to:

```javascript
import { MODES, getMode, yieldColorFor, defaultFiltersFor } from "../../frontend/user/modules/modes.js";
```

Then append these two new test cases at the end of the file:

```javascript
test("defaultFiltersFor: yield mode returns minYield 4 + maxBudget 1500", () => {
  assert.deepEqual(defaultFiltersFor("yield"), { minYield: 4, maxBudget: 1500 });
});

test("defaultFiltersFor: home and city modes default to empty filters", () => {
  assert.deepEqual(defaultFiltersFor("home"), {});
  assert.deepEqual(defaultFiltersFor("city"), {});
});
```

- [ ] **Step 2: Write the new helper test file**

Write `tests/frontend/test_filter_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import { filtersToApiParams, describeFilter, prunedFilters } from "../../frontend/user/modules/modes.js";

test("filtersToApiParams: yield filters → snake_case params", () => {
  const params = filtersToApiParams({ minYield: 4, maxBudget: 1500 });
  assert.deepEqual(params, { min_yield: 4, max_budget: 1500 });
});

test("filtersToApiParams: empty filter object → empty params", () => {
  assert.deepEqual(filtersToApiParams({}), {});
});

test("filtersToApiParams: skips undefined / null / empty-string values", () => {
  const params = filtersToApiParams({
    minYield: 4,
    maxBudget: undefined,
    minSamples: null,
    minScore: "",
  });
  assert.deepEqual(params, { min_yield: 4 });
});

test("filtersToApiParams: passes minSamples and minScore through", () => {
  const params = filtersToApiParams({ minSamples: 2, minScore: 50 });
  assert.deepEqual(params, { min_samples: 2, min_score: 50 });
});

test("describeFilter: renders human-friendly chip labels", () => {
  assert.equal(describeFilter("minYield", 4), "租售比 ≥ 4%");
  assert.equal(describeFilter("maxBudget", 1500), "总价 ≤ 1500 万");
  assert.equal(describeFilter("minSamples", 2), "样本量 ≥ 2");
  assert.equal(describeFilter("minScore", 50), "机会分 ≥ 50");
});

test("describeFilter: unknown key falls back to key=value", () => {
  assert.equal(describeFilter("custom", 7), "custom = 7");
});

test("prunedFilters: drops keys whose value matches the API default", () => {
  // /api/v2/opportunities defaults: min_yield 0, max_budget 10000,
  // min_samples 0, min_score 0. So filters at the API default are NOT
  // distinct from "no filter" and shouldn't render as chips.
  const pruned = prunedFilters({ minYield: 0, maxBudget: 10000, minScore: 50 });
  assert.deepEqual(pruned, { minScore: 50 });
});
```

- [ ] **Step 3: Run both test files to verify they fail**

Run: `node --test tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs`
Expected: imports fail (`defaultFiltersFor`, `filtersToApiParams`, `describeFilter`, `prunedFilters` don't exist yet).

- [ ] **Step 4: Extend `frontend/user/modules/modes.js`**

Open `frontend/user/modules/modes.js`. The file currently exports `MODES`, `getMode`, and `yieldColorFor`. Extend it to also carry per-mode default filters and the helper functions.

Find the `MODES` definition (the array of three mode objects). For each entry, add a `defaultFilters` field. The yield entry currently looks like this (the other entries have the same shape):

```javascript
  {
    id: "yield",
    label: "收益猎手",
    hotkey: "1",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "yield", label: "租售比", format: "pct" },
      { key: "score", label: "机会分", format: "int" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    enabled: true,
  },
```

Add `defaultFilters: { minYield: 4, maxBudget: 1500 }` immediately after `defaultSort` for yield, and `defaultFilters: {}` for both home and city. The yield entry should now read:

```javascript
  {
    id: "yield",
    label: "收益猎手",
    hotkey: "1",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "yield", label: "租售比", format: "pct" },
      { key: "score", label: "机会分", format: "int" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    defaultFilters: { minYield: 4, maxBudget: 1500 },
    enabled: true,
  },
```

After the `MODE_INDEX` line, add these new exports at the bottom of the file (before any existing exports that follow):

```javascript
export function defaultFiltersFor(modeId) {
  return { ...(getMode(modeId).defaultFilters || {}) };
}

const FILTER_KEY_MAP = {
  minYield: "min_yield",
  maxBudget: "max_budget",
  minSamples: "min_samples",
  minScore: "min_score",
};

const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
};

export function filtersToApiParams(filters) {
  const out = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value === undefined || value === null || value === "") continue;
    const apiKey = FILTER_KEY_MAP[key];
    if (!apiKey) continue;
    out[apiKey] = value;
  }
  return out;
}

const FILTER_LABELS = {
  minYield: (v) => `租售比 ≥ ${v}%`,
  maxBudget: (v) => `总价 ≤ ${v} 万`,
  minSamples: (v) => `样本量 ≥ ${v}`,
  minScore: (v) => `机会分 ≥ ${v}`,
};

export function describeFilter(key, value) {
  const fn = FILTER_LABELS[key];
  return fn ? fn(value) : `${key} = ${value}`;
}

export function prunedFilters(filters) {
  const out = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Object.prototype.hasOwnProperty.call(FILTER_API_DEFAULTS, key)) {
      if (Number(value) === FILTER_API_DEFAULTS[key]) continue;
    }
    out[key] = value;
  }
  return out;
}
```

- [ ] **Step 5: Verify**

Run: `node --test tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs`
Expected: 16 tests passed (9 modes — 7 existing + 2 new — plus 7 filter-helpers).

Run: `node --check frontend/user/modules/modes.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs`
Expected: 35 tests passed (5 + 9 + 11 + 6 + 4 — wait, recount: state 5, modes 9 [7+2], drawer 11, storage 6, filter 7 → total 38).

Note: the precise total is **38 tests** (5 state + 9 modes + 11 drawer + 6 storage + 7 filter helpers). Use that count as the success criterion.

- [ ] **Step 6: Commit**

```bash
git add frontend/user/modules/modes.js tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs
git commit -m "feat(user): add per-mode default filters + chip/api helpers"
```

---

### Task 3: opportunity-board.js — pass filters to API

**Files:**
- Modify: `frontend/user/modules/opportunity-board.js`

The board currently calls `api.opportunities()` with no args. We change it to read `state.filters[modeId]`, run it through `filtersToApiParams`, pass to the API, and reload whenever either mode OR the active filter slice changes.

- [ ] **Step 1: Open `frontend/user/modules/opportunity-board.js` and update imports**

Find:

```javascript
import { api } from "./api.js";
import { getMode } from "./modes.js";
```

Replace with:

```javascript
import { api } from "./api.js";
import { getMode, filtersToApiParams } from "./modes.js";
```

- [ ] **Step 2: Track active-filter changes alongside mode changes**

Find this block (the entire `initBoard` body up to and including the subscriber):

```javascript
export async function initBoard({ container, store }) {
  const list = container.querySelector('[data-role="board-list"]');
  const empty = container.querySelector('[data-role="board-empty"]');
  const countEl = container.querySelector('[data-role="board-count"]');
  const modeLabelEl = container.querySelector('[data-role="board-mode-label"]');

  let lastItems = [];
  let lastMode = store.get().mode;

  await loadFor(lastMode);

  store.subscribe(async (state) => {
    if (state.mode !== lastMode) {
      lastMode = state.mode;
      await loadFor(state.mode);
      return;
    }
    render(state);
  });
```

Replace it with:

```javascript
export async function initBoard({ container, store }) {
  const list = container.querySelector('[data-role="board-list"]');
  const empty = container.querySelector('[data-role="board-empty"]');
  const countEl = container.querySelector('[data-role="board-count"]');
  const modeLabelEl = container.querySelector('[data-role="board-mode-label"]');

  let lastItems = [];
  let lastMode = store.get().mode;
  let lastFilterKey = filterKeyFor(store.get(), lastMode);

  await loadFor(lastMode, store.get());

  store.subscribe(async (state) => {
    const nextFilterKey = filterKeyFor(state, state.mode);
    if (state.mode !== lastMode || nextFilterKey !== lastFilterKey) {
      lastMode = state.mode;
      lastFilterKey = nextFilterKey;
      await loadFor(state.mode, state);
      return;
    }
    render(state);
  });
```

- [ ] **Step 3: Update `loadFor` to send params**

Find:

```javascript
  async function loadFor(modeId) {
    const mode = getMode(modeId);
    if (!mode.enabled) {
      lastItems = [];
      render(store.get());
      return;
    }
    try {
      const data = await api.opportunities();
      lastItems = sortItems(data.items || [], mode.defaultSort);
    } catch (err) {
      console.error("[atlas:board] opportunities load failed", err);
      lastItems = [];
    }
    render(store.get());
  }
```

Replace with:

```javascript
  async function loadFor(modeId, state) {
    const mode = getMode(modeId);
    if (!mode.enabled) {
      lastItems = [];
      render(store.get());
      return;
    }
    const filters = (state && state.filters && state.filters[modeId]) || {};
    const params = filtersToApiParams(filters);
    try {
      const data = await api.opportunities(params);
      lastItems = sortItems(data.items || [], mode.defaultSort);
    } catch (err) {
      console.error("[atlas:board] opportunities load failed", err);
      lastItems = [];
    }
    render(store.get());
  }
```

- [ ] **Step 4: Add the `filterKeyFor` helper**

At the bottom of the file (after the existing `escapeAttr` function), append:

```javascript
function filterKeyFor(state, modeId) {
  const filters = (state && state.filters && state.filters[modeId]) || {};
  return JSON.stringify(filters);
}
```

The `JSON.stringify` is sufficient because filter objects are flat key→primitive maps — the key order coming out of an object literal or `Object.assign` is consistent for the same set of keys.

- [ ] **Step 5: Verify**

Run: `node --check frontend/user/modules/opportunity-board.js`
Expected: exit 0.

Run: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs`
Expected: 38 tests passed.

Run: `pytest -q`
Expected: 20 passed.

- [ ] **Step 6: Commit**

```bash
git add frontend/user/modules/opportunity-board.js
git commit -m "feat(user): board reads state.filters and passes to api"
```

---

### Task 4: filter-bar.js — render chips + match count

**Files:**
- Create: `frontend/user/modules/filter-bar.js`
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/shell.css`

The filter-bar currently shows a Phase 3 placeholder. We replace it with two slots: a left container for chips, a right container for the match count. The `filter-bar.js` module subscribes to the store, renders chips for `prunedFilters(state.filters[state.mode])`, wires X-button clicks to set the filter back to its API default (so the chip disappears), and updates the count whenever the board pushes new items.

The board needs to publish its result count somehow. The simplest path: the board writes `state.boardCount` (a number) to the store after each render. The filter bar reads that. We add this in step 4 of this task.

- [ ] **Step 1: Update `frontend/user/index.html` filter-bar mount**

Find:

```html
      <div class="atlas-filterbar" data-component="filter-bar">
        <span class="dim">筛选条 (Phase 3 启用)</span>
      </div>
```

Replace with:

```html
      <div class="atlas-filterbar" data-component="filter-bar">
        <div class="atlas-filter-chips" data-role="filter-chips"></div>
        <div class="atlas-filter-spacer"></div>
        <span class="atlas-filter-count mono dim" data-role="filter-count">—</span>
      </div>
```

- [ ] **Step 2: Append filter-bar styles to `frontend/user/styles/shell.css`**

Open `frontend/user/styles/shell.css` and append at the end:

```css
.atlas-filter-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.atlas-filter-spacer {
  flex: 1;
}

.atlas-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 2px 6px 2px 8px;
  font-size: 11px;
  color: var(--text-0);
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.atlas-filter-chip-clear {
  appearance: none;
  border: none;
  background: transparent;
  color: var(--text-dim);
  font: inherit;
  font-size: 12px;
  line-height: 1;
  padding: 0 2px;
  cursor: pointer;
}

.atlas-filter-chip-clear:hover {
  color: var(--down);
}

.atlas-filter-empty {
  font-size: 11px;
  color: var(--text-xs);
  letter-spacing: 0.08em;
}

.atlas-filter-count {
  font-size: 11px;
  letter-spacing: 0.06em;
}
```

- [ ] **Step 3: Implement `frontend/user/modules/filter-bar.js`**

Write `frontend/user/modules/filter-bar.js`:

```javascript
import { describeFilter, getMode, prunedFilters } from "./modes.js";

const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
};

export function initFilterBar({ root, store }) {
  const container = root.querySelector('[data-component="filter-bar"]');
  const chipsEl = container.querySelector('[data-role="filter-chips"]');
  const countEl = container.querySelector('[data-role="filter-count"]');

  chipsEl.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-clear]");
    if (!button) return;
    clearFilter(button.dataset.filterClear);
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const mode = getMode(state.mode);
    const activeFilters = prunedFilters((state.filters && state.filters[state.mode]) || {});
    const entries = Object.entries(activeFilters);

    if (entries.length === 0) {
      chipsEl.innerHTML = `<span class="atlas-filter-empty">${mode.label} 模式 · 无筛选</span>`;
    } else {
      chipsEl.innerHTML = entries
        .map(
          ([key, value]) =>
            `<span class="atlas-filter-chip">${escapeText(describeFilter(key, value))}<button type="button" class="atlas-filter-chip-clear" data-filter-clear="${escapeAttr(key)}" aria-label="移除 ${escapeAttr(describeFilter(key, value))}">×</button></span>`,
        )
        .join("");
    }

    if (typeof state.boardCount === "number") {
      countEl.textContent = `${state.boardCount} 条`;
    } else {
      countEl.textContent = "—";
    }
  }

  function clearFilter(key) {
    const state = store.get();
    const modeId = state.mode;
    const current = (state.filters && state.filters[modeId]) || {};
    if (!Object.prototype.hasOwnProperty.call(current, key)) return;
    const next = { ...current };
    if (Object.prototype.hasOwnProperty.call(FILTER_API_DEFAULTS, key)) {
      // Reset to the API default — keeps the key present in the filter object
      // so reloads still see an explicit value, but prunedFilters hides the chip.
      next[key] = FILTER_API_DEFAULTS[key];
    } else {
      delete next[key];
    }
    const filters = { ...(state.filters || {}), [modeId]: next };
    store.set({ filters });
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

- [ ] **Step 4: Make the board publish `boardCount`**

Open `frontend/user/modules/opportunity-board.js`. Find the `render(state)` function. There are exactly three places that update `countEl.textContent` (stub-mode → "--", zero-items → "0", default → length). Each of those should ALSO publish `boardCount` to the store.

Find:

```javascript
  function render(state) {
    const mode = getMode(state.mode);
    modeLabelEl.textContent = mode.label;
    if (!mode.enabled) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = `${mode.label} 模式将于 Phase 3 启用`;
      countEl.textContent = "--";
      return;
    }
    if (lastItems.length === 0) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = "暂无机会";
      countEl.textContent = "0";
      return;
    }
    empty.hidden = true;
    countEl.textContent = String(lastItems.length);
```

Replace with:

```javascript
  function render(state) {
    const mode = getMode(state.mode);
    modeLabelEl.textContent = mode.label;
    if (!mode.enabled) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = `${mode.label} 模式将于 Phase 3 启用`;
      countEl.textContent = "--";
      publishCount(null);
      return;
    }
    if (lastItems.length === 0) {
      list.innerHTML = "";
      empty.hidden = false;
      empty.textContent = "暂无机会";
      countEl.textContent = "0";
      publishCount(0);
      return;
    }
    empty.hidden = true;
    countEl.textContent = String(lastItems.length);
    publishCount(lastItems.length);
```

Inside `initBoard` (right after the `let lastFilterKey = ...` line you added in Task 3), define a closure-bound `publishCount` that the `render` function will reach via JavaScript's lexical scope:

```javascript
  function publishCount(value) {
    const current = store.get().boardCount;
    if (current === value) return;
    store.set({ boardCount: value });
  }
```

`render` is defined inside `initBoard` and only called from there, so the closure capture is enough — no module-level fallback needed.

- [ ] **Step 5: Verify the modules compile**

Run: `node --check frontend/user/modules/filter-bar.js`
Expected: exit 0.

Run: `node --check frontend/user/modules/opportunity-board.js`
Expected: exit 0.

Run: `pytest -q`
Expected: 20 passed.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs`
Expected: 38 tests passed.

- [ ] **Step 6: Commit**

```bash
git add frontend/user/modules/filter-bar.js frontend/user/modules/opportunity-board.js frontend/user/index.html frontend/user/styles/shell.css
git commit -m "feat(user): live filter bar with removable chips + match count"
```

---

### Task 5: bootstrap + persistence + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

We rehydrate filters from localStorage at boot, seed defaults for missing modes, register a save-on-change subscriber, and wire `initFilterBar`.

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. The current top of the file:

```javascript
import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
import { initDrawer } from "./detail-drawer.js";
```

Add two new imports directly after the `initDrawer` import:

```javascript
import { initFilterBar } from "./filter-bar.js";
import { createStorage } from "./storage.js";
import { MODES, defaultFiltersFor } from "./modes.js";
```

Then replace the `bootstrap` function. The current body looks like:

```javascript
async function bootstrap(root) {
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
  });

  initShell({ root, store });
  initDrawer({ root, store });

  const mapContainer = root.querySelector('[data-component="map"]');
  const boardContainer = root.querySelector('[data-component="board"]');

  // Map and board boot in parallel — they only talk via the store.
  await Promise.all([
    initMap({ container: mapContainer, store }),
    initBoard({ container: boardContainer, store }),
  ]);

  console.info("[atlas] user shell ready");
}
```

Replace it with:

```javascript
async function bootstrap(root) {
  const filtersStorage = createStorage("atlas:filters:v1");
  const persistedFilters = filtersStorage.read() || {};
  const initialFilters = {};
  for (const mode of MODES) {
    initialFilters[mode.id] = persistedFilters[mode.id] || defaultFiltersFor(mode.id);
  }

  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
  });

  let lastSerializedFilters = JSON.stringify(initialFilters);
  store.subscribe((state) => {
    const next = JSON.stringify(state.filters);
    if (next === lastSerializedFilters) return;
    lastSerializedFilters = next;
    filtersStorage.write(state.filters);
  });

  initShell({ root, store });
  initDrawer({ root, store });
  initFilterBar({ root, store });

  const mapContainer = root.querySelector('[data-component="map"]');
  const boardContainer = root.querySelector('[data-component="board"]');

  // Map and board boot in parallel — they only talk via the store.
  await Promise.all([
    initMap({ container: mapContainer, store }),
    initBoard({ container: boardContainer, store }),
  ]);

  console.info("[atlas] user shell ready");
}
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/", 'data-component="drawer"'),
```

Add directly below it:

```python
            (f"{base}/", 'data-role="filter-chips"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 11 rows OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 3a 起）` and change to `## 路由布局（Phase 3b 起）`.

Then find the row whose third column starts with `用户平台。收益模式端到端 + 详情抽屉`. Replace the description with:

```markdown
用户平台。收益模式端到端 + 详情抽屉 + 实时筛选条（按模式记忆筛选 + 命中条数）。Home/City 模式 chip 已启用，全模式支持见后续 phase。
```

- [ ] **Step 6: Verify all exit criteria**

Run each:
- `pytest -q` → 20 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs` → 38 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 11 OK
- For each new/modified JS file, `node --check`:
  - `frontend/user/modules/state.js api.js runtime.js modes.js map.js opportunity-board.js shell.js detail-drawer.js drawer-data.js storage.js filter-bar.js main.js` → exit 0 each
- `node --check frontend/backstage/app.js` → exit 0 (regression guard)

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire filter bar in bootstrap + persist filters per mode + extend smoke + docs"
```

---

## Phase 3b Exit Criteria

- [ ] `pytest -q` — 20 passed (no backend change in this phase)
- [ ] `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs` — 38 passed (5 + 9 + 11 + 6 + 7)
- [ ] Each JS file passes `node --check`: state, api, runtime, modes, map, opportunity-board, shell, detail-drawer, drawer-data, storage, filter-bar, main
- [ ] `node --check frontend/backstage/app.js` — exit 0 (regression guard)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 11 rows OK
- [ ] Manual: open `http://127.0.0.1:8013/?mode=yield` → filter bar shows two chips: `租售比 ≥ 4%` and `总价 ≤ 1500 万`; right end shows `N 条`
- [ ] Manual: click X on `总价 ≤ 1500 万` chip → board reloads (now without the budget cap), count updates
- [ ] Manual: refresh the page → previously-removed chip stays removed (localStorage persisted)
- [ ] Manual: switch to home mode → filter bar shows `自住找房 模式 · 无筛选`; switch back to yield → previous chip state restored
- [ ] `git log --oneline 8c49a0c..HEAD` shows the Phase 3a follow-up commit `b7cd2d6` plus exactly 5 new Phase 3b commits

## Out of Scope (deferred)

- Filter editor / "+ add filter" popover — Phase 3c
- URL `?filters=...` round-trip — separate polish pass
- Home onboarding modal + `/api/v2/user/prefs` backend — Phase 3c
- City mode district map color band — Phase 3d
- Per-mode viewport memory — Phase 6
- Backend filter parameters beyond `min_yield` / `max_budget` / `min_samples` / `min_score`
