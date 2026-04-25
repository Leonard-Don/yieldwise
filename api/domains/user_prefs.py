from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from .. import personal_storage
from ..schemas.user_prefs import UserPrefs, UserPrefsPatch

router = APIRouter(tags=["user-prefs"])

PREFS_FILE = "user_prefs.json"


@router.get("/user/prefs")
def get_prefs() -> dict[str, Any]:
    raw = personal_storage.read_json(PREFS_FILE)
    if raw is None:
        return UserPrefs().model_dump()
    try:
        return UserPrefs.model_validate(raw).model_dump()
    except Exception:
        # Stored payload drifted from current schema — treat as empty so
        # the user can start fresh through the onboarding modal.
        return UserPrefs().model_dump()


@router.patch("/user/prefs")
def patch_prefs(patch: UserPrefsPatch) -> dict[str, Any]:
    raw = personal_storage.read_json(PREFS_FILE) or {}
    try:
        current = UserPrefs.model_validate(raw).model_dump()
    except Exception:
        current = UserPrefs().model_dump()

    update = patch.model_dump(exclude_unset=True)
    merged = {**current, **update}
    merged["updated_at"] = datetime.now().isoformat(timespec="seconds")

    validated = UserPrefs.model_validate(merged).model_dump()
    personal_storage.write_json(PREFS_FILE, validated)
    return validated
