from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.schemas.user_prefs import UserPrefs, UserPrefsPatch


def test_user_prefs_empty_is_valid() -> None:
    prefs = UserPrefs()
    dump = prefs.model_dump()
    for key in (
        "budget_min_wan",
        "budget_max_wan",
        "districts",
        "area_min_sqm",
        "area_max_sqm",
        "updated_at",
    ):
        assert key in dump


def test_user_prefs_districts_default_is_empty_list() -> None:
    prefs = UserPrefs()
    assert prefs.districts == []


def test_user_prefs_round_trips_full_payload() -> None:
    payload = {
        "budget_min_wan": 500,
        "budget_max_wan": 1500,
        "districts": ["pudong", "jingan"],
        "area_min_sqm": 60,
        "area_max_sqm": 120,
        "updated_at": "2026-04-24T10:00:00",
    }
    prefs = UserPrefs.model_validate(payload)
    assert prefs.budget_max_wan == 1500
    assert prefs.districts == ["pudong", "jingan"]
    assert prefs.area_min_sqm == 60


def test_user_prefs_patch_accepts_partial_payload() -> None:
    patch = UserPrefsPatch.model_validate({"budget_max_wan": 1200})
    update = patch.model_dump(exclude_unset=True)
    assert update == {"budget_max_wan": 1200}


def test_user_prefs_patch_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        UserPrefsPatch.model_validate({"budget_max_wan": 1200, "evil": True})


def test_user_prefs_patch_empty_object_is_valid() -> None:
    patch = UserPrefsPatch.model_validate({})
    assert patch.model_dump(exclude_unset=True) == {}


def test_user_prefs_negative_budget_rejected() -> None:
    with pytest.raises(ValidationError):
        UserPrefs.model_validate({"budget_max_wan": -1})
