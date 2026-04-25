# Phase 3c-2 — Home Onboarding Modal + Home Mode Wire-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Light up Home mode end-to-end. On first entry into the Home chip, a one-time onboarding modal collects budget / districts / area, persists via `PATCH /api/v2/user/prefs` (Phase 3c-1), and the modal closes. Subsequent visits skip the modal and use the stored prefs to drive Home-mode default filters (`max_budget` from `budget_max_wan`, `district` from the first selected district). The onboarding can be re-opened from the topbar via a "偏好" button.

**Architecture:** Pure frontend addition with one tiny backend gloss (`/api/v2/map/districts` is already shipped and provides the dropdown source). A new `home-onboarding.js` is a focused DOM module that subscribes to `state.userPrefs` + `state.mode`; when `mode === "home"` and `prefs` is "empty" it shows. A new `user-prefs.js` API namespace wraps GET/PATCH and a small bootstrap function rehydrates `state.userPrefs` at app start. `modes.js` learns a `resolveDefaultFilters(modeId, userPrefs)` that derives Home defaults dynamically from prefs (so an onboarded user sees their budget/district as filter chips immediately). Home mode flips to `enabled: true`. The "偏好" topbar button dispatches a custom store flag `state.onboardingOpen = true` to re-open the modal regardless of mode.

**Tech Stack:** Vanilla JS (browser-native ES modules) · `node:test` for the new pure helpers · existing `/api/v2/user/prefs` endpoints (Phase 3c-1) · existing `/api/v2/map/districts` for the dropdown. No new deps.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 "自住模式首次引导" + section 5 三模式语义 row "默认筛选 home: 必填预算 + 区域 + 面积")

**Prior plans:** 2026-04-24-phase-3c-1-user-prefs-backend.md (merged at `6f6ce11`)

---

## File Structure (Phase 3c-2 outcome)

```
frontend/user/
├── index.html                         # MODIFIED: add onboarding modal mount + topbar 偏好 button
├── styles/
│   ├── shell.css                      # MODIFIED: 偏好 button styling
│   └── onboarding.css                 # NEW
└── modules/
    ├── api.js                         # MODIFIED: add userPrefs.get + userPrefs.patch + districtsAll
    ├── modes.js                       # MODIFIED: add resolveDefaultFilters + home enabled=true
    ├── home-onboarding.js             # NEW — modal DOM + form + submit
    ├── shell.js                       # MODIFIED: wire 偏好 button + open modal via store
    ├── opportunity-board.js           # MODIFIED: replace defaultSort/Filters lookup with resolved per-state
    └── main.js                        # MODIFIED: rehydrate userPrefs at boot + initOnboarding wiring

tests/frontend/
├── test_modes.mjs                     # MODIFIED: extend with resolveDefaultFilters cases
└── test_user_prefs_helpers.mjs        # NEW (~5 cases — emptiness check + resolver edge cases)

scripts/phase1_smoke.py                # MODIFIED: +1 substring assertion for onboarding modal mount
README.md                              # MODIFIED: bump Phase 3c-1 → Phase 3c-2
```

**Out-of-scope (deferred):**
- Cross-field validators (budget_min ≤ budget_max etc.) — Phase 3c-3 polish
- Multi-district `/api/v2/opportunities` — needs v2 contract change; Phase 3c-3 if desired
- Area filter wired to API — `/api/v2/opportunities` does not accept an area param; the form collects + persists area but does not push it to API filtering. Documented in Out-of-Scope below.
- City mode district color band — Phase 3d
- Office anchor (commute calc) — Phase 6

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-3c-2-home-onboarding .worktrees/phase-3c-2-home-onboarding
cd .worktrees/phase-3c-2-home-onboarding
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 40 pytest passed; 38 node tests passed; 12 smoke routes OK. If any check fails, stop — Phase 3c-1 should be merged cleanly first.

---

### Task 1: API client extension + user-prefs helpers

**Files:**
- Modify: `frontend/user/modules/api.js`
- Create: `frontend/user/modules/user-prefs-helpers.js`
- Create: `tests/frontend/test_user_prefs_helpers.mjs`

We add three things:
1. `api.userPrefs.get()` — calls `GET /api/v2/user/prefs` (uncached — values can change at runtime)
2. `api.userPrefs.patch(payload)` — calls `PATCH /api/v2/user/prefs`
3. `api.districtsAll()` — calls `GET /api/v2/map/districts` (cached) for the dropdown

Plus a tiny pure helper module `user-prefs-helpers.js` with `isPrefsEmpty(prefs)` (used to decide whether to auto-open the onboarding modal).

- [ ] **Step 1: Write failing tests for the helper**

Write `tests/frontend/test_user_prefs_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

import { isPrefsEmpty } from "../../frontend/user/modules/user-prefs-helpers.js";

test("isPrefsEmpty: null prefs is empty", () => {
  assert.equal(isPrefsEmpty(null), true);
  assert.equal(isPrefsEmpty(undefined), true);
});

test("isPrefsEmpty: fresh defaults shape is empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: [],
    area_min_sqm: null,
    area_max_sqm: null,
    office_anchor: null,
    updated_at: null,
  };
  assert.equal(isPrefsEmpty(prefs), true);
});

test("isPrefsEmpty: budget_max_wan set is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: 1500,
    districts: [],
    area_min_sqm: null,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});

test("isPrefsEmpty: districts populated is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: ["pudong"],
    area_min_sqm: null,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});

test("isPrefsEmpty: area set is non-empty", () => {
  const prefs = {
    budget_min_wan: null,
    budget_max_wan: null,
    districts: [],
    area_min_sqm: 60,
    area_max_sqm: null,
  };
  assert.equal(isPrefsEmpty(prefs), false);
});
```

- [ ] **Step 2: Verify tests fail**

Run: `node --test tests/frontend/test_user_prefs_helpers.mjs`
Expected: ERR_MODULE_NOT_FOUND.

- [ ] **Step 3: Implement the helper**

Write `frontend/user/modules/user-prefs-helpers.js`:

```javascript
const SIGNAL_KEYS = ["budget_min_wan", "budget_max_wan", "area_min_sqm", "area_max_sqm"];

export function isPrefsEmpty(prefs) {
  if (!prefs || typeof prefs !== "object") return true;
  for (const key of SIGNAL_KEYS) {
    const value = prefs[key];
    if (value !== null && value !== undefined && value !== "") return false;
  }
  const districts = prefs.districts;
  if (Array.isArray(districts) && districts.length > 0) return false;
  return true;
}
```

- [ ] **Step 4: Run the helper tests**

Run: `node --test tests/frontend/test_user_prefs_helpers.mjs`
Expected: 5 tests passed.

Run: `node --check frontend/user/modules/user-prefs-helpers.js`
Expected: exit 0.

- [ ] **Step 5: Extend `frontend/user/modules/api.js`**

Open `frontend/user/modules/api.js`. Find the existing `export const api = { ... }` block. The current shape is:

```javascript
export const api = {
  opportunities: (params) => getJSON(`/api/v2/opportunities${buildQuery(params)}`),
  mapBuildings: (params) => getJSON(`/api/v2/map/buildings${buildQuery(params)}`),
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  runtimeConfig: () => getJSON("/api/runtime-config"),
  invalidate,
};
```

Replace it with:

```javascript
async function getJSONFresh(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`API ${url} → ${response.status}`);
  return response.json();
}

async function patchJSON(url, payload) {
  const response = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API ${url} → ${response.status} ${text}`);
  }
  return response.json();
}

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

The existing `getJSON` (cache-backed) is unchanged. We add `getJSONFresh` for the prefs round-trip because the user can mutate them at runtime — caching would surface stale data. We also add `patchJSON` for the modal submission.

- [ ] **Step 6: Sanity-check api.js**

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add frontend/user/modules/user-prefs-helpers.js frontend/user/modules/api.js tests/frontend/test_user_prefs_helpers.mjs
git commit -m "feat(user): add user-prefs API client + emptiness helper"
```

---

### Task 2: modes.js — resolveDefaultFilters + home enabled=true

**Files:**
- Modify: `frontend/user/modules/modes.js`
- Modify: `tests/frontend/test_modes.mjs`

Today `MODES.find(home).defaultFilters` is `{}` — Home mode is `enabled: false`. We flip it to `enabled: true` and add a new exported function `resolveDefaultFilters(modeId, userPrefs)` that returns:
- yield → static `{minYield: 4, maxBudget: 1500}` (unchanged)
- home → `{maxBudget: prefs.budget_max_wan, district: prefs.districts[0] || undefined}` (only sets keys when prefs are present)
- city → `{}`

Note: `district` is a NEW filter key added in this task. We extend `FILTER_KEY_MAP` to include `district → district` and `FILTER_LABELS` to map it to a Chinese chip. The `prunedFilters` API-default for `district` should be `"all"` (the API's default).

- [ ] **Step 1: Add tests for the new resolver**

Open `tests/frontend/test_modes.mjs`. Find the existing import line:

```javascript
import { MODES, getMode, yieldColorFor, defaultFiltersFor } from "../../frontend/user/modules/modes.js";
```

Replace it with:

```javascript
import {
  MODES,
  getMode,
  yieldColorFor,
  defaultFiltersFor,
  resolveDefaultFilters,
} from "../../frontend/user/modules/modes.js";
```

At the end of the file, append:

```javascript
test("resolveDefaultFilters: yield mode static defaults", () => {
  assert.deepEqual(resolveDefaultFilters("yield", null), { minYield: 4, maxBudget: 1500 });
});

test("resolveDefaultFilters: home with empty prefs returns empty", () => {
  assert.deepEqual(resolveDefaultFilters("home", null), {});
  assert.deepEqual(resolveDefaultFilters("home", {}), {});
  assert.deepEqual(resolveDefaultFilters("home", { budget_max_wan: null, districts: [] }), {});
});

test("resolveDefaultFilters: home with budget pulls maxBudget", () => {
  assert.deepEqual(
    resolveDefaultFilters("home", { budget_max_wan: 1200, districts: [] }),
    { maxBudget: 1200 },
  );
});

test("resolveDefaultFilters: home with districts uses first district", () => {
  assert.deepEqual(
    resolveDefaultFilters("home", { budget_max_wan: 1200, districts: ["pudong", "jingan"] }),
    { maxBudget: 1200, district: "pudong" },
  );
});

test("resolveDefaultFilters: city mode is empty regardless of prefs", () => {
  assert.deepEqual(resolveDefaultFilters("city", { budget_max_wan: 1200 }), {});
});

test("MODES: home mode is now enabled", () => {
  assert.equal(getMode("home").enabled, true);
});
```

Also extend the existing tests for the new `district` filter key. Find:

```javascript
test("filtersToApiParams: yield filters → snake_case params", () => {
  const params = filtersToApiParams({ minYield: 4, maxBudget: 1500 });
  assert.deepEqual(params, { min_yield: 4, max_budget: 1500 });
});
```

Add this new test directly below it (in `tests/frontend/test_filter_helpers.mjs`, NOT in test_modes.mjs):

```javascript
test("filtersToApiParams: district key passes through as 'district'", () => {
  const params = filtersToApiParams({ district: "pudong", maxBudget: 1500 });
  assert.deepEqual(params, { district: "pudong", max_budget: 1500 });
});
```

And one new test for `describeFilter` in `tests/frontend/test_filter_helpers.mjs`. Find:

```javascript
test("describeFilter: renders human-friendly chip labels", () => {
  assert.equal(describeFilter("minYield", 4), "租售比 ≥ 4%");
  assert.equal(describeFilter("maxBudget", 1500), "总价 ≤ 1500 万");
  assert.equal(describeFilter("minSamples", 2), "样本量 ≥ 2");
  assert.equal(describeFilter("minScore", 50), "机会分 ≥ 50");
});
```

Replace with:

```javascript
test("describeFilter: renders human-friendly chip labels", () => {
  assert.equal(describeFilter("minYield", 4), "租售比 ≥ 4%");
  assert.equal(describeFilter("maxBudget", 1500), "总价 ≤ 1500 万");
  assert.equal(describeFilter("minSamples", 2), "样本量 ≥ 2");
  assert.equal(describeFilter("minScore", 50), "机会分 ≥ 50");
  assert.equal(describeFilter("district", "pudong"), "区域 = pudong");
});
```

And one new test for `prunedFilters`:

```javascript
test("prunedFilters: drops district='all' (API default)", () => {
  const pruned = prunedFilters({ district: "all", maxBudget: 1500 });
  assert.deepEqual(pruned, { maxBudget: 1500 });
});
```

- [ ] **Step 2: Verify tests fail**

Run: `node --test tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs`
Expected: failures (`resolveDefaultFilters` undefined, district label missing, etc.).

- [ ] **Step 3: Update `frontend/user/modules/modes.js`**

Open the file. Find the `home` MODES entry:

```javascript
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
    defaultFilters: {},
    enabled: false,
  },
```

Change `enabled: false` to `enabled: true`.

Find `FILTER_KEY_MAP`:

```javascript
const FILTER_KEY_MAP = {
  minYield: "min_yield",
  maxBudget: "max_budget",
  minSamples: "min_samples",
  minScore: "min_score",
};
```

Replace with:

```javascript
const FILTER_KEY_MAP = {
  minYield: "min_yield",
  maxBudget: "max_budget",
  minSamples: "min_samples",
  minScore: "min_score",
  district: "district",
};
```

Find `FILTER_API_DEFAULTS`:

```javascript
const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
};
```

Replace with:

```javascript
const FILTER_API_DEFAULTS = {
  minYield: 0,
  maxBudget: 10000,
  minSamples: 0,
  minScore: 0,
  district: "all",
};
```

Find `FILTER_LABELS`:

```javascript
const FILTER_LABELS = {
  minYield: (v) => `租售比 ≥ ${v}%`,
  maxBudget: (v) => `总价 ≤ ${v} 万`,
  minSamples: (v) => `样本量 ≥ ${v}`,
  minScore: (v) => `机会分 ≥ ${v}`,
};
```

Replace with:

```javascript
const FILTER_LABELS = {
  minYield: (v) => `租售比 ≥ ${v}%`,
  maxBudget: (v) => `总价 ≤ ${v} 万`,
  minSamples: (v) => `样本量 ≥ ${v}`,
  minScore: (v) => `机会分 ≥ ${v}`,
  district: (v) => `区域 = ${v}`,
};
```

Update `prunedFilters` to also drop the new `district` default. Find:

```javascript
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

Replace with:

```javascript
export function prunedFilters(filters) {
  const out = {};
  for (const [key, value] of Object.entries(filters || {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Object.prototype.hasOwnProperty.call(FILTER_API_DEFAULTS, key)) {
      const apiDefault = FILTER_API_DEFAULTS[key];
      if (typeof apiDefault === "number" && Number(value) === apiDefault) continue;
      if (typeof apiDefault === "string" && value === apiDefault) continue;
    }
    out[key] = value;
  }
  return out;
}
```

Add a new export at the bottom of the file (after `prunedFilters`):

```javascript
export function resolveDefaultFilters(modeId, userPrefs) {
  if (modeId === "yield") {
    return { ...defaultFiltersFor("yield") };
  }
  if (modeId === "home") {
    const out = {};
    if (userPrefs && typeof userPrefs === "object") {
      const budget = userPrefs.budget_max_wan;
      if (budget !== null && budget !== undefined && budget !== "") {
        out.maxBudget = Number(budget);
      }
      const districts = userPrefs.districts;
      if (Array.isArray(districts) && districts.length > 0) {
        out.district = String(districts[0]);
      }
    }
    return out;
  }
  return {};
}
```

- [ ] **Step 4: Run the tests**

Run: `node --test tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs`
Expected: 12 (modes) + 9 (filter helpers) = 21 tests pass. (Existing 9 + 6 new modes; existing 7 + 2 new filter helpers.)

Run: `node --check frontend/user/modules/modes.js`
Expected: exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/modes.js tests/frontend/test_modes.mjs tests/frontend/test_filter_helpers.mjs
git commit -m "feat(user): home mode enabled + resolveDefaultFilters from prefs"
```

---

### Task 3: home-onboarding.js — modal DOM module

**Files:**
- Create: `frontend/user/modules/home-onboarding.js`
- Create: `frontend/user/styles/onboarding.css`
- Modify: `frontend/user/index.html`

The modal renders inside `<main class="atlas-main">` (same containment scope as the drawer) so it doesn't cover the topbar. It collects four numeric ranges plus a multi-select districts list. Submit button is disabled until at least `budget_max_wan` is filled (the spec says budget is mandatory).

The modal subscribes to two store keys:
1. `state.onboardingOpen` (bool) — explicitly toggled on by the topbar 偏好 button or by mode switching to home with empty prefs
2. `state.userPrefs` — when prefs change (e.g., post-PATCH), the modal hides itself

- [ ] **Step 1: Add modal markup + topbar 偏好 button to `frontend/user/index.html`**

Open the file. Find the topbar section:

```html
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
        <nav class="atlas-modes" data-component="mode-chips" aria-label="模式切换"></nav>
        <div class="atlas-topbar-spacer"></div>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
      </header>
```

Replace with:

```html
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
        <nav class="atlas-modes" data-component="mode-chips" aria-label="模式切换"></nav>
        <div class="atlas-topbar-spacer"></div>
        <button type="button" class="atlas-prefs-button" data-component="prefs-button">偏好</button>
        <span class="atlas-runtime-tag mono dim" data-component="runtime-tag"></span>
      </header>
```

Find the closing of `<aside class="atlas-drawer" ...>` block (it ends with `</aside>` followed by `</main>`). Insert the onboarding modal markup directly after the drawer's `</aside>` and before the `</main>` close:

```html
        <div class="atlas-onboarding-backdrop" data-component="onboarding-backdrop" data-open="false"></div>
        <section class="atlas-onboarding" data-component="onboarding" data-open="false" aria-hidden="true" aria-labelledby="atlas-onboarding-title">
          <header class="atlas-onboarding-header">
            <h2 id="atlas-onboarding-title" class="atlas-onboarding-title">自住找房 · 偏好设定</h2>
            <button type="button" class="atlas-onboarding-close" data-role="onboarding-close" aria-label="关闭">×</button>
          </header>
          <form class="atlas-onboarding-form" data-role="onboarding-form" novalidate>
            <fieldset class="atlas-onboarding-fieldset">
              <legend>预算（万元）<span class="atlas-onboarding-required">*</span></legend>
              <div class="atlas-onboarding-pair">
                <label>下限<input type="number" name="budget_min_wan" min="0" step="10" placeholder="0" /></label>
                <label>上限<input type="number" name="budget_max_wan" min="0" step="10" placeholder="必填" required /></label>
              </div>
            </fieldset>
            <fieldset class="atlas-onboarding-fieldset">
              <legend>优先区域</legend>
              <div class="atlas-onboarding-districts" data-role="onboarding-districts"></div>
            </fieldset>
            <fieldset class="atlas-onboarding-fieldset">
              <legend>面积（平米）</legend>
              <div class="atlas-onboarding-pair">
                <label>下限<input type="number" name="area_min_sqm" min="0" step="5" placeholder="0" /></label>
                <label>上限<input type="number" name="area_max_sqm" min="0" step="5" placeholder="无上限" /></label>
              </div>
            </fieldset>
            <footer class="atlas-onboarding-actions">
              <span class="atlas-onboarding-status mono dim" data-role="onboarding-status">填写后保存到 data/personal/user_prefs.json</span>
              <button type="submit" class="atlas-onboarding-submit" data-role="onboarding-submit" disabled>保存</button>
            </footer>
          </form>
        </section>
```

Also add the stylesheet link directly after the `drawer.css` link in the `<head>` (around line 12):

```html
    <link rel="stylesheet" href="/styles/onboarding.css" />
```

- [ ] **Step 2: Write `frontend/user/styles/onboarding.css`**

```css
.atlas-onboarding {
  position: absolute;
  inset: 32px 32px;
  margin: auto;
  width: min(440px, 100%);
  max-height: calc(100% - 64px);
  background: var(--bg-1);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55);
  z-index: 7;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(8px);
  pointer-events: none;
  transition: opacity 160ms ease, transform 160ms ease;
}

.atlas-onboarding[data-open="true"] {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}

.atlas-onboarding-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(7, 10, 16, 0.55);
  z-index: 6;
  opacity: 0;
  pointer-events: none;
  transition: opacity 160ms ease;
}

.atlas-onboarding-backdrop[data-open="true"] {
  opacity: 1;
  pointer-events: auto;
}

.atlas-onboarding-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
}

.atlas-onboarding-title {
  margin: 0;
  font-size: 13px;
  letter-spacing: 0.06em;
}

.atlas-onboarding-close {
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

.atlas-onboarding-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 16px;
  overflow-y: auto;
}

.atlas-onboarding-fieldset {
  border: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.atlas-onboarding-fieldset legend {
  padding: 0;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-dim);
}

.atlas-onboarding-required {
  color: var(--down);
  margin-left: 4px;
}

.atlas-onboarding-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.atlas-onboarding-pair label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 11px;
  color: var(--text-dim);
}

.atlas-onboarding-pair input {
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 6px 8px;
  color: var(--text-0);
  font: inherit;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.atlas-onboarding-pair input:focus {
  outline: 1px solid var(--up);
  outline-offset: 0;
}

.atlas-onboarding-districts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
}

.atlas-onboarding-district-chip {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-onboarding-district-chip[aria-pressed="true"] {
  color: var(--text-0);
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.08);
}

.atlas-onboarding-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--line);
}

.atlas-onboarding-status {
  font-size: 10px;
  letter-spacing: 0.06em;
}

.atlas-onboarding-status[data-state="error"] {
  color: var(--down);
}

.atlas-onboarding-submit {
  appearance: none;
  border: 1px solid var(--up);
  background: rgba(0, 214, 143, 0.1);
  color: var(--text-0);
  padding: 5px 14px;
  font: inherit;
  font-size: 11px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  letter-spacing: 0.08em;
}

.atlas-onboarding-submit[disabled] {
  opacity: 0.4;
  cursor: not-allowed;
}

.atlas-prefs-button {
  appearance: none;
  border: 1px solid var(--line);
  background: var(--bg-2);
  color: var(--text-dim);
  padding: 4px 10px;
  font: inherit;
  font-size: 11px;
  letter-spacing: 0.08em;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.atlas-prefs-button:hover {
  color: var(--text-0);
  border-color: var(--up);
}
```

- [ ] **Step 3: Implement `frontend/user/modules/home-onboarding.js`**

```javascript
import { api } from "./api.js";
import { resolveDefaultFilters } from "./modes.js";

export function initOnboarding({ root, store }) {
  const modal = root.querySelector('[data-component="onboarding"]');
  const backdrop = root.querySelector('[data-component="onboarding-backdrop"]');
  const closeBtn = modal.querySelector('[data-role="onboarding-close"]');
  const form = modal.querySelector('[data-role="onboarding-form"]');
  const submitBtn = modal.querySelector('[data-role="onboarding-submit"]');
  const statusEl = modal.querySelector('[data-role="onboarding-status"]');
  const districtsEl = modal.querySelector('[data-role="onboarding-districts"]');
  const inputs = {
    budget_min_wan: form.elements.namedItem("budget_min_wan"),
    budget_max_wan: form.elements.namedItem("budget_max_wan"),
    area_min_sqm: form.elements.namedItem("area_min_sqm"),
    area_max_sqm: form.elements.namedItem("area_max_sqm"),
  };

  let districtIds = [];
  let selectedDistricts = new Set();

  closeBtn.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.dataset.open === "true") {
      close();
    }
  });
  form.addEventListener("input", refreshSubmitState);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submit().catch((err) => showError(err.message || "保存失败"));
  });

  store.subscribe(handleStateChange);
  loadDistricts();
  handleStateChange(store.get());

  function handleStateChange(state) {
    if (state.onboardingOpen) {
      open(state.userPrefs);
    } else {
      close();
    }
  }

  function open(prefs) {
    seedForm(prefs || {});
    modal.dataset.open = "true";
    backdrop.dataset.open = "true";
    modal.setAttribute("aria-hidden", "false");
    statusEl.textContent = "填写后保存到 data/personal/user_prefs.json";
    statusEl.removeAttribute("data-state");
    refreshSubmitState();
    inputs.budget_max_wan.focus();
  }

  function close() {
    if (modal.dataset.open !== "true" && backdrop.dataset.open !== "true") return;
    modal.dataset.open = "false";
    backdrop.dataset.open = "false";
    modal.setAttribute("aria-hidden", "true");
    if (store.get().onboardingOpen) {
      store.set({ onboardingOpen: false });
    }
  }

  function seedForm(prefs) {
    inputs.budget_min_wan.value = numericString(prefs.budget_min_wan);
    inputs.budget_max_wan.value = numericString(prefs.budget_max_wan);
    inputs.area_min_sqm.value = numericString(prefs.area_min_sqm);
    inputs.area_max_sqm.value = numericString(prefs.area_max_sqm);
    selectedDistricts = new Set(Array.isArray(prefs.districts) ? prefs.districts : []);
    renderDistricts();
  }

  async function loadDistricts() {
    try {
      const data = await api.districtsAll();
      const items = data.districts || [];
      districtIds = items.map((d) => ({ id: d.id, name: d.name || d.short || d.id }));
      renderDistricts();
    } catch (err) {
      districtsEl.textContent = `区域列表加载失败：${err.message}`;
    }
  }

  function renderDistricts() {
    if (!districtIds.length) {
      districtsEl.textContent = "区域加载中…";
      return;
    }
    districtsEl.innerHTML = districtIds
      .map(
        (d) =>
          `<button type="button" class="atlas-onboarding-district-chip" data-district-id="${escapeAttr(d.id)}" aria-pressed="${selectedDistricts.has(d.id) ? "true" : "false"}">${escapeText(d.name)}</button>`,
      )
      .join("");
    districtsEl.querySelectorAll("[data-district-id]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.dataset.districtId;
        if (selectedDistricts.has(id)) selectedDistricts.delete(id);
        else selectedDistricts.add(id);
        btn.setAttribute("aria-pressed", selectedDistricts.has(id) ? "true" : "false");
        refreshSubmitState();
      });
    });
  }

  function refreshSubmitState() {
    const ok = inputs.budget_max_wan.value && Number(inputs.budget_max_wan.value) > 0;
    submitBtn.disabled = !ok;
  }

  function showError(message) {
    statusEl.textContent = message;
    statusEl.dataset.state = "error";
  }

  async function submit() {
    statusEl.textContent = "保存中…";
    statusEl.removeAttribute("data-state");
    const payload = {
      budget_min_wan: numericValue(inputs.budget_min_wan.value),
      budget_max_wan: numericValue(inputs.budget_max_wan.value),
      area_min_sqm: numericValue(inputs.area_min_sqm.value),
      area_max_sqm: numericValue(inputs.area_max_sqm.value),
      districts: [...selectedDistricts],
    };
    const saved = await api.userPrefs.patch(payload);
    // Seed the home-mode filter slice so the chip bar immediately reflects
    // the saved prefs (otherwise filter-bar shows "无筛选" while the board
    // is silently filtered through the resolver fallback in loadFor).
    const currentFilters = store.get().filters || {};
    const homeFilters = resolveDefaultFilters("home", saved);
    store.set({
      userPrefs: saved,
      onboardingOpen: false,
      filters: { ...currentFilters, home: homeFilters },
    });
  }
}

function numericString(value) {
  if (value === null || value === undefined || value === "") return "";
  return String(value);
}

function numericValue(raw) {
  if (raw === null || raw === undefined || raw === "") return null;
  const num = Number(raw);
  return Number.isNaN(num) ? null : num;
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

Run: `node --check frontend/user/modules/home-onboarding.js`
Expected: exit 0.

Run: `grep -c 'data-component="onboarding"' frontend/user/index.html`
Expected: 1.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/home-onboarding.js frontend/user/styles/onboarding.css frontend/user/index.html
git commit -m "feat(user): add home onboarding modal (form + districts + submit)"
```

---

### Task 4: Wire bootstrap + filter resolution

**Files:**
- Modify: `frontend/user/modules/main.js`
- Modify: `frontend/user/modules/shell.js`
- Modify: `frontend/user/modules/opportunity-board.js`

We:
1. At boot, fetch `userPrefs` and stash in `state.userPrefs`. If the user lands on `?mode=home` while prefs are empty, set `onboardingOpen: true`.
2. On mode change to home with empty prefs, set `onboardingOpen: true` (so the modal auto-opens).
3. Wire the topbar 偏好 button (in `shell.js`) to set `onboardingOpen: true` regardless of mode.
4. The `opportunity-board.js` per-mode filter lookup now consults `resolveDefaultFilters(state.mode, state.userPrefs)` whenever there's no persisted filter for that mode. This keeps the behavior: persisted filters win over derived defaults.

The cleanest approach for #4: when a mode has NO entries persisted in `state.filters[mode]` (because the user has never edited it), seed it from `resolveDefaultFilters(mode, userPrefs)` at the moment we look up filters. Storing the seed back into `state.filters` makes the chips render correctly.

- [ ] **Step 1: Update `frontend/user/modules/main.js`**

Open the file. The top of the file currently has:

```javascript
import { createStore } from "./state.js";
import { initShell } from "./shell.js";
import { initMap } from "./map.js";
import { initBoard } from "./opportunity-board.js";
import { initDrawer } from "./detail-drawer.js";
import { initFilterBar } from "./filter-bar.js";
import { createStorage } from "./storage.js";
import { MODES, defaultFiltersFor } from "./modes.js";
```

Add directly below those:

```javascript
import { initOnboarding } from "./home-onboarding.js";
import { isPrefsEmpty } from "./user-prefs-helpers.js";
import { api } from "./api.js";
```

Find the existing `bootstrap` function. Find this block within it:

```javascript
  const store = createStore({
    mode: "yield",
    selection: null,
    runtime: null,
    filters: initialFilters,
    boardCount: null,
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
  });

  // Fire-and-forget: prefetch the user prefs (needed by the home onboarding
  // gate). Failures are non-fatal — the user can still click 偏好 to open
  // the modal and try again.
  api.userPrefs
    .get()
    .then((prefs) => store.set({ userPrefs: prefs }))
    .catch((err) => console.warn("[atlas] user prefs prefetch failed", err));
```

Find the existing `initShell({ root, store })` call. After that line, add:

```javascript
  initOnboarding({ root, store });

  // Auto-open the onboarding modal when a fresh user lands on home mode.
  let lastMode = store.get().mode;
  store.subscribe((state) => {
    if (state.mode !== lastMode) {
      lastMode = state.mode;
      if (state.mode === "home" && isPrefsEmpty(state.userPrefs)) {
        store.set({ onboardingOpen: true });
      }
    }
  });
  if (store.get().mode === "home" && isPrefsEmpty(store.get().userPrefs)) {
    store.set({ onboardingOpen: true });
  }
```

- [ ] **Step 2: Update `frontend/user/modules/shell.js`**

Open the file. Find the existing `initShell` function. After the existing `chipsContainer.addEventListener("click", ...)` block, add:

```javascript
  const prefsButton = root.querySelector('[data-component="prefs-button"]');
  if (prefsButton) {
    prefsButton.addEventListener("click", () => {
      store.set({ onboardingOpen: true });
    });
  }
```

- [ ] **Step 3: Update `frontend/user/modules/opportunity-board.js`**

Open the file. Find the existing import line:

```javascript
import { getMode, filtersToApiParams } from "./modes.js";
```

Replace with:

```javascript
import { getMode, filtersToApiParams, resolveDefaultFilters } from "./modes.js";
```

Find the `loadFor(modeId, state)` function. The current body is:

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

Replace with:

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

Also extend the `filterKeyFor` helper at the bottom of the file to also include `userPrefs.updated_at` so the board reloads when prefs change. Find:

```javascript
function filterKeyFor(state, modeId) {
  const filters = (state && state.filters && state.filters[modeId]) || {};
  return JSON.stringify(filters);
}
```

Replace with:

```javascript
function filterKeyFor(state, modeId) {
  const filters = (state && state.filters && state.filters[modeId]) || {};
  const prefsKey =
    state && state.userPrefs && state.userPrefs.updated_at
      ? state.userPrefs.updated_at
      : "";
  return JSON.stringify(filters) + "|" + prefsKey;
}
```

- [ ] **Step 4: Verify**

Run: `node --check frontend/user/modules/main.js frontend/user/modules/shell.js frontend/user/modules/opportunity-board.js`
Expected: exit 0 each.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs`
Expected: 43 tests passed (5 + 12 + 11 + 6 + 9 + 5 — wait recount: state 5, modes 12 (was 9 + 3 new = 12 wait... was 9 + 6 in this plan task 2 = 15... let me redo)

Actually let me count:
- test_state.mjs: 5 (unchanged)
- test_modes.mjs: 9 from Phase 3b + 6 new in Task 2 = 15
- test_drawer_data.mjs: 11 (unchanged)
- test_storage.mjs: 6 (unchanged)
- test_filter_helpers.mjs: 7 from Phase 3b + 2 new in Task 2 = 9
- test_user_prefs_helpers.mjs: 5 new in Task 1

Total: 5 + 15 + 11 + 6 + 9 + 5 = 51.

Run: `pytest -q`
Expected: 40 passed (no backend changed).

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/main.js frontend/user/modules/shell.js frontend/user/modules/opportunity-board.js
git commit -m "feat(user): wire onboarding modal + home defaults from user prefs"
```

---

### Task 5: smoke + README

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Extend smoke**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/user/prefs", '"districts"'),
```

Add directly above the user-prefs line (so the order in the smoke output keeps the user-platform HTML checks together):

```python
            (f"{base}/", 'data-component="onboarding"'),
```

The user-prefs row stays where it is.

- [ ] **Step 2: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 13 OK, exit 0.

- [ ] **Step 3: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 3c-1 起）` and change to `## 路由布局（Phase 3c-2 起）`.

Find the row whose third column starts with `用户平台。`. Its current text:

```markdown
用户平台。收益模式端到端 + 详情抽屉 + 实时筛选条（按模式记忆筛选 + 命中条数）。Home/City 模式 chip 已启用，全模式支持见后续 phase。
```

Replace with:

```markdown
用户平台。收益模式端到端 + 详情抽屉 + 实时筛选条 + 自住模式（首次进入弹窗收集预算/区域/面积，写入 data/personal/user_prefs.json；筛选条自动派生）。City 模式 chip 已启用，区域聚合见 Phase 3d。
```

- [ ] **Step 4: Verify all exit criteria**

Run each:
- `pytest -q` → 40 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs` → 51 passed (5 + 15 + 11 + 6 + 9 + 5)
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 13 OK
- For each JS file under `frontend/user/modules/`, `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py README.md
git commit -m "feat(user): wire onboarding into smoke + docs"
```

---

## Phase 3c-2 Exit Criteria

- [ ] `pytest -q` — 40 passed (no backend changes)
- [ ] `node --test ...` — 51 passed (5 state + 15 modes + 11 drawer + 6 storage + 9 filter helpers + 5 user-prefs helpers)
- [ ] Each JS file passes `node --check`: state, api, runtime, modes, map, opportunity-board, shell, detail-drawer, drawer-data, storage, filter-bar, home-onboarding, user-prefs-helpers, main
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 13 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` — open `http://127.0.0.1:8013/?mode=home` with no `data/personal/user_prefs.json` → onboarding modal appears centered over the map+board area, three fieldsets visible, submit disabled until budget upper is filled
- [ ] Manual: fill `budget_max_wan = 1500`, click two district chips (e.g. 浦东、静安), submit → modal closes, filter bar shows `总价 ≤ 1500 万` and `区域 = pudong`, board reloads with 1+ matches; `data/personal/user_prefs.json` exists on disk
- [ ] Manual: refresh page on `/?mode=home` → modal does NOT re-open; filter chips still present; topbar 偏好 button reopens the modal with form pre-filled
- [ ] `git log --oneline 6f6ce11..HEAD` shows exactly 5 Phase 3c-2 commits

## Out of Scope (deferred)

- Cross-field validators (budget_min ≤ budget_max etc.) — Phase 3c-3
- Multi-district filtering on `/api/v2/opportunities` — needs v2 contract change
- Area filter on board — `/api/v2/opportunities` does not accept area param; the form persists area to `user_prefs.json` but does not push it into the filter chain
- City mode district color band — Phase 3d
- Office anchor (commute calc) — Phase 6
- Editing prefs from inside the modal with field-level validation messages — current modal accepts any non-negative numeric input and lets backend 422 surface in `statusEl`
