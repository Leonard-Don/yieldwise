from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.service import (
    normalize_alias_list,
    read_csv_rows,
    rebuild_reference_anchor_report,
    rebuild_reference_summary,
    reference_run_detail_full,
    write_csv_rows,
    write_json_file,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_json_command(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout.strip()
    if not stdout:
        return {}
    return json.loads(stdout)


def merge_anchor_enrichment(
    *,
    reference_run_dir: Path,
    enriched_community_csv: Path,
    anchor_report_path: Path,
) -> dict[str, Any]:
    manifest_path = reference_run_dir / "manifest.json"
    manifest = load_json(manifest_path)
    run_id = str(manifest.get("run_id") or "")
    detail = reference_run_detail_full(run_id)
    if not detail:
        raise SystemExit(f"无法读取 reference run: {run_id}")

    community_rows = deepcopy(detail.get("communityRows") or [])
    district_rows = deepcopy(detail.get("districtRows") or [])
    building_rows = deepcopy(detail.get("buildingRows") or [])
    reference_catalog = deepcopy(detail.get("referenceCatalog") or {"districts": [], "communities": [], "buildings": []})
    community_csv_rows = read_csv_rows(enriched_community_csv)
    community_csv_by_id = {str(item.get("community_id") or ""): item for item in community_csv_rows if item.get("community_id")}
    alias_lookup: dict[str, list[str]] = {}

    for row in community_rows:
        community_id = str(row.get("community_id") or "")
        csv_row = community_csv_by_id.get(community_id)
        if not csv_row:
            continue
        aliases = normalize_alias_list(csv_row.get("aliases") or row.get("aliases") or [])
        source_refs = normalize_alias_list(csv_row.get("source_refs") or row.get("source_refs") or [])
        row["aliases"] = aliases
        row["center_lng"] = csv_row.get("center_lng") or None
        row["center_lat"] = csv_row.get("center_lat") or None
        row["anchor_source"] = csv_row.get("anchor_source") or None
        row["anchor_quality"] = csv_row.get("anchor_quality") or None
        row["source_refs"] = source_refs
        alias_lookup[community_id] = aliases

    for row in reference_catalog.get("communities", []):
        community_id = str(row.get("community_id") or "")
        csv_row = community_csv_by_id.get(community_id)
        if not csv_row:
            continue
        aliases = normalize_alias_list(csv_row.get("aliases") or row.get("aliases") or [])
        source_refs = normalize_alias_list(csv_row.get("source_refs") or row.get("source_refs") or [])
        row["aliases"] = aliases
        row["center_lng"] = csv_row.get("center_lng") or None
        row["center_lat"] = csv_row.get("center_lat") or None
        row["anchor_source"] = csv_row.get("anchor_source") or None
        row["anchor_quality"] = csv_row.get("anchor_quality") or None
        row["source_refs"] = source_refs

    for row in reference_catalog.get("buildings", []):
        community_id = str(row.get("community_id") or "")
        aliases = normalize_alias_list([*(row.get("community_aliases") or []), *(alias_lookup.get(community_id) or [])])
        if aliases:
            row["community_aliases"] = aliases

    anchor_report = load_json(anchor_report_path)
    existing_report_items = anchor_report.get("items") if isinstance(anchor_report.get("items"), list) else []
    rebuilt_report = rebuild_reference_anchor_report(community_rows, existing_report_items)

    summary = rebuild_reference_summary(district_rows, community_rows, building_rows)

    outputs = manifest.setdefault("outputs", {})
    inputs = manifest.setdefault("inputs", {})
    inputs["community_file"] = str(enriched_community_csv)
    outputs["community_dictionary_enriched"] = str(enriched_community_csv)
    outputs["anchor_report"] = str(anchor_report_path)
    anchor_review_history_path = reference_run_dir / "anchor_review_history.json"
    outputs["anchor_review_history"] = str(anchor_review_history_path)
    manifest["summary"] = summary

    write_json_file(detail["outputPaths"]["communityPath"], community_rows)
    write_json_file(detail["outputPaths"]["referenceCatalogPath"], reference_catalog)
    if detail["outputPaths"].get("summaryPath"):
        write_json_file(detail["outputPaths"]["summaryPath"], summary)
    write_json_file(anchor_report_path, rebuilt_report)
    if not anchor_review_history_path.exists():
        write_json_file(anchor_review_history_path, [])
    write_json_file(manifest_path, manifest)

    if community_csv_rows:
        fieldnames: list[str] = []
        for row in community_csv_rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        write_csv_rows(enriched_community_csv, fieldnames, community_csv_rows)

    return {
        "runId": run_id,
        "anchoredCommunityCount": summary.get("anchored_community_count", 0),
        "communityCount": summary.get("community_count", 0),
        "anchorReportPath": str(anchor_report_path),
        "referenceCatalogPath": str(detail["outputPaths"]["referenceCatalogPath"]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize a full staged public snapshot: reference -> enrich -> import -> geo -> metrics.")
    parser.add_argument("--snapshot-dir", required=True, type=Path)
    parser.add_argument("--snapshot-date", default=date.today().isoformat())
    parser.add_argument("--reference-batch-name", default="shanghai-citywide-reference-2026-04-14")
    parser.add_argument("--import-batch-name", default="public-browser-sampling-2026-04-14")
    parser.add_argument("--geo-batch-name", default="manual-priority-geometry-2026-04-14")
    parser.add_argument("--metrics-batch-name", default="staged-metrics-2026-04-14")
    parser.add_argument("--pause-ms", type=int, default=60)
    parser.add_argument("--enriched-community-file", type=Path, default=None)
    parser.add_argument("--anchor-report-file", type=Path, default=None)
    parser.add_argument("--browser-capture-file", type=Path, default=None)
    parser.add_argument("--browser-capture-output-dir", type=Path, default=None)
    parser.add_argument("--skip-geo", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_dir = args.snapshot_dir if args.snapshot_dir.is_absolute() else (ROOT_DIR / args.snapshot_dir)
    if not snapshot_dir.exists():
        raise SystemExit(f"snapshot-dir 不存在: {snapshot_dir}")

    district_file = snapshot_dir / "district_dictionary_seed.csv"
    community_file = snapshot_dir / "community_dictionary_seed.csv"
    building_file = snapshot_dir / "building_dictionary_seed.csv"
    sale_file = snapshot_dir / "public_browser_sampling_sale.csv"
    rent_file = snapshot_dir / "public_browser_sampling_rent.csv"
    geojson_file = snapshot_dir / "manual_priority_building_footprints.geojson"

    reference_dir = ROOT_DIR / "tmp" / "reference-runs" / args.reference_batch_name
    import_dir = ROOT_DIR / "tmp" / "import-runs" / args.import_batch_name
    geo_dir = ROOT_DIR / "tmp" / "geo-assets" / args.geo_batch_name
    enriched_csv = reference_dir / "community_dictionary_enriched.csv"
    anchor_report = reference_dir / "anchor_report.json"
    browser_capture_result: dict[str, Any] | None = None

    env = os.environ.copy()

    reference_result = run_json_command(
        [
            sys.executable,
            "jobs/import_reference_dictionary.py",
            "--provider-id",
            "shanghai-open-data",
            "--batch-name",
            args.reference_batch_name,
            "--district-file",
            str(district_file),
            "--community-file",
            str(community_file),
            "--building-file",
            str(building_file),
            "--output-dir",
            str(reference_dir),
        ],
        env=env,
    )

    if args.enriched_community_file:
        enriched_source = args.enriched_community_file if args.enriched_community_file.is_absolute() else (ROOT_DIR / args.enriched_community_file)
        if not enriched_source.exists():
            raise SystemExit(f"enriched-community-file 不存在: {enriched_source}")
        enriched_csv.parent.mkdir(parents=True, exist_ok=True)
        enriched_csv.write_text(enriched_source.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
        if args.anchor_report_file:
            anchor_source = args.anchor_report_file if args.anchor_report_file.is_absolute() else (ROOT_DIR / args.anchor_report_file)
            if not anchor_source.exists():
                raise SystemExit(f"anchor-report-file 不存在: {anchor_source}")
            anchor_report.write_text(anchor_source.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            write_json_file(anchor_report, {"community_count": 0, "anchored_count": 0, "anchored_pct": 0.0, "items": []})
    else:
        run_json_command(
            [
                sys.executable,
                "jobs/enrich_community_anchors.py",
                "--district-file",
                str(district_file),
                "--community-file",
                str(community_file),
                "--output-file",
                str(enriched_csv),
                "--report-file",
                str(anchor_report),
                "--pause-ms",
                str(args.pause_ms),
            ],
            env=env,
        )

    enrichment_result = merge_anchor_enrichment(
        reference_run_dir=reference_dir,
        enriched_community_csv=enriched_csv,
        anchor_report_path=anchor_report,
    )

    env["ATLAS_REFERENCE_CATALOG_FILE"] = enrichment_result["referenceCatalogPath"]

    if args.browser_capture_file:
        capture_file = args.browser_capture_file if args.browser_capture_file.is_absolute() else (ROOT_DIR / args.browser_capture_file)
        if not capture_file.exists():
            raise SystemExit(f"browser-capture-file 不存在: {capture_file}")
        capture_output_dir = args.browser_capture_output_dir
        if capture_output_dir is None:
            capture_output_dir = ROOT_DIR / "tmp" / "browser-capture-runs" / args.import_batch_name
        elif not capture_output_dir.is_absolute():
            capture_output_dir = ROOT_DIR / capture_output_dir
        browser_capture_result = run_json_command(
            [
                sys.executable,
                "jobs/import_public_browser_capture.py",
                "--provider-id",
                "public-browser-sampling",
                "--batch-name",
                args.import_batch_name,
                "--capture-file",
                str(capture_file),
                "--output-dir",
                str(capture_output_dir),
                "--import-output-dir",
                str(import_dir),
            ],
            env=env,
        )
        outputs = browser_capture_result.get("outputs") or {}
        sale_file = Path(str(outputs.get("sale_csv") or sale_file))
        rent_file = Path(str(outputs.get("rent_csv") or rent_file))

    if browser_capture_result and browser_capture_result.get("import_result"):
        import_result = browser_capture_result["import_result"]
    else:
        import_result = run_json_command(
            [
                sys.executable,
                "jobs/import_authorized_listings.py",
                "--provider-id",
                "public-browser-sampling",
                "--batch-name",
                args.import_batch_name,
                "--sale-file",
                str(sale_file),
                "--rent-file",
                str(rent_file),
                "--output-dir",
                str(import_dir),
            ],
            env=env,
        )

    geo_result: dict[str, Any] | None = None
    if not args.skip_geo and geojson_file.exists():
        geo_result = run_json_command(
            [
                sys.executable,
                "jobs/import_geo_assets.py",
                "--provider-id",
                "manual-geometry-staging",
                "--batch-name",
                args.geo_batch_name,
                "--geojson-file",
                str(geojson_file),
                "--output-dir",
                str(geo_dir),
            ],
            env=env,
        )

    metrics_result = run_json_command(
        [
            sys.executable,
            "jobs/refresh_metrics.py",
            "--date",
            args.snapshot_date,
            "--batch-name",
            args.metrics_batch_name,
        ],
        env=env,
    )

    print(
        json.dumps(
            {
                "snapshotDir": str(snapshot_dir),
                "reference": reference_result,
                "enrichment": enrichment_result,
                "browserCapture": browser_capture_result,
                "import": import_result,
                "geo": geo_result,
                "metrics": metrics_result,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
