"""Regression tests for the public-browser-capture rent-price parser.

The 2026-04-29 bug audit found 24% of staged rent rows had implausible
1–19 元/月 values. Root cause: the old regex made BOTH the 月租/租金
prefix and the 元 suffix optional, so plain `\\d+` was a valid match.
Free text like "中层/16层 ... 月租12200元" then let "16" outrank the
real "月租12200元" because it appeared first.
"""
from __future__ import annotations

from jobs.import_public_browser_capture import build_structured_row, parse_monthly_rent


def _rent(text: str) -> float | None:
    return parse_monthly_rent([text], None)


# ── Regression: the exact bug pattern ──
def test_smoke_text_with_16ceng_does_not_extract_16() -> None:
    text = "上海 松江区 松江大学城嘉和休闲广场 A座 中层/16层 89平米 2室2厅 南向 精装 月租12200元"
    assert _rent(text) == 12200.0


def test_explicit_floor_does_not_leak_into_rent() -> None:
    text = "上海 松江区 松江大学城嘉和休闲广场 A座 6层/16层 89平米 月租12200元"
    assert _rent(text) == 12200.0


def test_no_rent_signal_returns_none() -> None:
    # 16层 alone (no 月租 prefix, no 元 suffix) must not be mistaken for rent
    assert _rent("80平米 16层") is None
    assert _rent("16层") is None


# ── Positive cases (must still parse) ──
def test_yuelu_prefix_with_yuan_suffix() -> None:
    assert _rent("月租 8400 元") == 8400.0


def test_zujin_prefix_no_suffix() -> None:
    assert _rent("租金18500") == 18500.0


def test_yuan_per_month_suffix() -> None:
    assert _rent("12000元/月") == 12000.0


def test_wan_yuan_unit() -> None:
    assert _rent("3.5万元/月") == 35000.0


def test_yuelu_prefix_wan_unit() -> None:
    assert _rent("月租 1.2 万") == 12000.0


def test_explicit_value_wins_over_text() -> None:
    # explicit_value short-circuits the regex
    assert parse_monthly_rent(["月租 99 元"], "8500") == 8500.0


def test_implausible_explicit_value_falls_back_to_text() -> None:
    text = "万盛金邸 3号楼 9层/16层 89平米 2室2厅 南向 精装 月租12200元"
    assert parse_monthly_rent([text], "16") == 12200.0


def test_implausible_explicit_value_without_rent_signal_is_missing() -> None:
    assert parse_monthly_rent(["万盛金邸 3号楼 9层/16层 89平米"], "16") is None


def test_structured_row_does_not_let_total_floors_override_rent() -> None:
    structured, parsed = build_structured_row(
        {
            "source_listing_id": "rent-regression-001",
            "business_type": "rent",
            "url": "https://example.com/rent-regression-001",
            "community_name": "万盛金邸",
            "address_text": "万盛金邸 3号楼",
            "raw_text": "万盛金邸 3号楼 9层/16层 89平米 2室2厅 南向 精装 月租12200元",
            "published_at": "2026-04-14T10:42:00+08:00",
            "total_floors": "16",
            "monthly_rent": "16",
        }
    )

    assert structured["monthly_rent"] == 12200.0
    assert parsed["attention"] == []
