# Phase 3d — City Mode District Polygons + Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Light up City mode end-to-end. Switching to the City chip clears building polygons, fetches district boundaries via `AMap.DistrictSearch`, and renders them filled by Δ-vs-mean yield (green = above the city average, red = below). The opportunity board sources its rows from `/api/v2/map/districts` instead of `/api/v2/opportunities` and shows district name / mean yield / score.

**Architecture:** Frontend-only. `runtime.js` extends the AMap script src to include the `AMap.DistrictSearch` plugin. `map.js` becomes mode-aware: it tracks current overlays in a `currentOverlays` array, subscribes to mode changes, and on each change clears existing overlays and renders the appropriate set (yield/home → buildings; city → district polygons). District boundaries are cached in a module-level `Map<districtName, boundaries[]>` so subsequent city-mode entries are instant. `modes.js` adds `districtColorFor(yieldValue, avgYield)` for the green/amber/red Δ band. `opportunity-board.js` branches the data source by mode: `loadFor("city")` calls `api.mapDistricts()` and renders the district list; yield/home keep their existing `api.opportunities()` path. Drawer integration for districts is deferred — clicks on city polygons set `state.selection = {type: "district", id, props}` but the drawer just shows the district name + KPIs from the row data (no new backend endpoint).

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for the new pure helper · `AMap.DistrictSearch` plugin (loaded via the existing AMap script tag) · existing `/api/v2/map/districts` endpoint. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 三模式语义 row "city: 行政区聚合涂色：Δ 均值（涨绿跌红）" + section 5 row 4 "全市观察")

**Prior plan:** 2026-04-24-phase-3c-2-home-onboarding.md (merged at `dcfc8e2`)

---

## File Structure (Phase 3d outcome)

```
frontend/user/
├── modules/
│   ├── runtime.js                 # MODIFIED: add AMap.DistrictSearch to plugin list
│   ├── modes.js                   # MODIFIED: add districtColorFor(value, avg)
│   ├── map.js                     # MODIFIED: mode-aware rendering + district polygons
│   └── opportunity-board.js       # MODIFIED: city mode loads from mapDistricts
└── styles/
    └── map.css                    # MODIFIED: district overlay styling

tests/frontend/
└── test_modes.mjs                 # MODIFIED: +5 tests for districtColorFor

scripts/phase1_smoke.py            # MODIFIED: +1 row asserting GET /api/v2/map/districts shape
README.md                          # MODIFIED: bump Phase 3c-2 → Phase 3d
```

**Out-of-scope (deferred):**
- City-mode detail drawer with district KPIs (region 均租售比 / 挂牌量 / 6-12-24 月趋势 / 分位数). Click on a district polygon stores selection but the drawer just renders the row data; full district aggregate endpoint is a Phase 3e backend task.
- Street-level (`subdistrict`) aggregate when district data is too sparse — spec section 5 calls this out as a Phase 6 polish.
- Trend / quantile fields on district rows — backend already returns `trend` per district but we don't visualize it; trend chart is Phase 6.
- District color legend overlay — single-line legend can land in Phase 6 polish.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-3d-city-mode .worktrees/phase-3d-city-mode
cd .worktrees/phase-3d-city-mode
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 40 pytest passed; 51 node tests passed; 13 smoke routes OK.

---

### Task 1: runtime.js — load DistrictSearch plugin

**Files:**
- Modify: `frontend/user/modules/runtime.js`

The current AMap script src loads only `AMap.Scale,AMap.ToolBar`. Backstage uses `AMap.DistrictSearch,AMap.Scale,AMap.ToolBar`. We add it.

- [ ] **Step 1: Edit `frontend/user/modules/runtime.js`**

Find the line:

```javascript
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.Scale,AMap.ToolBar`;
```

Replace with:

```javascript
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.DistrictSearch,AMap.Scale,AMap.ToolBar`;
```

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/runtime.js`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/runtime.js
git commit -m "feat(user): load AMap.DistrictSearch plugin"
```

---

### Task 2: modes.js — districtColorFor + tests

**Files:**
- Modify: `frontend/user/modules/modes.js`
- Modify: `tests/frontend/test_modes.mjs`

District color band per spec: Δ vs city-mean. We accept the district value and the mean; positive Δ → green (`var(--up)`), negative → red (`var(--down)`), small dead-zone (≤ 0.2 percentage points) → warn (`var(--warn)`). Null/NaN → dim.

- [ ] **Step 1: Add tests**

Open `tests/frontend/test_modes.mjs`. Find the import line (it should currently be):

```javascript
import {
  MODES,
  getMode,
  yieldColorFor,
  defaultFiltersFor,
  resolveDefaultFilters,
} from "../../frontend/user/modules/modes.js";
```

Replace with:

```javascript
import {
  MODES,
  getMode,
  yieldColorFor,
  defaultFiltersFor,
  resolveDefaultFilters,
  districtColorFor,
} from "../../frontend/user/modules/modes.js";
```

Append at the end of the file:

```javascript
test("districtColorFor: null/NaN returns dim", () => {
  assert.equal(districtColorFor(null, 4), "var(--text-dim)");
  assert.equal(districtColorFor(Number.NaN, 4), "var(--text-dim)");
  assert.equal(districtColorFor(4, null), "var(--text-dim)");
});

test("districtColorFor: value above mean by > 0.2 → up", () => {
  assert.equal(districtColorFor(5, 4), "var(--up)");
});

test("districtColorFor: value below mean by > 0.2 → down", () => {
  assert.equal(districtColorFor(3, 4), "var(--down)");
});

test("districtColorFor: value within ±0.2 of mean → warn", () => {
  assert.equal(districtColorFor(4.1, 4), "var(--warn)");
  assert.equal(districtColorFor(3.9, 4), "var(--warn)");
});

test("districtColorFor: handles fractional yield (auto-scale 0.04 → 4)", () => {
  // The function should accept either fraction or percent — same heuristic as
  // yieldColorFor — to handle staged data that stores yield as 0.04 vs 4.0.
  assert.equal(districtColorFor(0.05, 0.04), "var(--up)");
  assert.equal(districtColorFor(0.03, 0.04), "var(--down)");
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_modes.mjs`
Expected: import error (`districtColorFor` undefined).

- [ ] **Step 3: Implement `districtColorFor` in `frontend/user/modules/modes.js`**

Find the existing `yieldColorFor` function:

```javascript
export function yieldColorFor(yieldPct) {
  if (yieldPct === null || yieldPct === undefined || Number.isNaN(yieldPct)) {
    return "var(--text-dim)";
  }
  if (yieldPct < 3.5) return "var(--down)";
  if (yieldPct < 5) return "var(--warn)";
  return "var(--up)";
}
```

Add directly below it:

```javascript
function normalizeYieldScalar(value) {
  if (value === null || value === undefined) return null;
  const num = Number(value);
  if (Number.isNaN(num)) return null;
  // Match the percent-vs-fraction heuristic in map.js: < 1 means fraction.
  return num < 1 ? num * 100 : num;
}

export function districtColorFor(value, mean) {
  const v = normalizeYieldScalar(value);
  const m = normalizeYieldScalar(mean);
  if (v === null || m === null) return "var(--text-dim)";
  const delta = v - m;
  if (delta > 0.2) return "var(--up)";
  if (delta < -0.2) return "var(--down)";
  return "var(--warn)";
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_modes.mjs`
Expected: 20 tests passed (existing 15 + 5 new).

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs`
Expected: 56 tests passed (5 + 20 + 11 + 6 + 9 + 5).

Run: `node --check frontend/user/modules/modes.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/modes.js tests/frontend/test_modes.mjs
git commit -m "feat(user): add districtColorFor color band for city mode"
```

---

### Task 3: map.js — mode-aware rendering + district polygons

**Files:**
- Modify: `frontend/user/modules/map.js`
- Modify: `frontend/user/styles/map.css`

The current `initMap` boots the map, fetches buildings, and renders building polygons unconditionally. We refactor:

- Track the AMap instance, the current set of overlays, and the current mode at module scope inside `initMap`.
- After AMap loads, subscribe to store mode changes; on each change, clear current overlays (`map.remove(currentOverlays)`) and render the new set.
- For yield/home modes: render building polygons (existing logic).
- For city mode: fetch all district boundaries via `AMap.DistrictSearch` (cached per district name in a module-level Map), render each as an `AMap.Polygon` colored by `districtColorFor(district.yield, summary.avgYield)`. On click, `store.set({selection: {type: "district", id, props}})`.

The `syncSelectionHighlight` logic stays — when a building selection comes in, it draws the highlight marker; for districts, it just no-ops (existing guard returns early when `sel.type !== "building"`).

- [ ] **Step 1: Replace `frontend/user/modules/map.js`**

Open the file. The current top-of-file imports are:

```javascript
import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import { yieldColorFor } from "./modes.js";
```

Replace with:

```javascript
import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import { yieldColorFor, districtColorFor } from "./modes.js";
```

Find the existing `initMap` function. It currently ends after calling `syncSelectionHighlight({ map, AMap, store });` and before `function showError(...)`. Replace the WHOLE existing `initMap` function body with this version (this is a substantial refactor — replace the entire function from `export async function initMap({ container, store })` to its closing brace `}`):

```javascript
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

  let currentOverlays = [];
  let currentMode = null;
  let renderToken = 0;

  function clearOverlays() {
    if (currentOverlays.length === 0) return;
    map.remove(currentOverlays);
    currentOverlays = [];
  }

  async function renderForMode(modeId) {
    const myToken = ++renderToken;
    clearOverlays();
    if (modeId === "city") {
      const next = await renderDistricts({ AMap, map });
      if (myToken !== renderToken) {
        // a newer mode-change won — discard these overlays
        map.remove(next);
        return;
      }
      currentOverlays = next;
    } else {
      const next = await renderBuildings({ AMap, map, store });
      if (myToken !== renderToken) {
        map.remove(next);
        return;
      }
      currentOverlays = next;
    }
  }

  currentMode = store.get().mode;
  await renderForMode(currentMode);

  store.subscribe((state) => {
    if (state.mode !== currentMode) {
      currentMode = state.mode;
      renderForMode(currentMode).catch((err) =>
        console.error("[atlas:map] renderForMode failed", err),
      );
    }
  });

  syncSelectionHighlight({ map, AMap, store });

  return map;
}
```

Find the existing `renderBuildings` function. Replace it with this version (it now takes the new `{ AMap, map, store }` signature, fetches buildings inline, and returns the array of overlays so the caller can track them):

```javascript
async function renderBuildings({ AMap, map, store }) {
  const overlays = [];
  let buildings;
  try {
    buildings = await api.mapBuildings();
  } catch (err) {
    console.error("[atlas:map] buildings load failed", err);
    return overlays;
  }
  for (const feature of buildings.features || []) {
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
  if (overlays.length > 0) map.add(overlays);
  return overlays;
}
```

Add a NEW function `renderDistricts` directly below `renderBuildings`:

```javascript
const districtBoundaryCache = new Map();

async function renderDistricts({ AMap, map }) {
  const overlays = [];
  let payload;
  try {
    payload = await api.mapDistricts();
  } catch (err) {
    console.error("[atlas:map] districts load failed", err);
    return overlays;
  }

  const districts = payload.districts || [];
  const summary = payload.summary || {};
  const meanYield = summary.avgYield;

  if (!AMap.DistrictSearch) {
    console.warn("[atlas:map] AMap.DistrictSearch unavailable — falling back to label markers");
    for (const district of districts) {
      // No polygon plugin — skip silently. Phase 6 may add label markers fallback.
    }
    return overlays;
  }

  const search = new AMap.DistrictSearch({
    level: "district",
    extensions: "all",
    subdistrict: 0,
    showbiz: false,
  });

  await Promise.all(
    districts.map(async (district) => {
      const boundaries = await fetchBoundariesCached(search, district.name);
      const color = districtColorFor(district.yield, meanYield);
      for (const path of boundaries) {
        const polygon = new AMap.Polygon({
          path,
          strokeColor: color,
          strokeWeight: 1,
          strokeOpacity: 0.85,
          fillColor: color,
          fillOpacity: 0.25,
          bubble: false,
        });
        polygon.setExtData({ districtId: district.id, props: district });
        polygon.on("click", () => {
          store.set({
            selection: { type: "district", id: district.id, props: district },
          });
        });
        overlays.push(polygon);
      }
    }),
  );

  if (overlays.length > 0) map.add(overlays);
  return overlays;
}

function fetchBoundariesCached(search, districtName) {
  if (districtBoundaryCache.has(districtName)) {
    return Promise.resolve(districtBoundaryCache.get(districtName));
  }
  return new Promise((resolve) => {
    search.search(districtName, (status, result) => {
      if (status !== "complete") {
        districtBoundaryCache.set(districtName, []);
        resolve([]);
        return;
      }
      const first = result?.districtList?.[0];
      const boundaries = first?.boundaries ?? [];
      districtBoundaryCache.set(districtName, boundaries);
      resolve(boundaries);
    });
  });
}
```

Note: `renderDistricts` references `store` inside its click handler but doesn't take `store` as a parameter — that's a closure leak. The cleanest fix is to pass `store` through. Update the `renderForMode` call site to pass `store`:

In the `renderForMode` function inside `initMap`, change the city-mode branch from:

```javascript
      const next = await renderDistricts({ AMap, map });
```

to:

```javascript
      const next = await renderDistricts({ AMap, map, store });
```

And update the `renderDistricts` signature and use:

```javascript
async function renderDistricts({ AMap, map, store }) {
```

(the `store` parameter is now on the destructured arg list — the click handler already references it correctly).

The existing `syncSelectionHighlight`, `createOverlay`, `numericYieldPct`, and `showError` helpers are unchanged.

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/map.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs`
Expected: 56 tests passed (no test changes in this task).

Run: `pytest -q`
Expected: 40 passed.

- [ ] **Step 3: Append a small style hint to `frontend/user/styles/map.css`**

District polygons get filled with the same fill colors as buildings (driven inline). No new selectors needed for now. **Skip step 3** — leave map.css unchanged in this task.

- [ ] **Step 4: Commit**

```bash
git add frontend/user/modules/map.js
git commit -m "feat(user): mode-aware map rendering + city district polygons"
```

---

### Task 4: opportunity-board.js — city mode loads from mapDistricts

**Files:**
- Modify: `frontend/user/modules/opportunity-board.js`

For city mode, the API source switches to `/api/v2/map/districts` and the rows are districts (the boardColumns config in `modes.js` already names `districtName / yield / score`). For yield/home, the existing `api.opportunities()` path stays. The row click handler dispatches `selection` with the appropriate type.

- [ ] **Step 1: Open `frontend/user/modules/opportunity-board.js` and update `loadFor`**

The current `loadFor` body (after Phase 3c-2) is:

```javascript
  async function loadFor(modeId, state) {
    const mode = getMode(modeId);
    if (!mode.enabled) {
      lastItems = [];
      render(store.get());
      return;
    }
    const persisted = state && state.filters ? state.filters[modeId] : null;
    const filters =
      persisted && Object.keys(persisted).length > 0
        ? persisted
        : resolveDefaultFilters(modeId, (state && state.userPrefs) || null);
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

Replace it with:

```javascript
  async function loadFor(modeId, state) {
    const mode = getMode(modeId);
    if (!mode.enabled) {
      lastItems = [];
      render(store.get());
      return;
    }
    if (modeId === "city") {
      try {
        const data = await api.mapDistricts();
        lastItems = sortItems(data.districts || [], mode.defaultSort);
      } catch (err) {
        console.error("[atlas:board] districts load failed", err);
        lastItems = [];
      }
      render(store.get());
      return;
    }
    const persisted = state && state.filters ? state.filters[modeId] : null;
    const filters =
      persisted && Object.keys(persisted).length > 0
        ? persisted
        : resolveDefaultFilters(modeId, (state && state.userPrefs) || null);
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

- [ ] **Step 2: Update the row click handler to disambiguate by mode**

Find the existing row click handler inside `render(state)`:

```javascript
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
```

Replace with:

```javascript
    list.querySelectorAll(".atlas-board-row").forEach((row) => {
      row.addEventListener("click", () => {
        const id = row.dataset.id;
        const item = lastItems.find((it) => String(it.id) === id);
        if (!item) return;
        const selectionType = state.mode === "city" ? "district" : "community";
        const selection = {
          type: selectionType,
          id: item.id,
          props: item,
        };
        if (selectionType === "community" && item.primaryBuildingId) {
          selection.primaryBuildingId = item.primaryBuildingId;
        }
        store.set({ selection });
      });
    });
```

- [ ] **Step 3: Guard the detail drawer against district selections**

Both the map's district polygon click (Task 3) and the board row click (this task) emit `selection: {type: "district", ...}`. The drawer's existing `fetchDetail` throws "未知的选中类型：district" on this type, which then renders as an error in the drawer body. Until Phase 3e adds a real district endpoint, the drawer should silently skip district selections (close itself if open, ignore if closed).

Open `frontend/user/modules/detail-drawer.js`. Find the existing `handleStateChange` function:

```javascript
  function handleStateChange(state) {
    const sel = state.selection;
    if (!sel) {
      if (lastSelectionId !== null) {
        renderClosed();
        lastSelectionId = null;
        lastMode = null;
      }
      return;
    }
```

Replace with:

```javascript
  function handleStateChange(state) {
    const sel = state.selection;
    if (!sel || (sel.type !== "building" && sel.type !== "community")) {
      if (lastSelectionId !== null) {
        renderClosed();
        lastSelectionId = null;
        lastMode = null;
      }
      return;
    }
```

This treats any non-building / non-community selection (including `district`) the same as a null selection — close the drawer if open, no-op otherwise.

- [ ] **Step 4: Verify**

Run: `node --check frontend/user/modules/opportunity-board.js`
Expected: exit 0.

Run: `node --check frontend/user/modules/detail-drawer.js`
Expected: exit 0.

Run combined frontend tests: 56 passed (no test additions in this task).

Run: `pytest -q`
Expected: 40 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/opportunity-board.js frontend/user/modules/detail-drawer.js
git commit -m "feat(user): city mode board sources from mapDistricts + drawer ignores district selections"
```

---

### Task 5: smoke + README

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Extend smoke to assert districts payload shape**

The smoke already hits `/api/v2/map/districts` with substring `'"districts"'`. That's enough to prove the route returns the right top-level key. We add a SECOND assertion against the same endpoint that checks for `'"summary"'` — this confirms the city-mode color band has access to the city-mean yield field.

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/map/districts", '"districts"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/map/districts", '"summary"'),
```

- [ ] **Step 2: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 14 OK, exit 0.

- [ ] **Step 3: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 3c-2 起）` and change to `## 路由布局（Phase 3d 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式端到端 + 详情抽屉 + 实时筛选条 + 自住模式（弹窗 + 偏好持久化）+ 全市模式（行政区多边形 + Δ 均值涨绿跌红 + 板列切换到区聚合）。
```

- [ ] **Step 4: Verify all exit criteria**

Run each:
- `pytest -q` → 40 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs` → 56 passed (5 + 20 + 11 + 6 + 9 + 5)
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 14 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire city mode into smoke + docs"
```

---

## Phase 3d Exit Criteria

- [ ] `pytest -q` — 40 passed (no backend changes)
- [ ] `node --test ...` — 56 passed (5 state + 20 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check` — exit 0 each
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 14 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` — visit `http://127.0.0.1:8013/?mode=city`. Map shows 16 district polygons (with valid `AMAP_API_KEY`); colors mostly red since most district yields trail the city mean in mock data; board lists districts by mean yield desc.
- [ ] Manual: switch back to yield → district polygons disappear, building polygons return; the React-style flicker is acceptable.
- [ ] `git log --oneline dcfc8e2..HEAD` shows exactly 5 Phase 3d commits

## Out of Scope (deferred)

- District detail drawer with aggregate KPIs (need new `/api/v2/districts/{id}` endpoint) — Phase 3e
- Street-level subdistrict aggregate when district data is sparse — Phase 6
- Trend chart inside drawer (6/12/24 月) — Phase 6
- Color band legend overlay — Phase 6 polish
- Quantile fields per district — backend doesn't expose them today
