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


def test_upload_portfolio_creates_staged_run(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="al", password="hunter22", role="analyst")
    client = TestClient(app)
    _login(client, "al", "hunter22")
    csv_body = (
        "project_name,address,building_no,unit_type,monthly_rent_cny,"
        "occupancy_rate_pct,move_in_date,longitude,latitude\n"
        "Alpha,addr,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    ).encode("utf-8")
    r = client.post(
        "/api/v2/customer-data/imports",
        data={"type": "portfolio"},
        files={"file": ("portfolio.csv", csv_body, "text/csv")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["run"]["rowCount"] == 1
    assert body["run"]["errorCount"] == 0
    assert body["run"]["clientId"] == "al"
    assert body["errorsPreview"] == []


def test_viewer_cannot_upload(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="v", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "v", "hunter22")
    csv_body = b"project_name,longitude,latitude\nA,121,31\n"
    r = client.post(
        "/api/v2/customer-data/imports",
        data={"type": "portfolio"},
        files={"file": ("p.csv", csv_body, "text/csv")},
    )
    assert r.status_code == 403


def test_get_import_status_unknown_returns_404(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="u", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "u", "hunter22")
    r = client.get("/api/v2/customer-data/imports/does-not-exist")
    assert r.status_code == 404
