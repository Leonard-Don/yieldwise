from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.watchlist import WatchlistAddPayload, WatchlistEntry


def test_entry_round_trips_full_payload() -> None:
    payload = {
        "target_id": "daning-jinmaofu-b1",
        "target_type": "building",
        "added_at": "2026-04-24T10:00:00",
        "status": "shortlisted",
        "priority": 1,
        "thesis": "收益稳定",
        "review_due_at": "2026-05-10",
        "last_seen_snapshot": {"yieldAvg": 0.04, "score": 66},
    }
    entry = WatchlistEntry.model_validate(payload)
    assert entry.target_id == "daning-jinmaofu-b1"
    assert entry.target_type == "building"
    assert entry.status == "shortlisted"
    assert entry.priority == 1
    assert entry.thesis == "收益稳定"
    assert entry.last_seen_snapshot == {"yieldAvg": 0.04, "score": 66}


def test_entry_defaults_optional_fields_to_none() -> None:
    entry = WatchlistEntry.model_validate(
        {"target_id": "pudong-xyz", "target_type": "community"}
    )
    assert entry.added_at is None
    assert entry.last_seen_snapshot is None
    assert entry.status == "watching"
    assert entry.priority == 3


def test_entry_accepts_district_target_type() -> None:
    entry = WatchlistEntry.model_validate({"target_id": "pudong", "target_type": "district"})
    assert entry.target_type == "district"


def test_entry_rejects_invalid_target_type() -> None:
    with pytest.raises(ValidationError):
        WatchlistEntry.model_validate({"target_id": "x", "target_type": "listing"})


def test_add_payload_accepts_minimal() -> None:
    body = WatchlistAddPayload.model_validate(
        {"target_id": "daning-jinmaofu-b1", "target_type": "building"}
    )
    assert body.target_id == "daning-jinmaofu-b1"


def test_add_payload_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        WatchlistAddPayload.model_validate(
            {"target_id": "x", "target_type": "building", "evil": True}
        )


def test_add_payload_rejects_missing_required() -> None:
    with pytest.raises(ValidationError):
        WatchlistAddPayload.model_validate({"target_id": "x"})
