"""T1 regression: verify psycopg pool is the single connection path.

Spec §5.4 T1. Pool wired at api/persistence.py:55-72.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from api import persistence


def test_get_pool_returns_singleton_per_dsn(monkeypatch):
    """Same DSN -> same pool object (registry invariant).

    We stub ``psycopg_pool.ConnectionPool`` so the test does not require a
    reachable database — the registry/singleton behaviour is independent of
    pool internals.
    """
    monkeypatch.setattr(persistence, "_POOL_REGISTRY", {})

    class _FakePool:
        def __init__(self, *args, **kwargs):
            self.kwargs = kwargs
            self.closed = False

        def close(self):
            self.closed = True

    import psycopg_pool

    monkeypatch.setattr(psycopg_pool, "ConnectionPool", _FakePool)

    fake_dsn = "postgresql://localhost/yieldwise_pool_singleton_check"
    pool1 = persistence._get_pool(fake_dsn)
    pool2 = persistence._get_pool(fake_dsn)
    try:
        assert pool1 is pool2
    finally:
        persistence._POOL_REGISTRY.pop(fake_dsn, None)
        try:
            pool1.close()
        except Exception:
            pass


def test_postgres_connection_requires_dsn(monkeypatch):
    """Without POSTGRES_DSN env, postgres_connection() must raise — never silent fallback."""
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    monkeypatch.setattr(persistence, "_POOL_REGISTRY", {})
    with pytest.raises(RuntimeError, match="POSTGRES_DSN"):
        with persistence.postgres_connection():
            pass


@pytest.mark.skipif(
    not os.environ.get("POSTGRES_DSN"),
    reason="needs live POSTGRES_DSN",
)
def test_pool_handles_concurrent_queries():
    """50 queries across 20 threads should all succeed against pool size 8."""
    def query():
        with persistence.postgres_cursor() as cur:
            cur.execute("SELECT 1 AS one")
            return cur.fetchone()

    with ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(lambda _: query(), range(50)))

    assert len(results) == 50
    assert all(r["one"] == 1 for r in results)
