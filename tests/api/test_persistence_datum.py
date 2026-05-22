"""Unit tests for the persistence-layer datum resolution helper.

``_resolve_datum_pair`` decides what goes into the ``centroid_gcj02`` and
``centroid_wgs84`` columns for a reference-catalog row. The contract: the two
columns must always be a *true datum pair*, never the same numbers copied into
both — which is exactly the bug this work fixes.
"""
from __future__ import annotations

import math

from api.geo_datum import gcj02_to_wgs84, wgs84_to_gcj02
from api.persistence import _coerce_coord, _resolve_datum_pair, _upsert_reference_catalog

_M_PER_DEG_LAT = 111_320.0


def _meters_apart(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat_mid = math.radians((a[1] + b[1]) / 2.0)
    d_lat_m = (a[1] - b[1]) * _M_PER_DEG_LAT
    d_lng_m = (a[0] - b[0]) * _M_PER_DEG_LAT * math.cos(lat_mid)
    return math.hypot(d_lng_m, d_lat_m)


class _RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple) -> None:
        self.calls.append((sql, params))


def _jsonb(value):
    return value


def test_coerce_coord_parses_float_int_string() -> None:
    assert _coerce_coord(121.5) == 121.5
    assert _coerce_coord("121.5") == 121.5
    assert _coerce_coord(31) == 31.0
    assert _coerce_coord(None) is None
    assert _coerce_coord("") is None
    assert _coerce_coord("not-a-number") is None


def test_untagged_pair_is_treated_as_gcj02() -> None:
    # AMAP rows historically carry an untagged center_lng/center_lat — GCJ-02.
    gcj, wgs = _resolve_datum_pair({"center_lng": "121.5", "center_lat": "31.2"})
    assert gcj == (121.5, 31.2)
    assert wgs is not None
    # WGS-84 column is the *converted* value, not a copy of the GCJ-02 pair.
    assert wgs != gcj
    assert wgs == gcj02_to_wgs84(121.5, 31.2)


def test_two_columns_are_a_real_datum_pair_not_a_copy() -> None:
    gcj, wgs = _resolve_datum_pair({"center_lng": 121.47, "center_lat": 31.23})
    assert gcj is not None and wgs is not None
    # The Shanghai datum gap is hundreds of metres — the regression that
    # copied one pair into both columns would make this distance zero.
    assert _meters_apart(gcj, wgs) > 300.0


def test_explicit_wgs84_pair_is_trusted_verbatim() -> None:
    gcj, wgs = _resolve_datum_pair({
        "center_lng": "121.500000",
        "center_lat": "31.200000",
        "center_lng_wgs84": "121.495400",
        "center_lat_wgs84": "31.198300",
    })
    assert wgs == (121.4954, 31.1983)
    # GCJ-02 column still comes from the explicit GCJ-02 primary pair.
    assert gcj == (121.5, 31.2)


def test_explicit_wgs84_backfills_gcj02_when_primary_absent() -> None:
    # Only a WGS-84 pair supplied → GCJ-02 column is derived by forward xform.
    gcj, wgs = _resolve_datum_pair({
        "center_lng_wgs84": "121.4954",
        "center_lat_wgs84": "31.1983",
    })
    assert wgs == (121.4954, 31.1983)
    assert gcj == wgs84_to_gcj02(121.4954, 31.1983)


def test_wgs84_datum_tag_inverts_resolution() -> None:
    # coordinate_datum=wgs84 → the primary pair IS the WGS-84 column, and the
    # GCJ-02 column is the forward transform of it.
    gcj, wgs = _resolve_datum_pair({
        "center_lng": "121.4954",
        "center_lat": "31.1983",
        "coordinate_datum": "wgs84",
    })
    assert wgs == (121.4954, 31.1983)
    assert gcj == wgs84_to_gcj02(121.4954, 31.1983)


def test_epsg4326_datum_tag_inverts_resolution() -> None:
    gcj, wgs = _resolve_datum_pair({
        "center_lng": "121.4954",
        "center_lat": "31.1983",
        "coordinate_datum": " EPSG:4326 ",
    })
    assert wgs == (121.4954, 31.1983)
    assert gcj == wgs84_to_gcj02(121.4954, 31.1983)


def test_missing_coordinates_resolve_to_none_pair() -> None:
    assert _resolve_datum_pair({}) == (None, None)
    assert _resolve_datum_pair({"center_lng": "", "center_lat": ""}) == (None, None)
    assert _resolve_datum_pair({"center_lng": "121.5"}) == (None, None)


def test_reference_catalog_upsert_persists_both_community_datums() -> None:
    cur = _RecordingCursor()
    _upsert_reference_catalog(
        cur,
        _jsonb,
        [
            {
                "community_id": "pudong-001",
                "district_id": "pudong",
                "community_name": "汤臣一品",
                "aliases": ["汤臣一品"],
                "center_lng": "121.500000",
                "center_lat": "31.200000",
                "coordinate_datum": "gcj02",
            }
        ],
        [],
    )

    sql, params = cur.calls[0]
    expected_wgs = gcj02_to_wgs84(121.5, 31.2)

    assert "centroid_gcj02" in sql
    assert "centroid_wgs84" in sql
    assert params[4:8] == (121.5, 31.2, 121.5, 31.2)
    assert params[8:12] == (*expected_wgs, *expected_wgs)


def test_reference_catalog_upsert_persists_both_building_datums() -> None:
    cur = _RecordingCursor()
    _upsert_reference_catalog(
        cur,
        _jsonb,
        [],
        [
            {
                "building_id": "pudong-001-b001",
                "community_id": "pudong-001",
                "building_name": "1幢",
                "center_lng_wgs84": "121.495400",
                "center_lat_wgs84": "31.198300",
            }
        ],
    )

    sql, params = cur.calls[0]
    expected_gcj = wgs84_to_gcj02(121.4954, 31.1983)

    assert "geom_gcj02" in sql
    assert "geom_wgs84" in sql
    assert params[5:9] == (*expected_gcj, *expected_gcj)
    assert params[9:13] == (121.4954, 31.1983, 121.4954, 31.1983)
