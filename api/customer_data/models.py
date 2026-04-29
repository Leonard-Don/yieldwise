"""Pydantic row models for customer_data uploads."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Type

from pydantic import BaseModel, ConfigDict, Field

Stage = Literal["lead", "qualified", "negotiating", "won", "lost"]


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


class PipelineRow(_Base):
    project_name: str
    address: str | None = None
    stage: Stage
    est_price_cny: Decimal | None = None
    notes: str | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)
    updated_at: date | None = None


class CompSetRow(_Base):
    source: str
    report_date: date | None = None
    address: str | None = None
    transaction_price_cny: Decimal | None = None
    rent_per_sqm_cny: Decimal | None = None
    area_sqm: Decimal | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)


ROW_MODELS: dict[str, Type[_Base]] = {
    "portfolio": PortfolioRow,
    "pipeline": PipelineRow,
    "comp_set": CompSetRow,
}
