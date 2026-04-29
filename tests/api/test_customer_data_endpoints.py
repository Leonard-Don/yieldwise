"""Customer data endpoint tests — start with template download."""
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
    return client.post("/api/auth/login", json={"username": username, "password": password})


def _seed_and_login(role="analyst"):
    user_store.create_user(username="u", password="hunter22", role=role)
    client = TestClient(app)
    _login(client, "u", "hunter22")
    return client


def test_portfolio_template_downloads_with_bom():
    client = _seed_and_login()
    r = client.get("/api/v2/customer-data/templates/portfolio.csv")
    assert r.status_code == 200
    # First 3 bytes must be the UTF-8 BOM
    assert r.content.startswith(b"\xef\xbb\xbf")
    text = r.content.decode("utf-8-sig")
    assert "project_name" in text.split("\n", 1)[0]
    assert r.headers.get("content-type", "").startswith("text/csv")


def test_unknown_template_404():
    client = _seed_and_login()
    r = client.get("/api/v2/customer-data/templates/unknown.csv")
    assert r.status_code == 404
