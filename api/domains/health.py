from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def v2_health() -> dict[str, str]:
    return {"status": "ok", "surface": "user-platform-v2"}
