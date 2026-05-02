from __future__ import annotations

from jobs.clean_dirty_listings import clean_rent, clean_sale


def test_clean_rent_nulls_implausible_monthly_rent() -> None:
    rows = [
        {
            "resolved_district_name": "浦东新区",
            "resolved_community_name": "联洋年华",
            "monthly_rent": 16,
            "resolution_notes": "",
        },
        {"monthly_rent": 12200},
    ]
    affected: dict[tuple[str, str], int] = {}

    cleaned = clean_rent(rows, threshold=1000, dry_run=False, affected_communities=affected)

    assert cleaned == 1
    assert rows[0]["monthly_rent"] is None
    assert rows[1]["monthly_rent"] == 12200
    assert rows[0]["resolution_notes"].startswith("clean_dirty: rent original=16.0")
    assert affected == {("浦东新区", "联洋年华"): 1}


def test_clean_rent_dry_run_keeps_rows_unchanged() -> None:
    rows = [{"monthly_rent": 19, "resolution_notes": ""}]
    affected: dict[tuple[str, str], int] = {}

    cleaned = clean_rent(rows, threshold=1000, dry_run=True, affected_communities=affected)

    assert cleaned == 1
    assert rows[0]["monthly_rent"] == 19
    assert rows[0]["resolution_notes"] == ""


def test_clean_sale_nulls_known_ui_default_tuple() -> None:
    rows = [
        {
            "raw_community_name": "万盛金邸",
            "price_total_wan": 323.0,
            "unit_price_yuan": 36292.13,
            "resolution_notes": "needs review",
        },
        {"price_total_wan": 960.0, "unit_price_yuan": 99482.0},
    ]
    affected: dict[tuple[str, str], int] = {}

    cleaned = clean_sale(
        rows,
        bug_wan=323.0,
        bug_unit=36292.13,
        dry_run=False,
        affected_communities=affected,
    )

    assert cleaned == 1
    assert rows[0]["price_total_wan"] is None
    assert rows[0]["unit_price_yuan"] is None
    assert "clean_dirty: sale original_wan=323.0" in rows[0]["resolution_notes"]
    assert rows[1]["price_total_wan"] == 960.0
    assert affected == {("?", "万盛金邸"): 1}
