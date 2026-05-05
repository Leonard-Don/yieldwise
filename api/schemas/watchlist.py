from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


TargetType = Literal["building", "community", "district"]
CandidateStatus = Literal["watching", "researching", "shortlisted", "rejected"]
CandidateAction = Literal["complete_review", "defer_review", "shortlist", "reject"]


class WatchlistEntry(BaseModel):
    """A single watchlist row persisted under data/personal/watchlist.json.

    The required fields remain intentionally small so old local files keep
    loading, while the optional candidate fields let the frontstage become a
    personal research queue instead of a plain star list.
    """

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: TargetType
    added_at: str | None = None
    updated_at: str | None = None
    status: CandidateStatus = "watching"
    priority: int = Field(default=3, ge=1, le=5)
    thesis: str | None = None
    target_price_wan: float | None = Field(default=None, ge=0)
    target_monthly_rent: float | None = Field(default=None, ge=0)
    target_yield_pct: float | None = Field(default=None, ge=0)
    review_due_at: str | None = None
    last_reviewed_at: str | None = None
    notes: str | None = None
    last_seen_snapshot: dict[str, Any] | None = None


class WatchlistAddPayload(BaseModel):
    """POST body for /api/v2/watchlist."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: TargetType
    status: CandidateStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    thesis: str | None = None
    target_price_wan: float | None = Field(default=None, ge=0)
    target_monthly_rent: float | None = Field(default=None, ge=0)
    target_yield_pct: float | None = Field(default=None, ge=0)
    review_due_at: str | None = None
    notes: str | None = None


class WatchlistPatchPayload(BaseModel):
    """PATCH body for /api/v2/watchlist/{target_id}."""

    model_config = ConfigDict(extra="forbid")

    status: CandidateStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    thesis: str | None = None
    target_price_wan: float | None = Field(default=None, ge=0)
    target_monthly_rent: float | None = Field(default=None, ge=0)
    target_yield_pct: float | None = Field(default=None, ge=0)
    review_due_at: str | None = None
    last_reviewed_at: str | None = None
    notes: str | None = None
    last_seen_snapshot: dict[str, Any] | None = None


class WatchlistActionPayload(BaseModel):
    """POST body for /api/v2/watchlist/{target_id}/actions."""

    model_config = ConfigDict(extra="forbid")

    action: CandidateAction
    days: int | None = Field(default=None, ge=1, le=90)
    notes: str | None = None
