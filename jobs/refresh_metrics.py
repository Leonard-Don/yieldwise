from __future__ import annotations

import argparse
import json
import sys
import re
from datetime import date, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.service import flatten_communities
from api.persistence import persist_metrics_snapshot_to_postgres


def build_snapshot(snapshot_date: date) -> dict:
    community_metrics = []
    building_floor_metrics = []

    for community in flatten_communities(use_staged_metrics_overlay=False):
        community_metrics.append(
            {
                "community_id": community["id"],
                "snapshot_date": snapshot_date.isoformat(),
                "sale_median_wan": community["avgPriceWan"],
                "rent_median_monthly": community["monthlyRent"],
                "yield_pct": community["yield"],
                "rent_sale_ratio": round((community["avgPriceWan"] * 10000) / max(community["monthlyRent"], 1), 2),
                "sale_sample_size": community["sample"],
                "rent_sample_size": 0 if int(community["sample"] or 0) <= 0 else max(1, round(community["sample"] * 0.84)),
                "opportunity_score": community["score"],
            }
        )

        for building in community["buildings"]:
            for bucket in ("low", "mid", "high"):
                bucket_value = building[bucket]
                building_floor_metrics.append(
                    {
                        "community_id": community["id"],
                        "building_id": building["id"],
                        "floor_bucket": bucket,
                        "snapshot_date": snapshot_date.isoformat(),
                        "sale_median_wan": round(community["avgPriceWan"] * (0.92 + building["sequenceNo"] * 0.03), 2),
                        "rent_median_monthly": round(community["monthlyRent"] * (bucket_value / max(community["yield"], 0.1)), 2),
                        "yield_pct": bucket_value,
                        "rent_sale_ratio": round((community["avgPriceWan"] * 10000) / max(community["monthlyRent"], 1), 2),
                        "sample_size": (
                            0
                            if int(community["sample"] or 0) <= 0
                            else max(4, round(community["sample"] / max(1, len(community["buildings"]) * 1.2)))
                        ),
                        "opportunity_score": building["score"],
                    }
                )

    return {
        "snapshot_date": snapshot_date.isoformat(),
        "community_metrics": community_metrics,
        "building_floor_metrics": building_floor_metrics,
    }


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return slug.strip("-") or "metrics-run"


def materialize_metrics_run(snapshot: dict, *, batch_name: str, output_dir: str | None = None) -> dict:
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    run_id = f"{slugify(batch_name)}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    run_dir = Path(output_dir) if output_dir else ROOT_DIR / "tmp" / "metrics-runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "community_metric_count": len(snapshot.get("community_metrics") or []),
        "building_floor_metric_count": len(snapshot.get("building_floor_metrics") or []),
        "community_coverage_count": len({item.get("community_id") for item in (snapshot.get("community_metrics") or []) if item.get("community_id")}),
        "building_coverage_count": len({item.get("building_id") for item in (snapshot.get("building_floor_metrics") or []) if item.get("building_id")}),
    }
    snapshot_path = run_dir / "snapshot.json"
    summary_path = run_dir / "summary.json"
    manifest_path = run_dir / "manifest.json"
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "run_id": run_id,
        "batch_name": batch_name,
        "created_at": created_at,
        "snapshot_date": snapshot.get("snapshot_date"),
        "outputs": {
            "snapshot": str(snapshot_path),
            "summary": str(summary_path),
        },
        "summary": summary,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "runId": run_id,
        "batchName": batch_name,
        "createdAt": created_at,
        "snapshotDate": snapshot.get("snapshot_date"),
        "outputDir": str(run_dir),
        "manifestPath": str(manifest_path),
        "summary": summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a metrics snapshot payload for the Shanghai Yield Atlas MVP.")
    parser.add_argument("--date", default=date.today().isoformat(), help="Snapshot date in YYYY-MM-DD format.")
    parser.add_argument("--output", help="Optional path to write the JSON snapshot.")
    parser.add_argument("--output-dir", help="Optional metrics run directory. When provided, materializes a staged metrics run.")
    parser.add_argument("--batch-name", help="Optional metrics batch name. When provided, materializes a staged metrics run in tmp/metrics-runs.")
    parser.add_argument("--write-postgres", action="store_true", help="Persist the snapshot into PostgreSQL metrics tables.")
    parser.add_argument("--dsn", help="Optional PostgreSQL DSN. Falls back to POSTGRES_DSN env var.")
    parser.add_argument("--apply-schema", action="store_true", help="Apply db/schema.sql before writing metrics.")
    args = parser.parse_args()

    snapshot = build_snapshot(date.fromisoformat(args.date))
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2)
    materialized = False

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
        print(f"Wrote snapshot to {output_path}")

    if args.output_dir or args.batch_name:
        metrics_run = materialize_metrics_run(
            snapshot,
            batch_name=args.batch_name or f"staged-metrics-{snapshot['snapshot_date']}",
            output_dir=args.output_dir,
        )
        print(json.dumps({"metricsRun": metrics_run}, ensure_ascii=False, indent=2))
        materialized = True

    if args.write_postgres:
        result = persist_metrics_snapshot_to_postgres(snapshot, dsn=args.dsn, apply_schema=args.apply_schema)
        print(json.dumps({"postgres": result}, ensure_ascii=False, indent=2))
        return

    if materialized:
        return

    print(payload)


if __name__ == "__main__":
    main()
