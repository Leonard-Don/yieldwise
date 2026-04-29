#!/usr/bin/env python3
"""Import residential building footprints from OpenStreetMap (Overpass API)
into the project's geometry_batch staging contract.

OSM has good coverage of Shanghai residential building footprints, especially
inner-ring. This script:

1. Queries Overpass for `way["building"~"apartments|residential|house"]`
   inside a named Shanghai district (or all 16).
2. Converts each way to a GeoJSON Polygon feature.
3. Tags each feature with district_id/district_name from the query context.
   community / building resolution is left to the downstream review queue
   — most OSM buildings won't have an exact community match, but at least
   the footprints become visible in the geo-QA panel.

Output (gitignored, reversible):
    tmp/geo-assets/osm-footprints-<DATE>-<TS>/
        manifest.json
        building_footprints.geojson
        unresolved_features.json
        coverage_tasks.json
        review_history.json
        work_orders.json
        work_order_events.json
        summary.json

Run:
    # one-shot Pudong residential apartments:
    python3 jobs/import_osm_geometry.py --district pudong

    # all 16 districts (slow — ~5 min and ~50-150 MB output):
    python3 jobs/import_osm_geometry.py --all

    # tighter filter:
    python3 jobs/import_osm_geometry.py --district huangpu --building-types apartments
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

ROOT_DIR = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))

OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
# Overpass rejects "Mozilla/*" UAs as bot traffic. Use a descriptive
# project-specific UA per their fair-use guidance.
USER_AGENT = "Yieldwise/0.1 (internal research; +https://github.com/Leonard-Don/yieldwise)"

# Mirrors the project's district id → name (matches generate_amap_seed_data + others).
DISTRICTS: dict[str, str] = {
    "huangpu": "黄浦区", "jingan": "静安区", "xuhui": "徐汇区", "changning": "长宁区",
    "putuo": "普陀区", "hongkou": "虹口区", "yangpu": "杨浦区", "minhang": "闵行区",
    "baoshan": "宝山区", "jiading": "嘉定区", "pudong": "浦东新区", "jinshan": "金山区",
    "songjiang": "松江区", "qingpu": "青浦区", "fengxian": "奉贤区", "chongming": "崇明区",
}

DEFAULT_BUILDING_TYPES = "apartments|residential|house"


def _overpass_query(district_name: str, building_re: str, timeout_s: int) -> str:
    return (
        f"[out:json][timeout:{timeout_s}];"
        f'area["name"="{district_name}"]["admin_level"="6"]->.a;'
        f'way["building"~"{building_re}"](area.a);'
        f"out tags geom;"
    )


def fetch_district(district_name: str, *, building_re: str, timeout_s: int = 60) -> dict:
    body = urlencode({"data": _overpass_query(district_name, building_re, timeout_s)}).encode("utf-8")
    req = Request(
        OVERPASS_ENDPOINT,
        data=body,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urlopen(req, timeout=timeout_s + 10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"Overpass fetch failed for {district_name}: {exc}") from exc


def way_to_polygon(geom: list[dict]) -> list[list[float]] | None:
    """Convert Overpass way geometry (list of {lat, lon}) to GeoJSON Polygon coords.

    Skips degenerate ways (<4 points or unclosed). A valid Polygon ring is
    closed (first == last) and has at least 4 distinct points.
    """
    if not isinstance(geom, list) or len(geom) < 4:
        return None
    coords: list[list[float]] = []
    for p in geom:
        try:
            lon = float(p["lon"])
            lat = float(p["lat"])
        except (KeyError, TypeError, ValueError):
            return None
        coords.append([lon, lat])
    if coords[0] != coords[-1]:
        coords.append(list(coords[0]))
    if len(coords) < 4:
        return None
    return coords


def osm_to_feature(elem: dict, district_id: str, district_name: str, captured_at: str) -> dict | None:
    if elem.get("type") != "way":
        return None
    coords = way_to_polygon(elem.get("geometry") or [])
    if coords is None:
        return None
    tags = elem.get("tags") or {}
    osm_id = elem.get("id")
    name = tags.get("name") or tags.get("addr:housename") or ""
    return {
        "type": "Feature",
        "properties": {
            "provider_id": "openstreetmap",
            "source_ref": f"osm-way-{osm_id}",
            "captured_at": captured_at,
            "district_id": district_id,
            "district_name": district_name,
            "community_id": None,
            "community_name": None,
            "building_id": None,
            "building_name": name or None,
            "osm_building_type": tags.get("building"),
            "osm_addr_street": tags.get("addr:street"),
            "osm_addr_housenumber": tags.get("addr:housenumber"),
            "resolution_notes": "osm-imported (community / building unresolved)",
        },
        "geometry": {"type": "Polygon", "coordinates": [coords]},
    }


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--district", action="append", choices=sorted(DISTRICTS), help="One or more districts. Repeat to add. Default: --district pudong")
    p.add_argument("--all", action="store_true", help="Fetch every Shanghai district (slow + heavy)")
    p.add_argument("--building-types", default=DEFAULT_BUILDING_TYPES, help=f"Pipe-separated regex (default: {DEFAULT_BUILDING_TYPES!r})")
    p.add_argument("--timeout", type=int, default=60, help="Overpass timeout seconds")
    p.add_argument("--pause-ms", type=int, default=300, help="Pause between district queries (be polite to Overpass)")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "geo-assets")
    p.add_argument("--batch-name", default="osm-footprints")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        districts = list(DISTRICTS)
    elif args.district:
        districts = list(args.district)
    else:
        districts = ["pudong"]
    captured_at = datetime.now(TZ).isoformat(timespec="seconds")
    ts = datetime.now(TZ).strftime("%Y%m%d%H%M%S")
    run_slug = f"{args.batch_name}-{ts}"
    output_dir = args.output_root / run_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Querying Overpass for: {', '.join(districts)}  (building~{args.building_types!r})")
    features: list[dict] = []
    per_district: dict[str, int] = {}
    for did in districts:
        dname = DISTRICTS[did]
        print(f"  {dname:<8}", end="", flush=True)
        try:
            payload = fetch_district(dname, building_re=args.building_types, timeout_s=args.timeout)
        except RuntimeError as exc:
            print(f" ERROR: {exc}", file=sys.stderr)
            per_district[did] = 0
            continue
        elems = payload.get("elements") or []
        kept = 0
        for e in elems:
            feat = osm_to_feature(e, district_id=did, district_name=dname, captured_at=captured_at)
            if feat is not None:
                features.append(feat)
                kept += 1
        per_district[did] = kept
        print(f"  raw={len(elems):>5}  kept={kept:>5}")
        time.sleep(args.pause_ms / 1000)

    # Write the geometry_batch outputs (matching shape of manual-geometry-staging runs)
    geojson = {
        "type": "FeatureCollection",
        "name": f"{run_slug}-building-footprints",
        "features": features,
    }
    write_json(output_dir / "building_footprints.geojson", geojson)
    write_json(output_dir / "unresolved_features.json", [])
    write_json(output_dir / "coverage_tasks.json", [])
    write_json(output_dir / "review_history.json", [])
    write_json(output_dir / "work_orders.json", [])
    write_json(output_dir / "work_order_events.json", [])

    summary = {
        "feature_count": len(features),
        "resolved_building_count": 0,
        "unresolved_feature_count": len(features),
        "community_count": 0,
        "coverage_pct": 0.0,
        "coverage_task_count": 0,
        "open_task_count": 0,
        "review_task_count": 0,
        "capture_task_count": 0,
        "scheduled_task_count": 0,
        "resolved_task_count": 0,
        "per_district": per_district,
        "source_attribution": "© OpenStreetMap contributors (ODbL); fetched via Overpass API",
    }
    write_json(output_dir / "summary.json", summary)

    manifest = {
        "run_id": run_slug,
        "provider_id": "openstreetmap",
        "adapter_scope": "geometry_batch",
        "adapter_contract": {
            "scope": "geometry_batch",
            "description": "OSM-derived building footprints. Community/building resolution deferred.",
            "requiredOutputs": [
                "manifest", "building_footprints", "coverage_tasks",
                "review_history", "work_orders", "work_order_events", "summary",
            ],
            "recordKinds": [
                "geo_asset", "geo_capture_task", "geo_review_event", "geo_work_order",
            ],
        },
        "batch_name": args.batch_name,
        "asset_type": "building_footprint",
        "created_at": captured_at,
        "input": {"districts": districts, "endpoint": OVERPASS_ENDPOINT, "building_types": args.building_types},
        "summary": summary,
        "attention": {"unresolved_examples": []},
        "outputs": {
            "building_footprints": str(output_dir / "building_footprints.geojson"),
            "unresolved_features": str(output_dir / "unresolved_features.json"),
            "coverage_tasks": str(output_dir / "coverage_tasks.json"),
            "review_history": str(output_dir / "review_history.json"),
            "work_orders": str(output_dir / "work_orders.json"),
            "work_order_events": str(output_dir / "work_order_events.json"),
            "summary": str(output_dir / "summary.json"),
            "manifest": str(output_dir / "manifest.json"),
        },
    }
    write_json(output_dir / "manifest.json", manifest)

    print(f"\nstaged → {output_dir}")
    print(f"  total features: {len(features)}")
    for did, n in per_district.items():
        print(f"    {DISTRICTS[did]:<8} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
