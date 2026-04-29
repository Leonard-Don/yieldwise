from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Role = Literal["admin", "analyst", "viewer"]


class CurrentUser(BaseModel):
    """Public-safe user shape — never includes password_hash."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    username: str
    role: Role
    disabled: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    user: CurrentUser
    redirect: str = "/"


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8)
    role: Role


class AdminUserPatch(BaseModel):
    role: Role | None = None
    disabled: bool | None = None
    password: str | None = Field(default=None, min_length=8)
