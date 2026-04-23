# Phase 1 — Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the existing research workbench to `/backstage`, stand up an empty D1-styled user shell at `/`, create the `api/domains/` and `api/backstage/` directory skeleton with a working `/api/v2/health` endpoint, add a pytest baseline and update CI.

**Architecture:** Two static mounts (backstage under `/backstage`, user platform under `/`). Existing `/api/*` endpoints stay where they are (untouched). New `/api/v2/*` endpoints live under `api/domains/`. All legacy features continue to work unchanged — this phase only rearranges files, adds two new directories, and introduces one health endpoint.

**Tech Stack:** FastAPI · vanilla ES modules · pytest · httpx (for TestClient) · no build tools introduced.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md`

---

## File Structure (Phase 1 outcome)

```
api/
├── main.py                   # MODIFIED: mount /backstage and / separately; include v2 router; favicon route
├── domains/                  # NEW
│   ├── __init__.py
│   └── health.py             # /api/v2/health
├── backstage/                # NEW (empty reservation for Phase 2)
│   └── __init__.py
├── service.py                # unchanged
├── persistence.py            # unchanged
├── provider_adapters.py      # unchanged
├── reference_catalog.py      # unchanged
├── mock_data.py              # unchanged
├── env.py                    # unchanged
├── requirements.txt          # unchanged
└── requirements-dev.txt      # NEW: pytest + httpx

frontend/                     # NEW
├── backstage/
│   ├── index.html            # MOVED from project root
│   ├── styles.css            # MOVED from project root
│   └── app.js                # MOVED from project root
└── user/
    ├── index.html            # NEW: D1 shell skeleton
    ├── styles/
    │   ├── tokens.css        # NEW: D1 color/typography variables
    │   └── shell.css         # NEW: topbar/map/board grid layout
    └── modules/
        └── main.js           # NEW: tiny bootstrap logger

tests/                        # NEW
├── __init__.py
├── conftest.py               # TestClient fixture
├── test_canary.py            # baseline sanity test
└── api/
    ├── __init__.py
    ├── test_routing.py       # /backstage and / serve correct HTML
    └── test_v2_health.py     # /api/v2/health returns ok

scripts/
├── full_browser_regression.py   # MODIFIED: default --url points at /backstage/
└── phase1_smoke.py              # NEW: lightweight route sanity for local + CI

.github/workflows/validate.yml    # MODIFIED: pytest step + updated node --check path

pytest.ini                    # NEW: test discovery config
README.md                     # MODIFIED: document / and /backstage split
```

**Files removed from project root:** `index.html`, `styles.css`, `app.js` (moved into `frontend/backstage/`). `favicon.svg`, `favicon.ico`, `assets/shanghai-districts-reference.svg` stay at root (favicon served via explicit route; assets/* is currently unreferenced in source code and kept for reference material).

---

### Task 1: Add pytest baseline with canary test

**Files:**
- Create: `api/requirements-dev.txt`
- Create: `pytest.ini`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_canary.py`
- Create: `tests/api/__init__.py`

- [ ] **Step 1: Create dev requirements file**

Write `api/requirements-dev.txt`:

```
-r requirements.txt
pytest>=8.0,<9.0
httpx>=0.27,<1.0
```

- [ ] **Step 2: Install dev deps locally**

Run: `pip install -r api/requirements-dev.txt`
Expected: pytest and httpx installed without errors.

- [ ] **Step 3: Create pytest config**

Write `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -q --tb=short
```

- [ ] **Step 4: Create empty package files**

Write `tests/__init__.py` (empty).
Write `tests/api/__init__.py` (empty).

- [ ] **Step 5: Create shared conftest with TestClient fixture**

Write `tests/conftest.py`:

```python
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
```

- [ ] **Step 6: Write the canary test**

Write `tests/test_canary.py`:

```python
def test_canary():
    assert True
```

- [ ] **Step 7: Run pytest**

Run: `pytest -q`
Expected: `1 passed` (the canary).

- [ ] **Step 8: Commit**

```bash
git add api/requirements-dev.txt pytest.ini tests/
git commit -m "test: add pytest baseline with canary"
```

---

### Task 2: Write failing test for /backstage route

**Files:**
- Create: `tests/api/test_routing.py`

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_routing.py`:

```python
from __future__ import annotations


def test_backstage_index_serves_workbench(client) -> None:
    response = client.get("/backstage/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>Shanghai Yield Atlas</title>" in body
    assert 'src="./app.js"' in body, "backstage page must load the legacy app bundle"


def test_backstage_assets_resolve(client) -> None:
    assert client.get("/backstage/styles.css").status_code == 200
    assert client.get("/backstage/app.js").status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_routing.py -v`
Expected: FAIL — currently `/` (not `/backstage/`) serves the workbench, so these return 404.

---

### Task 3: Migrate workbench files + mount /backstage + favicon route

**Files:**
- Create: `frontend/backstage/index.html` (moved from `/index.html`)
- Create: `frontend/backstage/styles.css` (moved from `/styles.css`)
- Create: `frontend/backstage/app.js` (moved from `/app.js`)
- Modify: `api/main.py:833` (replace root static mount)

- [ ] **Step 1: Move workbench files**

Run:

```bash
mkdir -p frontend/backstage
git mv index.html frontend/backstage/index.html
git mv styles.css frontend/backstage/styles.css
git mv app.js frontend/backstage/app.js
```

Expected: `git status` shows three renames.

- [ ] **Step 2a: Add FileResponse import**

At the top of `api/main.py`, alongside the existing FastAPI imports, add:

```python
from fastapi.responses import FileResponse
```

So that block becomes:

```python
from fastapi import Body, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
```

- [ ] **Step 2b: Replace the root static mount at line 833**

Delete the current final line of `api/main.py`:

```python
app.mount("/", StaticFiles(directory=ROOT_DIR, html=True), name="static")
```

Replace it with:

```python
FRONTEND_DIR = ROOT_DIR / "frontend"


@app.get("/favicon.svg", include_in_schema=False)
def favicon_svg() -> FileResponse:
    return FileResponse(ROOT_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico() -> FileResponse:
    return FileResponse(ROOT_DIR / "favicon.ico", media_type="image/x-icon")


app.mount(
    "/backstage",
    StaticFiles(directory=FRONTEND_DIR / "backstage", html=True),
    name="backstage",
)
```

Note: for this task, only `/backstage` serves files; `/` will 404 until Task 5 adds the user shell mount.

- [ ] **Step 3: Run the routing test**

Run: `pytest tests/api/test_routing.py::test_backstage_index_serves_workbench tests/api/test_routing.py::test_backstage_assets_resolve -v`
Expected: PASS for both.

- [ ] **Step 4: Manual browser check**

Run in one terminal: `uvicorn api.main:app --port 8013`
In a browser, open: `http://127.0.0.1:8013/backstage/`
Expected: the existing research workbench loads fully (map, panels, data). Console has no 404 errors.

- [ ] **Step 5: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0 with no errors.

- [ ] **Step 6: Commit**

```bash
git add api/main.py frontend/backstage/
git commit -m "feat: move research workbench to /backstage route"
```

---

### Task 4: Write failing test for user shell at /

**Files:**
- Modify: `tests/api/test_routing.py` (append new tests)

- [ ] **Step 1: Append the failing tests**

Append to `tests/api/test_routing.py`:

```python
def test_user_shell_serves_html(client) -> None:
    response = client.get("/")
    assert response.status_code == 200, response.text
    body = response.text
    assert "<title>" in body
    assert "Shanghai Yield Atlas" in body
    assert 'data-user-shell="atlas"' in body, "user shell must mark its root element"


def test_user_shell_modules_resolve(client) -> None:
    assert client.get("/styles/tokens.css").status_code == 200
    assert client.get("/styles/shell.css").status_code == 200
    assert client.get("/modules/main.js").status_code == 200
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `pytest tests/api/test_routing.py::test_user_shell_serves_html tests/api/test_routing.py::test_user_shell_modules_resolve -v`
Expected: FAIL — `/` currently has no mount so returns 404 on all four URLs.

---

### Task 5: Create D1 user shell skeleton + mount /

**Files:**
- Create: `frontend/user/index.html`
- Create: `frontend/user/styles/tokens.css`
- Create: `frontend/user/styles/shell.css`
- Create: `frontend/user/modules/main.js`
- Modify: `api/main.py` (append user shell mount AFTER the backstage mount)

- [ ] **Step 1: Create the D1 design tokens**

Write `frontend/user/styles/tokens.css`:

```css
:root {
  --bg-0: #070a10;
  --bg-1: #0a0e14;
  --bg-2: #0f1823;
  --line: #1a2332;
  --text-0: #cfd6e0;
  --text-dim: #7a8494;
  --text-xs: #5a6a80;
  --up: #00d68f;
  --down: #ff4d4d;
  --warn: #ffb020;
  --radius-sm: 4px;
  --radius-md: 6px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --font-ui: "Inter", system-ui, -apple-system, sans-serif;
  --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, monospace;
}

html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  background: var(--bg-0);
  color: var(--text-0);
  font-family: var(--font-ui);
  font-size: 13px;
  line-height: 1.5;
}

* {
  box-sizing: border-box;
}

.mono {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.up { color: var(--up); }
.down { color: var(--down); }
.warn { color: var(--warn); }
.dim { color: var(--text-dim); }
```

- [ ] **Step 2: Create the shell layout skeleton CSS**

Write `frontend/user/styles/shell.css`:

```css
.atlas-shell {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  height: 100vh;
}

.atlas-topbar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--bg-1);
}

.atlas-topbar h1 {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.atlas-filterbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-bottom: 1px solid var(--line);
  background: var(--bg-1);
  font-size: 11px;
  color: var(--text-dim);
}

.atlas-main {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  overflow: hidden;
}

.atlas-map {
  background: var(--bg-0);
  border-right: 1px solid var(--line);
  position: relative;
}

.atlas-board {
  background: var(--bg-0);
  overflow-y: auto;
}

.atlas-statusbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 5px 14px;
  border-top: 1px solid var(--line);
  background: var(--bg-1);
  font-size: 10px;
  color: var(--text-dim);
}

.atlas-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-xs);
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}
```

- [ ] **Step 3: Create the user shell HTML**

Write `frontend/user/index.html`:

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
  </head>
  <body data-user-shell="atlas">
    <div class="atlas-shell">
      <header class="atlas-topbar">
        <h1>Shanghai · Yield · Atlas</h1>
      </header>
      <div class="atlas-filterbar"><span>筛选条位置</span></div>
      <main class="atlas-main">
        <section class="atlas-map"><div class="atlas-placeholder">地图</div></section>
        <aside class="atlas-board"><div class="atlas-placeholder">机会榜</div></aside>
      </main>
      <footer class="atlas-statusbar">
        <span class="mono">Phase 1 scaffold · platform shell</span>
      </footer>
    </div>
    <script type="module" src="/modules/main.js"></script>
  </body>
</html>
```

- [ ] **Step 4: Create the bootstrap module**

Write `frontend/user/modules/main.js`:

```javascript
const root = document.querySelector('[data-user-shell="atlas"]');
if (!root) {
  console.error("[atlas] user shell root not found");
} else {
  console.info("[atlas] user shell bootstrap ok");
}
```

- [ ] **Step 5: Mount the user shell in api/main.py**

Append at the very end of `api/main.py` (after the `/backstage` mount):

```python
app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR / "user", html=True),
    name="user",
)
```

Order note: the `/backstage` mount is registered first, so it takes precedence for any `/backstage/...` request. The `/` catch-all comes last.

- [ ] **Step 6: Run the failing tests to verify they pass**

Run: `pytest tests/api/test_routing.py -v`
Expected: all four routing tests pass.

- [ ] **Step 7: Manual browser check**

Restart uvicorn, open `http://127.0.0.1:8013/`.
Expected: dark D1 shell with "Shanghai · Yield · Atlas" top bar, "筛选条位置" row, "地图" + "机会榜" placeholders, footer "Phase 1 scaffold · platform shell". Console shows `[atlas] user shell bootstrap ok`.

Also open `http://127.0.0.1:8013/backstage/` — workbench should still work.

- [ ] **Step 8: Commit**

```bash
git add frontend/user/ api/main.py
git commit -m "feat: stand up D1 user shell skeleton at /"
```

---

### Task 6: Write failing test for /api/v2/health

**Files:**
- Create: `tests/api/test_v2_health.py`

- [ ] **Step 1: Write the failing test**

Write `tests/api/test_v2_health.py`:

```python
from __future__ import annotations


def test_v2_health_returns_ok(client) -> None:
    response = client.get("/api/v2/health")
    assert response.status_code == 200, response.text
    assert response.json() == {"status": "ok", "surface": "user-platform-v2"}


def test_v2_health_is_independent_of_legacy_health(client) -> None:
    legacy = client.get("/api/health")
    v2 = client.get("/api/v2/health")
    assert legacy.status_code == 200
    assert v2.status_code == 200
    assert legacy.json() != v2.json(), "v2 health must be distinguishable from legacy health"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_v2_health.py -v`
Expected: FAIL — no `/api/v2/health` route exists yet (404).

---

### Task 7: Create api/domains/ with health router

**Files:**
- Create: `api/domains/__init__.py`
- Create: `api/domains/health.py`
- Modify: `api/main.py` (include_router at `/api/v2`)

- [ ] **Step 1: Create the domains package**

Write `api/domains/__init__.py` (empty).

- [ ] **Step 2: Implement the health router**

Write `api/domains/health.py`:

```python
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def v2_health() -> dict[str, str]:
    return {"status": "ok", "surface": "user-platform-v2"}
```

- [ ] **Step 3: Wire the router into api/main.py**

In `api/main.py`, add this import near the other imports (right under the existing `from .service import (...)` block):

```python
from .domains import health as v2_health
```

Then, after the `@app.get("/api/health")` definition (near line 89) and before any other route, add:

```python
app.include_router(v2_health.router, prefix="/api/v2")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/api/test_v2_health.py -v`
Expected: both tests pass.

- [ ] **Step 5: Compile check + full test run**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: all tests so far pass (canary + routing + v2 health = 7 tests).

- [ ] **Step 6: Commit**

```bash
git add api/domains/ api/main.py
git commit -m "feat: add /api/v2/health via api/domains/ package"
```

---

### Task 8: Reserve api/backstage/ directory for Phase 2

**Files:**
- Create: `api/backstage/__init__.py`

- [ ] **Step 1: Create the reservation package with a header comment**

Write `api/backstage/__init__.py`:

```python
"""
Backstage (research-tool) domain modules.

Populated in Phase 2: functions currently living in api/service.py that
serve /backstage will be migrated here (runs.py, review.py, geo_qa.py,
anchors.py). Phase 1 only establishes the directory so imports and
module boundaries are fixed before the mechanical migration starts.
"""
```

- [ ] **Step 2: Compile check**

Run: `python3 -m compileall api`
Expected: exit 0.

- [ ] **Step 3: Commit**

```bash
git add api/backstage/
git commit -m "chore: reserve api/backstage/ package for phase 2 migration"
```

---

### Task 9: Create phase1 smoke script

**Files:**
- Create: `scripts/phase1_smoke.py`

- [ ] **Step 1: Write the smoke script**

Write `scripts/phase1_smoke.py`:

```python
"""Phase 1 smoke: boot uvicorn in a subprocess, hit the four key routes,
assert each response, then shut down.

Run:
    python3 scripts/phase1_smoke.py
    python3 scripts/phase1_smoke.py --port 8014
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


def wait_for_server(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except URLError as err:
            last_err = err
        time.sleep(0.2)
    raise TimeoutError(f"server at {url} did not come up within {timeout}s: {last_err}")


def fetch(url: str) -> tuple[int, str]:
    with urlopen(url, timeout=5.0) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"

    proc = subprocess.Popen(
        ["uvicorn", "api.main:app", "--port", str(args.port), "--log-level", "warning"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server(f"{base}/api/health")

        checks = [
            (f"{base}/", 'data-user-shell="atlas"'),
            (f"{base}/backstage/", "<title>Shanghai Yield Atlas</title>"),
            (f"{base}/api/v2/health", '"surface":"user-platform-v2"'),
            (f"{base}/api/health", '"status":"ok"'),
        ]
        failed: list[str] = []
        for url, expected_substring in checks:
            status, body = fetch(url)
            ok = status == 200 and expected_substring in body
            line = f"[{status}] {url}  expect {expected_substring!r} -> {'OK' if ok else 'FAIL'}"
            print(line)
            if not ok:
                failed.append(url)

        if failed:
            print(f"\nFAIL ({len(failed)} routes):", ", ".join(failed))
            return 1
        print("\nPhase 1 smoke OK")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it**

Run: `python3 scripts/phase1_smoke.py`
Expected: four `[200] ... OK` lines, then `Phase 1 smoke OK`, exit 0.

- [ ] **Step 3: Commit**

```bash
git add scripts/phase1_smoke.py
git commit -m "test: add phase1 route smoke script"
```

---

### Task 10: Update full_browser_regression default URL

**Files:**
- Modify: `scripts/full_browser_regression.py:1589`

- [ ] **Step 1: Update the argparse default**

Open `scripts/full_browser_regression.py`, find line 1589:

```python
    parser.add_argument("--url", default="http://127.0.0.1:8013")
```

Replace with:

```python
    parser.add_argument("--url", default="http://127.0.0.1:8013/backstage/")
```

- [ ] **Step 2: Verify the script still compiles**

Run: `python3 -m compileall scripts/full_browser_regression.py`
Expected: exit 0.

- [ ] **Step 3: Spot-run (optional, takes a few minutes)**

Only run this step if Playwright is installed and the user wants to spot-check. Otherwise skip — CI and manual browser checks from Tasks 3 and 5 already covered the critical paths.

```bash
uvicorn api.main:app --port 8013 &
sleep 2
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/backstage/
kill %1
```

Expected: regression reaches its normal conclusion (the script's existing exit behavior).

- [ ] **Step 4: Commit**

```bash
git add scripts/full_browser_regression.py
git commit -m "test: point full_browser_regression at /backstage/ default"
```

---

### Task 11: Update CI workflow

**Files:**
- Modify: `.github/workflows/validate.yml`

- [ ] **Step 1: Rewrite the workflow**

Replace the entire contents of `.github/workflows/validate.yml` with:

```yaml
name: Validate

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install Python deps
        run: pip install -r api/requirements-dev.txt

      - name: Python compile check
        run: python3 -m compileall api jobs scripts

      - name: Backstage JS syntax check
        run: node --check frontend/backstage/app.js

      - name: User shell JS syntax check
        run: node --check frontend/user/modules/main.js

      - name: Pytest
        run: pytest -q

      - name: Phase 1 route smoke
        run: python3 scripts/phase1_smoke.py
```

- [ ] **Step 2: Verify the workflow locally (fast pieces only)**

Run: `python3 -m compileall api jobs scripts`
Expected: exit 0.

Run: `node --check frontend/backstage/app.js`
Expected: exit 0.

Run: `node --check frontend/user/modules/main.js`
Expected: exit 0.

Run: `pytest -q`
Expected: all tests pass.

Run: `python3 scripts/phase1_smoke.py`
Expected: all four routes OK.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/validate.yml
git commit -m "ci: validate both frontends, run pytest + phase1 smoke"
```

---

### Task 12: Document route split in README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add a "路由布局" section near the top**

Insert immediately after the `## 这个仓库现在是什么` section in `README.md`:

```markdown
## 路由布局（Phase 1 起）

| 路径 | 绑定 | 说明 |
| --- | --- | --- |
| `/` | `frontend/user/` | 面向用户的研究平台（Phase 1 为空壳，后续 phase 填入） |
| `/backstage` | `frontend/backstage/` | 原研究台，所有运营/复核/几何 QA 在此 |
| `/api/*` | `api/service.py` + `api/backstage/`（Phase 2 迁移） | 传统接口，backstage 前端使用 |
| `/api/v2/*` | `api/domains/` | 用户平台专属接口 |

要直接打开研究台请访问 `http://127.0.0.1:8000/backstage/`。`/` 在 Phase 1 结束时是一个空的 D1 shell。
```

- [ ] **Step 2: Update the "30 秒启动" section**

Find the existing "30 秒启动" block:

```markdown
## 30 秒启动

\`\`\`bash
uvicorn api.main:app --reload --port 8000
\`\`\`

打开 [http://127.0.0.1:8000](http://127.0.0.1:8000)。
```

Replace with:

```markdown
## 30 秒启动

\`\`\`bash
uvicorn api.main:app --reload --port 8000
\`\`\`

- 用户平台：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 研究台（原主页）：[http://127.0.0.1:8000/backstage/](http://127.0.0.1:8000/backstage/)
```

(If the exact text differs, match what's there — the point is to list both URLs.)

- [ ] **Step 3: Update the "最短路径" validation block**

Find the block with `node --check app.js` and `python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/`. Replace both to match the new paths:

```bash
python3 -m compileall api jobs scripts
node --check frontend/backstage/app.js
python3 scripts/phase1_smoke.py
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/backstage/
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: document / vs /backstage route split"
```

---

## Phase 1 Exit Criteria

Run each of the following and confirm success before declaring Phase 1 complete:

- [ ] `pytest -q` — all tests pass (7 tests: 1 canary, 4 routing, 2 v2 health)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `node --check frontend/user/modules/main.js` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — all four routes OK
- [ ] Manual: `uvicorn api.main:app --port 8013`, open `/` in browser, see D1 shell with placeholders, console log `[atlas] user shell bootstrap ok`
- [ ] Manual: open `/backstage/`, verify the workbench loads fully (map, data, panels) — no regressions
- [ ] `git log --oneline` shows 8 focused commits (one per task that changed code)

## Out of Scope (deferred to Phase 2+)

- Any actual content in `/` beyond the D1 shell skeleton
- Any migration of functions out of `api/service.py` — the file is untouched in Phase 1
- Any new endpoints under `/api/v2/*` beyond `/health`
- `data/personal/` directory and personalization files
- Keyboard shortcuts, drawers, modes, search
