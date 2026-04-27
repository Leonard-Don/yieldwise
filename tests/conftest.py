from __future__ import annotations

import os

import pytest

os.environ.setdefault("ATLAS_ENABLE_DEMO_MOCK", "1")

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402
from api.backstage.runs import _runtime_data_state_cached  # noqa: E402

_runtime_data_state_cached.cache_clear()


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
