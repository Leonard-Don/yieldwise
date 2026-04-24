from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..service import get_building as _get_building

router = APIRouter(tags=["buildings"])


@router.get("/buildings/{building_id}")
def get_building(building_id: str) -> dict[str, Any]:
    building = _get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building
