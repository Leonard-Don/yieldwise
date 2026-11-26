"""GeoJSON / KML / CSV export builders and SVG<->lon/lat geometry helpers.

Extracted from api/service.py. service.py re-exports every public name here,
so ``from api.service import build_geojson`` keeps working.
"""

from __future__ import annotations

import csv
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from .backstage.geo_qa import (
    db_geo_asset_rows,
    geo_asset_run_detail,
    geo_asset_run_detail_full,
    geo_asset_work_orders,
    geo_task_watchlist,
    geo_work_order_status_label,
)
from .backstage.runs import database_mode_active, list_geo_asset_runs

ROOT_DIR = Path(__file__).resolve().parent.parent


def service():
    # Community/building lookups stay in api.service; resolve lazily to avoid an
    # import cycle and so tests that monkeypatch api.service.* still take effect.
    from . import service as _service

    return _service


def normalize_svg_to_lon_lat(x: float, y: float) -> tuple[float, float]:
    lon = 121.05 + (x / 760.0) * 0.8
    lat = 31.0 + ((520.0 - y) / 520.0) * 0.55
    return round(lon, 6), round(lat, 6)


def building_svg_point(community: dict[str, Any], building: dict[str, Any]) -> tuple[float, float]:
    building_count = max(len(community.get("buildings", [])), 1)
    sequence_no = int(building.get("sequenceNo", 1))
    sequence_offset = sequence_no - (building_count + 1) / 2
    return community["x"] + sequence_offset * 18, community["y"] + (10 if sequence_no % 2 == 0 else -10)


def floor_svg_point(community: dict[str, Any], building: dict[str, Any], floor_no: int) -> tuple[float, float]:
    base_x, base_y = building_svg_point(community, building)
    safe_floor = max(int(floor_no or 1), 1)
    total_floors = max(int(building.get("totalFloors", safe_floor)), 1)
    floor_offset = min(safe_floor, total_floors) / total_floors
    return base_x + ((safe_floor % 4) - 1.5) * 2.2, base_y - floor_offset * 22


def footprint_dimensions(building: dict[str, Any], scale: float = 1.0) -> tuple[float, float]:
    total_floors = max(int(building.get("totalFloors", 12)), 1)
    half_width = (8 + min(total_floors, 30) * 0.22) * scale
    half_height = (6 + min(total_floors, 30) * 0.14) * scale
    return round(half_width, 2), round(half_height, 2)


def footprint_polygon(center_x: float, center_y: float, *, half_width: float, half_height: float) -> list[tuple[float, float]]:
    return [
        (round(center_x - half_width, 2), round(center_y + half_height * 0.45, 2)),
        (round(center_x + half_width * 0.35, 2), round(center_y + half_height, 2)),
        (round(center_x + half_width, 2), round(center_y - half_height * 0.35, 2)),
        (round(center_x - half_width * 0.25, 2), round(center_y - half_height, 2)),
    ]


def building_footprint_svg(community: dict[str, Any], building: dict[str, Any]) -> list[tuple[float, float]]:
    center_x, center_y = building_svg_point(community, building)
    half_width, half_height = footprint_dimensions(building, scale=1.0)
    return footprint_polygon(center_x, center_y, half_width=half_width, half_height=half_height)


def floor_footprint_svg(community: dict[str, Any], building: dict[str, Any], floor_no: int) -> list[tuple[float, float]]:
    center_x, center_y = floor_svg_point(community, building, floor_no)
    half_width, half_height = footprint_dimensions(building, scale=0.82)
    return footprint_polygon(center_x, center_y, half_width=half_width, half_height=half_height)


def svg_polygon_to_lon_lat(points: list[tuple[float, float]]) -> list[list[float]]:
    ring = [[*normalize_svg_to_lon_lat(x, y)] for x, y in points]
    if ring and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def normalize_lon_lat_to_svg(lon: float, lat: float) -> tuple[float, float]:
    x = ((lon - 121.05) / 0.8) * 760.0
    y = 520.0 - ((lat - 31.0) / 0.55) * 520.0
    return round(x, 2), round(y, 2)


def ring_without_close(ring: list[list[float]]) -> list[list[float]]:
    if len(ring) >= 2 and ring[0] == ring[-1]:
        return ring[:-1]
    return ring


def feature_ring(feature: dict[str, Any]) -> list[list[float]]:
    geometry = feature.get("geometry", {})
    if geometry.get("type") == "Polygon":
        ring = geometry.get("coordinates", [[]])[0]
        parsed = [[float(lon), float(lat)] for lon, lat in ring]
        if parsed and parsed[0] != parsed[-1]:
            parsed.append(parsed[0])
        return parsed
    if geometry.get("type") == "MultiPolygon":
        ring = geometry.get("coordinates", [[[]]])[0][0]
        parsed = [[float(lon), float(lat)] for lon, lat in ring]
        if parsed and parsed[0] != parsed[-1]:
            parsed.append(parsed[0])
        return parsed
    return []


def polygon_center_lon_lat(ring: list[list[float]]) -> tuple[float, float]:
    open_ring = ring_without_close(ring)
    if not open_ring:
        return 121.4737, 31.2304
    lon = round(sum(point[0] for point in open_ring) / len(open_ring), 6)
    lat = round(sum(point[1] for point in open_ring) / len(open_ring), 6)
    return lon, lat


def ring_to_svg_points(ring: list[list[float]]) -> list[tuple[float, float]]:
    return [normalize_lon_lat_to_svg(lon, lat) for lon, lat in ring_without_close(ring)]


def transformed_ring(
    ring: list[list[float]],
    *,
    scale: float = 1.0,
    delta_lon: float = 0.0,
    delta_lat: float = 0.0,
) -> list[list[float]]:
    open_ring = ring_without_close(ring)
    if not open_ring:
        return []
    center_lon, center_lat = polygon_center_lon_lat(open_ring)
    transformed = [
        [
            round(center_lon + (lon - center_lon) * scale + delta_lon, 6),
            round(center_lat + (lat - center_lat) * scale + delta_lat, 6),
        ]
        for lon, lat in open_ring
    ]
    if transformed and transformed[0] != transformed[-1]:
        transformed.append(transformed[0])
    return transformed


def floor_ring_from_building_ring(
    ring: list[list[float]],
    building: dict[str, Any],
    floor_no: int,
) -> list[list[float]]:
    open_ring = ring_without_close(ring)
    if not open_ring:
        return []
    lon_values = [point[0] for point in open_ring]
    lat_values = [point[1] for point in open_ring]
    lon_span = max(max(lon_values) - min(lon_values), 0.00018)
    lat_span = max(max(lat_values) - min(lat_values), 0.00014)
    total_floors = max(int(building.get("totalFloors", floor_no)), 1)
    floor_ratio = min(max(int(floor_no), 1), total_floors) / total_floors
    delta_lon = (((int(floor_no) % 4) - 1.5) * lon_span) * 0.035
    delta_lat = ((0.5 - floor_ratio) * lat_span) * 0.12
    return transformed_ring(ring, scale=0.78, delta_lon=delta_lon, delta_lat=delta_lat)


def imported_building_geo_asset_index(geo_run_id: str | None = None) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if geo_run_id:
        run_summaries = [r for r in list_geo_asset_runs() if r.get("runId") == geo_run_id]
    else:
        # Skip source runs whose features inherently lack building_id — those
        # runs would be loaded into memory only to be filtered out feature-by-
        # feature inside the loop. The biggest offender is the OSM-derived run
        # (81 MB / 69k features, all building_id=None). Excluding by source id
        # turns a 4-second cold load into instant work.
        run_summaries = [
            r for r in list_geo_asset_runs()
            if str(r.get("providerId") or "") not in {"openstreetmap"}
        ]
    for run_summary in run_summaries:
        detail = geo_asset_run_detail_full(run_summary["runId"])
        if not detail:
            continue
        for feature in detail["features"]:
            properties = feature.get("properties", {})
            building_id = properties.get("building_id")
            if not building_id or building_id in index:
                continue
            ring = feature_ring(feature)
            if len(ring_without_close(ring)) < 3:
                continue
            center_lon, center_lat = polygon_center_lon_lat(ring)
            index[building_id] = {
                "runId": detail["runId"],
                "batchName": detail["batchName"],
                "providerId": detail["providerId"],
                "ring": ring,
                "svg_points": ring_to_svg_points(ring),
                "center_lon": center_lon,
                "center_lat": center_lat,
                "properties": properties,
            }
    return index


# OSM-matched community footprint counts: a side-file written by
# jobs/match_osm_to_communities.py. Surfaces "OSM 实拍楼栋数" on the user
# platform without parsing the 81 MB GeoJSON each request.
#
# Note on ID-system fallback: staged catalogs sometimes carry semantic IDs
# (`songjiang-daxuecheng`) while my AMAP-discovered catalog uses hash IDs
# (`songjiang-<digest>`) — both refer to the same real community. The
# matcher keys by AMAP id; we read with a name+district fallback so the
# user platform's semantic-ID community detail still finds its count.
@lru_cache(maxsize=1)
def _osm_community_building_counts_cached() -> dict[str, dict[str, int]]:
    import glob
    pattern = str(ROOT_DIR / "tmp" / "geo-assets" / "osm-matched-*" / "community_building_counts.json")
    candidates = sorted(glob.glob(pattern), reverse=True)
    if not candidates:
        return {"by_id": {}, "by_name": {}}
    try:
        rows = json.loads(Path(candidates[0]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"by_id": {}, "by_name": {}}
    by_id: dict[str, int] = {}
    by_name: dict[str, int] = {}
    for row in rows:
        cid = row.get("communityId") or row.get("community_id")
        name = row.get("communityName") or row.get("community_name")
        district = row.get("districtId") or row.get("district_id") or ""
        cnt = int(row.get("buildingCount") or row.get("building_count") or 0)
        if cid:
            by_id[str(cid)] = cnt
        if name:
            # Take the larger count if multiple AMAP IDs collapse to the same name+district
            key = f"{district}::{name}"
            by_name[key] = max(by_name.get(key, 0), cnt)
    return {"by_id": by_id, "by_name": by_name}


def osm_community_building_count(community_id: str, community_name: str = "", district_id: str = "") -> int:
    """OSM-derived footprint count for a community, 0 if no matched run yet.

    Looks up by community_id first; falls back to (district_id, community_name)
    so callers using a different ID system (e.g. staged shanghai-open-data IDs
    vs AMAP hash IDs) still resolve.
    """
    counts = _osm_community_building_counts_cached()
    direct = counts["by_id"].get(str(community_id))
    if direct:
        return direct
    if community_name:
        return counts["by_name"].get(f"{district_id}::{community_name}", 0)
    return 0


def database_geo_asset_index(geo_run_id: str | None = None) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    if not database_mode_active() or not geo_run_id:
        return index
    for row in db_geo_asset_rows(geo_run_id):
        building_id = row.get("building_id")
        if not building_id or building_id in index:
            continue
        geometry_json = row.get("geometry_json")
        if not geometry_json:
            continue
        try:
            geometry = json.loads(geometry_json)
        except (TypeError, json.JSONDecodeError):
            continue
        ring = feature_ring({"geometry": geometry})
        if len(ring_without_close(ring)) < 3:
            continue
        center_lon, center_lat = polygon_center_lon_lat(ring)
        index[building_id] = {
            "runId": row.get("run_id"),
            "batchName": row.get("batch_name"),
            "providerId": row.get("provider_id"),
            "ring": ring,
            "svg_points": ring_to_svg_points(ring),
            "center_lon": center_lon,
            "center_lat": center_lat,
        }
    return index


def build_geojson(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> dict[str, Any]:
    features = []
    for community in service().flatten_communities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    ):
        lon = community.get("centerLng")
        lat = community.get("centerLat")
        if lon is None or lat is None:
            lon, lat = normalize_svg_to_lon_lat(community["x"], community["y"])
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": community["name"],
                    "district": community["districtName"],
                    "avg_price_wan": community["avgPriceWan"],
                    "monthly_rent": community["monthlyRent"],
                    "yield_pct": community["yield"],
                    "opportunity_score": community["score"],
                    "sample_size": community["sample"],
                },
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }
        )
    return {"type": "FeatureCollection", "name": "Yieldwise", "features": features}


def build_building_geojson(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    geo_run_id: str | None = None,
    include_svg_props: bool = False,
) -> dict[str, Any]:
    features = []
    imported_assets = imported_building_geo_asset_index(geo_run_id)
    database_assets = database_geo_asset_index(geo_run_id)
    for community in service().flatten_communities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    ):
        for building in community.get("buildings", []):
            database_ring = feature_ring({"geometry": building.get("geometryJson")}) if database_mode_active() and building.get("geometryJson") else []
            selected_database_asset = database_assets.get(building["id"])
            imported_asset = imported_assets.get(building["id"])
            if selected_database_asset:
                ring = selected_database_asset["ring"]
                center_lng = selected_database_asset["center_lon"]
                center_lat = selected_database_asset["center_lat"]
                svg_points = selected_database_asset["svg_points"]
                center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
                geometry_source = "database_selected"
            elif database_ring:
                ring = database_ring
                center_lng, center_lat = polygon_center_lon_lat(ring)
                svg_points = ring_to_svg_points(ring)
                center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
                geometry_source = "database"
            elif imported_asset:
                center_lng = imported_asset["center_lon"]
                center_lat = imported_asset["center_lat"]
                ring = imported_asset["ring"]
                svg_points = imported_asset["svg_points"]
                center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
                geometry_source = "imported"
            else:
                center_x, center_y = building_svg_point(community, building)
                center_lng, center_lat = normalize_svg_to_lon_lat(center_x, center_y)
                svg_points = building_footprint_svg(community, building)
                ring = svg_polygon_to_lon_lat(svg_points)
                geometry_source = "synthetic"
            properties = {
                "name": f'{community["name"]} · {building["name"]}',
                "district_id": community["districtId"],
                "district_name": community["districtName"],
                "community_id": community["id"],
                "community_name": community["name"],
                "building_id": building["id"],
                "building_name": building["name"],
                "total_floors": building["totalFloors"],
                "yield_avg_pct": building["yieldAvg"],
                "yield_spread_vs_community": round(building["yieldAvg"] - community["yield"], 2),
                "opportunity_score": building["score"],
                "center_lng": center_lng,
                "center_lat": center_lat,
                "export_scope": "building_footprints",
                "geometry_source": geometry_source,
                "geo_asset_run_id": selected_database_asset["runId"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["runId"] if imported_asset else None),
                "geo_asset_batch_name": selected_database_asset["batchName"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["batchName"] if imported_asset else None),
                "geo_asset_provider_id": selected_database_asset["providerId"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["providerId"] if imported_asset else None),
            }
            if include_svg_props:
                properties["svg_points"] = [[x, y] for x, y in svg_points]
                properties["svg_center"] = [center_x, center_y]
            features.append(
                {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                }
            )
    return {"type": "FeatureCollection", "name": "YieldwiseBuildings", "features": features}


def build_kml(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> str:
    placemarks = []
    for community in service().flatten_communities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    ):
        lon = community.get("centerLng")
        lat = community.get("centerLat")
        if lon is None or lat is None:
            lon, lat = normalize_svg_to_lon_lat(community["x"], community["y"])
        placemarks.append(
            f"""
  <Placemark>
    <name>{escape_xml(community["name"])}</name>
    <description><![CDATA[
      行政区: {community["districtName"]}<br/>
      年化回报率: {community["yield"]:.2f}%<br/>
      挂牌总价: {community["avgPriceWan"]} 万<br/>
      月租中位数: {community["monthlyRent"]} 元<br/>
      机会评分: {community["score"]}<br/>
      样本量: {community["sample"]}
    ]]></description>
    <Point>
      <coordinates>{lon},{lat},0</coordinates>
    </Point>
  </Placemark>
""".rstrip()
        )

    joined = "\n".join(placemarks)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Yieldwise</name>
{joined}
  </Document>
</kml>
"""


def floor_watchlist_point(item: dict[str, Any]) -> tuple[float, float]:
    community = service().get_community(item["communityId"])
    building = service().get_building(item["buildingId"])
    if not community:
        return 121.4737, 31.2304

    floor_no = max(int(item.get("floorNo") or 1), 1)
    x, y = floor_svg_point(community, building or {"totalFloors": floor_no, "sequenceNo": 1}, floor_no)
    return normalize_svg_to_lon_lat(x, y)


def geo_task_watchlist_point(item: dict[str, Any]) -> tuple[float, float]:
    community = service().get_community(item.get("communityId"))
    building = service().get_building(item.get("buildingId")) if item.get("buildingId") else None
    if building and community:
        center_x, center_y = building_svg_point(community, building)
        return normalize_svg_to_lon_lat(center_x, center_y)
    if community:
        return normalize_svg_to_lon_lat(community["x"], community["y"])
    return 121.4737, 31.2304


def build_geo_work_order_geojson(
    *,
    district: str | None = None,
    geo_run_id: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    limit: int = 50,
    include_svg_props: bool = False,
) -> dict[str, Any]:
    selected_run_id = geo_run_id or next(iter([item["runId"] for item in list_geo_asset_runs()]), None)
    if not selected_run_id:
        return {"type": "FeatureCollection", "name": "ShanghaiGeoWorkOrders", "features": []}

    detail = geo_asset_run_detail(selected_run_id)
    if not detail:
        return {"type": "FeatureCollection", "name": "ShanghaiGeoWorkOrders", "features": []}

    imported_assets = imported_building_geo_asset_index(selected_run_id)
    features = []
    for item in geo_asset_work_orders(
        selected_run_id,
        district=district,
        status=status,
        assignee=assignee,
        limit=limit,
    ):
        community = service().get_community(item.get("communityId"))
        building = service().get_building(item.get("buildingId")) if item.get("buildingId") else None
        imported_asset = imported_assets.get(item.get("buildingId")) if item.get("buildingId") else None
        svg_points: list[tuple[float, float]] = []
        geometry: dict[str, Any]
        geometry_source = "community_anchor"

        if imported_asset and building:
            ring = imported_asset["ring"]
            center_lng = imported_asset["center_lon"]
            center_lat = imported_asset["center_lat"]
            svg_points = imported_asset["svg_points"]
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry = {"type": "Polygon", "coordinates": [ring]}
            geometry_source = "imported"
        elif community and building:
            center_x, center_y = building_svg_point(community, building)
            center_lng, center_lat = normalize_svg_to_lon_lat(center_x, center_y)
            svg_points = building_footprint_svg(community, building)
            ring = svg_polygon_to_lon_lat(svg_points)
            geometry = {"type": "Polygon", "coordinates": [ring]}
            geometry_source = "synthetic"
        elif community:
            center_x, center_y = community["x"], community["y"]
            center_lng, center_lat = normalize_svg_to_lon_lat(center_x, center_y)
            geometry = {"type": "Point", "coordinates": [center_lng, center_lat]}
        else:
            center_lng, center_lat = 121.4737, 31.2304
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry = {"type": "Point", "coordinates": [center_lng, center_lat]}
            geometry_source = "city_fallback"

        linked_tasks = item.get("linkedTasks") or []
        properties = {
            "name": item.get("title"),
            "title": item.get("title"),
            "status": item.get("status"),
            "status_label": item.get("statusLabel") or geo_work_order_status_label(item.get("status")),
            "assignee": item.get("assignee"),
            "district": item.get("districtName"),
            "district_id": item.get("districtId"),
            "community_id": item.get("communityId"),
            "community_name": item.get("communityName"),
            "building_id": item.get("buildingId"),
            "building_name": item.get("buildingName"),
            "work_order_id": item.get("workOrderId"),
            "task_count": item.get("taskCount"),
            "task_ids": item.get("taskIds"),
            "primary_task_id": item.get("primaryTaskId"),
            "linked_task_ids": [task.get("taskId") for task in linked_tasks if task.get("taskId")],
            "focus_floor_no": item.get("focusFloorNo"),
            "focus_yield_pct": item.get("focusYieldPct"),
            "impact_score": item.get("impactScore"),
            "impact_band": item.get("impactBand"),
            "watchlist_hits": item.get("watchlistHits"),
            "due_at": item.get("dueAt"),
            "created_at": item.get("createdAt"),
            "updated_at": item.get("updatedAt"),
            "created_by": item.get("createdBy"),
            "notes": item.get("notes"),
            "center_lng": center_lng,
            "center_lat": center_lat,
            "geometry_source": geometry_source,
            "geo_asset_run_id": detail.get("runId"),
            "geo_asset_batch_name": detail.get("batchName"),
            "geo_asset_provider_id": detail.get("providerId"),
            "export_scope": "geo_work_orders",
        }
        if include_svg_props:
            if svg_points:
                properties["svg_points"] = [[x, y] for x, y in svg_points]
            properties["svg_center"] = [center_x, center_y]

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})

    return {"type": "FeatureCollection", "name": "ShanghaiGeoWorkOrders", "features": features}


def build_geo_work_order_csv(
    *,
    district: str | None = None,
    geo_run_id: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    limit: int = 50,
) -> str:
    selected_run_id = geo_run_id or next(iter([item["runId"] for item in list_geo_asset_runs()]), None)
    detail = geo_asset_run_detail(selected_run_id) if selected_run_id else None

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "geo_asset_run_id",
            "geo_asset_batch_name",
            "district_name",
            "community_name",
            "building_name",
            "work_order_id",
            "title",
            "status",
            "status_label",
            "assignee",
            "task_count",
            "task_ids",
            "primary_task_id",
            "focus_floor_no",
            "focus_yield_pct",
            "impact_score",
            "impact_band",
            "watchlist_hits",
            "due_at",
            "created_at",
            "updated_at",
            "created_by",
            "notes",
        ],
    )
    writer.writeheader()
    if not selected_run_id or not detail:
        return output.getvalue()

    for item in geo_asset_work_orders(
        selected_run_id,
        district=district,
        status=status,
        assignee=assignee,
        limit=limit,
    ):
        writer.writerow(
            {
                "geo_asset_run_id": detail.get("runId"),
                "geo_asset_batch_name": detail.get("batchName"),
                "district_name": item.get("districtName"),
                "community_name": item.get("communityName"),
                "building_name": item.get("buildingName"),
                "work_order_id": item.get("workOrderId"),
                "title": item.get("title"),
                "status": item.get("status"),
                "status_label": item.get("statusLabel") or geo_work_order_status_label(item.get("status")),
                "assignee": item.get("assignee"),
                "task_count": item.get("taskCount"),
                "task_ids": "|".join(str(task_id) for task_id in (item.get("taskIds") or []) if task_id),
                "primary_task_id": item.get("primaryTaskId"),
                "focus_floor_no": item.get("focusFloorNo"),
                "focus_yield_pct": item.get("focusYieldPct"),
                "impact_score": item.get("impactScore"),
                "impact_band": item.get("impactBand"),
                "watchlist_hits": item.get("watchlistHits"),
                "due_at": item.get("dueAt"),
                "created_at": item.get("createdAt"),
                "updated_at": item.get("updatedAt"),
                "created_by": item.get("createdBy"),
                "notes": item.get("notes"),
            }
        )
    return output.getvalue()


def build_geo_task_watchlist_geojson(
    *,
    district: str | None = None,
    geo_run_id: str | None = None,
    limit: int = 50,
    include_resolved: bool = False,
    include_svg_props: bool = False,
) -> dict[str, Any]:
    features = []
    if not geo_run_id:
        return {"type": "FeatureCollection", "name": "ShanghaiGeoTaskWatchlist", "features": features}

    imported_assets = imported_building_geo_asset_index(geo_run_id)
    for item in geo_task_watchlist(
        district=district,
        geo_run_id=geo_run_id,
        limit=limit,
        include_resolved=include_resolved,
    ):
        community = service().get_community(item.get("communityId"))
        building = service().get_building(item.get("buildingId")) if item.get("buildingId") else None
        database_ring = feature_ring({"geometry": building.get("geometryJson")}) if building and database_mode_active() and building.get("geometryJson") else []
        imported_asset = imported_assets.get(item.get("buildingId")) if item.get("buildingId") else None
        svg_points: list[tuple[float, float]] = []
        geometry: dict[str, Any]
        geometry_source = "community_anchor"

        if database_ring and building:
            ring = database_ring
            center_lng, center_lat = polygon_center_lon_lat(ring)
            svg_points = ring_to_svg_points(ring)
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry = {"type": "Polygon", "coordinates": [ring]}
            geometry_source = "database"
        elif imported_asset and building:
            ring = imported_asset["ring"]
            center_lng = imported_asset["center_lon"]
            center_lat = imported_asset["center_lat"]
            svg_points = imported_asset["svg_points"]
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry = {"type": "Polygon", "coordinates": [ring]}
            geometry_source = "imported"
        elif community and building:
            center_x, center_y = building_svg_point(community, building)
            center_lng, center_lat = normalize_svg_to_lon_lat(center_x, center_y)
            svg_points = building_footprint_svg(community, building)
            ring = svg_polygon_to_lon_lat(svg_points)
            geometry = {"type": "Polygon", "coordinates": [ring]}
            geometry_source = "synthetic"
        elif community:
            center_x, center_y = community["x"], community["y"]
            center_lng, center_lat = normalize_svg_to_lon_lat(center_x, center_y)
            geometry = {"type": "Point", "coordinates": [center_lng, center_lat]}
        else:
            center_lng, center_lat = 121.4737, 31.2304
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry = {"type": "Point", "coordinates": [center_lng, center_lat]}
            geometry_source = "city_fallback"

        properties = {
            "name": f'{item.get("communityName") or "待识别小区"} · {item.get("buildingName") or "待识别楼栋"}',
            "district": item.get("districtName"),
            "district_id": item.get("districtId"),
            "community_id": item.get("communityId"),
            "community_name": item.get("communityName"),
            "building_id": item.get("buildingId"),
            "building_name": item.get("buildingName"),
            "task_id": item.get("taskId"),
            "task_scope": item.get("taskScope"),
            "task_scope_label": item.get("taskScopeLabel"),
            "status": item.get("status"),
            "status_label": item.get("statusLabel"),
            "impact_score": item.get("impactScore"),
            "impact_band": item.get("impactBand"),
            "impact_label": item.get("impactLabel"),
            "watchlist_hits": item.get("watchlistHits"),
            "focus_floor_no": item.get("focusFloorNo"),
            "focus_yield_pct": item.get("focusYieldPct"),
            "focus_trend_label": item.get("focusTrendLabel"),
            "target_granularity": item.get("targetGranularity"),
            "community_score": item.get("communityScore"),
            "building_opportunity_score": item.get("buildingOpportunityScore"),
            "coverage_gap_count": item.get("coverageGapCount"),
            "work_order_id": item.get("workOrderId"),
            "work_order_status": item.get("workOrderStatus"),
            "work_order_status_label": item.get("workOrderStatusLabel"),
            "work_order_assignee": item.get("workOrderAssignee"),
            "recommended_action": item.get("recommendedAction"),
            "source_ref": item.get("sourceRef"),
            "review_owner": item.get("reviewOwner"),
            "reviewed_at": item.get("reviewedAt"),
            "updated_at": item.get("updatedAt"),
            "center_lng": center_lng,
            "center_lat": center_lat,
            "export_scope": "geo_task_watchlist",
            "geometry_source": geometry_source,
            "geo_asset_run_id": item.get("geoAssetRunId"),
            "geo_asset_batch_name": item.get("geoAssetBatchName"),
            "geo_asset_provider_id": item.get("geoAssetProviderId"),
        }
        if include_svg_props:
            if svg_points:
                properties["svg_points"] = [[x, y] for x, y in svg_points]
            properties["svg_center"] = [center_x, center_y]

        features.append({"type": "Feature", "properties": properties, "geometry": geometry})
    return {"type": "FeatureCollection", "name": "ShanghaiGeoTaskWatchlist", "features": features}


def build_geo_task_watchlist_csv(
    *,
    district: str | None = None,
    geo_run_id: str | None = None,
    limit: int = 50,
    include_resolved: bool = False,
) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "geo_asset_run_id",
            "geo_asset_batch_name",
            "district_name",
            "community_name",
            "building_name",
            "task_id",
            "task_scope",
            "task_scope_label",
            "status",
            "status_label",
            "impact_score",
            "impact_band",
            "impact_label",
            "watchlist_hits",
            "focus_floor_no",
            "focus_yield_pct",
            "focus_trend_label",
            "target_granularity",
            "community_score",
            "building_opportunity_score",
            "coverage_gap_count",
            "work_order_id",
            "work_order_status",
            "work_order_status_label",
            "work_order_assignee",
            "source_ref",
            "recommended_action",
            "review_owner",
            "reviewed_at",
            "updated_at",
        ],
    )
    writer.writeheader()
    if not geo_run_id:
        return output.getvalue()

    for item in geo_task_watchlist(
        district=district,
        geo_run_id=geo_run_id,
        limit=limit,
        include_resolved=include_resolved,
    ):
        writer.writerow(
            {
                "geo_asset_run_id": item.get("geoAssetRunId"),
                "geo_asset_batch_name": item.get("geoAssetBatchName"),
                "district_name": item.get("districtName"),
                "community_name": item.get("communityName"),
                "building_name": item.get("buildingName"),
                "task_id": item.get("taskId"),
                "task_scope": item.get("taskScope"),
                "task_scope_label": item.get("taskScopeLabel"),
                "status": item.get("status"),
                "status_label": item.get("statusLabel"),
                "impact_score": item.get("impactScore"),
                "impact_band": item.get("impactBand"),
                "impact_label": item.get("impactLabel"),
                "watchlist_hits": item.get("watchlistHits"),
                "focus_floor_no": item.get("focusFloorNo"),
                "focus_yield_pct": item.get("focusYieldPct"),
                "focus_trend_label": item.get("focusTrendLabel"),
                "target_granularity": item.get("targetGranularity"),
                "community_score": item.get("communityScore"),
                "building_opportunity_score": item.get("buildingOpportunityScore"),
                "coverage_gap_count": item.get("coverageGapCount"),
                "work_order_id": item.get("workOrderId"),
                "work_order_status": item.get("workOrderStatus"),
                "work_order_status_label": item.get("workOrderStatusLabel"),
                "work_order_assignee": item.get("workOrderAssignee"),
                "source_ref": item.get("sourceRef"),
                "recommended_action": item.get("recommendedAction"),
                "review_owner": item.get("reviewOwner"),
                "reviewed_at": item.get("reviewedAt"),
                "updated_at": item.get("updatedAt"),
            }
        )
    return output.getvalue()


def build_floor_watchlist_geojson(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    run_id: str | None = None,
    baseline_run_id: str | None = None,
    geo_run_id: str | None = None,
    limit: int = 50,
    include_svg_props: bool = False,
) -> dict[str, Any]:
    features = []
    imported_assets = imported_building_geo_asset_index(geo_run_id)
    database_assets = database_geo_asset_index(geo_run_id)
    building_contexts = service()._floor_watchlist_building_context_by_id()
    for item in service().floor_watchlist(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        limit=limit,
    ):
        building, community = building_contexts.get(str(item["buildingId"]), (None, None))
        if not community or not building:
            continue
        database_ring = feature_ring({"geometry": building.get("geometryJson")}) if database_mode_active() and building.get("geometryJson") else []
        selected_database_asset = database_assets.get(item["buildingId"])
        imported_asset = imported_assets.get(item["buildingId"])
        if selected_database_asset:
            ring = floor_ring_from_building_ring(selected_database_asset["ring"], building, int(item["floorNo"]))
            center_lng, center_lat = polygon_center_lon_lat(ring)
            svg_points = ring_to_svg_points(ring)
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry_source = "database_selected"
        elif database_ring:
            ring = floor_ring_from_building_ring(database_ring, building, int(item["floorNo"]))
            center_lng, center_lat = polygon_center_lon_lat(ring)
            svg_points = ring_to_svg_points(ring)
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry_source = "database"
        elif imported_asset:
            ring = floor_ring_from_building_ring(imported_asset["ring"], building, int(item["floorNo"]))
            center_lng, center_lat = polygon_center_lon_lat(ring)
            svg_points = ring_to_svg_points(ring)
            center_x, center_y = normalize_lon_lat_to_svg(center_lng, center_lat)
            geometry_source = "imported"
        else:
            center_x, center_y = floor_svg_point(community, building, int(item["floorNo"]))
            center_lng, center_lat = floor_watchlist_point(item)
            svg_points = floor_footprint_svg(community, building, int(item["floorNo"]))
            ring = svg_polygon_to_lon_lat(svg_points)
            geometry_source = "synthetic"
        properties = {
            "name": f'{item["communityName"]} · {item["buildingName"]} · {item["floorNo"]}层',
            "district": item["districtName"],
            "district_id": item["districtId"],
            "community_id": item["communityId"],
            "community_name": item["communityName"],
            "building_id": item["buildingId"],
            "building_name": item["buildingName"],
            "floor_no": item["floorNo"],
            "latest_yield_pct": item["latestYieldPct"],
            "window_yield_delta_pct": item.get("windowYieldDeltaPct"),
            "yield_delta_since_first": item.get("yieldDeltaSinceFirst"),
            "latest_pair_count": item["latestPairCount"],
            "window_pair_count_delta": item.get("windowPairCountDelta"),
            "observed_runs": item["observedRuns"],
            "total_pair_count": item["totalPairCount"],
            "persistence_score": item["persistenceScore"],
            "trend_label": item["trendLabel"],
            "latest_status": item["latestStatus"],
            "latest_batch_name": item["latestBatchName"],
            "baseline_batch_name": item.get("baselineBatchName"),
            "latest_created_at": item.get("latestCreatedAt"),
            "baseline_created_at": item.get("baselineCreatedAt"),
            "center_lng": center_lng,
            "center_lat": center_lat,
            "export_scope": "floor_watchlist",
            "geometry_source": geometry_source,
            "geo_asset_run_id": selected_database_asset["runId"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["runId"] if imported_asset else None),
            "geo_asset_batch_name": selected_database_asset["batchName"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["batchName"] if imported_asset else None),
            "geo_asset_provider_id": selected_database_asset["providerId"] if selected_database_asset else (None if geometry_source == "database" else imported_asset["providerId"] if imported_asset else None),
        }
        if include_svg_props:
            properties["svg_points"] = [[x, y] for x, y in svg_points]
            properties["svg_center"] = [center_x, center_y]
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )
    return {"type": "FeatureCollection", "name": "ShanghaiYieldFloorWatchlist", "features": features}


def build_floor_watchlist_kml(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    run_id: str | None = None,
    baseline_run_id: str | None = None,
    geo_run_id: str | None = None,
    limit: int = 50,
) -> str:
    placemarks = []
    payload = build_floor_watchlist_geojson(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        geo_run_id=geo_run_id,
        limit=limit,
        include_svg_props=False,
    )
    for feature in payload.get("features", []):
        properties = feature.get("properties", {})
        ring = feature_ring(feature)
        coordinate_string = " ".join(f"{lon},{lat},0" for lon, lat in ring)
        delta_text = (
            f'{properties["window_yield_delta_pct"]:+.2f}%'
            if properties.get("window_yield_delta_pct") is not None
            else f'{properties["yield_delta_since_first"]:+.2f}%'
            if properties.get("yield_delta_since_first") is not None
            else "首批样本"
        )
        pair_delta_text = (
            f'{int(properties["window_pair_count_delta"]):+d}'
            if properties.get("window_pair_count_delta") is not None
            else "n/a"
        )
        placemarks.append(
            f"""
  <Placemark>
    <name>{escape_xml(str(properties.get("name", "楼层对象")))}</name>
    <description><![CDATA[
      行政区: {properties.get("district")}<br/>
      当前回报率: {float(properties.get("latest_yield_pct", 0.0)):.2f}%<br/>
      趋势标签: {properties.get("trend_label")}<br/>
      持续分: {properties.get("persistence_score")}<br/>
      当前批次: {properties.get("latest_batch_name")}<br/>
      基线批次: {properties.get("baseline_batch_name") or "自动首批"}<br/>
      回报变化: {delta_text}<br/>
      配对变化: {pair_delta_text}<br/>
      当前样本对: {properties.get("latest_pair_count")}<br/>
      累计样本对: {properties.get("total_pair_count")}<br/>
      观测批次: {properties.get("observed_runs")}<br/>
      几何来源: {properties.get("geometry_source")}
    ]]></description>
    <Polygon>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>{coordinate_string}</coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>
  </Placemark>
""".rstrip()
        )

    joined = "\n".join(placemarks)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Yieldwise Floor Watchlist</name>
{joined}
  </Document>
</kml>
"""


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
