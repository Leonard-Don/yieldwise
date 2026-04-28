from __future__ import annotations

from api.backstage.review import (
    browser_capture_review_queue_id,
    browser_capture_review_summary,
    browser_sampling_priority_label,
    browser_sampling_required_fields,
    browser_sampling_task_display_label,
    browser_sampling_task_type_label,
)


def test_task_type_label_known_types() -> None:
    assert browser_sampling_task_type_label("floor_pair_capture") == "楼层补样"
    assert browser_sampling_task_type_label("building_depth_capture") == "楼栋加深"
    assert browser_sampling_task_type_label("community_profile_capture") == "小区补面"


def test_task_type_label_unknown_passes_through() -> None:
    assert browser_sampling_task_type_label("custom_task") == "custom_task"


def test_priority_label_band_thresholds() -> None:
    assert browser_sampling_priority_label(95.0) == "极高优先"
    assert browser_sampling_priority_label(88.0) == "极高优先"
    assert browser_sampling_priority_label(80.0) == "高优先"
    assert browser_sampling_priority_label(70.0) == "中优先"
    assert browser_sampling_priority_label(40.0) == "常规优先"


def test_required_fields_returns_independent_list() -> None:
    floor_fields = browser_sampling_required_fields("floor_pair_capture")
    assert isinstance(floor_fields, list)
    floor_fields.append("mutated")
    # Mutating the returned list must not pollute the next call.
    assert "mutated" not in browser_sampling_required_fields("floor_pair_capture")


def test_review_queue_id_formats_lowercase_business_and_listing() -> None:
    assert browser_capture_review_queue_id("Sale", "  abc123 ") == "sale::abc123"
    assert browser_capture_review_queue_id(None, None) == "::"


def test_review_summary_aggregates_status_counts() -> None:
    queue = [
        {"status": "pending"},
        {"status": "pending"},
        {"status": "resolved"},
        {"status": "waived"},
        {"status": "superseded"},
        {"status": "superseded"},
        {},  # default-pending
    ]
    summary = browser_capture_review_summary(queue)
    assert summary == {
        "pendingCount": 3,
        "resolvedCount": 1,
        "waivedCount": 1,
        "supersededCount": 2,
    }


def test_task_display_label_falls_back_when_no_task() -> None:
    assert browser_sampling_task_display_label(None) == "当前任务"
    assert browser_sampling_task_display_label({}) == "待识别小区"
    assert (
        browser_sampling_task_display_label(
            {"communityName": "中海建国里", "buildingName": "12号楼", "floorNo": 7}
        )
        == "中海建国里 · 12号楼 · 7层"
    )
