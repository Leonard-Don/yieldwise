"""CSV parser tests."""
from __future__ import annotations

import io

import pytest

from api.customer_data.parser import ParseResult, parse_csv


_GOOD_PORTFOLIO_CSV = (
    "﻿project_name,address,building_no,unit_type,monthly_rent_cny,"
    "occupancy_rate_pct,move_in_date,longitude,latitude\n"
    "Alpha,addr1,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    "Beta,addr2,2,3-1,9000,88.5,2025-01-15,121.40,31.18\n"
)


def test_parse_good_csv_returns_rows_no_errors():
    res = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    assert isinstance(res, ParseResult)
    assert len(res.rows) == 2
    assert res.errors == []
    assert res.rows[0].project_name == "Alpha"


def test_parse_strips_utf8_bom():
    res = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    # BOM must not contaminate the first column header
    assert res.rows[0].project_name == "Alpha"


def test_parse_captures_invalid_row_in_errors():
    bad_csv = (
        "project_name,address,building_no,unit_type,monthly_rent_cny,"
        "occupancy_rate_pct,move_in_date,longitude,latitude\n"
        "Good,a,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
        "Bad,a,1,2-1,not-a-number,95,2024-09-01,121.59,31.21\n"
        ",a,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    )
    res = parse_csv(bad_csv.encode("utf-8"), type_="portfolio")
    assert len(res.rows) == 1
    assert len(res.errors) == 2
    # row 1 = header, row 2 = "Good", row 3 = "Bad" (first error), row 4 = empty project_name
    assert res.errors[0]["row_index"] == 3
    assert "monthly_rent_cny" in str(res.errors[0]["error_messages"])
    assert res.errors[1]["row_index"] == 4


def test_parse_rejects_unknown_type():
    with pytest.raises(ValueError, match="type"):
        parse_csv(b"x,y\n", type_="not-a-type")


def test_parse_pipeline_validates_stage():
    pipeline_csv = (
        "project_name,address,stage,est_price_cny,notes,longitude,latitude,updated_at\n"
        "P1,a,negotiating,1000000,note,121.5,31.0,2026-04-15\n"
        "P2,a,bogus,500000,note,121.5,31.0,2026-04-15\n"
    )
    res = parse_csv(pipeline_csv.encode("utf-8"), type_="pipeline")
    assert len(res.rows) == 1
    assert len(res.errors) == 1


def test_parse_empty_file_returns_zero_rows_no_errors():
    res = parse_csv(b"", type_="portfolio")
    assert res.rows == []
    assert res.errors == []
