from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class UserPrefs(BaseModel):
    """Persistent personalization for the Home mode (predominantly).

    All fields optional — a fresh user has none of these set yet. The
    onboarding modal collects budget / districts / area.
    """

    model_config = ConfigDict(extra="ignore")

    budget_min_wan: float | None = Field(default=None, ge=0)
    budget_max_wan: float | None = Field(default=None, ge=0)
    districts: list[str] = Field(default_factory=list)
    area_min_sqm: float | None = Field(default=None, ge=0)
    area_max_sqm: float | None = Field(default=None, ge=0)
    updated_at: str | None = None


class UserPrefsPatch(BaseModel):
    """PATCH body — same fields as UserPrefs but unknown keys 422.

    `model_dump(exclude_unset=True)` is the merge contract: only fields
    explicitly provided by the client overwrite existing values.
    """

    model_config = ConfigDict(extra="forbid")

    budget_min_wan: float | None = Field(default=None, ge=0)
    budget_max_wan: float | None = Field(default=None, ge=0)
    districts: list[str] | None = None
    area_min_sqm: float | None = Field(default=None, ge=0)
    area_max_sqm: float | None = Field(default=None, ge=0)
