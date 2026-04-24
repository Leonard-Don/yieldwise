from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..service import opportunities as _opportunities

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
def list_opportunities(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
) -> dict[str, Any]:
    return {
        "items": _opportunities(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
            min_score=min_score,
        )
    }
