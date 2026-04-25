# Phase 3c-1 — User Prefs Backend (Personal-Data Layer + /api/v2/user/prefs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the first piece of the personal-data layer: a JSON-on-disk storage utility (`fcntl.flock` + `.trash/` backup rotation) plus the `/api/v2/user/prefs` GET/PATCH endpoints backed by a Pydantic `UserPrefs` schema. The frontend Home onboarding modal consuming these endpoints is Phase 3c-2 — this plan ships only the backend so it can be tested and merged independently.

**Architecture:** New `api/personal_storage.py` is a small generic file-storage helper (read_json / write_json / rotate_trash) that future domains (watchlist, annotations, alerts) will reuse. Pydantic schemas live under `api/schemas/`. Domain logic in `api/domains/user_prefs.py` is a thin wrapper: GET reads + validates (returns empty defaults on missing/corrupt), PATCH merges + revalidates + writes. Data lives in `data/personal/` (gitignored). Tests monkey-patch the data directory via the `ATLAS_PERSONAL_DATA_DIR` env var so each pytest run gets a clean tmp_path.

**Tech Stack:** FastAPI · Pydantic 2.9 (already in deps) · Python `fcntl` (POSIX file locking — macOS + Linux) · pytest + httpx TestClient. No new dependencies.

**Parent spec:** `docs/superpowers/specs/2026-04-23-user-facing-platform-design.md` (section 6 数据模型与个人化层 + section 6 Schemas + API table for `/api/v2/user/prefs`)

**Prior plans:** 2026-04-24-phase-3b-filter-bar.md (merged at `f213640`)

---

## File Structure (Phase 3c-1 outcome)

```
api/
├── main.py                    # MODIFIED: include_router for v2_user_prefs
├── personal_storage.py        # NEW — generic JSON read/write with flock + .trash/ backup
├── schemas/                   # NEW directory
│   ├── __init__.py            # NEW (empty)
│   └── user_prefs.py          # NEW — UserPrefs + UserPrefsPatch pydantic models
└── domains/
    └── user_prefs.py          # NEW — GET + PATCH /api/v2/user/prefs

data/
└── personal/                  # NEW (gitignored — created at runtime)

tests/api/
├── test_personal_storage.py   # NEW — flock, backup rotation, corrupt JSON
├── test_user_prefs_schema.py  # NEW — pydantic validation
└── test_v2_user_prefs.py      # NEW — GET / PATCH via TestClient

.gitignore                      # MODIFIED: add data/personal/
scripts/phase1_smoke.py         # MODIFIED: +1 row asserting GET /api/v2/user/prefs returns 200
README.md                       # MODIFIED: bump Phase 3b → Phase 3c-1; expand v2 row endpoint list
```

**Out-of-scope (deferred to Phase 3c-2 and later):**
- Frontend Home onboarding modal — Phase 3c-2
- Wiring `home` mode default filters to user_prefs — Phase 3c-2
- Watchlist / annotations / alerts (each adds its own JSON file under `data/personal/` reusing this same storage utility) — Phase 4 / Phase 5
- District-set filter on `/api/v2/opportunities` — needs a v2 contract change; current endpoint accepts only single `district` param. Phase 3c-2 will negotiate this if needed.
- Cross-field validators on UserPrefs (e.g., budget_min ≤ budget_max). Phase 3c-2 adds them once the onboarding form pins down exact UX.

---

## Pre-Phase Setup

- [ ] **Create the worktree** (run from main repo root)

```bash
git worktree add -b feature/phase-3c-1-user-prefs-backend .worktrees/phase-3c-1-user-prefs-backend
cd .worktrees/phase-3c-1-user-prefs-backend
```

- [ ] **Verify baseline**

```bash
pytest -q
node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs
python3 scripts/phase1_smoke.py
```

Expected: 20 pytest, 38 node tests, 11 smoke routes — all green. If anything fails, stop — Phase 3b should be merged cleanly first.

---

### Task 1: `api/personal_storage.py` + tests

**Files:**
- Create: `api/personal_storage.py`
- Create: `tests/api/test_personal_storage.py`

This is a pure-Python utility: read JSON / write JSON, copy the prior version into `.trash/<timestamp>-<filename>` before each write, keep at most 20 history files, and use `fcntl.flock` on a per-file lock file with one retry on `BlockingIOError`.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_personal_storage.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from api import personal_storage


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_read_returns_none_when_file_missing(data_dir: Path) -> None:
    assert personal_storage.read_json("missing.json") is None


def test_write_then_read_roundtrip(data_dir: Path) -> None:
    payload = {"budget_max_wan": 1500, "districts": ["pudong"]}
    personal_storage.write_json("user_prefs.json", payload)
    assert personal_storage.read_json("user_prefs.json") == payload


def test_write_creates_data_dir_if_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "nested" / "personal"
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(target))
    personal_storage.write_json("user_prefs.json", {"a": 1})
    assert (target / "user_prefs.json").is_file()


def test_write_backs_up_existing_file_to_trash(data_dir: Path) -> None:
    personal_storage.write_json("user_prefs.json", {"v": 1})
    personal_storage.write_json("user_prefs.json", {"v": 2})
    trash_files = sorted((data_dir / ".trash").glob("*-user_prefs.json"))
    assert len(trash_files) == 1
    backed = json.loads(trash_files[0].read_text(encoding="utf-8"))
    assert backed == {"v": 1}


def test_trash_rotation_keeps_at_most_twenty(data_dir: Path) -> None:
    for i in range(25):
        personal_storage.write_json("user_prefs.json", {"v": i})
    trash_files = list((data_dir / ".trash").glob("*-user_prefs.json"))
    assert len(trash_files) == 20


def test_read_returns_none_on_corrupt_json(data_dir: Path) -> None:
    bad = data_dir / "user_prefs.json"
    bad.write_text("{not valid", encoding="utf-8")
    assert personal_storage.read_json("user_prefs.json") is None


def test_write_uses_atomic_rename(data_dir: Path) -> None:
    personal_storage.write_json("user_prefs.json", {"a": 1})
    # No leftover *.tmp file should remain.
    leftovers = list(data_dir.glob("*.tmp"))
    assert leftovers == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/api/test_personal_storage.py -v`
Expected: ImportError or ModuleNotFoundError — `api.personal_storage` doesn't exist yet.

- [ ] **Step 3: Implement `api/personal_storage.py`**

```python
from __future__ import annotations

import fcntl
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT_DIR / "data" / "personal"
TRASH_DIRNAME = ".trash"
TRASH_RETENTION = 20
LOCK_RETRY_DELAY_S = 0.05


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_PERSONAL_DATA_DIR")
    return Path(override) if override else DEFAULT_DATA_DIR


def read_json(filename: str) -> dict[str, Any] | None:
    path = _data_dir() / filename
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def write_json(filename: str, payload: dict[str, Any]) -> None:
    base = _data_dir()
    base.mkdir(parents=True, exist_ok=True)
    trash = base / TRASH_DIRNAME
    trash.mkdir(parents=True, exist_ok=True)
    target = base / filename
    lock_path = base / f".{filename}.lock"

    for attempt in (1, 2):
        lock_fd = open(lock_path, "w")
        try:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_fd.close()
                if attempt == 2:
                    raise
                time.sleep(LOCK_RETRY_DELAY_S)
                continue

            try:
                if target.is_file():
                    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")[:-3]
                    backup_name = f"{timestamp}-{filename}"
                    shutil.copy2(target, trash / backup_name)
                    _rotate_trash(trash, filename, TRASH_RETENTION)

                tmp_path = target.with_suffix(target.suffix + ".tmp")
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
                os.replace(tmp_path, target)
            finally:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()
            return
        except Exception:
            try:
                lock_fd.close()
            except Exception:
                pass
            raise


def _rotate_trash(trash_dir: Path, filename: str, keep: int) -> None:
    matches = sorted(trash_dir.glob(f"*-{filename}"), reverse=True)
    for old in matches[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/api/test_personal_storage.py -v`
Expected: 7 tests pass.

- [ ] **Step 5: Compile + full suite sanity**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 27 passed (20 prior + 7 new).

- [ ] **Step 6: Commit**

```bash
git add api/personal_storage.py tests/api/test_personal_storage.py
git commit -m "feat(api): add personal-data JSON storage with flock + trash rotation"
```

---

### Task 2: `api/schemas/user_prefs.py` + tests

**Files:**
- Create: `api/schemas/__init__.py` (empty)
- Create: `api/schemas/user_prefs.py`
- Create: `tests/api/test_user_prefs_schema.py`

Two pydantic models:
- `UserPrefs` — full record with `budget_min_wan`, `budget_max_wan`, `districts`, `area_min_sqm`, `area_max_sqm`, `office_anchor`, `updated_at`. All fields optional (a fresh user has nothing set).
- `UserPrefsPatch` — same shape, but with `model_config = ConfigDict(extra="forbid")` so the API rejects unknown fields with 422.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_user_prefs_schema.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.user_prefs import UserPrefs, UserPrefsPatch


def test_user_prefs_empty_is_valid() -> None:
    prefs = UserPrefs()
    dump = prefs.model_dump()
    for key in (
        "budget_min_wan",
        "budget_max_wan",
        "districts",
        "area_min_sqm",
        "area_max_sqm",
        "office_anchor",
        "updated_at",
    ):
        assert key in dump


def test_user_prefs_districts_default_is_empty_list() -> None:
    prefs = UserPrefs()
    assert prefs.districts == []


def test_user_prefs_round_trips_full_payload() -> None:
    payload = {
        "budget_min_wan": 500,
        "budget_max_wan": 1500,
        "districts": ["pudong", "jingan"],
        "area_min_sqm": 60,
        "area_max_sqm": 120,
        "office_anchor": {"lng": 121.5, "lat": 31.2, "label": "lujiazui"},
        "updated_at": "2026-04-24T10:00:00",
    }
    prefs = UserPrefs.model_validate(payload)
    assert prefs.budget_max_wan == 1500
    assert prefs.districts == ["pudong", "jingan"]
    assert prefs.office_anchor == {"lng": 121.5, "lat": 31.2, "label": "lujiazui"}


def test_user_prefs_patch_accepts_partial_payload() -> None:
    patch = UserPrefsPatch.model_validate({"budget_max_wan": 1200})
    update = patch.model_dump(exclude_unset=True)
    assert update == {"budget_max_wan": 1200}


def test_user_prefs_patch_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        UserPrefsPatch.model_validate({"budget_max_wan": 1200, "evil": True})


def test_user_prefs_patch_empty_object_is_valid() -> None:
    patch = UserPrefsPatch.model_validate({})
    assert patch.model_dump(exclude_unset=True) == {}


def test_user_prefs_negative_budget_rejected() -> None:
    with pytest.raises(ValidationError):
        UserPrefs.model_validate({"budget_max_wan": -1})
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/api/test_user_prefs_schema.py -v`
Expected: ImportError — `api.schemas.user_prefs` doesn't exist yet.

- [ ] **Step 3: Create the package + module**

Write `api/schemas/__init__.py`:

```python
"""Pydantic schemas for the user-platform API surface."""
```

Write `api/schemas/user_prefs.py`:

```python
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserPrefs(BaseModel):
    """Persistent personalization for the Home mode (predominantly).

    All fields optional — a fresh user has none of these set yet. The
    onboarding modal in Phase 3c-2 collects budget/districts/area; the
    office_anchor is reserved for Phase 6 commute calculation.
    """

    model_config = ConfigDict(extra="ignore")

    budget_min_wan: float | None = Field(default=None, ge=0)
    budget_max_wan: float | None = Field(default=None, ge=0)
    districts: list[str] = Field(default_factory=list)
    area_min_sqm: float | None = Field(default=None, ge=0)
    area_max_sqm: float | None = Field(default=None, ge=0)
    office_anchor: dict[str, Any] | None = None
    updated_at: str | None = None


class UserPrefsPatch(BaseModel):
    """PATCH body — same fields as UserPrefs but unknown keys 422.

    `model_dump(exclude_unset=True)` is the merge contract: only fields
    explicitly provided by the client overwrite existing values.
    """

    model_config = ConfigDict(extra="forbid")

    budget_min_wan: float | None = Field(default=None, ge=0)
    budget_max_wan: float | None = Field(default=None, ge=0)
    districts: list[str] | None = None
    area_min_sqm: float | None = Field(default=None, ge=0)
    area_max_sqm: float | None = Field(default=None, ge=0)
    office_anchor: dict[str, Any] | None = None
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/api/test_user_prefs_schema.py -v`
Expected: 7 tests pass.

- [ ] **Step 5: Compile + full suite**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 34 passed (20 prior + 7 storage + 7 schema).

- [ ] **Step 6: Commit**

```bash
git add api/schemas/__init__.py api/schemas/user_prefs.py tests/api/test_user_prefs_schema.py
git commit -m "feat(api): add UserPrefs and UserPrefsPatch pydantic schemas"
```

---

### Task 3: `api/domains/user_prefs.py` + tests

**Files:**
- Create: `api/domains/user_prefs.py`
- Create: `tests/api/test_v2_user_prefs.py`

GET `/api/v2/user/prefs`: read `data/personal/user_prefs.json` via `personal_storage.read_json`. If missing or fails validation, return an empty `UserPrefs()` dump. Always 200.

PATCH `/api/v2/user/prefs`: accept a `UserPrefsPatch` body. Read existing prefs (or empty defaults), merge via `exclude_unset=True`, set `updated_at = datetime.now().isoformat(timespec="seconds")`, validate as `UserPrefs`, write to disk, return the validated payload.

- [ ] **Step 1: Write the failing tests**

Write `tests/api/test_v2_user_prefs.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_personal_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_get_returns_empty_defaults_when_no_file(client) -> None:
    response = client.get("/api/v2/user/prefs")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] is None
    assert body["districts"] == []
    assert body["updated_at"] is None


def test_patch_writes_and_get_round_trips(client, isolated_personal_dir: Path) -> None:
    response = client.patch(
        "/api/v2/user/prefs",
        json={"budget_max_wan": 1500, "districts": ["pudong"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] == 1500
    assert body["districts"] == ["pudong"]
    assert body["updated_at"] is not None

    # Followup GET sees the persisted state.
    follow = client.get("/api/v2/user/prefs").json()
    assert follow["budget_max_wan"] == 1500
    assert follow["districts"] == ["pudong"]

    # File actually exists on disk.
    assert (isolated_personal_dir / "user_prefs.json").is_file()


def test_patch_merges_partial_updates(client) -> None:
    client.patch("/api/v2/user/prefs", json={"budget_max_wan": 1500, "districts": ["pudong"]})
    response = client.patch("/api/v2/user/prefs", json={"area_min_sqm": 60})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["budget_max_wan"] == 1500
    assert body["districts"] == ["pudong"]
    assert body["area_min_sqm"] == 60


def test_patch_rejects_unknown_field_with_422(client) -> None:
    response = client.patch("/api/v2/user/prefs", json={"evil": True})
    assert response.status_code == 422


def test_patch_rejects_negative_budget_with_422(client) -> None:
    response = client.patch("/api/v2/user/prefs", json={"budget_max_wan": -10})
    assert response.status_code == 422


def test_get_returns_defaults_when_stored_file_is_corrupt(
    client, isolated_personal_dir: Path
) -> None:
    (isolated_personal_dir / "user_prefs.json").write_text("{not json", encoding="utf-8")
    response = client.get("/api/v2/user/prefs")
    assert response.status_code == 200
    assert response.json()["budget_max_wan"] is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/api/test_v2_user_prefs.py -v`
Expected: 404 on every endpoint — the route doesn't exist yet. (Or ImportError if you haven't created the module file. The expected failure is route-level, not import-level — see Step 3.)

- [ ] **Step 3: Implement `api/domains/user_prefs.py`**

```python
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.user_prefs import UserPrefs, UserPrefsPatch

router = APIRouter(tags=["user-prefs"])

PREFS_FILE = "user_prefs.json"


@router.get("/user/prefs")
def get_prefs() -> dict[str, Any]:
    raw = personal_storage.read_json(PREFS_FILE)
    if raw is None:
        return UserPrefs().model_dump()
    try:
        return UserPrefs.model_validate(raw).model_dump()
    except Exception:
        # Stored payload drifted from current schema — treat as empty so
        # the user can start fresh through the onboarding modal.
        return UserPrefs().model_dump()


@router.patch("/user/prefs")
def patch_prefs(patch: UserPrefsPatch) -> dict[str, Any]:
    raw = personal_storage.read_json(PREFS_FILE) or {}
    try:
        current = UserPrefs.model_validate(raw).model_dump()
    except Exception:
        current = UserPrefs().model_dump()

    update = patch.model_dump(exclude_unset=True)
    merged = {**current, **update}
    merged["updated_at"] = datetime.now().isoformat(timespec="seconds")

    validated = UserPrefs.model_validate(merged).model_dump()
    personal_storage.write_json(PREFS_FILE, validated)
    return validated
```

- [ ] **Step 4: Wire into `api/main.py`**

Open `api/main.py`. Find the existing v2 imports — after Phase 2a they look like:

```python
from .domains import (
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
)
```

Extend the alphabetical list to include `user_prefs`:

```python
from .domains import (
    buildings as v2_buildings,
    communities as v2_communities,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    user_prefs as v2_user_prefs,
)
```

Find the existing `app.include_router(v2_communities.router, prefix="/api/v2")` line (or whichever was added last). Add after the last v2 include_router call:

```python
app.include_router(v2_user_prefs.router, prefix="/api/v2")
```

- [ ] **Step 5: Run the tests**

Run: `pytest tests/api/test_v2_user_prefs.py -v`
Expected: 6 tests pass.

- [ ] **Step 6: Compile + full suite**

Run: `python3 -m compileall api`
Expected: exit 0.

Run: `pytest -q`
Expected: 40 passed (20 prior + 7 storage + 7 schema + 6 v2 routes).

- [ ] **Step 7: Commit**

```bash
git add api/domains/user_prefs.py api/main.py tests/api/test_v2_user_prefs.py
git commit -m "feat(api): add /api/v2/user/prefs GET + PATCH"
```

---

### Task 4: .gitignore + smoke + README

**Files:**
- Modify: `.gitignore` — add `data/personal/`
- Modify: `scripts/phase1_smoke.py` — +1 row asserting `GET /api/v2/user/prefs`
- Modify: `README.md` — bump section header + expand v2 row

- [ ] **Step 1: Edit `.gitignore`**

Open `.gitignore`. Find the `tmp/` line; add `data/personal/` directly above it (preserving alphabetical order isn't required; this just keeps the personal-data block readable):

Find:

```
tmp/
```

Replace with:

```
data/personal/
tmp/
```

- [ ] **Step 2: Edit `scripts/phase1_smoke.py`**

Open `scripts/phase1_smoke.py`. Find the line:

```python
            (f"{base}/api/v2/map/buildings", '"features"'),
```

Add directly below it:

```python
            (f"{base}/api/v2/user/prefs", '"districts"'),
```

The substring check leverages the fact that the empty default `UserPrefs` dump always includes the `"districts"` key — so it proves both that the route is mounted AND that the schema defaults are intact.

- [ ] **Step 3: Run the smoke**

Run: `python3 scripts/phase1_smoke.py`
Expected: 12 rows OK, exit 0.

- [ ] **Step 4: Update `README.md`**

Open `README.md`. Find `## 路由布局（Phase 3b 起）` and change to `## 路由布局（Phase 3c-1 起）`.

Find the row whose third column starts with `用户平台。`. Leave that row alone (no frontend changes in this phase).

Find the row whose third column begins with `用户平台专属接口。已开放：`. The full current text is:

```markdown
| `/api/v2/*` | `api/domains/` | 用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}` |
```

Replace its third column with:

```markdown
用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/user/prefs` (GET + PATCH)
```

- [ ] **Step 5: Verify all exit criteria**

Run each:
- `pytest -q` → 40 passed
- `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs` → 38 passed (no frontend touched)
- `python3 -m compileall api jobs scripts` → exit 0
- `python3 scripts/phase1_smoke.py` → 12 OK
- `grep -n "data/personal/" .gitignore` → 1 hit
- `node --check frontend/backstage/app.js` → exit 0 (regression guard, no frontend changed)

- [ ] **Step 6: Commit**

```bash
git add .gitignore scripts/phase1_smoke.py README.md
git commit -m "feat(api): wire /api/v2/user/prefs into smoke + docs + gitignore"
```

---

## Phase 3c-1 Exit Criteria

- [ ] `pytest -q` — 40 passed (20 prior + 7 storage + 7 schema + 6 v2 routes)
- [ ] `python3 -m compileall api jobs scripts` — exit 0
- [ ] `python3 scripts/phase1_smoke.py` — 12 rows OK
- [ ] `node --test tests/frontend/test_state.mjs tests/frontend/test_modes.mjs tests/frontend/test_drawer_data.mjs tests/frontend/test_storage.mjs tests/frontend/test_filter_helpers.mjs` — 38 passed (frontend untouched)
- [ ] `node --check frontend/backstage/app.js` — exit 0
- [ ] `data/personal/` is in `.gitignore`
- [ ] Manual: with `ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013` running, `curl -s http://127.0.0.1:8013/api/v2/user/prefs` returns `{"budget_min_wan": null, ..., "districts": [], ..., "updated_at": null}` and `curl -X PATCH -H 'Content-Type: application/json' -d '{"budget_max_wan": 1500}' http://127.0.0.1:8013/api/v2/user/prefs` returns the merged payload with `updated_at` populated. A second GET sees the persisted budget. The file `data/personal/user_prefs.json` exists; a `data/personal/.trash/` is created on the second PATCH.
- [ ] `git log --oneline f213640..HEAD` shows exactly 4 commits

## Out of Scope (deferred to Phase 3c-2 and later)

- Frontend Home onboarding modal — Phase 3c-2
- Wiring Home mode default filters to user_prefs — Phase 3c-2
- Watchlist / annotations / alerts JSON files — Phase 4 / Phase 5 (each reuses `personal_storage`)
- Cross-field validation (budget_min ≤ budget_max etc.) — Phase 3c-2 once the onboarding form fixes the UX
- District-set filtering on `/api/v2/opportunities` (multi-district) — possible Phase 3c-2 contract change
