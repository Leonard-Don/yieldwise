from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.annotations import (
    Annotation,
    AnnotationCreatePayload,
    AnnotationUpdatePayload,
)


def test_annotation_round_trips_full_payload() -> None:
    payload = {
        "note_id": "abc-123",
        "target_id": "daning-jinmaofu-b1",
        "target_type": "building",
        "body": "Saw 2 fresh listings this week.",
        "created_at": "2026-04-24T10:00:00",
        "updated_at": "2026-04-24T10:00:00",
    }
    note = Annotation.model_validate(payload)
    assert note.note_id == "abc-123"
    assert note.target_type == "building"
    assert note.body.startswith("Saw")


def test_annotation_defaults_timestamps_to_none() -> None:
    note = Annotation.model_validate(
        {
            "note_id": "abc-123",
            "target_id": "x",
            "target_type": "community",
            "body": "test",
        }
    )
    assert note.created_at is None
    assert note.updated_at is None


def test_annotation_rejects_unknown_target_type() -> None:
    with pytest.raises(ValidationError):
        Annotation.model_validate(
            {"note_id": "x", "target_id": "y", "target_type": "district", "body": "z"}
        )


def test_create_payload_accepts_minimal_fields() -> None:
    body = AnnotationCreatePayload.model_validate(
        {"target_id": "x", "target_type": "building", "body": "hi"}
    )
    assert body.body == "hi"


def test_create_payload_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        AnnotationCreatePayload.model_validate(
            {"target_id": "x", "target_type": "building", "body": "hi", "evil": True}
        )


def test_update_payload_only_accepts_body() -> None:
    body = AnnotationUpdatePayload.model_validate({"body": "new content"})
    assert body.body == "new content"
    with pytest.raises(ValidationError):
        AnnotationUpdatePayload.model_validate(
            {"body": "new content", "target_id": "x"}
        )
