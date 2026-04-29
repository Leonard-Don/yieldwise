# Yieldwise Plan 2 — M2 Auth (Single-Tenant Multi-User)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Yieldwise v0.2 — single-tenant multi-user authentication. Three roles (admin / analyst / viewer), session-cookie based (no JWT), bcrypt password hashing, JSON-file backed user store (matches existing `personal_storage.py` pattern), initial admin seeded from env vars on first boot. Login + admin user-management UIs ship as static HTML pages.

**Architecture:** Auth lives in a new `api/auth/` package: hashing, JSON-backed user storage (locked with `fcntl` like the existing `personal_storage.py`), session helpers, FastAPI `Depends` decorators for `current_user` / `require_role`. Login + logout + whoami endpoints land at `/api/auth/*`. Admin-only user management endpoints at `/api/auth/admin/users*`. `SessionMiddleware` (Starlette built-in) wraps the whole app; `SESSION_SECRET` env var required at boot. Routes are protected at the FastAPI layer via dependency injection. Static shells (`/` and `/backstage/`) get auth-gated via a small middleware that redirects unauthenticated visits to `/login`. Two new minimal HTML pages (`frontend/login/` + `frontend/admin/`) — vanilla JS, fetch-based forms, no bundler. The user platform's existing UI stays unchanged.

**Tech Stack:** FastAPI · Starlette `SessionMiddleware` · `bcrypt` (NEW dep) · `python-multipart` (NEW dep, required by FastAPI for form parsing) · vanilla JS ES modules · pytest · `node:test` · `fcntl` (stdlib) for file locking.

**Parent spec:** `docs/superpowers/specs/2026-04-29-yieldwise-commercialization-design.md` §5.1 M2.

**Predecessor:** `docs/superpowers/plans/2026-04-29-yieldwise-plan-1-foundation.md` (tagged at `yieldwise-v0.1-foundation`, commit `9191d24`).

---

## Scope

This plan covers ONLY M2 Auth.

**Out of scope (subsequent plans):**
- **Plan 3** — M3 Customer Data Import (~5–6 工程日)
- **Plan 4** — M4 Reports + M5 Deployment Package (~7–10 工程日)
- **Plan 5** — M6 Backstage Workflow Pivot + T2 service.py cleanup (~10–12 工程日)

**Total this plan:** ~5–7 工程日 ≈ 3 weeks part-time.

---

## Design Decisions

1. **JSON-file-backed user store**, not Postgres. Matches `api/personal_storage.py` pattern (already in-tree at `data/personal/*.json`). Pros: works in `staged` mode without DB, zero migration ceremony, simple backups. Cons: doesn't scale past ~1000 users — but private deploys are typically <50. Future: optional Postgres backend toggled by env, deferred.
2. **bcrypt directly**, not passlib. Smaller dep, no transitive footprint. Cost factor 12 (industry default).
3. **Starlette `SessionMiddleware`**, not custom JWT. HTTP-only session cookie. Server-side state minimal — session payload is signed-and-base64'd in the cookie itself. `SESSION_SECRET` env var required at boot.
4. **3 roles via Enum**: `admin` (full + user mgmt), `analyst` (read+write data, no user mgmt), `viewer` (read-only).
5. **Auth-gating strategy**:
   - `/api/auth/*` — public (login + logout)
   - `/api/health` + `/api/v2/health` — public (load balancers / monitors)
   - All other `/api/*` and `/api/v2/*` — `Depends(current_user)`, return 401 if not authenticated
   - Static `/` and `/backstage/` — middleware redirects to `/login` if no session
   - `/login` HTML — public
   - `/admin/users` HTML — `require_role("admin")` middleware redirect to `/login` if not authenticated
6. **Initial admin seed**: on FastAPI startup, if user store is empty, read `ATLAS_ADMIN_USERNAME` + `ATLAS_ADMIN_PASSWORD` env vars; create admin user; log "Created initial admin user". If env vars missing AND store empty, log loud warning but DO NOT block boot (so `staged` solo dev still works without forcing auth setup).
7. **Login flow**: HTML form at `/login` POSTs to `/api/auth/login` (form-encoded). On success, server sets session cookie and returns 200 with `{"redirect": next_url}`. Client navigates.
8. **Logout flow**: `POST /api/auth/logout` clears the session and returns 204. Client clears local UI state and navigates to `/login`.
9. **CSRF**: rely on `SameSite=Lax` cookie + the fact that we're a same-origin SPA. No separate CSRF token in v0.2. Document in `docs/security.md` (NEW). If a client requests a public CDN-hosted dashboard, revisit.
10. **Audit logs**: out of scope for v0.2. Per-user actions can be added in Plan 4 alongside service.py cleanup. Document the absence.

---

## File Structure (Plan 2 outcome)

```
api/
├── main.py                          # MODIFIED: SessionMiddleware + auth routers + static-shell gate
├── auth/                            # NEW package
│   ├── __init__.py
│   ├── hashing.py                   # NEW — bcrypt hash/verify
│   ├── storage.py                   # NEW — JSON file-locked user CRUD (uses personal_storage helpers)
│   ├── session.py                   # NEW — read/write session payload
│   ├── deps.py                      # NEW — FastAPI Depends: current_user, require_role
│   ├── seed.py                      # NEW — initial admin seed from env
│   └── middleware.py                # NEW — static-shell auth-gate middleware
├── domains/
│   └── auth.py                      # NEW — /api/auth/* routes (login/logout/whoami + admin user mgmt)
├── schemas/
│   └── auth.py                      # NEW — User, LoginRequest, LoginResponse, AdminUserCreate, AdminUserPatch
├── persistence.py                   # unchanged
├── personal_storage.py              # unchanged (its helpers may be reused)
└── requirements.txt                 # MODIFIED: + bcrypt>=4.2,<5.0, + python-multipart>=0.0.20,<1.0

frontend/
├── login/                           # NEW
│   ├── index.html
│   ├── login.css
│   └── login.js
├── admin/                           # NEW
│   ├── index.html
│   ├── admin.css
│   └── admin.js
├── user/                            # unchanged
└── backstage/                       # unchanged

data/personal/
└── auth_users.json                  # generated at runtime — initial admin seeded on first boot

docs/
├── deployment/
│   └── auth-setup.md                # NEW — admin seed env vars, session secret, role model
└── security.md                      # NEW — CSRF posture, session lifetime, audit log status

tests/api/
├── test_auth_hashing.py             # NEW — 3 cases
├── test_auth_storage.py             # NEW — 5 cases
├── test_auth_endpoints.py           # NEW — 6 cases (login/logout/whoami/protected)
├── test_auth_admin.py               # NEW — 5 cases (list/create/disable/role-change/admin-only)
└── test_auth_seed.py                # NEW — 3 cases (env seed, no env, idempotent)

tests/frontend/
├── test_login_flow.mjs              # NEW — 2 cases
└── test_admin_helpers.mjs           # NEW — 3 cases

scripts/
└── phase1_smoke.py                  # MODIFIED: assert /api/auth/whoami returns 401 (anonymous), /login HTML serves

README.md                            # MODIFIED: + brief auth section
```

---

## Phase A: Foundation — bcrypt + storage + hashing (~1.5 工程日)

### Task A.1: Add bcrypt + python-multipart dependencies

**Why:** bcrypt for password hashing, python-multipart required by FastAPI for form-encoded login.

**Files:**
- Modify: `api/requirements.txt`
- Modify: `docs/legal/dependency-licenses.md`

**Steps:**

1. Append to `api/requirements.txt`:
```
bcrypt>=4.2,<5.0
python-multipart>=0.0.20,<1.0
```

2. Install + verify:
```bash
python3 -m pip install -r api/requirements.txt
python3 -c "import bcrypt, multipart; print(bcrypt.__version__, multipart.__version__)"
```
Expected: bcrypt ≥4.2, multipart ≥0.0.20.

3. Run pip-licenses for both:
```bash
python3 -m piplicenses --packages bcrypt python-multipart --format=markdown --with-urls
```
Expected: both Apache-2.0 (bcrypt) / MIT (python-multipart). If either is GPL/AGPL, STOP and report DONE_WITH_CONCERNS.

4. Append rows to `docs/legal/dependency-licenses.md` Backend Dependencies table:
```
| bcrypt | <version> | Apache-2.0 | https://github.com/pyca/bcrypt |
| python-multipart | <version> | MIT | https://github.com/Kludex/python-multipart |
```

5. Commit:
```bash
git add api/requirements.txt docs/legal/dependency-licenses.md
git commit -m "$(cat <<'EOF'
chore(deps): add bcrypt + python-multipart for auth (M2)

bcrypt: Apache-2.0 password hashing.
python-multipart: MIT, required by FastAPI for form-encoded login POST.
License matrix updated.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.2: api/auth/__init__.py + hashing module

**Why:** Encapsulate bcrypt usage; one canonical spot for hash/verify so future cost-factor changes are local.

**Files:**
- Create: `api/auth/__init__.py` (empty + 1-line docstring)
- Create: `api/auth/hashing.py`
- Create: `tests/api/test_auth_hashing.py`

**TDD: write tests first, run, fail, then implement.**

**Steps:**

1. Create `tests/api/test_auth_hashing.py`:

```python
"""Auth password hashing tests."""
from __future__ import annotations

import pytest

from api.auth.hashing import hash_password, verify_password


def test_hash_password_returns_bcrypt_string():
    h = hash_password("hunter2")
    assert isinstance(h, str)
    assert h.startswith("$2") and len(h) >= 60


def test_verify_password_round_trip():
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h) is True
    assert verify_password("wrong password", h) is False


def test_verify_password_rejects_invalid_hash():
    # Garbage input must not crash; must return False.
    assert verify_password("any", "not-a-bcrypt-hash") is False
    assert verify_password("any", "") is False
```

2. Run — must fail with ImportError:
```bash
pytest tests/api/test_auth_hashing.py -v
```

3. Create `api/auth/__init__.py`:
```python
"""Yieldwise authentication package — hashing, storage, sessions, deps."""
```

4. Create `api/auth/hashing.py`:

```python
"""Password hashing — bcrypt, cost factor 12."""
from __future__ import annotations

import bcrypt

_ROUNDS = 12


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password with bcrypt cost factor 12. Returns the bcrypt
    string (utf-8 decoded) safe to store in JSON."""
    if not isinstance(plaintext, str):
        raise TypeError("password must be str")
    salt = bcrypt.gensalt(rounds=_ROUNDS)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash. Never raises;
    returns False on any malformed input."""
    if not isinstance(plaintext, str) or not isinstance(hashed, str) or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
```

5. Run — must pass:
```bash
pytest tests/api/test_auth_hashing.py -v
```
Expected: 3 passed.

6. Commit:
```bash
git add api/auth/__init__.py api/auth/hashing.py tests/api/test_auth_hashing.py
git commit -m "$(cat <<'EOF'
feat(auth): bcrypt password hashing module (M2)

Cost factor 12 (industry default). hash_password returns the bcrypt
string; verify_password never raises on malformed input.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.3: User storage (JSON-backed, file-locked)

**Why:** Single canonical spot for user CRUD. Matches `personal_storage.py` pattern; file-locked via `fcntl` so concurrent admin operations don't corrupt the JSON.

**Files:**
- Create: `api/auth/storage.py`
- Create: `tests/api/test_auth_storage.py`

**TDD first.**

**Steps:**

1. Create `tests/api/test_auth_storage.py`:

```python
"""Auth user storage tests."""
from __future__ import annotations

import os
import json
from pathlib import Path

import pytest

from api.auth import storage as user_store


@pytest.fixture()
def tmp_users(tmp_path, monkeypatch):
    """Point ATLAS_PERSONAL_DATA_DIR at a temp dir for test isolation."""
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    yield tmp_path


def test_list_users_empty(tmp_users):
    assert user_store.list_users() == []


def test_create_user_then_lookup(tmp_users):
    u = user_store.create_user(username="alice", password="hunter2", role="analyst")
    assert u.username == "alice"
    assert u.role == "analyst"
    assert u.disabled is False
    assert u.id  # uuid-like
    looked_up = user_store.get_by_username("alice")
    assert looked_up is not None
    assert looked_up.id == u.id


def test_create_user_duplicate_username_raises(tmp_users):
    user_store.create_user(username="bob", password="x", role="viewer")
    with pytest.raises(ValueError, match="exists"):
        user_store.create_user(username="bob", password="y", role="admin")


def test_disable_and_change_role(tmp_users):
    u = user_store.create_user(username="carol", password="x", role="viewer")
    user_store.set_role(u.id, "analyst")
    user_store.set_disabled(u.id, True)
    refreshed = user_store.get_by_id(u.id)
    assert refreshed.role == "analyst"
    assert refreshed.disabled is True


def test_verify_credentials(tmp_users):
    user_store.create_user(username="dave", password="hunter2", role="admin")
    assert user_store.verify_credentials("dave", "hunter2") is not None
    assert user_store.verify_credentials("dave", "wrong") is None
    assert user_store.verify_credentials("nobody", "hunter2") is None
    # disabled users cannot authenticate even with correct password
    u = user_store.get_by_username("dave")
    user_store.set_disabled(u.id, True)
    assert user_store.verify_credentials("dave", "hunter2") is None
```

2. Run — must fail with ImportError.

3. Create `api/auth/storage.py`:

```python
"""JSON-backed, file-locked user store. Matches personal_storage.py pattern.

Storage path: <ATLAS_PERSONAL_DATA_DIR or data/personal/>/auth_users.json
"""
from __future__ import annotations

import fcntl
import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .hashing import hash_password, verify_password

_FILENAME = "auth_users.json"
_LOCK_RETRY_DELAY_S = 0.05
_VALID_ROLES = ("admin", "analyst", "viewer")


@dataclass(frozen=True)
class User:
    id: str
    username: str
    role: str
    disabled: bool
    created_at: str
    password_hash: str = ""  # never serialized to clients


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_PERSONAL_DATA_DIR")
    base = Path(override) if override else Path(__file__).resolve().parents[2] / "data" / "personal"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _store_path() -> Path:
    return _data_dir() / _FILENAME


@contextmanager
def _locked_file(mode: str) -> Iterator:
    """Acquire an exclusive flock on the store. Creates the file if missing."""
    path = _store_path()
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    fh = open(path, mode, encoding="utf-8")
    try:
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(_LOCK_RETRY_DELAY_S)
        yield fh
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
        finally:
            fh.close()


def _read_all() -> list[dict]:
    path = _store_path()
    if not path.exists():
        return []
    with _locked_file("r") as fh:
        text = fh.read()
    if not text.strip():
        return []
    return json.loads(text)


def _write_all(rows: list[dict]) -> None:
    with _locked_file("w") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2, sort_keys=True)


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        disabled=row.get("disabled", False),
        created_at=row.get("created_at", ""),
        password_hash=row.get("password_hash", ""),
    )


def list_users() -> list[User]:
    return [_row_to_user(r) for r in _read_all()]


def get_by_id(user_id: str) -> User | None:
    for r in _read_all():
        if r["id"] == user_id:
            return _row_to_user(r)
    return None


def get_by_username(username: str) -> User | None:
    for r in _read_all():
        if r["username"] == username:
            return _row_to_user(r)
    return None


def create_user(*, username: str, password: str, role: str) -> User:
    if role not in _VALID_ROLES:
        raise ValueError(f"role must be one of {_VALID_ROLES}, got {role!r}")
    rows = _read_all()
    if any(r["username"] == username for r in rows):
        raise ValueError(f"user {username!r} exists")
    new_row = {
        "id": str(uuid.uuid4()),
        "username": username,
        "role": role,
        "disabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "password_hash": hash_password(password),
    }
    rows.append(new_row)
    _write_all(rows)
    return _row_to_user(new_row)


def set_role(user_id: str, role: str) -> None:
    if role not in _VALID_ROLES:
        raise ValueError(f"role must be one of {_VALID_ROLES}")
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["role"] = role
            _write_all(rows)
            return
    raise KeyError(user_id)


def set_disabled(user_id: str, disabled: bool) -> None:
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["disabled"] = bool(disabled)
            _write_all(rows)
            return
    raise KeyError(user_id)


def set_password(user_id: str, password: str) -> None:
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["password_hash"] = hash_password(password)
            _write_all(rows)
            return
    raise KeyError(user_id)


def verify_credentials(username: str, password: str) -> User | None:
    """Return User if username + password match AND user is not disabled."""
    user = get_by_username(username)
    if user is None or user.disabled:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
```

4. Run tests — must pass:
```bash
pytest tests/api/test_auth_storage.py -v
```
Expected: 5 passed.

5. Commit:
```bash
git add api/auth/storage.py tests/api/test_auth_storage.py
git commit -m "$(cat <<'EOF'
feat(auth): JSON-backed file-locked user store (M2)

Single source of truth for user CRUD. Matches personal_storage.py
pattern with fcntl locking. Honors ATLAS_PERSONAL_DATA_DIR override.
verify_credentials returns None for disabled users even with correct
password.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase B: Endpoints + middleware (~1.5 工程日)

### Task B.1: Auth schemas

**Why:** Pydantic models for the wire contract.

**Files:**
- Create: `api/schemas/auth.py`

**Steps:**

1. Create `api/schemas/auth.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Role = Literal["admin", "analyst", "viewer"]


class CurrentUser(BaseModel):
    """Public-safe user shape — never includes password_hash."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    username: str
    role: Role
    disabled: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    user: CurrentUser
    redirect: str = "/"


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8)
    role: Role


class AdminUserPatch(BaseModel):
    role: Role | None = None
    disabled: bool | None = None
    password: str | None = Field(default=None, min_length=8)
```

2. No tests needed yet (schemas verified through endpoint tests in B.4).

3. Commit:
```bash
git add api/schemas/auth.py
git commit -m "$(cat <<'EOF'
feat(auth): pydantic schemas for auth endpoints (M2)

CurrentUser (public-safe, no password_hash), LoginRequest /
LoginResponse, AdminUserCreate / AdminUserPatch. Role is a
Literal["admin","analyst","viewer"].

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.2: Session helpers + Depends

**Why:** Encapsulate `request.session` reads and `Depends` decorators so route handlers stay clean.

**Files:**
- Create: `api/auth/session.py`
- Create: `api/auth/deps.py`

**Steps:**

1. Create `api/auth/session.py`:

```python
"""Session payload helpers. Session is signed by SessionMiddleware in main.py.

Payload shape: {"user_id": str, "username": str, "role": str}
"""
from __future__ import annotations

from typing import Any

from starlette.requests import Request

from api.schemas.auth import CurrentUser

_SESSION_KEY = "yw"  # short to keep cookie compact


def store_session(request: Request, user: CurrentUser) -> None:
    request.session[_SESSION_KEY] = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }


def clear_session(request: Request) -> None:
    request.session.pop(_SESSION_KEY, None)


def read_session(request: Request) -> dict[str, Any] | None:
    return request.session.get(_SESSION_KEY)
```

2. Create `api/auth/deps.py`:

```python
"""FastAPI dependency injectors for auth. Use as Depends(current_user) etc."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Request, status

from api.auth.session import read_session
from api.auth import storage as user_store
from api.schemas.auth import CurrentUser


def current_user(request: Request) -> CurrentUser:
    """Return the current logged-in user or raise 401."""
    payload = read_session(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    user = user_store.get_by_id(payload.get("user_id", ""))
    if user is None or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user gone or disabled")
    return CurrentUser(id=user.id, username=user.username, role=user.role, disabled=user.disabled)


def require_role(*allowed: str) -> Callable[[CurrentUser], CurrentUser]:
    """Build a dependency that requires the current user to have one of the allowed roles."""

    def _checker(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="role not permitted")
        return user

    return _checker
```

3. Commit:
```bash
git add api/auth/session.py api/auth/deps.py
git commit -m "$(cat <<'EOF'
feat(auth): session helpers + FastAPI Depends decorators (M2)

session.py reads/writes a short payload key 'yw' to keep the cookie
compact. deps.py exposes current_user (raises 401 if no session)
and require_role(*roles) (raises 403 if role mismatch).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.3: /api/auth/* endpoints (login / logout / whoami)

**Why:** First user-facing auth surface.

**Files:**
- Create: `api/domains/auth.py`
- Create: `tests/api/test_auth_endpoints.py`
- Modify: `api/main.py` (import + router include + SessionMiddleware)

**TDD first.**

**Steps:**

1. Create `tests/api/test_auth_endpoints.py`:

```python
"""Auth endpoint tests — login / logout / whoami."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate_users(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret-please-change")
    # Reset session middleware state by reloading app — not strictly necessary
    # because TestClient creates a fresh cookie jar per test.
    yield


def _seed_user(role="analyst"):
    return user_store.create_user(username="alice", password="hunter2", role=role)


def test_whoami_anonymous_returns_401():
    client = TestClient(app)
    r = client.get("/api/auth/whoami")
    assert r.status_code == 401


def test_login_invalid_credentials_returns_401():
    _seed_user()
    client = TestClient(app)
    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401():
    client = TestClient(app)
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert r.status_code == 401


def test_login_success_sets_session_and_whoami_works():
    _seed_user(role="analyst")
    client = TestClient(app)
    r = client.post("/api/auth/login", json={"username": "alice", "password": "hunter2"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["username"] == "alice"
    assert body["user"]["role"] == "analyst"
    # follow-up whoami uses session cookie
    me = client.get("/api/auth/whoami")
    assert me.status_code == 200
    assert me.json()["username"] == "alice"


def test_logout_clears_session():
    _seed_user()
    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "alice", "password": "hunter2"})
    out = client.post("/api/auth/logout")
    assert out.status_code == 204
    me = client.get("/api/auth/whoami")
    assert me.status_code == 401


def test_disabled_user_cannot_login():
    u = _seed_user()
    user_store.set_disabled(u.id, True)
    client = TestClient(app)
    r = client.post("/api/auth/login", json={"username": "alice", "password": "hunter2"})
    assert r.status_code == 401
```

2. Run — must fail (404 or fixture error).

3. Create `api/domains/auth.py`:

```python
"""Auth endpoints: /api/auth/login, /logout, /whoami, plus admin user CRUD."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.auth import storage as user_store
from api.auth.deps import current_user, require_role
from api.auth.session import clear_session, store_session
from api.schemas.auth import (
    AdminUserCreate,
    AdminUserPatch,
    CurrentUser,
    LoginRequest,
    LoginResponse,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    user_row = user_store.verify_credentials(payload.username, payload.password)
    if user_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user = CurrentUser(
        id=user_row.id, username=user_row.username, role=user_row.role, disabled=False
    )
    store_session(request, user)
    return LoginResponse(user=user, redirect="/")


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    clear_session(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/whoami", response_model=CurrentUser)
def whoami(user: CurrentUser = Depends(current_user)) -> CurrentUser:
    return user


# --- admin user management (gated by require_role("admin")) ---

@router.get("/auth/admin/users", response_model=list[CurrentUser])
def admin_list_users(_: CurrentUser = Depends(require_role("admin"))) -> list[CurrentUser]:
    return [
        CurrentUser(id=u.id, username=u.username, role=u.role, disabled=u.disabled)
        for u in user_store.list_users()
    ]


@router.post("/auth/admin/users", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: AdminUserCreate,
    _: CurrentUser = Depends(require_role("admin")),
) -> CurrentUser:
    try:
        u = user_store.create_user(
            username=payload.username, password=payload.password, role=payload.role
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CurrentUser(id=u.id, username=u.username, role=u.role, disabled=u.disabled)


@router.patch("/auth/admin/users/{user_id}", response_model=CurrentUser)
def admin_patch_user(
    user_id: str,
    payload: AdminUserPatch,
    _: CurrentUser = Depends(require_role("admin")),
) -> CurrentUser:
    if user_store.get_by_id(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    if payload.role is not None:
        user_store.set_role(user_id, payload.role)
    if payload.disabled is not None:
        user_store.set_disabled(user_id, payload.disabled)
    if payload.password is not None:
        user_store.set_password(user_id, payload.password)
    refreshed = user_store.get_by_id(user_id)
    assert refreshed is not None
    return CurrentUser(
        id=refreshed.id, username=refreshed.username, role=refreshed.role, disabled=refreshed.disabled
    )
```

4. Modify `api/main.py`:

   - Add to existing `from .domains import (...)` block (alphabetical, between `auth` and `buildings` — wait, this conflicts with existing `domains/auth` which doesn't exist yet. Place alphabetically: `auth as v2_auth`).
   
   Actually since this is a NEW domain module, add:
   ```python
   from .domains import (
       auth as v2_auth,  # NEW — first in the alphabetical list
       alerts as v2_alerts,
       ...
   )
   ```
   
   - In the imports area near top of main.py, after the existing imports:
   ```python
   from starlette.middleware.sessions import SessionMiddleware
   ```
   
   - Add SessionMiddleware to the app, AFTER the existing CORSMiddleware:
   ```python
   _SESSION_SECRET = os.environ.get("SESSION_SECRET")
   if not _SESSION_SECRET:
       # In dev/staged solo mode, allow boot with a noisy fallback. Production
       # MUST set SESSION_SECRET (an admin-seed warning is logged on first boot).
       import secrets as _secrets
       _SESSION_SECRET = _secrets.token_urlsafe(32)
       import logging as _logging
       _logging.getLogger(__name__).warning(
           "SESSION_SECRET not set; using ephemeral random secret. "
           "All sessions will be invalidated on app restart. "
           "Set SESSION_SECRET in production."
       )

   app.add_middleware(
       SessionMiddleware,
       secret_key=_SESSION_SECRET,
       session_cookie="yieldwise_session",
       same_site="lax",
       https_only=False,  # client should set ATLAS_HTTPS_ONLY=true behind TLS
       max_age=60 * 60 * 24 * 14,  # 14 days
   )
   if os.environ.get("ATLAS_HTTPS_ONLY", "").lower() in ("1", "true", "yes"):
       # Replace the just-added middleware with https_only=True. SessionMiddleware
       # is added once; we re-create the app config block above conditionally.
       pass  # see note below
   ```
   
   **NOTE** for the implementer: the conditional `https_only=True` swap is awkward because middleware is registered once. Simpler approach: read both env vars upfront and pass `https_only=...` directly:
   ```python
   _HTTPS_ONLY = os.environ.get("ATLAS_HTTPS_ONLY", "").lower() in ("1", "true", "yes")
   app.add_middleware(
       SessionMiddleware,
       secret_key=_SESSION_SECRET,
       session_cookie="yieldwise_session",
       same_site="lax",
       https_only=_HTTPS_ONLY,
       max_age=60 * 60 * 24 * 14,
   )
   ```
   Use this simpler form.
   
   - Include the auth router. It uses `/api/auth/*` paths NOT `/api/v2/*`. Add a separate include (do NOT put it under `/api/v2`):
   ```python
   app.include_router(v2_auth.router, prefix="/api")
   ```
   Place it BEFORE the v2 includes block, since it's a different prefix.

5. Run endpoint tests — must pass:
```bash
pytest tests/api/test_auth_endpoints.py -v
```
Expected: 6 passed.

6. Run full pytest:
```bash
pytest tests/api -x --timeout=30 2>&1 | tail -3
```
Expected: 215 passed (201 + 6 endpoint + 5 storage + 3 hashing — total +14 from this plan so far). 1 skipped.

> Note: counting tests this way is informational only. The actual count depends on test isolation; the implementer should report whatever pytest emits.

7. Commit:
```bash
git add api/domains/auth.py api/main.py tests/api/test_auth_endpoints.py
git commit -m "$(cat <<'EOF'
feat(auth): /api/auth/login, /logout, /whoami, /admin/users (M2)

Login establishes session via SessionMiddleware. Logout clears it.
Whoami requires session and returns current user. Admin endpoints
gated by require_role("admin"): list, create, patch (role/disabled/
password).

SessionMiddleware reads SESSION_SECRET env (warns + uses ephemeral
random if missing). Cookie is HTTP-only, SameSite=Lax, 14-day max.
ATLAS_HTTPS_ONLY=true upgrades it to Secure cookie.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase C: Route protection + admin seed (~1.5 工程日)

### Task C.1: Protect /api/v2/* via Depends(current_user)

**Why:** Existing v2 endpoints are publicly readable. Plan 2 requires login to read.

**Files:**
- Modify: `api/main.py` (or per-router files — see strategy below)
- Modify: tests in `tests/api/` that call `/api/v2/*` (add login fixture)

**Strategy — controller decision:**

Two ways to protect `/api/v2/*`:

(a) **Per-route Depends**: add `_: CurrentUser = Depends(current_user)` to every `@router.get` / `@router.post` in `api/domains/*.py`. Explicit but ~50 line touches.

(b) **Router-level dependency**: at `app.include_router(...)` time, pass `dependencies=[Depends(current_user)]`. Single touch in main.py.

Use **(b) — router-level dependency**. It's a one-line change per `include_router` call and it's harder to forget when adding new routes.

**Steps:**

1. Modify `api/main.py` — change the include_router calls for protected v2 routes to:

```python
from fastapi import Depends as _Depends
from api.auth.deps import current_user as _current_user_dep

_AUTH_REQUIRED = [_Depends(_current_user_dep)]

app.include_router(v2_alerts.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_health.router, prefix="/api/v2")  # public — load balancers
app.include_router(v2_config.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_opportunities.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_map_tiles.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_buildings.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_communities.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_districts.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_user_prefs.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_watchlist.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_annotations.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
app.include_router(v2_search.router, prefix="/api/v2", dependencies=_AUTH_REQUIRED)
# auth router itself: NO dependencies (login must be reachable anonymously);
# admin endpoints already gated via require_role("admin") inline.
app.include_router(v2_auth.router, prefix="/api")
```

> Note: `/api/health` is the legacy non-v2 health route (kept public). The legacy `/api/*` (non-v2) routes that come from `api/service.py` re-exports may also need protection. Out of scope for this task — Plan 5 (M6 backstage workflow pivot) will rebuild those endpoints. For now, leave legacy `/api/*` accessible: a logged-out user can still hit them. Document this gap in `docs/security.md` (Task C.4).

2. Update existing tests that hit `/api/v2/*` — they will now return 401 unless the test client is logged in. Add a shared fixture:

   Create or modify `tests/api/conftest.py`:
   ```python
   import pytest
   from fastapi.testclient import TestClient
   from api.main import app
   from api.auth import storage as user_store


   @pytest.fixture()
   def auth_test_env(tmp_path, monkeypatch):
       monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
       monkeypatch.setenv("SESSION_SECRET", "test-secret")
       yield tmp_path


   @pytest.fixture()
   def authed_client(auth_test_env):
       """A TestClient logged in as an analyst user."""
       user_store.create_user(username="tester", password="hunter2", role="analyst")
       client = TestClient(app)
       r = client.post("/api/auth/login", json={"username": "tester", "password": "hunter2"})
       assert r.status_code == 200, r.text
       return client


   @pytest.fixture()
   def admin_client(auth_test_env):
       user_store.create_user(username="boss", password="hunter2", role="admin")
       client = TestClient(app)
       client.post("/api/auth/login", json={"username": "boss", "password": "hunter2"})
       return client
   ```
   
   Then audit each existing v2 test file (`test_v2_*.py`, `test_alerts_*.py`, `test_watchlist*.py`, etc.) and replace bare `TestClient(app)` with the `authed_client` fixture. This is mechanical but touches many files. Strategy:
   
   - List all tests that call `/api/v2/*`:
     ```bash
     grep -l '/api/v2/' tests/api/*.py
     ```
   - For each file, replace `client = TestClient(app)` with a function-arg `def test_xxx(authed_client):` and use `authed_client` instead of `client`.
   - For tests asserting unauthenticated behavior, use a fresh `TestClient(app)` directly.

3. Run full pytest — many tests will fail until the fixtures are wired:
```bash
pytest tests/api -x --timeout=30 2>&1 | tail -10
```

4. Fix each failing test until green. THIS IS THE LARGEST SUB-STEP. Expect this task to take ~0.75 工程日 of mechanical fixture wiring.

5. Commit:
```bash
git add api/main.py tests/api/conftest.py tests/api/test_*.py
git commit -m "$(cat <<'EOF'
feat(auth): require login for /api/v2/* via router-level Depends (M2)

Wraps every protected v2 router with Depends(current_user). Legacy
/api/* routes (re-exports from service.py) remain unauthenticated;
they will be rebuilt or gated in Plan 5 (M6).

Adds tests/api/conftest.py fixtures: authed_client (analyst) and
admin_client (admin). Existing v2 tests migrated to use authed_client
where they need an authenticated session.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.2: Static-shell auth gate

**Why:** Visiting `/` or `/backstage/` while logged out should redirect to `/login`, not silently serve HTML that 401s every API call.

**Files:**
- Create: `api/auth/middleware.py`
- Modify: `api/main.py` (register the middleware before static-files mount)

**Steps:**

1. Create `api/auth/middleware.py`:

```python
"""Static-shell auth gate. Anonymous visits to /, /backstage/, /admin/ get
redirected to /login. Public exceptions: /login, /api/*, /api/health,
favicon, static assets.

This runs as a Starlette BaseHTTPMiddleware. It reads request.session
(populated by SessionMiddleware, which MUST be added BEFORE this).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from api.auth.session import read_session

_PUBLIC_PREFIXES = (
    "/login",
    "/api/",  # all API requests handle their own auth via Depends
    "/favicon",
    "/assets/",
)
_GATED_SHELLS = (
    "/",
    "/backstage",
    "/admin",
)


def _is_gated(path: str) -> bool:
    if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return False
    return any(path == p or path.startswith(p + "/") for p in _GATED_SHELLS)


class StaticShellAuthGate(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _is_gated(request.url.path):
            payload = read_session(request)
            if not payload:
                next_url = request.url.path
                if request.url.query:
                    next_url += "?" + request.url.query
                return RedirectResponse(
                    url=f"/login?next={next_url}",
                    status_code=302,
                )
        return await call_next(request)
```

2. In `api/main.py`, register the middleware AFTER SessionMiddleware (Starlette adds middleware in reverse — innermost last):

```python
from api.auth.middleware import StaticShellAuthGate

# After app.add_middleware(SessionMiddleware, ...)
app.add_middleware(StaticShellAuthGate)
```

3. Test by hand:
```bash
uvicorn api.main:app --port 8014 &
SERVER_PID=$!
sleep 2
echo "anonymous /:"
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8014/
echo "anonymous /backstage/:"
curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" http://127.0.0.1:8014/backstage/
echo "anonymous /api/health:"
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8014/api/health
kill $SERVER_PID
```
Expected: `/` returns 302 → `/login?next=/`; `/backstage/` returns 302 → `/login?next=/backstage/`; `/api/health` returns 200.

4. Add a pytest:
```python
# tests/api/test_auth_middleware.py
from fastapi.testclient import TestClient
from api.main import app


def test_anonymous_root_redirects_to_login(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    client = TestClient(app, follow_redirects=False)
    r = client.get("/")
    assert r.status_code == 302
    assert r.headers["location"].startswith("/login?next=/")


def test_anonymous_backstage_redirects_to_login(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    client = TestClient(app, follow_redirects=False)
    r = client.get("/backstage/")
    assert r.status_code == 302


def test_anonymous_api_health_is_public(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    client = TestClient(app)
    r = client.get("/api/health")
    assert r.status_code == 200
```

5. Run pytest:
```bash
pytest tests/api/test_auth_middleware.py -v
```
Expected: 3 passed.

6. Commit:
```bash
git add api/auth/middleware.py api/main.py tests/api/test_auth_middleware.py
git commit -m "$(cat <<'EOF'
feat(auth): static-shell auth gate (M2)

StaticShellAuthGate redirects anonymous visits to /, /backstage/,
/admin/* to /login?next=<path>. /api/* requests are not gated by
this middleware — they handle auth via per-route Depends.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.3: Initial admin seed from env

**Why:** First-time deploy. If user store is empty AND `ATLAS_ADMIN_USERNAME` + `ATLAS_ADMIN_PASSWORD` env vars are set, create the admin user during FastAPI startup.

**Files:**
- Create: `api/auth/seed.py`
- Create: `tests/api/test_auth_seed.py`
- Modify: `api/main.py` (call seed on startup event)

**TDD first.**

**Steps:**

1. Create `tests/api/test_auth_seed.py`:

```python
"""Initial admin seed tests."""
from __future__ import annotations

import pytest

from api.auth.seed import seed_initial_admin
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    yield


def test_seed_creates_admin_when_store_empty(monkeypatch):
    monkeypatch.setenv("ATLAS_ADMIN_USERNAME", "boss")
    monkeypatch.setenv("ATLAS_ADMIN_PASSWORD", "hunter22")
    seed_initial_admin()
    users = user_store.list_users()
    assert len(users) == 1
    assert users[0].username == "boss"
    assert users[0].role == "admin"


def test_seed_is_idempotent(monkeypatch):
    monkeypatch.setenv("ATLAS_ADMIN_USERNAME", "boss")
    monkeypatch.setenv("ATLAS_ADMIN_PASSWORD", "hunter22")
    seed_initial_admin()
    seed_initial_admin()  # second call should not raise or duplicate
    assert len(user_store.list_users()) == 1


def test_seed_no_op_without_env(monkeypatch, caplog):
    monkeypatch.delenv("ATLAS_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_PASSWORD", raising=False)
    seed_initial_admin()  # logs warning, returns silently
    assert user_store.list_users() == []
```

2. Run — must fail (ImportError).

3. Create `api/auth/seed.py`:

```python
"""Initial admin seed. Idempotent. No-op if user store is non-empty
or if ATLAS_ADMIN_USERNAME / ATLAS_ADMIN_PASSWORD env vars are missing.
"""
from __future__ import annotations

import logging
import os

from api.auth import storage as user_store

_logger = logging.getLogger(__name__)


def seed_initial_admin() -> None:
    """Called once on FastAPI startup. Creates an admin user if store is empty
    AND ATLAS_ADMIN_USERNAME + ATLAS_ADMIN_PASSWORD are set.

    Logs a clear warning if store is empty but env is unset (typical solo-dev
    starting state); this lets the app boot without forcing auth setup.
    """
    if user_store.list_users():
        return  # idempotent: already seeded
    username = os.environ.get("ATLAS_ADMIN_USERNAME")
    password = os.environ.get("ATLAS_ADMIN_PASSWORD")
    if not username or not password:
        _logger.warning(
            "Yieldwise auth: user store empty and ATLAS_ADMIN_USERNAME/"
            "ATLAS_ADMIN_PASSWORD not set; no users seeded. "
            "App will allow anonymous access to legacy /api/* routes; "
            "/api/v2/* and static shells require login. "
            "Set the env vars to seed an admin on next boot."
        )
        return
    if len(password) < 8:
        _logger.error(
            "Yieldwise auth: ATLAS_ADMIN_PASSWORD must be at least 8 chars; refusing to seed."
        )
        return
    user_store.create_user(username=username, password=password, role="admin")
    _logger.info("Yieldwise auth: seeded initial admin user %r", username)
```

4. Run tests — must pass:
```bash
pytest tests/api/test_auth_seed.py -v
```
Expected: 3 passed.

5. Wire into `api/main.py`. Add a startup event:

```python
from api.auth.seed import seed_initial_admin

@app.on_event("startup")
def _yieldwise_startup() -> None:
    seed_initial_admin()
```

(Note: `@app.on_event("startup")` is the Starlette legacy API; the modern lifespan context manager is preferred but the legacy decorator is still supported in Starlette 0.41+. Use the legacy form here for simplicity. If the existing `api/main.py` already has lifespan / startup handlers, integrate accordingly.)

6. Commit:
```bash
git add api/auth/seed.py tests/api/test_auth_seed.py api/main.py
git commit -m "$(cat <<'EOF'
feat(auth): initial admin seed from env (M2)

On FastAPI startup, if user store is empty AND ATLAS_ADMIN_USERNAME +
ATLAS_ADMIN_PASSWORD are set, create an admin user. Idempotent;
silent if store has users; warns if store empty but env unset (so
solo-dev boot still works).

Refuses to seed if ATLAS_ADMIN_PASSWORD < 8 chars.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.4: Auth deployment + security docs

**Why:** Customer ops will read these. Documents env vars, role model, CSRF posture, audit-log absence.

**Files:**
- Create: `docs/deployment/auth-setup.md`
- Create: `docs/security.md`

**Steps:**

1. Create `docs/deployment/auth-setup.md`:

```markdown
# Yieldwise Auth Setup

Single-tenant multi-user auth. JSON-file backed user store at
`data/personal/auth_users.json`. Bcrypt password hashing.

## Environment Variables

| Var | Required | Purpose |
| --- | --- | --- |
| `SESSION_SECRET` | **Yes (production)** | URL-safe random ≥32 bytes. Used to sign session cookies. Rotate to invalidate all sessions. |
| `ATLAS_ADMIN_USERNAME` | First boot only | Username for the seeded admin. |
| `ATLAS_ADMIN_PASSWORD` | First boot only | Min 8 chars. Change immediately after first login via the admin UI. |
| `ATLAS_HTTPS_ONLY` | Recommended (production) | Set to `true` to mark the session cookie as `Secure`. Required if running behind TLS. |
| `ATLAS_PERSONAL_DATA_DIR` | Optional | Override the user-store directory (default: `<repo>/data/personal/`). |

## Role Model

- `admin` — full access including user management.
- `analyst` — read + write data; no user management.
- `viewer` — read-only.

## First Boot

\`\`\`bash
export SESSION_SECRET=$(openssl rand -base64 32)
export ATLAS_ADMIN_USERNAME=ops
export ATLAS_ADMIN_PASSWORD='change-me-immediately'
export ATLAS_HTTPS_ONLY=true
uvicorn api.main:app --host 0.0.0.0 --port 8000
\`\`\`

The startup log will show:

\`\`\`
Yieldwise auth: seeded initial admin user 'ops'
\`\`\`

Visit `/login`, sign in as `ops`, change the password via `/admin/users`.

## Adding More Users

1. Sign in as admin.
2. Visit `/admin/users`.
3. Add user with username, password (≥8 chars), role.

## Disabling a User

Same UI: toggle `disabled`. Disabled users cannot log in even with correct password. Their existing sessions become invalid on next request.

## Rotating Passwords

Same UI: "Change password" sets a new password. The user must re-login.

## Backup

Back up `data/personal/auth_users.json` regularly. Format is plain JSON; passwords are bcrypt-hashed.

## Restoring

Stop uvicorn → restore the JSON file → restart. No migration step required.
```

(Replace escaped `\`\`\`` with actual triple-backticks in the file.)

2. Create `docs/security.md`:

```markdown
# Yieldwise Security Posture (v0.2)

## Auth

- **Session cookies** signed with `SESSION_SECRET`. HTTP-only, `SameSite=Lax`.
- `Secure` flag set when `ATLAS_HTTPS_ONLY=true`.
- 14-day session lifetime; re-login required after expiry.
- bcrypt cost factor 12 for password hashing.

## CSRF

We rely on `SameSite=Lax` cookie + same-origin SPA. **No separate CSRF token in v0.2.**

This is acceptable for:
- Private deployments behind corporate VPN / SSO front
- Same-origin browser app

This is NOT acceptable for:
- Public CDN-hosted dashboards with credentialed cross-origin requests
- Embedded iframes from third-party domains

If you need either, file a Plan 4+ ticket to add explicit CSRF tokens.

## Audit Log

**Not implemented in v0.2.** Login / logout / admin actions are not persisted to a queryable log. Server-level logs (`uvicorn` stdout) capture login attempts at INFO level, but there is no per-tenant audit table.

If your compliance program requires an audit log, file a Plan 4+ ticket. The natural location is a new `audit_events.json` file in `data/personal/` alongside `auth_users.json`.

## Rate Limiting

**Not implemented in v0.2.** Login endpoint does not rate-limit failed attempts. If exposed to the public internet, deploy behind a rate-limiting reverse proxy (Cloudflare, nginx with `limit_req`, etc.).

## Data Encryption

- **At rest:** customer data lives in PostgreSQL or staged JSON files. Yieldwise does not encrypt at the application layer; rely on disk-level encryption (LUKS / FileVault / BitLocker) and Postgres TDE if required.
- **In transit:** Yieldwise expects to run behind a TLS-terminating reverse proxy (nginx, Caddy, AWS ALB). The app itself does not implement TLS.

## Threat Model

In scope: 
- Casual unauthorized access (lost session cookie, weak password)
- Internal abuse (analyst tries to access admin endpoints)
- Disabled-user lockout

Out of scope (v0.2):
- Sophisticated CSRF
- Brute-force credential stuffing (use a reverse proxy)
- Insider data exfiltration (use OS-level audit + DLP)
- Compromised admin account (assume admin = trusted)
```

3. Commit:
```bash
git add docs/deployment/auth-setup.md docs/security.md
git commit -m "$(cat <<'EOF'
docs: auth deployment + security posture (M2)

auth-setup.md: env vars, role model, first-boot recipe.
security.md: CSRF posture, audit-log status, rate limiting,
threat-model in/out scope. Calls out gaps explicitly so client
legal/security teams can assess.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase D: Login UI (~1 工程日)

### Task D.1: Login HTML + CSS + JS

**Files:**
- Create: `frontend/login/index.html`
- Create: `frontend/login/login.css`
- Create: `frontend/login/login.js`
- Modify: `api/main.py` (route `/login` to serve the HTML)

**Steps:**

1. Create `frontend/login/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Yieldwise · 登录</title>
  <link rel="stylesheet" href="/static/login.css">
</head>
<body>
  <main class="login-shell">
    <header class="login-brand">
      <h1>Yieldwise · 租知</h1>
      <p>租赁资产投研工作台</p>
    </header>
    <form id="login-form" class="login-form" novalidate>
      <label>
        <span>用户名</span>
        <input type="text" name="username" autocomplete="username" required>
      </label>
      <label>
        <span>密码</span>
        <input type="password" name="password" autocomplete="current-password" required>
      </label>
      <button type="submit">登录</button>
      <p class="login-error" data-role="error" hidden></p>
    </form>
  </main>
  <script type="module" src="/static/login.js"></script>
</body>
</html>
```

2. Create `frontend/login/login.css`:

```css
:root {
  --bg: #0a0e14;
  --fg: #e5e7eb;
  --accent: #4ade80;
  --error: #f87171;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: ui-sans-serif, system-ui, -apple-system, "PingFang SC", sans-serif;
}
.login-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 1.5rem;
}
.login-brand h1 { font-size: 1.75rem; margin: 0 0 0.25rem; letter-spacing: 0.02em; }
.login-brand p { margin: 0; opacity: 0.7; }
.login-form {
  margin-top: 2rem;
  display: grid;
  gap: 1rem;
  width: min(100%, 320px);
}
.login-form label { display: grid; gap: 0.4rem; font-size: 0.85rem; }
.login-form input {
  background: rgba(255,255,255,0.04);
  color: var(--fg);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  font: inherit;
}
.login-form input:focus { outline: 1px solid var(--accent); outline-offset: 1px; }
.login-form button {
  background: var(--accent);
  color: #052e16;
  border: 0;
  padding: 0.7rem;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
}
.login-form button:hover { filter: brightness(1.05); }
.login-error { color: var(--error); font-size: 0.85rem; margin: 0; }
```

3. Create `frontend/login/login.js`:

```javascript
const form = document.getElementById("login-form");
const errorEl = form.querySelector('[data-role="error"]');

function getNextUrl() {
  const params = new URLSearchParams(window.location.search);
  const next = params.get("next");
  // Allow only same-origin paths to defeat open-redirect attacks.
  if (next && next.startsWith("/") && !next.startsWith("//")) {
    return next;
  }
  return "/";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorEl.hidden = true;
  const data = new FormData(form);
  const payload = {
    username: data.get("username"),
    password: data.get("password"),
  };
  try {
    const r = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (r.status === 401) {
      errorEl.textContent = "用户名或密码错误";
      errorEl.hidden = false;
      return;
    }
    if (!r.ok) {
      errorEl.textContent = `登录失败 (${r.status})`;
      errorEl.hidden = false;
      return;
    }
    window.location.href = getNextUrl();
  } catch (err) {
    errorEl.textContent = `网络错误: ${err.message}`;
    errorEl.hidden = false;
  }
});
```

4. Modify `api/main.py` — add a route that serves the login HTML and a static-files mount for the CSS/JS:

```python
# Find the existing static mount for /. Pattern is something like:
# app.mount("/", StaticFiles(directory=...), name="user")
# Add BEFORE that mount:

LOGIN_DIR = FRONTEND_DIR / "login"


@app.get("/login")
def serve_login() -> FileResponse:
    return FileResponse(LOGIN_DIR / "index.html")


# Mount login assets separately at /static/ so the HTML can reference them:
app.mount("/static", StaticFiles(directory=LOGIN_DIR), name="login-static")
```

> Read the existing `api/main.py` static-mount block carefully and place the login route + mount BEFORE the catch-all `/` mount, so that `/login` doesn't get swallowed by the user-shell static mount. The current static mount(s) are around line 130+ in the file (post-Plan 1).

5. Add a basic `node:test` for the redirect helper:

   Create `tests/frontend/test_login_flow.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

// We test the URL-validation logic by importing it. Since login.js attaches
// to the DOM on import, we extract the safe-redirect helper to a separate
// pure module if testing it inline becomes too DOM-coupled. For v0.2, the
// helper inside login.js is intentionally inline; this test verifies the
// allowed/rejected paths via a mirrored function.

function pickNext(query) {
  const params = new URLSearchParams(query);
  const next = params.get("next");
  if (next && next.startsWith("/") && !next.startsWith("//")) return next;
  return "/";
}

test("pickNext accepts same-origin paths", () => {
  assert.equal(pickNext("?next=/backstage/"), "/backstage/");
  assert.equal(pickNext("?next=/admin/users"), "/admin/users");
});

test("pickNext rejects external URLs and protocol-relative URLs", () => {
  assert.equal(pickNext("?next=//evil.example/"), "/");
  assert.equal(pickNext("?next=https://evil.example/"), "/");
  assert.equal(pickNext("?next="), "/");
  assert.equal(pickNext(""), "/");
});
```

> NOTE: this duplicates the helper in test code rather than importing from `login.js` (which has DOM side-effects on import). Document the duplication in a comment so future refactors keep them in sync. A cleaner long-term approach is to extract `pickNext` to `frontend/login/helpers.js` and import from both — out of scope for D.1.

6. Run the test:
```bash
node --test tests/frontend/test_login_flow.mjs
```
Expected: 2 pass.

7. Manual smoke:
```bash
uvicorn api.main:app --port 8014 &
sleep 2
curl -s http://127.0.0.1:8014/login | head -10
kill %1
```
Expected: HTML output with `<title>Yieldwise · 登录</title>`.

8. Commit:
```bash
git add frontend/login/ tests/frontend/test_login_flow.mjs api/main.py
git commit -m "$(cat <<'EOF'
feat(auth): login UI (M2)

frontend/login/index.html + login.css + login.js. Vanilla, no
bundler. POSTs JSON to /api/auth/login and navigates to ?next= or /.
Same-origin path validation defeats open-redirect.

Wires /login route in api/main.py + /static mount for login assets.
node:test covers pickNext accept/reject behavior.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase E: Admin user-management UI (~1.5 工程日)

### Task E.1: Admin HTML + CSS + JS

**Files:**
- Create: `frontend/admin/index.html`
- Create: `frontend/admin/admin.css`
- Create: `frontend/admin/admin.js`
- Modify: `api/main.py` (route `/admin/users` to serve the HTML; admin-only via static-shell gate already covers `/admin/*`)

**Steps:**

1. Create `frontend/admin/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Yieldwise · 用户管理</title>
  <link rel="stylesheet" href="/static-admin/admin.css">
</head>
<body>
  <header class="admin-topbar">
    <h1>用户管理</h1>
    <div class="admin-meta">
      <span data-role="me-name"></span>
      <button type="button" data-role="logout">登出</button>
    </div>
  </header>
  <main class="admin-shell">
    <section class="admin-add">
      <h2>添加用户</h2>
      <form id="add-user-form" class="admin-form" novalidate>
        <label>
          <span>用户名</span>
          <input type="text" name="username" required>
        </label>
        <label>
          <span>密码（≥8 字符）</span>
          <input type="password" name="password" required minlength="8">
        </label>
        <label>
          <span>角色</span>
          <select name="role" required>
            <option value="viewer">viewer</option>
            <option value="analyst">analyst</option>
            <option value="admin">admin</option>
          </select>
        </label>
        <button type="submit">添加</button>
      </form>
      <p class="admin-error" data-role="add-error" hidden></p>
    </section>
    <section class="admin-list">
      <h2>当前用户</h2>
      <table>
        <thead>
          <tr><th>用户名</th><th>角色</th><th>状态</th><th>操作</th></tr>
        </thead>
        <tbody data-role="users"></tbody>
      </table>
    </section>
  </main>
  <script type="module" src="/static-admin/admin.js"></script>
</body>
</html>
```

2. Create `frontend/admin/admin.css`:

```css
:root {
  --bg: #0a0e14;
  --fg: #e5e7eb;
  --accent: #4ade80;
  --error: #f87171;
  --border: rgba(255,255,255,0.08);
  --card-bg: rgba(255,255,255,0.03);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: ui-sans-serif, system-ui, "PingFang SC", sans-serif; }
.admin-topbar { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); }
.admin-topbar h1 { font-size: 1.25rem; margin: 0; }
.admin-meta button { background: none; color: var(--fg); border: 1px solid var(--border); padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.admin-shell { padding: 1.5rem; display: grid; gap: 2rem; max-width: 800px; margin: 0 auto; }
.admin-add, .admin-list { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem; }
h2 { margin: 0 0 1rem; font-size: 1rem; opacity: 0.85; }
.admin-form { display: grid; gap: 0.75rem; grid-template-columns: 1fr 1fr 1fr auto; align-items: end; }
.admin-form label { display: grid; gap: 0.3rem; font-size: 0.8rem; }
.admin-form input, .admin-form select { background: rgba(255,255,255,0.04); color: var(--fg); border: 1px solid var(--border); padding: 0.5rem; border-radius: 4px; font: inherit; }
.admin-form button { background: var(--accent); color: #052e16; border: 0; padding: 0.55rem 1rem; border-radius: 4px; font-weight: 600; cursor: pointer; }
.admin-error { color: var(--error); font-size: 0.85rem; margin: 0.5rem 0 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { text-align: left; padding: 0.5rem 0.4rem; border-bottom: 1px solid var(--border); }
th { font-weight: 500; opacity: 0.7; }
td button { background: none; color: var(--fg); border: 1px solid var(--border); padding: 0.3rem 0.6rem; border-radius: 4px; cursor: pointer; margin-right: 0.25rem; font-size: 0.8rem; }
td button:hover { background: rgba(255,255,255,0.04); }
```

3. Create `frontend/admin/admin.js`:

```javascript
const usersEl = document.querySelector('[data-role="users"]');
const meEl = document.querySelector('[data-role="me-name"]');
const addForm = document.getElementById("add-user-form");
const addError = document.querySelector('[data-role="add-error"]');
const logoutBtn = document.querySelector('[data-role="logout"]');

async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, { credentials: "same-origin", ...opts });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`${r.status} ${text}`);
  }
  return r.json();
}

async function loadMe() {
  const me = await fetchJSON("/api/auth/whoami");
  meEl.textContent = `${me.username} (${me.role})`;
}

async function loadUsers() {
  const users = await fetchJSON("/api/auth/admin/users");
  usersEl.innerHTML = "";
  for (const u of users) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHTML(u.username)}</td>
      <td>${escapeHTML(u.role)}</td>
      <td>${u.disabled ? "<em>已禁用</em>" : "<span>启用</span>"}</td>
      <td></td>
    `;
    const actions = tr.querySelector("td:last-child");
    actions.appendChild(makeRoleSelector(u));
    actions.appendChild(makeToggleBtn(u));
    actions.appendChild(makeRotatePwBtn(u));
    usersEl.appendChild(tr);
  }
}

function makeRoleSelector(u) {
  const sel = document.createElement("select");
  for (const role of ["viewer", "analyst", "admin"]) {
    const opt = document.createElement("option");
    opt.value = role;
    opt.textContent = role;
    if (role === u.role) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.addEventListener("change", async () => {
    await patchUser(u.id, { role: sel.value });
    await loadUsers();
  });
  return sel;
}

function makeToggleBtn(u) {
  const btn = document.createElement("button");
  btn.textContent = u.disabled ? "启用" : "禁用";
  btn.addEventListener("click", async () => {
    await patchUser(u.id, { disabled: !u.disabled });
    await loadUsers();
  });
  return btn;
}

function makeRotatePwBtn(u) {
  const btn = document.createElement("button");
  btn.textContent = "改密";
  btn.addEventListener("click", async () => {
    const pw = window.prompt(`为 ${u.username} 设置新密码（≥8 字符）：`);
    if (!pw) return;
    if (pw.length < 8) {
      window.alert("密码至少 8 字符");
      return;
    }
    await patchUser(u.id, { password: pw });
    window.alert("密码已更新");
  });
  return btn;
}

async function patchUser(id, payload) {
  await fetchJSON(`/api/auth/admin/users/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
}

addForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  addError.hidden = true;
  const data = new FormData(addForm);
  const payload = {
    username: data.get("username"),
    password: data.get("password"),
    role: data.get("role"),
  };
  try {
    await fetchJSON("/api/auth/admin/users", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    addForm.reset();
    await loadUsers();
  } catch (err) {
    addError.textContent = err.message;
    addError.hidden = false;
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  window.location.href = "/login";
});

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

(async () => {
  try {
    await loadMe();
    await loadUsers();
  } catch (err) {
    if (err.message.startsWith("401") || err.message.startsWith("403")) {
      window.location.href = "/login";
      return;
    }
    addError.textContent = `加载失败：${err.message}`;
    addError.hidden = false;
  }
})();
```

4. Modify `api/main.py` — add a route + static mount for admin assets:

```python
ADMIN_DIR = FRONTEND_DIR / "admin"


@app.get("/admin/users")
def serve_admin() -> FileResponse:
    return FileResponse(ADMIN_DIR / "index.html")


app.mount("/static-admin", StaticFiles(directory=ADMIN_DIR), name="admin-static")
```

(Place this near the login mount. Note the `/static-admin/` prefix to avoid colliding with `/static/` for login.)

5. Add backend admin tests `tests/api/test_auth_admin.py`:

```python
"""Admin user management tests — list / create / patch / role-only."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    yield


def _login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200
    return r


def test_admin_list_requires_admin_role():
    user_store.create_user(username="boss", password="hunter22", role="admin")
    user_store.create_user(username="alice", password="hunter22", role="analyst")
    client = TestClient(app)
    _login(client, "alice", "hunter22")
    r = client.get("/api/auth/admin/users")
    assert r.status_code == 403


def test_admin_can_list():
    user_store.create_user(username="boss", password="hunter22", role="admin")
    client = TestClient(app)
    _login(client, "boss", "hunter22")
    r = client.get("/api/auth/admin/users")
    assert r.status_code == 200
    body = r.json()
    assert any(u["username"] == "boss" for u in body)


def test_admin_can_create_user():
    user_store.create_user(username="boss", password="hunter22", role="admin")
    client = TestClient(app)
    _login(client, "boss", "hunter22")
    r = client.post(
        "/api/auth/admin/users",
        json={"username": "new", "password": "hunter22", "role": "viewer"},
    )
    assert r.status_code == 201
    assert r.json()["username"] == "new"


def test_admin_can_disable_and_change_role():
    user_store.create_user(username="boss", password="hunter22", role="admin")
    target = user_store.create_user(username="al", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "boss", "hunter22")
    r = client.patch(
        f"/api/auth/admin/users/{target.id}",
        json={"role": "analyst", "disabled": True},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["role"] == "analyst"
    assert body["disabled"] is True


def test_admin_create_duplicate_returns_409():
    user_store.create_user(username="boss", password="hunter22", role="admin")
    user_store.create_user(username="al", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "boss", "hunter22")
    r = client.post(
        "/api/auth/admin/users",
        json={"username": "al", "password": "hunter22", "role": "viewer"},
    )
    assert r.status_code == 409
```

6. Run pytest:
```bash
pytest tests/api/test_auth_admin.py -v
```
Expected: 5 passed.

7. Run full pytest one more time to make sure nothing else broke:
```bash
pytest tests/api -x --timeout=30 2>&1 | tail -3
```

8. Add a `node:test` for the `escapeHTML` helper (optional but useful):

   Create `tests/frontend/test_admin_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

// Mirror of escapeHTML from frontend/admin/admin.js
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

test("escapeHTML escapes ampersand and angle brackets", () => {
  assert.equal(escapeHTML("<script>alert(1)</script>"), "&lt;script&gt;alert(1)&lt;/script&gt;");
  assert.equal(escapeHTML("a & b"), "a &amp; b");
});

test("escapeHTML escapes quotes", () => {
  assert.equal(escapeHTML(`"x"`), "&quot;x&quot;");
  assert.equal(escapeHTML("'x'"), "&#39;x&#39;");
});

test("escapeHTML coerces non-strings", () => {
  assert.equal(escapeHTML(42), "42");
  assert.equal(escapeHTML(null), "null");
});
```

9. Run:
```bash
node --test tests/frontend/test_admin_helpers.mjs
```

10. Commit:
```bash
git add frontend/admin/ tests/api/test_auth_admin.py tests/frontend/test_admin_helpers.mjs api/main.py
git commit -m "$(cat <<'EOF'
feat(auth): admin user-management UI (M2)

frontend/admin/index.html + admin.css + admin.js. List users,
create user, change role, toggle disabled, rotate password. Vanilla
JS + fetch + form. escapeHTML for XSS safety on user-supplied
strings.

Wires /admin/users route + /static-admin mount in api/main.py.

Backend: 5 admin endpoint tests (role-gating, list, create, patch,
duplicate). Frontend: 3 escapeHTML cases.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase F: Plan 2 ship checks (~0.5 工程日)

### Task F.1: Update phase1_smoke.py

**File:** `scripts/phase1_smoke.py`

**Steps:**

1. Find the smoke routes list. The bundled state currently asserts the user platform is reachable anonymously — this will FAIL after Plan 2 because `/` redirects to `/login`. Update:

   - Replace the `/` assertion with a check that `/login` is reachable AND that `/` returns 302.
   - Add `/api/auth/whoami` returning 401 (anonymous case).

   Example diff:
   ```python
   # Add or replace:
   (f"{base}/login", "<title>Yieldwise · 登录</title>"),
   # Note: phase1_smoke uses substring assertions on response body. /api/auth/whoami
   # returns JSON when authenticated and 401 plain when not — adjust the smoke harness
   # if needed to support status-code-only assertions, OR write a sentinel string in
   # the 401 response body.
   ```
   
   Actually, the phase1_smoke harness currently appears to assert 200 + substring. To assert 401, the harness needs adjustment. Read `scripts/phase1_smoke.py` carefully and decide:
   
   (a) Add a new `expect_status` parameter to the harness so we can assert 401 without a substring.
   (b) OR drop the `/api/auth/whoami` smoke check and rely on pytest tests for that route.
   
   Recommendation: (b) — the pytest tests already cover whoami exhaustively. Smoke is for "does the server boot and return reasonable responses on the happy path". An anonymous visit should redirect to /login; that's the smoke we care about.

2. Modify the smoke list:
   - Remove the `/` assertion (it will redirect now)
   - Add `/login` substring assertion
   - Update `/backstage/` assertion or remove it (it'll redirect too)

3. Re-run smoke against a freshly seeded admin to confirm authenticated paths still work. This requires the smoke script to:
   - Set `ATLAS_ADMIN_USERNAME=smoketest`, `ATLAS_ADMIN_PASSWORD=smoketestpw`
   - Boot the server
   - POST to /api/auth/login to establish a session
   - Use the session cookie for subsequent v2 requests

   This is a meaningful refactor of `phase1_smoke.py`. If the implementer judges it too large for F.1, **split it into two tasks**: (1) update routes that don't need auth (login + redirects), and (2) add an authenticated smoke pass with a separate environment fixture.

   For initial F.1: just do the unauthenticated changes (login HTML reachable, / redirects, /api/health public). Leave the authenticated smoke as a TODO comment in the file pointing at this plan.

4. Run smoke, expect `Phase 1 smoke OK`:
```bash
SESSION_SECRET=test-secret python3 scripts/phase1_smoke.py
```

5. Commit:
```bash
git add scripts/phase1_smoke.py
git commit -m "$(cat <<'EOF'
test(smoke): adapt phase1_smoke to Plan 2 auth (M2)

Anonymous visits to / and /backstage/ redirect to /login. Drop
those assertions; add /login HTML substring check; /api/health
remains public.

TODO: add authenticated smoke pass (post-login session) once F.1
completes. Currently smoke is unauthenticated only.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task F.2: README update

**File:** `README.md`

**Steps:**

1. Add a new section "## 认证 / Auth" right after the existing "## 分支策略" section:

```markdown
## 认证 / Auth

v0.2 起 `/`、`/backstage/`、`/admin/users` 都需要登录。

- 首次部署：设置 `SESSION_SECRET` + `ATLAS_ADMIN_USERNAME` + `ATLAS_ADMIN_PASSWORD`（≥8 字符），启动后用初始 admin 登录。
- 角色：`admin`（含用户管理）/ `analyst`（读写数据）/ `viewer`（只读）。
- 详细部署：`docs/deployment/auth-setup.md`
- 安全姿态（CSRF、审计、限流的边界）：`docs/security.md`
```

2. Commit:
```bash
git add README.md
git commit -m "$(cat <<'EOF'
docs(readme): brief auth section pointing to deployment + security docs (M2)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task F.3: Final regression sweep

```bash
python3 -m compileall -q api jobs scripts
pytest tests/api -x --timeout=30 2>&1 | tail -3
for f in frontend/backstage/{data,lib}/*.js frontend/backstage/app.js frontend/user/modules/*.js frontend/login/*.js frontend/admin/*.js; do node --check "$f" || break; done
node --test tests/frontend/*.mjs
SESSION_SECRET=test python3 scripts/phase1_smoke.py
```

All should pass.

---

### Task F.4: Tag the milestone

```bash
git tag -a yieldwise-v0.2-auth -m "$(cat <<'EOF'
Yieldwise v0.2 Auth

Plan 2 complete: single-tenant multi-user authentication.

- bcrypt password hashing (cost 12)
- JSON-file-locked user store (data/personal/auth_users.json)
- Starlette SessionMiddleware (signed cookie, SameSite=Lax, 14d)
- /api/auth/login, /logout, /whoami
- /api/auth/admin/users (admin role required)
- 3 roles: admin / analyst / viewer
- /api/v2/* protected by router-level Depends
- Static / and /backstage/ redirect anonymous to /login
- Initial admin seeded from ATLAS_ADMIN_USERNAME + ATLAS_ADMIN_PASSWORD
- Login UI at /login (vanilla HTML/CSS/JS)
- Admin user-management UI at /admin/users

Tests: pytest +27 cases (auth_hashing 3 + auth_storage 5 + auth_endpoints 6 + auth_admin 5 + auth_seed 3 + auth_middleware 3 + +2 from minor adjustments).

Next: Plan 3 (M3 Customer Data Import).
EOF
)"
git push origin yieldwise-v0.2-auth
```

---

## Self-Review (writing-plans)

**1. Spec coverage (against spec §5.1 M2):**

| Spec requirement | Plan 2 task | Status |
|---|---|---|
| `api/auth/` package | A.2, A.3, B.2, C.1, C.2, C.3 | ✅ |
| bcrypt + session cookie | A.2, B.3 | ✅ |
| 3 roles admin/analyst/viewer | A.3 (storage validation), B.1 (schema) | ✅ |
| `/admin/users` simple management page | E.1 | ✅ |
| All `/api/v2/*` session middleware | C.1 (router-level Depends) | ✅ |
| User table | A.3 (JSON-file storage) | ✅ |
| First-time seed admin from env | C.3 | ✅ |
| Drop SSO / SAML / LDAP | (out of scope, doc'd in security.md) | ✅ |

**2. Placeholder scan:** none — every code step shows actual code; every command shows the actual command.

**3. Type consistency:** `User`, `CurrentUser`, `Role`, `LoginRequest`, `LoginResponse`, `AdminUserCreate`, `AdminUserPatch`, `hash_password`, `verify_password`, `verify_credentials`, `current_user`, `require_role`, `read_session`, `store_session`, `clear_session`, `seed_initial_admin`, `StaticShellAuthGate` — names are consistent across tasks.

**4. Cross-bundle dependencies (sequential):**
- B1 → B2 → B3 → C1 → C2 → C3 → C4 → D1 → E1 → F1 → F2
- B1 + B2 + B3 = Phase A+B (foundation + endpoints)
- C1-C4 = Phase C (route protection + seed + docs)
- D1 = Phase D (login UI)
- E1 = Phase E (admin UI)
- F1-F4 = Phase F (ship)

**5. Open issues left to subsequent plans:**
- Audit log absent (security.md flags it; Plan 4 task)
- Rate limiting absent (security.md flags it; ops responsibility)
- Legacy `/api/*` (non-v2) routes unprotected — Plan 5 (M6) rebuilds them
- `phase1_smoke.py` authenticated smoke pass — F.1 TODO

---

## Hand-off

After Plan 2 ships and is tagged `yieldwise-v0.2-auth`, write Plan 3:
**M3 Customer Data Import** (~5–6 工程日).
