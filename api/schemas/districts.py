from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DistrictSummary(BaseModel):
    """Single-district detail response.

    The JSON field is `yield` (matching the rest of the API surface) but the
    Python attribute is `yield_pct` to dodge the keyword. Use
    `model_dump(by_alias=True)` when serialising for HTTP.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    name: str
    yield_pct: float | None = Field(default=None, alias="yield", serialization_alias="yield")
    score: int | None = None
    sample: int | None = None
    community_count: int = 0
    communities: list[dict[str, Any]] = Field(default_factory=list)
