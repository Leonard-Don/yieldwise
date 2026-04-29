# Phase 5b — Alerts Banner Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface alerts visually at the very top of the user platform: on page load, fetch `/api/v2/alerts/since-last-open`; when items exist, render a collapsible banner above the topbar showing a one-line summary plus an expandable change list and a "标记已读" button that calls `POST /api/v2/alerts/mark-seen` and dismisses the banner.

**Architecture:** Pure frontend addition. New `frontend/user/modules/alerts.js` is a focused DOM module that subscribes to `state.alerts` (a slice owning `{items, last_open_at}`). It owns a banner mount placed as a new first row inside `.atlas-shell` (sibling of `.atlas-topbar`). On boot, `main.js` prefetches via `api.alerts.sinceLastOpen()` and stashes the response. Click "标记已读" → optimistic dismiss + `POST /mark-seen` → on success, remains dismissed; on error, refetches state. Pure formatting helpers live in `alerts-helpers.js` (`formatAlertLine`, `severityFor`) and are unit-tested via `node:test`.

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` · existing `/api/v2/alerts/*` endpoints (Phase 5a). No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 row 1 "变化横幅" + section 5 row 2 顶栏 "变化计数")

**Prior plan:** 2026-04-24-phase-5a-alerts-backend.md (merged at `fcf17c4`)

---

## File Structure (Phase 5b outcome)

```
frontend/user/
├── index.html                       # MODIFIED: add banner mount as first child of .atlas-shell
├── styles/
│   ├── shell.css                    # MODIFIED: grid +1 row + banner styling
│   └── alerts.css                   # NEW
└── modules/
    ├── api.js                       # MODIFIED: api.alerts.{sinceLastOpen, markSeen, getRules, patchRules}
    ├── alerts-helpers.js            # NEW — pure helpers (formatAlertLine, severityFor)
    ├── alerts.js                    # NEW — DOM module: banner + collapse + mark-seen
    └── main.js                      # MODIFIED: prefetch alerts + initAlerts wiring

tests/frontend/
└── test_alerts_helpers.mjs          # NEW (~6 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/alerts/since-last-open
README.md                            # MODIFIED: bump Phase 5a → Phase 5b
```

**Out-of-scope (deferred):**
- Target name resolution — alerts only show `target_id` (e.g. `daning-jinmaofu-b1`). The backend payload doesn't include human-readable names; resolving them would mean per-target fetches or a backend join. Phase 6 polish.
- Banner collapse-state persistence (`localStorage`) — the banner re-renders fresh on each load.
- Topbar 变化计数 chip (separate from the banner) — the banner header IS the count display for Phase 5b. A dedicated chip can be added in Phase 6.
- Editing alert rules from the UI — the backend has GET/PATCH /alerts/rules but no UI form. Defer to a Phase 6 偏好-style modal extension.
- Manual browser screenshot

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-5b-alerts-banner .worktrees/phase-5b-alerts-banner
cd .worktrees/phase-5b-alerts-banner
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 90 pytest passed; 65 node tests passed; 17 smoke routes OK.

---

### Task 1: API client extension + alerts helpers

**Files:**
- Modify: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/alerts-helpers.js`
- Create: `tests/frontend/test_alerts_helpers.mjs`

We add `api.alerts.{getRules, patchRules, sinceLastOpen, markSeen}` and a tiny pure helper module that keeps banner formatting out of the DOM module.

Helpers:
- `formatAlertLine(alert)` — returns a Chinese summary line per kind:
  - `yield_up` / `yield_down` → `"租售比 4.00% → 4.60% (+0.60)"`
  - `price_drop` → `"总价 1000 → 950 万 (−5.0%)"` (percentage of base)
  - `score_jump` → `"机会分 60 → 70 (+10)"`
- `severityFor(alert)` — returns `"up"` / `"down"` / `"warn"` for CSS theming hooks

- [ ] **Step 1: Write failing tests for the helper**

Write `tests/frontend/test_alerts_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatAlertLine,
  severityFor,
} from "../../frontend/user/modules/alerts-helpers.js";

test("formatAlertLine: yield_up renders pp delta", () => {
  const line = formatAlertLine({
    kind: "yield_up",
    from_value: 4.0,
    to_value: 4.6,
    delta: 0.6,
  });
  assert.equal(line, "租售比 4.00% → 4.60% (+0.60)");
});

test("formatAlertLine: yield_down renders negative delta", () => {
  const line = formatAlertLine({
    kind: "yield_down",
    from_value: 4.0,
    to_value: 3.4,
    delta: -0.6,
  });
  assert.equal(line, "租售比 4.00% → 3.40% (−0.60)");
});

test("formatAlertLine: price_drop renders percent off base", () => {
  const line = formatAlertLine({
    kind: "price_drop",
    from_value: 1000.0,
    to_value: 950.0,
    delta: -50.0,
  });
  assert.equal(line, "总价 1000 → 950 万 (−5.0%)");
});

test("formatAlertLine: score_jump renders signed delta", () => {
  const up = formatAlertLine({
    kind: "score_jump",
    from_value: 60,
    to_value: 70,
    delta: 10,
  });
  assert.equal(up, "机会分 60 → 70 (+10)");
  const down = formatAlertLine({
    kind: "score_jump",
    from_value: 60,
    to_value: 50,
    delta: -10,
  });
  assert.equal(down, "机会分 60 → 50 (−10)");
});

test("formatAlertLine: unknown kind falls back to string", () => {
  const line = formatAlertLine({ kind: "mystery", from_value: 1, to_value: 2 });
  assert.equal(line, "mystery 1 → 2");
});

test("severityFor: yield_up + score_jump positive → up", () => {
  assert.equal(severityFor({ kind: "yield_up" }), "up");
  assert.equal(severityFor({ kind: "score_jump", delta: 10 }), "up");
});

test("severityFor: yield_down + price_drop + negative score → down", () => {
  assert.equal(severityFor({ kind: "yield_down" }), "down");
  assert.equal(severityFor({ kind: "price_drop" }), "down");
  assert.equal(severityFor({ kind: "score_jump", delta: -5 }), "down");
});

test("severityFor: unknown kind → warn", () => {
  assert.equal(severityFor({ kind: "mystery" }), "warn");
});
```

- [ ] **Step 2: Verify failing**

Run: `node --test tests/frontend/test_alerts_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement `frontend/user/modules/alerts-helpers.js`**

```javascript
const MINUS = "−";

function signed(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const num = Number(value);
  const abs = Math.abs(num).toFixed(digits);
  return num >= 0 ? `+${abs}` : `${MINUS}${abs}`;
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return Number(value).toFixed(digits);
}

function fmtInt(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return String(Math.round(Number(value)));
}

export function formatAlertLine(alert) {
  if (!alert) return "";
  const { kind, from_value: from, to_value: to, delta } = alert;
  if (kind === "yield_up" || kind === "yield_down") {
    return `租售比 ${fmt(from)}% → ${fmt(to)}% (${signed(delta)})`;
  }
  if (kind === "price_drop") {
    const fromNum = Number(from);
    const pct = fromNum > 0 ? ((Number(to) - fromNum) / fromNum) * 100 : 0;
    const pctSigned = pct >= 0 ? `+${pct.toFixed(1)}` : `${MINUS}${Math.abs(pct).toFixed(1)}`;
    return `总价 ${fmtInt(from)} → ${fmtInt(to)} 万 (${pctSigned}%)`;
  }
  if (kind === "score_jump") {
    const sign = Number(delta) >= 0 ? "+" : MINUS;
    return `机会分 ${fmtInt(from)} → ${fmtInt(to)} (${sign}${Math.abs(Math.round(Number(delta)))})`;
  }
  return `${kind} ${fmtInt(from)} → ${fmtInt(to)}`;
}

export function severityFor(alert) {
  if (!alert) return "warn";
  const kind = alert.kind;
  if (kind === "yield_up") return "up";
  if (kind === "yield_down" || kind === "price_drop") return "down";
  if (kind === "score_jump") {
    return Number(alert.delta) >= 0 ? "up" : "down";
  }
  return "warn";
}
```

- [ ] **Step 4: Verify passing**

Run: `node --test tests/frontend/test_alerts_helpers.mjs`
Expected: 8 tests passed.

Run: `node --check frontend/user/modules/alerts-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Extend `frontend/user/modules/api.js`**

Open `frontend/user/modules/api.js`. The current `export const api = ...` block (after Phase 4b) has `opportunities`, `mapBuildings`, `mapDistricts`, `districtsAll`, `runtimeConfig`, `userPrefs`, `watchlist`, `annotations`, `invalidate`. Add an `alerts` namespace AFTER `annotations`. Replace the export block with:

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
  alerts: {
    sinceLastOpen: () => getJSONFresh("/api/v2/alerts/since-last-open"),
    markSeen: () => postJSON("/api/v2/alerts/mark-seen", {}),
    getRules: () => getJSONFresh("/api/v2/alerts/rules"),
    patchRules: (payload) => patchJSON("/api/v2/alerts/rules", payload),
  },
  invalidate,
};
```

- [ ] **Step 6: Sanity-check**

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs`
Expected: 73 passed (5 + 20 + 11 + 6 + 9 + 5 + 4 + 5 + 8).

Run: `pytest -q`
Expected: 90 passed (no backend changes).

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/alerts-helpers.js tests/frontend/test_alerts_helpers.mjs
git commit -m "feat(user): add alerts API client + format/severity helpers"
```

---

### Task 2: alerts banner mount + CSS

**Files:**
- Modify: `frontend/user/index.html`
- Modify: `frontend/user/styles/shell.css`
- Create: `frontend/user/styles/alerts.css`

The banner is a new first row in `.atlas-shell`. CSS grid changes from `auto auto 1fr auto` to `auto auto auto 1fr auto` (banner / topbar / filterbar / main / statusbar). The banner element is `hidden` by default; alerts.js (Task 3) toggles visibility.

- [ ] **Step 1: Add the banner mount in `frontend/user/index.html`**

Open `frontend/user/index.html`. Find the `<link rel="stylesheet" href="/styles/onboarding.css" />` line and add directly below it:

```html
    <link rel="stylesheet" href="/styles/alerts.css" />
```

Find the opening `<div class="atlas-shell">` and add a new banner element directly after it, BEFORE the existing `<header class="atlas-topbar">`:

```html
      <section class="atlas-banner" data-component="alerts-banner" hidden>
        <div class="atlas-banner-summary">
          <strong class="atlas-banner-count" data-role="banner-count">0 条变化</strong>
          <span class="atlas-banner-since mono dim" data-role="banner-since"></span>
        </div>
        <div class="atlas-banner-actions">
          <button type="button" class="atlas-banner-toggle" data-role="banner-toggle" aria-expanded="false">展开</button>
          <button type="button" class="atlas-banner-mark" data-role="banner-mark">标记已读</button>
        </div>
        <ol class="atlas-banner-list" data-role="banner-list" hidden></ol>
      </section>
```

- [ ] **Step 2: Update grid + banner styling in `frontend/user/styles/shell.css`**

Open `frontend/user/styles/shell.css`. Find the existing `.atlas-shell` rule:

```css
.atlas-shell {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  height: 100vh;
}
```

Replace the `grid-template-rows` line. The new shape is:

```css
.atlas-shell {
  display: grid;
  grid-template-rows: auto auto auto 1fr auto;
  height: 100vh;
}
```

This adds an extra `auto` track at the top for the banner. When the banner is `hidden` it produces an empty 0-height row, which is fine.

- [ ] **Step 3: Create `frontend/user/styles/alerts.css`**

```css
.atlas-banner {
  display: flex;
  flex-direction: column;
  background: rgba(255, 176, 32, 0.12);
  border-bottom: 1px solid var(--warn);
  color: var(--text-0);
  font-family: var(--font-ui);
}

.atlas-banner[hidden] {
  display: none;
}

.atlas-banner-summary {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 8px 14px;
  flex: 1;
}

.atlas-banner-count {
  font-size: 12px;
  letter-spacing: 0.06em;
  color: var(--warn);
}

.atlas-banner-since {
  font-size: 10px;
  letter-spacing: 0.06em;
}

.atlas-banner-actions {
  display: flex;
  gap: 6px;
  padding: 0 14px 8px;
}

.atlas-banner-toggle,
.atlas-banner-mark {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 3px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.06em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-banner-toggle:hover,
.atlas-banner-mark:hover {
  color: var(--text-0);
  border-color: var(--warn);
}

.atlas-banner-mark {
  border-color: var(--warn);
  color: var(--warn);
}

.atlas-banner-mark:hover {
  background: rgba(255, 176, 32, 0.12);
}

.atlas-banner-mark[disabled],
.atlas-banner-toggle[disabled] {
  opacity: 0.4;
  cursor: progress;
}

.atlas-banner-list {
  list-style: none;
  margin: 0;
  padding: 0 14px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border-top: 1px dashed var(--line);
}

.atlas-banner-list[hidden] {
  display: none;
}

.atlas-banner-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 2fr);
  gap: 10px;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  align-items: baseline;
  padding: 4px 0;
  border-bottom: 1px solid var(--line);
}

.atlas-banner-row:last-child {
  border-bottom: none;
}

.atlas-banner-target {
  color: var(--text-dim);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atlas-banner-line {
  color: var(--text-0);
}

.atlas-banner-row[data-severity="up"] .atlas-banner-line {
  color: var(--up);
}

.atlas-banner-row[data-severity="down"] .atlas-banner-line {
  color: var(--down);
}

.atlas-banner-row[data-severity="warn"] .atlas-banner-line {
  color: var(--warn);
}
```

- [ ] **Step 4: Sanity-check**

Run: `grep -c 'data-component="alerts-banner"' frontend/user/index.html`
Expected: 1.

Run: `grep -c 'href="/styles/alerts.css"' frontend/user/index.html`
Expected: 1.

Run: `pytest -q`
Expected: 90 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/index.html frontend/user/styles/shell.css frontend/user/styles/alerts.css
git commit -m "feat(user): add alerts banner mount + slide-row grid"
```

---

### Task 3: alerts.js DOM module

**Files:**
- Create: `frontend/user/modules/alerts.js`

The module:
- Subscribes to `state.alerts` (`{items, last_open_at}`)
- When `items.length > 0`: shows banner with count + `自 ${last_open_at} 起`; toggle button expands the per-row list
- When `items.length === 0`: hides banner
- Mark-seen click: optimistic dismiss (sets `state.alerts = {items: [], last_open_at: <something>}`); then `POST /mark-seen`; on error refetch via `api.alerts.sinceLastOpen()`

- [ ] **Step 1: Implement `frontend/user/modules/alerts.js`**

```javascript
import { api } from "./api.js";
import { formatAlertLine, severityFor } from "./alerts-helpers.js";

export function initAlerts({ root, store }) {
  const banner = root.querySelector('[data-component="alerts-banner"]');
  const countEl = banner.querySelector('[data-role="banner-count"]');
  const sinceEl = banner.querySelector('[data-role="banner-since"]');
  const toggleBtn = banner.querySelector('[data-role="banner-toggle"]');
  const markBtn = banner.querySelector('[data-role="banner-mark"]');
  const listEl = banner.querySelector('[data-role="banner-list"]');

  let expanded = false;

  toggleBtn.addEventListener("click", () => {
    expanded = !expanded;
    listEl.hidden = !expanded;
    toggleBtn.textContent = expanded ? "收起" : "展开";
    toggleBtn.setAttribute("aria-expanded", expanded ? "true" : "false");
  });

  markBtn.addEventListener("click", () => {
    void markSeen();
  });

  store.subscribe(render);
  render(store.get());

  function render(state) {
    const alerts = state.alerts || { items: [], last_open_at: null };
    const items = Array.isArray(alerts.items) ? alerts.items : [];
    if (items.length === 0) {
      banner.hidden = true;
      expanded = false;
      listEl.hidden = true;
      toggleBtn.textContent = "展开";
      toggleBtn.setAttribute("aria-expanded", "false");
      return;
    }
    banner.hidden = false;
    countEl.textContent = `${items.length} 条变化`;
    sinceEl.textContent = alerts.last_open_at
      ? `自 ${alerts.last_open_at} 起`
      : "首次扫描";
    listEl.innerHTML = items
      .map((alert) => renderRow(alert))
      .join("");
    listEl.hidden = !expanded;
  }

  function renderRow(alert) {
    const severity = severityFor(alert);
    return `<li class="atlas-banner-row" data-severity="${escapeAttr(severity)}"><span class="atlas-banner-target">${escapeText(alert.target_id || "")}</span><span class="atlas-banner-line">${escapeText(formatAlertLine(alert))}</span></li>`;
  }

  async function markSeen() {
    const before = store.get().alerts;
    markBtn.disabled = true;
    toggleBtn.disabled = true;
    // Optimistic clear
    store.set({ alerts: { items: [], last_open_at: before?.last_open_at ?? null } });
    try {
      await api.alerts.markSeen();
    } catch (err) {
      console.error("[atlas:alerts] mark-seen failed", err);
      try {
        const fresh = await api.alerts.sinceLastOpen();
        store.set({
          alerts: {
            items: fresh.items || [],
            last_open_at: fresh.last_open_at || null,
          },
        });
      } catch (refetchErr) {
        console.error("[atlas:alerts] refetch failed", refetchErr);
        // Restore previous state so the banner remains usable.
        store.set({ alerts: before });
      }
    } finally {
      markBtn.disabled = false;
      toggleBtn.disabled = false;
    }
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

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/alerts.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs`
Expected: 73 passed (no test changes in this task).

Run: `pytest -q`
Expected: 90 passed.

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/alerts.js
git commit -m "feat(user): add alerts banner DOM module (collapse + mark-seen)"
```

---

### Task 4: Bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. The current top-of-file imports (after Phase 4b):

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
import { initAnnotations } from "./annotations.js";
import { isPrefsEmpty } from "./user-prefs-helpers.js";
import { api } from "./api.js";
```

Add a new import directly below `initAnnotations`:

```javascript
import { initAlerts } from "./alerts.js";
```

Find the `createStore({...})` call. The current shape (after Phase 4b) is:

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
    alerts: { items: [], last_open_at: null },
  });
```

Find the existing `api.watchlist.list().then(...)` block. Add a sibling fire-and-forget block directly below it for the alerts prefetch:

```javascript
  api.alerts
    .sinceLastOpen()
    .then((data) =>
      store.set({
        alerts: {
          items: data.items || [],
          last_open_at: data.last_open_at || null,
        },
      }),
    )
    .catch((err) => console.warn("[atlas] alerts prefetch failed", err));
```

Find the existing `initAnnotations({ root, store });` line and add the alerts init directly below it:

```javascript
  initAlerts({ root, store });
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/alerts/rules", '"yield_delta_abs"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/alerts/since-last-open", '"last_open_at"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 18 OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 5a 起）` and change to `## 路由布局（Phase 5b 起）`.

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉 + 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅（顶部展示自上次打开以来关注对象的变化，支持收起+标记已读）。
```

Leave the `/api/v2/*` row unchanged — Phase 5b doesn't add new endpoints.

- [ ] **Step 6: Verify all exit criteria**

Run each:
- `pytest -q` → 90 passed (no backend changes)
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs` → 73 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 18 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire alerts banner into bootstrap + smoke + docs"
```

---

## Phase 5b Exit Criteria

- [ ] `pytest -q` — 90 passed (no backend changes)
- [ ] `node --test ...` — 73 passed (5 state + 20 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers + 4 watchlist helpers + 5 annotations helpers + 8 alerts helpers)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check` — exit 0 each
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 18 rows OK
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, add a watchlist entry and POST a stale baseline to alerts_state.json. Reload page. Banner appears at top with `N 条变化` count + 自上次打开 timestamp. Click 展开 → list of changes shown with target_ids + formatted lines (e.g. `租售比 1.00% → 2.99% (+1.99)`); colors from severity (`up`/`down`/`warn`). Click 标记已读 → banner hides; refresh → banner stays gone.
- [ ] `git log --oneline fcf17c4..HEAD` shows exactly 4 commits

## Out of Scope (deferred)

- Target name resolution — banner shows raw target_id; Phase 6 polish for joining names
- Banner collapse persistence in localStorage — re-renders fresh on each load
- Topbar 变化计数 chip (separate from the banner) — Phase 6
- Editing alert rules from the UI — Phase 6 (extend 偏好 modal)
- Alerts for non-watchlist targets — out of scope
- Manual browser screenshot
