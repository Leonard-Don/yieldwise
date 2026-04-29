#!/usr/bin/env python3
"""Annotate an OSM-derived geo-asset run with community associations.

Walks each polygon in `building_footprints.geojson`, computes a centroid,
finds the nearest known community whose centroid is within --max-meters,
and writes the association into the feature's properties (community_id,
community_name) plus a per-feature `match_distance_m`.

Reads the latest reference catalog (or one specified via --reference-run)
to source community centroids.

Output: a NEW geo-asset run dir alongside the input — the original is not
modified. The new run takes the same shape as manual-geometry-staging so
the workbench review pipeline picks it up.

Run:
    # auto-pick latest osm-footprints-* run as input, latest reference run as targets:
    python3 jobs/match_osm_to_communities.py

    # explicit:
    python3 jobs/match_osm_to_communities.py \\
        --osm-run osm-footprints-20260429110730 \\
        --reference-run amap-communities-2026-04-29-20260429111213 \\
        --max-meters 250
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))

OSM_RUNS_ROOT = ROOT_DIR / "tmp" / "geo-assets"
REFERENCE_RUNS_ROOT = ROOT_DIR / "tmp" / "reference-runs"

# At Shanghai's latitude (~31°N), 1° lat ≈ 111km, 1° lng ≈ 95km.
# Squared distance in m² is fine for nearest-neighbor; no need for haversine
# at sub-km scales.
DEG_TO_M_LAT = 111_000.0
DEG_TO_M_LNG_AT_31N = 95_000.0


def latest_run(runs_root: Path, prefix: str) -> Path | None:
    candidates = sorted(
        (p for p in runs_root.glob(f"{prefix}*") if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def load_reference_communities(ref_dir: Path) -> list[dict]:
    cd_path = ref_dir / "community_dictionary.json"
    if not cd_path.exists():
        return []
    rows = json.loads(cd_path.read_text(encoding="utf-8"))
    out: list[dict] = []
    for r in rows:
        try:
            lng = float(r.get("center_lng") or 0)
            lat = float(r.get("center_lat") or 0)
        except (TypeError, ValueError):
            continue
        if not lng or not lat:
            continue
        out.append({
            "community_id": r.get("community_id"),
            "community_name": r.get("community_name"),
            "district_id": r.get("district_id"),
            "district_name": r.get("district_name"),
            "lng": lng,
            "lat": lat,
        })
    return out


def polygon_centroid(coords: list[list[float]]) -> tuple[float, float] | None:
    """Average coordinate. Good enough at building-footprint scale."""
    if not coords:
        return None
    pts = coords[0] if isinstance(coords[0][0], list) else coords  # outer ring
    if not pts:
        return None
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    n = len(pts)
    return (sx / n, sy / n)


def dist_meters(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    dx = (lng1 - lng2) * DEG_TO_M_LNG_AT_31N
    dy = (lat1 - lat2) * DEG_TO_M_LAT
    return (dx * dx + dy * dy) ** 0.5


def index_communities_by_district(communities: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for c in communities:
        out.setdefault(c["district_id"] or "?", []).append(c)
    return out


def match_feature(
    feat: dict,
    by_district: dict[str, list[dict]],
    max_meters: float,
) -> tuple[dict, float | None]:
    """Return (matched_community_or_None, distance_in_m_or_None)."""
    geom = feat.get("geometry") or {}
    if geom.get("type") != "Polygon":
        return ({}, None)
    centroid = polygon_centroid(geom.get("coordinates") or [])
    if centroid is None:
        return ({}, None)
    cx, cy = centroid
    district_id = (feat.get("properties") or {}).get("district_id")
    candidates = by_district.get(district_id, []) if district_id else [c for cs in by_district.values() for c in cs]
    if not candidates:
        return ({}, None)
    best = None
    best_d = float("inf")
    for c in candidates:
        d = dist_meters(cx, cy, c["lng"], c["lat"])
        if d < best_d:
            best_d = d
            best = c
    if best is None or best_d > max_meters:
        return ({}, None)
    return (best, best_d)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--osm-run", help="OSM run folder name (default: latest osm-footprints-*)")
    p.add_argument("--reference-run", help="Reference run folder name (default: latest with center_lng populated)")
    p.add_argument("--max-meters", type=float, default=200.0, help="Max distance to consider a community match")
    p.add_argument("--batch-name", default="osm-matched")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "geo-assets")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # ── Locate OSM run ──
    if args.osm_run:
        osm_dir = OSM_RUNS_ROOT / args.osm_run
    else:
        osm_dir = latest_run(OSM_RUNS_ROOT, "osm-footprints-")
    if not osm_dir or not osm_dir.exists():
        raise SystemExit("no osm-footprints-* run found")

    # ── Locate reference run with coords ──
    if args.reference_run:
        ref_dir = REFERENCE_RUNS_ROOT / args.reference_run
    else:
        # try the AMAP-communities run first (richest), fall back to citywide-reference
        for prefix in ("amap-communities-", "shanghai-citywide-reference-"):
            ref_dir = latest_run(REFERENCE_RUNS_ROOT, prefix)
            if ref_dir is not None:
                break
    if not ref_dir or not ref_dir.exists():
        raise SystemExit("no reference run found")

    print(f"OSM run: {osm_dir.name}")
    print(f"Reference: {ref_dir.name}")

    geojson = json.loads((osm_dir / "building_footprints.geojson").read_text(encoding="utf-8"))
    features = geojson.get("features") or []
    print(f"  features: {len(features)}")

    communities = load_reference_communities(ref_dir)
    print(f"  community centroids: {len(communities)}")
    by_district = index_communities_by_district(communities)

    matched = 0
    distance_buckets: dict[str, int] = {"<50m": 0, "50-100m": 0, "100-200m": 0, ">200m": 0}
    new_features: list[dict] = []
    for feat in features:
        community, distance_m = match_feature(feat, by_district, args.max_meters)
        new_feat = json.loads(json.dumps(feat))  # deep copy
        props = new_feat.setdefault("properties", {})
        if community and distance_m is not None:
            matched += 1
            props["community_id"] = community["community_id"]
            props["community_name"] = community["community_name"]
            props["match_distance_m"] = round(distance_m, 1)
            props["resolution_notes"] = f"osm-matched: nearest community {distance_m:.0f}m away"
            if distance_m < 50:
                distance_buckets["<50m"] += 1
            elif distance_m < 100:
                distance_buckets["50-100m"] += 1
            else:
                distance_buckets["100-200m"] += 1
        else:
            distance_buckets[">200m"] += 1
        new_features.append(new_feat)

    ts = datetime.now(TZ).strftime("%Y%m%d%H%M%S")
    run_slug = f"{args.batch_name}-{ts}"
    out_dir = args.output_root / run_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    new_geojson = {
        "type": "FeatureCollection",
        "name": f"{run_slug}-building-footprints",
        "features": new_features,
    }
    write_json(out_dir / "building_footprints.geojson", new_geojson)
    write_json(out_dir / "unresolved_features.json", [])
    write_json(out_dir / "coverage_tasks.json", [])
    write_json(out_dir / "review_history.json", [])
    write_json(out_dir / "work_orders.json", [])
    write_json(out_dir / "work_order_events.json", [])

    summary = {
        "feature_count": len(new_features),
        "resolved_building_count": 0,
        "matched_community_count": matched,
        "unresolved_feature_count": len(new_features) - matched,
        "match_rate_pct": round(matched / max(len(new_features), 1) * 100, 2),
        "distance_distribution": distance_buckets,
        "max_meters_threshold": args.max_meters,
        "source_attribution": "© OpenStreetMap contributors (ODbL); community match via AMAP catalog",
        "input_osm_run": osm_dir.name,
        "input_reference_run": ref_dir.name,
    }
    write_json(out_dir / "summary.json", summary)

    write_json(out_dir / "manifest.json", {
        "run_id": run_slug,
        "provider_id": "openstreetmap",
        "adapter_scope": "geometry_batch",
        "adapter_contract": {
            "scope": "geometry_batch",
            "description": f"OSM footprints with nearest-community match within {args.max_meters}m.",
            "requiredOutputs": [
                "manifest", "building_footprints", "coverage_tasks",
                "review_history", "work_orders", "work_order_events", "summary",
            ],
            "recordKinds": ["geo_asset", "geo_capture_task", "geo_review_event", "geo_work_order"],
        },
        "batch_name": args.batch_name,
        "asset_type": "building_footprint",
        "created_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "input": {
            "osm_run": osm_dir.name, "reference_run": ref_dir.name,
            "max_meters": args.max_meters,
        },
        "summary": summary,
        "attention": {"unresolved_examples": []},
        "outputs": {
            "building_footprints": str(out_dir / "building_footprints.geojson"),
            "unresolved_features": str(out_dir / "unresolved_features.json"),
            "coverage_tasks": str(out_dir / "coverage_tasks.json"),
            "review_history": str(out_dir / "review_history.json"),
            "work_orders": str(out_dir / "work_orders.json"),
            "work_order_events": str(out_dir / "work_order_events.json"),
            "summary": str(out_dir / "summary.json"),
            "manifest": str(out_dir / "manifest.json"),
        },
    })

    print(f"\nstaged → {out_dir}")
    print(f"  matched: {matched} / {len(features)}  ({summary['match_rate_pct']}%)")
    print("  distance distribution:")
    for k, v in distance_buckets.items():
        print(f"    {k:<10} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
