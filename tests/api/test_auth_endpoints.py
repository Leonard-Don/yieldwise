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
