from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..backstage.geo_qa import geo_asset_run_detail_full as _geo_run_detail
from ..backstage.runs import list_geo_asset_runs as _list_geo_runs
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


@router.get("/osm-footprints")
def map_osm_footprints(
    district: str | None = Query(default=None),
    viewport: str | None = Query(default=None, description="lng_min,lat_min,lng_max,lat_max bbox"),
    limit: int = Query(default=2000, ge=1, le=20000),
) -> dict[str, Any]:
    """Return polygon footprints from the most recent osm-* geo-asset run.

    Optional viewport (`lng_min,lat_min,lng_max,lat_max`) clips features whose
    polygon centroid falls outside the bbox. Default `limit` of 2000 keeps the
    response small enough to render at typical city-zoom levels (zoom ~15-16).
    """
    bbox = _parse_viewport(viewport)
    runs = _list_geo_runs()
    osm_run = next(
        (r for r in runs if str(r.get("providerId") or "") == "openstreetmap"),
        None,
    )
    if osm_run is None:
        return {"type": "FeatureCollection", "features": [], "runId": None, "totalFeatures": 0}
    detail = _geo_run_detail(osm_run["runId"])
    if not detail:
        return {"type": "FeatureCollection", "features": [], "runId": osm_run["runId"], "totalFeatures": 0}

    raw_features = detail.get("features") or []
    out: list[dict[str, Any]] = []
    for feat in raw_features:
        props = feat.get("properties") or {}
        if district and district not in (None, "", "all") and props.get("district_id") != district:
            continue
        geom = feat.get("geometry") or {}
        if geom.get("type") != "Polygon":
            continue
        coords = geom.get("coordinates") or [[]]
        ring = coords[0] if coords else []
        if len(ring) < 4:
            continue
        if bbox:
            cx = sum(p[0] for p in ring) / len(ring)
            cy = sum(p[1] for p in ring) / len(ring)
            if not (bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3]):
                continue
        out.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {
                "districtId": props.get("district_id"),
                "districtName": props.get("district_name"),
                "communityId": props.get("community_id"),
                "communityName": props.get("community_name"),
                "buildingName": props.get("building_name"),
                "matchDistanceM": props.get("match_distance_m"),
                "osmId": props.get("source_ref"),
            },
        })
        if len(out) >= limit:
            break
    return {
        "type": "FeatureCollection",
        "features": out,
        "runId": osm_run["runId"],
        "totalFeatures": len(raw_features),
        "returnedFeatures": len(out),
    }


def _parse_viewport(s: str | None) -> tuple[float, float, float, float] | None:
    if not s:
        return None
    parts = s.split(",")
    if len(parts) != 4:
        return None
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        return None
