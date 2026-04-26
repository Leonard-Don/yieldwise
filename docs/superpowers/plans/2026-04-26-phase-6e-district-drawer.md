# Phase 6e — District Detail Drawer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a city-mode district polygon (or city-mode board row) is clicked, open the existing detail drawer with district KPIs (均租售比 / 均机会分 / 样本量) and a clickable list of the district's top communities. Clicking a community in that list drills down to community detail (existing path).

**Architecture:** Adds one backend endpoint `GET /api/v2/districts/{id}` that pulls a single district from `service.list_districts()` and returns it pre-shaped (id / name / yield / score / sample / communities sorted by yield desc). Frontend extends `detail-drawer.js`'s already-present render path: the Phase 3d guard that silently dropped district selections is loosened to also accept `district`; `fetchDetail` gets a third branch; `renderBody` branches on `sel.type` to emit either the building/community body (KPI + floor chart + listing summary) or the new district body (KPI + community list). The KPI row reuses Phase 3a's `pickKpisFor("city", detail)` since district fields (`yield` / `score` / `sample`) match exactly what the city-mode KPI extractor expects.

**Tech Stack:** FastAPI · Pydantic 2.9 · `service.list_districts()` (already used by `/api/v2/map/districts`) · vanilla JS ES modules · `node:test` for the new pure helper · existing detail-drawer / drawer-data infrastructure. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 5 三模式语义 row "city → 抽屉 KPI 重点：区均租售比 / 挂牌量 / 6-12-24 月趋势 / 分位数")

**Prior plan:** 2026-04-26-phase-6d-cmd-k-search.md (merged at `539eb93`)

---

## File Structure (Phase 6e outcome)

```
api/
├── main.py                          # MODIFIED: include_router for v2_districts
├── schemas/
│   └── districts.py                 # NEW — DistrictSummary (output schema)
└── domains/
    └── districts.py                 # NEW — GET /api/v2/districts/{id}

frontend/user/
├── styles/
│   └── drawer.css                   # MODIFIED: add .atlas-district-* community list styling
└── modules/
    ├── api.js                       # MODIFIED: api.districtDetail(id)
    ├── drawer-data.js               # MODIFIED: add topCommunitiesFromDistrict(detail, limit)
    └── detail-drawer.js             # MODIFIED: handle 'district' type (fetchDetail + renderBody branch + click → community drilldown)

tests/api/
├── test_districts_schema.py         # NEW (~3 cases)
└── test_v2_districts.py             # NEW (~5 cases)

tests/frontend/
└── test_drawer_data.mjs             # MODIFIED: +3 cases for topCommunitiesFromDistrict

scripts/phase1_smoke.py              # MODIFIED: +1 row asserting GET /api/v2/districts/{id}
README.md                            # MODIFIED: bump Phase 6d → Phase 6e
```

**Out-of-scope (deferred):**
- 6/12/24 月趋势 / 分位数 — backend doesn't expose historical district metrics; mock data has only the current snapshot. Spec lists these but they need a separate data layer (a metrics history table). Phase 7+.
- 挂牌量 (listing count) — no listings endpoint exists; community count is the closest available proxy and is shown instead.
- District-level alerts (`district_delta_abs` rule) — Phase 5a stubbed the rule field but the diff function ignores districts. Separate plan.
- Map-side selection sync (clicking a community in the drawer's district list could re-color the city map polygons) — Phase 6f / polish.
- Notes for districts — schema's `target_type` Literal accepts "building"/"community"/"floor"/"listing"; "district" isn't in that list, so the notes section stays hidden when sel.type === 'district'. Adding district notes would be a Phase 4c.
- Manual browser screenshot.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-6e-district-drawer .worktrees/phase-6e-district-drawer
cd .worktrees/phase-6e-district-drawer
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 109 pytest passed; 93 node tests passed; 20 smoke routes OK.

---

### Task 1: District schema + endpoint + tests

**Files:**
- Create: `api/schemas/districts.py`
- Create: `api/domains/districts.py`
- Create: `tests/api/test_districts_schema.py`
- Create: `tests/api/test_v2_districts.py`
- Modify: `api/main.py`

`DistrictSummary` is the response shape: `id` / `name` / `yield_pct` (renamed from `yield` to avoid the Python keyword) / `score` / `sample` / `community_count` / `communities`. The endpoint walks `list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)`, picks the matching id, sorts its `communities` by yield desc, and returns a JSON body that uses the `yield` key in output (Pydantic `Field(serialization_alias="yield")`).

- [ ] **Step 1: Write the failing schema tests**

Write `tests/api/test_districts_schema.py`:

```python
from __future__ import annotations

from api.schemas.districts import DistrictSummary


def test_district_summary_round_trip_minimal() -> None:
    payload = {
        "id": "pudong",
        "name": "浦东新区",
        "yield": 4.5,
        "score": 80,
        "sample": 100,
        "community_count": 12,
        "communities": [],
    }
    summary = DistrictSummary.model_validate(payload)
    assert summary.name == "浦东新区"
    assert summary.yield_pct == 4.5
    assert summary.community_count == 12


def test_district_summary_serialises_yield_alias() -> None:
    summary = DistrictSummary(
        id="pudong",
        name="浦东新区",
        yield_pct=4.5,
        score=80,
        sample=100,
        community_count=0,
        communities=[],
    )
    dump = summary.model_dump(by_alias=True)
    assert dump["yield"] == 4.5
    assert "yield_pct" not in dump


def test_district_summary_communities_default_empty() -> None:
    summary = DistrictSummary.model_validate(
        {"id": "x", "name": "Y", "yield": 0.0, "score": 0, "sample": 0, "community_count": 0}
    )
    assert summary.communities == []
```

- [ ] **Step 2: Verify schema tests fail**

Run: `pytest tests/api/test_districts_schema.py -v`
Expected: ImportError.

- [ ] **Step 3: Implement `api/schemas/districts.py`**

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DistrictSummary(BaseModel):
    """Single-district detail response.

    The JSON field is `yield` (matching the rest of the API surface) but the
    Python attribute is `yield_pct` to dodge the keyword. Use
    `model_dump(by_alias=True)` when serialising for HTTP.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    name: str
    yield_pct: float | None = Field(default=None, alias="yield", serialization_alias="yield")
    score: int | None = None
    sample: int | None = None
    community_count: int = 0
    communities: list[dict[str, Any]] = Field(default_factory=list)
```

- [ ] **Step 4: Verify schema tests pass**

Run: `pytest tests/api/test_districts_schema.py -v`
Expected: 3 passed.

- [ ] **Step 5: Write the failing endpoint tests**

Write `tests/api/test_v2_districts.py`:

```python
from __future__ import annotations


def test_get_district_404_for_unknown_id(client) -> None:
    response = client.get("/api/v2/districts/nope")
    assert response.status_code == 404


def test_get_district_returns_pudong(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == "pudong"
    assert body["name"] == "浦东新区"
    assert "yield" in body
    assert "communities" in body
    assert isinstance(body["communities"], list)


def test_get_district_includes_community_count(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    body = response.json()
    assert body["community_count"] == len(body["communities"])


def test_get_district_communities_sorted_yield_desc(client) -> None:
    response = client.get("/api/v2/districts/pudong")
    body = response.json()
    yields = [
        c.get("yield") for c in body["communities"] if c.get("yield") is not None
    ]
    assert yields == sorted(yields, reverse=True)


def test_get_district_works_for_huangpu(client) -> None:
    # Sanity check on a different district id
    response = client.get("/api/v2/districts/huangpu")
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        assert response.json()["id"] == "huangpu"
```

- [ ] **Step 6: Verify endpoint tests fail**

Run: `pytest tests/api/test_v2_districts.py -v`
Expected: 404s for the not-yet-mounted route.

- [ ] **Step 7: Implement `api/domains/districts.py`**

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..schemas.districts import DistrictSummary
from ..service import list_districts

router = APIRouter(tags=["districts"])


@router.get("/districts/{district_id}")
def get_district(district_id: str) -> dict[str, Any]:
    rows = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    match = next((d for d in rows if d.get("id") == district_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="District not found")
    communities = list(match.get("communities") or [])
    communities.sort(key=lambda c: -(_safe_float(c.get("yield")) or 0.0))
    summary = DistrictSummary(
        id=match.get("id"),
        name=match.get("name") or "",
        yield_pct=_safe_float(match.get("yield")),
        score=_safe_int(match.get("score")),
        sample=_safe_int(match.get("sample") or match.get("saleSample")),
        community_count=len(communities),
        communities=communities,
    )
    return summary.model_dump(by_alias=True)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def _safe_int(value: Any) -> int | None:
    f = _safe_float(value)
    return int(f) if f is not None else None
```

- [ ] **Step 8: Wire into `api/main.py`**

Open `api/main.py`. Find the v2 imports block (after Phase 6d it includes `search as v2_search`). Add `districts as v2_districts` alphabetically:

```python
from .domains import (
    alerts as v2_alerts,
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    districts as v2_districts,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    search as v2_search,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)
```

Add the include_router call alongside the other v2 includes:

```python
app.include_router(v2_districts.router, prefix="/api/v2")
```

- [ ] **Step 9: Run all backend tests**

Run: `pytest tests/api/test_districts_schema.py tests/api/test_v2_districts.py -v`
Expected: 8 passed (3 schema + 5 endpoint).

Run: `pytest -q`
Expected: 117 passed (109 prior + 3 schema + 5 endpoint).

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 10: Commit**

```bash
git add api/schemas/districts.py api/domains/districts.py api/main.py tests/api/test_districts_schema.py tests/api/test_v2_districts.py
git commit -m "feat(api): add /api/v2/districts/{id} aggregate endpoint"
```

---

### Task 2: drawer-data.js helper + tests

**Files:**
- Modify: `frontend/user/modules/drawer-data.js`
- Modify: `tests/frontend/test_drawer_data.mjs`

Add a single pure helper `topCommunitiesFromDistrict(detail, limit)` that returns up to `limit` `{id, name, yield, score}` rows from `detail.communities`, treating missing arrays / non-numeric values defensively. The existing `pickKpisFor("city", detail)` already handles district KPIs (yield/score/sample) without changes — this task only adds the community-list helper.

- [ ] **Step 1: Add failing tests**

Open `tests/frontend/test_drawer_data.mjs`. Find the existing import line. Replace:

```javascript
import {
  formatPct,
  formatWan,
  formatYuan,
  normalizeYieldPct,
  bucketBars,
  pickKpisFor,
} from "../../frontend/user/modules/drawer-data.js";
```

with:

```javascript
import {
  formatPct,
  formatWan,
  formatYuan,
  normalizeYieldPct,
  bucketBars,
  pickKpisFor,
  topCommunitiesFromDistrict,
} from "../../frontend/user/modules/drawer-data.js";
```

Append the following tests at the end of the file:

```javascript
test("topCommunitiesFromDistrict: empty input → []", () => {
  assert.deepEqual(topCommunitiesFromDistrict(null, 5), []);
  assert.deepEqual(topCommunitiesFromDistrict({}, 5), []);
  assert.deepEqual(topCommunitiesFromDistrict({ communities: [] }, 5), []);
});

test("topCommunitiesFromDistrict: returns up to limit rows preserving server order", () => {
  const detail = {
    communities: [
      { id: "a", name: "A", yield: 5.0, score: 80 },
      { id: "b", name: "B", yield: 4.5, score: 70 },
      { id: "c", name: "C", yield: 4.0, score: 60 },
      { id: "d", name: "D", yield: 3.5, score: 50 },
    ],
  };
  const top2 = topCommunitiesFromDistrict(detail, 2);
  assert.deepEqual(top2.map((row) => row.id), ["a", "b"]);
});

test("topCommunitiesFromDistrict: tolerates missing fields", () => {
  const detail = {
    communities: [
      { id: "a", name: "A" },
      { id: "b", yield: 4.0 },
      { name: "C", yield: 3.0 }, // missing id — dropped
    ],
  };
  const rows = topCommunitiesFromDistrict(detail, 5);
  assert.deepEqual(rows.map((r) => r.id), ["a", "b"]);
});
```

- [ ] **Step 2: Verify the new tests fail**

Run: `node --test tests/frontend/test_drawer_data.mjs`
Expected: 3 failing tests for the new helper (plus 11 existing passes — total runs but reports failures).

- [ ] **Step 3: Append the helper to `frontend/user/modules/drawer-data.js`**

Open the file. Add at the end (after `pickKpisFor` and the `KPI_MAP` const):

```javascript
export function topCommunitiesFromDistrict(detail, limit) {
  if (!detail || typeof detail !== "object") return [];
  const items = Array.isArray(detail.communities) ? detail.communities : [];
  const out = [];
  for (const row of items) {
    if (!row || !row.id) continue;
    out.push({
      id: row.id,
      name: row.name || row.id,
      yield: row.yield ?? null,
      score: row.score ?? null,
    });
    if (out.length >= Math.max(0, limit | 0)) break;
  }
  return out;
}
```

- [ ] **Step 4: Verify**

Run: `node --test tests/frontend/test_drawer_data.mjs`
Expected: 14 passed (11 prior + 3 new).

Run: `node --check frontend/user/modules/drawer-data.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs`
Expected: 96 passed (93 prior + 3 new).

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/drawer-data.js tests/frontend/test_drawer_data.mjs
git commit -m "feat(user): add topCommunitiesFromDistrict drawer helper"
```

---

### Task 3: detail-drawer.js handles district + drawer.css community list

**Files:**
- Modify: `frontend/user/modules/api.js`
- Modify: `frontend/user/modules/detail-drawer.js`
- Modify: `frontend/user/styles/drawer.css`

Three edits:
1. `api.districtDetail(id)` — wraps GET /api/v2/districts/{id}
2. `detail-drawer.js` — guard accepts "district"; `fetchDetail` adds district branch; `renderBody` branches on `sel.type` so districts render KPI + community list (no floor chart, no listing summary); clicking a community row dispatches a fresh `selection: {type: "community", id, props}` so the existing community fetch path takes over
3. `drawer.css` — small list styling for the community drilldown rows

- [ ] **Step 1: Extend `api.js`**

Open `frontend/user/modules/api.js`. Find the existing `mapDistricts` line and add a sibling method directly below it. Find:

```javascript
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  districtsAll: () => getJSON("/api/v2/map/districts"),
```

Replace with:

```javascript
  mapDistricts: (params) => getJSON(`/api/v2/map/districts${buildQuery(params)}`),
  districtsAll: () => getJSON("/api/v2/map/districts"),
  districtDetail: (id) => getJSONFresh(`/api/v2/districts/${encodeURIComponent(id)}`),
```

Run: `node --check frontend/user/modules/api.js`
Expected: exit 0.

- [ ] **Step 2: Update `frontend/user/modules/detail-drawer.js`**

Open the file. Update the import line to include the new helper. Find:

```javascript
import { bucketBars, formatWan, formatYuan, pickKpisFor } from "./drawer-data.js";
```

Replace with:

```javascript
import {
  bucketBars,
  formatPct,
  formatWan,
  formatYuan,
  pickKpisFor,
  topCommunitiesFromDistrict,
} from "./drawer-data.js";
```

(The `formatPct` is needed for the community list rendering. It's already exported from drawer-data.js.)

Find the existing guard in `handleStateChange`:

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

Replace with:

```javascript
  function handleStateChange(state) {
    const sel = state.selection;
    if (
      !sel ||
      (sel.type !== "building" &&
        sel.type !== "community" &&
        sel.type !== "district")
    ) {
      if (lastSelectionId !== null) {
        renderClosed();
        lastSelectionId = null;
        lastMode = null;
      }
      return;
    }
```

Find the existing `fetchDetail` function:

```javascript
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
```

Replace with:

```javascript
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
    if (sel.type === "district") {
      return getJSON(`/api/v2/districts/${encodeURIComponent(sel.id)}`);
    }
    throw new Error(`未知的选中类型：${sel.type}`);
  }
```

Find the existing `renderBody` function:

```javascript
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
```

Replace with:

```javascript
  function renderBody({ sel, detail, mode }) {
    if (sel && sel.type === "district") {
      return renderDistrictBody({ detail });
    }
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

  function renderDistrictBody({ detail }) {
    const kpis = pickKpisFor("city", {
      yield: detail.yield,
      score: detail.score,
      sample: detail.sample,
    });
    const top = topCommunitiesFromDistrict(detail, 8);
    return `${renderKpiRow(kpis)}<div><h3 class="atlas-section-title">区内小区（前 ${top.length}）</h3>${renderCommunityList(top)}</div>`;
  }

  function renderCommunityList(rows) {
    if (rows.length === 0) {
      return `<div class="atlas-district-empty">该区暂无小区数据</div>`;
    }
    return `<ol class="atlas-district-list">${rows
      .map(
        (row) =>
          `<li class="atlas-district-row" data-community-id="${escapeAttr(row.id)}"><span class="atlas-district-name">${escapeText(row.name)}</span><span class="atlas-district-stat">${escapeText(formatPct(row.yield))}</span><span class="atlas-district-stat">${escapeText(formatScore(row.score))}</span></li>`,
      )
      .join("")}</ol>`;
  }

  function formatScore(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return "—";
    return String(Math.round(Number(value)));
  }
```

Find the existing call site that builds the body inside `renderDetail`:

```javascript
    bodyEl.innerHTML = renderBody({ detail, mode });
```

Replace with:

```javascript
    bodyEl.innerHTML = renderBody({ sel, detail, mode });
```

Find the section where the click handlers live (currently the file has none on the body — clicks were external until now). At the bottom of `initDrawer`, after `syncSelectionHighlight` if present, add a delegated click handler for community drilldown. Find the existing event-wiring block at the top of `initDrawer`:

```javascript
  closeButton.addEventListener("click", close);
  backdrop.addEventListener("click", close);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.dataset.open === "true") {
      close();
    }
  });
```

Add directly below it (alongside the other listeners):

```javascript
  bodyEl.addEventListener("click", (event) => {
    const row = event.target.closest("[data-community-id]");
    if (!row) return;
    const communityId = row.dataset.communityId;
    if (!communityId) return;
    store.set({
      selection: {
        type: "community",
        id: communityId,
        props: { name: row.querySelector(".atlas-district-name")?.textContent || "" },
      },
    });
  });
```

- [ ] **Step 3: Append district list styles to `frontend/user/styles/drawer.css`**

Open `frontend/user/styles/drawer.css`. Append at the end:

```css
.atlas-district-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.atlas-district-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, auto) minmax(0, auto);
  align-items: baseline;
  gap: 10px;
  padding: 6px 8px;
  background: var(--bg-2);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 80ms ease, background 80ms ease;
}

.atlas-district-row:hover {
  border-color: var(--up);
  background: rgba(0, 214, 143, 0.08);
}

.atlas-district-name {
  color: var(--text-0);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.atlas-district-stat {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  color: var(--text-dim);
}

.atlas-district-empty {
  color: var(--text-xs);
  font-size: 11px;
  letter-spacing: 0.06em;
  padding: 8px 0;
}
```

- [ ] **Step 4: Verify**

Run: `node --check frontend/user/modules/detail-drawer.js`
Expected: exit 0.

Run combined: `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs tests/frontend/test_user_prefs_helpers.mjs tests/frontend/test_watchlist_helpers.mjs tests/frontend/test_annotations_helpers.mjs tests/frontend/test_alerts_helpers.mjs tests/frontend/test_shortcuts_helpers.mjs tests/frontend/test_search_helpers.mjs`
Expected: 96 passed.

Run: `pytest -q`
Expected: 117 passed.

- [ ] **Step 5: Commit**

```bash
git add frontend/user/modules/api.js frontend/user/modules/detail-drawer.js frontend/user/styles/drawer.css
git commit -m "feat(user): drawer renders district detail + community drilldown"
```

---

### Task 4: smoke + README

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Extend `scripts/phase1_smoke.py`**

Open the file. Find the line:

```python
            (f"{base}/api/v2/search?q=%E6%B5%A6%E4%B8%9C", '"items"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/districts/pudong", '"communities"'),
```

- [ ] **Step 2: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 21 OK, exit 0.

- [ ] **Step 3: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 6d 起）` and change to `## 路由布局（Phase 6e 起）`.

Find the row whose third column begins with `用户平台专属接口。已开放：`. Replace its description with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/districts/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)、`/annotations` (GET-by-target + POST + PATCH + DELETE)、`/alerts/{rules,since-last-open,mark-seen}` (GET + PATCH + POST)、`/search` (GET)
```

Find the row whose third column starts with `用户平台。`. Replace its description with:

```markdown
用户平台。收益模式 + 详情抽屉（含区级 KPI + 区内小区下钻）+ 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅（含目标名解析）+ 键盘快捷键（⌘K 搜索、⌘1/2/3 切模式、F 关注、N 笔记、? 帮助）。
```

- [ ] **Step 4: Verify all exit criteria**

Run each:
- `pytest -q` → 117 passed
- `node --test ... 11 frontend test files` → 96 passed
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 21 OK
- For each JS file under `frontend/user/modules/`: `node --check` → exit 0
- `node --check frontend/backstage/app.js` → exit 0

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py README.md
git commit -m "feat(api): wire district detail into smoke + docs"
```

---

## Phase 6e Exit Criteria

- [ ] `pytest -q` — 117 passed (109 prior + 3 schema + 5 v2 districts)
- [ ] `node --test ...` — 96 passed (93 prior + 3 drawer-data district helper)
- [ ] Each JS file under `frontend/user/modules/` passes `node --check`
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 21 rows OK
- [ ] Manual: `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running. Switch to city mode (`⌘3`), click any district row in the board → drawer opens with title (district name), 3 KPI cards (均租售比 / 均机会分 / 样本量), and a `区内小区（前 N）` list with up to 8 communities sorted by yield. Click a community row → drawer rerenders with that community's building/community detail (KPI + floor chart + listing summary). Esc closes the drawer.
- [ ] `git log --oneline 539eb93..HEAD` shows exactly 4 commits

## Out of Scope (deferred)

- 6/12/24 月趋势 / 分位数 (district historical metrics)
- 挂牌量 (listings count) — needs a listings endpoint
- District-level alerts (`district_delta_abs` rule)
- Map-side selection sync (city polygon ↔ drawer community-row two-way binding)
- Notes for districts (target_type doesn't include "district" today)
- Manual browser screenshot
