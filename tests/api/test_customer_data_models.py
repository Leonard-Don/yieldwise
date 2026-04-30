"""Customer data row model tests."""
from __future__ import annotations

import pytest

from api.customer_data.models import (
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


def test_row_models_registry():
    assert ROW_MODELS["portfolio"] is PortfolioRow
    assert "pipeline" not in ROW_MODELS
    assert "comp_set" not in ROW_MODELS
