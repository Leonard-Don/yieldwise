from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DecisionTargetType = Literal["building", "community", "district"]


class DecisionMemoTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: DecisionTargetType


class DecisionMemoCandidateContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: DecisionTargetType
    status: str | None = None
    priority: int | None = None
    thesis: str | None = None
    notes: str | None = None
    target_price_wan: float | None = None
    target_monthly_rent: float | None = None
    target_yield_pct: float | None = None
    review_due_at: str | None = None
    task_labels: list[str] = Field(default_factory=list, max_length=10)
    trigger_labels: list[str] = Field(default_factory=list, max_length=10)


class DecisionMemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targets: list[DecisionMemoTarget] = Field(default_factory=list, max_length=5)
    candidate_contexts: list[DecisionMemoCandidateContext] = Field(default_factory=list, max_length=5)
