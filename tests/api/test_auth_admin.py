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
