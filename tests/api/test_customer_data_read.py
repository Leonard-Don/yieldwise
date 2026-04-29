"""Customer-data read endpoint tests (no-DB path)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    yield


def _seed_login(role="viewer"):
    user_store.create_user(username="r", password="hunter22", role=role)
    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "r", "password": "hunter22"})
    return client


def test_portfolio_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/portfolio")
    assert r.status_code == 200
    assert r.json() == []


def test_pipeline_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/pipeline")
    assert r.status_code == 200
    assert r.json() == []


def test_comp_set_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/comp_set")
    assert r.status_code == 200
    assert r.json() == []
