from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


TargetType = Literal["building", "community"]


class WatchlistEntry(BaseModel):
    """A single watchlist row persisted under data/personal/watchlist.json.

    `last_seen_snapshot` is reserved for Phase 5 (alerts) — Phase 4a always
    writes None. Existing rows with stored snapshots are preserved on read
    via the existing pydantic round-trip.
    """

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: TargetType
    added_at: str | None = None
    last_seen_snapshot: dict[str, Any] | None = None


class WatchlistAddPayload(BaseModel):
    """POST body for /api/v2/watchlist."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: TargetType
