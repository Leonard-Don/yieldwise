from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..service import (
    list_districts as _list_districts,
    map_buildings_payload as _map_buildings_payload,
    map_communities_payload as _map_communities_payload,
    summarize as _summarize,
)

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/districts")
def map_districts(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    return {
        "districts": _list_districts(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
        "summary": _summarize(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
    }


@router.get("/communities")
def map_communities(
    district: str | None = Query(default="all"),
    sample_status: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="all"),
    zoom: float | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict[str, Any]:
    return _map_communities_payload(
        district=district,
        sample_status=sample_status,
        focus_scope=focus_scope,
        zoom=zoom,
        viewport=viewport,
    )


@router.get("/buildings")
def map_buildings(
    district: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="priority"),
    geometry_quality: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict[str, Any]:
    return _map_buildings_payload(
        district=district,
        focus_scope=focus_scope,
        geometry_quality=geometry_quality,
        geo_run_id=geo_run_id,
        viewport=viewport,
    )
