from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


SearchTargetType = Literal["building", "community", "district"]


class SearchHit(BaseModel):
    """A single search result row."""

    model_config = ConfigDict(extra="ignore")

    target_id: str
    target_type: SearchTargetType
    target_name: str
    district_name: str | None = None
