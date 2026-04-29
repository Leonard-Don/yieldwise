"""Aggregation-layer filter that excludes browser-smoke-* fixture rows.

scripts/browser_capture_smoke.py creates fake captures (default 323 万 sale,
12200 元 rent) to verify the capture-submit round-trip. Without filtering,
those fixtures contaminate analytical aggregations like staged_community_dataset.
"""
from __future__ import annotations

from api.service import _filter_out_smoke_fixtures


def test_filter_drops_browser_smoke_rows() -> None:
    rows = [
        {"source_listing_id": "browser-smoke-sale-20260414143945", "monthly_rent": 12200},
        {"source_listing_id": "PB-RENT-001", "monthly_rent": 23800},
        {"source_listing_id": "browser-smoke-rent-20260414144002", "monthly_rent": 12200},
        {"source_listing_id": "real-listing-xyz", "monthly_rent": 8400},
    ]
    out = _filter_out_smoke_fixtures(rows)
    ids = [r["source_listing_id"] for r in out]
    assert ids == ["PB-RENT-001", "real-listing-xyz"]


def test_filter_handles_empty_input() -> None:
    assert _filter_out_smoke_fixtures([]) == []


def test_filter_handles_missing_listing_id() -> None:
    rows = [
        {"foo": "bar"},                                # no source_listing_id at all
        {"source_listing_id": None, "x": 1},           # None
        {"source_listing_id": "", "x": 2},             # empty
        {"source_listing_id": "browser-smoke-sale-1"},  # smoke
    ]
    out = _filter_out_smoke_fixtures(rows)
    assert len(out) == 3  # only the smoke row removed
    assert all(not str(r.get("source_listing_id") or "").startswith("browser-smoke-") for r in out)


def test_filter_preserves_row_order() -> None:
    rows = [
        {"source_listing_id": "PB-1"},
        {"source_listing_id": "browser-smoke-X"},
        {"source_listing_id": "PB-2"},
        {"source_listing_id": "browser-smoke-Y"},
        {"source_listing_id": "PB-3"},
    ]
    ids = [r["source_listing_id"] for r in _filter_out_smoke_fixtures(rows)]
    assert ids == ["PB-1", "PB-2", "PB-3"]
