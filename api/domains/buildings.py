from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..service import get_building as _get_building
from ..service import get_floor_detail as _get_floor_detail

router = APIRouter(tags=["buildings"])


@router.get("/buildings/{building_id}")
def get_building(building_id: str) -> dict[str, Any]:
    building = _get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.get("/buildings/{building_id}/floors/{floor_no}")
def get_building_floor(building_id: str, floor_no: int) -> dict[str, Any]:
    floor = _get_floor_detail(building_id, floor_no)
    if not floor:
        raise HTTPException(status_code=404, detail="Floor detail not found")
    return floor
