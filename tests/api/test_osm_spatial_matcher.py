"""Unit tests for OSM-to-community spatial matcher."""
from __future__ import annotations

from api.geo_datum import gcj02_to_wgs84
from jobs.match_osm_to_communities import (
    dist_meters,
    index_communities_by_district,
    match_feature,
    parse_args,
    polygon_centroid,
    resolve_community_wgs84,
)


def test_dist_meters_zero_for_same_point() -> None:
    assert dist_meters(121.5, 31.2, 121.5, 31.2) == 0


def test_dist_meters_lat_delta() -> None:
    # 0.001° lat ≈ 111m
    d = dist_meters(121.5, 31.2, 121.5, 31.201)
    assert 100 < d < 120


def test_dist_meters_lng_delta() -> None:
    # 0.001° lng at 31°N ≈ 95m
    d = dist_meters(121.5, 31.2, 121.501, 31.2)
    assert 90 < d < 100


def test_polygon_centroid_simple_square() -> None:
    coords = [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]
    cx, cy = polygon_centroid(coords)
    # average of all 5 points (the closing copy biases slightly)
    assert abs(cx - 0.8) < 0.01
    assert abs(cy - 0.8) < 0.01


def test_polygon_centroid_handles_nested_outer_ring() -> None:
    # GeoJSON shape: [[outer ring], [hole], ...] — function handles both
    nested = [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
    cx, cy = polygon_centroid(nested)
    assert abs(cx - 4.0) < 0.01
    assert abs(cy - 4.0) < 0.01


def test_polygon_centroid_empty_returns_none() -> None:
    assert polygon_centroid([]) is None


def test_match_feature_picks_closest_within_radius() -> None:
    feat = {
        "geometry": {"type": "Polygon", "coordinates": [[
            [121.500, 31.200], [121.501, 31.200], [121.501, 31.201], [121.500, 31.201], [121.500, 31.200],
        ]]},
        "properties": {"district_id": "huangpu"},
    }
    by_district = index_communities_by_district([
        # ~50m away (close enough)
        {"community_id": "huangpu-near", "community_name": "近邻", "district_id": "huangpu",
         "district_name": "黄浦区", "lng": 121.5005, "lat": 31.2015},
        # ~500m away (too far for 200m threshold)
        {"community_id": "huangpu-far", "community_name": "远邻", "district_id": "huangpu",
         "district_name": "黄浦区", "lng": 121.506, "lat": 31.205},
        # in different district, ignored entirely by the district pre-filter
        {"community_id": "pudong-other", "community_name": "浦东", "district_id": "pudong",
         "district_name": "浦东新区", "lng": 121.5005, "lat": 31.2015},
    ])
    community, distance = match_feature(feat, by_district, max_meters=200.0)
    assert community["community_id"] == "huangpu-near"
    assert distance < 200


def test_match_feature_returns_empty_when_too_far() -> None:
    feat = {
        "geometry": {"type": "Polygon", "coordinates": [[
            [121.500, 31.200], [121.501, 31.200], [121.501, 31.201], [121.500, 31.201], [121.500, 31.200],
        ]]},
        "properties": {"district_id": "huangpu"},
    }
    by_district = index_communities_by_district([
        # 1km away — beyond default 200m threshold
        {"community_id": "huangpu-far", "community_name": "远", "district_id": "huangpu",
         "district_name": "黄浦区", "lng": 121.510, "lat": 31.210},
    ])
    community, distance = match_feature(feat, by_district, max_meters=200.0)
    assert community == {}
    assert distance is None


def test_match_feature_skips_non_polygon() -> None:
    feat = {"geometry": {"type": "Point", "coordinates": [121.5, 31.2]}, "properties": {}}
    community, distance = match_feature(feat, {"any": []}, max_meters=200.0)
    assert community == {}
    assert distance is None


# ── Datum resolution ──────────────────────────────────────────────────────
# OSM footprints are WGS-84; AMAP community centroids are GCJ-02. The matcher
# resolves every community to WGS-84 before any distance comparison.


def test_resolve_community_untagged_pair_is_converted_from_gcj02() -> None:
    # An untagged center_lng/center_lat pair is treated as GCJ-02 (the AMAP
    # default) and converted to WGS-84.
    row = {"center_lng": "121.500000", "center_lat": "31.200000"}
    resolved = resolve_community_wgs84(row)
    expected = gcj02_to_wgs84(121.5, 31.2)
    assert resolved is not None
    assert abs(resolved[0] - expected[0]) < 1e-9
    assert abs(resolved[1] - expected[1]) < 1e-9
    # And it actually moved — not the raw GCJ-02 numbers.
    assert resolved != (121.5, 31.2)


def test_resolve_community_prefers_explicit_wgs84_pair() -> None:
    # When an explicit WGS-84 pair is present it is trusted verbatim.
    row = {
        "center_lng": "121.500000",
        "center_lat": "31.200000",
        "center_lng_wgs84": "121.495400",
        "center_lat_wgs84": "31.198300",
    }
    resolved = resolve_community_wgs84(row)
    assert resolved == (121.4954, 31.1983)


def test_resolve_community_wgs84_datum_tag_passes_through() -> None:
    # coordinate_datum=wgs84 means the primary pair is already WGS-84.
    row = {"center_lng": "121.4954", "center_lat": "31.1983", "coordinate_datum": "wgs84"}
    assert resolve_community_wgs84(row) == (121.4954, 31.1983)


def test_resolve_community_missing_coords_returns_none() -> None:
    assert resolve_community_wgs84({}) is None
    assert resolve_community_wgs84({"center_lng": "", "center_lat": ""}) is None
    assert resolve_community_wgs84({"center_lng": 0, "center_lat": 0}) is None


def test_datum_correction_changes_match_outcome() -> None:
    # The crux of the bug: a building footprint in true WGS-84 sits ~480 m from
    # the *raw* GCJ-02 community centroid but right on top of the *converted*
    # WGS-84 centroid. With the correction the match flips from miss to hit at
    # a real building-scale threshold.
    gcj_centroid = (121.500000, 31.200000)  # what AMAP stores
    wgs_centroid = gcj02_to_wgs84(*gcj_centroid)  # the true location
    # OSM footprint centroid sits ~15 m from the true WGS-84 centroid.
    osm_cx = wgs_centroid[0] + 0.00015
    osm_cy = wgs_centroid[1]

    raw_gap = dist_meters(osm_cx, osm_cy, *gcj_centroid)
    corrected_gap = dist_meters(osm_cx, osm_cy, *wgs_centroid)

    assert raw_gap > 300  # uncorrected: way beyond any building-scale radius
    assert corrected_gap < 60  # corrected: a real, tight match


def test_parse_args_preserves_legacy_default_match_radius(monkeypatch) -> None:
    # Existing no-argument matcher runs used a 200 m radius. Datum correction
    # changes *what* is measured, but the CLI default stays compatible so
    # unattended scripts do not silently shrink their output set.
    monkeypatch.setattr("sys.argv", ["match_osm_to_communities.py"])
    args = parse_args()
    assert args.max_meters == 200.0
