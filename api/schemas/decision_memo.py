from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DecisionTargetType = Literal["building", "community", "district"]


class DecisionMemoTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: DecisionTargetType


class DecisionMemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targets: list[DecisionMemoTarget] = Field(default_factory=list, max_length=5)
