"""Unit tests for the sampling-helper backlog parser."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from guided_sampling_helper import (
    _infer_scope_kind,
    build_public_search_query,
    live_pack_items_to_rows,
    live_rows_to_backlog_sections,
    parse_backlog,
    replace_backlog_priority_sections,
)


def test_scope_kind_inference() -> None:
    assert _infer_scope_kind("B座 9层") == "floor_pair"
    assert _infer_scope_kind("3幢") == "building_depth"
    assert _infer_scope_kind("5号楼") == "building_depth"
    assert _infer_scope_kind("小区补面") == "community_profile"
    assert _infer_scope_kind("something else") == "other"


def test_public_search_query_includes_business_context() -> None:
    assert build_public_search_query("松江大学城嘉和休闲广场", "sale") == "上海 松江大学城嘉和休闲广场 二手房"
    assert build_public_search_query("X", "rent") == "上海 X 租房"


def test_parse_backlog_extracts_priority_items() -> None:
    text = """
# Public Sampling Backlog

## 当前第一优先级

- 松江大学城嘉和休闲广场 `B座 9层`
  - 目标：从当前 `3` 组 pair 补到 `4` 组，稳住新扩出来的高收益楼层。
- 中兴新村 `5号楼 7层`
  - 目标：从当前 `3` 组 pair 补到 `4` 组。

## 当前第二优先级

- 联洋年华 `小区补面`
  - 目标：从当前 `3` 套聚合样本补到 `6` 套。

## 已完成

- 不应该被解析进来 `B座`
  - 结果：已经做完
"""
    items = parse_backlog(text)
    communities = [(it["priority"], it["community"]) for it in items]
    assert (1, "松江大学城嘉和休闲广场") in communities
    assert (1, "中兴新村") in communities
    assert (2, "联洋年华") in communities
    # 已完成 section is not in PRIORITY_HEADERS so its items are skipped
    assert all(it["community"] != "不应该被解析进来" for it in items)


def test_parse_backlog_extracts_goal_counts_with_backticks() -> None:
    """Live backlog wraps digits in backticks: 从当前 `3` 组 ... 补到 `4` 组"""
    text = """
## 当前第一优先级
- 中兴新村 `5号楼 7层`
  - 目标：从当前 `3` 组 pair 补到 `4` 组。
"""
    items = parse_backlog(text)
    assert len(items) == 1
    assert items[0]["current_count"] == 3
    assert items[0]["target_count"] == 4


def test_parse_backlog_extracts_goal_counts_plain_digits() -> None:
    """Older format without backticks must still parse."""
    text = """
## 当前第一优先级
- 万盛金邸 `小区补面`
  - 目标：从当前 2 套补到 5 套。
"""
    items = parse_backlog(text)
    assert items[0]["current_count"] == 2
    assert items[0]["target_count"] == 5


def test_live_pack_items_to_rows_preserves_actionable_context() -> None:
    rows = live_pack_items_to_rows([
        {
            "taskId": "browser-floor::sample::9",
            "priorityScore": 92,
            "priorityLabel": "极高优先",
            "taskTypeLabel": "楼层补样",
            "targetGranularity": "floor",
            "districtName": "松江区",
            "communityName": "松江大学城嘉和休闲广场",
            "buildingName": "B座",
            "floorNo": 9,
            "currentPairCount": 3,
            "targetPairCount": 4,
            "missingPairCount": 1,
            "pendingAttentionCount": 2,
            "taskLifecycleLabel": "待复核",
            "captureGoal": "至少再补 1 组 sale/rent 配对。",
            "saleQuery": "上海 松江区 松江大学城嘉和休闲广场 B座 9层 二手房",
            "rentQuery": "上海 松江区 松江大学城嘉和休闲广场 B座 9层 租房",
            "recommendedAction": "先复核，再补采。",
            "requiredFields": ["页面 URL", "小区名"],
        }
    ])

    assert rows == [
        {
            "source_mode": "live_pack",
            "task_id": "browser-floor::sample::9",
            "priority_score": 92,
            "priority_label": "极高优先",
            "task_type_label": "楼层补样",
            "target_granularity": "floor",
            "district": "松江区",
            "community": "松江大学城嘉和休闲广场",
            "scope": "B座 9层",
            "building": "B座",
            "floor": 9,
            "current_count": 3,
            "target_count": 4,
            "delta_to_target": 1,
            "pending_attention_count": 2,
            "task_lifecycle_label": "待复核",
            "capture_goal": "至少再补 1 组 sale/rent 配对。",
            "sale_search_query": "上海 松江区 松江大学城嘉和休闲广场 B座 9层 二手房",
            "rent_search_query": "上海 松江区 松江大学城嘉和休闲广场 B座 9层 租房",
            "recommended_action": "先复核，再补采。",
            "required_fields": "页面 URL / 小区名",
        }
    ]


def test_live_rows_to_backlog_sections_groups_by_priority() -> None:
    sections = live_rows_to_backlog_sections(
        [
            {
                "priority_score": 95,
                "priority_label": "极高优先",
                "community": "松江大学城嘉和休闲广场",
                "scope": "B座 9层",
                "current_count": 3,
                "target_count": 4,
                "delta_to_target": 1,
                "pending_attention_count": 2,
                "capture_goal": "至少再补 1 组 sale/rent 配对。",
                "sale_search_query": "上海 松江大学城嘉和休闲广场 二手房",
                "rent_search_query": "上海 松江大学城嘉和休闲广场 租房",
            },
            {
                "priority_score": 70,
                "priority_label": "中优先",
                "community": "联洋年华",
                "scope": "小区补面",
                "current_count": 3,
                "target_count": 6,
                "delta_to_target": 3,
            },
        ],
        generated_at="2026-05-03 13:30:00",
    )

    assert "## 当前第一优先级" in sections["当前第一优先级"]
    assert "松江大学城嘉和休闲广场 `B座 9层`" in sections["当前第一优先级"]
    assert "待复核 `2`" in sections["当前第一优先级"]
    assert "联洋年华 `小区补面`" in sections["当前第二优先级"]


def test_replace_backlog_priority_sections_keeps_completed_history() -> None:
    text = """# Public Sampling Backlog

intro

## 当前第一优先级

- 旧任务 `A座`

## 当前第二优先级

- 旧任务二 `小区补面`

## 已完成

- 历史任务 `B座`
"""
    updated = replace_backlog_priority_sections(
        text,
        {
            "当前第一优先级": "## 当前第一优先级\n\n- 新任务 `1号楼`\n",
            "当前第二优先级": "## 当前第二优先级\n\n- 新任务二 `小区补面`\n",
        },
    )

    assert "旧任务" not in updated
    assert "新任务 `1号楼`" in updated
    assert "新任务二 `小区补面`" in updated
    assert "历史任务 `B座`" in updated
