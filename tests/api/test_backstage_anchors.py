from __future__ import annotations

from pathlib import Path

from api.backstage.anchors import (
    default_anchor_review_history_path,
    default_reference_anchor_report_path,
    latest_anchor_review_at,
    reference_anchor_present,
    target_reference_run_id,
)


def test_default_anchor_review_history_path_is_manifest_sibling() -> None:
    manifest = Path("/tmp/reference-runs/run-x/manifest.json")
    assert default_anchor_review_history_path(manifest) == manifest.parent / "anchor_review_history.json"


def test_default_reference_anchor_report_path_is_manifest_sibling() -> None:
    manifest = Path("/tmp/reference-runs/run-x/manifest.json")
    assert default_reference_anchor_report_path(manifest) == manifest.parent / "anchor_report.json"


def test_reference_anchor_present_true_when_both_coords_set() -> None:
    assert reference_anchor_present({"center_lng": 121.5, "center_lat": 31.2}) is True


def test_reference_anchor_present_false_for_missing_or_blank_coords() -> None:
    assert reference_anchor_present({"center_lng": 121.5}) is False
    assert reference_anchor_present({"center_lng": 121.5, "center_lat": None}) is False
    assert reference_anchor_present({"center_lng": "", "center_lat": ""}) is False
    assert reference_anchor_present({}) is False


def test_latest_anchor_review_at_picks_latest_timestamp() -> None:
    history = [
        {"reviewedAt": "2026-04-10T08:00:00+08:00"},
        {"reviewedAt": "2026-04-25T14:30:00+08:00"},
        {"reviewedAt": "2026-04-12T22:15:00+08:00"},
        {"unrelated": "ignored"},
    ]
    latest = latest_anchor_review_at(history)
    assert latest is not None
    assert "2026-04-25" in latest


def test_target_reference_run_id_returns_explicit_when_provided() -> None:
    # Explicit run id short-circuits without touching the filesystem.
    assert target_reference_run_id("ref-2026-04-01") == "ref-2026-04-01"
