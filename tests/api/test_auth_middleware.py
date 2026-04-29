"""StaticShellAuthGate redirect behaviour."""
from __future__ import annotations

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
