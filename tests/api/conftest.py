"""API-test fixtures.

Two separate concerns:

1. Most existing v2 tests inherit a session-scoped ``client`` fixture from
   ``tests/conftest.py`` and exercise endpoints with no notion of auth. After
   B3-C.1 those endpoints require a logged-in session. Rather than migrate
   every single ``def test_xxx(client)`` to ``def test_xxx(authed_client)``,
   we shadow the inherited ``client`` here with a function-scoped fixture
   that installs a ``current_user`` dependency override on the app, yields a
   fresh ``TestClient``, and clears the override on teardown. This keeps
   existing tests untouched while satisfying the new auth gate.

2. Two named fixtures from the plan — ``authed_client`` and ``admin_client``
   — are provided for tests that need to exercise the real login flow
   (e.g. session-cookie behaviour, admin role checks). Those go through
   ``/api/auth/login`` and carry a real session cookie.
"""
from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.auth import storage as user_store
from api.auth.deps import current_user
from api.main import app
from api.schemas.auth import CurrentUser


def _stub_current_user() -> CurrentUser:
    """Return a fake analyst user; bypasses session-cookie + storage lookup."""
    return CurrentUser(
        id="test-stub-user",
        username="test-stub",
        role="analyst",
        disabled=False,
    )


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Function-scoped TestClient with current_user overridden to a stub.

    Shadows the session-scoped ``client`` fixture in ``tests/conftest.py``.
    Tests that want real login behaviour should use ``authed_client`` or
    create a raw ``TestClient(app)`` directly instead.
    """
    app.dependency_overrides[current_user] = _stub_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(current_user, None)


@pytest.fixture()
def auth_test_env(tmp_path, monkeypatch):
    """Isolated env for tests that exercise the real auth flow."""
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    yield tmp_path


@pytest.fixture()
def authed_client(auth_test_env) -> Iterator[TestClient]:
    """A TestClient logged in as an analyst user via /api/auth/login."""
    user_store.create_user(username="tester", password="hunter2", role="analyst")
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"username": "tester", "password": "hunter2"}
    )
    assert response.status_code == 200, response.text
    yield client


@pytest.fixture()
def admin_client(auth_test_env) -> Iterator[TestClient]:
    """A TestClient logged in as an admin user via /api/auth/login."""
    user_store.create_user(username="boss", password="hunter2", role="admin")
    client = TestClient(app)
    response = client.post(
        "/api/auth/login", json={"username": "boss", "password": "hunter2"}
    )
    assert response.status_code == 200, response.text
    yield client
