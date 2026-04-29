"""Unit tests for OSM-to-community spatial matcher."""
from __future__ import annotations

from jobs.match_osm_to_communities import (
    dist_meters,
    index_communities_by_district,
    match_feature,
    polygon_centroid,
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
