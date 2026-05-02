#!/usr/bin/env python3
"""Cross-source geometry-run overlap report.

The built-in `/api/geo-assets/runs/{id}/compare` only compares runs that
share the same provider_id + asset_type — it's designed to track diff
between successive captures of the same source. This script does the
other comparison: how well do TWO different sources (e.g. manual-
geometry-staging vs openstreetmap) cover the same buildings?

For each feature in --primary-run, find the nearest feature in
--baseline-run within --max-meters; bucket by distance; summarize.

Output:
    tmp/geo-comparisons/<TS>/
        per-feature-matches.json
        summary.json
        summary.md       # human-readable

Run:
    python3 jobs/compare_geo_runs.py
        # auto: latest manual-priority-geometry as primary,
        #       latest osm-matched as baseline

    python3 jobs/compare_geo_runs.py \\
        --primary-run manual-priority-geometry-2026-04-17-priority4-20260417204646 \\
        --baseline-run osm-matched-20260429111404 \\
        --max-meters 100
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
GEO_RUNS_ROOT = ROOT_DIR / "tmp" / "geo-assets"

DEG_TO_M_LAT = 111_000.0
DEG_TO_M_LNG_AT_31N = 95_000.0


def latest_run_with_provider(provider_id: str) -> Path | None:
    """Pick the most-recently-modified geo run whose manifest source id matches."""
    matches: list[tuple[float, Path]] = []
    for d in GEO_RUNS_ROOT.iterdir():
        if not d.is_dir():
            continue
        manifest = d / "manifest.json"
        if not manifest.exists():
            continue
        try:
            m = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if m.get("provider_id") == provider_id:
            matches.append((d.stat().st_mtime, d))
    matches.sort(key=lambda kv: kv[0], reverse=True)
    return matches[0][1] if matches else None


def load_features(run_dir: Path) -> list[dict]:
    geojson_path = run_dir / "building_footprints.geojson"
    if not geojson_path.exists():
        raise SystemExit(f"missing {geojson_path}")
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    return data.get("features") or []


def polygon_centroid(coords: list[list[float]]) -> tuple[float, float] | None:
    if not coords:
        return None
    pts = coords[0] if isinstance(coords[0][0], list) else coords
    if not pts:
        return None
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    return (sx / len(pts), sy / len(pts))


def feature_centroid(feat: dict) -> tuple[float, float] | None:
    geom = feat.get("geometry") or {}
    if geom.get("type") != "Polygon":
        return None
    return polygon_centroid(geom.get("coordinates") or [])


def dist_meters(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    dx = (lng1 - lng2) * DEG_TO_M_LNG_AT_31N
    dy = (lat1 - lat2) * DEG_TO_M_LAT
    return (dx * dx + dy * dy) ** 0.5


def build_district_index(features: list[dict]) -> dict[str, list[tuple[float, float, dict]]]:
    """Bucket baseline centroids by district_id for fast lookup."""
    out: dict[str, list[tuple[float, float, dict]]] = {}
    for feat in features:
        c = feature_centroid(feat)
        if c is None:
            continue
        props = feat.get("properties") or {}
        district = props.get("district_id") or "?"
        out.setdefault(district, []).append((c[0], c[1], feat))
    return out


def find_nearest(cx: float, cy: float, district: str, baseline_index: dict, max_m: float):
    """Return (distance, baseline_feature) or (inf, None)."""
    candidates = baseline_index.get(district, [])
    if not candidates:
        return (float("inf"), None)
    best_d = float("inf")
    best_feat = None
    for blng, blat, feat in candidates:
        d = dist_meters(cx, cy, blng, blat)
        if d < best_d:
            best_d = d
            best_feat = feat
    if best_d > max_m:
        return (float("inf"), None)
    return (best_d, best_feat)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--primary-run", help="Run dir name. Default: latest manual-geometry-staging")
    p.add_argument("--baseline-run", help="Run dir name. Default: latest openstreetmap (osm-matched)")
    p.add_argument("--max-meters", type=float, default=100.0)
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "geo-comparisons")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    primary_dir = (
        GEO_RUNS_ROOT / args.primary_run
        if args.primary_run else latest_run_with_provider("manual-geometry-staging")
    )
    baseline_dir = (
        GEO_RUNS_ROOT / args.baseline_run
        if args.baseline_run else latest_run_with_provider("openstreetmap")
    )
    if not primary_dir or not primary_dir.exists():
        raise SystemExit("no primary run found (manual-geometry-staging?)")
    if not baseline_dir or not baseline_dir.exists():
        raise SystemExit("no baseline run found (openstreetmap?)")

    print(f"Primary:  {primary_dir.name}")
    print(f"Baseline: {baseline_dir.name}")

    primary_features = load_features(primary_dir)
    baseline_features = load_features(baseline_dir)
    print(f"  primary  features: {len(primary_features)}")
    print(f"  baseline features: {len(baseline_features)}")

    baseline_index = build_district_index(baseline_features)

    # ── Per-feature analysis ──
    per_feature: list[dict] = []
    distance_buckets = {"<10m": 0, "10-25m": 0, "25-50m": 0, "50-100m": 0, ">100m or unmatched": 0}
    community_agree = 0
    community_disagree = 0
    community_one_sided = 0
    for feat in primary_features:
        c = feature_centroid(feat)
        if c is None:
            continue
        cx, cy = c
        primary_props = feat.get("properties") or {}
        district = primary_props.get("district_id") or "?"
        distance, match = find_nearest(cx, cy, district, baseline_index, args.max_meters)
        baseline_props = (match.get("properties") or {}) if match else {}

        primary_community = primary_props.get("community_id")
        baseline_community = baseline_props.get("communityId") or baseline_props.get("community_id")
        if primary_community and baseline_community:
            if primary_community == baseline_community:
                community_agree += 1
            else:
                community_disagree += 1
        elif primary_community or baseline_community:
            community_one_sided += 1

        if distance == float("inf"):
            distance_buckets[">100m or unmatched"] += 1
        elif distance < 10:
            distance_buckets["<10m"] += 1
        elif distance < 25:
            distance_buckets["10-25m"] += 1
        elif distance < 50:
            distance_buckets["25-50m"] += 1
        else:
            distance_buckets["50-100m"] += 1

        per_feature.append({
            "primary_building_id": primary_props.get("building_id"),
            "primary_building_name": primary_props.get("building_name"),
            "primary_community": primary_props.get("community_name"),
            "district": primary_props.get("district_name"),
            "match_distance_m": round(distance, 1) if distance != float("inf") else None,
            "baseline_osm_id": baseline_props.get("osmId") or baseline_props.get("source_ref"),
            "baseline_community": baseline_props.get("communityName") or baseline_props.get("community_name"),
        })

    matched = sum(v for k, v in distance_buckets.items() if k != ">100m or unmatched")
    total = len(per_feature)

    summary = {
        "primary_run": primary_dir.name,
        "baseline_run": baseline_dir.name,
        "primary_count": len(primary_features),
        "baseline_count": len(baseline_features),
        "max_meters": args.max_meters,
        "matched_within_threshold": matched,
        "match_rate_pct": round(matched / max(total, 1) * 100, 1),
        "distance_buckets": distance_buckets,
        "community_agreement": {
            "both_assigned_same": community_agree,
            "both_assigned_different": community_disagree,
            "only_one_side_assigned": community_one_sided,
        },
        "fetched_at": datetime.now(TZ).isoformat(timespec="seconds"),
    }

    ts = datetime.now(TZ).strftime("%Y%m%d%H%M%S")
    out_dir = args.output_root / f"compare-{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "per-feature-matches.json").write_text(
        json.dumps(per_feature, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    md = render_markdown(summary, per_feature[:20])
    (out_dir / "summary.md").write_text(md, encoding="utf-8")

    print(f"\nstaged → {out_dir}")
    print(f"  match_rate within {args.max_meters}m: {summary['match_rate_pct']}% ({matched}/{total})")
    print("  distance distribution:")
    for k, v in distance_buckets.items():
        print(f"    {k:<22} {v}")
    print(f"  community agreement: same={community_agree}  differ={community_disagree}  one-sided={community_one_sided}")
    return 0


def render_markdown(summary: dict, sample_rows: list[dict]) -> str:
    lines = [
        "# Geo-run cross-source comparison",
        "",
        f"- **Primary** (`{summary['primary_run']}`): {summary['primary_count']} features",
        f"- **Baseline** (`{summary['baseline_run']}`): {summary['baseline_count']} features",
        f"- **Threshold**: {summary['max_meters']} m",
        "",
        f"**Match rate**: {summary['match_rate_pct']}% ({summary['matched_within_threshold']}/{summary['primary_count']})",
        "",
        "## Distance distribution",
        "",
        "| bucket | count |",
        "|---|---:|",
    ]
    for k, v in summary["distance_buckets"].items():
        lines.append(f"| {k} | {v} |")
    lines.extend([
        "",
        "## Community-attribution agreement",
        "",
        "| outcome | count |",
        "|---|---:|",
        f"| both runs assigned same community | {summary['community_agreement']['both_assigned_same']} |",
        f"| assigned different communities | {summary['community_agreement']['both_assigned_different']} |",
        f"| only one side has assignment | {summary['community_agreement']['only_one_side_assigned']} |",
        "",
        "## First 20 per-feature rows",
        "",
        "| primary building | district | distance (m) | baseline osmId | community-agree? |",
        "|---|---|---:|---|---|",
    ])
    for row in sample_rows:
        agree = "—"
        if row.get("primary_community") and row.get("baseline_community"):
            agree = "✓" if row["primary_community"] == row["baseline_community"] else "✗"
        lines.append(
            f"| {row.get('primary_building_name') or row.get('primary_building_id') or '?'} "
            f"| {row.get('district') or '?'} "
            f"| {row.get('match_distance_m') if row.get('match_distance_m') is not None else '—'} "
            f"| {row.get('baseline_osm_id') or '—'} "
            f"| {agree} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
