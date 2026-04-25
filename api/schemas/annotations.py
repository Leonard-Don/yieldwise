from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


AnnotationTargetType = Literal["building", "community", "floor", "listing"]


class Annotation(BaseModel):
    """Persisted note keyed by `note_id` (server-generated UUID).

    Stored under data/personal/annotations.json as `{"items": [Annotation, ...]}`.
    """

    model_config = ConfigDict(extra="ignore")

    note_id: str
    target_id: str
    target_type: AnnotationTargetType
    body: str
    created_at: str | None = None
    updated_at: str | None = None


class AnnotationCreatePayload(BaseModel):
    """POST /api/v2/annotations body."""

    model_config = ConfigDict(extra="forbid")

    target_id: str
    target_type: AnnotationTargetType
    body: str


class AnnotationUpdatePayload(BaseModel):
    """PATCH /api/v2/annotations/{note_id} body — only `body` is editable."""

    model_config = ConfigDict(extra="forbid")

    body: str
