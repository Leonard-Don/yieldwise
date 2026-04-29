# Phase 2a — User-Platform Backend Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `/api/v2/opportunities`, `/api/v2/map/{districts,communities,buildings}`, `/api/v2/buildings/{id}`, `/api/v2/communities/{id}` endpoints behind thin `api/domains/*` modules — no business-logic change.

**Architecture:** Each new domain module imports the corresponding function from `api.service` and re-exposes it under `/api/v2/*` via an `APIRouter`. Legacy `/api/*` routes are untouched, so backstage is unaffected. Tests assert byte-identical JSON equality between v2 and legacy responses — this proves zero drift. Phase 2b (frontend) will enrich the v2 endpoints with bbox/mode filtering; this phase only establishes the contract surface.

**Tech Stack:** FastAPI · pytest · httpx (already in requirements-dev). No new deps.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (Phase 2 section)

**Prior plan:** `docs/superpowers/plans/2026-04-23-phase-1-scaffolding.md` (merged as `bf2b599`)

---

## File Structure (Phase 2a outcome)

```
api/
├── main.py                     # MODIFIED: 4 new include_router lines (add to /api/v2)
├── domains/                    # EXISTING (from Phase 1)
│   ├── __init__.py
│   ├── health.py               # existing
│   ├── opportunities.py        # NEW
│   ├── buildings.py            # NEW
│   ├── communities.py          # NEW
│   └── map_tiles.py            # NEW
├── backstage/                  # unchanged (empty reservation from Phase 1)
├── service.py                  # unchanged — functions stay here; domains wrap them
└── persistence.py              # unchanged

tests/api/
├── test_routing.py             # unchanged
├── test_v2_health.py           # unchanged
├── test_v2_opportunities.py    # NEW
├── test_v2_buildings.py        # NEW
├── test_v2_communities.py      # NEW
└── test_v2_map.py              # NEW

scripts/
└── phase1_smoke.py             # MODIFIED: +4 route checks (name kept for CI stability)

README.md                       # MODIFIED: expand the "路由布局" v2 row to list concrete endpoints
```

**No physical function migration** in Phase 2a. The ~10k-line `service.py` is untouched. Phase 2a only establishes 4 new wafer-thin domain modules that import from `service` and expose an `APIRouter`. Physical extraction — when we want it — can happen safely later once the user-platform surface is stable and tests exist on both sides.

---

### Task 1: /api/v2/opportunities

**Files:**
- Create: `api/domains/opportunities.py`
- Create: `tests/api/test_v2_opportunities.py`
- Modify: `api/main.py` (add import + include_router)

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_v2_opportunities.py`:

```python
from __future__ import annotations


def test_v2_opportunities_matches_legacy_default(client) -> None:
    legacy = client.get("/api/opportunities")
    v2 = client.get("/api/v2/opportunities")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_opportunities_matches_legacy_with_filters(client) -> None:
    params = {
        "district": "pudong",
        "min_yield": 3.5,
        "max_budget": 1500.0,
        "min_samples": 2,
        "min_score": 10,
    }
    legacy = client.get("/api/opportunities", params=params)
    v2 = client.get("/api/v2/opportunities", params=params)
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_opportunities_returns_items_key(client) -> None:
    response = client.get("/api/v2/opportunities")
    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body, dict)
    assert "items" in body
    assert isinstance(body["items"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_v2_opportunities.py -v`
Expected: FAIL — `/api/v2/opportunities` doesn't exist yet (404).

- [ ] **Step 3: Create the domain module**

Write `api/domains/opportunities.py`:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..service import opportunities as _opportunities

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
def list_opportunities(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
) -> dict[str, Any]:
    return {
        "items": _opportunities(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
            min_score=min_score,
        )
    }
```

- [ ] **Step 4: Wire into api/main.py**

Open `api/main.py`. Find the existing v2 health router include (currently near line 96):

```python
app.include_router(v2_health.router, prefix="/api/v2")
```

Add a line directly above it that imports the new domain at the top, alongside the existing `from .domains import health as v2_health` import:

```python
from .domains import health as v2_health, opportunities as v2_opportunities
```

And add an `include_router` call right after the v2_health one:

```python
app.include_router(v2_opportunities.router, prefix="/api/v2")
```

- [ ] **Step 5: Run tests to verify pass**

Run: `pytest tests/api/test_v2_opportunities.py -v`
Expected: 3 passed.

- [ ] **Step 6: Full suite sanity**

Run: `pytest -q`
Expected: 10 passed (7 from Phase 1 + 3 new).

- [ ] **Step 7: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add api/domains/opportunities.py api/main.py tests/api/test_v2_opportunities.py
git commit -m "feat: add /api/v2/opportunities domain route"
```

---

### Task 2: /api/v2/map/{districts,communities,buildings}

**Files:**
- Create: `api/domains/map_tiles.py`
- Create: `tests/api/test_v2_map.py`
- Modify: `api/main.py`

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_v2_map.py`:

```python
from __future__ import annotations


def test_v2_map_districts_matches_legacy(client) -> None:
    legacy = client.get("/api/map/districts")
    v2 = client.get("/api/v2/map/districts")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_districts_with_filters(client) -> None:
    params = {"district": "pudong", "min_yield": 3.0, "max_budget": 1500.0, "min_samples": 1}
    legacy = client.get("/api/map/districts", params=params)
    v2 = client.get("/api/v2/map/districts", params=params)
    assert v2.json() == legacy.json()


def test_v2_map_communities_matches_legacy(client) -> None:
    legacy = client.get("/api/map/communities")
    v2 = client.get("/api/v2/map/communities")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_communities_with_filters(client) -> None:
    params = {
        "district": "pudong",
        "sample_status": "active_metrics",
        "focus_scope": "priority",
    }
    legacy = client.get("/api/map/communities", params=params)
    v2 = client.get("/api/v2/map/communities", params=params)
    assert v2.json() == legacy.json()


def test_v2_map_buildings_matches_legacy(client) -> None:
    legacy = client.get("/api/map/buildings")
    v2 = client.get("/api/v2/map/buildings")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_map_buildings_with_filters(client) -> None:
    params = {"district": "pudong", "focus_scope": "priority", "geometry_quality": "all"}
    legacy = client.get("/api/map/buildings", params=params)
    v2 = client.get("/api/v2/map/buildings", params=params)
    assert v2.json() == legacy.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_v2_map.py -v`
Expected: 6 FAIL — none of the /api/v2/map/* routes exist yet.

- [ ] **Step 3: Create the domain module**

Write `api/domains/map_tiles.py`:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..service import (
    list_districts as _list_districts,
    map_buildings_payload as _map_buildings_payload,
    map_communities_payload as _map_communities_payload,
    summarize as _summarize,
)

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/districts")
def map_districts(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return {
        "districts": _list_districts(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
        "summary": _summarize(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
    }


@router.get("/communities")
def map_communities(
    district: str | None = Query(default="all"),
    sample_status: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="all"),
    zoom: float | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict[str, Any]:
    return _map_communities_payload(
        district=district,
        sample_status=sample_status,
        focus_scope=focus_scope,
        zoom=zoom,
        viewport=viewport,
    )


@router.get("/buildings")
def map_buildings(
    district: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="priority"),
    geometry_quality: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict[str, Any]:
    return _map_buildings_payload(
        district=district,
        focus_scope=focus_scope,
        geometry_quality=geometry_quality,
        geo_run_id=geo_run_id,
        viewport=viewport,
    )
```

- [ ] **Step 4: Wire into api/main.py**

Extend the existing v2 imports and include_router block. After Task 1, the imports should be:

```python
from .domains import health as v2_health, opportunities as v2_opportunities
```

Change to:

```python
from .domains import (
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
)
```

And add after the existing include_router calls:

```python
app.include_router(v2_map_tiles.router, prefix="/api/v2")
```

Note: `map_tiles` already has `prefix="/map"` internally, so the full prefix becomes `/api/v2/map`.

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_v2_map.py -v`
Expected: 6 passed.

- [ ] **Step 6: Full suite sanity**

Run: `pytest -q`
Expected: 16 passed.

- [ ] **Step 7: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add api/domains/map_tiles.py api/main.py tests/api/test_v2_map.py
git commit -m "feat: add /api/v2/map/{districts,communities,buildings} routes"
```

---

### Task 3: /api/v2/buildings/{id}

**Files:**
- Create: `api/domains/buildings.py`
- Create: `tests/api/test_v2_buildings.py`
- Modify: `api/main.py`

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_v2_buildings.py`:

```python
from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def sample_building_id(client) -> str:
    """Pull a real building id from the legacy map/buildings GeoJSON FeatureCollection."""
    response = client.get("/api/map/buildings")
    assert response.status_code == 200, response.text
    body = response.json()
    features = body.get("features") or []
    assert features, "no building features in staged data; cannot run detail tests"
    props = features[0].get("properties") or {}
    building_id = props.get("building_id")
    assert building_id, f"first feature has no building_id in properties: {props!r}"
    return str(building_id)


def test_v2_building_detail_matches_legacy(client, sample_building_id) -> None:
    legacy = client.get(f"/api/buildings/{sample_building_id}")
    v2 = client.get(f"/api/v2/buildings/{sample_building_id}")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_building_detail_404_for_unknown(client) -> None:
    response = client.get("/api/v2/buildings/does-not-exist-xyz-123")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_v2_buildings.py -v`
Expected: FAIL — `/api/v2/buildings/{id}` does not exist yet.

- [ ] **Step 3: Create the domain module**

Write `api/domains/buildings.py`:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..service import get_building as _get_building

router = APIRouter(tags=["buildings"])


@router.get("/buildings/{building_id}")
def get_building(building_id: str) -> dict[str, Any]:
    building = _get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building
```

- [ ] **Step 4: Wire into api/main.py**

Extend the existing v2 imports:

```python
from .domains import (
    buildings as v2_buildings,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
)
```

Add after the existing include_router calls:

```python
app.include_router(v2_buildings.router, prefix="/api/v2")
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_v2_buildings.py -v`
Expected: 2 passed.

- [ ] **Step 6: Full suite sanity**

Run: `pytest -q`
Expected: 18 passed.

- [ ] **Step 7: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add api/domains/buildings.py api/main.py tests/api/test_v2_buildings.py
git commit -m "feat: add /api/v2/buildings/{id} domain route"
```

---

### Task 4: /api/v2/communities/{id}

**Files:**
- Create: `api/domains/communities.py`
- Create: `tests/api/test_v2_communities.py`
- Modify: `api/main.py`

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_v2_communities.py`:

```python
from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def sample_community_id(client) -> str:
    """Pull a real community id from the legacy map/communities endpoint."""
    response = client.get("/api/map/communities")
    assert response.status_code == 200, response.text
    body = response.json()
    items = body.get("items") or []
    assert items, "no communities in staged data; cannot run detail tests"
    community_id = items[0].get("community_id")
    assert community_id, f"first community item has no community_id: {items[0]!r}"
    return str(community_id)


def test_v2_community_detail_matches_legacy(client, sample_community_id) -> None:
    legacy = client.get(f"/api/communities/{sample_community_id}")
    v2 = client.get(f"/api/v2/communities/{sample_community_id}")
    assert legacy.status_code == 200, legacy.text
    assert v2.status_code == 200, v2.text
    assert v2.json() == legacy.json()


def test_v2_community_detail_404_for_unknown(client) -> None:
    response = client.get("/api/v2/communities/does-not-exist-xyz-123")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_v2_communities.py -v`
Expected: FAIL — no `/api/v2/communities/{id}` route.

- [ ] **Step 3: Create the domain module**

Write `api/domains/communities.py`:

```python
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..service import get_community as _get_community

router = APIRouter(tags=["communities"])


@router.get("/communities/{community_id}")
def get_community(community_id: str) -> dict[str, Any]:
    community = _get_community(community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community
```

- [ ] **Step 4: Wire into api/main.py**

Extend the existing v2 imports:

```python
from .domains import (
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
)
```

Add after the existing include_router calls:

```python
app.include_router(v2_communities.router, prefix="/api/v2")
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/api/test_v2_communities.py -v`
Expected: 2 passed.

- [ ] **Step 6: Full suite sanity**

Run: `pytest -q`
Expected: 20 passed.

- [ ] **Step 7: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add api/domains/communities.py api/main.py tests/api/test_v2_communities.py
git commit -m "feat: add /api/v2/communities/{id} domain route"
```

---

### Task 5: Extend smoke script + README

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Extend the smoke script's checks list**

Open `scripts/phase1_smoke.py` and find the `checks` list (currently has 4 tuples: `/`, `/backstage/`, `/api/v2/health`, `/api/health`). Replace the list with:

```python
        checks = [
            (f"{base}/", 'data-user-shell="atlas"'),
            (f"{base}/backstage/", "<title>Shanghai Yield Atlas</title>"),
            (f"{base}/api/v2/health", '"surface":"user-platform-v2"'),
            (f"{base}/api/health", '"status":"ok"'),
            (f"{base}/api/v2/opportunities", '"items"'),
            (f"{base}/api/v2/map/districts", '"districts"'),
            (f"{base}/api/v2/map/communities", '"items"'),
            (f"{base}/api/v2/map/buildings", '"features"'),
        ]
```

Note: the substring expectations are intentionally loose — we only assert that the expected top-level key is present somewhere in the JSON. That's enough to prove the route is live and returning the right shape; exhaustive content-level checks are pytest's job.

- [ ] **Step 2: Run the smoke script**

Run: `python3 scripts/phase1_smoke.py`
Expected: all 8 routes OK, exit 0.

- [ ] **Step 3: Update README v2 row**

Open `README.md`, find the "路由布局（Phase 1 起）" section (added in Phase 1). The v2 row is currently:

```markdown
| `/api/v2/*` | `api/domains/` | 用户平台专属接口 |
```

Replace with:

```markdown
| `/api/v2/*` | `api/domains/` | 用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}` |
```

Also update the "Phase 1 起" suffix to reflect progress — change:

```markdown
## 路由布局（Phase 1 起）
```

to:

```markdown
## 路由布局（Phase 2a 起）
```

- [ ] **Step 4: Verify**

Run: `grep -n "路由布局" README.md` — expect exactly 1 match.
Run: `grep -c "/api/v2" README.md` — expect at least 1.
Run: `python3 scripts/phase1_smoke.py` — 8 routes OK.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py README.md
git commit -m "test: extend phase smoke to cover /api/v2/* routes + docs"
```

---

## Phase 2a Exit Criteria

Run each and confirm before declaring Phase 2a complete:

- [ ] `pytest -q` — 20 tests pass (7 from Phase 1 + 13 new)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `node --check frontend/backstage/app.js` — exit 0 (unchanged but sanity)
- [ ] `node --check frontend/user/modules/main.js` — exit 0 (unchanged but sanity)
- [ ] `python3 scripts/phase1_smoke.py` — 8 routes OK
- [ ] Manual: `uvicorn api.main:app --port 8013`, browser-check that `/backstage/` still loads and runs (regression guard)
- [ ] Manual: `curl -s http://127.0.0.1:8013/api/v2/opportunities | python3 -m json.tool | head -10` shows `{"items": [...]}` with at least one item
- [ ] `git log --oneline` on the feature branch shows 5 focused commits

## Out of Scope (deferred to Phase 2b and later)

- Any change to the frontend — `frontend/user/` remains the empty D1 shell.
- Any new filtering parameters on v2 endpoints (e.g., `bbox`, `mode`). v2 endpoints mirror legacy behavior exactly in 2a; Phase 2b will add mode-aware / viewport-aware filters.
- Physical migration of `service.py` functions into domain modules. Domain modules wrap `service.*` imports; the functions themselves stay in `service.py` until a later phase.
- `api/backstage/` population — still a Phase 3+ concern.
- Touching `/api/*` legacy routes in any way.
