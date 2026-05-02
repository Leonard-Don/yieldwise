"""Unit tests for cross-source geo-run comparator."""
from __future__ import annotations

from jobs.compare_geo_runs import (
    build_district_index,
    feature_centroid,
    find_nearest,
)


def _feat(district: str, ring: list[list[float]], **props) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {"district_id": district, **props},
    }


def test_feature_centroid_basic_square() -> None:
    feat = _feat("huangpu", [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]])
    cx, cy = feature_centroid(feat)
    # 5 points, including closing copy → mean ≈ 0.8
    assert abs(cx - 0.8) < 0.01
    assert abs(cy - 0.8) < 0.01


def test_feature_centroid_handles_non_polygon() -> None:
    feat = {"geometry": {"type": "Point", "coordinates": [121.5, 31.2]}, "properties": {}}
    assert feature_centroid(feat) is None


def test_district_index_buckets_by_district() -> None:
    feats = [
        _feat("huangpu", [[121.48, 31.21], [121.49, 31.21], [121.49, 31.22], [121.48, 31.22], [121.48, 31.21]]),
        _feat("huangpu", [[121.50, 31.23], [121.51, 31.23], [121.51, 31.24], [121.50, 31.24], [121.50, 31.23]]),
        _feat("pudong",  [[121.55, 31.22], [121.56, 31.22], [121.56, 31.23], [121.55, 31.23], [121.55, 31.22]]),
    ]
    idx = build_district_index(feats)
    assert sorted(idx.keys()) == ["huangpu", "pudong"]
    assert len(idx["huangpu"]) == 2
    assert len(idx["pudong"]) == 1


def test_find_nearest_picks_closest_within_threshold() -> None:
    feats = [
        _feat("huangpu", [[121.48, 31.21], [121.49, 31.21], [121.49, 31.22], [121.48, 31.22], [121.48, 31.21]],
              osmId="osm-near"),
        _feat("huangpu", [[121.55, 31.25], [121.56, 31.25], [121.56, 31.26], [121.55, 31.26], [121.55, 31.25]],
              osmId="osm-far"),
    ]
    idx = build_district_index(feats)
    # query point very close to centroid of "osm-near" (centroid ≈ 121.484, 31.214)
    distance, match = find_nearest(121.4845, 31.2145, "huangpu", idx, max_m=200.0)
    assert match is not None
    assert match["properties"]["osmId"] == "osm-near"
    assert distance < 200


def test_find_nearest_returns_inf_when_no_district_features() -> None:
    distance, match = find_nearest(121.5, 31.2, "no-such-district", {}, max_m=200.0)
    assert distance == float("inf")
    assert match is None


def test_find_nearest_returns_inf_when_too_far() -> None:
    feats = [
        _feat("huangpu", [[121.55, 31.25], [121.56, 31.25], [121.56, 31.26], [121.55, 31.26], [121.55, 31.25]],
              osmId="osm-far"),
    ]
    idx = build_district_index(feats)
    distance, match = find_nearest(121.48, 31.21, "huangpu", idx, max_m=200.0)  # ~7km away
    assert distance == float("inf")
    assert match is None
