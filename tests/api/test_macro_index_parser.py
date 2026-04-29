"""Unit tests for the public-mirror housing-index HTML parser."""
from __future__ import annotations

from jobs.import_macro_housing_index import _parse_int, parse_table_rows, yoy_change


def test_parse_int_handles_thousands_and_currency() -> None:
    assert _parse_int("63,528 元/㎡") == 63528
    assert _parse_int("12000") == 12000
    assert _parse_int("-5%") == -5
    assert _parse_int("") is None
    assert _parse_int("无数据") is None


def test_parse_table_rows_extracts_monthly_data() -> None:
    html = """
    <html><body><table>
      <tr><th>summary</th><th>...</th></tr>
      <tr><td>1</td><td>2026-03</td><td>61000</td><td>63528</td><td></td></tr>
      <tr><td>2</td><td>2026-02</td><td>61100</td><td>63294</td><td></td></tr>
      <tr><td>not data row</td></tr>
      <tr><td>3</td><td>2025-12</td><td>60200</td><td>55820</td><td></td></tr>
    </table></body></html>
    """
    rows = parse_table_rows(html)
    months = [r["month"] for r in rows]
    assert months == ["2026-03", "2026-02", "2025-12"]
    assert rows[0]["secondhand_yuan_per_sqm"] == 61000
    assert rows[0]["new_yuan_per_sqm"] == 63528


def test_yoy_change_computes_year_over_year() -> None:
    rows = [
        {"month": "2026-03", "secondhand_yuan_per_sqm": 61000, "new_yuan_per_sqm": 63528},
        {"month": "2025-03", "secondhand_yuan_per_sqm": 65000, "new_yuan_per_sqm": 60000},
    ]
    yoy = yoy_change(rows)
    # secondhand: 61000 vs 65000 → -6.15%
    assert yoy["2026-03"]["secondhand_yoy_pct"] == round((61000 - 65000) / 65000 * 100, 2)
    assert yoy["2026-03"]["new_yoy_pct"] == round((63528 - 60000) / 60000 * 100, 2)


def test_yoy_handles_missing_prior_year() -> None:
    rows = [{"month": "2026-03", "secondhand_yuan_per_sqm": 61000, "new_yuan_per_sqm": 63528}]
    assert yoy_change(rows) == {}
