from __future__ import annotations

from api import service


def test_geo_task_exports_are_empty_without_geo_run_id() -> None:
    payload = service.build_geo_task_watchlist_geojson()
    assert payload == {
        "type": "FeatureCollection",
        "name": "ShanghaiGeoTaskWatchlist",
        "features": [],
    }

    csv_payload = service.build_geo_task_watchlist_csv()
    assert csv_payload.splitlines()[0].startswith("geo_asset_run_id,geo_asset_batch_name")
    assert len(csv_payload.splitlines()) == 1


def test_floor_watchlist_uses_light_floor_evidence_path(monkeypatch) -> None:
    monkeypatch.setattr(
        service,
        "_list_import_runs_cached",
        lambda: (
            {"runId": "run-1", "createdAt": "2026-01-01T00:00:00"},
            {"runId": "run-2", "createdAt": "2026-01-02T00:00:00"},
        ),
    )
    monkeypatch.setattr(
        service,
        "_floor_watchlist_building_context_by_id",
        lambda: {
            "building-1": (
                {
                    "id": "building-1",
                    "name": "1号楼",
                    "totalFloors": 18,
                    "low": 3.5,
                    "mid": 4.0,
                    "high": 4.2,
                    "score": 90,
                    "yieldAvg": 4.0,
                },
                {
                    "id": "community-1",
                    "name": "测试小区",
                    "districtId": "pudong",
                    "districtName": "浦东新区",
                    "yield": 3.0,
                    "avgPriceWan": 500.0,
                    "monthlyRent": 12000,
                    "sample": 2,
                },
            )
        },
    )

    def light_detail(run_id: str) -> dict:
        yield_pct = 4.0 if run_id == "run-1" else 4.3
        return {
            "runId": run_id,
            "providerId": "fixture",
            "batchName": run_id,
            "createdAt": "2026-01-01T00:00:00" if run_id == "run-1" else "2026-01-02T00:00:00",
            "floorEvidence": [
                {
                    "community_id": "community-1",
                    "building_id": "building-1",
                    "floor_no": 8,
                    "yield_pct": yield_pct,
                    "pair_count": 2,
                    "sale_median_wan": 500.0,
                    "rent_median_monthly": 12000,
                }
            ],
        }

    monkeypatch.setattr(service, "_import_run_floor_evidence_cached", light_detail)
    monkeypatch.setattr(
        service,
        "_import_run_detail_full_cached",
        lambda run_id: (_ for _ in ()).throw(AssertionError("heavy import detail should not be used")),
    )

    items = service.floor_watchlist(district="pudong", limit=5)

    assert len(items) == 1
    assert items[0]["buildingId"] == "building-1"
    assert items[0]["floorNo"] == 8
    assert items[0]["latestYieldPct"] == 4.3
    assert items[0]["yieldDeltaSinceFirst"] == 0.3
    assert items[0]["observedRuns"] == 2
