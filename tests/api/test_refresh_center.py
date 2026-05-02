from __future__ import annotations

from api.backstage.refresh_center import summarize_import_anomaly_filters


def test_refresh_center_endpoint_exposes_closed_loop_sections(client) -> None:
    response = client.get("/api/ops/refresh-center")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ready", "needs_review", "blocked"}
    assert payload["selectedRuns"].keys() >= {"reference", "import", "geo", "metrics"}
    assert {item["step"] for item in payload["refreshPlan"]} == {"reference", "import", "geo", "metrics"}
    assert {item["id"] for item in payload["dryRunChecks"]} >= {
        "reference_run",
        "listing_run",
        "geo_run",
        "postgres",
        "anomaly_filters",
    }
    assert "geometryQa" in payload
    assert "anomalyFilters" in payload
    assert isinstance(payload["anomalyFilters"]["filters"], list)


def test_refresh_center_report_can_run_without_persisting(client) -> None:
    response = client.post("/api/ops/refresh-center/report", json={"persist": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["persisted"] is False
    assert payload["reportPath"] is None
    assert payload["reports"]["nextReportDir"] == "tmp/refresh-reports"


def test_import_anomaly_filters_count_review_confidence_and_yield_outliers() -> None:
    payload = summarize_import_anomaly_filters(
        {
            "runId": "import-1",
            "batchName": "测试批次",
            "createdAt": "2026-05-02T12:00:00+08:00",
            "providerId": "fixture",
            "storageMode": "file",
            "reviewQueue": [
                {"queueId": "q1", "normalizedPath": "浦东 · A楼 · 8层", "status": "needs_review", "confidence": 0.4}
            ],
            "attention": {
                "low_confidence_pairs": [
                    {"pair_id": "p1", "match_confidence": 0.61, "normalized_address": "浦东 · A楼 · 8层"}
                ]
            },
            "floorEvidence": [
                {
                    "community_id": "c1",
                    "building_id": "b1",
                    "floor_no": 8,
                    "yield_pct": 9.4,
                    "pair_count": 1,
                    "best_pair_confidence": 0.62,
                },
                {
                    "community_id": "c1",
                    "building_id": "b2",
                    "floor_no": 3,
                    "yield_pct": 3.2,
                    "pair_count": 3,
                    "best_pair_confidence": 0.91,
                },
            ],
        }
    )

    filters = {item["id"]: item for item in payload["filters"]}
    assert payload["status"] == "warn"
    assert filters["review_queue"]["count"] == 1
    assert filters["low_confidence_pairs"]["count"] == 1
    assert filters["single_pair_floors"]["count"] == 1
    assert filters["low_confidence_floors"]["count"] == 1
    assert filters["yield_outliers"]["count"] == 1
