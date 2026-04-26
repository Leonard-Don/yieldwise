from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ..schemas.districts import DistrictSummary
from ..service import list_districts

router = APIRouter(tags=["districts"])


@router.get("/districts/{district_id}")
def get_district(district_id: str) -> dict[str, Any]:
    rows = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    match = next((d for d in rows if d.get("id") == district_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="District not found")
    communities = list(match.get("communities") or [])
    communities.sort(key=lambda c: -(_safe_float(c.get("yield")) or 0.0))
    summary = DistrictSummary(
        id=match.get("id"),
        name=match.get("name") or "",
        yield_pct=_safe_float(match.get("yield")),
        score=_safe_int(match.get("score")),
        sample=_safe_int(match.get("sample") or match.get("saleSample")),
        community_count=len(communities),
        communities=communities,
    )
    return summary.model_dump(by_alias=True)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def _safe_int(value: Any) -> int | None:
    f = _safe_float(value)
    return int(f) if f is not None else None
