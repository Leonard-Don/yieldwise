"""Unit tests for the sampling-helper backlog parser."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from guided_sampling_helper import _infer_scope_kind, build_anjuke_url, parse_backlog


def test_scope_kind_inference() -> None:
    assert _infer_scope_kind("B座 9层") == "floor_pair"
    assert _infer_scope_kind("3幢") == "building_depth"
    assert _infer_scope_kind("5号楼") == "building_depth"
    assert _infer_scope_kind("小区补面") == "community_profile"
    assert _infer_scope_kind("something else") == "other"


def test_anjuke_url_encodes_chinese() -> None:
    url = build_anjuke_url("松江大学城嘉和休闲广场", "sale")
    assert url.startswith("https://shanghai.anjuke.com/sale/?kw=")
    # The url-encoded community name is included
    assert "%E6%9D%BE%E6%B1%9F" in url  # 松江
    assert build_anjuke_url("X", "rent").startswith("https://shanghai.anjuke.com/zu/?kw=")


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
