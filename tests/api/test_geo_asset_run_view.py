from __future__ import annotations

from api.backstage.geo_qa import build_geo_asset_run_view


def test_feature_preview_preserves_coordinate_datum(monkeypatch) -> None:
    from api import service

    monkeypatch.setattr(service, "flatten_communities", lambda **_: [])
    monkeypatch.setattr(service, "floor_watchlist", lambda **_: [])

    view = build_geo_asset_run_view(
        {
            "runId": "geo-run-1",
            "batchName": "AMap footprint sample",
            "createdAt": "2026-05-20T12:00:00+08:00",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "community_id": "pudong-001",
                        "community_name": "汤臣一品",
                        "building_id": "pudong-001-b001",
                        "building_name": "1号楼",
                        "source_ref": "amap://footprint/1",
                        "resolution_notes": "已命中楼栋词典",
                        "coordinate_datum": "gcj02",
                    },
                    "geometry": {"type": "Polygon", "coordinates": [[]]},
                }
            ],
            "coverageTasks": [],
            "reviewHistory": [],
            "workOrderRows": [],
            "workOrderEvents": [],
        }
    )

    assert view["featurePreview"][0]["coordinateDatum"] == "gcj02"


def test_feature_preview_canonicalizes_legacy_coordinate_datum_alias(monkeypatch) -> None:
    from api import service

    monkeypatch.setattr(service, "flatten_communities", lambda **_: [])
    monkeypatch.setattr(service, "floor_watchlist", lambda **_: [])

    view = build_geo_asset_run_view(
        {
            "runId": "geo-run-2",
            "batchName": "Legacy footprint sample",
            "createdAt": "2026-05-20T12:00:00+08:00",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "community_id": "pudong-001",
                        "community_name": "汤臣一品",
                        "building_id": "pudong-001-b001",
                        "building_name": "1号楼",
                        "source_ref": "amap://footprint/2",
                        "resolution_notes": "已命中楼栋词典",
                        "coordinate_datum": "WGS-84",
                    },
                    "geometry": {"type": "Polygon", "coordinates": [[]]},
                }
            ],
            "coverageTasks": [],
            "reviewHistory": [],
            "workOrderRows": [],
            "workOrderEvents": [],
        }
    )

    assert view["featurePreview"][0]["coordinateDatum"] == "wgs84"
