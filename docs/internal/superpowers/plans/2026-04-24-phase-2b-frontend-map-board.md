# Phase 2b — User-Platform Frontend (Map + Opportunity Board) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the yield-mode-end-to-end user platform at `/`: AMap-rendered building polygons colored by 租售比 + a viewport-filtered opportunity board on the right, driven by a small pub/sub store. Home and City mode chips render and toggle but only stub their behavior.

**Architecture:** Vanilla ES modules (no build tool) under `frontend/user/modules/`. A ~50-line pub/sub store in `state.js` is the single source of truth for `{mode, viewport, selection, runtime}`. Modules subscribe; they never import each other. AMap loads via the same script-tag mechanism the backstage already uses, but module code is fresh — we deliberately do NOT import from `frontend/backstage/app.js` (mixing module and non-module code, plus pulling in 12k lines of unrelated state, would defeat the rewrite).

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for store/mode unit checks · CSS variables (D1 financial-terminal palette already in `tokens.css`) · existing `/api/v2/*` and `/api/runtime-config` endpoints. No new deps.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (Phase 2 + section 5 visual design)

**Prior plan:** `docs/superpowers/plans/2026-04-24-phase-2a-user-platform-routes.md` (merged at `75c4165` — gives us all the v2 endpoints this phase consumes)

---

## File Structure (Phase 2b outcome)

```
frontend/user/
├── index.html                       # MODIFIED: mount points + script tag
├── styles/
│   ├── tokens.css                   # unchanged (Phase 1)
│   ├── shell.css                    # MODIFIED: mode-chip + filter styling
│   ├── map.css                      # NEW
│   └── board.css                    # NEW
└── modules/
    ├── state.js                     # NEW — pub/sub store
    ├── api.js                       # NEW — fetch + small response cache
    ├── runtime.js                   # NEW — runtime-config + AMap script loader
    ├── modes.js                     # NEW — yield/home/city config table
    ├── map.js                       # NEW — AMap render
    ├── opportunity-board.js         # NEW — opportunity list
    ├── shell.js                     # NEW — topbar chips + URL sync
    └── main.js                      # MODIFIED: bootstrap + wire modules

tests/frontend/                      # NEW directory (node:test)
├── test_state.mjs                   # NEW
└── test_modes.mjs                   # NEW

scripts/phase1_smoke.py              # MODIFIED: add 1 substring check proving the new layout html landed
README.md                            # MODIFIED: note Phase 2b lights up yield mode at /
```

**Out-of-scope (deferred to Phase 3+):** detail drawer, watchlist, annotations, alerts, mode-specific filter persistence, Home onboarding, City district aggregate. The mode chips switch but Home/City show "stub" placeholder content in the board area.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add .worktrees/phase-2b-frontend feature/phase-2b-frontend
cd .worktrees/phase-2b-frontend
```

- [ ] **Verify baseline**

```bash
pytest -q                                    # expect: 20 passed
node --check frontend/user/modules/main.js   # expect: exit 0
python3 scripts/phase1_smoke.py              # expect: 8 routes OK (uvicorn auto-spawned)
```

If anything fails, stop — Phase 2a should be merged cleanly before this starts.

---

### Task 1: pub/sub state store

**Files:**
- Create: `frontend/user/modules/state.js`
- Create: `tests/frontend/test_state.mjs`

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_state.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import { createStore } from "../../frontend/user/modules/state.js";

test("createStore: get returns initial state", () => {
  const store = createStore({ mode: "yield", count: 0 });
  assert.deepEqual(store.get(), { mode: "yield", count: 0 });
});

test("createStore: set merges patch and notifies subscribers", () => {
  const store = createStore({ mode: "yield", count: 0 });
  const calls = [];
  store.subscribe((state) => calls.push(state));
  store.set({ count: 1 });
  assert.deepEqual(store.get(), { mode: "yield", count: 1 });
  assert.equal(calls.length, 1);
  assert.deepEqual(calls[0], { mode: "yield", count: 1 });
});

test("createStore: set with no actual change does not notify", () => {
  const store = createStore({ mode: "yield", count: 0 });
  const calls = [];
  store.subscribe((state) => calls.push(state));
  store.set({ count: 0 });
  assert.equal(calls.length, 0);
});

test("createStore: subscribe returns an unsubscribe", () => {
  const store = createStore({ mode: "yield" });
  const calls = [];
  const off = store.subscribe((state) => calls.push(state));
  off();
  store.set({ mode: "home" });
  assert.equal(calls.length, 0);
});

test("createStore: select returns a derived value", () => {
  const store = createStore({ mode: "yield", filters: { minYield: 4 } });
  assert.equal(store.select((s) => s.filters.minYield), 4);
});
```

- [ ] **Step 2: Verify it fails**

Run: `node --test tests/frontend/test_state.mjs`
Expected: ERR_MODULE_NOT_FOUND for `state.js`.

- [ ] **Step 3: Implement the store**

Write `frontend/user/modules/state.js`:

```javascript
export function createStore(initial = {}) {
  let state = { ...initial };
  const listeners = new Set();

  function get() {
    return state;
  }

  function set(patch) {
    let changed = false;
    const next = { ...state };
    for (const key of Object.keys(patch)) {
      if (!Object.is(state[key], patch[key])) {
        next[key] = patch[key];
        changed = true;
      }
    }
    if (!changed) return;
    state = next;
    for (const listener of listeners) {
      listener(state);
    }
  }

  function subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }

  function select(selector) {
    return selector(state);
  }

  return { get, set, subscribe, select };
}
```

- [ ] **Step 4: Verify it passes**

Run: `node --test tests/frontend/test_state.mjs`
Expected: 5 tests passed.

Run: `node --check frontend/user/modules/state.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/state.js tests/frontend/test_state.mjs
git commit -m "feat(user): add pub/sub state store"
```

---

### Task 2: API client + runtime/AMap loader

**Files:**
- Create: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/runtime.js`

- [ ] **Step 1: Implement `api.js`**

Write `frontend/user/modules/api.js`:

```javascript
const cache = new Map();

async function getJSON(url, { signal } = {}) {
  if (cache.has(url)) {
    return cache.get(url);
  }
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(`API ${url} → ${response.status}`);
  }
  const body = await response.json();
  cache.set(url, body);
  return body;
}

function invalidate(prefix) {
  for (const key of [...cache.keys()]) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}

function buildQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params || {})) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  invalidate,
};
```

- [ ] **Step 2: Implement `runtime.js`** — script-tag AMap loader (no copy from backstage; rewritten to ES-module shape)

Write `frontend/user/modules/runtime.js`:

```javascript
let amapScriptPromise = null;

export function loadAmap({ apiKey, securityJsCode, timeoutMs = 8000 }) {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("loadAmap: window unavailable (SSR?)"));
  }
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }
  if (amapScriptPromise) {
    return amapScriptPromise;
  }
  if (!apiKey) {
    return Promise.reject(new Error("loadAmap: missing apiKey"));
  }
  if (securityJsCode) {
    window._AMapSecurityConfig = { securityJsCode };
  }
  amapScriptPromise = new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      reject(new Error("AMap script timeout"));
    }, timeoutMs);
    const script = document.createElement("script");
    script.async = true;
    script.defer = true;
    script.dataset.amapLoader = "user-platform";
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.Scale,AMap.ToolBar`;
    script.onload = () => {
      window.clearTimeout(timeoutId);
      if (window.AMap) {
        resolve(window.AMap);
      } else {
        reject(new Error("AMap unavailable after script load"));
      }
    };
    script.onerror = () => {
      window.clearTimeout(timeoutId);
      reject(new Error("AMap script failed"));
    };
    document.head.appendChild(script);
  });
  return amapScriptPromise;
}
```

- [ ] **Step 3: Sanity-check**

Run:
```
node --check frontend/user/modules/api.js
node --check frontend/user/modules/runtime.js
```
Expected: exit 0 each.

- [ ] **Step 4: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/runtime.js
git commit -m "feat(user): add api client + amap loader"
```

---

### Task 3: Mode configuration table

**Files:**
- Create: `frontend/user/modules/modes.js`
- Create: `tests/frontend/test_modes.mjs`

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_modes.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import { MODES, getMode, yieldColorFor } from "../../frontend/user/modules/modes.js";

test("MODES: yield/home/city present in declared order", () => {
  assert.deepEqual(MODES.map((m) => m.id), ["yield", "home", "city"]);
});

test("getMode: returns the matching config", () => {
  const m = getMode("yield");
  assert.equal(m.id, "yield");
  assert.equal(m.label, "收益猎手");
});

test("getMode: unknown id falls back to yield", () => {
  assert.equal(getMode("nonsense").id, "yield");
});

test("yieldColorFor: yieldPct under 3.5 is down/red", () => {
  assert.equal(yieldColorFor(2.0), "var(--down)");
});

test("yieldColorFor: yieldPct between 3.5 and 5 is warn/amber", () => {
  assert.equal(yieldColorFor(4.0), "var(--warn)");
});

test("yieldColorFor: yieldPct >= 5 is up/green", () => {
  assert.equal(yieldColorFor(5.5), "var(--up)");
});

test("yieldColorFor: null/NaN returns dim", () => {
  assert.equal(yieldColorFor(null), "var(--text-dim)");
  assert.equal(yieldColorFor(Number.NaN), "var(--text-dim)");
});
```

- [ ] **Step 2: Verify it fails**

Run: `node --test tests/frontend/test_modes.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `modes.js`**

Write `frontend/user/modules/modes.js`:

```javascript
export const MODES = [
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
  {
    id: "home",
    label: "自住找房",
    hotkey: "2",
    boardColumns: [
      { key: "name", label: "名称" },
      { key: "avgPriceWan", label: "总价(万)", format: "wan" },
      { key: "yield", label: "租售比", format: "pct" },
    ],
    defaultSort: { key: "avgPriceWan", direction: "asc" },
    enabled: false,
  },
  {
    id: "city",
    label: "全市观察",
    hotkey: "3",
    boardColumns: [
      { key: "districtName", label: "区" },
      { key: "yield", label: "均租售比", format: "pct" },
      { key: "score", label: "机会分", format: "int" },
    ],
    defaultSort: { key: "yield", direction: "desc" },
    enabled: false,
  },
];

const MODE_INDEX = new Map(MODES.map((m) => [m.id, m]));

export function getMode(id) {
  return MODE_INDEX.get(id) || MODES[0];
}

export function yieldColorFor(yieldPct) {
  if (yieldPct === null || yieldPct === undefined || Number.isNaN(yieldPct)) {
    return "var(--text-dim)";
  }
  if (yieldPct < 3.5) return "var(--down)";
  if (yieldPct < 5) return "var(--warn)";
  return "var(--up)";
}
```

- [ ] **Step 4: Verify**

Run:
```
node --test tests/frontend/test_modes.mjs
node --check frontend/user/modules/modes.js
```
Expected: 7 tests passed; compile exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/modes.js tests/frontend/test_modes.mjs
git commit -m "feat(user): add mode config table + yield color band"
```

---

### Task 4: Layout HTML + CSS

**Files:**
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/shell.css`
- Create: `frontend/user/styles/map.css`
- Create: `frontend/user/styles/board.css`

- [ ] **Step 1: Replace `frontend/user/index.html`**

Overwrite the file with:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Shanghai Yield Atlas</title>
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="/styles/tokens.css" />
    <link rel="stylesheet" href="/styles/shell.css" />
    <link rel="stylesheet" href="/styles/map.css" />
    <link rel="stylesheet" href="/styles/board.css" />
  </head>
  <body data-user-shell="atlas">
    <div class="atlas-shell">
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
        <nav class="atlas-modes" data-component="mode-chips" aria-label="模式切换"></nav>
        <div class="atlas-topbar-spacer"></div>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
      </header>
      <div class="atlas-filterbar" data-component="filter-bar">
        <span class="dim">筛选条 (Phase 3 启用)</span>
      </div>
      <main class="atlas-main">
        <section class="atlas-map" id="atlas-map" data-component="map">
          <div class="atlas-placeholder" data-role="map-placeholder">地图加载中…</div>
        </section>
        <aside class="atlas-board" data-component="board">
          <div class="atlas-board-header mono">
            <span data-role="board-count">--</span>
            <span class="dim" data-role="board-mode-label">--</span>
          </div>
          <ol class="atlas-board-list" data-role="board-list"></ol>
          <div class="atlas-board-empty" data-role="board-empty" hidden>暂无机会</div>
        </aside>
      </main>
      <footer class="atlas-statusbar mono" data-component="statusbar">
        <span data-role="statusbar-mode">mode: --</span>
        <span data-role="statusbar-data">data: --</span>
        <span data-role="statusbar-build">phase 2b</span>
      </footer>
    </div>
    <script type="module" src="/modules/main.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Append to `frontend/user/styles/shell.css`**

Open `frontend/user/styles/shell.css` and append the following at the end:

```css
.atlas-modes {
  display: flex;
  gap: 6px;
}

.atlas-mode-chip {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: color 80ms ease, border-color 80ms ease, background 80ms ease;
}

.atlas-mode-chip[aria-pressed="true"] {
  color: var(--text-0);
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.08);
}

.atlas-mode-chip[data-stub="true"] {
  opacity: 0.7;
}

.atlas-mode-chip[data-stub="true"][aria-pressed="true"] {
  border-color: var(--warn);
  background: rgba(255, 176, 32, 0.08);
}

.atlas-topbar-spacer {
  flex: 1;
}

.atlas-runtime-tag {
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
```

- [ ] **Step 3: Create `frontend/user/styles/map.css`**

```css
.atlas-map {
  position: relative;
  min-height: 320px;
}

#atlas-map > .atlas-placeholder {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
  background: linear-gradient(180deg, rgba(7, 10, 16, 0.88), rgba(7, 10, 16, 0.6));
}

#atlas-map.is-ready > .atlas-placeholder {
  display: none;
}

.atlas-map-error {
  position: absolute;
  inset: 16px;
  border: 1px solid var(--down);
  background: rgba(255, 77, 77, 0.06);
  color: var(--down);
  padding: 12px;
  font-size: 12px;
  z-index: 3;
}
```

- [ ] **Step 4: Create `frontend/user/styles/board.css`**

```css
.atlas-board-header {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.atlas-board-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.atlas-board-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 10px;
  align-items: baseline;
  padding: 8px 14px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  transition: background 80ms ease;
}

.atlas-board-row:hover {
  background: var(--bg-2);
}

.atlas-board-row[aria-selected="true"] {
  background: rgba(0, 214, 143, 0.06);
  border-left: 2px solid var(--up);
  padding-left: 12px;
}

.atlas-board-row .name {
  color: var(--text-0);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atlas-board-row .secondary {
  color: var(--text-dim);
  font-size: 11px;
}

.atlas-board-empty {
  padding: 32px 14px;
  text-align: center;
  color: var(--text-xs);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
```

- [ ] **Step 5: Verify CSS files don't break anything**

Open `http://127.0.0.1:8013/` mentally — no JS yet for these new chips/board, so the page shows the empty topbar nav, the filter-bar stub, the map placeholder, and "--" board counters. That's intentional; behavior wires up in later tasks.

- [ ] **Step 6: Commit**

```bash
git add frontend/user/index.html frontend/user/styles/shell.css frontend/user/styles/map.css frontend/user/styles/board.css
git commit -m "feat(user): add map+board layout html and css"
```

---

### Task 5: Map module (AMap + building polygons + selection)

**Files:**
- Create: `frontend/user/modules/map.js`

- [ ] **Step 1: Implement `map.js`**

Write `frontend/user/modules/map.js`:

```javascript
import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import { yieldColorFor } from "./modes.js";

const SHANGHAI_CENTER = [121.4737, 31.2304];
const DEFAULT_ZOOM = 10.8;

export async function initMap({ container, store }) {
  const placeholder = container.querySelector('[data-role="map-placeholder"]');
  const runtime = await api.runtimeConfig();
  store.set({ runtime });

  if (!runtime.hasAmapKey || !runtime.amapApiKey) {
    showError(container, "AMap key 未配置 — 设置 AMAP_API_KEY 后重启");
    return null;
  }

  let AMap;
  try {
    AMap = await loadAmap({
      apiKey: runtime.amapApiKey,
      securityJsCode: runtime.amapSecurityJsCode,
    });
  } catch (err) {
    console.error("[atlas:map] AMap load failed", err);
    showError(container, `AMap 加载失败：${err.message}`);
    return null;
  }

  const map = new AMap.Map(container.id, {
    center: SHANGHAI_CENTER,
    zoom: DEFAULT_ZOOM,
    viewMode: "2D",
    mapStyle: "amap://styles/dark",
    showLabel: true,
    zooms: [8, 18],
  });
  map.addControl(new AMap.Scale());
  map.addControl(new AMap.ToolBar({ position: "RB" }));
  container.classList.add("is-ready");
  if (placeholder) placeholder.remove();

  const buildings = await api.mapBuildings();
  renderBuildings({ map, AMap, store, features: buildings.features || [] });

  syncSelectionHighlight({ map, AMap, store });

  return map;
}

function showError(container, message) {
  const div = document.createElement("div");
  div.className = "atlas-map-error";
  div.textContent = message;
  container.appendChild(div);
}

function renderBuildings({ map, AMap, store, features }) {
  const overlays = [];
  for (const feature of features) {
    const geometry = feature.geometry;
    const props = feature.properties || {};
    if (!geometry) continue;
    const yieldPct = numericYieldPct(props.yield_avg_pct);
    const color = yieldColorFor(yieldPct);
    const overlay = createOverlay({ AMap, geometry, color });
    if (!overlay) continue;
    overlay.setExtData({ buildingId: props.building_id, props });
    overlay.on("click", () => {
      store.set({
        selection: { type: "building", id: props.building_id, props },
      });
    });
    overlays.push(overlay);
  }
  map.add(overlays);
  return overlays;
}

function createOverlay({ AMap, geometry, color }) {
  if (geometry.type === "Polygon") {
    return new AMap.Polygon({
      path: geometry.coordinates[0],
      strokeColor: color,
      strokeWeight: 1,
      strokeOpacity: 0.9,
      fillColor: color,
      fillOpacity: 0.35,
      bubble: true,
    });
  }
  if (geometry.type === "Point") {
    return new AMap.CircleMarker({
      center: geometry.coordinates,
      radius: 6,
      strokeColor: color,
      strokeWeight: 1,
      fillColor: color,
      fillOpacity: 0.7,
      bubble: true,
    });
  }
  return null;
}

function numericYieldPct(raw) {
  if (raw === null || raw === undefined) return null;
  const value = Number(raw);
  if (Number.isNaN(value)) return null;
  // Backend stores yield as a percentage already (e.g. 4.16 = 4.16%). Some
  // staged sources return a fraction (0.04). Detect by magnitude.
  return value < 1 ? value * 100 : value;
}

function syncSelectionHighlight({ map, AMap, store }) {
  let lastMarker = null;
  store.subscribe((state) => {
    const sel = state.selection;
    if (lastMarker) {
      map.remove(lastMarker);
      lastMarker = null;
    }
    if (!sel || sel.type !== "building") return;
    const props = sel.props || {};
    const lng = Number(props.center_lng);
    const lat = Number(props.center_lat);
    if (Number.isNaN(lng) || Number.isNaN(lat)) return;
    lastMarker = new AMap.CircleMarker({
      center: [lng, lat],
      radius: 8,
      strokeColor: "#ffffff",
      strokeWeight: 2,
      fillColor: "var(--up)",
      fillOpacity: 0.0,
      bubble: false,
    });
    map.add(lastMarker);
    map.setCenter([lng, lat]);
  });
}
```

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/map.js`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/map.js
git commit -m "feat(user): render building polygons with yield color band"
```

---

### Task 6: Opportunity board

**Files:**
- Create: `frontend/user/modules/opportunity-board.js`

- [ ] **Step 1: Implement `opportunity-board.js`**

Write `frontend/user/modules/opportunity-board.js`:

```javascript
import { api } from "./api.js";
import { getMode } from "./modes.js";

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
    list.innerHTML = lastItems
      .map((item) => renderRow(item, mode, state.selection))
      .join("");
    list.querySelectorAll(".atlas-board-row").forEach((row) => {
      row.addEventListener("click", () => {
        const id = row.dataset.id;
        const item = lastItems.find((it) => String(it.id) === id);
        if (!item) return;
        store.set({
          selection: {
            type: "community",
            id: item.id,
            props: item,
            primaryBuildingId: item.primaryBuildingId,
          },
        });
      });
    });
  }
}

function renderRow(item, mode, selection) {
  const selected =
    selection && (selection.id === item.id || selection.id === item.primaryBuildingId);
  const cells = mode.boardColumns
    .map((col) => formatCell(item, col))
    .join("");
  return `<li class="atlas-board-row mono" data-id="${escapeAttr(item.id)}" aria-selected="${selected ? "true" : "false"}">${cells}</li>`;
}

function formatCell(item, col) {
  const raw = item[col.key];
  if (col.key === "name") {
    return `<span class="name" title="${escapeAttr(raw ?? "")}">${escapeText(raw ?? "—")}</span>`;
  }
  if (col.key === "districtName") {
    return `<span class="name">${escapeText(raw ?? "—")}</span>`;
  }
  return `<span class="secondary">${formatValue(raw, col.format)}</span>`;
}

function formatValue(value, format) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (format === "pct") return `${Number(value).toFixed(2)}%`;
  if (format === "wan") return Number(value).toLocaleString("en-US");
  if (format === "int") return String(Math.round(Number(value)));
  return String(value);
}

function sortItems(items, sortSpec) {
  if (!sortSpec) return items;
  const dir = sortSpec.direction === "asc" ? 1 : -1;
  return [...items].sort((a, b) => {
    const av = a[sortSpec.key];
    const bv = b[sortSpec.key];
    if (av === bv) return 0;
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    return av > bv ? dir : -dir;
  });
}

function escapeText(value) {
  return String(value).replace(/[&<>"]/g, (c) => ({
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

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/opportunity-board.js`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/opportunity-board.js
git commit -m "feat(user): add opportunity board (yield mode end-to-end)"
```

---

### Task 7: Shell wiring (mode chips + URL sync)

**Files:**
- Create: `frontend/user/modules/shell.js`

- [ ] **Step 1: Implement `shell.js`**

Write `frontend/user/modules/shell.js`:

```javascript
import { MODES, getMode } from "./modes.js";

const VALID_MODES = new Set(MODES.map((m) => m.id));

export function initShell({ root, store }) {
  const chipsContainer = root.querySelector('[data-component="mode-chips"]');
  const runtimeTag = root.querySelector('[data-component="runtime-tag"]');
  const statusbar = root.querySelector('[data-component="statusbar"]');
  const statusbarMode = statusbar.querySelector('[data-role="statusbar-mode"]');
  const statusbarData = statusbar.querySelector('[data-role="statusbar-data"]');

  // Render chips once. Stub modes (home/city) are still clickable in Phase 2b
  // — the spec calls for switchable chips with stub board content rather than
  // disabled chips. Per-mode behavior wires up in Phase 3.
  chipsContainer.innerHTML = MODES.map(
    (m) => `<button type="button" class="atlas-mode-chip" data-mode="${m.id}" aria-pressed="false" data-stub="${m.enabled ? "false" : "true"}">⌘${m.hotkey} ${m.label}</button>`,
  ).join("");
  chipsContainer.addEventListener("click", (event) => {
    const target = event.target.closest("[data-mode]");
    if (!target) return;
    setMode(target.dataset.mode);
  });

  // Initial mode from URL ?mode=... falling back to store.
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("mode");
  if (requested && VALID_MODES.has(requested)) {
    store.set({ mode: requested });
  }

  store.subscribe(renderFromState);
  renderFromState(store.get());

  function setMode(modeId) {
    if (!VALID_MODES.has(modeId)) return;
    store.set({ mode: modeId });
    const next = new URLSearchParams(window.location.search);
    next.set("mode", modeId);
    window.history.replaceState({}, "", `${window.location.pathname}?${next.toString()}`);
  }

  function renderFromState(state) {
    const activeMode = state.mode;
    chipsContainer
      .querySelectorAll("[data-mode]")
      .forEach((btn) => {
        btn.setAttribute("aria-pressed", btn.dataset.mode === activeMode ? "true" : "false");
      });
    statusbarMode.textContent = `mode: ${activeMode}`;
    if (state.runtime) {
      const tag = state.runtime.activeDataMode || "—";
      runtimeTag.textContent = `data ${tag}`;
      statusbarData.textContent = `data: ${tag}`;
    }
  }
}
```

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/shell.js`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/shell.js
git commit -m "feat(user): wire mode chips + url sync"
```

---

### Task 8: Bootstrap + manual browser verification

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Replace `frontend/user/modules/main.js`**

Overwrite the file:

```javascript
import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";

const root = document.querySelector('[data-user-shell="atlas"]');
if (!root) {
  console.error("[atlas] user shell root not found");
} else {
  bootstrap(root).catch((err) => {
    console.error("[atlas] bootstrap failed", err);
  });
}

async function bootstrap(root) {
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
  });

  initShell({ root, store });

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

Open `scripts/phase1_smoke.py` and replace the `(f"{base}/", 'data-user-shell="atlas"')` row with two rows that prove the new layout html landed:

Find:
```python
            (f"{base}/", 'data-user-shell="atlas"'),
```

Replace with:
```python
            (f"{base}/", 'data-user-shell="atlas"'),
            (f"{base}/", 'data-component="mode-chips"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 9 rows OK, exit 0.

- [ ] **Step 5: Manual browser capture**

Start uvicorn explicitly with mock mode (so the map is non-empty), then capture a screenshot:

```bash
ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013 &
UVICORN_PID=$!
sleep 2
python3 scripts/browser_capture_smoke.py --url http://127.0.0.1:8013/
kill $UVICORN_PID 2>/dev/null
```

The capture script writes a PNG under `output/playwright/`. Open it and confirm:
- The dark D1 shell loads
- Three mode chips on the topbar — yield pressed (green), home/city slightly dimmed (`data-stub="true"`) but still clickable
- The map area shows tiles centered on Shanghai (or, if `AMAP_API_KEY` is unset locally, the polished `atlas-map-error` panel)
- The right rail shows the opportunity board with rows (when AMap is unavailable the board still renders — it's data-driven, not map-driven)

If `AMAP_API_KEY` is unset, that's a real environmental constraint — note it in your report. The board functionality is the load-bearing acceptance for Phase 2b.

- [ ] **Step 6: Update `README.md`**

Open `README.md`, find the "路由布局（Phase 2a 起）" heading and change it to "路由布局（Phase 2b 起）".

Then find the row:
```markdown
| `/` | `frontend/user/` | 用户平台壳（Phase 1：D1 视觉占位） |
```

Replace with:
```markdown
| `/` | `frontend/user/` | 用户平台。收益模式端到端：AMap 楼栋 + 机会榜 + URL ?mode= 同步。Home/City 模式 chip 已启用，行为见 Phase 3。 |
```

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): bootstrap yield-mode end-to-end + extend smoke"
```

---

## Phase 2b Exit Criteria

Run each and confirm before declaring Phase 2b complete:

- [ ] `pytest -q` — 20 passed (no backend change in this phase)
- [ ] `node --test tests/frontend/` — 12 passed (5 state + 7 modes)
- [ ] `cd frontend/user/modules && node --check state.js && node --check api.js && node --check runtime.js && node --check modes.js && node --check map.js && node --check opportunity-board.js && node --check shell.js && node --check main.js` — exit 0 each
- [ ] `node --check frontend/backstage/app.js` — exit 0 (regression guard)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 9 rows OK
- [ ] Manual: open `http://127.0.0.1:8013/?mode=yield` — three mode chips render, yield is pressed, board lists ≥1 row, statusbar shows `data: mock` (under `ATLAS_ENABLE_DEMO_MOCK=1`)
- [ ] Manual: click another mode chip → URL updates to `?mode=home` (or `city`); board shows the "Phase 3 启用" placeholder; map stays put
- [ ] Manual: click a board row → row highlights with the green left bar; map recenters and draws a white-ringed marker (only verifiable when AMap key present)
- [ ] `git log --oneline 75c4165..HEAD` shows 8 focused feature commits

## Out of Scope (deferred to Phase 3 and later)

- Detail drawer (楼栋透视) — Phase 3
- Per-mode filter persistence in localStorage — Phase 3
- Filter chips behavior — Phase 3 (placeholder bar exists)
- Watchlist (★), annotations, alerts — Phase 4-5
- Home onboarding (预算/区域/面积) — Phase 3
- City district aggregate map — Phase 3
- Keyboard shortcuts (⌘1/2/3, ⌘K) — Phase 6
- bbox/viewport server-side filtering — Phase 3 will add `?bbox=` to v2 endpoints; this phase loads the full result set client-side
- Map↔board cross-direction selection (board click recentering map) — Phase 2b only wires map → board (board row highlights when its primaryBuildingId matches the clicked polygon). Board → map recentering uses opportunity `x/y` which are not WGS coordinates and can't be projected without additional joins; deferred to Phase 3
- Spec deliverable "榜单随视野变" (board filtered by current viewport) — depends on bbox endpoints from Phase 3; for Phase 2b the board shows the full result set sorted by yield desc
