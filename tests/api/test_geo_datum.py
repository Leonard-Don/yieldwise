"""Unit tests for the GCJ-02 ↔ WGS-84 datum conversion.

Verifies the forward/inverse transforms against a known Shanghai reference
pair, exercises the round-trip accuracy, and pins the magnitude of the
GCJ-02 offset that the matcher used to ignore.
"""
from __future__ import annotations

import math

from api.geo_datum import (
    datum_offset_meters,
    gcj02_to_wgs84,
    is_inside_china,
    wgs84_to_gcj02,
)

# ── Metres-per-degree at Shanghai's latitude (~31°N) for distance asserts ──
_M_PER_DEG_LAT = 111_320.0


def _meters_apart(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Equirectangular metres between two (lng, lat) points — fine sub-km."""
    lat_mid = math.radians((a[1] + b[1]) / 2.0)
    d_lat_m = (a[1] - b[1]) * _M_PER_DEG_LAT
    d_lng_m = (a[0] - b[0]) * _M_PER_DEG_LAT * math.cos(lat_mid)
    return math.hypot(d_lng_m, d_lat_m)


# ── Known reference pair ──────────────────────────────────────────────────
# Shanghai 人民广场 (People's Square), WGS-84 ≈ (121.47370, 31.23037).
# _SH_GCJ02 is the GCJ-02 image produced by the standard published transform —
# i.e. the coordinate AMap reports for that location. It is the canonical
# reference output: it agrees (sub-metre) with every open GCJ-02 library and
# with the offset AMap actually applies in Shanghai's inner ring.
_SH_WGS84 = (121.473700, 31.230370)
_SH_GCJ02 = (121.478223, 31.228428)


def test_wgs84_to_gcj02_matches_known_shanghai_point() -> None:
    got = wgs84_to_gcj02(*_SH_WGS84)
    # Agreement with the reference GCJ-02 value within ~1 m.
    assert _meters_apart(got, _SH_GCJ02) < 1.0


def test_gcj02_to_wgs84_matches_known_shanghai_point() -> None:
    got = gcj02_to_wgs84(*_SH_GCJ02)
    assert _meters_apart(got, _SH_WGS84) < 1.0


def test_round_trip_gcj_wgs_gcj_is_sub_meter() -> None:
    # GCJ-02 → WGS-84 → GCJ-02 must return to the start sub-meter.
    start = _SH_GCJ02
    back = wgs84_to_gcj02(*gcj02_to_wgs84(*start))
    assert _meters_apart(start, back) < 0.001  # sub-millimetre, in fact


def test_round_trip_wgs_gcj_wgs_is_sub_meter() -> None:
    start = (121.473700, 31.230370)
    back = gcj02_to_wgs84(*wgs84_to_gcj02(*start))
    assert _meters_apart(start, back) < 0.001


def test_round_trip_holds_across_shanghai_grid() -> None:
    # Sweep a grid covering all 16 Shanghai districts; every point must
    # round-trip to sub-millimetre.
    worst = 0.0
    lng = 120.9
    while lng <= 122.0:
        lat = 30.7
        while lat <= 31.9:
            start = (lng, lat)
            back = gcj02_to_wgs84(*wgs84_to_gcj02(*start))
            worst = max(worst, _meters_apart(start, back))
            lat += 0.1
        lng += 0.1
    assert worst < 0.001


def test_offset_is_not_negligible_in_shanghai() -> None:
    # The whole point of the bug: the GCJ-02 offset in Shanghai is hundreds of
    # metres — far larger than a building, and larger than the old 200-250 m
    # match threshold. Pin it so a regression that silently zeroes the
    # transform fails loudly.
    offset = datum_offset_meters(*_SH_WGS84)
    assert 300.0 < offset < 700.0


def test_forward_transform_actually_moves_the_point() -> None:
    moved = wgs84_to_gcj02(*_SH_WGS84)
    assert moved != _SH_WGS84
    # Offset is small in degrees but non-trivial.
    assert abs(moved[0] - _SH_WGS84[0]) > 1e-4
    assert abs(moved[1] - _SH_WGS84[1]) > 1e-4


def test_inverse_undoes_forward_to_sub_meter() -> None:
    # Independent of the reference constants: forward then inverse on a fresh
    # WGS-84 point must land back within a millimetre.
    for pt in [(121.5, 31.2), (121.62, 31.05), (121.30, 31.50), (121.80, 30.90)]:
        recovered = gcj02_to_wgs84(*wgs84_to_gcj02(*pt))
        assert _meters_apart(pt, recovered) < 0.001


def test_points_outside_china_pass_through_unchanged() -> None:
    # GCJ-02 obfuscation is PRC-only; out-of-border points must be identity.
    for pt in [(-122.4194, 37.7749), (139.6917, 35.6895), (0.0, 0.0)]:
        assert wgs84_to_gcj02(*pt) == pt
        assert gcj02_to_wgs84(*pt) == pt


def test_is_inside_china_bounding_box() -> None:
    assert is_inside_china(121.47, 31.23) is True  # Shanghai
    assert is_inside_china(116.40, 39.90) is True  # Beijing
    assert is_inside_china(-122.42, 37.77) is False  # San Francisco
    assert is_inside_china(139.69, 35.69) is False  # Tokyo


def test_conversion_accepts_string_or_int_coordinates() -> None:
    # AMap loaders carry coords as strings (e.g. "121.473700"); the transform
    # must coerce rather than throw.
    got = wgs84_to_gcj02("121.473700", "31.230370")  # type: ignore[arg-type]
    assert _meters_apart(got, _SH_GCJ02) < 1.0


def test_gcj02_to_wgs84_is_close_to_identity_distance() -> None:
    # Sanity: inverse output is offset from input by the same ~hundreds of m
    # as the forward transform — i.e. it really removed the obfuscation.
    g = _SH_GCJ02
    w = gcj02_to_wgs84(*g)
    assert 300.0 < _meters_apart(g, w) < 700.0
