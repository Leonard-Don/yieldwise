from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..service import get_community as _get_community

router = APIRouter(tags=["communities"])


@router.get("/communities/{community_id}")
def get_community(community_id: str) -> dict[str, Any]:
    community = _get_community(community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community
