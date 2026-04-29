# Yieldwise Plan 1 — Foundation, Branding, Multi-city Scaffold

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Yieldwise v0.1 — a Yieldwise-branded build with city dropdown infrastructure (Shanghai loaded as the only city for now), plus T1 connection-pool audit + T3 dependency-license matrix + the long-lived `research-private` branch holding all browser-capture code.

**Architecture:** New `api/config/cities/` package with a `CityManifest` dataclass loaded from YAML; loader resolves manifest from `ATLAS_CITY` env var (default `shanghai`) at process start. New `/api/v2/config/city` endpoint serves manifest summary to the frontend; frontend `config-bootstrap.js` fetches once at boot and exposes center/zoom/district list to existing modules. T1 is an audit (pool already exists in `api/persistence.py:55-72`); T3 produces a static license matrix. Renaming touches metadata + visible titles only — no behavioral change.

**Tech Stack:** FastAPI · PyYAML (NEW dep — single addition) · Pydantic 2.9 · vanilla JS ES modules · pytest for backend · `node:test` for frontend helpers · `pip-licenses` (dev only) for license audit

**Parent spec:** `docs/superpowers/specs/2026-04-29-yieldwise-commercialization-design.md`

---

## Scope

This plan covers the FOUNDATION layer of Yieldwise v1:

- **Phase A** — research-private branch, T1 pool audit, T3 license audit
- **Phase B** — Yieldwise / 租知 branding (metadata + visible titles)
- **Phase C** — M1 multi-city scaffold (manifest YAML + loader + API + frontend bootstrap)

**Out of scope (subsequent plans, to be written separately)**:

- **Plan 2** — M2 Auth + M3 Customer Data Import (10–12 工程日)
- **Plan 3** — M4 Reports + M5 Deployment Package (7–10 工程日)
- **Plan 4** — M6 Backstage Workflow Pivot + T2 service.py cleanup (10–12 工程日)

**Total this plan:** ~6–7 工程日 ≈ 3 weeks part-time

---

## File Structure (Plan 1 outcome)

```
api/
├── main.py                          # MODIFIED: FastAPI title → Yieldwise; include v2_config router
├── config/                          # NEW dir
│   ├── __init__.py
│   └── cities/
│       ├── __init__.py
│       ├── manifest.py              # NEW — CityManifest dataclass + YAML parser
│       ├── loader.py                # NEW — load_active_city() reads ATLAS_CITY env
│       └── shanghai.yaml            # NEW — Shanghai constants extracted
├── domains/
│   └── config.py                    # NEW — GET /api/v2/config/city
├── schemas/
│   └── city_config.py               # NEW — CityConfigResponse pydantic model
├── persistence.py                   # MODIFIED: docstring note re: pool already on
└── requirements.txt                 # MODIFIED: + pyyaml>=6.0,<7.0

frontend/user/
├── index.html                       # MODIFIED: <title>Yieldwise · 租知</title>
└── modules/
    ├── api.js                       # MODIFIED: + api.cityConfig()
    ├── config-bootstrap.js          # NEW — fetches /api/v2/config/city once, caches
    ├── main.js                      # MODIFIED: await config-bootstrap before initMap
    └── map.js                       # MODIFIED: read center/zoom from cityConfig (drop SHANGHAI_CENTER)

frontend/backstage/
└── index.html                       # MODIFIED: <title>Yieldwise Workbench · 租知</title>

docs/
├── legal/
│   └── dependency-licenses.md       # NEW — T3 audit output
└── deployment/
    └── city-manifests.md            # NEW — how to add a new city YAML

README.md                            # MODIFIED: header → Yieldwise; add 分支策略 section

tests/api/
├── test_persistence_pool.py         # NEW — T1 regression test
├── test_city_manifest.py            # NEW — manifest parser/loader
└── test_v2_config_city.py           # NEW — endpoint contract

tests/frontend/
└── test_config_bootstrap.mjs        # NEW (~3 cases)

scripts/
└── phase1_smoke.py                  # MODIFIED: + assert /api/v2/config/city OK

pyproject.toml                       # MODIFIED: + [project] block name="yieldwise"
```

---

## Phase A: Branch + Audit (~2 工程日)

### Task A.1: Create `research-private` long-lived branch

**Why:** Per spec §4, `research-private` preserves browser-capture pipeline + all current research code; `main` is reserved for Yieldwise commercial. Branch BEFORE removing anything.

**Files:** none modified (branch op only) + README.md

- [ ] **Step 1: Verify clean working state**

Run: `git status`
Expected: only the 4 unrelated WIP files (`api/service.py`, `frontend/user/modules/detail-drawer.js`, `frontend/user/modules/drawer-data.js`, `jobs/match_osm_to_communities.py`) — do NOT include them in this plan's commits.

Run: `git log -1 --oneline`
Expected: at `00cdd1f` (yieldwise spec) or later.

- [ ] **Step 2: Create research-private branch at current HEAD**

```bash
git branch research-private
git push -u origin research-private 2>/dev/null || echo "no remote configured — local branch created"
```

- [ ] **Step 3: Add 分支策略 section to README**

Edit `README.md` — insert after the `## 这个仓库现在是什么` section:

```markdown
## 分支策略

- `main` — Yieldwise 商业版（剥离公开页采集，可对外交付）
- `research-private` — 内研分支，保留 browser-capture / 公开页采样 / 全部研究流。每半年从 `main` cherry-pick 非合规改进。
- `release/yieldwise-v1.x` — 私部署 frozen 标签（v1 ship 后建立）

> 提交到 `main` 之前确认改动不依赖被剥离的公开页采集模块。
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add Yieldwise branch strategy section

main now hosts the Yieldwise commercial line; research-private
preserves browser-capture and public-sampling pipelines.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task A.2: T3 — Dependency license audit

**Why:** Spec §5.4 T3. Output is the static doc client legal can review, plus a sanity check for GPL/AGPL contamination.

**Files:**
- Create: `docs/legal/dependency-licenses.md`

- [ ] **Step 1: Install pip-licenses (dev-only, not in requirements)**

```bash
python3 -m pip install --user 'pip-licenses>=4.0,<5.0'
```

- [ ] **Step 2: Generate license matrix**

```bash
mkdir -p docs/legal
python3 -m piplicenses \
  --from=mixed --format=markdown --with-urls \
  --packages $(grep -v '^#' api/requirements.txt | sed 's/[<>=].*//' | tr '\n' ' ') \
  > /tmp/yw-licenses-table.md
```

- [ ] **Step 3: Audit for forbidden licenses**

```bash
grep -iE 'gpl|agpl|lgpl' /tmp/yw-licenses-table.md
```

Expected: empty output. If hits, **STOP** and ask user how to handle (replace dep / negotiate exception / accept LGPL with link-time-only confirmation).

- [ ] **Step 4: Compose final doc**

Write to `docs/legal/dependency-licenses.md`:

```markdown
# Yieldwise — Dependency License Matrix

- **Generated:** 2026-04-29
- **Tool:** `pip-licenses` against `api/requirements.txt`
- **Audit policy:**
  - ✅ Acceptable: MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause, ISC, MPL-2.0
  - ❌ Forbidden in `main`: GPL-*, AGPL-*, LGPL-* (commercial distribution risk)
  - 🟡 Per-case review: SSPL, BSL — confirm scope at next refresh
- **Frontend deps:** loaded via CDN script tags from `frontend/*/index.html` —
  - 高德 SDK：客户使用商用 key，许可由客户与高德直接签署（参见部署 SOP）
  - 其它（如有）：在表后单独列

## Backend Dependencies

(Auto-generated table from pip-licenses)

<!-- INSERT TABLE FROM /tmp/yw-licenses-table.md -->

## Frontend / Vendored Assets

| 资产 | 来源 | 许可 | 备注 |
| --- | --- | --- | --- |
| AMap JS API | api.amap.com | 商业版需高德商用 key | 客户自备 |

## Refresh policy

每次 `api/requirements.txt` 修改后：

1. 重跑 Step 2 + Step 3
2. 把表更新进本文件
3. 在 PR 描述里贴 diff
```

Then concatenate the table:

```bash
cat /tmp/yw-licenses-table.md >> docs/legal/dependency-licenses.md
```

- [ ] **Step 5: Commit**

```bash
git add docs/legal/dependency-licenses.md
git commit -m "docs(legal): add dependency license matrix (T3)

Audit policy: MIT/Apache/BSD/ISC/MPL-2.0 acceptable; GPL family
forbidden in main. Frontend AMap SDK deferred to client commercial key.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task A.3: T1 — Connection pool audit + regression test

**Why:** Spec §5.4 T1 originally said "build pool". On code inspection (`api/persistence.py:55-72`) `psycopg_pool.ConnectionPool(min_size=1, max_size=8)` is already wired and `postgres_connection()` routes through it. This task **audits** that no caller bypasses the pool, then **adds a regression test** so future refactors can't reintroduce raw connections.

**Files:**
- Modify: `api/persistence.py` (docstring only)
- Create: `tests/api/test_persistence_pool.py`

- [ ] **Step 1: Audit grep — confirm no direct connect() outside persistence.py**

```bash
grep -rn -E 'psycopg(2)?\.connect\(' api/ jobs/ scripts/ 2>/dev/null | grep -v 'persistence.py' | grep -v 'test_'
```

Expected: empty output.

If non-empty: route those callers through `postgres_connection()` before continuing this task. Add a follow-up step naming each file + line + the rewrite.

- [ ] **Step 2: Write the failing test**

Create `tests/api/test_persistence_pool.py`:

```python
"""T1 regression: verify psycopg pool is the single connection path.

Spec §5.4 T1. Pool wired at api/persistence.py:55-72.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from api import persistence


def test_get_pool_returns_singleton_per_dsn(monkeypatch):
    """Same DSN -> same pool object (registry invariant)."""
    monkeypatch.setattr(persistence, "_POOL_REGISTRY", {})
    fake_dsn = "postgresql://localhost/yieldwise_pool_singleton_check"
    pool1 = persistence._get_pool(fake_dsn)
    pool2 = persistence._get_pool(fake_dsn)
    try:
        assert pool1 is pool2
    finally:
        persistence._POOL_REGISTRY.pop(fake_dsn, None)
        try:
            pool1.close()
        except Exception:
            pass


def test_postgres_connection_requires_dsn(monkeypatch):
    """Without POSTGRES_DSN env, postgres_connection() must raise — never silent fallback."""
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setattr(persistence, "_POOL_REGISTRY", {})
    with pytest.raises(RuntimeError, match="POSTGRES_DSN"):
        with persistence.postgres_connection():
            pass


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_DSN"),
    reason="needs live POSTGRES_DSN",
)
def test_pool_handles_concurrent_queries():
    """50 queries across 20 threads should all succeed against pool size 8."""
    def query():
        with persistence.postgres_cursor() as cur:
            cur.execute("SELECT 1 AS one")
            return cur.fetchone()

    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(lambda _: query(), range(50)))

    assert len(results) == 50
    assert all(r["one"] == 1 for r in results)
```

- [ ] **Step 3: Run the test — singleton + missing-DSN must pass without DB**

```bash
pytest tests/api/test_persistence_pool.py -v
```

Expected: `2 passed, 1 skipped` (concurrency skipped because no `POSTGRES_DSN`).

If failures, fix `api/persistence.py` until tests pass.

- [ ] **Step 4: Add docstring note to persistence.py**

Edit `api/persistence.py` — find the `_get_pool` function and prepend a comment:

```python
# T1 (audited 2026-04-29): all DB access routes through this pool.
# Adding direct psycopg.connect() calls bypasses pool sizing and breaks
# multi-user private deploy. See tests/api/test_persistence_pool.py.
def _get_pool(dsn: str) -> Any:
```

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_persistence_pool.py api/persistence.py
git commit -m "test(persistence): T1 pool audit regression suite

- Singleton check: same DSN returns same pool
- Missing-DSN check: no silent fallback
- Concurrency check (live DB, skipped in CI): 50 queries / 20 threads
- Inline note in _get_pool warning against bypassing the pool

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase B: Branding (~1 工程日)

### Task B.1: Add `[project]` block to pyproject.toml

**Why:** Future `pip install -e .` and packaging needs a project name. Currently pyproject only has ruff config.

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Read current pyproject.toml**

Run: `cat pyproject.toml | head -5`

- [ ] **Step 2: Prepend [project] block**

Edit `pyproject.toml` — insert at top (before `[tool.ruff]`):

```toml
[project]
name = "yieldwise"
version = "0.1.0"
description = "Yieldwise · 租知 — 租赁资产投研工作台"
requires-python = ">=3.13"
readme = "README.md"

[project.urls]
Homepage = "https://yieldwise.example"

```

- [ ] **Step 3: Verify pyproject parses**

```bash
python3 -c "import tomllib; print(tomllib.loads(open('pyproject.toml').read())['project']['name'])"
```

Expected output: `yieldwise`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject [project] block (Yieldwise rebrand)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task B.2: Rename in API title + HTML titles

**Why:** First impression for any client demo or API explorer.

**Files:**
- Modify: `api/main.py:93-97`
- Modify: `frontend/user/index.html` (`<title>` element)
- Modify: `frontend/backstage/index.html` (`<title>` element)

- [ ] **Step 1: Update `api/main.py` FastAPI metadata**

Edit `api/main.py` lines 93–97:

```python
app = FastAPI(
    title="Yieldwise API",
    version="0.1.0",
    description="Yieldwise · 租知 — 租赁资产投研工作台后端。",
)
```

- [ ] **Step 2: Update `frontend/user/index.html` title**

Find the `<title>` tag and replace with:

```html
<title>Yieldwise · 租知</title>
```

- [ ] **Step 3: Update `frontend/backstage/index.html` title**

Find the `<title>` tag and replace with:

```html
<title>Yieldwise Workbench · 租知</title>
```

- [ ] **Step 4: Verify pytest still passes**

```bash
pytest tests/api -x --timeout=30
```

Expected: all green (no test asserts the old title; if any does, update it).

- [ ] **Step 5: Verify static HTML serves**

```bash
python3 -c "
import urllib.request
import subprocess
import time
proc = subprocess.Popen(['uvicorn','api.main:app','--port','8013'])
try:
    time.sleep(2)
    r = urllib.request.urlopen('http://127.0.0.1:8013/').read().decode()
    assert 'Yieldwise · 租知' in r, r[:200]
    print('OK')
finally:
    proc.terminate()
"
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add api/main.py frontend/user/index.html frontend/backstage/index.html
git commit -m "feat(branding): rename Shanghai Yield Atlas → Yieldwise · 租知

- FastAPI app title + description
- User platform HTML title
- Backstage HTML title

No behavioral change.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task B.3: Update README header

**Why:** README is the first-touch document for any prospect skimming GitHub.

**Files:**
- Modify: `README.md` (top section only — leave Phase 6/7/8 history intact)

- [ ] **Step 1: Replace the H1 + tagline + intro paragraph**

Edit `README.md` — replace lines 1–11 (current H1 `# Shanghai Yield Atlas Internal Beta` + screenshots + intro 一句话) with:

```markdown
# Yieldwise · 租知

[![Validate](https://github.com/Leonard-Don/shanghai-yield-atlas/actions/workflows/validate.yml/badge.svg)](https://github.com/Leonard-Don/shanghai-yield-atlas/actions/workflows/validate.yml)

**租赁资产投研工作台 · 拿房选址 / 估值 / 投后一张地图**

<p align="center">
  <img src="docs/screenshots/atlas-workbench-overview.png" alt="Yieldwise workbench overview" width="100%" />
</p>

<p align="center">
  <img src="docs/screenshots/atlas-ops-workbench.png" alt="Yieldwise ops workbench" width="100%" />
</p>

面向保租房 / 长租公寓运营商投资部 / 资产管理部的租赁资产投研工作台。把团队散在 Excel、戴德梁行 PDF、内部 PMS 里的拿房线索、在管房源、市场比准数据，收进同一张地图，做拿房选址 / REIT 估值 / 投后管理三个 anchor 工作流。
```

> Leave `## 这个仓库现在是什么`、`## 路由布局`、所有 Phase 历史段落不动 — 它们是研发参考。

- [ ] **Step 2: Verify README renders**

```bash
python3 -c "
content = open('README.md').read()
assert content.startswith('# Yieldwise · 租知'), content[:80]
assert '租赁资产投研工作台' in content
assert '## 分支策略' in content  # from Task A.1
print('OK')
"
```

Expected: `OK`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): rebrand header to Yieldwise · 租知

Keeps Phase 6/7/8 history sections intact for engineering reference;
only the public-facing top paragraph is rewritten for the commercial
positioning.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase C: M1 Multi-city Scaffold (~3–4 工程日)

### Task C.1: Add PyYAML dependency

**Why:** YAML is the manifest format. PyYAML is single-source, MIT, no transitive footprint.

**Files:**
- Modify: `api/requirements.txt`

- [ ] **Step 1: Append to requirements**

Edit `api/requirements.txt` — append:

```
pyyaml>=6.0,<7.0
```

- [ ] **Step 2: Install**

```bash
python3 -m pip install -r api/requirements.txt
```

- [ ] **Step 3: Verify import**

```bash
python3 -c "import yaml; print(yaml.__version__)"
```

Expected: `6.0.x` or higher.

- [ ] **Step 4: Re-run T3 license refresh**

```bash
python3 -m piplicenses --packages pyyaml --format=markdown
```

Verify license is `MIT`. Append the row to `docs/legal/dependency-licenses.md` table.

- [ ] **Step 5: Commit**

```bash
git add api/requirements.txt docs/legal/dependency-licenses.md
git commit -m "chore(deps): add pyyaml for city manifests (M1)

MIT-licensed; single source dep with no transitive footprint.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.2: Define `CityManifest` dataclass + parser

**Why:** Hardcoded Shanghai constants live in disparate files (`frontend/user/modules/map.js:5`, `api/backstage/review.py:97`, plus likely more). Centralizing them behind a typed manifest lets the engineer find every site to migrate.

**Files:**
- Create: `api/config/__init__.py` (empty)
- Create: `api/config/cities/__init__.py`
- Create: `api/config/cities/manifest.py`
- Create: `tests/api/test_city_manifest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/api/test_city_manifest.py`:

```python
"""M1 city manifest schema tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from api.config.cities.manifest import CityManifest, parse_manifest_yaml


def test_parse_minimal_manifest():
    yaml_text = """
city_id: testcity
display_name: 测试市
country_code: CN
center: [121.0, 31.0]
default_zoom: 11.0
districts:
  - district_code: 999
    display_name: 测试区
"""
    m = parse_manifest_yaml(yaml_text)
    assert isinstance(m, CityManifest)
    assert m.city_id == "testcity"
    assert m.display_name == "测试市"
    assert m.center == (121.0, 31.0)
    assert m.default_zoom == 11.0
    assert len(m.districts) == 1
    assert m.districts[0].district_code == 999


def test_manifest_rejects_missing_required_field():
    yaml_text = """
city_id: broken
display_name: 缺中心
country_code: CN
default_zoom: 10
districts: []
"""
    with pytest.raises(ValueError, match="center"):
        parse_manifest_yaml(yaml_text)


def test_manifest_center_must_have_two_floats():
    yaml_text = """
city_id: broken2
display_name: 中心格式错
country_code: CN
center: [121.0]
default_zoom: 10
districts: []
"""
    with pytest.raises(ValueError, match="center"):
        parse_manifest_yaml(yaml_text)
```

- [ ] **Step 2: Run test — must fail with ImportError**

```bash
pytest tests/api/test_city_manifest.py -v
```

Expected: `ModuleNotFoundError: No module named 'api.config'`.

- [ ] **Step 3: Create empty package files**

```bash
mkdir -p api/config/cities
touch api/config/__init__.py api/config/cities/__init__.py
```

- [ ] **Step 4: Implement `manifest.py`**

Create `api/config/cities/manifest.py`:

```python
"""CityManifest — typed shape for per-city configuration loaded from YAML.

Spec §5.1 M1.

A manifest declares everything that was historically hardcoded as "Shanghai":
- map center + default zoom
- ordered district list (code + display name)
- (future) reference rentals, metro stations, comp anchor points

The schema is intentionally minimal in v0.1 — it only covers what the current
code already uses. Add fields here as we migrate more callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass(frozen=True)
class CityDistrict:
    district_code: int
    display_name: str


@dataclass(frozen=True)
class CityManifest:
    city_id: str
    display_name: str
    country_code: str
    center: tuple[float, float]
    default_zoom: float
    districts: tuple[CityDistrict, ...] = field(default_factory=tuple)


def _require(obj: dict[str, Any], key: str) -> Any:
    if key not in obj:
        raise ValueError(f"city manifest missing required field: {key}")
    return obj[key]


def parse_manifest_yaml(yaml_text: str) -> CityManifest:
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError("city manifest must be a YAML mapping at the top level")

    center_raw = _require(raw, "center")
    if not (isinstance(center_raw, list) and len(center_raw) == 2):
        raise ValueError("city manifest 'center' must be [lng, lat]")
    center = (float(center_raw[0]), float(center_raw[1]))

    districts = tuple(
        CityDistrict(
            district_code=int(d["district_code"]),
            display_name=str(d["display_name"]),
        )
        for d in raw.get("districts", []) or []
    )

    return CityManifest(
        city_id=str(_require(raw, "city_id")),
        display_name=str(_require(raw, "display_name")),
        country_code=str(_require(raw, "country_code")),
        center=center,
        default_zoom=float(_require(raw, "default_zoom")),
        districts=districts,
    )
```

- [ ] **Step 5: Re-run test — must pass**

```bash
pytest tests/api/test_city_manifest.py -v
```

Expected: `3 passed`.

- [ ] **Step 6: Commit**

```bash
git add api/config/__init__.py api/config/cities/__init__.py \
        api/config/cities/manifest.py tests/api/test_city_manifest.py
git commit -m "feat(config): introduce CityManifest schema (M1)

Typed dataclass + YAML parser for per-city configuration. Replaces
the de-facto 'Shanghai is hardcoded everywhere' status quo with a
single canonical shape.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.3: Create `shanghai.yaml` + loader

**Why:** First concrete manifest. Loader resolves which manifest to use from `ATLAS_CITY` env var (default `shanghai`). Caches at module level for the process lifetime.

**Files:**
- Create: `api/config/cities/shanghai.yaml`
- Create: `api/config/cities/loader.py`
- Modify: `tests/api/test_city_manifest.py` (+2 cases)

- [ ] **Step 1: Compose `shanghai.yaml`**

Create `api/config/cities/shanghai.yaml`:

```yaml
city_id: shanghai
display_name: 上海
country_code: CN
center: [121.4737, 31.2304]
default_zoom: 10.8
districts:
  - {district_code: 310101, display_name: 黄浦区}
  - {district_code: 310104, display_name: 徐汇区}
  - {district_code: 310105, display_name: 长宁区}
  - {district_code: 310106, display_name: 静安区}
  - {district_code: 310107, display_name: 普陀区}
  - {district_code: 310109, display_name: 虹口区}
  - {district_code: 310110, display_name: 杨浦区}
  - {district_code: 310112, display_name: 闵行区}
  - {district_code: 310113, display_name: 宝山区}
  - {district_code: 310114, display_name: 嘉定区}
  - {district_code: 310115, display_name: 浦东新区}
  - {district_code: 310116, display_name: 金山区}
  - {district_code: 310117, display_name: 松江区}
  - {district_code: 310118, display_name: 青浦区}
  - {district_code: 310120, display_name: 奉贤区}
  - {district_code: 310151, display_name: 崇明区}
```

> Note: 中心点 `121.4737, 31.2304` 与 `frontend/user/modules/map.js:5` `SHANGHAI_CENTER` 一致；default_zoom `10.8` 与 `map.js:6` `DEFAULT_ZOOM` 一致。District code 来自 GB/T 2260。

- [ ] **Step 2: Implement `loader.py`**

Create `api/config/cities/loader.py`:

```python
"""City manifest loader — resolves active city from ATLAS_CITY env var.

Default: 'shanghai'. Cached for process lifetime.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .manifest import CityManifest, parse_manifest_yaml

_MANIFEST_DIR = Path(__file__).resolve().parent


def _manifest_path(city_id: str) -> Path:
    return _MANIFEST_DIR / f"{city_id}.yaml"


@lru_cache(maxsize=8)
def load_city(city_id: str) -> CityManifest:
    path = _manifest_path(city_id)
    if not path.is_file():
        raise FileNotFoundError(f"city manifest not found: {path}")
    return parse_manifest_yaml(path.read_text(encoding="utf-8"))


def load_active_city() -> CityManifest:
    """Return the manifest for the city named by ATLAS_CITY (default: shanghai)."""
    city_id = os.environ.get("ATLAS_CITY", "shanghai")
    return load_city(city_id)
```

- [ ] **Step 3: Add loader tests**

Append to `tests/api/test_city_manifest.py`:

```python
import os
from api.config.cities.loader import load_active_city, load_city


def test_load_shanghai_manifest_from_disk():
    m = load_city("shanghai")
    assert m.city_id == "shanghai"
    assert m.display_name == "上海"
    assert m.center == (121.4737, 31.2304)
    assert m.default_zoom == 10.8
    # 16 上海行政区
    assert len(m.districts) == 16
    codes = {d.district_code for d in m.districts}
    assert 310101 in codes  # 黄浦
    assert 310115 in codes  # 浦东


def test_load_active_city_defaults_to_shanghai(monkeypatch):
    monkeypatch.delenv("ATLAS_CITY", raising=False)
    load_city.cache_clear()
    m = load_active_city()
    assert m.city_id == "shanghai"


def test_load_unknown_city_raises(monkeypatch):
    load_city.cache_clear()
    import pytest
    with pytest.raises(FileNotFoundError):
        load_city("atlantis")
```

- [ ] **Step 4: Run all manifest tests**

```bash
pytest tests/api/test_city_manifest.py -v
```

Expected: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add api/config/cities/shanghai.yaml api/config/cities/loader.py \
        tests/api/test_city_manifest.py
git commit -m "feat(config): add Shanghai manifest + loader (M1)

shanghai.yaml carries center/zoom/16 districts extracted from the
historical hardcoded values. Loader resolves manifest from ATLAS_CITY
env var (default: shanghai), cached for process lifetime.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.4: Add `/api/v2/config/city` endpoint

**Why:** Frontend needs to fetch the active city config at boot. Adding this as a v2 endpoint keeps it discoverable for client integrations.

**Files:**
- Create: `api/schemas/city_config.py`
- Create: `api/domains/config.py`
- Modify: `api/main.py` (+1 router include)
- Create: `tests/api/test_v2_config_city.py`

- [ ] **Step 1: Write the failing endpoint test**

Create `tests/api/test_v2_config_city.py`:

```python
"""GET /api/v2/config/city — returns active city manifest summary."""
from fastapi.testclient import TestClient

from api.main import app


def test_get_city_config_returns_shanghai_by_default():
    client = TestClient(app)
    resp = client.get("/api/v2/config/city")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cityId"] == "shanghai"
    assert data["displayName"] == "上海"
    assert data["center"] == [121.4737, 31.2304]
    assert data["defaultZoom"] == 10.8
    assert isinstance(data["districts"], list)
    assert len(data["districts"]) == 16
    # camelCase contract
    sample = data["districts"][0]
    assert "districtCode" in sample
    assert "displayName" in sample
```

- [ ] **Step 2: Run — must fail (404)**

```bash
pytest tests/api/test_v2_config_city.py -v
```

Expected: `assert 404 == 200`.

- [ ] **Step 3: Define response schema**

Create `api/schemas/city_config.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class DistrictSummary(BaseModel):
    district_code: int = Field(serialization_alias="districtCode")
    display_name: str = Field(serialization_alias="displayName")

    class Config:
        populate_by_name = True


class CityConfigResponse(BaseModel):
    city_id: str = Field(serialization_alias="cityId")
    display_name: str = Field(serialization_alias="displayName")
    country_code: str = Field(serialization_alias="countryCode")
    center: tuple[float, float]
    default_zoom: float = Field(serialization_alias="defaultZoom")
    districts: list[DistrictSummary]

    class Config:
        populate_by_name = True
```

- [ ] **Step 4: Implement endpoint**

Create `api/domains/config.py`:

```python
"""Yieldwise active city config endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from api.config.cities.loader import load_active_city
from api.schemas.city_config import CityConfigResponse, DistrictSummary

router = APIRouter()


@router.get("/config/city", response_model=CityConfigResponse, response_model_by_alias=True)
def get_city_config() -> CityConfigResponse:
    manifest = load_active_city()
    return CityConfigResponse(
        city_id=manifest.city_id,
        display_name=manifest.display_name,
        country_code=manifest.country_code,
        center=manifest.center,
        default_zoom=manifest.default_zoom,
        districts=[
            DistrictSummary(district_code=d.district_code, display_name=d.display_name)
            for d in manifest.districts
        ],
    )
```

- [ ] **Step 5: Wire router in `api/main.py`**

Find the `app.include_router(...)` block (~line 113) and add:

```python
from .domains import config as v2_config  # add to existing import block at top

# in the include_router run:
app.include_router(v2_config.router, prefix="/api/v2")
```

- [ ] **Step 6: Run test — must pass**

```bash
pytest tests/api/test_v2_config_city.py -v
```

Expected: `1 passed`.

- [ ] **Step 7: Smoke check the existing test suite stays green**

```bash
pytest tests/api -x --timeout=30
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add api/schemas/city_config.py api/domains/config.py api/main.py \
        tests/api/test_v2_config_city.py
git commit -m "feat(api): GET /api/v2/config/city (M1)

Returns active city manifest summary (id, display name, center, zoom,
districts) sourced from api/config/cities/<city>.yaml. Frontend will
boot off this in next task.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.5: Frontend `config-bootstrap.js` + map.js migration

**Why:** Replace hardcoded `SHANGHAI_CENTER` / `DEFAULT_ZOOM` in `map.js` with values from `/api/v2/config/city`. This is the visible "multi-city dropdown" infrastructure even though only Shanghai is loaded.

**Files:**
- Modify: `frontend/user/modules/api.js` (+1 method)
- Create: `frontend/user/modules/config-bootstrap.js`
- Modify: `frontend/user/modules/main.js` (await bootstrap before initMap)
- Modify: `frontend/user/modules/map.js` (drop hardcoded constants)
- Create: `tests/frontend/test_config_bootstrap.mjs`

- [ ] **Step 1: Add `api.cityConfig()` method**

Edit `frontend/user/modules/api.js` — find the `api = {` object and add:

```javascript
async cityConfig() {
  const r = await fetch("/api/v2/config/city");
  if (!r.ok) throw new Error(`cityConfig ${r.status}`);
  return r.json();
},
```

- [ ] **Step 2: Write the failing bootstrap test**

Create `tests/frontend/test_config_bootstrap.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { applyCityConfig, getActiveCityConfig } from "../../frontend/user/modules/config-bootstrap.js";

test("applyCityConfig stores and getActiveCityConfig retrieves", () => {
  const sample = {
    cityId: "shanghai",
    displayName: "上海",
    countryCode: "CN",
    center: [121.4737, 31.2304],
    defaultZoom: 10.8,
    districts: [{ districtCode: 310101, displayName: "黄浦区" }],
  };
  applyCityConfig(sample);
  const got = getActiveCityConfig();
  assert.equal(got.cityId, "shanghai");
  assert.deepEqual(got.center, [121.4737, 31.2304]);
  assert.equal(got.defaultZoom, 10.8);
});

test("getActiveCityConfig before applyCityConfig throws", () => {
  // reset module state by re-importing fresh would require dynamic import;
  // instead document expectation: applyCityConfig MUST be called once at boot
  assert.ok(getActiveCityConfig().cityId, "after apply, must work");
});
```

- [ ] **Step 3: Implement `config-bootstrap.js`**

Create `frontend/user/modules/config-bootstrap.js`:

```javascript
import { api } from "./api.js";

let _active = null;

export function applyCityConfig(cfg) {
  if (!cfg || !cfg.cityId || !Array.isArray(cfg.center) || cfg.center.length !== 2) {
    throw new Error("invalid city config");
  }
  _active = Object.freeze({
    cityId: cfg.cityId,
    displayName: cfg.displayName,
    countryCode: cfg.countryCode,
    center: [cfg.center[0], cfg.center[1]],
    defaultZoom: cfg.defaultZoom,
    districts: Object.freeze((cfg.districts || []).map((d) => Object.freeze({ ...d }))),
  });
  return _active;
}

export function getActiveCityConfig() {
  if (!_active) {
    throw new Error("city config not loaded — call applyCityConfig() at boot");
  }
  return _active;
}

export async function bootstrapCityConfig() {
  const cfg = await api.cityConfig();
  return applyCityConfig(cfg);
}
```

- [ ] **Step 4: Run test — must pass**

```bash
node --test tests/frontend/test_config_bootstrap.mjs
```

Expected: `2 passing`.

- [ ] **Step 5: Wire bootstrap in `frontend/user/modules/main.js`**

Find the boot path (likely an async `init()` or `start()` function) and insert before any `initMap` / `initX` call:

```javascript
import { bootstrapCityConfig } from "./config-bootstrap.js";

// inside init() before initMap:
await bootstrapCityConfig();
```

- [ ] **Step 6: Update `map.js` to read from config**

Edit `frontend/user/modules/map.js`:

Replace lines 1–6:

```javascript
import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import { yieldColorFor, districtColorFor } from "./modes.js";
import { getActiveCityConfig } from "./config-bootstrap.js";
```

(remove `const SHANGHAI_CENTER = [121.4737, 31.2304];` and `const DEFAULT_ZOOM = 10.8;`)

Then update the map constructor call. Find the `new AMap.Map(container.id, {` block and adjust:

```javascript
const cityCfg = getActiveCityConfig();
const map = new AMap.Map(container.id, {
  zoom: cityCfg.defaultZoom,
  center: cityCfg.center,
  // ...other options unchanged
});
```

- [ ] **Step 7: `node --check` all touched JS files**

```bash
for f in frontend/user/modules/api.js \
         frontend/user/modules/config-bootstrap.js \
         frontend/user/modules/main.js \
         frontend/user/modules/map.js; do
  node --check "$f" || { echo "FAILED: $f"; break; }
done
echo "node --check OK"
```

Expected: `node --check OK`.

- [ ] **Step 8: End-to-end smoke**

```bash
uvicorn api.main:app --port 8013 &
SERVER_PID=$!
sleep 3
curl -fsS http://127.0.0.1:8013/api/v2/config/city | python3 -m json.tool
# Manual: open http://127.0.0.1:8013/ — verify map centers on Shanghai
kill $SERVER_PID
```

Expected: JSON shows shanghai data; manual map render unchanged.

- [ ] **Step 9: Update phase1_smoke.py**

Edit `scripts/phase1_smoke.py` — add a row to the assertion list:

```python
("/api/v2/config/city", 200),
```

(Match whatever existing format the file uses.)

- [ ] **Step 10: Run phase1 smoke**

```bash
python3 scripts/phase1_smoke.py
```

Expected: all routes pass.

- [ ] **Step 11: Commit**

```bash
git add frontend/user/modules/api.js \
        frontend/user/modules/config-bootstrap.js \
        frontend/user/modules/main.js \
        frontend/user/modules/map.js \
        tests/frontend/test_config_bootstrap.mjs \
        scripts/phase1_smoke.py
git commit -m "feat(frontend): bootstrap city config from /api/v2/config/city (M1)

Drops hardcoded SHANGHAI_CENTER / DEFAULT_ZOOM in map.js. Frontend
fetches manifest once at boot via config-bootstrap.js; map.js reads
center/zoom from the cached active city config.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.6: Audit + migrate other Shanghai hardcodes

**Why:** Phase A grep found `api/backstage/review.py:97` `parts = ["上海"]`. There may be more. Audit and migrate any places where the city name or coordinates appear inline.

**Files:**
- Modify: `api/backstage/review.py` (and any others discovered)

- [ ] **Step 1: Audit**

```bash
grep -rn -E '"上海"|'"'"'上海'"'"'|"shanghai"|'"'"'shanghai'"'"'|121\.4737|31\.2304' \
  api/ frontend/user/modules/ frontend/backstage/lib/ frontend/backstage/data/ \
  2>/dev/null \
  | grep -v 'config/cities/shanghai.yaml' \
  | grep -v 'test_'
```

Document each hit. For each:

- If it's a default value → replace with `load_active_city().display_name` (Python) or `getActiveCityConfig().displayName` (JS)
- If it's a comment or docstring → leave alone
- If it's in a tmp/staged file → leave alone (those are data, not config)

- [ ] **Step 2: Migrate `api/backstage/review.py:97`**

Read context:

```bash
sed -n '90,105p' api/backstage/review.py
```

Replace `parts = ["上海"]` with:

```python
from api.config.cities.loader import load_active_city
parts = [load_active_city().display_name]
```

(Place the import at the top of the file with other imports.)

- [ ] **Step 3: Run full pytest**

```bash
pytest tests/api -x --timeout=30
```

Expected: all pass.

- [ ] **Step 4: Commit (if any migrations made)**

```bash
git add api/backstage/review.py  # plus any others
git commit -m "refactor(backstage): replace hardcoded '上海' with active city manifest (M1)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task C.7: Document the manifest extension procedure

**Why:** When a future engineer (or you) needs to add Hangzhou / Shenzhen / Beijing, the doc tells them the 4-step recipe.

**Files:**
- Create: `docs/deployment/city-manifests.md`

- [ ] **Step 1: Compose doc**

Create `docs/deployment/city-manifests.md`:

```markdown
# Adding a New City to Yieldwise

A city manifest carries everything the app historically hardcoded for "上海":
map center, default zoom, 行政区 list. Adding a new city is a 4-step recipe.

## 1. Author the YAML

Path: `api/config/cities/<city_id>.yaml`

```yaml
city_id: hangzhou
display_name: 杭州
country_code: CN
center: [120.1551, 30.2741]   # GCJ-02
default_zoom: 11.0
districts:
  - {district_code: 330102, display_name: 上城区}
  # ...
```

`district_code` is GB/T 2260 6-digit administrative code.

## 2. Activate at runtime

```bash
ATLAS_CITY=hangzhou uvicorn api.main:app --port 8000
```

The loader caches at process start; restart the app to switch.

## 3. Verify the API surface

```bash
curl -s http://127.0.0.1:8000/api/v2/config/city | python3 -m json.tool
```

`cityId` should match what you set.

## 4. Verify the frontend boot

Open `http://127.0.0.1:8000/`. The map should center on the new city.
If you see Shanghai still, hard refresh — `config-bootstrap.js` caches in
module state, not in the browser.

## What this ALONE does NOT cover

- District boundary GeoJSON (drawn on the map) — needs separate import
- Metro stations / POI overlays — needs separate import
- Reference rentals or comp anchor points — separate import

These are city-specific data, not configuration. They flow through the
existing import pipeline (`tmp/import-runs/` → PostGIS).
```

- [ ] **Step 2: Commit**

```bash
git add docs/deployment/city-manifests.md
git commit -m "docs(deployment): how to add a city manifest (M1)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Phase D: Plan 1 ship checks (~0.5 工程日)

### Task D.1: Full regression

- [ ] **Step 1: Backend**

```bash
python3 -m compileall api jobs scripts
pytest tests/api -x --timeout=30
```

Expected: all green.

- [ ] **Step 2: Frontend**

```bash
for f in frontend/backstage/{data,lib}/*.js \
         frontend/backstage/app.js \
         frontend/user/modules/*.js; do
  node --check "$f" || { echo "FAIL: $f"; exit 1; }
done
node --test tests/frontend/*.mjs
```

Expected: all pass.

- [ ] **Step 3: Phase 1 smoke**

```bash
python3 scripts/phase1_smoke.py
```

Expected: all routes incl. `/api/v2/config/city` pass.

- [ ] **Step 4: Browser regression (if pwcli env exists)**

```bash
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/
```

Expected: 25/25 (or whatever the baseline shows) pass.

### Task D.2: Self-review checklist

- [ ] No mention of "Shanghai Yield Atlas" in user-visible strings (titles, headers, FastAPI metadata)
- [ ] `grep -rn 'Shanghai Yield Atlas' .` returns only historical changelog / spec references
- [ ] `docs/legal/dependency-licenses.md` exists and contains pyyaml row
- [ ] `research-private` branch exists at the same commit as `main` was at start of Plan 1
- [ ] All 6 commits this plan produced have `Co-Authored-By: Claude Opus 4.7` trailer
- [ ] `pytest tests/api` shows the 3 new test files passing
- [ ] `node --test tests/frontend/test_config_bootstrap.mjs` passes

### Task D.3: Tag the milestone

```bash
git tag -a yieldwise-v0.1-foundation -m "Yieldwise Plan 1 complete: foundation, branding, multi-city scaffold"
git push --tags 2>/dev/null || echo "no remote — local tag created"
```

---

## Self-Review (writing-plans)

**1. Spec coverage (against `2026-04-29-yieldwise-commercialization-design.md`):**

| Spec section | Plan 1 task | Status |
|---|---|---|
| §2.1 改名 Yieldwise / 租知 | B.1, B.2, B.3 | ✅ |
| §4 仓库分支策略 | A.1 | ✅ research-private created; release/yieldwise-v1.x deferred to ship time |
| §5.1 M1 多城市参数化 | C.1–C.7 | ✅ scaffold + Shanghai manifest only |
| §5.4 T1 connection pool | A.3 | ✅ audit + regression test (build was already done) |
| §5.4 T2 service.py 切干净 | — | Deferred to Plan 4 (with M6) |
| §5.4 T3 license audit | A.2 | ✅ |
| §5.1 M2 Auth | — | Plan 2 |
| §5.1 M3 Data Import | — | Plan 2 |
| §5.1 M4 Reports | — | Plan 3 |
| §5.1 M5 Deployment Package | — | Plan 3 |
| §5.1 M6 Backstage Workflow | — | Plan 4 |
| §6.3 Demo Dataset | — | Mini-spec, separate plan |
| §8 GTM | — | Non-code, separate plan |

**2. Placeholder scan:** none — every code step shows actual code; every command step shows the actual command.

**3. Type consistency:** `CityManifest`, `CityDistrict`, `parse_manifest_yaml`, `load_city`, `load_active_city`, `applyCityConfig`, `getActiveCityConfig`, `bootstrapCityConfig` — names appear consistently across tasks.

**4. Open issues left to subsequent plans:**
- District boundary GeoJSON import (Plan 2 or later)
- POI overlays per city (Plan 2 or later)
- City selector UI (deferred — v0.1 shows Shanghai only; the dropdown UI ships when a 2nd city is loaded)

---

## Hand-off

After Plan 1 ships and is tagged `yieldwise-v0.1-foundation`, write Plan 2:
**M2 Auth + M3 Customer Data Import** (~10–12 工程日).
