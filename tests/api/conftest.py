"""API-test fixtures for the public local workbench."""
from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture()
def client() -> Iterator[TestClient]:
    """Function-scoped client for public local routes."""
    yield TestClient(app)
