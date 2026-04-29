# Phase 3a — Detail Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a building polygon is clicked or a board row is clicked, slide in a right-side drawer over the board column showing a mode-aware KPI bar, a 3-bucket floor distribution SVG, and a listing-summary panel sourced from `/api/v2/buildings/{id}` (or `/api/v2/communities/{id}` if the selection is a community).

**Architecture:** Pure frontend addition. A new `frontend/user/modules/detail-drawer.js` subscribes to `state.selection` from the existing pub/sub store; on non-null selection it fetches detail via the `api` client and renders into a fixed mount in `index.html`. Pure data-shaping helpers live in `frontend/user/modules/drawer-data.js` so they can be exercised by `node:test` without a DOM. CSS slides the drawer in over the board column with a backdrop. **Listings list** (per spec section 5) is implemented as a sale/rent **summary panel** because the staged/mock backend exposes `saleMedianWan` / `rentMedianMonthly` / `sampleSize` aggregates rather than per-listing rows — when the listings endpoint exists in a later phase, the panel can be expanded.

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for `drawer-data.js` · CSS variables (D1 tokens already present) · existing `/api/v2/buildings/{id}` and `/api/v2/communities/{id}` endpoints. No new deps.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (Phase 3 — section 7; section 5 page-skeleton row 5 "楼栋透视抽屉")

**Prior plan:** `docs/superpowers/plans/2026-04-24-phase-2b-frontend-map-board.md` (merged at `3acc392`)

---

## File Structure (Phase 3a outcome)

```
frontend/user/
├── index.html                       # MODIFIED: add drawer container after <main>
├── styles/
│   └── drawer.css                   # NEW
└── modules/
    ├── drawer-data.js               # NEW — pure helpers (KPI per mode, bucket bars, formatters)
    ├── detail-drawer.js             # NEW — DOM module (subscribe + fetch + render + close)
    └── main.js                      # MODIFIED: import + initDrawer in bootstrap

tests/frontend/
└── test_drawer_data.mjs             # NEW (~7 cases)

scripts/phase1_smoke.py              # MODIFIED: +1 substring assertion for the drawer mount
README.md                            # MODIFIED: bump Phase 2b → Phase 3a section header
```

**Out-of-scope (deferred):**
- Notes / annotations area inside the drawer (Phase 4)
- ★ watchlist button (Phase 4)
- Per-listing row breakdown — needs a new backend endpoint, deferred until that data layer exists
- Filter chip behavior (Phase 3b)
- Home onboarding modal (Phase 3b)
- City district aggregate map color band (Phase 3b)

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-3a-drawer .worktrees/phase-3a-drawer
cd .worktrees/phase-3a-drawer
```

- [ ] **Verify baseline**

```bash
pytest -q                                                 # expect: 20 passed
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs   # expect: 12 passed
python3 scripts/phase1_smoke.py                            # expect: 9 routes OK
```

If any baseline check fails, stop — Phase 2b should be merged cleanly first.

---

### Task 1: drawer-data.js — pure helpers + tests

**Files:**
- Create: `frontend/user/modules/drawer-data.js`
- Create: `tests/frontend/test_drawer_data.mjs`

- [ ] **Step 1: Write the failing tests**

Write `tests/frontend/test_drawer_data.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  formatPct,
  formatWan,
  formatYuan,
  normalizeYieldPct,
  bucketBars,
  pickKpisFor,
} from "../../frontend/user/modules/drawer-data.js";

test("formatPct: null/undefined/NaN → —", () => {
  assert.equal(formatPct(null), "—");
  assert.equal(formatPct(undefined), "—");
  assert.equal(formatPct(Number.NaN), "—");
});

test("formatPct: 4.16 → '4.16%'", () => {
  assert.equal(formatPct(4.16), "4.16%");
});

test("formatWan: 306.85 → '306.85 万'", () => {
  assert.equal(formatWan(306.85), "306.85 万");
  assert.equal(formatWan(null), "—");
});

test("formatYuan: 12900 → '¥12,900'", () => {
  assert.equal(formatYuan(12900), "¥12,900");
  assert.equal(formatYuan(null), "—");
});

test("normalizeYieldPct: < 1 treated as fraction → ×100", () => {
  assert.equal(normalizeYieldPct(0.04), 4);
  assert.equal(normalizeYieldPct(4.16), 4.16);
  assert.equal(normalizeYieldPct(null), null);
});

test("bucketBars: returns 3 entries with label/value/pct", () => {
  const bars = bucketBars({ low: 3.2, mid: 4.5, high: 5.1 });
  assert.equal(bars.length, 3);
  assert.deepEqual(bars.map((b) => b.label), ["低层", "中层", "高层"]);
  assert.equal(bars[2].value, 5.1);
  // pct is value relative to the max in the set, scaled 0-100
  assert.equal(bars[2].pct, 100);
  assert.ok(bars[0].pct < bars[2].pct);
});

test("bucketBars: handles all-zero/empty without dividing by zero", () => {
  const bars = bucketBars({ low: 0, mid: 0, high: 0 });
  assert.equal(bars.length, 3);
  assert.equal(bars[0].pct, 0);
  assert.equal(bars[1].pct, 0);
  assert.equal(bars[2].pct, 0);
});

test("pickKpisFor: yield mode focuses on yield/score/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("yield", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
  assert.equal(kpis[0].value, "4.00%");
});

test("pickKpisFor: home mode focuses on price/rent/sample", () => {
  const detail = {
    yieldAvg: 0.04,
    score: 66,
    sampleSize: 13,
    saleMedianWan: 306.85,
    rentMedianMonthly: 12900,
  };
  const kpis = pickKpisFor("home", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["price", "rent", "sample"]);
  assert.equal(kpis[0].value, "306.85 万");
  assert.equal(kpis[1].value, "¥12,900");
});

test("pickKpisFor: city mode focuses on yield/score/sample (community-level KPI labels)", () => {
  const detail = { yield: 4.16, score: 99, sample: 16 };
  const kpis = pickKpisFor("city", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
  assert.equal(kpis[0].value, "4.16%");
});

test("pickKpisFor: unknown mode falls back to yield mode kpis", () => {
  const detail = { yieldAvg: 0.04, score: 66, sampleSize: 13 };
  const kpis = pickKpisFor("nonsense", detail);
  assert.deepEqual(kpis.map((k) => k.key), ["yield", "score", "sample"]);
});
```

- [ ] **Step 2: Verify it fails**

Run: `node --test tests/frontend/test_drawer_data.mjs`
Expected: ERR_MODULE_NOT_FOUND for `drawer-data.js`.

- [ ] **Step 3: Implement `drawer-data.js`**

Write `frontend/user/modules/drawer-data.js`:

```javascript
export function normalizeYieldPct(raw) {
  if (raw === null || raw === undefined) return null;
  const value = Number(raw);
  if (Number.isNaN(value)) return null;
  // Backend exposes yield either as a percentage (4.16) or a fraction (0.04).
  return value < 1 ? value * 100 : value;
}

export function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Number(value).toFixed(2)}%`;
}

export function formatWan(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${Number(value).toFixed(2)} 万`;
}

export function formatYuan(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const rounded = Math.round(Number(value));
  return `¥${rounded.toLocaleString("en-US")}`;
}

export function formatInt(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return String(Math.round(Number(value)));
}

export function bucketBars({ low = 0, mid = 0, high = 0 } = {}) {
  const values = [
    { key: "low", label: "低层", value: Number(low) || 0 },
    { key: "mid", label: "中层", value: Number(mid) || 0 },
    { key: "high", label: "高层", value: Number(high) || 0 },
  ];
  const max = Math.max(...values.map((v) => v.value));
  return values.map((v) => ({
    ...v,
    pct: max > 0 ? Math.round((v.value / max) * 100) : 0,
  }));
}

export function pickKpisFor(modeId, detail) {
  const kpis = KPI_MAP[modeId] || KPI_MAP.yield;
  return kpis(detail);
}

const KPI_MAP = {
  yield: (d) => [
    { key: "yield", label: "租售比", value: formatPct(normalizeYieldPct(d.yieldAvg)) },
    { key: "score", label: "机会分", value: formatInt(d.score) },
    { key: "sample", label: "样本量", value: formatInt(d.sampleSize) },
  ],
  home: (d) => [
    { key: "price", label: "中位总价", value: formatWan(d.saleMedianWan) },
    { key: "rent", label: "中位月租", value: formatYuan(d.rentMedianMonthly) },
    { key: "sample", label: "样本量", value: formatInt(d.sampleSize) },
  ],
  city: (d) => [
    { key: "yield", label: "均租售比", value: formatPct(normalizeYieldPct(d.yield ?? d.yieldAvg)) },
    { key: "score", label: "均机会分", value: formatInt(d.score) },
    { key: "sample", label: "样本量", value: formatInt(d.sample ?? d.sampleSize) },
  ],
};
```

- [ ] **Step 4: Verify it passes**

Run: `node --test tests/frontend/test_drawer_data.mjs`
Expected: 11 tests passed.

Run: `node --check frontend/user/modules/drawer-data.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/drawer-data.js tests/frontend/test_drawer_data.mjs
git commit -m "feat(user): add drawer pure helpers (formatters + bucket bars + KPI table)"
```

---

### Task 2: drawer.css + index.html mount

**Files:**
- Create: `frontend/user/styles/drawer.css`
- Modify: `frontend/user/index.html`

- [ ] **Step 1: Write `frontend/user/styles/drawer.css`**

```css
.atlas-drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: min(420px, 100%);
  background: var(--bg-1);
  border-left: 1px solid var(--line);
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.45);
  transform: translateX(100%);
  transition: transform 180ms ease;
  z-index: 5;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.atlas-drawer[data-open="true"] {
  transform: translateX(0);
}

.atlas-drawer-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(7, 10, 16, 0.45);
  opacity: 0;
  pointer-events: none;
  transition: opacity 180ms ease;
  z-index: 4;
}

.atlas-drawer-backdrop[data-open="true"] {
  opacity: 1;
  pointer-events: auto;
}

.atlas-drawer-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
  gap: 10px;
}

.atlas-drawer-title {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-0);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atlas-drawer-subtitle {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.atlas-drawer-close {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  font: inherit;
  font-size: 11px;
  width: 22px;
  height: 22px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  line-height: 1;
}

.atlas-drawer-close:hover {
  color: var(--text-0);
  border-color: var(--up);
}

.atlas-drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.atlas-drawer-status {
  font-size: 11px;
  color: var(--text-dim);
  padding: 4px 0;
}

.atlas-drawer-status[data-state="error"] {
  color: var(--down);
}

.atlas-kpi-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
}

.atlas-kpi {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.atlas-kpi-label {
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-xs);
}

.atlas-kpi-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 14px;
  color: var(--text-0);
}

.atlas-section-title {
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin: 4px 0 0;
}

.atlas-bucket-chart {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  height: 80px;
  padding: 6px 4px 0;
  border-bottom: 1px solid var(--line);
}

.atlas-bucket-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.atlas-bucket-bar {
  width: 100%;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-bottom: none;
  position: relative;
}

.atlas-bucket-bar > span {
  position: absolute;
  inset: 0;
  background: var(--up);
  opacity: 0.7;
}

.atlas-bucket-label {
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--text-dim);
}

.atlas-bucket-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  color: var(--text-0);
}

.atlas-listing-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.atlas-listing-cell {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.atlas-listing-cell .atlas-kpi-value {
  font-size: 13px;
}

.atlas-listing-cell .atlas-kpi-label {
  letter-spacing: 0.06em;
}

.atlas-drawer-empty {
  color: var(--text-dim);
  font-size: 11px;
  padding: 24px 0;
  text-align: center;
}
```

- [ ] **Step 2: Add a stylesheet link + drawer mount to `frontend/user/index.html`**

Open `frontend/user/index.html`. Add this stylesheet line directly after the existing `board.css` link:

```html
    <link rel="stylesheet" href="/styles/drawer.css" />
```

Then, directly after the closing `</main>` tag and before the `<footer ...>` tag, insert these two elements:

```html
      <div class="atlas-drawer-backdrop" data-component="drawer-backdrop" data-open="false"></div>
      <aside class="atlas-drawer" data-component="drawer" data-open="false" aria-hidden="true">
        <header class="atlas-drawer-header">
          <div>
            <h2 class="atlas-drawer-title" data-role="drawer-title">—</h2>
            <span class="atlas-drawer-subtitle mono" data-role="drawer-subtitle">—</span>
          </div>
          <button type="button" class="atlas-drawer-close" data-role="drawer-close" aria-label="关闭">×</button>
        </header>
        <div class="atlas-drawer-body" data-role="drawer-body">
          <div class="atlas-drawer-empty">选择楼栋或机会榜条目以查看详情</div>
        </div>
      </aside>
```

The drawer is positioned `absolute` inside `.atlas-shell`, so the existing layout grid does not need to change.

- [ ] **Step 3: Sanity-check**

Run: `node --check frontend/user/modules/main.js` (still untouched in this task — should still parse) — exit 0.

Run: `grep -c 'data-component="drawer"' frontend/user/index.html` → 1.

Run: `grep -c 'href="/styles/drawer.css"' frontend/user/index.html` → 1.

Run: `pytest -q` — 20 passed.

- [ ] **Step 4: Commit**

```bash
git add frontend/user/index.html frontend/user/styles/drawer.css
git commit -m "feat(user): add drawer mount + slide-in css"
```

---

### Task 3: detail-drawer.js — DOM module

**Files:**
- Create: `frontend/user/modules/detail-drawer.js`

- [ ] **Step 1: Implement `detail-drawer.js`**

Write `frontend/user/modules/detail-drawer.js`:

```javascript
import { api } from "./api.js";
import { bucketBars, formatWan, formatYuan, pickKpisFor } from "./drawer-data.js";

export function initDrawer({ root, store }) {
  const drawer = root.querySelector('[data-component="drawer"]');
  const backdrop = root.querySelector('[data-component="drawer-backdrop"]');
  const titleEl = drawer.querySelector('[data-role="drawer-title"]');
  const subtitleEl = drawer.querySelector('[data-role="drawer-subtitle"]');
  const bodyEl = drawer.querySelector('[data-role="drawer-body"]');
  const closeButton = drawer.querySelector('[data-role="drawer-close"]');

  let activeRequestId = 0;
  let lastSelectionId = null;
  let lastMode = null;

  closeButton.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.dataset.open === "true") {
      close();
    }
  });

  store.subscribe(handleStateChange);
  handleStateChange(store.get());

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
    const id = `${sel.type}:${sel.id}`;
    if (id === lastSelectionId) {
      // Same selection — only act if mode actually changed.
      if (state.mode !== lastMode) {
        lastMode = state.mode;
        renderKpisForCurrent(state.mode);
      }
      return;
    }
    lastSelectionId = id;
    lastMode = state.mode;
    const myRequestId = ++activeRequestId;
    open();
    renderLoading(sel);
    fetchDetail(sel)
      .then((detail) => {
        if (myRequestId !== activeRequestId) return; // a newer selection won
        renderDetail({ sel, detail, mode: state.mode });
      })
      .catch((err) => {
        if (myRequestId !== activeRequestId) return;
        renderError(err.message || "详情加载失败");
      });
  }

  function close() {
    store.set({ selection: null });
    renderClosed();
    lastSelectionId = null;
  }

  function open() {
    drawer.dataset.open = "true";
    backdrop.dataset.open = "true";
    drawer.setAttribute("aria-hidden", "false");
  }

  function renderClosed() {
    drawer.dataset.open = "false";
    backdrop.dataset.open = "false";
    drawer.setAttribute("aria-hidden", "true");
    titleEl.textContent = "—";
    subtitleEl.textContent = "—";
    bodyEl.innerHTML = '<div class="atlas-drawer-empty">选择楼栋或机会榜条目以查看详情</div>';
  }

  function renderLoading(sel) {
    titleEl.textContent = sel.props?.name || sel.props?.communityName || sel.id;
    subtitleEl.textContent = (sel.type || "").toUpperCase();
    bodyEl.innerHTML = '<div class="atlas-drawer-status">加载详情中…</div>';
  }

  function renderError(message) {
    bodyEl.innerHTML = `<div class="atlas-drawer-status" data-state="error">${escapeText(message)}</div>`;
  }

  function renderDetail({ sel, detail, mode }) {
    titleEl.textContent = detail.name || sel.props?.name || sel.id;
    subtitleEl.textContent = (detail.districtName || sel.props?.districtName || "").toString();
    bodyEl.innerHTML = renderBody({ detail, mode });
    bodyEl.dataset.detailJson = JSON.stringify({
      yieldAvg: detail.yieldAvg,
      score: detail.score,
      sampleSize: detail.sampleSize ?? detail.sample,
      saleMedianWan: detail.saleMedianWan ?? detail.avgPriceWan,
      rentMedianMonthly: detail.rentMedianMonthly ?? detail.monthlyRent,
      yield: detail.yield,
      sample: detail.sample,
    });
  }

  function renderKpisForCurrent(mode) {
    if (!bodyEl.dataset.detailJson) return;
    const cached = JSON.parse(bodyEl.dataset.detailJson);
    const kpiHtml = renderKpiRow(pickKpisFor(mode, cached));
    const kpiContainer = bodyEl.querySelector('[data-role="kpi-row"]');
    if (kpiContainer) {
      kpiContainer.outerHTML = kpiHtml;
    }
  }

  function renderBody({ detail, mode }) {
    const kpis = pickKpisFor(mode, detail);
    const bars = bucketBars({
      low: detail.low ?? 0,
      mid: detail.mid ?? 0,
      high: detail.high ?? 0,
    });
    return [
      renderKpiRow(kpis),
      renderFloorChart(bars),
      renderListingSummary(detail),
    ].join("");
  }

  function renderKpiRow(kpis) {
    const cells = kpis
      .map(
        (k) => `<div class="atlas-kpi"><span class="atlas-kpi-label">${escapeText(k.label)}</span><span class="atlas-kpi-value">${escapeText(k.value)}</span></div>`,
      )
      .join("");
    return `<div class="atlas-kpi-row" data-role="kpi-row">${cells}</div>`;
  }

  function renderFloorChart(bars) {
    const cols = bars
      .map(
        (b) =>
          `<div class="atlas-bucket-col"><span class="atlas-bucket-value">${escapeText(formatBucketValue(b.value))}</span><div class="atlas-bucket-bar" style="height: ${b.pct}%"><span></span></div><span class="atlas-bucket-label">${escapeText(b.label)}</span></div>`,
      )
      .join("");
    return `<div><h3 class="atlas-section-title">楼层段租售比</h3><div class="atlas-bucket-chart">${cols}</div></div>`;
  }

  function renderListingSummary(detail) {
    const sale = detail.saleMedianWan ?? detail.avgPriceWan;
    const rent = detail.rentMedianMonthly ?? detail.monthlyRent;
    const cells = [
      { label: "中位总价", value: formatWan(sale) },
      { label: "中位月租", value: formatYuan(rent) },
    ]
      .map(
        (c) =>
          `<div class="atlas-listing-cell"><span class="atlas-kpi-label">${escapeText(c.label)}</span><span class="atlas-kpi-value">${escapeText(c.value)}</span></div>`,
      )
      .join("");
    return `<div><h3 class="atlas-section-title">挂牌摘要</h3><div class="atlas-listing-summary">${cells}</div></div>`;
  }

  async function fetchDetail(sel) {
    if (sel.type === "building") {
      return getJSON(`/api/v2/buildings/${encodeURIComponent(sel.id)}`);
    }
    if (sel.type === "community") {
      // Prefer the building behind a community row for richer KPI/floor data.
      const buildingId = sel.primaryBuildingId || sel.props?.primaryBuildingId;
      if (buildingId) {
        return getJSON(`/api/v2/buildings/${encodeURIComponent(buildingId)}`);
      }
      return getJSON(`/api/v2/communities/${encodeURIComponent(sel.id)}`);
    }
    throw new Error(`未知的选中类型：${sel.type}`);
  }
}

async function getJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API ${url} → ${response.status}`);
  }
  return response.json();
}

function formatBucketValue(value) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const num = Number(value);
  if (num === 0) return "0";
  return num >= 1 ? num.toFixed(2) : (num * 100).toFixed(2);
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

- [ ] **Step 2: Verify**

Run: `node --check frontend/user/modules/detail-drawer.js`
Expected: exit 0.

Run: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs`
Expected: 23 tests passed (5 + 7 + 11).

- [ ] **Step 3: Commit**

```bash
git add frontend/user/modules/detail-drawer.js
git commit -m "feat(user): add detail drawer (subscribe → fetch → render → close)"
```

---

### Task 4: Wire bootstrap + smoke + README

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open `frontend/user/modules/main.js`. Find:

```javascript
import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
```

Append the drawer import directly after the board import:

```javascript
import { initDrawer } from "./detail-drawer.js";
```

Then, inside `bootstrap`, find the existing `Promise.all([...])` block. Add `initDrawer({ root, store })` BEFORE the `Promise.all`. The drawer is synchronous (no fetch on init) and only reacts to selection changes, so it should be wired before the parallel boot to ensure it catches a `?building=` style URL state if one is later added.

The relevant section should now look like:

```javascript
  initShell({ root, store });
  initDrawer({ root, store });

  const mapContainer = root.querySelector('[data-component="map"]');
  const boardContainer = root.querySelector('[data-component="board"]');

  // Map and board boot in parallel — they only talk via the store.
  await Promise.all([
    initMap({ container: mapContainer, store }),
    initBoard({ container: boardContainer, store }),
  ]);
```

- [ ] **Step 2: Verify the module compiles**

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

- [ ] **Step 3: Extend `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/", 'data-component="mode-chips"'),
```

Add directly below it:

```python
            (f"{base}/", 'data-component="drawer"'),
```

- [ ] **Step 4: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 10 rows OK, exit 0.

- [ ] **Step 5: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 2b 起）` and change it to `## 路由布局（Phase 3a 起）`.

Then find the row whose third column starts with `用户平台。收益模式端到端`. Replace its description with:

```markdown
用户平台。收益模式端到端 + 详情抽屉（点击楼栋/榜单条目滑入：KPI 条 + 楼层段租售比 + 挂牌摘要）。Home/City 模式 chip 已启用，全模式支持见 Phase 3b。
```

- [ ] **Step 6: Verify exit criteria**

Run each:
- `pytest -q` → 20 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs` → 23 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 10 OK
- `node --check frontend/user/modules/main.js` → exit 0
- `node --check frontend/backstage/app.js` → exit 0 (regression guard)

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/main.js scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire detail drawer in bootstrap + extend smoke + docs"
```

---

## Phase 3a Exit Criteria

- [ ] `pytest -q` — 20 passed (no backend change in this phase)
- [ ] `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs` — 23 passed (5 + 7 + 11)
- [ ] Each new JS file passes `node --check`: `state.js api.js runtime.js modes.js map.js opportunity-board.js shell.js detail-drawer.js drawer-data.js main.js`
- [ ] `node --check frontend/backstage/app.js` — exit 0 (regression guard)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 10 rows OK
- [ ] Manual: open `http://127.0.0.1:8013/?mode=yield`, click a board row → drawer slides in from the right with title, district subtitle, three KPI cards, three floor-bucket bars, and a 2-cell listing summary
- [ ] Manual: click the X button → drawer slides out, board column visible again
- [ ] Manual: click a board row → drawer opens; press Esc → drawer closes
- [ ] Manual: click a board row → drawer opens; click another row → drawer re-renders with new content (not double-stacked)
- [ ] Manual: switch from yield → home mode while drawer is open → KPI row updates without re-fetching
- [ ] `git log --oneline 3acc392..HEAD` shows exactly 4 commits

## Out of Scope (deferred to Phase 3b and later)

- Notes / annotations area (Phase 4)
- ★ watchlist button (Phase 4)
- Per-listing row breakdown (needs new backend endpoint)
- Filter chip behavior + per-mode filter persistence (Phase 3b)
- Home onboarding modal (Phase 3b)
- City district aggregate map color band (Phase 3b)
- Map → drawer → board cross-highlighting beyond what already exists from selection state
