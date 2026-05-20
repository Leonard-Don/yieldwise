from __future__ import annotations

from jobs.import_geo_assets import BuildingCatalogEntry, normalized_feature


def _catalog_entry() -> BuildingCatalogEntry:
    return BuildingCatalogEntry(
        district_id="pudong",
        district_name="浦东新区",
        district_short_name="浦东",
        community_id="pudong-001",
        community_name="汤臣一品",
        building_id="pudong-001-b001",
        building_name="1号楼",
        total_floors=40,
    )


def test_normalized_feature_preserves_coordinate_datum() -> None:
    feature = {
        "type": "Feature",
        "properties": {
            "source_ref": "amap://aoi/footprint-1",
            "coordinate_datum": "gcj02",
        },
        "geometry": {"type": "Polygon", "coordinates": [[]]},
    }

    normalized = normalized_feature(
        feature,
        _catalog_entry(),
        provider_id="amap-aoi-poi",
        captured_at="2026-05-21T01:00:00+08:00",
        resolution_notes="命中 building_id",
    )

    assert normalized["properties"]["coordinate_datum"] == "gcj02"
