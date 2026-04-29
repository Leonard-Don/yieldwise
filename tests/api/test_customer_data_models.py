"""Customer data row model tests."""
from __future__ import annotations

import pytest

from api.customer_data.models import (
    CompSetRow,
    PipelineRow,
    PortfolioRow,
    ROW_MODELS,
)


def test_portfolio_row_validates_lng_lat_required():
    with pytest.raises(ValueError):
        PortfolioRow(project_name="x", longitude=None, latitude=31.0)


def test_portfolio_row_accepts_iso_date_string():
    r = PortfolioRow(
        project_name="A",
        address="addr",
        building_no="1",
        unit_type="2室1厅",
        monthly_rent_cny=7800,
        occupancy_rate_pct=95,
        move_in_date="2024-09-01",
        longitude=121.59,
        latitude=31.21,
    )
    assert r.move_in_date.isoformat() == "2024-09-01"
    assert float(r.monthly_rent_cny) == 7800.0


def test_pipeline_row_rejects_invalid_stage():
    with pytest.raises(ValueError, match="stage"):
        PipelineRow(
            project_name="P", stage="not-a-stage",
            longitude=121.5, latitude=31.0,
        )


def test_pipeline_row_accepts_all_stages():
    for stage in ("lead", "qualified", "negotiating", "won", "lost"):
        r = PipelineRow(
            project_name="P", stage=stage,
            longitude=121.5, latitude=31.0,
        )
        assert r.stage == stage


def test_comp_set_row_iso_date_and_numeric_fields():
    r = CompSetRow(
        source="戴德梁行 2026Q1",
        report_date="2026-03-31",
        address="addr",
        transaction_price_cny="250000000.00",
        rent_per_sqm_cny="180.5",
        area_sqm=1500,
        longitude=121.46,
        latitude=31.23,
    )
    assert r.report_date.isoformat() == "2026-03-31"
    assert float(r.transaction_price_cny) == 250_000_000.0


def test_row_models_registry():
    assert ROW_MODELS["portfolio"] is PortfolioRow
    assert ROW_MODELS["pipeline"] is PipelineRow
    assert ROW_MODELS["comp_set"] is CompSetRow
