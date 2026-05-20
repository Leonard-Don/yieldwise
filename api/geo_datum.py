"""GCJ-02 ↔ WGS-84 datum conversion.

Chinese map providers (高德/AMap, 腾讯, 百度's GCJ layer) publish coordinates
in **GCJ-02** ("火星坐标系" / Mars Coordinates) — a state-mandated obfuscation
of true WGS-84. OpenStreetMap, GPS hardware and Overpass all return plain
WGS-84. In Shanghai the GCJ-02 offset is roughly 300-600 m, so mixing the two
datums without conversion silently corrupts every cross-source spatial join.

This module implements the standard, widely-published GCJ-02 forward transform
and the iterative numerical inverse:

- ``wgs84_to_gcj02`` — exact forward transform (the published algorithm).
- ``gcj02_to_wgs84`` — fixed-point inverse. The forward transform has no
  closed-form inverse, but it is a near-identity perturbation, so a handful of
  fixed-point iterations converge to sub-millimetre accuracy. Three iterations
  already drive the residual well below 1 mm anywhere in China; we use four
  for headroom.

All coordinates are ``(lng, lat)`` decimal-degree pairs — matching GeoJSON
axis order and the rest of the codebase (``center_lng`` / ``center_lat``).

Coordinates outside mainland China are returned unchanged: GCJ-02 obfuscation
is only applied inside the PRC land border, and applying the offset to e.g.
Hong Kong or open-ocean points would *introduce* error rather than remove it.
"""
from __future__ import annotations

import math

__all__ = [
    "wgs84_to_gcj02",
    "gcj02_to_wgs84",
    "is_inside_china",
    "datum_offset_meters",
    "normalize_coordinate_datum",
]

# Krasovsky 1940 ellipsoid — the ellipsoid the GCJ-02 algorithm is defined on.
_A = 6_378_245.0  # semi-major axis, metres
_EE = 0.006_693_421_622_965_943  # first eccentricity squared

# GCJ-02 → WGS-84 fixed-point iteration count. The forward transform is a
# near-identity map (offset ~ 1e-3°), so the inverse converges geometrically;
# 3 iterations reach sub-mm, 4 leaves a comfortable safety margin.
_INVERSE_ITERATIONS = 4

# Approximate metres-per-degree at Shanghai's latitude (~31°N). Used only by
# datum_offset_meters() for human-readable diagnostics — not by the transform.
_M_PER_DEG_LAT = 111_320.0


def normalize_coordinate_datum(value: object) -> str | None:
    """Return the canonical datum id used by API/import contracts."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    compact = raw.lower().replace("-", "").replace("_", "").replace(" ", "")
    if compact == "gcj02":
        return "gcj02"
    if compact == "wgs84":
        return "wgs84"
    return raw


def is_inside_china(lng: float, lat: float) -> bool:
    """Rough mainland-China bounding box.

    GCJ-02 obfuscation is applied only inside the PRC land border. Outside this
    box the transform is an identity, so coordinates pass through untouched.
    This is the same crude rectangle used by every open GCJ-02 implementation;
    it intentionally errs toward "inside" for border regions.
    """
    return 73.66 < lng < 135.05 and 3.86 < lat < 53.55


def _transform_lat(x: float, y: float) -> float:
    ret = (
        -100.0
        + 2.0 * x
        + 3.0 * y
        + 0.2 * y * y
        + 0.1 * x * y
        + 0.2 * math.sqrt(abs(x))
    )
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x: float, y: float) -> float:
    ret = (
        300.0
        + x
        + 2.0 * y
        + 0.1 * x * x
        + 0.1 * x * y
        + 0.1 * math.sqrt(abs(x))
    )
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret


def _delta(lng: float, lat: float) -> tuple[float, float]:
    """The GCJ-02 perturbation (d_lng, d_lat) in degrees at a WGS-84 point.

    This is the core published algorithm: it returns the offset that, added to
    a WGS-84 coordinate, yields the GCJ-02 coordinate.
    """
    d_lat = _transform_lat(lng - 105.0, lat - 35.0)
    d_lng = _transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * math.pi
    magic = math.sin(rad_lat)
    magic = 1.0 - _EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((_A * (1.0 - _EE)) / (magic * sqrt_magic) * math.pi)
    d_lng = (d_lng * 180.0) / (_A / sqrt_magic * math.cos(rad_lat) * math.pi)
    return d_lng, d_lat


def wgs84_to_gcj02(lng: float, lat: float) -> tuple[float, float]:
    """Convert a WGS-84 ``(lng, lat)`` to GCJ-02.

    This is the exact, published forward transform. Coordinates outside
    mainland China are returned unchanged.
    """
    lng = float(lng)
    lat = float(lat)
    if not is_inside_china(lng, lat):
        return lng, lat
    d_lng, d_lat = _delta(lng, lat)
    return lng + d_lng, lat + d_lat


def gcj02_to_wgs84(lng: float, lat: float) -> tuple[float, float]:
    """Convert a GCJ-02 ``(lng, lat)`` back to WGS-84.

    The forward transform has no closed form inverse. Because it is a
    near-identity perturbation we solve ``wgs84 + delta(wgs84) == gcj02`` by
    fixed-point iteration: start from the GCJ-02 point as the WGS-84 estimate,
    then repeatedly subtract the delta evaluated at the current estimate. The
    iteration contracts geometrically and reaches sub-millimetre accuracy in a
    few steps anywhere in China.

    Coordinates outside mainland China are returned unchanged.
    """
    lng = float(lng)
    lat = float(lat)
    if not is_inside_china(lng, lat):
        return lng, lat
    # Initial estimate: the GCJ-02 point itself (offset is small).
    est_lng, est_lat = lng, lat
    for _ in range(_INVERSE_ITERATIONS):
        d_lng, d_lat = _delta(est_lng, est_lat)
        est_lng = lng - d_lng
        est_lat = lat - d_lat
    return est_lng, est_lat


def datum_offset_meters(lng: float, lat: float) -> float:
    """Approximate magnitude of the GCJ-02 offset at a WGS-84 point, in metres.

    Diagnostic helper — quantifies how far apart the two datums place the same
    physical location. Uses a local equirectangular approximation, which is
    accurate to well under 1 % at the sub-kilometre offsets GCJ-02 produces.
    """
    g_lng, g_lat = wgs84_to_gcj02(lng, lat)
    d_lat_m = (g_lat - lat) * _M_PER_DEG_LAT
    d_lng_m = (g_lng - lng) * _M_PER_DEG_LAT * math.cos(math.radians(lat))
    return math.hypot(d_lng_m, d_lat_m)
