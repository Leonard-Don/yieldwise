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
