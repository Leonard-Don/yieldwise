from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

import pytest

from api.backstage import refresh_center
from api.backstage.refresh_center import summarize_import_anomaly_filters


@pytest.fixture()
def isolated_refresh_center_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    job_dir = tmp_path / "refresh-jobs"
    monkeypatch.setattr(refresh_center, "JOB_DIR", job_dir)
    monkeypatch.setattr(refresh_center, "JOB_HISTORY_PATH", job_dir / "jobs.json")
    monkeypatch.setattr(refresh_center, "EXECUTION_LOCK_PATH", job_dir / "execution.lock.json")
    monkeypatch.setattr(refresh_center, "ANOMALY_REVIEW_PATH", job_dir / "anomaly-review.json")
    monkeypatch.setattr(refresh_center, "REPORT_DIR", tmp_path / "refresh-reports")
    return job_dir


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
        "data_quality_gate",
    }
    assert "geometryQa" in payload
    assert "anomalyFilters" in payload
    assert "dataQualityGate" in payload
    assert payload["dataQualityGate"]["status"] in {"ok", "warn", "blocker"}
    assert isinstance(payload["anomalyFilters"]["filters"], list)


def test_refresh_center_report_can_run_without_persisting(client) -> None:
    response = client.post("/api/ops/refresh-center/report", json={"persist": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["persisted"] is False
    assert payload["reportPath"] is None
    assert payload["reports"]["nextReportDir"] == "tmp/refresh-reports"


def test_refresh_center_execute_records_job_without_metrics(client, isolated_refresh_center_paths: Path) -> None:
    response = client.post("/api/ops/refresh-center/execute", json={"refreshMetrics": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["jobId"].startswith("refresh-center-")
    assert payload["status"] in {"completed", "blocked"}
    assert payload["completedAt"]

    step_ids = {item["step"] for item in payload["steps"]}
    if payload["status"] == "completed":
        assert {"reference", "metrics", "report"} <= step_ids
        assert next(item for item in payload["steps"] if item["step"] == "metrics")["status"] == "skipped"
    else:
        assert "dry_run" in step_ids

    jobs = client.get("/api/ops/refresh-center/jobs").json()["items"]
    assert any(item["jobId"] == payload["jobId"] for item in jobs)


def test_refresh_center_anomaly_queue_can_record_review_state(client, isolated_refresh_center_paths: Path) -> None:
    queue_response = client.get("/api/ops/refresh-center/anomalies")

    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    assert queue_payload["summary"].keys() >= {"totalCount", "pendingCount", "needsSampleCount"}
    assert isinstance(queue_payload["items"], list)

    anomaly_id = queue_payload["items"][0]["anomalyId"] if queue_payload["items"] else "manual-test-anomaly"
    update_response = client.post(
        f"/api/ops/refresh-center/anomalies/{quote(anomaly_id, safe='')}",
        json={"status": "waived", "resolutionNotes": "测试豁免", "reviewer": "pytest"},
    )

    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["status"] == "updated"
    assert payload["item"]["anomalyId"] == anomaly_id
    assert payload["item"]["status"] == "waived"


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
