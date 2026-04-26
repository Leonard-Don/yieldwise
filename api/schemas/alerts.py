from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


AlertTargetType = Literal["building", "community", "district"]
AlertKind = Literal[
    "yield_up",
    "yield_down",
    "price_drop",
    "score_jump",
    "district_delta_up",
    "district_delta_down",
]


class AlertsState(BaseModel):
    """Persisted at data/personal/alerts_state.json."""

    model_config = ConfigDict(extra="ignore")

    baselines: dict[str, dict[str, Any]] = Field(default_factory=dict)
    last_open_at: str | None = None


class AlertRules(BaseModel):
    """Persisted at data/personal/alert_rules.json. Defaults match spec section 6."""

    model_config = ConfigDict(extra="ignore")

    yield_delta_abs: float = Field(default=0.5, ge=0)
    price_drop_pct: float = Field(default=3.0, ge=0)
    score_delta_abs: int = Field(default=5, ge=0)
    listing_new: bool = True
    district_delta_abs: float = Field(default=1.0, ge=0)


class AlertRulesPatch(BaseModel):
    """PATCH /api/v2/alerts/rules body — partial update."""

    model_config = ConfigDict(extra="forbid")

    yield_delta_abs: float | None = Field(default=None, ge=0)
    price_drop_pct: float | None = Field(default=None, ge=0)
    score_delta_abs: int | None = Field(default=None, ge=0)
    listing_new: bool | None = None
    district_delta_abs: float | None = Field(default=None, ge=0)


class Alert(BaseModel):
    """Single emitted change row."""

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_name: str | None = None
    target_type: AlertTargetType
    kind: AlertKind
    from_value: float | None = None
    to_value: float | None = None
    delta: float | None = None
