"""Unit tests for OSM way → GeoJSON Polygon conversion."""
from __future__ import annotations

from jobs.import_osm_geometry import osm_to_feature, way_to_polygon


def test_way_to_polygon_closes_open_ring() -> None:
    geom = [
        {"lat": 31.1, "lon": 121.5},
        {"lat": 31.1, "lon": 121.6},
        {"lat": 31.2, "lon": 121.6},
        {"lat": 31.2, "lon": 121.5},
    ]  # not closed
    coords = way_to_polygon(geom)
    assert coords is not None
    assert coords[0] == coords[-1], "ring must be closed"
    assert len(coords) == 5  # original 4 + closing copy


def test_way_to_polygon_keeps_already_closed_ring() -> None:
    geom = [
        {"lat": 31.1, "lon": 121.5},
        {"lat": 31.1, "lon": 121.6},
        {"lat": 31.2, "lon": 121.6},
        {"lat": 31.1, "lon": 121.5},
    ]  # already closed
    coords = way_to_polygon(geom)
    assert coords is not None
    assert len(coords) == 4


def test_way_to_polygon_rejects_too_short() -> None:
    assert way_to_polygon([{"lat": 1, "lon": 2}, {"lat": 1, "lon": 2}]) is None
    assert way_to_polygon([]) is None
    assert way_to_polygon(None) is None


def test_way_to_polygon_rejects_bad_coords() -> None:
    geom = [{"lat": "x", "lon": "y"}, {"lat": 1, "lon": 2}, {"lat": 3, "lon": 4}, {"lat": 5, "lon": 6}]
    assert way_to_polygon(geom) is None


def test_osm_to_feature_skips_non_way() -> None:
    elem = {"type": "node", "id": 1, "geometry": []}
    assert osm_to_feature(elem, "huangpu", "黄浦区", "2026-04-29T00:00:00+08:00") is None


def test_osm_to_feature_populates_district_and_polygon() -> None:
    elem = {
        "type": "way",
        "id": 178433181,
        "tags": {"building": "apartments", "name": "经纬公寓", "addr:street": "复兴中路"},
        "geometry": [
            {"lat": 31.21, "lon": 121.48},
            {"lat": 31.21, "lon": 121.49},
            {"lat": 31.22, "lon": 121.49},
            {"lat": 31.22, "lon": 121.48},
        ],
    }
    feat = osm_to_feature(elem, "huangpu", "黄浦区", "2026-04-29T00:00:00+08:00")
    assert feat is not None
    assert feat["type"] == "Feature"
    assert feat["properties"]["district_id"] == "huangpu"
    assert feat["properties"]["building_name"] == "经纬公寓"
    assert feat["properties"]["osm_addr_street"] == "复兴中路"
    assert feat["properties"]["source_ref"] == "osm-way-178433181"
    assert feat["geometry"]["type"] == "Polygon"
    # Polygon is wrapped in an outer array (the ring), and ring is closed
    assert feat["geometry"]["coordinates"][0][0] == feat["geometry"]["coordinates"][0][-1]
