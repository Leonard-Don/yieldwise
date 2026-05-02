from __future__ import annotations

import json
from pathlib import Path

from api.data_quality import (
    build_data_quality_gate,
    dirty_listing_summary_for_import_runs,
    quality_summary,
)


def test_quality_summary_marks_balanced_sample_as_usable() -> None:
    payload = quality_summary(
        {
            "saleSample": 4,
            "rentSample": 5,
            "yield": 4.2,
            "anchorQuality": 0.92,
            "dataFreshness": "2026-05-02T12:00:00+08:00",
        },
        target_type="community",
    )

    assert payload["status"] in {"usable", "strong"}
    assert payload["score"] >= 66
    assert payload["sampleLabel"] == "售 4 / 租 5"
    assert {item["id"] for item in payload["checks"]} >= {"sample_balance", "yield_signal"}


def test_quality_summary_blocks_missing_rent_side() -> None:
    payload = quality_summary({"saleSample": 4, "rentSample": 0, "yield": 4.2}, target_type="community")

    assert payload["status"] == "blocked"
    assert payload["checks"][0]["status"] == "blocker"


def test_dirty_listing_summary_counts_known_ui_corruption(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    (run_dir / "normalized_rent.json").write_text(
        json.dumps([{"monthly_rent": 16}, {"monthly_rent": 12200}], ensure_ascii=False),
        encoding="utf-8",
    )
    (run_dir / "normalized_sale.json").write_text(
        json.dumps(
            [
                {"price_total_wan": 323.0, "unit_price_yuan": 36292.13},
                {"price_total_wan": 960.0, "unit_price_yuan": 99482.0},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = dirty_listing_summary_for_import_runs(
        [{"runId": "run-1", "batchName": "Run 1", "outputDir": str(run_dir)}]
    )

    assert payload["totalIssueCount"] == 2
    assert payload["rentIssueCount"] == 1
    assert payload["saleIssueCount"] == 1
    assert payload["affectedRuns"][0]["runId"] == "run-1"


def test_data_quality_gate_blocks_dirty_rows_and_missing_sample(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    (run_dir / "normalized_rent.json").write_text(json.dumps([{"monthly_rent": 19}]), encoding="utf-8")
    (run_dir / "normalized_sale.json").write_text(json.dumps([]), encoding="utf-8")

    payload = build_data_quality_gate(
        communities=[
            {
                "id": "c1",
                "name": "测试小区",
                "districtName": "浦东新区",
                "saleSample": 2,
                "rentSample": 0,
                "yield": 4.1,
            }
        ],
        import_runs=[{"runId": "run-1", "outputDir": str(run_dir)}],
    )

    assert payload["status"] == "blocker"
    assert payload["statusCounts"]["blocked"] == 1
    assert payload["dirtyListings"]["totalIssueCount"] == 1
