from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..schemas.search import SearchHit
from ..service import list_districts
from . import search_scoring

router = APIRouter(tags=["search"])


def _flatten_index() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    districts = list_districts(district="all", min_yield=0, max_budget=10000, min_samples=0)
    for d in districts:
        out.append(
            {
                "name": d.get("name") or "",
                "target_id": d.get("id"),
                "target_type": "district",
                "district_name": d.get("name") or None,
            }
        )
        for c in d.get("communities") or []:
            out.append(
                {
                    "name": c.get("name") or "",
                    "target_id": c.get("id"),
                    "target_type": "community",
                    "district_name": d.get("name") or None,
                }
            )
            for b in c.get("buildings") or []:
                out.append(
                    {
                        "name": b.get("name") or "",
                        "target_id": b.get("id"),
                        "target_type": "building",
                        "district_name": d.get("name") or None,
                    }
                )
    return out


@router.get("/search")
def search(
    q: str = Query(default="", min_length=0, max_length=100),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    if not q.strip():
        return {"items": []}
    hits = search_scoring.rank_hits(_flatten_index(), q, limit)
    items = [
        SearchHit.model_validate(
            {
                "target_id": hit["target_id"],
                "target_type": hit["target_type"],
                "target_name": hit["name"],
                "district_name": hit.get("district_name"),
            }
        ).model_dump()
        for hit in hits
        if hit.get("target_id")
    ]
    return {"items": items}
