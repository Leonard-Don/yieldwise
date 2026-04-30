"""Pydantic row models for customer_data uploads."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Type

from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", str_strip_whitespace=True)


class PortfolioRow(_Base):
    project_name: str
    address: str | None = None
    building_no: str | None = None
    unit_type: str | None = None
    monthly_rent_cny: Decimal | None = None
    occupancy_rate_pct: Decimal | None = None
    move_in_date: date | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)


ROW_MODELS: dict[str, Type[_Base]] = {
    "portfolio": PortfolioRow,
}
