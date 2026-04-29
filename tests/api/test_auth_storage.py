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
