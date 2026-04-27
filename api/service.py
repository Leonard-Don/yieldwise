from __future__ import annotations

import csv
import io
import json
import math
import re
import subprocess
import sys
from copy import deepcopy
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from .mock_data import ADDRESS_QUEUE, DATA_SOURCES, DISTRICTS, PIPELINE_STEPS, SCHEMAS, SOURCE_HEALTH, SYSTEM_STRATEGY
from .persistence import database_has_real_data, postgres_data_snapshot, postgres_runtime_status, query_row, query_rows
from .provider_adapters import mock_enabled, provider_readiness_snapshot
from .reference_catalog import load_reference_catalog

# Phase 7a: run-state aggregation extracted to api/backstage/runs.py.
# Re-exported here so existing call sites (api/main.py, persistence.py,
# clear_runtime_caches, etc.) keep resolving the same function objects.
from .backstage.runs import (  # noqa: E402,F401
    _list_geo_asset_runs_cached,
    _list_import_runs_cached,
    _list_metrics_runs_cached,
    _list_reference_runs_cached,
    _runtime_data_state_cached,
    database_mode_active,
    db_geo_asset_run_rows,
    db_import_run_rows,
    db_reference_run_rows,
    demo_mode_active,
    geo_asset_run_summary_from_db_row,
    geo_asset_run_summary_from_manifest,
    import_run_summary_from_db_row,
    import_run_summary_from_manifest,
    list_geo_asset_runs,
    list_import_runs,
    list_metrics_runs,
    list_reference_runs,
    metrics_run_summary_from_manifest,
    reference_run_summary_from_db_row,
    reference_run_summary_from_manifest,
    runtime_data_state,
    staged_mode_active,
)

# Phase 7e1: geo coverage task / work-order helpers extracted to
# api/backstage/geo_qa.py. Re-exported for back-compat.
from .backstage.geo_qa import (  # noqa: E402,F401
    available_geo_baseline_runs_for,
    db_geo_asset_rows,
    db_geo_task_rows,
    db_geo_work_order_rows,
    default_geo_review_history_path,
    default_geo_task_path,
    default_geo_work_order_event_path,
    default_geo_work_order_path,
    derive_geo_asset_tasks,
    enrich_geo_asset_review_event_for_ui,
    enrich_geo_asset_task_for_ui,
    enrich_geo_asset_tasks_with_priority,
    enrich_geo_work_order_event_for_ui,
    enrich_geo_work_order_for_ui,
    geo_manifest_path_for_run,
    geo_task_priority_band,
    geo_task_priority_label,
    geo_task_recommended_action,
    geo_task_scope_label,
    geo_task_status_label,
    geo_work_order_matches_filters,
    geo_work_order_status_label,
    geo_work_order_status_sort_key,
    summarize_geo_asset_tasks,
    summarize_geo_work_orders,
)

# Phase 7b/7c/7d: browser sampling + capture-run + review-inbox + sampling-pack
# / submit / update workflow helpers extracted to api/backstage/review.py.
# Re-exported for back-compat.
from .backstage.review import (  # noqa: E402,F401
    BROWSER_SAMPLING_REQUIRED_FIELDS,
    _browser_capture_run_detail_cached,
    _browser_capture_task_history_index_cached,
    _browser_review_current_task_fixture_candidate,
    _browser_review_inbox_all_cached,
    _browser_review_items_by_task,
    _browser_review_items_by_task_run,
    _list_browser_capture_runs_cached,
    apply_browser_capture_review_queue_update,
    browser_capture_manifest_paths,
    browser_capture_review_queue_id,
    browser_capture_review_summary,
    browser_capture_review_workflow,
    browser_capture_review_workflow_item_payload,
    browser_capture_review_workflow_payload,
    browser_capture_run_artifacts,
    browser_capture_run_detail,
    browser_capture_run_summary_from_manifest,
    browser_capture_runs_root,
    browser_capture_task_history_index,
    browser_review_fixture_root,
    browser_review_inbox_payload,
    browser_review_inbox_summary,
    browser_sampling_current_count,
    browser_sampling_missing_count,
    browser_sampling_pack,
    browser_sampling_pack_payload,
    browser_sampling_priority_label,
    browser_sampling_progress_status,
    browser_sampling_query,
    browser_sampling_required_fields,
    browser_sampling_target_count,
    browser_sampling_task_display_label,
    browser_sampling_task_lookup,
    browser_sampling_task_type_label,
    build_browser_capture_detail_rows,
    build_browser_capture_review_queue,
    build_browser_sampling_pack_csv,
    create_browser_review_current_task_fixture,
    default_browser_capture_review_resolution_note,
    latest_public_browser_import_run,
    list_browser_capture_runs,
    merge_structured_capture_rows,
    normalize_browser_capture_review_update,
    restore_browser_review_fixture,
    submit_browser_sampling_capture,
    supersede_browser_capture_review_items,
    update_browser_capture_review_queue,
    update_browser_capture_review_queue_batch,
)


ROOT_DIR = Path(__file__).resolve().parent.parent

DISTRICT_STYLE_INDEX = {
    district["id"]: {
        "labelX": district.get("labelX"),
        "labelY": district.get("labelY"),
        "polygon": district.get("polygon"),
        "fallbackX": sum(float(point.split(",")[0]) for point in district.get("polygon", "").split()) / max(len(district.get("polygon", "").split()), 1)
        if district.get("polygon")
        else None,
        "fallbackY": sum(float(point.split(",")[1]) for point in district.get("polygon", "").split()) / max(len(district.get("polygon", "").split()), 1)
        if district.get("polygon")
        else None,
    }
    for district in DISTRICTS
}

PRIORITY_DISTRICT_IDS = ["pudong", "jingan", "minhang"]

BROWSER_CAPTURE_INPUT_FIELDS = [
    "source",
    "source_listing_id",
    "business_type",
    "url",
    "community_name",
    "address_text",
    "building_text",
    "unit_text",
    "floor_text",
    "total_floors",
    "area_sqm",
    "bedrooms",
    "living_rooms",
    "bathrooms",
    "orientation",
    "decoration",
    "price_total_wan",
    "unit_price_yuan",
    "monthly_rent",
    "published_at",
    "raw_text",
    "capture_notes",
]


def priority_districts() -> list[str]:
    return list(PRIORITY_DISTRICT_IDS)




def metrics_refresh_history_path() -> Path:
    return ROOT_DIR / "tmp" / "metrics-refresh-history.json"


def slugify_identifier(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower())
    return slug.strip("-") or "browser-capture"


def manifest_paths_under(base_dir: Path) -> list[Path]:
    if not base_dir.exists():
        return []
    return sorted({path.resolve() for path in base_dir.rglob("manifest.json")}, reverse=True)


def read_json_file(path: Path | None) -> Any:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def clear_runtime_caches() -> None:
    _list_reference_runs_cached.cache_clear()
    _reference_run_detail_full_cached.cache_clear()
    _list_import_runs_cached.cache_clear()
    _import_run_detail_full_cached.cache_clear()
    _import_floor_history_for_cached.cache_clear()
    _list_metrics_runs_cached.cache_clear()
    _metrics_run_detail_cached.cache_clear()
    _list_browser_capture_runs_cached.cache_clear()
    _browser_capture_run_detail_cached.cache_clear()
    _browser_review_inbox_all_cached.cache_clear()
    _browser_capture_task_history_index_cached.cache_clear()
    _list_geo_asset_runs_cached.cache_clear()
    _geo_asset_run_detail_full_cached.cache_clear()
    _geo_asset_run_comparison_cached.cache_clear()
    _geo_asset_run_detail_cached.cache_clear()
    _reference_catalog_indices_cached.cache_clear()
    _runtime_data_state_cached.cache_clear()
    _operations_payload_cached.cache_clear()
    _bootstrap_operations_payload_cached.cache_clear()
    _system_strategy_payload_cached.cache_clear()
    _current_community_dataset_cached.cache_clear()


def metrics_refresh_status_label(status: str | None) -> str:
    return {
        "completed": "已完成",
        "partial": "部分完成",
        "error": "失败",
    }.get(str(status or "").strip().lower(), "状态待补")


def metrics_refresh_mode_label(mode: str | None) -> str:
    return {
        "staged": "仅 staged",
        "staged+postgres": "staged + PostgreSQL",
        "postgres-only": "仅 PostgreSQL",
    }.get(str(mode or "").strip().lower(), "模式待补")


def metrics_refresh_trigger_label(trigger_source: str | None) -> str:
    return {
        "atlas-ui": "工作台手动",
        "browser-sampling": "公开页采样",
        "bootstrap": "本地 Bootstrap",
    }.get(str(trigger_source or "").strip().lower(), "系统触发")


def comparable_created_at_value(value: Any) -> float:
    if isinstance(value, datetime):
        try:
            return float(value.timestamp())
        except (OverflowError, OSError, ValueError):
            return float("-inf")
    text = str(value or "").strip()
    if not text:
        return float("-inf")
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return float(datetime.fromisoformat(text).timestamp())
    except ValueError:
        return float("-inf")


def created_at_is_before(left: Any, right: Any) -> bool:
    return comparable_created_at_value(left) < comparable_created_at_value(right)


def build_metrics_refresh_history_entry(
    *,
    batch_name: str,
    snapshot_date: str,
    write_postgres: bool,
    trigger_source: str,
    status: str,
    postgres_status: str,
    created_at: str | None = None,
    metrics_run: dict[str, Any] | None = None,
    postgres_summary: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    error: str | None = None,
    mode: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    resolved_created_at = created_at or datetime.now().astimezone().isoformat(timespec="seconds")
    resolved_mode = str(mode or ("staged+postgres" if write_postgres else "staged")).strip().lower()
    resolved_status = str(status or "completed").strip().lower()
    resolved_postgres_status = str(postgres_status or ("completed" if write_postgres else "skipped")).strip().lower()
    normalized_summary = summary if isinstance(summary, dict) else {}
    normalized_postgres_summary = postgres_summary if isinstance(postgres_summary, dict) else None
    entry = {
        "eventId": str(event_id or f"metrics-refresh-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"),
        "createdAt": resolved_created_at,
        "snapshotDate": snapshot_date,
        "batchName": batch_name,
        "metricsRunId": metrics_run.get("runId") if isinstance(metrics_run, dict) else None,
        "metricsRunCreatedAt": metrics_run.get("createdAt") if isinstance(metrics_run, dict) else None,
        "status": resolved_status,
        "statusLabel": metrics_refresh_status_label(resolved_status),
        "mode": resolved_mode,
        "modeLabel": metrics_refresh_mode_label(resolved_mode),
        "writePostgres": bool(write_postgres),
        "postgresStatus": resolved_postgres_status,
        "triggerSource": str(trigger_source or "atlas-ui").strip().lower() or "atlas-ui",
        "triggerLabel": metrics_refresh_trigger_label(trigger_source),
        "summary": {
            "communityMetricCount": int(normalized_summary.get("communityMetricCount") or 0),
            "buildingFloorMetricCount": int(normalized_summary.get("buildingFloorMetricCount") or 0),
            "communityCoverageCount": int(normalized_summary.get("communityCoverageCount") or 0),
            "buildingCoverageCount": int(normalized_summary.get("buildingCoverageCount") or 0),
        },
        "postgresSummary": normalized_postgres_summary,
    }
    if error:
        entry["error"] = str(error)
    return entry


def append_metrics_refresh_history(entry: dict[str, Any], *, limit: int = 12) -> None:
    existing_rows = read_json_file(metrics_refresh_history_path())
    history_rows = [row for row in existing_rows if isinstance(row, dict)] if isinstance(existing_rows, list) else []
    write_json_file(metrics_refresh_history_path(), [deepcopy(entry), *history_rows][: max(limit, 1)])


def list_metrics_refresh_history(limit: int | None = None) -> list[dict[str, Any]]:
    rows = read_json_file(metrics_refresh_history_path())
    if not isinstance(rows, list):
        return []
    items = [row for row in rows if isinstance(row, dict)]
    normalized_items = [
        build_metrics_refresh_history_entry(
            batch_name=str(item.get("batchName") or "未命名批次").strip() or "未命名批次",
            snapshot_date=str(item.get("snapshotDate") or "").strip() or "待补",
            write_postgres=bool(item.get("writePostgres")),
            trigger_source=str(item.get("triggerSource") or "atlas-ui"),
            status=str(item.get("status") or "completed"),
            postgres_status=str(item.get("postgresStatus") or ("completed" if item.get("writePostgres") else "skipped")),
            created_at=str(item.get("createdAt") or "").strip() or None,
            metrics_run={
                "runId": item.get("metricsRunId"),
                "createdAt": item.get("metricsRunCreatedAt"),
            },
            postgres_summary=item.get("postgresSummary") if isinstance(item.get("postgresSummary"), dict) else None,
            summary=item.get("summary") if isinstance(item.get("summary"), dict) else None,
            error=str(item.get("error") or "").strip() or None,
            mode=str(item.get("mode") or "").strip() or None,
            event_id=str(item.get("eventId") or "").strip() or None,
        )
        for item in items
    ]
    return deepcopy(normalized_items[:limit] if limit is not None else normalized_items)


def refresh_metrics_snapshot(
    *,
    snapshot_date: date | str | None = None,
    batch_name: str | None = None,
    write_postgres: bool = False,
    apply_schema: bool = False,
    dsn: str | None = None,
    trigger_source: str = "atlas-ui",
) -> dict[str, Any]:
    from jobs.refresh_metrics import build_snapshot, materialize_metrics_run
    from .persistence import persist_metrics_snapshot_to_postgres

    if snapshot_date is None:
        resolved_snapshot_date = datetime.now().astimezone().date()
    elif isinstance(snapshot_date, str):
        resolved_snapshot_date = date.fromisoformat(snapshot_date)
    else:
        resolved_snapshot_date = snapshot_date

    resolved_batch_name = str(batch_name or f"staged-metrics-{resolved_snapshot_date.isoformat()}").strip()
    if not resolved_batch_name:
        raise ValueError("batch_name cannot be empty")

    metrics_run: dict[str, Any] | None = None
    postgres_payload: dict[str, Any] | None = None
    steps: list[dict[str, Any]] = []
    metrics_response_summary = {
        "communityMetricCount": 0,
        "buildingFloorMetricCount": 0,
        "communityCoverageCount": 0,
        "buildingCoverageCount": 0,
    }
    history_status = "completed"
    postgres_status = "pending" if write_postgres else "skipped"

    try:
        snapshot = build_snapshot(resolved_snapshot_date)
        metrics_run = materialize_metrics_run(snapshot, batch_name=resolved_batch_name)
        raw_metrics_summary = metrics_run.get("summary") or {}
        metrics_response_summary = {
            "communityMetricCount": int(raw_metrics_summary.get("community_metric_count") or 0),
            "buildingFloorMetricCount": int(raw_metrics_summary.get("building_floor_metric_count") or 0),
            "communityCoverageCount": int(raw_metrics_summary.get("community_coverage_count") or 0),
            "buildingCoverageCount": int(raw_metrics_summary.get("building_coverage_count") or 0),
        }
        steps.append(
            {
                "step": "staged",
                "status": "completed",
                "runId": metrics_run.get("runId"),
                "summary": metrics_run.get("summary"),
            }
        )
        if write_postgres:
            postgres_payload = persist_metrics_snapshot_to_postgres(snapshot, dsn=dsn, apply_schema=apply_schema)
            postgres_status = "completed"
            steps.append(
                {
                    "step": "postgres",
                    "status": "completed",
                    "summary": postgres_payload,
                }
            )
        else:
            steps.append({"step": "postgres", "status": "skipped", "reason": "调用方未请求 PostgreSQL 写入。"})

        return {
            "status": "completed",
            "metricsRun": metrics_run,
            "postgres": postgres_payload,
            "steps": steps,
            "requested": {
                "snapshotDate": resolved_snapshot_date.isoformat(),
                "batchName": resolved_batch_name,
                "writePostgres": write_postgres,
                "triggerSource": str(trigger_source or "atlas-ui").strip().lower() or "atlas-ui",
            },
            "summary": metrics_response_summary,
        }
    except Exception as exc:
        if not steps:
            history_status = "error"
            steps.append({"step": "staged", "status": "error", "reason": str(exc)})
        elif write_postgres and postgres_status == "pending":
            postgres_status = "error"
            steps.append({"step": "postgres", "status": "error", "reason": str(exc)})
            history_status = "partial"
        else:
            history_status = "error"
        raise
    finally:
        try:
            append_metrics_refresh_history(
                build_metrics_refresh_history_entry(
                    batch_name=resolved_batch_name,
                    snapshot_date=resolved_snapshot_date.isoformat(),
                    write_postgres=write_postgres,
                    trigger_source=trigger_source,
                    status=history_status,
                    postgres_status=postgres_status,
                    metrics_run=metrics_run,
                    postgres_summary=postgres_payload,
                    summary=metrics_response_summary,
                    error=steps[-1].get("reason") if steps and steps[-1].get("status") == "error" else None,
                )
            )
        except Exception as history_exc:  # pragma: no cover - best effort local history
            print(f"[atlas] metrics refresh history append failed: {history_exc}", file=sys.stderr)
        clear_runtime_caches()


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    clear_runtime_caches()


def resolve_artifact_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    return path if path.is_absolute() else ROOT_DIR / path


def default_review_history_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "review_history.json"


def default_browser_capture_review_queue_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "review_queue.json"


def default_anchor_review_history_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "anchor_review_history.json"


def default_reference_anchor_report_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "anchor_report.json"


def import_manifest_paths() -> list[Path]:
    return manifest_paths_under(ROOT_DIR / "tmp" / "import-runs")


def geo_asset_manifest_paths() -> list[Path]:
    return manifest_paths_under(ROOT_DIR / "tmp" / "geo-assets")


def reference_manifest_paths() -> list[Path]:
    return manifest_paths_under(ROOT_DIR / "tmp" / "reference-runs")


def metrics_manifest_paths() -> list[Path]:
    return manifest_paths_under(ROOT_DIR / "tmp" / "metrics-runs")


def read_csv_rows(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except OSError:
        return []


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    clear_runtime_caches()


def db_summary_json(summary_value: Any) -> dict[str, Any]:
    if isinstance(summary_value, dict):
        return summary_value
    if isinstance(summary_value, str):
        try:
            parsed = json.loads(summary_value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def existing_output_manifest_path(path_value: str | None) -> Path | None:
    path = resolve_artifact_path(path_value)
    if path is None or not path.exists():
        return None
    return path


def reference_manifest_path_for_run(run_id: str) -> Path | None:
    for manifest_path in reference_manifest_paths():
        manifest = read_json_file(manifest_path)
        if isinstance(manifest, dict) and manifest.get("run_id") == run_id:
            return manifest_path
    return None


@lru_cache(maxsize=64)
def _reference_run_detail_full_cached(run_id: str) -> dict[str, Any] | None:
    manifest_path = reference_manifest_path_for_run(run_id)
    if manifest_path is None:
        return None
    manifest = read_json_file(manifest_path)
    if not isinstance(manifest, dict) or manifest.get("run_id") != run_id:
        return None
    run_summary = reference_run_summary_from_manifest(manifest, manifest_path)
    outputs = manifest.get("outputs", {})
    inputs = manifest.get("inputs", {})
    district_path = resolve_artifact_path(outputs.get("district_dictionary"))
    community_path = resolve_artifact_path(outputs.get("community_dictionary"))
    building_path = resolve_artifact_path(outputs.get("building_dictionary"))
    reference_catalog_path = resolve_artifact_path(outputs.get("reference_catalog"))
    summary_path = resolve_artifact_path(outputs.get("summary"))
    anchor_report_path = (
        resolve_artifact_path(outputs.get("anchor_report"))
        or default_reference_anchor_report_path(manifest_path)
    )
    review_history_path = (
        resolve_artifact_path(outputs.get("anchor_review_history"))
        or default_anchor_review_history_path(manifest_path)
    )
    community_csv_path = (
        resolve_artifact_path(outputs.get("community_dictionary_enriched"))
        or resolve_artifact_path(inputs.get("community_file"))
        or (manifest_path.parent / "community_dictionary_enriched.csv")
    )
    district_rows = read_json_file(district_path) or []
    community_rows = read_json_file(community_path) or []
    building_rows = read_json_file(building_path) or []
    reference_catalog = read_json_file(reference_catalog_path) or {}
    summary = read_json_file(summary_path) or manifest.get("summary", {})
    anchor_report = read_json_file(anchor_report_path) or {
        "community_count": len(community_rows),
        "anchored_count": sum(
            1 for item in community_rows if item.get("center_lng") not in (None, "") and item.get("center_lat") not in (None, "")
        ),
        "items": [],
    }
    review_history = read_json_file(review_history_path) or []
    community_csv_rows = read_csv_rows(community_csv_path)
    return {
        **run_summary,
        "manifestPath": manifest_path,
        "manifest": manifest,
        "summary": summary,
        "outputPaths": {
            "districtPath": district_path,
            "communityPath": community_path,
            "buildingPath": building_path,
            "referenceCatalogPath": reference_catalog_path,
            "communityCsvPath": community_csv_path,
            "summaryPath": summary_path,
            "anchorReportPath": anchor_report_path,
            "anchorReviewHistoryPath": review_history_path,
        },
        "districtRows": district_rows,
        "communityRows": community_rows,
        "buildingRows": building_rows,
        "communityCsvRows": community_csv_rows,
        "referenceCatalog": reference_catalog,
        "anchorReport": anchor_report,
        "anchorReviewHistory": review_history,
    }


def reference_run_detail_full(run_id: str) -> dict[str, Any] | None:
    detail = _reference_run_detail_full_cached(run_id)
    return deepcopy(detail) if detail else None


@lru_cache(maxsize=64)
def _metrics_run_detail_cached(run_id: str) -> dict[str, Any] | None:
    for manifest_path in metrics_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or manifest.get("run_id") != run_id:
            continue
        outputs = manifest.get("outputs", {})
        snapshot_path = resolve_artifact_path(outputs.get("snapshot"))
        summary_path = resolve_artifact_path(outputs.get("summary"))
        snapshot = read_json_file(snapshot_path) or {}
        summary = read_json_file(summary_path) or manifest.get("summary", {})
        return {
            **metrics_run_summary_from_manifest(manifest, manifest_path),
            "manifest": manifest,
            "manifestPath": manifest_path,
            "summary": summary,
            "snapshot": snapshot,
            "outputPaths": {
                "snapshotPath": snapshot_path,
                "summaryPath": summary_path,
            },
        }
    return None


def metrics_run_detail(run_id: str) -> dict[str, Any] | None:
    detail = _metrics_run_detail_cached(run_id)
    return deepcopy(detail) if detail else None


def latest_metrics_run_detail() -> dict[str, Any] | None:
    runs = list_metrics_runs()
    if not runs:
        return None
    return metrics_run_detail(runs[0]["runId"])


def latest_metrics_overlay() -> dict[str, Any]:
    detail = latest_metrics_run_detail()
    if not detail:
        return {
            "run": None,
            "communityIndex": {},
            "buildingBucketIndex": {},
        }
    snapshot = detail.get("snapshot") or {}
    community_index = {
        str(item.get("community_id")): item
        for item in (snapshot.get("community_metrics") or [])
        if item.get("community_id")
    }
    building_bucket_index: dict[str, dict[str, dict[str, Any]]] = {}
    for item in snapshot.get("building_floor_metrics") or []:
        building_id = str(item.get("building_id") or "")
        floor_bucket = str(item.get("floor_bucket") or "")
        if not building_id or not floor_bucket:
            continue
        building_bucket_index.setdefault(building_id, {})[floor_bucket] = item
    return {
        "run": detail,
        "communityIndex": community_index,
        "buildingBucketIndex": building_bucket_index,
    }


def latest_reference_anchor_review_lookup() -> dict[str, dict[str, Any]]:
    reference_runs = list_reference_runs()
    if not reference_runs:
        return {}
    detail = reference_run_detail_full(reference_runs[0]["runId"])
    if not detail:
        return {}
    latest_by_community: dict[str, dict[str, Any]] = {}
    for item in detail.get("anchorReviewHistory", []):
        if not isinstance(item, dict) or not item.get("communityId"):
            continue
        community_id = str(item.get("communityId"))
        current = latest_by_community.get(community_id)
        if current and (current.get("reviewedAt") or "") >= (item.get("reviewedAt") or ""):
            continue
        latest_by_community[community_id] = item
    return latest_by_community


STAGED_DISTRICT_LAYOUTS = {
    "jingan": {"name": "静安区", "short": "静安", "fallbackX": 318.0, "fallbackY": 182.0},
    "huangpu": {"name": "黄浦区", "short": "黄浦", "fallbackX": 362.0, "fallbackY": 244.0},
    "xuhui": {"name": "徐汇区", "short": "徐汇", "fallbackX": 326.0, "fallbackY": 298.0},
    "changning": {"name": "长宁区", "short": "长宁", "fallbackX": 252.0, "fallbackY": 234.0},
    "hongkou": {"name": "虹口区", "short": "虹口", "fallbackX": 410.0, "fallbackY": 186.0},
}


def median_value(values: list[float | int | None]) -> float | None:
    numbers = sorted(float(item) for item in values if item not in (None, ""))
    if not numbers:
        return None
    middle = len(numbers) // 2
    if len(numbers) % 2 == 1:
        return round(numbers[middle], 2)
    return round((numbers[middle - 1] + numbers[middle]) / 2, 2)


def parse_iso_datetime(value: Any) -> datetime | None:
    if hasattr(value, "isoformat"):
        try:
            return datetime.fromisoformat(value.isoformat())
        except (TypeError, ValueError):
            return None
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def latest_datetime_iso(values: list[Any]) -> str | None:
    parsed = [item for item in (parse_iso_datetime(value) for value in values) if item]
    if not parsed:
        return None
    normalized = []
    local_tz = datetime.now().astimezone().tzinfo
    for item in parsed:
        if item.tzinfo is None:
            normalized.append(item.replace(tzinfo=local_tz))
        else:
            normalized.append(item.astimezone(local_tz))
    return max(normalized).isoformat()


def staged_district_shape(district_id: str, district_name: str) -> dict[str, Any]:
    style = district_style(district_id)
    layout = STAGED_DISTRICT_LAYOUTS.get(district_id, {})
    fallback_x = style.get("fallbackX") or layout.get("fallbackX") or 380.0
    fallback_y = style.get("fallbackY") or layout.get("fallbackY") or 260.0
    polygon = style.get("polygon")
    if not polygon:
        polygon_points = [
            f"{round(fallback_x - 46, 2)},{round(fallback_y - 28, 2)}",
            f"{round(fallback_x + 44, 2)},{round(fallback_y - 18, 2)}",
            f"{round(fallback_x + 52, 2)},{round(fallback_y + 18, 2)}",
            f"{round(fallback_x - 12, 2)},{round(fallback_y + 34, 2)}",
            f"{round(fallback_x - 56, 2)},{round(fallback_y + 8, 2)}",
        ]
        polygon = " ".join(polygon_points)
    return {
        "id": district_id,
        "name": district_name,
        "short": style.get("short") or layout.get("short") or district_name[:2],
        "polygon": polygon,
        "labelX": style.get("labelX") or round(fallback_x, 2),
        "labelY": style.get("labelY") or round(fallback_y, 2),
        "fallbackX": round(fallback_x, 2),
        "fallbackY": round(fallback_y, 2),
    }


def anchor_decision_state_for(
    *,
    center_lng: Any = None,
    center_lat: Any = None,
    preview_lng: Any = None,
    preview_lat: Any = None,
    latest_review: dict[str, Any] | None = None,
    anchor_source: str | None = None,
) -> str:
    action = str((latest_review or {}).get("action") or "").strip()
    if action == "manual_override" or (anchor_source or "").startswith("manual_override"):
        return "manual_override"
    if center_lng not in (None, "") and center_lat not in (None, ""):
        return "confirmed"
    if preview_lng not in (None, "") and preview_lat not in (None, ""):
        return "pending"
    return "pending"


@lru_cache(maxsize=1)
def _reference_catalog_indices_cached() -> dict[str, Any]:
    catalog = load_reference_catalog(allow_mock=False)
    district_index: dict[str, dict[str, Any]] = {}
    community_index: dict[str, dict[str, Any]] = {}
    building_index: dict[str, dict[str, Any]] = {}
    anchor_report_lookup = latest_reference_anchor_report_lookup()
    anchor_review_lookup = latest_reference_anchor_review_lookup()
    for ref in catalog.get("district_refs", []):
        district_layout = staged_district_shape(ref.district_id, ref.district_name)
        district_index[ref.district_id] = {
            "districtId": ref.district_id,
            "districtName": ref.district_name,
            "districtShort": ref.short_name or district_layout["short"],
        }
    for ref in catalog.get("community_refs", []):
        district_layout = staged_district_shape(ref.district_id, ref.district_name)
        anchor_report = anchor_report_lookup.get(ref.community_id, {})
        latest_review = anchor_review_lookup.get(ref.community_id)
        preview_center_lng = anchor_report.get("center_lng") if ref.center_lng is None else None
        preview_center_lat = anchor_report.get("center_lat") if ref.center_lat is None else None
        community_index[ref.community_id] = {
            "districtId": ref.district_id,
            "districtName": ref.district_name,
            "districtShort": ref.district_short_name or district_layout["short"],
            "communityId": ref.community_id,
            "communityName": ref.community_name,
            "communityAliases": list(ref.aliases),
            "centerLng": ref.center_lng,
            "centerLat": ref.center_lat,
            "anchorSource": ref.anchor_source,
            "anchorQuality": ref.anchor_quality,
            "sourceConfidence": ref.source_confidence,
            "sourceRefs": list(ref.source_refs),
            "candidateSuggestions": list(anchor_report.get("candidate_suggestions") or ref.candidate_suggestions),
            "previewCenterLng": preview_center_lng,
            "previewCenterLat": preview_center_lat,
            "previewAnchorSource": anchor_report.get("match_source") if ref.center_lng is None else None,
            "previewAnchorQuality": anchor_report.get("anchor_quality") if ref.center_lng is None else None,
            "previewAnchorName": anchor_report.get("poi_name") if ref.center_lng is None else None,
            "previewAnchorAddress": anchor_report.get("formatted_address") if ref.center_lng is None else None,
            "anchorDecisionState": anchor_decision_state_for(
                center_lng=ref.center_lng,
                center_lat=ref.center_lat,
                preview_lng=preview_center_lng,
                preview_lat=preview_center_lat,
                latest_review=latest_review,
                anchor_source=ref.anchor_source,
            ),
            "latestAnchorReview": deepcopy(latest_review) if latest_review else None,
        }
    for ref in catalog.get("building_refs", []):
        district_layout = staged_district_shape(ref.district_id, ref.district_name)
        community_entry = community_index.setdefault(
            ref.community_id,
            {
                "districtId": ref.district_id,
                "districtName": ref.district_name,
                "districtShort": ref.district_short_name or district_layout["short"],
                "communityId": ref.community_id,
                "communityName": ref.community_name,
                "communityAliases": list(ref.community_aliases),
                "centerLng": None,
                "centerLat": None,
                "anchorSource": None,
                "anchorQuality": None,
                "sourceConfidence": None,
                "sourceRefs": [],
                "candidateSuggestions": [],
                "previewCenterLng": None,
                "previewCenterLat": None,
                "previewAnchorSource": None,
                "previewAnchorQuality": None,
                "previewAnchorName": None,
                "previewAnchorAddress": None,
                "anchorDecisionState": "pending",
                "latestAnchorReview": None,
            },
        )
        community_entry["communityAliases"] = sorted(
            {*(community_entry.get("communityAliases") or []), *list(ref.community_aliases), ref.community_name}
        )
        building_index[ref.building_id] = {
            "districtId": ref.district_id,
            "districtName": ref.district_name,
            "districtShort": ref.district_short_name or district_layout["short"],
            "communityId": ref.community_id,
            "communityName": ref.community_name,
            "buildingId": ref.building_id,
            "buildingName": ref.building_name,
            "totalFloors": ref.total_floors,
            "communityAliases": list(ref.community_aliases),
            "buildingAliases": list(ref.building_aliases),
            "sourceRefs": list(ref.source_refs),
            "centerLng": ref.center_lng or community_entry.get("centerLng"),
            "centerLat": ref.center_lat or community_entry.get("centerLat"),
            "anchorSource": ref.anchor_source,
            "anchorQuality": ref.anchor_quality,
        }
    return {"districts": district_index, "communities": community_index, "buildings": building_index}


def reference_catalog_indices() -> dict[str, Any]:
    return deepcopy(_reference_catalog_indices_cached())


def place_labels_from_indices(indexes: dict[str, Any], community_id: str | None, building_id: str | None = None) -> dict[str, str | None]:
    building_ref = indexes.get("buildings", {}).get(building_id) if building_id else None
    community_ref = indexes.get("communities", {}).get(community_id) if community_id else None
    district_name = (building_ref or community_ref or {}).get("districtName")
    community_name = (building_ref or community_ref or {}).get("communityName")
    building_name = building_ref.get("buildingName") if building_ref else None
    return {
        "districtName": district_name,
        "communityName": community_name,
        "buildingName": building_name,
    }


def latest_reference_anchor_report_lookup() -> dict[str, dict[str, Any]]:
    reference_runs = list_reference_runs()
    if not reference_runs:
        return {}
    detail = reference_run_detail_full(reference_runs[0]["runId"])
    if not detail or not isinstance(detail.get("anchorReport"), dict):
        return {}
    items = detail["anchorReport"].get("items")
    if not isinstance(items, list):
        return {}
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict) or not item.get("community_id"):
            continue
        lookup[str(item["community_id"])] = item
    if lookup:
        return lookup
    return {}


def reference_anchor_present(item: dict[str, Any]) -> bool:
    return item.get("center_lng") not in (None, "") and item.get("center_lat") not in (None, "")


def normalize_alias_list(values: Any) -> list[str]:
    if isinstance(values, str):
        raw_values = values.replace(";", "|").split("|")
    elif isinstance(values, list):
        raw_values = values
    else:
        raw_values = []
    normalized: list[str] = []
    for value in raw_values:
        text = str(value or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    return normalized


def serialize_alias_list(values: list[str]) -> str:
    return "|".join(normalize_alias_list(values))


def to_float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rebuild_reference_summary(
    district_rows: list[dict[str, Any]],
    community_rows: list[dict[str, Any]],
    building_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_refs = {
        str(source_ref).strip()
        for item in [*community_rows, *building_rows]
        for source_ref in (item.get("source_refs") or [])
        if str(source_ref or "").strip()
    }
    return {
        "district_count": len(district_rows),
        "community_count": len(community_rows),
        "building_count": len(building_rows),
        "community_alias_count": sum(len(normalize_alias_list(item.get("aliases") or [])) for item in community_rows),
        "building_alias_count": sum(len(normalize_alias_list(item.get("aliases") or [])) for item in building_rows),
        "source_ref_count": len(source_refs),
        "anchored_community_count": sum(1 for item in community_rows if reference_anchor_present(item)),
        "anchored_building_count": sum(
            1 for item in building_rows if item.get("center_lng") not in (None, "") and item.get("center_lat") not in (None, "")
        ),
    }


def rebuild_reference_anchor_report(
    community_rows: list[dict[str, Any]],
    existing_items: list[dict[str, Any]],
) -> dict[str, Any]:
    unresolved_lookup = {
        str(item.get("community_id")): item
        for item in existing_items
        if isinstance(item, dict) and item.get("community_id")
    }
    anchored_count = sum(1 for item in community_rows if reference_anchor_present(item))
    unresolved_items: list[dict[str, Any]] = []
    for community in community_rows:
        community_id = str(community.get("community_id") or "")
        if not community_id or reference_anchor_present(community):
            continue
        existing = unresolved_lookup.get(community_id)
        if existing:
            unresolved_items.append(existing)
    unresolved_items.sort(
        key=lambda item: (
            item.get("district_id") or "",
            item.get("community_name") or "",
        )
    )
    return {
        "community_count": len(community_rows),
        "anchored_count": anchored_count,
        "anchored_pct": round(anchored_count / max(len(community_rows), 1) * 100, 1) if community_rows else 0.0,
        "items": unresolved_items,
    }


def latest_anchor_review_at(review_history: list[dict[str, Any]]) -> str | None:
    timestamps = [item.get("reviewedAt") for item in review_history if isinstance(item, dict)]
    return latest_datetime_iso(timestamps)


def target_reference_run_id(reference_run_id: str | None = None) -> str | None:
    if reference_run_id:
        return reference_run_id
    reference_runs = list_reference_runs()
    if not reference_runs:
        return None
    return str(reference_runs[0]["runId"])


def confirm_community_anchor(
    community_id: str,
    *,
    action: str,
    candidate_index: int | None = None,
    center_lng: float | None = None,
    center_lat: float | None = None,
    anchor_source_label: str | None = None,
    review_note: str | None = None,
    alias_hint: str | None = None,
    reference_run_id: str | None = None,
    review_owner: str = "atlas-ui",
) -> dict[str, Any] | None:
    run_id = target_reference_run_id(reference_run_id)
    if not run_id:
        return None
    detail = reference_run_detail_full(run_id)
    if not detail:
        return None

    community_rows = deepcopy(detail.get("communityRows", []))
    building_rows = deepcopy(detail.get("buildingRows", []))
    district_rows = deepcopy(detail.get("districtRows", []))
    reference_catalog = deepcopy(detail.get("referenceCatalog") or {"districts": [], "communities": [], "buildings": []})
    anchor_report = deepcopy(detail.get("anchorReport") or {"items": []})
    review_history = deepcopy(detail.get("anchorReviewHistory", []))
    community_csv_rows = deepcopy(detail.get("communityCsvRows", []))

    target_row = next((item for item in community_rows if str(item.get("community_id")) == community_id), None)
    if not target_row:
        return None

    report_items = anchor_report.get("items") if isinstance(anchor_report.get("items"), list) else []
    report_item = next((item for item in report_items if str(item.get("community_id")) == community_id), None)
    previous_center_lng = to_float_or_none(target_row.get("center_lng"))
    previous_center_lat = to_float_or_none(target_row.get("center_lat"))
    aliases = normalize_alias_list(target_row.get("aliases") or [])

    resolved_center_lng: float | None = None
    resolved_center_lat: float | None = None
    resolved_anchor_source: str | None = None
    resolved_anchor_quality: float | None = None
    alias_to_append: str | None = None
    review_action_label: str
    review_state: str
    candidate_payload: dict[str, Any] | None = None

    if action == "confirm_candidate":
        if candidate_index is None:
            raise ValueError("候选确认必须传 candidate_index")
        candidate_suggestions = list((report_item or {}).get("candidate_suggestions") or [])
        if candidate_index < 0 or candidate_index >= len(candidate_suggestions):
            raise ValueError("candidate_index 超出候选范围")
        candidate_payload = candidate_suggestions[candidate_index]
        if candidate_index == 0:
            resolved_center_lng = to_float_or_none((report_item or {}).get("center_lng"))
            resolved_center_lat = to_float_or_none((report_item or {}).get("center_lat"))
        else:
            resolved_center_lng = to_float_or_none(candidate_payload.get("center_lng"))
            resolved_center_lat = to_float_or_none(candidate_payload.get("center_lat"))
        if resolved_center_lng is None or resolved_center_lat is None:
            raise ValueError("所选候选缺少可写回的坐标")
        resolved_anchor_source = str(
            candidate_payload.get("match_source")
            or candidate_payload.get("matchSource")
            or (report_item or {}).get("match_source")
            or "candidate_confirmed_gcj02"
        )
        resolved_anchor_quality = (
            to_float_or_none(candidate_payload.get("score"))
            or to_float_or_none((report_item or {}).get("anchor_quality"))
            or max(to_float_or_none(target_row.get("source_confidence")) or 0.0, 0.95)
        )
        candidate_name = str(candidate_payload.get("name") or "").strip()
        if candidate_name and candidate_name not in aliases:
            alias_to_append = candidate_name
        review_action_label = "confirm_candidate"
        review_state = "confirmed"
    elif action == "manual_override":
        resolved_center_lng = to_float_or_none(center_lng)
        resolved_center_lat = to_float_or_none(center_lat)
        if resolved_center_lng is None or resolved_center_lat is None:
            raise ValueError("手工覆盖必须传有效的 center_lng / center_lat")
        if not (-180 <= resolved_center_lng <= 180) or not (-90 <= resolved_center_lat <= 90):
            raise ValueError("手工覆盖坐标超出有效范围")
        resolved_anchor_source = (anchor_source_label or "manual_override_gcj02").strip() or "manual_override_gcj02"
        resolved_anchor_quality = 1.0
        alias_text = str(alias_hint or "").strip()
        if alias_text and alias_text not in aliases:
            alias_to_append = alias_text
        review_action_label = "manual_override"
        review_state = "manual_override"
    else:
        raise ValueError("Unsupported anchor confirmation action")

    if alias_to_append:
        aliases.append(alias_to_append)
    aliases = normalize_alias_list(aliases)
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    review_event = {
        "eventId": f"{run_id}::{community_id}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "referenceRunId": run_id,
        "communityId": community_id,
        "communityName": target_row.get("community_name"),
        "districtId": target_row.get("district_id"),
        "districtName": next(
            (item.get("district_name") for item in district_rows if item.get("district_id") == target_row.get("district_id")),
            target_row.get("district_id"),
        ),
        "action": review_action_label,
        "decisionState": review_state,
        "candidateIndex": candidate_index,
        "candidateName": candidate_payload.get("name") if candidate_payload else None,
        "candidateAddress": candidate_payload.get("address") if candidate_payload else None,
        "previousCenterLng": previous_center_lng,
        "previousCenterLat": previous_center_lat,
        "centerLng": resolved_center_lng,
        "centerLat": resolved_center_lat,
        "anchorSource": resolved_anchor_source,
        "anchorQuality": resolved_anchor_quality,
        "reviewNote": (review_note or "").strip() or None,
        "aliasAppended": alias_to_append,
        "reviewOwner": review_owner,
        "reviewedAt": reviewed_at,
    }

    target_row["aliases"] = aliases
    target_row["center_lng"] = resolved_center_lng
    target_row["center_lat"] = resolved_center_lat
    target_row["anchor_source"] = resolved_anchor_source
    target_row["anchor_quality"] = resolved_anchor_quality
    target_row["source_confidence"] = max(
        to_float_or_none(target_row.get("source_confidence")) or 0.0,
        resolved_anchor_quality or 0.0,
    )
    source_refs = normalize_alias_list(target_row.get("source_refs") or [])
    if candidate_payload and candidate_payload.get("query"):
        source_refs = normalize_alias_list([*source_refs, candidate_payload.get("query")])
    target_row["source_refs"] = source_refs

    for row in reference_catalog.get("communities", []):
        if str(row.get("community_id")) != community_id:
            continue
        row["aliases"] = aliases
        row["center_lng"] = resolved_center_lng
        row["center_lat"] = resolved_center_lat
        row["anchor_source"] = resolved_anchor_source
        row["anchor_quality"] = resolved_anchor_quality
        row["source_confidence"] = target_row.get("source_confidence")
        row["source_refs"] = source_refs
        break

    for row in reference_catalog.get("buildings", []):
        if str(row.get("community_id")) != community_id:
            continue
        row["community_aliases"] = normalize_alias_list([*(row.get("community_aliases") or []), *aliases])

    for row in community_csv_rows:
        if str(row.get("community_id")) != community_id:
            continue
        row["aliases"] = serialize_alias_list(aliases)
        row["center_lng"] = "" if resolved_center_lng is None else resolved_center_lng
        row["center_lat"] = "" if resolved_center_lat is None else resolved_center_lat
        row["anchor_source"] = resolved_anchor_source or ""
        row["anchor_quality"] = "" if resolved_anchor_quality is None else resolved_anchor_quality
        source_ref_value = row.get("source_refs") or row.get("source_ref")
        if source_ref_value is not None:
            row["source_refs"] = serialize_alias_list(source_refs)
        break

    review_history.append(review_event)
    review_history.sort(key=lambda item: item.get("reviewedAt") or "", reverse=True)

    anchor_report = rebuild_reference_anchor_report(community_rows, report_items)
    summary = rebuild_reference_summary(district_rows, community_rows, building_rows)
    manifest = deepcopy(detail["manifest"])
    manifest.setdefault("outputs", {})
    manifest["outputs"]["anchor_report"] = str(detail["outputPaths"]["anchorReportPath"])
    manifest["outputs"]["anchor_review_history"] = str(detail["outputPaths"]["anchorReviewHistoryPath"])
    manifest["outputs"]["community_dictionary_enriched"] = str(detail["outputPaths"]["communityCsvPath"])
    manifest["summary"] = summary

    write_json_file(detail["outputPaths"]["communityPath"], community_rows)
    write_json_file(detail["outputPaths"]["referenceCatalogPath"], reference_catalog)
    write_json_file(detail["outputPaths"]["anchorReportPath"], anchor_report)
    write_json_file(detail["outputPaths"]["anchorReviewHistoryPath"], review_history)
    if detail["outputPaths"].get("summaryPath"):
        write_json_file(detail["outputPaths"]["summaryPath"], summary)
    write_json_file(detail["manifestPath"], manifest)
    if community_csv_rows:
        fieldnames: list[str] = []
        for row in community_csv_rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        write_csv_rows(detail["outputPaths"]["communityCsvPath"], fieldnames, community_csv_rows)

    database_sync = {"status": "skipped", "message": "未配置 PostgreSQL，同步仅写回本地 reference 主档文件。"}
    try:
        from .persistence import postgres_runtime_status, sync_anchor_confirmation_to_postgres

        if postgres_runtime_status()["hasPostgresDsn"]:
            sync_summary = sync_anchor_confirmation_to_postgres(
                {
                    **review_event,
                    "communityAliases": aliases,
                    "communityRow": {
                        "community_id": community_id,
                        "community_name": target_row.get("community_name"),
                        "district_id": target_row.get("district_id"),
                        "district_name": review_event.get("districtName"),
                        "aliases": aliases,
                        "center_lng": resolved_center_lng,
                        "center_lat": resolved_center_lat,
                        "anchor_source": resolved_anchor_source,
                        "anchor_quality": resolved_anchor_quality,
                        "source_confidence": target_row.get("source_confidence"),
                    },
                }
            )
            database_sync = {
                "status": "synced",
                "message": "锚点确认结果已同步到 PostgreSQL。",
                "summary": sync_summary,
            }
    except Exception as exc:  # pragma: no cover - best effort sync
        database_sync = {
            "status": "error",
            "message": f"reference 主档已写回，但 PostgreSQL 同步失败: {exc}",
        }

    updated_community = get_community(community_id)
    return {
        "runId": run_id,
        "communityId": community_id,
        "action": review_action_label,
        "detail": reference_run_detail_full(run_id),
        "community": updated_community,
        "watchlist": anchor_watchlist_payload(limit=20),
        "databaseSync": database_sync,
        "latestAnchorReview": review_event,
    }


def place_labels_for(community_id: str | None, building_id: str | None = None) -> dict[str, str | None]:
    return place_labels_from_indices(reference_catalog_indices(), community_id, building_id)


def staged_import_artifacts(run_id: str | None = None) -> dict[str, Any] | None:
    run_summaries = list_import_runs()
    if not run_summaries:
        return None
    selected_run = next((item for item in run_summaries if item.get("runId") == run_id), None) if run_id else run_summaries[0]
    if not selected_run:
        return None
    manifest_path = import_manifest_path_for_run(selected_run["runId"])
    if manifest_path is None:
        return None
    manifest = read_json_file(manifest_path)
    if not isinstance(manifest, dict):
        return None
    outputs = manifest.get("outputs", {})
    sale_rows = read_json_file(resolve_artifact_path(outputs.get("normalized_sale"))) or []
    rent_rows = read_json_file(resolve_artifact_path(outputs.get("normalized_rent"))) or []
    queue_rows = read_json_file(resolve_artifact_path(outputs.get("address_resolution_queue"))) or []
    floor_pairs = read_json_file(resolve_artifact_path(outputs.get("floor_pairs"))) or []
    floor_evidence = read_json_file(resolve_artifact_path(outputs.get("floor_evidence"))) or []
    review_history = read_json_file(resolve_artifact_path(outputs.get("review_history")) or default_review_history_path(manifest_path)) or []
    return {
        "runId": selected_run["runId"],
        "providerId": selected_run.get("providerId"),
        "batchName": selected_run.get("batchName"),
        "createdAt": selected_run.get("createdAt"),
        "manifestPath": manifest_path,
        "manifest": manifest,
        "saleRows": sale_rows,
        "rentRows": rent_rows,
        "queueRows": queue_rows,
        "floorPairs": floor_pairs,
        "floorEvidence": floor_evidence,
        "reviewHistory": review_history,
    }


def staged_floor_history(building_id: str, floor_no: int) -> dict[str, Any]:
    history_rows: list[dict[str, Any]] = []
    for run_summary in sorted(list_import_runs(), key=lambda item: comparable_created_at_value(item.get("createdAt"))):
        artifacts = staged_import_artifacts(run_summary["runId"])
        if not artifacts:
            continue
        evidence = next(
            (
                item
                for item in artifacts["floorEvidence"]
                if item.get("building_id") == building_id and int(item.get("floor_no") or -1) == int(floor_no)
            ),
            None,
        )
        if not evidence:
            continue
        previous = history_rows[-1] if history_rows else None
        yield_pct = float(evidence.get("yield_pct") or 0)
        pair_count = int(evidence.get("pair_count") or 0)
        sale_median_wan = float(evidence.get("sale_median_wan") or 0)
        rent_median_monthly = float(evidence.get("rent_median_monthly") or 0)
        yield_delta = round(yield_pct - float(previous.get("yieldPct") or 0), 2) if previous else None
        pair_delta = pair_count - int(previous.get("pairCount") or 0) if previous else None
        sale_delta = round(sale_median_wan - float(previous.get("saleMedianWan") or 0), 2) if previous else None
        rent_delta = round(rent_median_monthly - float(previous.get("rentMedianMonthly") or 0), 2) if previous else None
        status, status_label = comparison_status_for_delta(yield_delta)
        history_rows.append(
            {
                "runId": artifacts["runId"],
                "batchName": artifacts["batchName"],
                "createdAt": artifacts["createdAt"],
                "pairCount": pair_count,
                "yieldPct": yield_pct,
                "saleMedianWan": sale_median_wan,
                "rentMedianMonthly": rent_median_monthly,
                "bestPairConfidence": float(evidence.get("best_pair_confidence") or 0),
                "yieldDeltaVsPrevious": yield_delta,
                "pairCountDeltaVsPrevious": pair_delta,
                "saleMedianDeltaWan": sale_delta,
                "rentMedianDeltaMonthly": rent_delta,
                "status": status if previous else "new",
                "statusLabel": status_label if previous else "首个快照",
                "isLatest": False,
            }
        )
    if not history_rows:
        return {"timeline": [], "summary": None}
    history_rows[-1]["isLatest"] = True
    first = history_rows[0]
    latest = history_rows[-1]
    return {
        "timeline": list(reversed(history_rows)),
        "summary": {
            "observedRuns": len(history_rows),
            "latestRunId": latest["runId"],
            "latestBatchName": latest["batchName"],
            "firstBatchName": first["batchName"],
            "yieldDeltaSinceFirst": round(latest["yieldPct"] - first["yieldPct"], 2) if len(history_rows) >= 2 else None,
            "avgYieldPct": round(sum(item["yieldPct"] for item in history_rows) / len(history_rows), 2),
            "totalPairCount": sum(item["pairCount"] for item in history_rows),
        },
    }


def staged_floor_snapshot_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run_summary in list_import_runs():
        artifacts = staged_import_artifacts(run_summary["runId"])
        if not artifacts:
            continue
        for item in artifacts["floorEvidence"]:
            rows.append(
                {
                    "building_id": item.get("building_id"),
                    "community_id": item.get("community_id"),
                    "floor_no": item.get("floor_no"),
                    "pair_count": item.get("pair_count"),
                    "sale_median_wan": item.get("sale_median_wan"),
                    "rent_median_monthly": item.get("rent_median_monthly"),
                    "yield_pct": item.get("yield_pct"),
                    "best_pair_confidence": item.get("best_pair_confidence"),
                    "run_id": artifacts["runId"],
                    "batch_name": artifacts["batchName"],
                    "created_at": artifacts["createdAt"],
                }
            )
    rows.sort(key=lambda item: (item.get("building_id") or "", int(item.get("floor_no") or 0), item.get("created_at") or ""))
    return rows


def district_style(district_id: str) -> dict[str, Any]:
    return DISTRICT_STYLE_INDEX.get(district_id, {})


def sample_status_for(
    *,
    sale_sample: int = 0,
    rent_sample: int = 0,
    sample_size: int = 0,
    min_dense_samples: int = 2,
) -> str:
    if sale_sample > 0 and rent_sample > 0 and sample_size >= min_dense_samples:
        return "active_metrics"
    if sale_sample > 0 or rent_sample > 0:
        return "sparse_sample"
    return "dictionary_only"


def sample_status_label(sample_status: str) -> str:
    return {
        "active_metrics": "有指标样本",
        "sparse_sample": "样本偏少",
        "dictionary_only": "仅主档挂图",
    }.get(sample_status, "状态待补")


def db_community_rows() -> list[dict[str, Any]]:
    return query_rows(
        """
        WITH latest_metric_date AS (
            SELECT MAX(snapshot_date) AS snapshot_date
            FROM metrics_community
        ),
        metric AS (
            SELECT mc.*
            FROM metrics_community mc
            JOIN latest_metric_date lmd ON lmd.snapshot_date = mc.snapshot_date
        ),
        sale AS (
            SELECT
                community_id,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY price_total_wan) AS sale_median_wan,
                COUNT(*) AS sale_sample,
                MAX(crawled_at) AS sale_freshness
            FROM listings_sale
            WHERE community_id IS NOT NULL AND status = 'active'
            GROUP BY community_id
        ),
        rent AS (
            SELECT
                community_id,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY monthly_rent) AS rent_median_monthly,
                COUNT(*) AS rent_sample,
                MAX(crawled_at) AS rent_freshness
            FROM listings_rent
            WHERE community_id IS NOT NULL AND status = 'active'
            GROUP BY community_id
        ),
        building_counts AS (
            SELECT community_id, COUNT(*) AS building_count
            FROM buildings
            GROUP BY community_id
        ),
        building_geom AS (
            SELECT
                b.community_id,
                AVG(ST_X(ST_Centroid(COALESCE(g.geom_wgs84, b.geom_wgs84)))) AS avg_lon,
                AVG(ST_Y(ST_Centroid(COALESCE(g.geom_wgs84, b.geom_wgs84)))) AS avg_lat
            FROM buildings b
            LEFT JOIN LATERAL (
                SELECT geom_wgs84
                FROM geo_assets g
                WHERE g.asset_type = 'building_footprint' AND g.building_id = b.building_id
                ORDER BY g.captured_at DESC NULLS LAST, g.asset_id DESC
                LIMIT 1
            ) g ON TRUE
            WHERE COALESCE(g.geom_wgs84, b.geom_wgs84) IS NOT NULL
            GROUP BY b.community_id
        )
        SELECT
            d.district_id,
            d.district_name,
            d.short_name,
            c.community_id,
            c.name AS community_name,
            COALESCE(ST_X(c.centroid_gcj02), ST_X(c.centroid_wgs84), bg.avg_lon) AS centroid_lon,
            COALESCE(ST_Y(c.centroid_gcj02), ST_Y(c.centroid_wgs84), bg.avg_lat) AS centroid_lat,
            c.anchor_source,
            c.anchor_quality,
            c.anchor_decision_state,
            c.latest_anchor_reviewed_at,
            COALESCE(m.sale_median_wan, s.sale_median_wan, 0) AS sale_median_wan,
            COALESCE(m.rent_median_monthly, r.rent_median_monthly, 0) AS rent_median_monthly,
            COALESCE(m.sale_sample_size, s.sale_sample, 0) AS sale_sample,
            COALESCE(m.rent_sample_size, r.rent_sample, 0) AS rent_sample,
            m.yield_pct,
            m.opportunity_score,
            m.snapshot_date AS metric_snapshot_date,
            COALESCE(bc.building_count, 0) AS building_count,
            COALESCE(
                (m.snapshot_date::timestamp AT TIME ZONE 'Asia/Shanghai'),
                GREATEST(COALESCE(s.sale_freshness, TIMESTAMPTZ 'epoch'), COALESCE(r.rent_freshness, TIMESTAMPTZ 'epoch'))
            ) AS data_freshness
        FROM communities c
        JOIN districts d ON d.district_id = c.district_id
        LEFT JOIN metric m ON m.community_id = c.community_id
        LEFT JOIN sale s ON s.community_id = c.community_id
        LEFT JOIN rent r ON r.community_id = c.community_id
        LEFT JOIN building_counts bc ON bc.community_id = c.community_id
        LEFT JOIN building_geom bg ON bg.community_id = c.community_id
        ORDER BY d.district_id, c.community_id
        """
    )


def db_latest_anchor_review_lookup() -> dict[str, dict[str, Any]]:
    if not database_mode_active():
        return {}
    rows = query_rows(
        """
        SELECT DISTINCT ON (community_id)
            community_id,
            action,
            decision_state,
            center_lng,
            center_lat,
            anchor_source,
            anchor_quality,
            review_note,
            alias_appended,
            review_owner,
            reviewed_at,
            payload_json
        FROM anchor_review_events
        WHERE community_id IS NOT NULL
        ORDER BY community_id, reviewed_at DESC, created_at DESC
        """
    )
    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        community_id = row.get("community_id")
        if not community_id:
            continue
        lookup[str(community_id)] = {
            "eventId": None,
            "communityId": str(community_id),
            "action": row.get("action"),
            "decisionState": row.get("decision_state"),
            "centerLng": row.get("center_lng"),
            "centerLat": row.get("center_lat"),
            "anchorSource": row.get("anchor_source"),
            "anchorQuality": row.get("anchor_quality"),
            "reviewNote": row.get("review_note"),
            "aliasAppended": row.get("alias_appended"),
            "reviewOwner": row.get("review_owner"),
            "reviewedAt": row.get("reviewed_at").isoformat() if hasattr(row.get("reviewed_at"), "isoformat") else row.get("reviewed_at"),
            "payload": row.get("payload_json"),
        }
    return lookup


def db_building_rows() -> list[dict[str, Any]]:
    return query_rows(
        """
        WITH latest_metric_date AS (
            SELECT MAX(snapshot_date) AS snapshot_date
            FROM metrics_building_floor
        ),
        metric AS (
            SELECT mbf.*
            FROM metrics_building_floor mbf
            JOIN latest_metric_date lmd ON lmd.snapshot_date = mbf.snapshot_date
        ),
        sale AS (
            SELECT
                building_id,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY price_total_wan) AS sale_median_wan,
                COUNT(*) AS sale_sample,
                MAX(crawled_at) AS sale_freshness
            FROM listings_sale
            WHERE building_id IS NOT NULL AND status = 'active'
            GROUP BY building_id
        ),
        rent AS (
            SELECT
                building_id,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY monthly_rent) AS rent_median_monthly,
                COUNT(*) AS rent_sample,
                MAX(crawled_at) AS rent_freshness
            FROM listings_rent
            WHERE building_id IS NOT NULL AND status = 'active'
            GROUP BY building_id
        ),
        sale_bucket AS (
            SELECT
                building_id,
                floor_bucket,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY price_total_wan) AS sale_median_wan,
                COUNT(*) AS sale_sample
            FROM listings_sale
            WHERE building_id IS NOT NULL AND status = 'active' AND floor_bucket IN ('low', 'mid', 'high')
            GROUP BY building_id, floor_bucket
        ),
        rent_bucket AS (
            SELECT
                building_id,
                floor_bucket,
                percentile_cont(0.5) WITHIN GROUP (ORDER BY monthly_rent) AS rent_median_monthly,
                COUNT(*) AS rent_sample
            FROM listings_rent
            WHERE building_id IS NOT NULL AND status = 'active' AND floor_bucket IN ('low', 'mid', 'high')
            GROUP BY building_id, floor_bucket
        ),
        metric_agg AS (
            SELECT
                building_id,
                MAX(snapshot_date) AS metric_snapshot_date,
                AVG(sale_median_wan) AS metric_sale_median_wan,
                AVG(rent_median_monthly) AS metric_rent_median_monthly,
                AVG(yield_pct) AS metric_yield_pct,
                AVG(opportunity_score) AS metric_opportunity_score,
                SUM(sample_size) AS metric_sample_size,
                MAX(CASE WHEN floor_bucket = 'low' THEN sale_median_wan END) AS metric_low_sale_median_wan,
                MAX(CASE WHEN floor_bucket = 'mid' THEN sale_median_wan END) AS metric_mid_sale_median_wan,
                MAX(CASE WHEN floor_bucket = 'high' THEN sale_median_wan END) AS metric_high_sale_median_wan,
                MAX(CASE WHEN floor_bucket = 'low' THEN rent_median_monthly END) AS metric_low_rent_median_monthly,
                MAX(CASE WHEN floor_bucket = 'mid' THEN rent_median_monthly END) AS metric_mid_rent_median_monthly,
                MAX(CASE WHEN floor_bucket = 'high' THEN rent_median_monthly END) AS metric_high_rent_median_monthly,
                MAX(CASE WHEN floor_bucket = 'low' THEN yield_pct END) AS metric_low_yield_pct,
                MAX(CASE WHEN floor_bucket = 'mid' THEN yield_pct END) AS metric_mid_yield_pct,
                MAX(CASE WHEN floor_bucket = 'high' THEN yield_pct END) AS metric_high_yield_pct
            FROM metric
            GROUP BY building_id
        )
        SELECT
            b.building_id,
            b.community_id,
            c.name AS community_name,
            c.district_id,
            d.district_name,
            d.short_name,
            b.building_no,
            b.total_floors,
            b.unit_count,
            ST_AsGeoJSON(COALESCE(
                (
                    SELECT g.geom_wgs84
                    FROM geo_assets g
                    WHERE g.asset_type = 'building_footprint' AND g.building_id = b.building_id
                    ORDER BY g.captured_at DESC NULLS LAST, g.asset_id DESC
                    LIMIT 1
                ),
                b.geom_wgs84
            )) AS building_geometry,
            COALESCE(ma.metric_sale_median_wan, s.sale_median_wan, 0) AS sale_median_wan,
            COALESCE(ma.metric_rent_median_monthly, r.rent_median_monthly, 0) AS rent_median_monthly,
            COALESCE(ma.metric_sample_size, GREATEST(COALESCE(s.sale_sample, 0), COALESCE(r.rent_sample, 0)), 0) AS metric_sample_size,
            COALESCE(s.sale_sample, 0) AS sale_sample,
            COALESCE(r.rent_sample, 0) AS rent_sample,
            ma.metric_yield_pct,
            ma.metric_opportunity_score,
            COALESCE(ma.metric_low_sale_median_wan, sb_low.sale_median_wan, s.sale_median_wan) AS low_sale_median_wan,
            COALESCE(ma.metric_mid_sale_median_wan, sb_mid.sale_median_wan, s.sale_median_wan) AS mid_sale_median_wan,
            COALESCE(ma.metric_high_sale_median_wan, sb_high.sale_median_wan, s.sale_median_wan) AS high_sale_median_wan,
            COALESCE(ma.metric_low_rent_median_monthly, rb_low.rent_median_monthly, r.rent_median_monthly) AS low_rent_median_monthly,
            COALESCE(ma.metric_mid_rent_median_monthly, rb_mid.rent_median_monthly, r.rent_median_monthly) AS mid_rent_median_monthly,
            COALESCE(ma.metric_high_rent_median_monthly, rb_high.rent_median_monthly, r.rent_median_monthly) AS high_rent_median_monthly,
            ma.metric_low_yield_pct,
            ma.metric_mid_yield_pct,
            ma.metric_high_yield_pct,
            COALESCE(
                (ma.metric_snapshot_date::timestamp AT TIME ZONE 'Asia/Shanghai'),
                GREATEST(COALESCE(s.sale_freshness, TIMESTAMPTZ 'epoch'), COALESCE(r.rent_freshness, TIMESTAMPTZ 'epoch'))
            ) AS data_freshness
        FROM buildings b
        JOIN communities c ON c.community_id = b.community_id
        JOIN districts d ON d.district_id = c.district_id
        LEFT JOIN metric_agg ma ON ma.building_id = b.building_id
        LEFT JOIN sale s ON s.building_id = b.building_id
        LEFT JOIN rent r ON r.building_id = b.building_id
        LEFT JOIN sale_bucket sb_low ON sb_low.building_id = b.building_id AND sb_low.floor_bucket = 'low'
        LEFT JOIN sale_bucket sb_mid ON sb_mid.building_id = b.building_id AND sb_mid.floor_bucket = 'mid'
        LEFT JOIN sale_bucket sb_high ON sb_high.building_id = b.building_id AND sb_high.floor_bucket = 'high'
        LEFT JOIN rent_bucket rb_low ON rb_low.building_id = b.building_id AND rb_low.floor_bucket = 'low'
        LEFT JOIN rent_bucket rb_mid ON rb_mid.building_id = b.building_id AND rb_mid.floor_bucket = 'mid'
        LEFT JOIN rent_bucket rb_high ON rb_high.building_id = b.building_id AND rb_high.floor_bucket = 'high'
        ORDER BY b.community_id, b.building_no
        """
    )


def db_floor_snapshot_rows() -> list[dict[str, Any]]:
    return query_rows(
        """
        SELECT
            fs.building_id,
            fs.community_id,
            fs.floor_no,
            fs.pair_count,
            fs.sale_median_wan,
            fs.rent_median_monthly,
            fs.yield_pct,
            fs.best_pair_confidence,
            ir.external_run_id AS run_id,
            ir.batch_name,
            ir.created_at
        FROM floor_evidence_snapshots fs
        JOIN ingestion_runs ir ON ir.run_id = fs.ingestion_run_id
        ORDER BY fs.building_id, fs.floor_no, ir.created_at
        """
    )



def building_id_for(community_id: str, index: int) -> str:
    return f"{community_id}-b{index + 1}"


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def enrich_community(community: dict[str, Any], district_item: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(community)
    buildings = []
    for index, building in enumerate(data.get("buildings", [])):
        building_copy = deepcopy(building)
        building_copy["id"] = building_copy.get("id") or building_id_for(data["id"], index)
        building_copy["sequenceNo"] = index + 1
        building_copy["communityId"] = data["id"]
        building_copy["communityName"] = data["name"]
        building_copy["districtId"] = district_item["id"]
        building_copy["districtName"] = district_item["name"]
        floor_yields = {
            "low": building_copy["low"],
            "mid": building_copy["mid"],
            "high": building_copy["high"],
        }
        building_copy["yieldAvg"] = round(sum(floor_yields.values()) / len(floor_yields), 2)
        building_copy["bestBucket"] = max(floor_yields, key=floor_yields.get)
        buildings.append(building_copy)

    focus_match = next((item for item in buildings if item["name"] == data.get("buildingFocus")), None)
    data["buildings"] = buildings
    data["districtName"] = district_item["name"]
    data["districtShort"] = district_item["short"]
    data["primaryBuildingId"] = data.get("primaryBuildingId") or (
        focus_match["id"] if focus_match else (buildings[0]["id"] if buildings else None)
    )
    return data


def interpolate_floor_yield(building: dict[str, Any], floor_no: int) -> float:
    total_floors = max(int(building.get("totalFloors", 1)), 1)
    if total_floors == 1:
        return round(building["mid"], 2)

    mid_floor = max(2, round(total_floors / 2))
    if floor_no <= mid_floor:
        ratio = (floor_no - 1) / max(1, mid_floor - 1)
        yield_pct = building["low"] + (building["mid"] - building["low"]) * ratio
    else:
        ratio = (floor_no - mid_floor) / max(1, total_floors - mid_floor)
        yield_pct = building["mid"] + (building["high"] - building["mid"]) * ratio

    return round(yield_pct, 2)


def floor_bucket_label(bucket: str) -> str:
    return {"low": "低楼层", "mid": "中楼层", "high": "高楼层"}[bucket]


def bucket_for_floor(total_floors: int, floor_no: int) -> str:
    low_top = max(1, round(total_floors * 0.33))
    high_start = max(low_top + 1, round(total_floors * 0.67))
    if floor_no <= low_top:
        return "low"
    if floor_no >= high_start:
        return "high"
    return "mid"


def build_score_breakdown(
    building: dict[str, Any],
    community: dict[str, Any],
    district_item: dict[str, Any],
    *,
    sample_size_estimate: int,
    avg_price_wan_estimate: float,
) -> list[dict[str, Any]]:
    raw_factors = [
        {
            "key": "district_spread",
            "label": "板块偏离",
            "weight": 0.32,
            "score": clamp(50 + (community["yield"] - district_item["yield"]) * 40, 0, 100),
            "summary": f"小区回报率相对所在行政区 {'领先' if community['yield'] >= district_item['yield'] else '落后'} "
            f"{abs(community['yield'] - district_item['yield']):.2f}%。",
        },
        {
            "key": "building_spread",
            "label": "楼栋偏离",
            "weight": 0.24,
            "score": clamp(50 + (building["yieldAvg"] - community["yield"]) * 55, 0, 100),
            "summary": f"楼栋均值相对小区 {'领先' if building['yieldAvg'] >= community['yield'] else '落后'} "
            f"{abs(building['yieldAvg'] - community['yield']):.2f}%。",
        },
        {
            "key": "sample_confidence",
            "label": "样本可信度",
            "weight": 0.18,
            "score": clamp(sample_size_estimate * 5.4, 0, 100),
            "summary": f"当前估算到 {sample_size_estimate} 套有效样本，可支撑楼栋层面的初步判断。",
        },
        {
            "key": "liquidity",
            "label": "流动性",
            "weight": 0.14,
            "score": clamp(78 - max(avg_price_wan_estimate - 900, 0) / 24 + community["sample"] * 0.45, 0, 100),
            "summary": f"总价 {avg_price_wan_estimate:.0f} 万，对比样本活跃度 {community['sample']} 套做了流动性折现。",
        },
        {
            "key": "data_quality",
            "label": "数据质量",
            "weight": 0.12,
            "score": clamp(60 + len(community["buildings"]) * 4 + max(building["totalFloors"] - 12, 0) * 1.1, 0, 100),
            "summary": "楼栋结构完整、楼层跨度足够，适合继续往逐层价差建模。",
        },
    ]

    raw_total = sum(item["score"] * item["weight"] for item in raw_factors) or 1
    scale = building["score"] / raw_total

    return [
        {
            **item,
            "score": round(item["score"], 1),
            "contribution": round(item["score"] * item["weight"] * scale, 1),
        }
        for item in raw_factors
    ]


def build_floor_curve(
    building: dict[str, Any],
    *,
    avg_price_wan_estimate: float,
) -> tuple[list[dict[str, Any]], int]:
    total_floors = max(int(building["totalFloors"]), 1)
    floor_curve = []

    for floor_no in range(1, total_floors + 1):
        bucket = bucket_for_floor(total_floors, floor_no)
        bucket_label = floor_bucket_label(bucket)
        yield_pct = interpolate_floor_yield(building, floor_no)
        floor_ratio = 0 if total_floors == 1 else (floor_no - 1) / (total_floors - 1)
        floor_price_premium = -0.02 + floor_ratio * 0.08
        floor_price_premium_pct = floor_price_premium * 100
        shape_bonus = 10 - abs(floor_ratio - 0.68) * 18
        est_price_wan = round(avg_price_wan_estimate * (1 + floor_price_premium), 1)
        est_monthly_rent = round(est_price_wan * 10000 * (yield_pct / 100) / 12)
        yield_spread_vs_building = round(yield_pct - building["yieldAvg"], 2)
        opportunity_score = round(
            clamp(
                building["score"]
                - 10
                + yield_spread_vs_building * 40
                + shape_bonus
                - max(floor_price_premium_pct, 0) * 0.35
                + max(-floor_price_premium_pct, 0) * 0.12,
                0,
                99,
            )
        )
        arbitrage_tag = (
            "重点关注"
            if opportunity_score >= 90
            else "可跟进"
            if opportunity_score >= 82
            else "观察"
            if opportunity_score >= 74
            else "对照"
        )
        floor_curve.append(
            {
                "floorNo": floor_no,
                "bucket": bucket,
                "bucketLabel": bucket_label,
                "yieldPct": yield_pct,
                "yieldSpreadVsBuilding": yield_spread_vs_building,
                "estPriceWan": est_price_wan,
                "estMonthlyRent": est_monthly_rent,
                "pricePremiumPct": round(floor_price_premium_pct, 2),
                "opportunityScore": opportunity_score,
                "arbitrageTag": arbitrage_tag,
            }
        )

    focus_floor = max(floor_curve, key=lambda item: (item["opportunityScore"], item["yieldPct"], -item["estPriceWan"]))
    return floor_curve, focus_floor["floorNo"]


def source_name_by_id(source_id: str) -> str:
    if source_id == "authorized-manual":
        return "授权手工样本"
    for source in DATA_SOURCES:
        if source["id"] == source_id:
            return source["name"]
    return source_id


def building_name_for(community_id: str, building_id: str) -> str | None:
    if staged_mode_active():
        return place_labels_for(community_id, building_id).get("buildingName")
    community = get_community(community_id)
    if not community:
        return None
    for building in community["buildings"]:
        if building["id"] == building_id:
            return building["name"]
    return None


def normalized_path_from_queue_item(
    *,
    community_id: str | None,
    building_id: str | None,
    parsed_unit: str | None,
    parsed_floor_no: int | None,
    labels: dict[str, str | None] | None = None,
) -> str:
    if staged_mode_active():
        labels = labels or place_labels_for(community_id, building_id)
        district_name = labels.get("districtName") or "待识别行政区"
        community_name = labels.get("communityName") or "待识别小区"
        building_name = labels.get("buildingName") or "待识别楼栋"
    else:
        community = get_community(community_id) if community_id else None
        building = get_building(building_id) if building_id else None
        district_name = (building or community or {}).get("districtName", "待识别行政区")
        community_name = (community or {}).get("name", "待识别小区")
        building_name = (building or {}).get("name", "待识别楼栋")
    unit_label = parsed_unit or "待识别单元"
    floor_label = f"{parsed_floor_no}层" if parsed_floor_no else "待识别楼层"
    return f"{district_name} / {community_name} / {building_name} / {unit_label} / {floor_label}"


def normalized_queue_item_from_import(
    run_summary: dict[str, Any],
    item: dict[str, Any],
    *,
    reference_indexes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    community_id = item.get("parsed_community_id")
    building_id = item.get("parsed_building_id")
    labels = (
        place_labels_from_indices(reference_indexes, community_id, building_id)
        if reference_indexes is not None
        else place_labels_for(community_id, building_id)
    )
    building_name = labels.get("buildingName") or "待识别楼栋"
    return {
        "queueId": f"{run_summary['runId']}::{item.get('source')}::{item.get('source_listing_id')}",
        "communityId": community_id,
        "buildingId": building_id,
        "buildingNo": building_name,
        "floorNo": item.get("parsed_floor_no"),
        "sourceId": item.get("source"),
        "rawAddress": item.get("raw_text"),
        "normalizedPath": normalized_path_from_queue_item(
            community_id=community_id,
            building_id=building_id,
            parsed_unit=item.get("parsed_unit"),
            parsed_floor_no=item.get("parsed_floor_no"),
            labels=labels,
        ),
        "status": item.get("parse_status", "matching"),
        "confidence": item.get("confidence_score", 0.0) or 0.0,
        "lastActionAt": (run_summary.get("createdAt") or "").replace("T", " ")[:16],
        "reviewHint": item.get("resolution_notes") or "等待人工复核。",
        "runId": run_summary["runId"],
        "batchName": run_summary["batchName"],
        "reviewOwner": item.get("review_owner"),
        "reviewedAt": item.get("reviewed_at"),
    }


def normalized_queue_item_from_mock(item: dict[str, Any]) -> dict[str, Any]:
    community = get_community(item["communityId"])
    building = next(
        (candidate for candidate in (community or {}).get("buildings", []) if candidate["name"] == item["buildingNo"]),
        None,
    )
    return {
        "queueId": item["queueId"],
        "communityId": item["communityId"],
        "buildingId": building["id"] if building else None,
        "buildingNo": item["buildingNo"],
        "floorNo": item["floorNo"],
        "sourceId": item["sourceId"],
        "rawAddress": item["rawAddress"],
        "normalizedPath": item["normalizedPath"],
        "status": item["status"],
        "confidence": item["confidence"],
        "lastActionAt": item["lastActionAt"],
        "reviewHint": item["reviewHint"],
        "runId": None,
        "batchName": None,
        "reviewOwner": item.get("reviewOwner"),
        "reviewedAt": item.get("reviewedAt"),
    }


def build_layout_label(sale_row: dict[str, Any] | None, rent_row: dict[str, Any] | None) -> str:
    source_row = sale_row or rent_row or {}
    bedrooms = source_row.get("bedrooms")
    living_rooms = source_row.get("living_rooms")
    bathrooms = source_row.get("bathrooms")
    if bedrooms is None or living_rooms is None or bathrooms is None:
        return "待补户型"
    return f"{bedrooms}室{living_rooms}厅{bathrooms}卫"


def normalize_import_pair_for_ui(
    run_summary: dict[str, Any],
    pair: dict[str, Any],
    sale_row: dict[str, Any] | None,
    rent_row: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    resolution_confidence = round(
        min((sale_row or {}).get("resolution_confidence", 1.0), (rent_row or {}).get("resolution_confidence", 1.0)),
        2,
    )
    unit_no = (sale_row or {}).get("parsed_unit") or (rent_row or {}).get("parsed_unit") or f"样本{index + 1}"
    orientation = (sale_row or {}).get("orientation") or (rent_row or {}).get("orientation") or "待补朝向"
    area_sqm = (sale_row or {}).get("area_sqm") or (rent_row or {}).get("area_sqm")
    match_confidence = pair.get("match_confidence", 0.0)
    review_state = (
        "已归一"
        if resolution_confidence >= 0.9 and match_confidence >= 0.85
        else "待复核"
        if resolution_confidence >= 0.8
        else "需人工确认"
    )
    return {
        "pairId": pair["pair_id"],
        "unitNo": unit_no,
        "layout": build_layout_label(sale_row, rent_row),
        "orientation": orientation,
        "areaSqm": area_sqm,
        "saleSourceName": source_name_by_id(pair["sale_source"]),
        "rentSourceName": source_name_by_id(pair["rent_source"]),
        "salePriceWan": pair.get("sale_price_wan"),
        "monthlyRent": pair.get("monthly_rent"),
        "yieldPct": pair.get("annual_yield_pct"),
        "resolutionConfidence": resolution_confidence,
        "dedupConfidence": match_confidence,
        "reviewState": review_state,
        "normalizedAddress": pair.get("normalized_address")
        or (sale_row or {}).get("normalized_address")
        or (rent_row or {}).get("normalized_address"),
        "rawSaleAddress": (sale_row or {}).get("raw_address"),
        "rawRentAddress": (rent_row or {}).get("raw_address"),
        "updatedAt": (run_summary.get("createdAt") or "").replace("T", " ")[:16],
    }


def derive_review_history_from_queue(run_summary: dict[str, Any], queue_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    derived_events = []
    for item in queue_rows:
        if not item.get("reviewed_at"):
            continue
        derived_events.append(
            {
                "eventId": f"{run_summary['runId']}::{item.get('source')}::{item.get('source_listing_id')}::{str(item.get('reviewed_at')).replace(':', '').replace('-', '')}",
                "queueId": f"{run_summary['runId']}::{item.get('source')}::{item.get('source_listing_id')}",
                "runId": run_summary["runId"],
                "source": item.get("source"),
                "sourceListingId": item.get("source_listing_id"),
                "communityId": item.get("parsed_community_id"),
                "buildingId": item.get("parsed_building_id"),
                "floorNo": item.get("parsed_floor_no"),
                "previousStatus": "unknown",
                "newStatus": item.get("parse_status"),
                "reviewOwner": item.get("review_owner"),
                "reviewedAt": item.get("reviewed_at"),
                "resolutionNotes": item.get("resolution_notes"),
            }
        )
    derived_events.sort(key=lambda entry: entry.get("reviewedAt") or "", reverse=True)
    return derived_events


def enrich_review_event_for_ui(run_summary: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    community_id = event.get("communityId") or event.get("community_id")
    building_id = event.get("buildingId") or event.get("building_id")
    floor_no = event.get("floorNo") or event.get("floor_no")
    if staged_mode_active():
        labels = place_labels_for(community_id, building_id)
        community_name = labels.get("communityName") or "待识别小区"
        building_name = labels.get("buildingName") or "待识别楼栋"
    else:
        community = get_community(community_id) if community_id else None
        building = get_building(building_id) if building_id else None
        community_name = (community or {}).get("name", "待识别小区")
        building_name = (building or {}).get("name") or building_name_for(community_id, building_id) or "待识别楼栋"
    return {
        "eventId": event.get("eventId") or event.get("event_id"),
        "queueId": event.get("queueId"),
        "runId": event.get("runId") or run_summary["runId"],
        "sourceId": event.get("source") or event.get("sourceId"),
        "sourceListingId": event.get("sourceListingId") or event.get("source_listing_id"),
        "communityId": community_id,
        "communityName": community_name,
        "buildingId": building_id,
        "buildingName": building_name,
        "floorNo": floor_no,
        "previousStatus": event.get("previousStatus") or event.get("previous_status") or "unknown",
        "newStatus": event.get("newStatus") or event.get("new_status") or "resolved",
        "reviewOwner": event.get("reviewOwner") or event.get("review_owner") or "atlas-ui",
        "reviewedAt": event.get("reviewedAt") or event.get("reviewed_at"),
        "resolutionNotes": event.get("resolutionNotes") or event.get("resolution_notes") or "已由工作台人工复核确认。",
    }


def import_manifest_path_for_run(run_id: str) -> Path | None:
    for manifest_path in import_manifest_paths():
        manifest = read_json_file(manifest_path)
        if isinstance(manifest, dict) and manifest.get("run_id") == run_id:
            return manifest_path
    return None


def import_run_queue_rows(run_summary: dict[str, Any]) -> list[dict[str, Any]]:
    manifest_path = import_manifest_path_for_run(str(run_summary.get("runId") or ""))
    if manifest_path:
        manifest = read_json_file(manifest_path)
        if isinstance(manifest, dict):
            outputs = manifest.get("outputs", {})
            queue_path = resolve_artifact_path(outputs.get("address_resolution_queue"))
            queue_rows = read_json_file(queue_path)
            if isinstance(queue_rows, list):
                return queue_rows
    detail = db_import_run_detail_full(str(run_summary.get("runId") or ""))
    if detail and isinstance(detail.get("queueRows"), list):
        return detail["queueRows"]
    return []


def db_import_run_detail_full(run_id: str) -> dict[str, Any] | None:
    snapshot = postgres_data_snapshot()
    if not snapshot.get("databaseReadable"):
        return None

    run_row = query_row(
        """
        SELECT
            run_id,
            external_run_id AS run_id_external,
            provider_id,
            batch_name,
            output_manifest_path,
            summary_json,
            created_at
        FROM ingestion_runs
        WHERE external_run_id = %s AND business_scope = 'sale_rent'
        ORDER BY created_at DESC, run_id DESC
        LIMIT 1
        """,
        (run_id,),
    )
    if not run_row:
        return None

    run_pk = int(run_row["run_id"])
    created_at = run_row.get("created_at")
    manifest_path = existing_output_manifest_path(run_row.get("output_manifest_path"))
    manifest_payload = read_json_file(manifest_path) if manifest_path else None
    summary = db_summary_json(run_row.get("summary_json"))
    run_summary = {
        "runId": run_row.get("run_id_external"),
        "providerId": run_row.get("provider_id"),
        "batchName": run_row.get("batch_name") or run_row.get("run_id_external"),
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        "outputDir": str(manifest_path.parent) if manifest_path else None,
        "resolvedRate": summary.get("resolved_rate", 0.0),
        "resolvedCount": summary.get("resolved_count", 0),
        "reviewCount": summary.get("review_count", 0),
        "matchingCount": summary.get("matching_count", 0),
        "pairCount": summary.get("floor_pair_count", 0),
        "evidenceCount": summary.get("floor_evidence_count", 0),
        "storageMode": "database+file" if manifest_path else "database",
    }

    queue_rows = query_rows(
        """
        SELECT
            source,
            source_listing_id,
            raw_text,
            parsed_district_id,
            parsed_community_id,
            parsed_building_id,
            parsed_unit,
            parsed_floor_no,
            parse_status,
            confidence_score,
            resolution_notes,
            review_owner,
            reviewed_at
        FROM address_resolution_queue
        WHERE ingestion_run_id = %s
        ORDER BY updated_at DESC, task_id DESC
        """,
        (run_pk,),
    )
    review_history_raw = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None)
        or {
            "eventId": row.get("event_id"),
            "queueId": row.get("queue_id"),
            "runId": run_summary["runId"],
            "source": row.get("source"),
            "sourceListingId": row.get("source_listing_id"),
            "communityId": row.get("parsed_community_id"),
            "buildingId": row.get("parsed_building_id"),
            "floorNo": row.get("floor_no"),
            "previousStatus": row.get("previous_status"),
            "newStatus": row.get("new_status"),
            "reviewOwner": row.get("review_owner"),
            "reviewedAt": row.get("reviewed_at").isoformat() if hasattr(row.get("reviewed_at"), "isoformat") else row.get("reviewed_at"),
            "resolutionNotes": row.get("resolution_notes"),
        }
        for row in query_rows(
            """
            SELECT
                event_id,
                queue_id,
                source,
                source_listing_id,
                parsed_community_id,
                parsed_building_id,
                floor_no,
                previous_status,
                new_status,
                review_owner,
                reviewed_at,
                resolution_notes,
                payload_json
            FROM address_review_events
            WHERE ingestion_run_id = %s
            ORDER BY reviewed_at DESC, created_at DESC
            """,
            (run_pk,),
        )
    ]
    floor_pairs = [
        {
            "pair_id": row.get("pair_id"),
            "community_id": row.get("community_id"),
            "building_id": row.get("building_id"),
            "floor_no": row.get("floor_no"),
            "sale_source": row.get("sale_source"),
            "sale_source_listing_id": row.get("sale_source_listing_id"),
            "rent_source": row.get("rent_source"),
            "rent_source_listing_id": row.get("rent_source_listing_id"),
            "sale_price_wan": row.get("sale_price_wan"),
            "monthly_rent": row.get("monthly_rent"),
            "annual_yield_pct": row.get("annual_yield_pct"),
            "area_gap_sqm": row.get("area_gap_sqm"),
            "floor_gap": row.get("floor_gap"),
            "match_confidence": row.get("match_confidence"),
            "normalized_address": row.get("normalized_address"),
        }
        for row in query_rows(
            """
            SELECT
                pair_id,
                community_id,
                building_id,
                floor_no,
                sale_source,
                sale_source_listing_id,
                rent_source,
                rent_source_listing_id,
                sale_price_wan,
                monthly_rent,
                annual_yield_pct,
                area_gap_sqm,
                floor_gap,
                match_confidence,
                normalized_address
            FROM floor_evidence_pairs
            WHERE ingestion_run_id = %s
            ORDER BY building_id, floor_no, match_confidence DESC, pair_id
            """,
            (run_pk,),
        )
    ]
    floor_evidence = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None)
        or {
            "community_id": row.get("community_id"),
            "building_id": row.get("building_id"),
            "floor_no": row.get("floor_no"),
            "pair_count": row.get("pair_count"),
            "sale_median_wan": row.get("sale_median_wan"),
            "rent_median_monthly": row.get("rent_median_monthly"),
            "yield_pct": row.get("yield_pct"),
            "best_pair_confidence": row.get("best_pair_confidence"),
        }
        for row in query_rows(
            """
            SELECT
                community_id,
                building_id,
                floor_no,
                pair_count,
                sale_median_wan,
                rent_median_monthly,
                yield_pct,
                best_pair_confidence,
                payload_json
            FROM floor_evidence_snapshots
            WHERE ingestion_run_id = %s
            ORDER BY building_id, floor_no
            """,
            (run_pk,),
        )
    ]
    sale_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None)
        or {}
        for row in query_rows("SELECT raw_payload_json AS payload_json FROM listings_sale WHERE ingestion_run_id = %s", (run_pk,))
    ]
    rent_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None)
        or {}
        for row in query_rows("SELECT raw_payload_json AS payload_json FROM listings_rent WHERE ingestion_run_id = %s", (run_pk,))
    ]
    sale_index = {
        (item.get("source"), item.get("source_listing_id")): item
        for item in sale_rows
        if item.get("source") and item.get("source_listing_id")
    }
    rent_index = {
        (item.get("source"), item.get("source_listing_id")): item
        for item in rent_rows
        if item.get("source") and item.get("source_listing_id")
    }
    review_queue = [
        normalized_queue_item_from_import(run_summary, item)
        for item in queue_rows
        if item.get("parse_status") != "resolved"
    ]
    top_evidence = []
    for evidence_item in floor_evidence[:6]:
        labels = place_labels_for(evidence_item.get("community_id"), evidence_item.get("building_id"))
        top_evidence.append(
            {
                "buildingId": evidence_item.get("building_id"),
                "buildingName": labels.get("buildingName") or "待识别楼栋",
                "communityId": evidence_item.get("community_id"),
                "communityName": labels.get("communityName") or "待识别小区",
                "floorNo": evidence_item.get("floor_no"),
                "yieldPct": evidence_item.get("yield_pct"),
                "pairCount": evidence_item.get("pair_count"),
                "bestPairConfidence": evidence_item.get("best_pair_confidence"),
            }
        )
    review_history = [enrich_review_event_for_ui(run_summary, item) for item in review_history_raw]
    review_history.sort(key=lambda entry: entry.get("reviewedAt") or "", reverse=True)

    return {
        **run_summary,
        "manifestPath": manifest_path,
        "manifest": manifest_payload or {"summary": summary, "attention": {}},
        "outputPaths": {
            "queuePath": None,
            "floorPairsPath": None,
            "floorEvidencePath": None,
            "salePath": None,
            "rentPath": None,
            "summaryPath": None,
            "reviewHistoryPath": None,
        },
        "attention": (manifest_payload or {}).get("attention", {}),
        "reviewQueue": review_queue,
        "reviewHistory": review_history,
        "topEvidence": top_evidence,
        "queueRows": queue_rows,
        "floorPairs": floor_pairs,
        "floorEvidence": floor_evidence,
        "saleIndex": sale_index,
        "rentIndex": rent_index,
    }


@lru_cache(maxsize=128)
def _import_run_detail_full_cached(run_id: str) -> dict[str, Any] | None:
    manifest_path = import_manifest_path_for_run(run_id)
    if manifest_path:
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict):
            manifest = None
        if manifest and manifest.get("run_id") == run_id:
            run_summary = import_run_summary_from_manifest(manifest, manifest_path)
            outputs = manifest.get("outputs", {})
            output_paths = {
                "queuePath": resolve_artifact_path(outputs.get("address_resolution_queue")),
                "floorPairsPath": resolve_artifact_path(outputs.get("floor_pairs")),
                "floorEvidencePath": resolve_artifact_path(outputs.get("floor_evidence")),
                "salePath": resolve_artifact_path(outputs.get("normalized_sale")),
                "rentPath": resolve_artifact_path(outputs.get("normalized_rent")),
                "summaryPath": resolve_artifact_path(outputs.get("summary")),
                "reviewHistoryPath": resolve_artifact_path(outputs.get("review_history")) or default_review_history_path(manifest_path),
            }
            queue_rows = read_json_file(output_paths["queuePath"]) or []
            floor_pairs = read_json_file(output_paths["floorPairsPath"]) or []
            floor_evidence = read_json_file(output_paths["floorEvidencePath"]) or []
            sale_rows = read_json_file(output_paths["salePath"]) or []
            rent_rows = read_json_file(output_paths["rentPath"]) or []
            review_history_raw = read_json_file(output_paths["reviewHistoryPath"]) or derive_review_history_from_queue(run_summary, queue_rows)
            sale_index = {(item.get("source"), item.get("source_listing_id")): item for item in sale_rows}
            rent_index = {(item.get("source"), item.get("source_listing_id")): item for item in rent_rows}

            review_queue = [
                normalized_queue_item_from_import(run_summary, item)
                for item in queue_rows
                if item.get("parse_status") != "resolved"
            ]
            top_evidence = []
            for evidence_item in floor_evidence[:6]:
                labels = place_labels_for(evidence_item.get("community_id"), evidence_item.get("building_id"))
                top_evidence.append(
                    {
                        "buildingId": evidence_item.get("building_id"),
                        "buildingName": labels.get("buildingName") or "待识别楼栋",
                        "communityId": evidence_item.get("community_id"),
                        "communityName": labels.get("communityName") or "待识别小区",
                        "floorNo": evidence_item.get("floor_no"),
                        "yieldPct": evidence_item.get("yield_pct"),
                        "pairCount": evidence_item.get("pair_count"),
                        "bestPairConfidence": evidence_item.get("best_pair_confidence"),
                    }
                )

            review_history = [
                enrich_review_event_for_ui(run_summary, item)
                for item in review_history_raw
            ]
            review_history.sort(key=lambda entry: entry.get("reviewedAt") or "", reverse=True)

            return {
                **run_summary,
                "manifestPath": manifest_path,
                "manifest": manifest,
                "outputPaths": output_paths,
                "attention": manifest.get("attention", {}),
                "reviewQueue": review_queue,
                "reviewHistory": review_history,
                "topEvidence": top_evidence,
                "queueRows": queue_rows,
                "floorPairs": floor_pairs,
                "floorEvidence": floor_evidence,
                "saleIndex": sale_index,
                "rentIndex": rent_index,
            }
    return db_import_run_detail_full(run_id)


def import_run_detail_full(run_id: str) -> dict[str, Any] | None:
    detail = _import_run_detail_full_cached(run_id)
    return deepcopy(detail) if detail else None


def import_run_detail(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    detail = import_run_detail_full(run_id)
    if not detail:
        return None
    comparison = import_run_comparison(run_id, baseline_run_id=baseline_run_id)
    return {
        "runId": detail["runId"],
        "providerId": detail["providerId"],
        "batchName": detail["batchName"],
        "createdAt": detail["createdAt"],
        "outputDir": detail["outputDir"],
        "resolvedRate": detail["resolvedRate"],
        "resolvedCount": detail["resolvedCount"],
        "reviewCount": detail["reviewCount"],
        "matchingCount": detail["matchingCount"],
        "pairCount": detail["pairCount"],
        "evidenceCount": detail["evidenceCount"],
        "attention": detail["attention"],
        "reviewQueue": detail["reviewQueue"],
        "reviewHistoryCount": len(detail["reviewHistory"]),
        "recentReviews": detail["reviewHistory"][:6],
        "topEvidence": detail["topEvidence"],
        "comparison": comparison,
    }


def baseline_run_for(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    runs = list_import_runs()
    current_run = next((item for item in runs if item["runId"] == run_id), None)
    if not current_run:
        return None

    if baseline_run_id:
        explicit_baseline = next((item for item in runs if item["runId"] == baseline_run_id), None)
        if not explicit_baseline:
            return None
        if not created_at_is_before(explicit_baseline.get("createdAt"), current_run.get("createdAt")):
            return None
        return explicit_baseline

    same_provider_candidates = [
        item
        for item in runs
        if item["runId"] != run_id
        and item.get("providerId") == current_run.get("providerId")
        and created_at_is_before(item.get("createdAt"), current_run.get("createdAt"))
    ]
    if same_provider_candidates:
        return same_provider_candidates[0]

    for item in runs:
        if item["runId"] == run_id:
            continue
        if created_at_is_before(item.get("createdAt"), current_run.get("createdAt")):
            return item
    return None


def comparison_status_for_delta(yield_delta: float | None) -> tuple[str, str]:
    if yield_delta is None:
        return "new", "新增楼层"
    if yield_delta >= 0.08:
        return "improved", "回报抬升"
    if yield_delta <= -0.08:
        return "deteriorated", "回报回落"
    return "stable", "基本持平"


def import_run_comparison(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    current_detail = import_run_detail_full(run_id)
    if not current_detail:
        return None

    baseline_run = baseline_run_for(run_id, baseline_run_id=baseline_run_id)
    if not baseline_run:
        return None

    baseline_detail = import_run_detail_full(baseline_run["runId"])
    if not baseline_detail:
        return None

    baseline_evidence_map = {
        (item.get("community_id"), item.get("building_id"), item.get("floor_no")): item
        for item in baseline_detail["floorEvidence"]
    }
    current_evidence_map = {
        (item.get("community_id"), item.get("building_id"), item.get("floor_no")): item
        for item in current_detail["floorEvidence"]
    }

    improved_count = 0
    deteriorated_count = 0
    stable_count = 0
    new_floor_count = 0
    removed_floor_count = 0
    overlap_count = 0
    yield_deltas: list[float] = []
    floor_changes = []

    for key, current_item in current_evidence_map.items():
        community_id, building_id, floor_no = key
        baseline_item = baseline_evidence_map.get(key)
        current_yield = current_item.get("yield_pct")
        previous_yield = baseline_item.get("yield_pct") if baseline_item else None
        yield_delta = round(current_yield - previous_yield, 2) if previous_yield is not None and current_yield is not None else None
        pair_delta = current_item.get("pair_count", 0) - (baseline_item.get("pair_count", 0) if baseline_item else 0)
        sale_delta = (
            round(current_item.get("sale_median_wan", 0) - baseline_item.get("sale_median_wan", 0), 2)
            if baseline_item and current_item.get("sale_median_wan") is not None and baseline_item.get("sale_median_wan") is not None
            else None
        )
        rent_delta = (
            round(current_item.get("rent_median_monthly", 0) - baseline_item.get("rent_median_monthly", 0), 2)
            if baseline_item and current_item.get("rent_median_monthly") is not None and baseline_item.get("rent_median_monthly") is not None
            else None
        )
        status, status_label = comparison_status_for_delta(yield_delta)
        if baseline_item:
            overlap_count += 1
            if yield_delta is not None:
                yield_deltas.append(yield_delta)
            if status == "improved":
                improved_count += 1
            elif status == "deteriorated":
                deteriorated_count += 1
            else:
                stable_count += 1
        else:
            new_floor_count += 1

        community = get_community(community_id) if community_id else None
        building = get_building(building_id) if building_id else None
        floor_changes.append(
            {
                "communityId": community_id,
                "communityName": (community or {}).get("name", "待识别小区"),
                "buildingId": building_id,
                "buildingName": (building or {}).get("name", "待识别楼栋"),
                "floorNo": floor_no,
                "currentYieldPct": current_yield,
                "previousYieldPct": previous_yield,
                "yieldDelta": yield_delta,
                "currentPairCount": current_item.get("pair_count", 0),
                "previousPairCount": baseline_item.get("pair_count", 0) if baseline_item else 0,
                "pairCountDelta": pair_delta,
                "currentSaleMedianWan": current_item.get("sale_median_wan"),
                "previousSaleMedianWan": baseline_item.get("sale_median_wan") if baseline_item else None,
                "saleMedianDeltaWan": sale_delta,
                "currentRentMedianMonthly": current_item.get("rent_median_monthly"),
                "previousRentMedianMonthly": baseline_item.get("rent_median_monthly") if baseline_item else None,
                "rentMedianDeltaMonthly": rent_delta,
                "status": status,
                "statusLabel": status_label,
                "bestPairConfidence": current_item.get("best_pair_confidence"),
            }
        )

    for key in baseline_evidence_map:
        if key not in current_evidence_map:
            removed_floor_count += 1

    floor_changes.sort(
        key=lambda item: (
            0 if item["status"] == "new" else 1,
            -(abs(item["yieldDelta"]) if item["yieldDelta"] is not None else 0),
            -item.get("currentYieldPct", 0),
        )
    )

    resolved_rate_delta = round((current_detail["resolvedRate"] - baseline_detail["resolvedRate"]) * 100, 1)
    return {
        "baselineRunId": baseline_detail["runId"],
        "baselineBatchName": baseline_detail["batchName"],
        "baselineCreatedAt": baseline_detail["createdAt"],
        "currentBatchName": current_detail["batchName"],
        "currentCreatedAt": current_detail["createdAt"],
        "resolvedRateDeltaPct": resolved_rate_delta,
        "reviewCountDelta": current_detail["reviewCount"] - baseline_detail["reviewCount"],
        "pairCountDelta": current_detail["pairCount"] - baseline_detail["pairCount"],
        "evidenceCountDelta": current_detail["evidenceCount"] - baseline_detail["evidenceCount"],
        "newFloorCount": new_floor_count,
        "removedFloorCount": removed_floor_count,
        "improvedFloorCount": improved_count,
        "deterioratedFloorCount": deteriorated_count,
        "stableFloorCount": stable_count,
        "overlapFloorCount": overlap_count,
        "avgYieldDeltaPct": round(sum(yield_deltas) / len(yield_deltas), 2) if yield_deltas else None,
        "topFloorChanges": floor_changes[:8],
    }


def import_floor_evidence_for(building_id: str, floor_no: int) -> dict[str, Any] | None:
    for run_summary in list_import_runs():
        detail = import_run_detail_full(run_summary["runId"])
        if not detail:
            continue
        evidence = next(
            (
                item
                for item in detail["floorEvidence"]
                if item.get("building_id") == building_id and item.get("floor_no") == floor_no
            ),
            None,
        )
        if not evidence:
            continue

        queue_items = [
            normalized_queue_item_from_import(detail, item)
            for item in detail["queueRows"]
            if item.get("parsed_building_id") == building_id and item.get("parsed_floor_no") == floor_no
        ]
        sample_pairs = []
        source_mix: dict[str, int] = {}
        for index, pair in enumerate(evidence.get("pairs", [])):
            sale_row = detail["saleIndex"].get((pair.get("sale_source"), pair.get("sale_source_listing_id")))
            rent_row = detail["rentIndex"].get((pair.get("rent_source"), pair.get("rent_source_listing_id")))
            normalized_pair = normalize_import_pair_for_ui(detail, pair, sale_row, rent_row, index)
            sample_pairs.append(normalized_pair)
            for source_name in (normalized_pair["saleSourceName"], normalized_pair["rentSourceName"]):
                source_mix[source_name] = source_mix.get(source_name, 0) + 1

        return {
            "runSummary": {
                "runId": detail["runId"],
                "batchName": detail["batchName"],
                "providerId": detail["providerId"],
                "createdAt": detail["createdAt"],
            },
            "evidence": evidence,
            "queueItems": queue_items,
            "samplePairs": sample_pairs,
            "sourceMix": [{"name": name, "count": count} for name, count in sorted(source_mix.items(), key=lambda item: item[1], reverse=True)],
        }
    return None


@lru_cache(maxsize=512)
def _import_floor_history_for_cached(building_id: str, floor_no: int) -> dict[str, Any]:
    history_rows: list[dict[str, Any]] = []

    for run_summary in sorted(_list_import_runs_cached(), key=lambda item: comparable_created_at_value(item.get("createdAt"))):
        detail = _import_run_detail_full_cached(run_summary["runId"])
        if not detail:
            continue

        evidence = next(
            (
                item
                for item in detail["floorEvidence"]
                if item.get("building_id") == building_id and item.get("floor_no") == floor_no
            ),
            None,
        )
        if not evidence:
            continue

        previous = history_rows[-1] if history_rows else None
        yield_pct = evidence.get("yield_pct")
        pair_count = evidence.get("pair_count", 0)
        sale_median_wan = evidence.get("sale_median_wan")
        rent_median_monthly = evidence.get("rent_median_monthly")

        if previous is None:
            status = "new"
            status_label = "首个快照"
            yield_delta = None
            pair_delta = None
            sale_delta = None
            rent_delta = None
        else:
            yield_delta = round(yield_pct - previous["yieldPct"], 2) if yield_pct is not None and previous.get("yieldPct") is not None else None
            pair_delta = pair_count - previous.get("pairCount", 0)
            sale_delta = (
                round(sale_median_wan - previous["saleMedianWan"], 2)
                if sale_median_wan is not None and previous.get("saleMedianWan") is not None
                else None
            )
            rent_delta = (
                round(rent_median_monthly - previous["rentMedianMonthly"], 2)
                if rent_median_monthly is not None and previous.get("rentMedianMonthly") is not None
                else None
            )
            status, status_label = comparison_status_for_delta(yield_delta)

        history_rows.append(
            {
                "runId": detail["runId"],
                "batchName": detail["batchName"],
                "createdAt": detail["createdAt"],
                "yieldPct": yield_pct,
                "pairCount": pair_count,
                "saleMedianWan": sale_median_wan,
                "rentMedianMonthly": rent_median_monthly,
                "bestPairConfidence": evidence.get("best_pair_confidence"),
                "yieldDeltaVsPrevious": yield_delta,
                "pairCountDeltaVsPrevious": pair_delta,
                "saleMedianDeltaWan": sale_delta,
                "rentMedianDeltaMonthly": rent_delta,
                "status": status,
                "statusLabel": status_label,
                "isLatest": False,
            }
        )

    if not history_rows:
        return {"timeline": [], "summary": None}

    history_rows[-1]["isLatest"] = True
    latest = history_rows[-1]
    first = history_rows[0]
    yield_values = [item["yieldPct"] for item in history_rows if item.get("yieldPct") is not None]
    summary = {
        "observedRuns": len(history_rows),
        "latestRunId": latest["runId"],
        "latestBatchName": latest["batchName"],
        "firstBatchName": first["batchName"],
        "yieldDeltaSinceFirst": (
            round(latest["yieldPct"] - first["yieldPct"], 2)
            if latest.get("yieldPct") is not None and first.get("yieldPct") is not None
            else None
        ),
        "avgYieldPct": round(sum(yield_values) / len(yield_values), 2) if yield_values else None,
        "totalPairCount": sum(item.get("pairCount", 0) for item in history_rows),
    }
    return {
        "timeline": list(reversed(history_rows)),
        "summary": summary,
    }


def import_floor_history_for(building_id: str, floor_no: int) -> dict[str, Any]:
    return deepcopy(_import_floor_history_for_cached(building_id, floor_no))


def floor_watchlist(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    run_id: str | None = None,
    baseline_run_id: str | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if database_mode_active():
        rows = db_floor_snapshot_rows()
        history_by_floor: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for row in rows:
            key = (str(row.get("building_id")), int(row.get("floor_no") or 0))
            history_by_floor.setdefault(key, []).append(row)
        watchlist = []
        for (building_id, floor_no), history_rows in history_by_floor.items():
            building = get_building(building_id)
            community = get_community((building or {}).get("communityId")) if building else None
            if not building or not community:
                continue
            if not community_visible(
                community,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            ):
                continue
            relevant_rows = history_rows
            if run_id:
                relevant_rows = [row for row in history_rows if row.get("run_id") == run_id or row.get("batch_name") == run_id]
            if not relevant_rows:
                continue
            relevant_rows.sort(key=lambda row: row.get("created_at") or datetime.min)
            latest_row = relevant_rows[-1]
            baseline_row = None
            if baseline_run_id:
                baseline_row = next(
                    (
                        row
                        for row in relevant_rows
                        if row.get("run_id") == baseline_run_id or row.get("batch_name") == baseline_run_id
                    ),
                    None,
                )
            if baseline_row is None and len(relevant_rows) >= 2:
                baseline_row = relevant_rows[0]
            summary = db_floor_history_summary_from_snapshot_rows(history_rows) or {}
            latest_yield = float(latest_row.get("yield_pct") or 0)
            latest_pair_count = int(latest_row.get("pair_count") or 0)
            baseline_yield = float(baseline_row.get("yield_pct") or 0) if baseline_row else None
            baseline_pair_count = int(baseline_row.get("pair_count") or 0) if baseline_row else 0
            window_yield_delta = round(latest_yield - baseline_yield, 2) if baseline_row else None
            window_pair_delta = latest_pair_count - baseline_pair_count if baseline_row else None
            status, status_label = comparison_status_for_delta(window_yield_delta)
            if baseline_row is None and summary.get("observedRuns", 0) <= 1:
                status, status_label = "new", "首批样本"
            persistence_score = round(
                clamp(
                    latest_yield * 24
                    + max(window_yield_delta or summary.get("yieldDeltaSinceFirst") or 0, 0) * 150
                    + (summary.get("observedRuns") or 1) * 7
                    + (summary.get("totalPairCount") or latest_pair_count) * 2.5
                    + latest_pair_count * 4,
                    0,
                    99,
                )
            )
            watchlist.append(
                {
                    "communityId": community["id"],
                    "communityName": community["name"],
                    "districtId": community["districtId"],
                    "districtName": community["districtName"],
                    "buildingId": building_id,
                    "buildingName": building["name"],
                    "floorNo": floor_no,
                    "latestYieldPct": latest_yield,
                    "yieldDeltaSinceFirst": summary.get("yieldDeltaSinceFirst"),
                    "windowYieldDeltaPct": window_yield_delta,
                    "latestPairCount": latest_pair_count,
                    "windowPairCountDelta": window_pair_delta,
                    "observedRuns": summary.get("observedRuns") or 1,
                    "totalPairCount": summary.get("totalPairCount") or latest_pair_count,
                    "latestBatchName": latest_row.get("batch_name"),
                    "latestCreatedAt": latest_row.get("created_at").isoformat() if latest_row.get("created_at") else None,
                    "baselineBatchName": baseline_row.get("batch_name") if baseline_row else None,
                    "baselineCreatedAt": baseline_row.get("created_at").isoformat() if baseline_row and baseline_row.get("created_at") else None,
                    "latestStatus": status,
                    "latestStatusLabel": status_label,
                    "persistenceScore": persistence_score,
                    "trendLabel": "持续走强" if (summary.get("yieldDeltaSinceFirst") or 0) >= 0.08 else "稳定高收益" if latest_yield >= community["yield"] else "继续观察",
                }
            )
        watchlist.sort(
            key=lambda item: (
                item["persistenceScore"],
                item["latestYieldPct"],
                item.get("windowYieldDeltaPct") if item.get("windowYieldDeltaPct") is not None else -999,
                item["observedRuns"],
                item["totalPairCount"],
            ),
            reverse=True,
        )
        return watchlist[:limit]
    if run_id:
        current_detail = import_run_detail_full(run_id)
        if not current_detail:
            return []

        baseline_run = baseline_run_for(run_id, baseline_run_id=baseline_run_id)
        baseline_detail = import_run_detail_full(baseline_run["runId"]) if baseline_run else None
        baseline_map = {
            (item.get("community_id"), item.get("building_id"), item.get("floor_no")): item
            for item in (baseline_detail["floorEvidence"] if baseline_detail else [])
        }
        watchlist = []

        for evidence in current_detail["floorEvidence"]:
            community_id = evidence.get("community_id")
            building_id = evidence.get("building_id")
            floor_no = evidence.get("floor_no")
            building = get_building(building_id) if building_id else None
            community = get_community(community_id) if community_id else None
            if not building or not community:
                continue
            if not community_visible(
                community,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            ):
                continue

            history_payload = import_floor_history_for(building_id, floor_no)
            summary = history_payload["summary"] or {}
            baseline_evidence = baseline_map.get((community_id, building_id, floor_no))
            current_yield = evidence.get("yield_pct") or 0.0
            current_pair_count = evidence.get("pair_count", 0)
            baseline_yield = baseline_evidence.get("yield_pct") if baseline_evidence else None
            baseline_pair_count = baseline_evidence.get("pair_count", 0) if baseline_evidence else 0
            yield_delta = round(current_yield - baseline_yield, 2) if baseline_yield is not None else None
            pair_delta = current_pair_count - baseline_pair_count
            status, status_label = comparison_status_for_delta(yield_delta)
            if baseline_detail and baseline_evidence is None:
                status, status_label = "new", "基线新增"

            observed_runs = summary.get("observedRuns") or 1
            total_pair_count = summary.get("totalPairCount") or current_pair_count
            persistence_score = round(
                clamp(
                    current_yield * 24
                    + max(yield_delta or 0, 0) * 165
                    + observed_runs * 6
                    + total_pair_count * 2.4
                    + current_pair_count * 4.5
                    + (7 if status in {"improved", "new"} else 0)
                    - (6 if status == "deteriorated" else 0),
                    0,
                    99,
                )
            )
            trend_label = (
                "相对基线上行"
                if status == "improved"
                else "基线新增"
                if status == "new"
                else "相对基线持平"
                if status == "stable"
                else "相对基线回落"
            )

            watchlist.append(
                {
                    "communityId": community["id"],
                    "communityName": community["name"],
                    "districtId": community["districtId"],
                    "districtName": community["districtName"],
                    "buildingId": building_id,
                    "buildingName": building["name"],
                    "floorNo": floor_no,
                    "latestYieldPct": current_yield,
                    "yieldDeltaSinceFirst": summary.get("yieldDeltaSinceFirst"),
                    "windowYieldDeltaPct": yield_delta,
                    "latestPairCount": current_pair_count,
                    "windowPairCountDelta": pair_delta if baseline_detail else None,
                    "observedRuns": observed_runs,
                    "totalPairCount": total_pair_count,
                    "latestBatchName": current_detail["batchName"],
                    "latestCreatedAt": current_detail["createdAt"],
                    "baselineBatchName": baseline_detail["batchName"] if baseline_detail else None,
                    "baselineCreatedAt": baseline_detail["createdAt"] if baseline_detail else None,
                    "latestStatus": status,
                    "latestStatusLabel": status_label,
                    "persistenceScore": persistence_score,
                    "trendLabel": trend_label,
                }
            )

        watchlist.sort(
            key=lambda item: (
                item["persistenceScore"],
                item["latestYieldPct"],
                item["windowYieldDeltaPct"] if item["windowYieldDeltaPct"] is not None else -999,
                item["observedRuns"],
                item["totalPairCount"],
            ),
            reverse=True,
        )
        return watchlist[:limit]

    floor_keys: set[tuple[str, int]] = set()
    for run_summary in list_import_runs():
        detail = import_run_detail_full(run_summary["runId"])
        if not detail:
            continue
        for item in detail["floorEvidence"]:
            building_id = item.get("building_id")
            floor_no = item.get("floor_no")
            if building_id and floor_no is not None:
                floor_keys.add((building_id, floor_no))

    watchlist = []
    for building_id, floor_no in floor_keys:
        building = get_building(building_id)
        community = get_community((building or {}).get("communityId")) if building else None
        if not building or not community:
            continue
        if not community_visible(
            community,
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ):
            continue

        history_payload = import_floor_history_for(building_id, floor_no)
        if not history_payload["timeline"] or not history_payload["summary"]:
            continue

        latest = history_payload["timeline"][0]
        summary = history_payload["summary"]
        latest_yield = latest.get("yieldPct") or 0.0
        yield_delta_since_first = summary.get("yieldDeltaSinceFirst") or 0.0
        observed_runs = summary.get("observedRuns") or 0
        total_pair_count = summary.get("totalPairCount") or 0
        latest_pair_count = latest.get("pairCount") or 0
        persistence_score = round(
            clamp(
                latest_yield * 24
                + max(yield_delta_since_first, 0) * 150
                + observed_runs * 7
                + total_pair_count * 2.5
                + latest_pair_count * 4
                + (8 if observed_runs >= 2 and latest_yield >= community.get("yield", 0) else 0),
                0,
                99,
            )
        )
        trend_label = (
            "持续走强"
            if observed_runs >= 2 and yield_delta_since_first >= 0.08
            else "新增样本"
            if observed_runs == 1
            else "稳定高收益"
            if latest_yield >= max(community.get("yield", 0), min_yield)
            else "继续观察"
        )

        watchlist.append(
            {
                "communityId": community["id"],
                "communityName": community["name"],
                "districtId": community["districtId"],
                "districtName": community["districtName"],
                "buildingId": building_id,
                "buildingName": building["name"],
                "floorNo": floor_no,
                "latestYieldPct": latest_yield,
                "yieldDeltaSinceFirst": yield_delta_since_first if observed_runs >= 2 else None,
                "latestPairCount": latest_pair_count,
                "observedRuns": observed_runs,
                "totalPairCount": total_pair_count,
                "latestBatchName": latest.get("batchName"),
                "latestCreatedAt": latest.get("createdAt"),
                "latestStatus": latest.get("status"),
                "latestStatusLabel": latest.get("statusLabel"),
                "persistenceScore": persistence_score,
                "trendLabel": trend_label,
            }
        )

    watchlist.sort(
        key=lambda item: (
            item["persistenceScore"],
            item["latestYieldPct"],
            item["observedRuns"],
            item["totalPairCount"],
        ),
        reverse=True,
    )
    return watchlist[:limit]


def parse_queue_id(queue_id: str) -> tuple[str, str] | None:
    parts = queue_id.split("::")
    if len(parts) < 3:
        return None
    return parts[1], parts[2]


def rebuild_import_run_summary(
    detail: dict[str, Any],
    *,
    queue_rows: list[dict[str, Any]],
    sale_rows: list[dict[str, Any]],
    rent_rows: list[dict[str, Any]],
    floor_pairs: list[dict[str, Any]],
    floor_evidence: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    resolved_rows = [item for item in queue_rows if item.get("parse_status") == "resolved"]
    summary = {
        "sale_input_count": len(sale_rows),
        "rent_input_count": len(rent_rows),
        "resolved_count": len(resolved_rows),
        "review_count": sum(1 for item in queue_rows if item.get("parse_status") == "needs_review"),
        "matching_count": sum(1 for item in queue_rows if item.get("parse_status") == "matching"),
        "resolved_rate": round(len(resolved_rows) / max(len(queue_rows), 1), 4),
        "resolved_community_count": len({item.get("parsed_community_id") for item in queue_rows if item.get("parsed_community_id")}),
        "resolved_building_count": len({item.get("parsed_building_id") for item in queue_rows if item.get("parsed_building_id")}),
        "floor_pair_count": len(floor_pairs),
        "floor_evidence_count": len(floor_evidence),
    }
    attention = {
        "unresolved_examples": [
            {
                "source": item.get("source"),
                "source_listing_id": item.get("source_listing_id"),
                "parse_status": item.get("parse_status"),
                "raw_text": item.get("raw_text"),
                "resolution_notes": item.get("resolution_notes"),
            }
            for item in queue_rows
            if item.get("parse_status") != "resolved"
        ][:8],
        "low_confidence_pairs": [
            {
                "pair_id": item.get("pair_id"),
                "match_confidence": item.get("match_confidence"),
                "normalized_address": item.get("normalized_address"),
            }
            for item in floor_pairs
            if (item.get("match_confidence") or 0) < 0.72
        ][:8],
    }
    return summary, attention


def update_import_queue_review(
    run_id: str,
    queue_id: str,
    *,
    parse_status: str = "resolved",
    resolution_notes: str | None = None,
    review_owner: str = "atlas-ui",
) -> dict[str, Any] | None:
    if parse_status not in {"resolved", "needs_review", "matching"}:
        raise ValueError("Unsupported parse status")

    detail = import_run_detail_full(run_id)
    if not detail:
        return None

    queue_key = parse_queue_id(queue_id)
    if not queue_key:
        return None

    source, source_listing_id = queue_key
    queue_rows = deepcopy(detail["queueRows"])
    sale_rows = deepcopy(list(detail["saleIndex"].values()))
    rent_rows = deepcopy(list(detail["rentIndex"].values()))
    floor_pairs = deepcopy(detail["floorPairs"])
    floor_evidence = deepcopy(detail["floorEvidence"])
    review_history = deepcopy(detail["reviewHistory"])
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")

    target_queue = next(
        (
            item
            for item in queue_rows
            if item.get("source") == source and item.get("source_listing_id") == source_listing_id
        ),
        None,
    )
    if not target_queue:
        return None

    review_note = resolution_notes or target_queue.get("resolution_notes") or "已由工作台人工复核确认。"
    previous_status = target_queue.get("parse_status", "unknown")
    target_queue["parse_status"] = parse_status
    target_queue["resolution_notes"] = review_note
    target_queue["review_owner"] = review_owner
    target_queue["reviewed_at"] = reviewed_at
    if parse_status == "resolved":
        target_queue["confidence_score"] = round(max(target_queue.get("confidence_score", 0.0), 0.92), 2)

    for row in sale_rows + rent_rows:
        if row.get("source") != source or row.get("source_listing_id") != source_listing_id:
            continue
        row["parse_status"] = parse_status
        row["resolution_notes"] = review_note
        row["review_owner"] = review_owner
        row["reviewed_at"] = reviewed_at
        if parse_status == "resolved":
            row["resolution_confidence"] = round(max(row.get("resolution_confidence", 0.0), 0.92), 2)

    summary, attention = rebuild_import_run_summary(
        detail,
        queue_rows=queue_rows,
        sale_rows=sale_rows,
        rent_rows=rent_rows,
        floor_pairs=floor_pairs,
        floor_evidence=floor_evidence,
    )
    output_paths = detail["outputPaths"]
    manifest = deepcopy(detail["manifest"])
    manifest.setdefault("outputs", {})
    manifest["outputs"]["review_history"] = str(output_paths.get("reviewHistoryPath") or default_review_history_path(detail["manifestPath"]))
    manifest["summary"] = summary
    manifest["attention"] = attention

    review_event = enrich_review_event_for_ui(
        detail,
        {
            "eventId": f"{run_id}::{source}::{source_listing_id}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "queueId": queue_id,
            "runId": run_id,
            "source": source,
            "sourceListingId": source_listing_id,
            "communityId": target_queue.get("parsed_community_id"),
            "buildingId": target_queue.get("parsed_building_id"),
            "floorNo": target_queue.get("parsed_floor_no"),
            "previousStatus": previous_status,
            "newStatus": parse_status,
            "reviewOwner": review_owner,
            "reviewedAt": reviewed_at,
            "resolutionNotes": review_note,
        },
    )
    review_history.insert(0, review_event)

    if output_paths.get("queuePath"):
        write_json_file(output_paths["queuePath"], queue_rows)
    if output_paths.get("salePath"):
        write_json_file(output_paths["salePath"], sale_rows)
    if output_paths.get("rentPath"):
        write_json_file(output_paths["rentPath"], rent_rows)
    if output_paths.get("summaryPath"):
        write_json_file(output_paths["summaryPath"], summary)
    if output_paths.get("reviewHistoryPath"):
        write_json_file(output_paths["reviewHistoryPath"], review_history)
    write_json_file(detail["manifestPath"], manifest)

    database_sync = {"status": "skipped", "message": "未配置 PostgreSQL，同步仅写回本地批次文件。"}
    try:
        from .persistence import postgres_runtime_status, persist_import_run_to_postgres

        if postgres_runtime_status()["hasPostgresDsn"]:
            persist_summary = persist_import_run_to_postgres(run_id)
            database_sync = {
                "status": "synced",
                "message": "已同步到 PostgreSQL。",
                "summary": persist_summary,
            }
    except Exception as exc:  # pragma: no cover - best effort sync
        database_sync = {
            "status": "error",
            "message": f"本地批次已更新，但 PostgreSQL 同步失败: {exc}",
        }

    updated_detail = import_run_detail(run_id)
    return {
        "runId": run_id,
        "queueId": queue_id,
        "status": parse_status,
        "reviewOwner": review_owner,
        "reviewedAt": reviewed_at,
        "detail": updated_detail,
        "databaseSync": database_sync,
    }


def build_import_resolution_trace(
    building: dict[str, Any],
    floor_item: dict[str, Any],
    run_summary: dict[str, Any],
    queue_items: list[dict[str, Any]],
    pair_count: int,
) -> list[dict[str, Any]]:
    queue_status = queue_items[0]["status"] if queue_items else "review"
    review_detail = queue_items[0]["reviewHint"] if queue_items else "当前批次没有单独挂起的地址项，但配对结果已落到逐层证据。"
    return [
        {
            "step": "授权导入",
            "status": "done",
            "detail": f"批次 {run_summary['batchName']} 已把 {pair_count} 组出售 / 出租样本落到 {building['name']} {floor_item['floorNo']} 层。",
        },
        {
            "step": "地址标准化",
            "status": "done" if queue_status == "resolved" else "review",
            "detail": f"按 district → resblock → building → unit → floor 完成归一，当前批次时间 {run_summary['createdAt']}.",
        },
        {
            "step": "样本配对",
            "status": "done",
            "detail": "已按小区、楼栋、面积差、楼层差和标准化置信度完成出售 / 出租样本对齐。",
        },
        {
            "step": "人工复核闸门",
            "status": "done" if queue_status == "resolved" else "review",
            "detail": review_detail,
        },
    ]


def all_address_queue_items() -> list[dict[str, Any]]:
    combined = [normalized_queue_item_from_mock(item) for item in ADDRESS_QUEUE] if demo_mode_active() else []
    reference_indexes = reference_catalog_indices() if staged_mode_active() else None
    for run_summary in list_import_runs():
        queue_rows = import_run_queue_rows(run_summary)
        combined.extend(
            normalized_queue_item_from_import(run_summary, item, reference_indexes=reference_indexes)
            for item in queue_rows
        )
    combined.sort(key=lambda item: (item["lastActionAt"], item["confidence"]), reverse=True)
    return combined


def queue_items_for(community_id: str, building_name: str, floor_no: int) -> list[dict[str, Any]]:
    def queue_sort_key(item: dict[str, Any]) -> tuple[int, float]:
        floor_gap = abs(item["floorNo"] - floor_no)
        return (floor_gap, -item["confidence"])

    return sorted(
        [
            deepcopy(item)
            for item in all_address_queue_items()
            if item["communityId"] == community_id
            and item["buildingNo"] == building_name
            and item["floorNo"] is not None
            and abs(item["floorNo"] - floor_no) <= 8
        ],
        key=queue_sort_key,
    )[:3]


def build_floor_sample_pairs(building: dict[str, Any], floor_item: dict[str, Any]) -> list[dict[str, Any]]:
    sample_count = max(3, min(5, round(building["sampleSizeEstimate"] / 2)))
    layouts = ["2室1厅1卫", "2室2厅1卫", "3室2厅2卫", "3室1厅2卫", "4室2厅2卫"]
    orientations = ["南", "南北", "东南", "西南", "东"]
    source_cycle = [source["id"] for source in DATA_SOURCES]
    sample_pairs = []

    for index in range(sample_count):
        sale_source_id = source_cycle[index % len(source_cycle)]
        rent_source_id = source_cycle[(index + 1) % len(source_cycle)]
        unit_no = f"{floor_item['floorNo']:02d}{index + 1:02d}"
        area_sqm = round(78 + building["sequenceNo"] * 6.4 + index * 5.8 + (floor_item["floorNo"] % 3) * 3.6, 1)
        sale_price_wan = round(floor_item["estPriceWan"] * (0.94 + index * 0.028), 1)
        monthly_rent = round(floor_item["estMonthlyRent"] * (0.93 + index * 0.036))
        yield_pct = round(monthly_rent * 12 / (sale_price_wan * 10000) * 100, 2)
        resolution_confidence = round(
            clamp(0.95 - index * 0.045 + floor_item["yieldSpreadVsBuilding"] * 0.02, 0.68, 0.99),
            2,
        )
        dedup_confidence = round(clamp(0.91 - index * 0.04 + (0.02 if index == 0 else 0), 0.58, 0.98), 2)
        review_state = (
            "已归一"
            if resolution_confidence >= 0.9
            else "待复核"
            if resolution_confidence >= 0.8
            else "需人工确认"
        )

        sample_pairs.append(
            {
                "pairId": f"{building['id']}-f{floor_item['floorNo']}-{index + 1}",
                "unitNo": unit_no,
                "layout": layouts[(building["sequenceNo"] + index) % len(layouts)],
                "orientation": orientations[(floor_item["floorNo"] + index) % len(orientations)],
                "areaSqm": area_sqm,
                "saleSourceName": source_name_by_id(sale_source_id),
                "rentSourceName": source_name_by_id(rent_source_id),
                "salePriceWan": sale_price_wan,
                "monthlyRent": monthly_rent,
                "yieldPct": yield_pct,
                "resolutionConfidence": resolution_confidence,
                "dedupConfidence": dedup_confidence,
                "reviewState": review_state,
                "normalizedAddress": (
                    f"{building['districtName']} / {building['communityName']} / {building['name']} / "
                    f"{index + 1}单元 / {floor_item['floorNo']}层 / {unit_no}"
                ),
                "rawSaleAddress": f"{building['communityName']}{building['name']}{floor_item['floorNo']}层{unit_no}",
                "rawRentAddress": f"{building['districtName']}{building['communityName']}{building['name']}{floor_item['floorNo']}F-{unit_no}",
                "updatedAt": f"2026-04-11 {8 + index:02d}:3{index}",
            }
        )

    return sample_pairs


def build_resolution_trace(
    building: dict[str, Any],
    floor_item: dict[str, Any],
    queue_items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    queue_status = queue_items[0]["status"] if queue_items else "matching"
    gate_detail = (
        queue_items[0]["reviewHint"]
        if queue_items
        else f"{building['name']} {floor_item['floorNo']} 层当前没有现成地址队列记录，按规则生成了待匹配占位。"
    )
    return [
        {
            "step": "原始抓取",
            "status": "done",
            "detail": f"出售与出租样本已在 {building['communityName']} / {building['name']} / {floor_item['floorNo']} 层收敛到同一候选层。",
        },
        {
            "step": "小区别名归一",
            "status": "done",
            "detail": f"已和物业小区字典对齐到 {building['communityName']}。",
        },
        {
            "step": "楼栋 / 单元解析",
            "status": "done" if queue_status in {"resolved", "matching"} else "review",
            "detail": f"楼栋号 {building['name']} 已识别，单元与门牌通过规则和历史别名表做二次补齐。",
        },
        {
            "step": "空间挂载",
            "status": "done",
            "detail": "已挂到 AOI / 楼栋 footprint，可用于地图定位和 Google Earth 导出。",
        },
        {
            "step": "人工复核闸门",
            "status": "done" if queue_status == "resolved" else "review",
            "detail": gate_detail,
        },
    ]



def db_geo_asset_run_detail_full(run_id: str) -> dict[str, Any] | None:
    snapshot = postgres_data_snapshot()
    if not snapshot.get("databaseReadable"):
        return None

    run_row = query_row(
        """
        SELECT
            run_id,
            external_run_id AS run_id_external,
            provider_id,
            batch_name,
            output_manifest_path,
            summary_json,
            created_at
        FROM ingestion_runs
        WHERE external_run_id = %s AND business_scope = 'geo_assets'
        ORDER BY created_at DESC, run_id DESC
        LIMIT 1
        """,
        (run_id,),
    )
    if not run_row:
        return None

    run_pk = int(run_row["run_id"])
    created_at = run_row.get("created_at")
    manifest_path = existing_output_manifest_path(run_row.get("output_manifest_path"))
    manifest_payload = read_json_file(manifest_path) if manifest_path else None
    summary = db_summary_json(run_row.get("summary_json"))
    run_summary = {
        "runId": run_row.get("run_id_external"),
        "providerId": run_row.get("provider_id"),
        "batchName": run_row.get("batch_name") or run_row.get("run_id_external"),
        "assetType": "building_footprint",
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        "outputDir": str(manifest_path.parent) if manifest_path else None,
        "featureCount": summary.get("feature_count", 0),
        "resolvedBuildingCount": summary.get("resolved_building_count", 0),
        "unresolvedFeatureCount": summary.get("unresolved_feature_count", 0),
        "communityCount": summary.get("community_count", 0),
        "coveragePct": summary.get("coverage_pct", 0.0),
        "taskCount": summary.get("coverage_task_count", 0),
        "openTaskCount": summary.get("open_task_count", 0),
        "reviewTaskCount": summary.get("review_task_count", 0),
        "captureTaskCount": summary.get("capture_task_count", 0),
        "storageMode": "database+file" if manifest_path else "database",
    }

    features = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None)
        or {
            "type": "Feature",
            "properties": {
                "district_id": row.get("district_id"),
                "district_name": row.get("district_name"),
                "community_id": row.get("community_id"),
                "community_name": row.get("community_name"),
                "building_id": row.get("building_id"),
                "building_name": row.get("building_name"),
                "source_ref": row.get("source_ref"),
                "captured_at": row.get("captured_at").isoformat() if hasattr(row.get("captured_at"), "isoformat") else row.get("captured_at"),
            },
            "geometry": json.loads(row["geometry_json"]) if row.get("geometry_json") else None,
        }
        for row in query_rows(
            """
            SELECT
                ga.community_id,
                ga.building_id,
                ga.source_ref,
                ga.captured_at,
                ga.payload_json,
                c.district_id,
                d.district_name,
                c.name AS community_name,
                b.building_no AS building_name,
                ST_AsGeoJSON(ga.geom_wgs84) AS geometry_json
            FROM geo_assets ga
            LEFT JOIN communities c ON c.community_id = ga.community_id
            LEFT JOIN buildings b ON b.building_id = ga.building_id
            LEFT JOIN districts d ON d.district_id = c.district_id
            WHERE ga.ingestion_run_id = %s AND ga.asset_type = 'building_footprint'
            ORDER BY ga.captured_at DESC NULLS LAST, ga.asset_id DESC
            """,
            (run_pk,),
        )
    ]
    coverage_task_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None) or row
        for row in query_rows(
            """
            SELECT
                task_id,
                task_scope,
                status,
                priority,
                provider_id,
                district_id,
                community_id,
                building_id,
                source_ref,
                community_name,
                building_name,
                resolution_notes,
                review_owner,
                reviewed_at,
                updated_at,
                payload_json
            FROM geo_asset_capture_tasks
            WHERE ingestion_run_id = %s
            ORDER BY updated_at DESC, task_id
            """,
            (run_pk,),
        )
    ]
    review_history_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None) or row
        for row in query_rows(
            """
            SELECT
                event_id,
                task_id,
                task_scope,
                previous_status,
                new_status,
                review_owner,
                reviewed_at,
                resolution_notes,
                payload_json
            FROM geo_asset_review_events
            WHERE ingestion_run_id = %s
            ORDER BY reviewed_at DESC, created_at DESC
            """,
            (run_pk,),
        )
    ]
    work_order_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None) or row
        for row in query_rows(
            """
            SELECT
                work_order_id,
                provider_id,
                status,
                district_id,
                community_id,
                building_id,
                title,
                assignee,
                task_ids_json,
                task_count,
                primary_task_id,
                focus_floor_no,
                focus_yield_pct,
                watchlist_hits,
                impact_score,
                impact_band,
                notes,
                due_at,
                created_by,
                created_at,
                updated_at,
                payload_json
            FROM geo_capture_work_orders
            WHERE ingestion_run_id = %s
            ORDER BY updated_at DESC, work_order_id
            """,
            (run_pk,),
        )
    ]
    work_order_event_rows = [
        (row.get("payload_json") if isinstance(row.get("payload_json"), dict) else None) or row
        for row in query_rows(
            """
            SELECT
                event_id,
                work_order_id,
                previous_status,
                new_status,
                changed_by,
                changed_at,
                notes,
                payload_json
            FROM geo_capture_work_order_events
            WHERE ingestion_run_id = %s
            ORDER BY changed_at DESC, created_at DESC
            """,
            (run_pk,),
        )
    ]
    coverage_tasks = [enrich_geo_asset_task_for_ui(run_summary, item) for item in coverage_task_rows]
    review_history = [enrich_geo_asset_review_event_for_ui(run_summary, item) for item in review_history_rows]
    work_order_events = [enrich_geo_work_order_event_for_ui(run_summary, item) for item in work_order_event_rows]
    review_history.sort(key=lambda entry: entry.get("reviewedAt") or "", reverse=True)
    work_order_events.sort(key=lambda entry: entry.get("changedAt") or "", reverse=True)

    return {
        **run_summary,
        "manifestPath": manifest_path,
        "manifest": manifest_payload or {"summary": summary, "attention": {}},
        "outputPaths": {
            "featurePath": None,
            "unresolvedPath": None,
            "coverageTaskPath": None,
            "reviewHistoryPath": None,
            "workOrderPath": None,
            "workOrderEventPath": None,
            "summaryPath": None,
        },
        "summary": summary,
        "attention": (manifest_payload or {}).get("attention", {}),
        "features": features,
        "unresolvedFeatures": [item for item in coverage_task_rows if item.get("task_scope") == "unresolved_feature"],
        "coverageTaskRows": coverage_task_rows,
        "coverageTasks": coverage_tasks,
        "taskSummary": summarize_geo_asset_tasks(coverage_task_rows),
        "reviewHistoryRows": review_history_rows,
        "reviewHistory": review_history,
        "workOrderRows": work_order_rows,
        "workOrders": [],
        "workOrderEventRows": work_order_event_rows,
        "workOrderEvents": work_order_events,
    }


@lru_cache(maxsize=64)
def _geo_asset_run_detail_full_cached(run_id: str) -> dict[str, Any] | None:
    manifest_path = geo_manifest_path_for_run(run_id)
    if manifest_path:
        manifest = read_json_file(manifest_path)
        if isinstance(manifest, dict) and manifest.get("run_id") == run_id:
            run_summary = geo_asset_run_summary_from_manifest(manifest, manifest_path)
            outputs = manifest.get("outputs", {})
            feature_path = resolve_artifact_path(outputs.get("building_footprints"))
            unresolved_path = resolve_artifact_path(outputs.get("unresolved_features"))
            coverage_task_path = resolve_artifact_path(outputs.get("coverage_tasks")) or default_geo_task_path(manifest_path)
            review_history_path = resolve_artifact_path(outputs.get("review_history")) or default_geo_review_history_path(manifest_path)
            work_order_path = resolve_artifact_path(outputs.get("work_orders")) or default_geo_work_order_path(manifest_path)
            work_order_event_path = (
                resolve_artifact_path(outputs.get("work_order_events")) or default_geo_work_order_event_path(manifest_path)
            )
            summary_path = resolve_artifact_path(outputs.get("summary"))
            feature_collection = read_json_file(feature_path) or {}
            features = feature_collection.get("features", []) if isinstance(feature_collection, dict) else []
            unresolved_features = read_json_file(unresolved_path) or []
            coverage_task_rows = read_json_file(coverage_task_path)
            if not isinstance(coverage_task_rows, list):
                coverage_task_rows = derive_geo_asset_tasks(run_summary, features, unresolved_features)
            review_history_rows = read_json_file(review_history_path) or []
            work_order_rows = read_json_file(work_order_path) or []
            work_order_event_rows = read_json_file(work_order_event_path) or []
            coverage_tasks = [enrich_geo_asset_task_for_ui(run_summary, item) for item in coverage_task_rows]
            review_history = [enrich_geo_asset_review_event_for_ui(run_summary, item) for item in review_history_rows]
            work_order_events = [enrich_geo_work_order_event_for_ui(run_summary, item) for item in work_order_event_rows]
            review_history.sort(key=lambda entry: entry.get("reviewedAt") or "", reverse=True)
            work_order_events.sort(key=lambda entry: entry.get("changedAt") or "", reverse=True)
            return {
                **run_summary,
                "manifestPath": manifest_path,
                "manifest": manifest,
                "outputPaths": {
                    "featurePath": feature_path,
                    "unresolvedPath": unresolved_path,
                    "coverageTaskPath": coverage_task_path,
                    "reviewHistoryPath": review_history_path,
                    "workOrderPath": work_order_path,
                    "workOrderEventPath": work_order_event_path,
                    "summaryPath": summary_path,
                },
                "summary": read_json_file(summary_path) or manifest.get("summary", {}),
                "attention": manifest.get("attention", {}),
                "features": features,
                "unresolvedFeatures": unresolved_features,
                "coverageTaskRows": coverage_task_rows,
                "coverageTasks": coverage_tasks,
                "taskSummary": summarize_geo_asset_tasks(coverage_task_rows),
                "reviewHistoryRows": review_history_rows,
                "reviewHistory": review_history,
                "workOrderRows": work_order_rows,
                "workOrders": [],
                "workOrderEventRows": work_order_event_rows,
                "workOrderEvents": work_order_events,
            }
    return db_geo_asset_run_detail_full(run_id)


def geo_asset_run_detail_full(run_id: str) -> dict[str, Any] | None:
    detail = _geo_asset_run_detail_full_cached(run_id)
    return deepcopy(detail) if detail else None


def build_geo_asset_run_view(detail: dict[str, Any]) -> dict[str, Any]:
    resolved_building_ids = {
        (feature.get("properties") or {}).get("building_id")
        for feature in detail.get("features", [])
        if (feature.get("properties") or {}).get("building_id")
    }
    catalog_communities = flatten_communities()
    coverage_gaps: list[dict[str, Any]] = []
    total_catalog_building_count = 0

    for community in catalog_communities:
        buildings = community.get("buildings", [])
        total_catalog_building_count += len(buildings)
        resolved_buildings = [building for building in buildings if building.get("id") in resolved_building_ids]
        missing_buildings = [building for building in buildings if building.get("id") not in resolved_building_ids]
        if not resolved_buildings and not missing_buildings:
            continue
        coverage_gaps.append(
            {
                "communityId": community["id"],
                "communityName": community["name"],
                "districtId": community["districtId"],
                "districtName": community["districtName"],
                "resolvedBuildingCount": len(resolved_buildings),
                "missingBuildingCount": len(missing_buildings),
                "totalBuildingCount": len(buildings),
                "coveragePct": round(len(resolved_buildings) / max(len(buildings), 1) * 100, 1),
                "missingBuildings": [
                    {
                        "buildingId": building["id"],
                        "buildingName": building["name"],
                        "sequenceNo": building.get("sequenceNo"),
                    }
                    for building in missing_buildings[:8]
                ],
            }
        )

    coverage_gaps.sort(
        key=lambda item: (
            -item["missingBuildingCount"],
            item["coveragePct"],
            item["communityName"],
        )
    )
    enriched_tasks, enriched_task_summary = enrich_geo_asset_tasks_with_priority(
        detail.get("coverageTasks", []),
        coverage_gaps=coverage_gaps,
    )
    task_index = {item.get("taskId"): item for item in enriched_tasks if item.get("taskId")}
    work_orders = [
        enrich_geo_work_order_for_ui(detail, item, task_index=task_index)
        for item in detail.get("workOrderRows", [])
        if isinstance(item, dict)
    ]
    work_orders.sort(key=lambda item: (item.get("updatedAt") or "", item.get("createdAt") or ""), reverse=True)
    active_work_order_by_task: dict[str, dict[str, Any]] = {}
    for item in work_orders:
        if item.get("status") == "closed":
            continue
        for task_id in item.get("taskIds", []):
            if task_id and task_id not in active_work_order_by_task:
                active_work_order_by_task[task_id] = item
    annotated_tasks = []
    for item in enriched_tasks:
        work_order = active_work_order_by_task.get(item.get("taskId"))
        if work_order:
            annotated_tasks.append(
                {
                    **item,
                    "workOrderId": work_order.get("workOrderId"),
                    "workOrderStatus": work_order.get("status"),
                    "workOrderStatusLabel": work_order.get("statusLabel"),
                    "workOrderAssignee": work_order.get("assignee"),
                }
            )
        else:
            annotated_tasks.append({**item, "workOrderId": None, "workOrderStatus": None, "workOrderStatusLabel": None})
    work_order_summary = summarize_geo_work_orders(work_orders, coverage_tasks=annotated_tasks)
    enriched_task_summary.update(work_order_summary)

    return {
        **detail,
        "coverage": {
            "catalogBuildingCount": total_catalog_building_count,
            "resolvedBuildingCount": len(resolved_building_ids),
            "missingBuildingCount": max(total_catalog_building_count - len(resolved_building_ids), 0),
            "catalogCoveragePct": round(len(resolved_building_ids) / max(total_catalog_building_count, 1) * 100, 1),
        },
        "coverageGaps": coverage_gaps,
        "taskSummary": enriched_task_summary,
        "coverageTasks": annotated_tasks,
        "reviewHistoryCount": len(detail.get("reviewHistory", [])),
        "recentReviews": detail.get("reviewHistory", [])[:6],
        "workOrders": work_orders,
        "workOrderSummary": work_order_summary,
        "workOrderEventCount": len(detail.get("workOrderEvents", [])),
        "recentWorkOrderEvents": detail.get("workOrderEvents", [])[:8],
        "featurePreview": [
            {
                "communityId": (feature.get("properties") or {}).get("community_id"),
                "communityName": (feature.get("properties") or {}).get("community_name"),
                "buildingId": (feature.get("properties") or {}).get("building_id"),
                "buildingName": (feature.get("properties") or {}).get("building_name"),
                "sourceRef": (feature.get("properties") or {}).get("source_ref"),
                "resolutionNotes": (feature.get("properties") or {}).get("resolution_notes"),
                "geometryType": (feature.get("geometry") or {}).get("type"),
            }
            for feature in detail.get("features", [])[:8]
        ],
    }


def feature_identity(feature: dict[str, Any]) -> dict[str, Any]:
    properties = feature.get("properties") or {}
    return {
        "communityId": properties.get("community_id"),
        "communityName": properties.get("community_name"),
        "buildingId": properties.get("building_id"),
        "buildingName": properties.get("building_name"),
        "districtId": properties.get("district_id"),
        "districtName": properties.get("district_name"),
        "sourceRef": properties.get("source_ref"),
        "resolutionNotes": properties.get("resolution_notes"),
        "geometryType": (feature.get("geometry") or {}).get("type"),
    }


def ring_area_score(ring: list[list[float]]) -> float:
    open_ring = ring_without_close(ring)
    if len(open_ring) < 3:
        return 0.0
    area = 0.0
    for index, (lon_a, lat_a) in enumerate(open_ring):
        lon_b, lat_b = open_ring[(index + 1) % len(open_ring)]
        area += lon_a * lat_b - lon_b * lat_a
    return abs(area) / 2


def approx_distance_meters(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    lon_a, lat_a = point_a
    lon_b, lat_b = point_b
    avg_lat_radians = math.radians((lat_a + lat_b) / 2)
    lon_scale = math.cos(avg_lat_radians) * 111_320
    lat_scale = 110_540
    delta_lon_m = (lon_b - lon_a) * lon_scale
    delta_lat_m = (lat_b - lat_a) * lat_scale
    return math.sqrt(delta_lon_m**2 + delta_lat_m**2)


def geometry_diff_summary(current_feature: dict[str, Any], baseline_feature: dict[str, Any]) -> dict[str, Any]:
    current_ring = feature_ring(current_feature)
    baseline_ring = feature_ring(baseline_feature)
    current_center = polygon_center_lon_lat(current_ring)
    baseline_center = polygon_center_lon_lat(baseline_ring)
    current_area = ring_area_score(current_ring)
    baseline_area = ring_area_score(baseline_ring)
    centroid_shift_m = round(approx_distance_meters(current_center, baseline_center), 1)
    area_delta_pct = (
        round(((current_area - baseline_area) / baseline_area) * 100, 1)
        if baseline_area > 0
        else None
    )
    current_vertex_count = len(ring_without_close(current_ring))
    baseline_vertex_count = len(ring_without_close(baseline_ring))
    vertex_delta = current_vertex_count - baseline_vertex_count
    has_significant_geometry_change = (
        centroid_shift_m >= 8
        or abs(area_delta_pct or 0.0) >= 6
        or abs(vertex_delta) >= 1
    )
    return {
        "centroidShiftMeters": centroid_shift_m,
        "areaDeltaPct": area_delta_pct,
        "vertexDelta": vertex_delta,
        "currentVertexCount": current_vertex_count,
        "baselineVertexCount": baseline_vertex_count,
        "hasSignificantGeometryChange": has_significant_geometry_change,
    }


def compare_geo_asset_run_details(
    current_view: dict[str, Any],
    current_detail: dict[str, Any],
    baseline_view: dict[str, Any],
    baseline_detail: dict[str, Any],
) -> dict[str, Any]:
    current_feature_index = {
        item["buildingId"]: feature
        for feature in current_detail.get("features", [])
        if (item := feature_identity(feature)).get("buildingId")
    }
    baseline_feature_index = {
        item["buildingId"]: feature
        for feature in baseline_detail.get("features", [])
        if (item := feature_identity(feature)).get("buildingId")
    }

    current_ids = set(current_feature_index)
    baseline_ids = set(baseline_feature_index)
    new_ids = sorted(current_ids - baseline_ids)
    removed_ids = sorted(baseline_ids - current_ids)
    shared_ids = sorted(current_ids & baseline_ids)
    changed_rows: list[dict[str, Any]] = []

    for building_id in shared_ids:
        diff_summary = geometry_diff_summary(current_feature_index[building_id], baseline_feature_index[building_id])
        if not diff_summary["hasSignificantGeometryChange"]:
            continue
        current_identity = feature_identity(current_feature_index[building_id])
        changed_rows.append(
            {
                **current_identity,
                "status": "changed",
                "statusLabel": "几何修正",
                **diff_summary,
            }
        )

    top_building_changes: list[dict[str, Any]] = []
    for building_id in new_ids:
        current_identity = feature_identity(current_feature_index[building_id])
        top_building_changes.append(
            {
                **current_identity,
                "status": "new",
                "statusLabel": "新增覆盖",
                "centroidShiftMeters": None,
                "areaDeltaPct": None,
                "vertexDelta": None,
            }
        )
    top_building_changes.extend(changed_rows)
    for building_id in removed_ids:
        baseline_identity = feature_identity(baseline_feature_index[building_id])
        top_building_changes.append(
            {
                **baseline_identity,
                "status": "removed",
                "statusLabel": "覆盖回退",
                "centroidShiftMeters": None,
                "areaDeltaPct": None,
                "vertexDelta": None,
            }
        )

    status_rank = {"new": 0, "changed": 1, "removed": 2}
    top_building_changes.sort(
        key=lambda item: (
            status_rank.get(str(item.get("status")), 9),
            -(item.get("centroidShiftMeters") or 0),
            -(abs(item.get("areaDeltaPct") or 0)),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )

    return {
        "baselineRunId": baseline_view.get("runId"),
        "baselineBatchName": baseline_view.get("batchName"),
        "baselineCreatedAt": baseline_view.get("createdAt"),
        "coveragePctDelta": round(
            (current_view.get("coverage", {}).get("catalogCoveragePct") or 0.0)
            - (baseline_view.get("coverage", {}).get("catalogCoveragePct") or 0.0),
            1,
        ),
        "resolvedBuildingDelta": (current_view.get("coverage", {}).get("resolvedBuildingCount") or 0)
        - (baseline_view.get("coverage", {}).get("resolvedBuildingCount") or 0),
        "missingBuildingDelta": (current_view.get("coverage", {}).get("missingBuildingCount") or 0)
        - (baseline_view.get("coverage", {}).get("missingBuildingCount") or 0),
        "openTaskDelta": (current_view.get("taskSummary", {}).get("openTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("openTaskCount") or 0),
        "reviewTaskDelta": (current_view.get("taskSummary", {}).get("reviewTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("reviewTaskCount") or 0),
        "captureTaskDelta": (current_view.get("taskSummary", {}).get("captureTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("captureTaskCount") or 0),
        "scheduledTaskDelta": (current_view.get("taskSummary", {}).get("scheduledTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("scheduledTaskCount") or 0),
        "resolvedTaskDelta": (current_view.get("taskSummary", {}).get("resolvedTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("resolvedTaskCount") or 0),
        "criticalOpenTaskDelta": (current_view.get("taskSummary", {}).get("criticalOpenTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("criticalOpenTaskCount") or 0),
        "watchlistLinkedTaskDelta": (current_view.get("taskSummary", {}).get("watchlistLinkedTaskCount") or 0)
        - (baseline_view.get("taskSummary", {}).get("watchlistLinkedTaskCount") or 0),
        "newBuildingCount": len(new_ids),
        "removedBuildingCount": len(removed_ids),
        "changedGeometryCount": len(changed_rows),
        "sharedBuildingCount": len(shared_ids),
        "topBuildingChanges": top_building_changes[:8],
    }


@lru_cache(maxsize=128)
def _geo_asset_run_comparison_cached(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    current_detail = geo_asset_run_detail_full(run_id)
    if not current_detail:
        return None
    current_view = build_geo_asset_run_view(current_detail)
    baseline_options = available_geo_baseline_runs_for(run_id)
    baseline_summary = (
        next((item for item in baseline_options if item.get("runId") == baseline_run_id), None)
        if baseline_run_id
        else (baseline_options[0] if baseline_options else None)
    )
    if not baseline_summary:
        return None
    baseline_detail = geo_asset_run_detail_full(baseline_summary["runId"])
    if not baseline_detail:
        return None
    baseline_view = build_geo_asset_run_view(baseline_detail)
    return compare_geo_asset_run_details(current_view, current_detail, baseline_view, baseline_detail)


def geo_asset_run_comparison(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    comparison = _geo_asset_run_comparison_cached(run_id, baseline_run_id)
    return deepcopy(comparison) if comparison else None


@lru_cache(maxsize=128)
def _geo_asset_run_detail_cached(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    detail = geo_asset_run_detail_full(run_id)
    if not detail:
        return None
    current_view = build_geo_asset_run_view(detail)
    current_view["comparison"] = geo_asset_run_comparison(run_id, baseline_run_id=baseline_run_id)
    return current_view


def geo_asset_run_detail(run_id: str, baseline_run_id: str | None = None) -> dict[str, Any] | None:
    detail = _geo_asset_run_detail_cached(run_id, baseline_run_id)
    return deepcopy(detail) if detail else None


def geo_task_watchlist(
    *,
    district: str | None = None,
    geo_run_id: str | None = None,
    limit: int = 12,
    include_resolved: bool = False,
) -> list[dict[str, Any]]:
    if database_mode_active():
        watchlist_by_building = {
            item["buildingId"]: item
            for item in floor_watchlist(district=district, limit=50)
            if item.get("buildingId")
        }
        work_order_by_task_id: dict[str, dict[str, Any]] = {}
        for order in db_geo_work_order_rows(geo_run_id):
            primary_task_id = order.get("primary_task_id")
            if primary_task_id:
                work_order_by_task_id[str(primary_task_id)] = order
            task_ids = order.get("task_ids_json") or []
            if isinstance(task_ids, str):
                try:
                    task_ids = json.loads(task_ids)
                except json.JSONDecodeError:
                    task_ids = []
            for task_id in task_ids:
                if task_id:
                    work_order_by_task_id[str(task_id)] = order
        items = []
        for row in db_geo_task_rows(geo_run_id):
            if not include_resolved and row.get("status") not in {"needs_review", "needs_capture", "scheduled"}:
                continue
            if district not in (None, "", "all") and row.get("district_id") != district:
                continue
            linked_watchlist = watchlist_by_building.get(row.get("building_id"))
            linked_order = work_order_by_task_id.get(str(row.get("task_id") or ""))
            impact_score = round(
                clamp(
                    (linked_watchlist.get("persistenceScore") if linked_watchlist else 0)
                    + (18 if row.get("priority") == "high" else 10 if row.get("priority") == "medium" else 4),
                    0,
                    99,
                )
            )
            impact_band = "critical" if impact_score >= 90 else "high" if impact_score >= 78 else "medium" if impact_score >= 60 else "low"
            items.append(
                {
                    "taskId": row.get("task_id"),
                    "taskScope": row.get("task_scope"),
                    "taskScopeLabel": geo_task_scope_label(row.get("task_scope")),
                    "status": row.get("status"),
                    "statusLabel": geo_task_status_label(row.get("status")),
                    "priority": row.get("priority"),
                    "providerId": row.get("provider_id"),
                    "districtId": row.get("district_id"),
                    "districtName": row.get("district_name"),
                    "communityId": row.get("community_id"),
                    "communityName": row.get("community_name"),
                    "buildingId": row.get("building_id"),
                    "buildingName": row.get("building_name"),
                    "sourceRef": row.get("source_ref"),
                    "resolutionNotes": row.get("resolution_notes"),
                    "reviewOwner": row.get("review_owner"),
                    "reviewedAt": row.get("reviewed_at").isoformat() if row.get("reviewed_at") else None,
                    "updatedAt": row.get("updated_at").isoformat() if row.get("updated_at") else None,
                    "runId": row.get("run_id"),
                    "batchName": row.get("batch_name"),
                    "watchlistHits": 1 if linked_watchlist else 0,
                    "watchlistFloors": [linked_watchlist] if linked_watchlist else [],
                    "communityScore": get_community(row.get("community_id")).get("score", 0) if row.get("community_id") and get_community(row.get("community_id")) else 0,
                    "buildingOpportunityScore": get_building(row.get("building_id")).get("score", 0) if row.get("building_id") and get_building(row.get("building_id")) else 0,
                    "focusFloorNo": linked_watchlist.get("floorNo") if linked_watchlist else None,
                    "focusYieldPct": linked_watchlist.get("latestYieldPct") if linked_watchlist else None,
                    "focusTrendLabel": linked_watchlist.get("trendLabel") if linked_watchlist else None,
                    "impactScore": impact_score,
                    "impactBand": impact_band,
                    "impactLabel": {"critical": "极高影响", "high": "高影响", "medium": "中影响", "low": "低影响"}[impact_band],
                    "recommendedAction": row.get("resolution_notes") or "优先补齐楼栋几何，避免影响楼层套利判断。",
                    "workOrderId": linked_order.get("work_order_id") if linked_order else None,
                    "workOrderStatus": linked_order.get("status") if linked_order else None,
                    "workOrderAssignee": linked_order.get("assignee") if linked_order else None,
                }
            )
        items.sort(
            key=lambda item: (
                {"needs_review": 0, "needs_capture": 1, "scheduled": 2, "resolved": 3, "captured": 4}.get(str(item.get("status")), 9),
                -float(item.get("impactScore") or 0),
                -int(item.get("watchlistHits") or 0),
                str(item.get("communityName") or ""),
                str(item.get("buildingName") or ""),
            )
        )
        return items[:limit]
    selected_run_id = geo_run_id or next(iter([item["runId"] for item in list_geo_asset_runs()]), None)
    if not selected_run_id:
        return []

    detail = geo_asset_run_detail(selected_run_id)
    if not detail:
        return []

    items: list[dict[str, Any]] = []
    for task in detail.get("coverageTasks", []):
        if not include_resolved and task.get("status") not in {"needs_review", "needs_capture", "scheduled"}:
            continue
        if district not in (None, "", "all") and task.get("districtId") != district:
            continue

        focus_floor = (task.get("watchlistFloors") or [None])[0] or {}
        items.append(
            {
                **task,
                "statusLabel": geo_task_status_label(task.get("status")),
                "focusFloorNo": focus_floor.get("floorNo"),
                "focusYieldPct": focus_floor.get("latestYieldPct"),
                "focusTrendLabel": focus_floor.get("trendLabel"),
                "targetGranularity": "floor" if focus_floor.get("floorNo") is not None else "building",
                "geoAssetRunId": detail.get("runId"),
                "geoAssetBatchName": detail.get("batchName"),
                "geoAssetProviderId": detail.get("providerId"),
            }
        )

    items.sort(
        key=lambda item: (
            {"needs_review": 0, "needs_capture": 1, "scheduled": 2, "resolved": 3, "captured": 4}.get(
                str(item.get("status")), 9
            ),
            -float(item.get("impactScore") or 0),
            -int(item.get("watchlistHits") or 0),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )
    return items[:limit]


def rebuild_geo_asset_summary(
    detail: dict[str, Any],
    *,
    coverage_task_rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    feature_count = detail["featureCount"]
    resolved_building_count = detail["resolvedBuildingCount"]
    unresolved_features = list(detail.get("unresolvedFeatures", []))
    task_summary = summarize_geo_asset_tasks(coverage_task_rows)
    summary = {
        "feature_count": feature_count,
        "resolved_building_count": resolved_building_count,
        "unresolved_feature_count": len(unresolved_features),
        "community_count": detail["communityCount"],
        "coverage_pct": detail["coveragePct"],
        "coverage_task_count": task_summary["taskCount"],
        "open_task_count": task_summary["openTaskCount"],
        "review_task_count": task_summary["reviewTaskCount"],
        "capture_task_count": task_summary["captureTaskCount"],
        "scheduled_task_count": task_summary["scheduledTaskCount"],
        "resolved_task_count": task_summary["resolvedTaskCount"],
    }
    attention = {
        "unresolved_examples": unresolved_features[:12],
        "open_task_examples": [
            {
                "task_id": item.get("task_id"),
                "task_scope": item.get("task_scope"),
                "community_name": item.get("community_name"),
                "building_name": item.get("building_name"),
                "status": item.get("status"),
                "resolution_notes": item.get("resolution_notes"),
            }
            for item in coverage_task_rows
            if item.get("status") in {"needs_review", "needs_capture", "scheduled"}
        ][:12],
    }
    return summary, attention


def update_geo_asset_task_review(
    run_id: str,
    task_id: str,
    *,
    status: str = "scheduled",
    resolution_notes: str | None = None,
    review_owner: str = "atlas-ui",
) -> dict[str, Any] | None:
    if status not in {"needs_review", "needs_capture", "scheduled", "resolved", "captured"}:
        raise ValueError("Unsupported geo asset task status")

    detail = geo_asset_run_detail_full(run_id)
    if not detail:
        return None

    coverage_task_rows = deepcopy(detail.get("coverageTaskRows", []))
    review_history = deepcopy(detail.get("reviewHistoryRows", []))
    target_task = next((item for item in coverage_task_rows if item.get("task_id") == task_id), None)
    if not target_task:
        return None

    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    previous_status = target_task.get("status", "unknown")
    review_note = resolution_notes or target_task.get("resolution_notes") or "已由工作台更新几何任务状态。"
    target_task["status"] = status
    target_task["resolution_notes"] = review_note
    target_task["review_owner"] = review_owner
    target_task["reviewed_at"] = reviewed_at
    target_task["updated_at"] = reviewed_at

    summary, attention = rebuild_geo_asset_summary(detail, coverage_task_rows=coverage_task_rows)
    manifest = deepcopy(detail["manifest"])
    manifest.setdefault("outputs", {})
    manifest["outputs"]["coverage_tasks"] = str(detail["outputPaths"]["coverageTaskPath"])
    manifest["outputs"]["review_history"] = str(detail["outputPaths"]["reviewHistoryPath"])
    manifest["summary"] = summary
    manifest["attention"] = attention

    review_event = {
        "eventId": f"{task_id}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "taskId": task_id,
        "taskScope": target_task.get("task_scope"),
        "communityId": target_task.get("community_id"),
        "communityName": target_task.get("community_name"),
        "buildingId": target_task.get("building_id"),
        "buildingName": target_task.get("building_name"),
        "sourceRef": target_task.get("source_ref"),
        "previousStatus": previous_status,
        "newStatus": status,
        "reviewOwner": review_owner,
        "reviewedAt": reviewed_at,
        "resolutionNotes": review_note,
    }
    review_history.insert(0, review_event)

    write_json_file(detail["outputPaths"]["coverageTaskPath"], coverage_task_rows)
    write_json_file(detail["outputPaths"]["reviewHistoryPath"], review_history)
    if detail["outputPaths"].get("summaryPath"):
        write_json_file(detail["outputPaths"]["summaryPath"], summary)
    write_json_file(detail["manifestPath"], manifest)

    database_sync = {"status": "skipped", "message": "未配置 PostgreSQL，同步仅写回本地几何批次文件。"}
    try:
        from .persistence import postgres_runtime_status, persist_geo_asset_run_to_postgres

        if postgres_runtime_status()["hasPostgresDsn"]:
            persist_summary = persist_geo_asset_run_to_postgres(run_id)
            database_sync = {
                "status": "synced",
                "message": "已同步到 PostgreSQL。",
                "summary": persist_summary,
            }
    except Exception as exc:  # pragma: no cover - best effort sync
        database_sync = {
            "status": "error",
            "message": f"本地几何批次已更新，但 PostgreSQL 同步失败: {exc}",
        }

    updated_detail = geo_asset_run_detail(run_id)
    return {
        "runId": run_id,
        "taskId": task_id,
        "status": status,
        "reviewOwner": review_owner,
        "reviewedAt": reviewed_at,
        "detail": updated_detail,
        "databaseSync": database_sync,
    }


def geo_asset_work_orders(
    run_id: str,
    *,
    district: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    detail = geo_asset_run_detail(run_id)
    if not detail:
        return []
    work_orders = [
        deepcopy(item)
        for item in detail.get("workOrders", [])
        if geo_work_order_matches_filters(
            item,
            district=district,
            status=status,
            assignee=assignee,
        )
    ]
    work_orders.sort(
        key=lambda item: (
            geo_work_order_status_sort_key(item.get("status")),
            -float(item.get("impactScore") or 0),
            -int(item.get("watchlistHits") or 0),
            item.get("dueAt") or "9999-12-31T23:59:59+08:00",
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )
    return work_orders[:limit]


def create_geo_asset_work_order(
    run_id: str,
    *,
    task_ids: list[str],
    assignee: str = "gis-team",
    due_at: str | None = None,
    notes: str | None = None,
    created_by: str = "atlas-ui",
) -> dict[str, Any] | None:
    detail = geo_asset_run_detail_full(run_id)
    if not detail:
        return None

    current_view = build_geo_asset_run_view(detail)
    task_index = {
        item.get("taskId"): item
        for item in current_view.get("coverageTasks", [])
        if item.get("taskId")
    }
    normalized_task_ids = [str(task_id) for task_id in task_ids if str(task_id).strip()]
    normalized_task_ids = list(dict.fromkeys(normalized_task_ids))
    if not normalized_task_ids:
        raise ValueError("至少需要选择一条几何任务来生成工单。")

    active_task_ids = {
        str(task_id)
        for item in current_view.get("workOrders", [])
        if item.get("status") != "closed"
        for task_id in item.get("taskIds", [])
        if task_id
    }
    for task_id in normalized_task_ids:
        if task_id not in task_index:
            raise ValueError(f"几何任务不存在: {task_id}")
        if task_id in active_task_ids:
            raise ValueError(f"几何任务已在打开中的工单里: {task_id}")

    selected_tasks = [task_index[task_id] for task_id in normalized_task_ids]
    selected_tasks.sort(
        key=lambda item: (
            -float(item.get("impactScore") or 0),
            -int(item.get("watchlistHits") or 0),
            str(item.get("communityName") or ""),
        )
    )
    primary_task = selected_tasks[0]
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    work_order_id = f"{run_id}::wo::{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    coverage_task_rows = deepcopy(detail.get("coverageTaskRows", []))
    review_history = deepcopy(detail.get("reviewHistoryRows", []))
    work_order_rows = deepcopy(detail.get("workOrderRows", []))
    work_order_event_rows = deepcopy(detail.get("workOrderEventRows", []))

    work_order_row = {
        "work_order_id": work_order_id,
        "status": "assigned",
        "assignee": assignee or "gis-team",
        "title": f"{primary_task.get('communityName', '待识别小区')} · {primary_task.get('buildingName', '待识别楼栋')} 几何补采",
        "task_ids": normalized_task_ids,
        "task_count": len(normalized_task_ids),
        "provider_id": detail.get("providerId"),
        "district_id": primary_task.get("districtId"),
        "district_name": primary_task.get("districtName"),
        "community_id": primary_task.get("communityId"),
        "community_name": primary_task.get("communityName"),
        "building_id": primary_task.get("buildingId"),
        "building_name": primary_task.get("buildingName"),
        "primary_task_id": primary_task.get("taskId"),
        "focus_floor_no": primary_task.get("focusFloorNo"),
        "focus_yield_pct": primary_task.get("focusYieldPct"),
        "watchlist_hits": max((int(item.get("watchlistHits") or 0) for item in selected_tasks), default=0),
        "impact_score": max((float(item.get("impactScore") or 0) for item in selected_tasks), default=0.0),
        "impact_band": primary_task.get("impactBand"),
        "notes": notes or primary_task.get("recommendedAction") or "已从 Geo Ops 工作台生成补采工单。",
        "created_by": created_by,
        "created_at": created_at,
        "updated_at": created_at,
        "due_at": due_at,
    }
    work_order_rows.insert(0, work_order_row)
    work_order_event_rows.insert(
        0,
        {
            "event_id": f"{work_order_id}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "work_order_id": work_order_id,
            "previous_status": None,
            "new_status": "assigned",
            "changed_by": created_by,
            "changed_at": created_at,
            "notes": work_order_row["notes"],
        },
    )

    for task_row in coverage_task_rows:
        if task_row.get("task_id") not in normalized_task_ids:
            continue
        if task_row.get("status") != "needs_capture":
            continue
        previous_status = task_row.get("status")
        task_row["status"] = "scheduled"
        task_row["review_owner"] = created_by
        task_row["reviewed_at"] = created_at
        task_row["updated_at"] = created_at
        task_row["resolution_notes"] = f"已生成补采工单 {work_order_id}，等待 GIS 执行。"
        review_history.insert(
            0,
            {
                "eventId": f"{task_row.get('task_id')}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                "taskId": task_row.get("task_id"),
                "taskScope": task_row.get("task_scope"),
                "communityId": task_row.get("community_id"),
                "communityName": task_row.get("community_name"),
                "buildingId": task_row.get("building_id"),
                "buildingName": task_row.get("building_name"),
                "sourceRef": task_row.get("source_ref"),
                "previousStatus": previous_status,
                "newStatus": "scheduled",
                "reviewOwner": created_by,
                "reviewedAt": created_at,
                "resolutionNotes": task_row["resolution_notes"],
            },
        )

    summary, attention = rebuild_geo_asset_summary(detail, coverage_task_rows=coverage_task_rows)
    manifest = deepcopy(detail["manifest"])
    manifest.setdefault("outputs", {})
    manifest["outputs"]["coverage_tasks"] = str(detail["outputPaths"]["coverageTaskPath"])
    manifest["outputs"]["review_history"] = str(detail["outputPaths"]["reviewHistoryPath"])
    manifest["outputs"]["work_orders"] = str(detail["outputPaths"]["workOrderPath"])
    manifest["outputs"]["work_order_events"] = str(detail["outputPaths"]["workOrderEventPath"])
    manifest["summary"] = summary
    manifest["attention"] = attention

    write_json_file(detail["outputPaths"]["coverageTaskPath"], coverage_task_rows)
    write_json_file(detail["outputPaths"]["reviewHistoryPath"], review_history)
    if detail["outputPaths"].get("summaryPath"):
        write_json_file(detail["outputPaths"]["summaryPath"], summary)
    write_json_file(detail["outputPaths"]["workOrderPath"], work_order_rows)
    write_json_file(detail["outputPaths"]["workOrderEventPath"], work_order_event_rows)
    write_json_file(detail["manifestPath"], manifest)

    database_sync = {"status": "skipped", "message": "未配置 PostgreSQL，同步仅写回本地几何工单文件。"}
    try:
        from .persistence import postgres_runtime_status, persist_geo_asset_run_to_postgres

        if postgres_runtime_status()["hasPostgresDsn"]:
            persist_summary = persist_geo_asset_run_to_postgres(run_id)
            database_sync = {
                "status": "synced",
                "message": "几何工单已同步到 PostgreSQL。",
                "summary": persist_summary,
            }
    except Exception as exc:  # pragma: no cover - best effort sync
        database_sync = {
            "status": "error",
            "message": f"本地几何工单已创建，但 PostgreSQL 同步失败: {exc}",
        }

    updated_detail = geo_asset_run_detail(run_id)
    created_order = next(
        (item for item in (updated_detail or {}).get("workOrders", []) if item.get("workOrderId") == work_order_id),
        None,
    )
    return {
        "runId": run_id,
        "workOrderId": work_order_id,
        "workOrder": created_order,
        "detail": updated_detail,
        "databaseSync": database_sync,
    }


def update_geo_asset_work_order(
    run_id: str,
    work_order_id: str,
    *,
    status: str,
    assignee: str | None = None,
    notes: str | None = None,
    changed_by: str = "atlas-ui",
) -> dict[str, Any] | None:
    if status not in {"assigned", "in_progress", "delivered", "closed"}:
        raise ValueError("Unsupported geo work order status")

    detail = geo_asset_run_detail_full(run_id)
    if not detail:
        return None

    coverage_task_rows = deepcopy(detail.get("coverageTaskRows", []))
    review_history = deepcopy(detail.get("reviewHistoryRows", []))
    work_order_rows = deepcopy(detail.get("workOrderRows", []))
    work_order_event_rows = deepcopy(detail.get("workOrderEventRows", []))
    target_order = next(
        (
            item
            for item in work_order_rows
            if (item.get("work_order_id") or item.get("workOrderId")) == work_order_id
        ),
        None,
    )
    if not target_order:
        return None

    changed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    previous_status = target_order.get("status") or "assigned"
    target_order["status"] = status
    target_order["assignee"] = assignee or target_order.get("assignee") or "gis-team"
    if notes:
        target_order["notes"] = notes
    target_order["updated_at"] = changed_at

    task_ids = {
        str(task_id)
        for task_id in (target_order.get("task_ids") or target_order.get("taskIds") or [])
        if task_id
    }
    for task_row in coverage_task_rows:
        if str(task_row.get("task_id")) not in task_ids:
            continue
        if status in {"assigned", "in_progress", "delivered"} and task_row.get("status") == "needs_capture":
            previous_task_status = task_row.get("status")
            task_row["status"] = "scheduled"
            task_row["review_owner"] = changed_by
            task_row["reviewed_at"] = changed_at
            task_row["updated_at"] = changed_at
            task_row["resolution_notes"] = f"工单 {work_order_id} 已进入 {geo_work_order_status_label(status)}。"
            review_history.insert(
                0,
                {
                    "eventId": f"{task_row.get('task_id')}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    "taskId": task_row.get("task_id"),
                    "taskScope": task_row.get("task_scope"),
                    "communityId": task_row.get("community_id"),
                    "communityName": task_row.get("community_name"),
                    "buildingId": task_row.get("building_id"),
                    "buildingName": task_row.get("building_name"),
                    "sourceRef": task_row.get("source_ref"),
                    "previousStatus": previous_task_status,
                    "newStatus": "scheduled",
                    "reviewOwner": changed_by,
                    "reviewedAt": changed_at,
                    "resolutionNotes": task_row["resolution_notes"],
                },
            )
        if status == "closed" and task_row.get("status") == "scheduled":
            task_row["status"] = "captured"
            task_row["review_owner"] = changed_by
            task_row["reviewed_at"] = changed_at
            task_row["updated_at"] = changed_at
            task_row["resolution_notes"] = f"工单 {work_order_id} 已关闭，下一版 footprint 视为已补齐。"
            review_history.insert(
                0,
                {
                    "eventId": f"{task_row.get('task_id')}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
                    "taskId": task_row.get("task_id"),
                    "taskScope": task_row.get("task_scope"),
                    "communityId": task_row.get("community_id"),
                    "communityName": task_row.get("community_name"),
                    "buildingId": task_row.get("building_id"),
                    "buildingName": task_row.get("building_name"),
                    "sourceRef": task_row.get("source_ref"),
                    "previousStatus": "scheduled",
                    "newStatus": "captured",
                    "reviewOwner": changed_by,
                    "reviewedAt": changed_at,
                    "resolutionNotes": task_row["resolution_notes"],
                },
            )

    work_order_event_rows.insert(
        0,
        {
            "event_id": f"{work_order_id}::{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "work_order_id": work_order_id,
            "previous_status": previous_status,
            "new_status": status,
            "changed_by": changed_by,
            "changed_at": changed_at,
            "notes": notes or f"工单状态更新为 {geo_work_order_status_label(status)}。",
        },
    )

    summary, attention = rebuild_geo_asset_summary(detail, coverage_task_rows=coverage_task_rows)
    manifest = deepcopy(detail["manifest"])
    manifest.setdefault("outputs", {})
    manifest["outputs"]["coverage_tasks"] = str(detail["outputPaths"]["coverageTaskPath"])
    manifest["outputs"]["review_history"] = str(detail["outputPaths"]["reviewHistoryPath"])
    manifest["outputs"]["work_orders"] = str(detail["outputPaths"]["workOrderPath"])
    manifest["outputs"]["work_order_events"] = str(detail["outputPaths"]["workOrderEventPath"])
    manifest["summary"] = summary
    manifest["attention"] = attention

    write_json_file(detail["outputPaths"]["coverageTaskPath"], coverage_task_rows)
    write_json_file(detail["outputPaths"]["reviewHistoryPath"], review_history)
    if detail["outputPaths"].get("summaryPath"):
        write_json_file(detail["outputPaths"]["summaryPath"], summary)
    write_json_file(detail["outputPaths"]["workOrderPath"], work_order_rows)
    write_json_file(detail["outputPaths"]["workOrderEventPath"], work_order_event_rows)
    write_json_file(detail["manifestPath"], manifest)

    database_sync = {"status": "skipped", "message": "未配置 PostgreSQL，同步仅写回本地几何工单文件。"}
    try:
        from .persistence import postgres_runtime_status, persist_geo_asset_run_to_postgres

        if postgres_runtime_status()["hasPostgresDsn"]:
            persist_summary = persist_geo_asset_run_to_postgres(run_id)
            database_sync = {
                "status": "synced",
                "message": "几何工单状态已同步到 PostgreSQL。",
                "summary": persist_summary,
            }
    except Exception as exc:  # pragma: no cover - best effort sync
        database_sync = {
            "status": "error",
            "message": f"本地几何工单已更新，但 PostgreSQL 同步失败: {exc}",
        }

    updated_detail = geo_asset_run_detail(run_id)
    updated_order = next(
        (item for item in (updated_detail or {}).get("workOrders", []) if item.get("workOrderId") == work_order_id),
        None,
    )
    return {
        "runId": run_id,
        "workOrderId": work_order_id,
        "workOrder": updated_order,
        "detail": updated_detail,
        "databaseSync": database_sync,
    }


def compute_yield_pct(sale_median_wan: float | int | None, rent_median_monthly: float | int | None) -> float:
    sale_value = float(sale_median_wan or 0)
    rent_value = float(rent_median_monthly or 0)
    if sale_value <= 0 or rent_value <= 0:
        return 0.0
    return round(rent_value * 12 / (sale_value * 10000) * 100, 2)


def compute_opportunity_score(yield_pct: float, sample_size: int, *, freshness_days: float | None = None) -> int:
    freshness_penalty = min(max((freshness_days or 0) * 1.2, 0), 18)
    return round(clamp(yield_pct * 24 + min(sample_size, 40) * 1.3 - freshness_penalty, 0, 99))


def freshness_days_from(value: Any) -> float | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return round((datetime.now().astimezone() - dt).total_seconds() / 86400, 2)


def db_community_dataset() -> list[dict[str, Any]]:
    if not database_mode_active():
        return []

    community_rows = db_community_rows()
    latest_anchor_reviews = db_latest_anchor_review_lookup()
    building_rows = db_building_rows()
    building_map: dict[str, list[dict[str, Any]]] = {}
    for row in building_rows:
        building_map.setdefault(row["community_id"], []).append(row)

    dataset: list[dict[str, Any]] = []
    for community_row in community_rows:
        district_id = str(community_row["district_id"])
        style = district_style(district_id)
        lon = community_row.get("centroid_lon")
        lat = community_row.get("centroid_lat")
        if lon is not None and lat is not None:
            x, y = normalize_lon_lat_to_svg(float(lon), float(lat))
        else:
            x = style.get("fallbackX") or 380
            y = style.get("fallbackY") or 260

        sale_median_wan = float(community_row.get("sale_median_wan") or 0)
        rent_median_monthly = float(community_row.get("rent_median_monthly") or 0)
        sale_sample = int(community_row.get("sale_sample") or 0)
        rent_sample = int(community_row.get("rent_sample") or 0)
        sample_size = max(sale_sample, rent_sample)
        yield_pct = float(community_row.get("yield_pct") or 0) or compute_yield_pct(sale_median_wan, rent_median_monthly)
        freshness_days = freshness_days_from(community_row.get("data_freshness"))
        sample_status = sample_status_for(
            sale_sample=sale_sample,
            rent_sample=rent_sample,
            sample_size=sample_size,
        )
        community_score = int(round(float(community_row.get("opportunity_score") or 0))) if community_row.get("opportunity_score") not in (None, "") else compute_opportunity_score(yield_pct, sample_size, freshness_days=freshness_days)
        buildings = []
        for index, building_row in enumerate(building_map.get(community_row["community_id"], []), start=1):
            low_yield = float(building_row.get("metric_low_yield_pct") or 0) or compute_yield_pct(building_row.get("low_sale_median_wan"), building_row.get("low_rent_median_monthly"))
            mid_yield = float(building_row.get("metric_mid_yield_pct") or 0) or compute_yield_pct(building_row.get("mid_sale_median_wan"), building_row.get("mid_rent_median_monthly"))
            high_yield = float(building_row.get("metric_high_yield_pct") or 0) or compute_yield_pct(building_row.get("high_sale_median_wan"), building_row.get("high_rent_median_monthly"))
            yield_values = [value for value in (low_yield, mid_yield, high_yield) if value > 0]
            overall_yield = float(building_row.get("metric_yield_pct") or 0) or compute_yield_pct(building_row.get("sale_median_wan"), building_row.get("rent_median_monthly"))
            yield_avg = round(sum(yield_values) / len(yield_values), 2) if yield_values else overall_yield
            best_bucket = max({"low": low_yield, "mid": mid_yield, "high": high_yield}, key=lambda key: {"low": low_yield, "mid": mid_yield, "high": high_yield}[key])
            building_sample_size = int(building_row.get("metric_sample_size") or 0) or max(int(building_row.get("sale_sample") or 0), int(building_row.get("rent_sample") or 0))
            geometry_json = building_row.get("building_geometry")
            buildings.append(
                {
                    "id": building_row["building_id"],
                    "name": building_row["building_no"],
                    "sequenceNo": index,
                    "communityId": community_row["community_id"],
                    "communityName": community_row["community_name"],
                    "districtId": district_id,
                    "districtName": community_row["district_name"],
                    "totalFloors": building_row.get("total_floors") or 0,
                    "unitCount": building_row.get("unit_count"),
                    "low": low_yield,
                    "mid": mid_yield,
                    "high": high_yield,
                    "yieldAvg": yield_avg,
                    "bestBucket": best_bucket,
                    "score": int(round(float(building_row.get("metric_opportunity_score") or 0))) if building_row.get("metric_opportunity_score") not in (None, "") else compute_opportunity_score(
                        yield_avg,
                        building_sample_size,
                        freshness_days=freshness_days_from(building_row.get("data_freshness")),
                    ),
                    "saleMedianWan": float(building_row.get("sale_median_wan") or 0),
                    "rentMedianMonthly": float(building_row.get("rent_median_monthly") or 0),
                    "sampleSize": building_sample_size,
                    "dataFreshness": building_row.get("data_freshness").isoformat() if building_row.get("data_freshness") else None,
                    "geometrySource": "geo_assets" if geometry_json else "catalog_gap",
                    "geometryJson": json.loads(geometry_json) if geometry_json else None,
                    "dataFreshnessLabel": "已入库样本" if building_sample_size else "主档楼栋",
                }
            )
        buildings.sort(key=lambda item: (item["name"], item["id"]))
        primary_building = max(buildings, key=lambda item: (item["score"], item["yieldAvg"]), default=None)
        dataset.append(
            {
                "id": community_row["community_id"],
                "name": community_row["community_name"],
                "districtId": district_id,
                "districtName": community_row["district_name"],
                "districtShort": community_row["short_name"],
                "x": round(float(x), 2),
                "y": round(float(y), 2),
                "avgPriceWan": round(sale_median_wan, 1) if sale_median_wan else 0,
                "monthlyRent": round(rent_median_monthly) if rent_median_monthly else 0,
                "yield": yield_pct,
                "score": community_score,
                "sample": sample_size,
                "saleSample": sale_sample,
                "rentSample": rent_sample,
                "sampleStatus": sample_status,
                "sampleStatusLabel": sample_status_label(sample_status),
                "buildingCount": int(community_row.get("building_count") or len(buildings)),
                "buildingFocus": primary_building["name"] if primary_building else None,
                "primaryBuildingId": primary_building["id"] if primary_building else None,
                "note": (
                    "数据库主读视图：已落库并具备租售比指标。"
                    if sample_status == "active_metrics"
                    else "数据库主读视图：当前只有少量样本，先作为弱提醒。"
                    if sample_status == "sparse_sample"
                    else "数据库主读视图：当前只有主档和坐标，待补房源样本。"
                ),
                "buildings": buildings,
                "dataFreshness": community_row.get("data_freshness").isoformat() if community_row.get("data_freshness") else None,
                "geometrySource": "centroid" if lon is not None and lat is not None else "district_fallback",
                "centerLng": float(lon) if lon is not None else None,
                "centerLat": float(lat) if lat is not None else None,
                "anchorSource": community_row.get("anchor_source")
                or ("community_centroid_gcj02" if community_row.get("centroid_lon") is not None and community_row.get("centroid_lat") is not None else "district_fallback"),
                "anchorQuality": float(community_row.get("anchor_quality")) if community_row.get("anchor_quality") not in (None, "") else (0.95 if community_row.get("centroid_lon") is not None and community_row.get("centroid_lat") is not None else None),
                "anchorDecisionState": community_row.get("anchor_decision_state")
                or anchor_decision_state_for(
                    center_lng=lon,
                    center_lat=lat,
                    latest_review=latest_anchor_reviews.get(str(community_row["community_id"])),
                    anchor_source=community_row.get("anchor_source"),
                ),
                "latestAnchorReview": deepcopy(latest_anchor_reviews.get(str(community_row["community_id"]))),
            }
        )
    return dataset


def staged_community_dataset(*, use_metrics_overlay: bool = True) -> list[dict[str, Any]]:
    if not staged_mode_active():
        return []

    reference_index = reference_catalog_indices()
    reference_communities = sorted(reference_index["communities"].values(), key=lambda item: (item["districtId"], item["communityName"], item["communityId"]))
    if not reference_communities and not staged_import_artifacts():
        return []

    artifacts = staged_import_artifacts()
    imported_assets = imported_building_geo_asset_index(None)
    metrics_overlay = latest_metrics_overlay() if use_metrics_overlay else {"run": None, "communityIndex": {}, "buildingBucketIndex": {}}
    metrics_run = metrics_overlay.get("run")
    metrics_community_index = metrics_overlay.get("communityIndex", {})
    metrics_building_bucket_index = metrics_overlay.get("buildingBucketIndex", {})
    sale_rows = [item for item in (artifacts["saleRows"] if artifacts else []) if item.get("community_id")]
    rent_rows = [item for item in (artifacts["rentRows"] if artifacts else []) if item.get("community_id")]
    community_groups: dict[str, dict[str, Any]] = {}

    for ref in reference_communities:
        community_groups[ref["communityId"]] = {
            "communityId": ref["communityId"],
            "communityName": ref["communityName"],
            "districtId": ref["districtId"],
            "districtName": ref["districtName"],
            "districtShort": ref["districtShort"],
            "saleRows": [],
            "rentRows": [],
            "buildings": {},
            "centerLng": ref.get("centerLng"),
            "centerLat": ref.get("centerLat"),
            "anchorSource": ref.get("anchorSource"),
            "anchorQuality": ref.get("anchorQuality"),
            "sourceRefs": list(ref.get("sourceRefs") or []),
            "candidateSuggestions": list(ref.get("candidateSuggestions") or []),
            "previewCenterLng": ref.get("previewCenterLng"),
            "previewCenterLat": ref.get("previewCenterLat"),
            "previewAnchorSource": ref.get("previewAnchorSource"),
            "previewAnchorQuality": ref.get("previewAnchorQuality"),
            "previewAnchorName": ref.get("previewAnchorName"),
            "previewAnchorAddress": ref.get("previewAnchorAddress"),
            "anchorDecisionState": ref.get("anchorDecisionState"),
            "latestAnchorReview": deepcopy(ref.get("latestAnchorReview")),
        }

    for building_ref in reference_index["buildings"].values():
        community_entry = community_groups.setdefault(
            building_ref["communityId"],
            {
                "communityId": building_ref["communityId"],
                "communityName": building_ref["communityName"],
                "districtId": building_ref["districtId"],
                "districtName": building_ref["districtName"],
                "districtShort": building_ref["districtShort"],
                "saleRows": [],
                "rentRows": [],
                "buildings": {},
                "centerLng": building_ref.get("centerLng"),
                "centerLat": building_ref.get("centerLat"),
                "anchorSource": building_ref.get("anchorSource"),
                "anchorQuality": building_ref.get("anchorQuality"),
                "sourceRefs": list(building_ref.get("sourceRefs") or []),
                "candidateSuggestions": list(building_ref.get("candidateSuggestions") or []),
                "previewCenterLng": None,
                "previewCenterLat": None,
                "previewAnchorSource": None,
                "previewAnchorQuality": None,
                "previewAnchorName": None,
                "previewAnchorAddress": None,
                "anchorDecisionState": None,
                "latestAnchorReview": None,
            },
        )
        community_entry["buildings"].setdefault(
            building_ref["buildingId"],
            {
                "buildingId": building_ref["buildingId"],
                "buildingName": building_ref["buildingName"],
                "communityId": building_ref["communityId"],
                "communityName": building_ref["communityName"],
                "districtId": building_ref["districtId"],
                "districtName": building_ref["districtName"],
                "saleRows": [],
                "rentRows": [],
                "totalFloors": building_ref.get("totalFloors"),
                "centerLng": building_ref.get("centerLng"),
                "centerLat": building_ref.get("centerLat"),
                "anchorSource": building_ref.get("anchorSource"),
                "anchorQuality": building_ref.get("anchorQuality"),
            },
        )

    for row in sale_rows + rent_rows:
        community_id = str(row.get("community_id"))
        building_id = str(row.get("building_id")) if row.get("building_id") else None
        building_ref = reference_index["buildings"].get(building_id, {}) if building_id else {}
        community_ref = reference_index["communities"].get(community_id, {})
        district_id = str(row.get("district_id") or building_ref.get("districtId") or community_ref.get("districtId") or "pudong")
        district_name = str(row.get("resolved_district_name") or building_ref.get("districtName") or community_ref.get("districtName") or district_id)
        community_name = str(row.get("resolved_community_name") or building_ref.get("communityName") or community_ref.get("communityName") or community_id)
        building_name = str(row.get("resolved_building_name") or building_ref.get("buildingName") or building_id or "待识别楼栋")
        community_entry = community_groups.setdefault(
            community_id,
            {
                "communityId": community_id,
                "communityName": community_name,
                "districtId": district_id,
                "districtName": district_name,
                "districtShort": staged_district_shape(district_id, district_name)["short"],
                "saleRows": [],
                "rentRows": [],
                "buildings": {},
                "centerLng": community_ref.get("centerLng"),
                "centerLat": community_ref.get("centerLat"),
                "anchorSource": community_ref.get("anchorSource"),
                "anchorQuality": community_ref.get("anchorQuality"),
                "sourceRefs": list(community_ref.get("sourceRefs") or []),
                "candidateSuggestions": list(community_ref.get("candidateSuggestions") or []),
                "previewCenterLng": community_ref.get("previewCenterLng"),
                "previewCenterLat": community_ref.get("previewCenterLat"),
                "previewAnchorSource": community_ref.get("previewAnchorSource"),
                "previewAnchorQuality": community_ref.get("previewAnchorQuality"),
                "previewAnchorName": community_ref.get("previewAnchorName"),
                "previewAnchorAddress": community_ref.get("previewAnchorAddress"),
                "anchorDecisionState": community_ref.get("anchorDecisionState"),
                "latestAnchorReview": deepcopy(community_ref.get("latestAnchorReview")),
            },
        )
        community_entry["saleRows" if row.get("business_type") == "sale" else "rentRows"].append(row)
        if building_id:
            building_entry = community_entry["buildings"].setdefault(
                building_id,
                {
                    "buildingId": building_id,
                    "buildingName": building_name,
                    "communityId": community_id,
                    "communityName": community_name,
                    "districtId": district_id,
                    "districtName": district_name,
                    "saleRows": [],
                    "rentRows": [],
                    "totalFloors": row.get("total_floors") or building_ref.get("totalFloors"),
                    "centerLng": building_ref.get("centerLng"),
                    "centerLat": building_ref.get("centerLat"),
                    "anchorSource": building_ref.get("anchorSource"),
                    "anchorQuality": building_ref.get("anchorQuality"),
                },
            )
            building_entry["saleRows" if row.get("business_type") == "sale" else "rentRows"].append(row)
            building_entry["totalFloors"] = building_entry.get("totalFloors") or row.get("total_floors") or building_ref.get("totalFloors")

    community_ids_by_district: dict[str, list[str]] = {}
    for community_id, community_entry in community_groups.items():
        community_ids_by_district.setdefault(community_entry["districtId"], []).append(community_id)

    dataset: list[dict[str, Any]] = []
    for district_id, community_ids in community_ids_by_district.items():
        community_ids.sort()
        for index, community_id in enumerate(community_ids):
            community_entry = community_groups[community_id]
            district_meta = staged_district_shape(community_entry["districtId"], community_entry["districtName"])
            sale_rows_for_community = community_entry["saleRows"]
            rent_rows_for_community = community_entry["rentRows"]
            community_metric = metrics_community_index.get(community_entry["communityId"]) or {}
            raw_sale_median_wan = median_value([item.get("price_total_wan") for item in sale_rows_for_community]) or 0.0
            raw_rent_median_monthly = median_value([item.get("monthly_rent") for item in rent_rows_for_community]) or 0.0
            sale_median_wan = float(community_metric.get("sale_median_wan") or raw_sale_median_wan or 0.0)
            rent_median_monthly = float(community_metric.get("rent_median_monthly") or raw_rent_median_monthly or 0.0)
            sale_sample = int(community_metric.get("sale_sample_size") or len(sale_rows_for_community) or 0)
            rent_sample = int(community_metric.get("rent_sample_size") or len(rent_rows_for_community) or 0)
            sample_size = max(sale_sample, rent_sample)
            yield_pct = float(community_metric.get("yield_pct") or 0) or compute_yield_pct(sale_median_wan, rent_median_monthly)
            raw_freshness_iso = latest_datetime_iso(
                [item.get("published_at") for item in sale_rows_for_community + rent_rows_for_community]
            )
            freshness_iso = metrics_run.get("createdAt") if metrics_run else raw_freshness_iso
            freshness_days = freshness_days_from(freshness_iso or raw_freshness_iso)
            sample_status = sample_status_for(
                sale_sample=sale_sample,
                rent_sample=rent_sample,
                sample_size=sample_size,
            )

            if community_entry.get("centerLng") is not None and community_entry.get("centerLat") is not None:
                x, y = normalize_lon_lat_to_svg(float(community_entry["centerLng"]), float(community_entry["centerLat"]))
            else:
                columns = 2 if len(community_ids) <= 4 else 3
                column_index = index % columns
                row_index = index // columns
                x = district_meta["fallbackX"] + (column_index - (columns - 1) / 2) * 42
                y = district_meta["fallbackY"] + (row_index - max((len(community_ids) - 1) // columns, 0) / 2) * 46

            buildings: list[dict[str, Any]] = []
            for building_index, building_entry in enumerate(
                sorted(community_entry["buildings"].values(), key=lambda item: (item["buildingName"], item["buildingId"])),
                start=1,
            ):
                sale_rows_for_building = building_entry["saleRows"]
                rent_rows_for_building = building_entry["rentRows"]
                bucket_metric_rows = metrics_building_bucket_index.get(building_entry["buildingId"], {})
                raw_sale_median_building = median_value([item.get("price_total_wan") for item in sale_rows_for_building]) or 0.0
                raw_rent_median_building = median_value([item.get("monthly_rent") for item in rent_rows_for_building]) or 0.0
                building_sample_size = max(
                    int(bucket_metric_rows.get("low", {}).get("sample_size") or 0),
                    int(bucket_metric_rows.get("mid", {}).get("sample_size") or 0),
                    int(bucket_metric_rows.get("high", {}).get("sample_size") or 0),
                    len(sale_rows_for_building),
                    len(rent_rows_for_building),
                )
                bucket_metrics: dict[str, tuple[float | None, float | None]] = {}
                for bucket in ("low", "mid", "high"):
                    bucket_metric = bucket_metric_rows.get(bucket) or {}
                    bucket_sale_median_raw = median_value(
                        [item.get("price_total_wan") for item in sale_rows_for_building if item.get("floor_bucket") == bucket]
                    )
                    bucket_rent_median_raw = median_value(
                        [item.get("monthly_rent") for item in rent_rows_for_building if item.get("floor_bucket") == bucket]
                    )
                    bucket_sale_median = float(bucket_metric.get("sale_median_wan") or bucket_sale_median_raw or 0) or None
                    bucket_rent_median = float(bucket_metric.get("rent_median_monthly") or bucket_rent_median_raw or 0) or None
                    bucket_metrics[bucket] = (bucket_sale_median, bucket_rent_median)
                low_yield = compute_yield_pct(*bucket_metrics["low"])
                mid_yield = compute_yield_pct(*bucket_metrics["mid"])
                high_yield = compute_yield_pct(*bucket_metrics["high"])
                sale_median_building_candidates = [
                    value
                    for value in (
                        bucket_metrics["low"][0],
                        bucket_metrics["mid"][0],
                        bucket_metrics["high"][0],
                    )
                    if value not in (None, 0)
                ]
                rent_median_building_candidates = [
                    value
                    for value in (
                        bucket_metrics["low"][1],
                        bucket_metrics["mid"][1],
                        bucket_metrics["high"][1],
                    )
                    if value not in (None, 0)
                ]
                sale_median_building = round(sum(sale_median_building_candidates) / len(sale_median_building_candidates), 2) if sale_median_building_candidates else raw_sale_median_building
                rent_median_building = round(sum(rent_median_building_candidates) / len(rent_median_building_candidates), 2) if rent_median_building_candidates else raw_rent_median_building
                overall_yield = compute_yield_pct(sale_median_building, rent_median_building)
                yield_values = [value for value in (low_yield, mid_yield, high_yield) if value > 0]
                yield_avg = round(sum(yield_values) / len(yield_values), 2) if yield_values else overall_yield
                best_bucket = max(
                    {"low": low_yield, "mid": mid_yield, "high": high_yield},
                    key=lambda key: {"low": low_yield, "mid": mid_yield, "high": high_yield}[key],
                )
                building_freshness = latest_datetime_iso(
                    [item.get("published_at") for item in sale_rows_for_building + rent_rows_for_building]
                )
                building_metric_score = max(
                    float(bucket_metric_rows.get("low", {}).get("opportunity_score") or 0),
                    float(bucket_metric_rows.get("mid", {}).get("opportunity_score") or 0),
                    float(bucket_metric_rows.get("high", {}).get("opportunity_score") or 0),
                )
                imported_asset = imported_assets.get(building_entry["buildingId"])
                buildings.append(
                    {
                        "id": building_entry["buildingId"],
                        "name": building_entry["buildingName"],
                        "sequenceNo": building_index,
                        "communityId": community_entry["communityId"],
                        "communityName": community_entry["communityName"],
                        "districtId": community_entry["districtId"],
                        "districtName": community_entry["districtName"],
                        "totalFloors": int(building_entry.get("totalFloors") or 0),
                        "unitCount": None,
                        "low": low_yield,
                        "mid": mid_yield,
                        "high": high_yield,
                        "yieldAvg": yield_avg,
                        "bestBucket": best_bucket,
                        "score": int(round(building_metric_score)) if building_metric_score > 0 else compute_opportunity_score(
                            yield_avg,
                            building_sample_size,
                            freshness_days=freshness_days_from(metrics_run.get("createdAt") if metrics_run else building_freshness),
                        ),
                        "saleMedianWan": sale_median_building,
                        "rentMedianMonthly": rent_median_building,
                        "sampleSize": building_sample_size,
                        "dataFreshness": metrics_run.get("createdAt") if metrics_run else building_freshness,
                        "geometrySource": (
                            "imported"
                            if imported_asset
                            else "building_anchor"
                            if building_entry.get("centerLng") is not None and building_entry.get("centerLat") is not None
                            else "synthetic_staged"
                        ),
                        "geometryJson": {"type": "Polygon", "coordinates": [imported_asset["ring"]]} if imported_asset else None,
                        "centerLng": building_entry.get("centerLng"),
                        "centerLat": building_entry.get("centerLat"),
                        "anchorSource": building_entry.get("anchorSource"),
                        "anchorQuality": building_entry.get("anchorQuality"),
                        "metricsRunId": metrics_run.get("runId") if metrics_run else None,
                        "metricsSnapshotDate": metrics_run.get("snapshotDate") if metrics_run else None,
                    }
                )
            primary_building = max(buildings, key=lambda item: (item["score"], item["yieldAvg"]), default=None)
            dataset.append(
                {
                    "id": community_entry["communityId"],
                    "name": community_entry["communityName"],
                    "districtId": community_entry["districtId"],
                    "districtName": community_entry["districtName"],
                    "districtShort": community_entry["districtShort"],
                    "x": round(float(x), 2),
                    "y": round(float(y), 2),
                    "avgPriceWan": round(sale_median_wan, 1),
                    "monthlyRent": round(rent_median_monthly),
                    "yield": yield_pct,
                    "score": int(round(float(community_metric.get("opportunity_score") or 0))) if community_metric.get("opportunity_score") not in (None, "") else compute_opportunity_score(yield_pct, sample_size, freshness_days=freshness_days),
                    "sample": sample_size,
                    "saleSample": sale_sample,
                    "rentSample": rent_sample,
                    "sampleStatus": sample_status,
                    "sampleStatusLabel": sample_status_label(sample_status),
                    "buildingCount": len(buildings),
                    "buildingFocus": primary_building["name"] if primary_building else None,
                    "primaryBuildingId": primary_building["id"] if primary_building else None,
                    "note": (
                        f"指标快照 {metrics_run.get('snapshotDate')}：已有小区级租售比样本，可进入主分析面。"
                        if metrics_run and sample_status == "active_metrics"
                        else "离线研究快照：已有小区级租售比样本，可进入主分析面。"
                        if sample_status == "active_metrics"
                        else f"指标快照 {metrics_run.get('snapshotDate')}：当前只有零散样本，先保留弱提示。"
                        if metrics_run and sample_status == "sparse_sample"
                        else "离线研究快照：当前只有零散样本，先保留弱提示。"
                        if sample_status == "sparse_sample"
                        else f"指标快照 {metrics_run.get('snapshotDate')}：已挂图并拿到真实坐标，后续补 listing / geometry 即可升格到主分析面。"
                        if metrics_run
                        else "离线研究快照：已挂图并拿到真实坐标，后续补 listing / geometry 即可升格到主分析面。"
                    ),
                    "buildings": buildings,
                    "dataFreshness": freshness_iso,
                    "geometrySource": "catalog_anchor" if community_entry.get("centerLng") is not None and community_entry.get("centerLat") is not None else "district_fallback",
                    "centerLng": community_entry.get("centerLng"),
                    "centerLat": community_entry.get("centerLat"),
                    "anchorSource": community_entry.get("anchorSource"),
                    "anchorQuality": community_entry.get("anchorQuality"),
                    "sourceRefs": list(community_entry.get("sourceRefs") or []),
                    "candidateSuggestions": list(community_entry.get("candidateSuggestions") or []),
                    "previewCenterLng": community_entry.get("previewCenterLng"),
                    "previewCenterLat": community_entry.get("previewCenterLat"),
                    "previewAnchorSource": community_entry.get("previewAnchorSource"),
                    "previewAnchorQuality": community_entry.get("previewAnchorQuality"),
                    "previewAnchorName": community_entry.get("previewAnchorName"),
                    "previewAnchorAddress": community_entry.get("previewAnchorAddress"),
                    "anchorDecisionState": community_entry.get("anchorDecisionState")
                    or anchor_decision_state_for(
                        center_lng=community_entry.get("centerLng"),
                        center_lat=community_entry.get("centerLat"),
                        preview_lng=community_entry.get("previewCenterLng"),
                        preview_lat=community_entry.get("previewCenterLat"),
                        latest_review=community_entry.get("latestAnchorReview"),
                        anchor_source=community_entry.get("anchorSource"),
                    ),
                    "latestAnchorReview": deepcopy(community_entry.get("latestAnchorReview")),
                    "metricsRunId": metrics_run.get("runId") if metrics_run else None,
                    "metricsSnapshotDate": metrics_run.get("snapshotDate") if metrics_run else None,
                }
            )
    dataset.sort(key=lambda item: (item["districtId"], -item["score"], item["name"]))
    return dataset


def staged_district_dataset(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> list[dict[str, Any]]:
    communities = [
        item
        for item in staged_community_dataset()
        if community_visible(
            item,
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        )
    ]
    district_map: dict[str, dict[str, Any]] = {}
    for community in communities:
        district_item = district_map.setdefault(
            community["districtId"],
            {
                **staged_district_shape(community["districtId"], community["districtName"]),
                "communities": [],
            },
        )
        district_item["communities"].append(community)

    visible_districts = []
    for district_item in district_map.values():
        if district not in (None, "", "all") and district_item["id"] != district:
            continue
        if not district_item["communities"]:
            continue
        community_count = len(district_item["communities"])
        district_item["yield"] = round(sum(item["yield"] for item in district_item["communities"]) / community_count, 2)
        district_item["budget"] = round(sum(item["avgPriceWan"] for item in district_item["communities"]) / community_count, 1)
        district_item["rent"] = round(sum(item["monthlyRent"] for item in district_item["communities"]) / community_count)
        district_item["saleSample"] = sum(int(item.get("saleSample") or 0) for item in district_item["communities"])
        district_item["rentSample"] = sum(int(item.get("rentSample") or 0) for item in district_item["communities"])
        district_item["score"] = max(int(item["score"]) for item in district_item["communities"])
        district_item["trend"] = "STAGED"
        visible_districts.append(district_item)
    visible_districts.sort(key=lambda item: item["id"])
    return visible_districts


def db_district_dataset(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> list[dict[str, Any]]:
    communities = [
        item
        for item in db_community_dataset()
        if community_visible(
            item,
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        )
    ]
    district_map: dict[str, dict[str, Any]] = {
        district_item["id"]: {key: deepcopy(value) for key, value in district_item.items() if key != "communities"}
        for district_item in DISTRICTS
    }
    for district_item in district_map.values():
        district_item["communities"] = []
    for community in communities:
        district_map.setdefault(
            community["districtId"],
            {
                "id": community["districtId"],
                "name": community["districtName"],
                "short": community.get("districtShort") or community["districtName"],
                "polygon": district_style(community["districtId"]).get("polygon"),
                "communities": [],
            },
        )["communities"].append(community)

    visible_districts = []
    for district_item in district_map.values():
        if district not in (None, "", "all") and district_item["id"] != district:
            continue
        if not district_item["communities"]:
            continue
        community_count = len(district_item["communities"])
        district_item["yield"] = round(sum(item["yield"] for item in district_item["communities"]) / community_count, 2)
        district_item["budget"] = round(sum(item["avgPriceWan"] for item in district_item["communities"]) / community_count, 1)
        district_item["rent"] = round(sum(item["monthlyRent"] for item in district_item["communities"]) / community_count)
        district_item["saleSample"] = sum(int(item.get("saleSample") or 0) for item in district_item["communities"])
        district_item["rentSample"] = sum(int(item.get("rentSample") or 0) for item in district_item["communities"])
        district_item["score"] = max(int(item["score"]) for item in district_item["communities"])
        district_item["trend"] = "DB"
        district_item.setdefault("polygon", district_style(district_item["id"]).get("polygon"))
        visible_districts.append(district_item)
    return visible_districts


def db_floor_history_summary_from_snapshot_rows(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    first = rows[0]
    latest = rows[-1]
    return {
        "observedRuns": len(rows),
        "latestRunId": latest.get("run_id"),
        "latestBatchName": latest.get("batch_name"),
        "firstBatchName": first.get("batch_name"),
        "yieldDeltaSinceFirst": round(float(latest.get("yield_pct") or 0) - float(first.get("yield_pct") or 0), 2)
        if len(rows) >= 2
        else None,
        "avgYieldPct": round(sum(float(row.get("yield_pct") or 0) for row in rows) / len(rows), 2),
        "totalPairCount": sum(int(row.get("pair_count") or 0) for row in rows),
    }


def db_floor_history(building_id: str, floor_no: int) -> dict[str, Any]:
    rows = [
        row
        for row in db_floor_snapshot_rows()
        if row.get("building_id") == building_id and int(row.get("floor_no") or -1) == int(floor_no)
    ]
    if not rows:
        return {"timeline": [], "summary": None}
    history_rows = []
    previous = None
    for row in rows:
        yield_pct = float(row.get("yield_pct") or 0)
        pair_count = int(row.get("pair_count") or 0)
        sale_median = float(row.get("sale_median_wan") or 0)
        rent_median = float(row.get("rent_median_monthly") or 0)
        yield_delta = round(yield_pct - float(previous.get("yieldPct") or 0), 2) if previous else None
        pair_delta = pair_count - int(previous.get("pairCount") or 0) if previous else None
        status, status_label = comparison_status_for_delta(yield_delta)
        history_rows.append(
            {
                "runId": row.get("run_id"),
                "batchName": row.get("batch_name"),
                "createdAt": row.get("created_at").isoformat() if row.get("created_at") else None,
                "pairCount": pair_count,
                "yieldPct": yield_pct,
                "saleMedianWan": sale_median,
                "rentMedianMonthly": rent_median,
                "bestPairConfidence": float(row.get("best_pair_confidence") or 0),
                "yieldDeltaVsPrevious": yield_delta,
                "pairCountDeltaVsPrevious": pair_delta,
                "saleMedianDeltaWan": round(sale_median - float(previous.get("saleMedianWan") or 0), 2) if previous else None,
                "rentMedianDeltaMonthly": round(rent_median - float(previous.get("rentMedianMonthly") or 0), 2) if previous else None,
                "status": status if previous else "new",
                "statusLabel": status_label if previous else "首个快照",
                "isLatest": False,
            }
        )
        previous = history_rows[-1]
    history_rows[-1]["isLatest"] = True
    return {
        "timeline": list(reversed(history_rows)),
        "summary": db_floor_history_summary_from_snapshot_rows(rows),
    }


@lru_cache(maxsize=1)
def _operations_payload_cached() -> dict[str, Any]:
    runtime = runtime_data_state()
    reference_runs = list_reference_runs()
    import_runs = list_import_runs()
    geo_asset_runs = list_geo_asset_runs()
    metrics_runs = list_metrics_runs()
    metrics_refresh_history = list_metrics_refresh_history(limit=8)
    browser_capture_runs = list_browser_capture_runs(limit=10)
    reference_index = reference_catalog_indices()
    community_dataset = current_community_dataset()
    priority_buildings = [
        building
        for community in community_dataset
        if community["districtId"] in priority_districts()
        for building in community.get("buildings", [])
    ]
    priority_real_geometry_count = sum(
        1 for building in priority_buildings if building.get("geometrySource") in {"geo_assets", "imported", "building_anchor"}
    )
    address_queue = all_address_queue_items() if (runtime["activeDataMode"] == "mock" or import_runs) else []
    resolved_count = sum(1 for item in address_queue if item["status"] == "resolved")
    review_count = sum(1 for item in address_queue if item["status"] == "needs_review")
    matching_count = sum(1 for item in address_queue if item["status"] == "matching")
    avg_normalization = round(
        (resolved_count / max(resolved_count + review_count + matching_count, 1)) * 100,
        1,
    )
    provider_health = runtime["providerReadiness"]
    db_snapshot = runtime["databaseSnapshot"]
    latest_reference_run = reference_runs[0] if reference_runs else None
    latest_import_run = import_runs[0] if import_runs else None
    latest_geo_run = geo_asset_runs[0] if geo_asset_runs else None
    latest_metrics_run = metrics_runs[0] if metrics_runs else None
    sample_freshness = db_snapshot["latestSampleAt"]
    latest_successful_run = db_snapshot["latestSuccessfulRunAt"]
    if runtime["activeDataMode"] == "staged" and latest_import_run:
        sample_freshness = latest_import_run.get("createdAt")
        latest_successful_run = latest_import_run.get("createdAt")
    elif runtime["activeDataMode"] == "staged" and latest_reference_run:
        latest_successful_run = latest_reference_run.get("createdAt")
    latest_metrics_refresh_at = db_snapshot.get("latestMetricsRefreshAt")
    if runtime["activeDataMode"] == "staged" and latest_metrics_run:
        latest_metrics_refresh_at = latest_metrics_run.get("createdAt")
    city_community_count = len(reference_index["communities"]) or int(db_snapshot.get("communityCount") or 0)
    anchored_community_count = sum(
        1
        for item in reference_index["communities"].values()
        if item.get("centerLng") is not None and item.get("centerLat") is not None
    )
    anchor_watchlist = anchor_watchlist_payload(limit=20)
    latest_anchor_review_lookup = latest_reference_anchor_review_lookup()
    latest_anchor_review_at_value = latest_anchor_review_at(list(latest_anchor_review_lookup.values()))
    return {
        "summary": {
            "sourceCount": len(provider_health),
            "readySourceCount": sum(
                1 for item in provider_health if item["connectionState"] in {"offline_ready", "credentials_ready", "connected_live"}
            ),
            "resolvedQueueCount": resolved_count,
            "reviewQueueCount": review_count,
            "matchingQueueCount": matching_count,
            "avgNormalizationPct": avg_normalization,
            "referenceRunCount": len(reference_runs),
            "importRunCount": len(import_runs),
            "geoAssetRunCount": len(geo_asset_runs),
            "metricsRunCount": len(metrics_runs),
            "browserCaptureRunCount": len(browser_capture_runs),
            "activeDataMode": runtime["activeDataMode"],
            "mockEnabled": runtime["mockEnabled"],
            "hasRealData": runtime["hasRealData"],
            "databaseConnected": runtime["databaseConnected"],
            "databaseReadable": runtime["databaseReadable"],
            "databaseSeeded": runtime["databaseSeeded"],
            "latestBootstrapAt": runtime.get("latestBootstrapAt"),
            "cityCoveragePct": db_snapshot["cityCoveragePct"],
            "buildingCoveragePct": db_snapshot["buildingCoveragePct"],
            "sampleFreshness": sample_freshness,
            "latestSuccessfulRunAt": latest_successful_run,
            "databaseCommunityCount": int(db_snapshot.get("communityCount") or 0),
            "databaseBuildingCount": int(db_snapshot.get("buildingCount") or 0),
            "databaseSaleListingCount": int(db_snapshot.get("saleListingCount") or 0),
            "databaseRentListingCount": int(db_snapshot.get("rentListingCount") or 0),
            "databaseGeoAssetCount": int(db_snapshot.get("geoAssetCount") or 0),
            "geoAssetCoveragePct": round(max((item.get("coveragePct") or 0.0) for item in geo_asset_runs), 1) if geo_asset_runs else 0.0,
            "geoAssetOpenTaskCount": sum(int(item.get("openTaskCount") or 0) for item in geo_asset_runs),
            "geoAssetCriticalTaskCount": 0,
            "geoAssetWatchlistLinkedTaskCount": 0,
            "cityCommunityCount": city_community_count,
            "anchoredCommunityCount": anchored_community_count,
            "anchoredCommunityPct": round(anchored_community_count / max(city_community_count, 1) * 100, 1) if city_community_count else 0.0,
            "priorityDistrictBuildingCount": len(priority_buildings),
            "priorityDistrictGeoCoveragePct": round(
                priority_real_geometry_count / max(len(priority_buildings), 1) * 100,
                1,
            )
            if priority_buildings
            else 0.0,
            "pendingAnchorCount": int(anchor_watchlist.get("summary", {}).get("watchCount") or 0),
            "candidateBackedAnchorCount": int(anchor_watchlist.get("summary", {}).get("candidateBackedCount") or 0),
            "latestAnchorReviewAt": latest_anchor_review_at_value,
            "latestReferenceRunAt": latest_reference_run.get("createdAt") if latest_reference_run else None,
            "latestListingRunAt": latest_import_run.get("createdAt") if latest_import_run else None,
            "latestGeoRunAt": latest_geo_run.get("createdAt") if latest_geo_run else None,
            "latestMetricsRunAt": latest_metrics_run.get("createdAt") if latest_metrics_run else None,
            "latestStagedMetricsRunAt": latest_metrics_run.get("createdAt") if latest_metrics_run else None,
            "latestBrowserCaptureAt": browser_capture_runs[0].get("createdAt") if browser_capture_runs else None,
            "latestReferencePersistAt": db_snapshot.get("latestReferencePersistAt"),
            "latestImportPersistAt": db_snapshot.get("latestImportPersistAt"),
            "latestGeoPersistAt": db_snapshot.get("latestGeoPersistAt"),
            "latestMetricsRefreshAt": latest_metrics_refresh_at,
            "latestDatabaseMetricsRefreshAt": db_snapshot.get("latestMetricsRefreshAt"),
            "browserCaptureAttentionCount": sum(int(item.get("attentionCount") or 0) for item in browser_capture_runs),
        },
        "runtime": runtime,
        "sourceHealth": provider_health,
        "addressQueue": address_queue,
        "anchorWatchlist": anchor_watchlist["items"],
        "referenceRuns": reference_runs,
        "importRuns": import_runs,
        "geoAssetRuns": geo_asset_runs,
        "metricsRuns": metrics_runs,
        "metricsRefreshHistory": metrics_refresh_history,
        "browserCaptureRuns": browser_capture_runs,
    }


def operations_payload() -> dict[str, Any]:
    return deepcopy(_operations_payload_cached())


def bootstrap_payload() -> dict[str, Any]:
    runtime = runtime_data_state()
    return {
        "districts": (
            list_districts()
            if runtime["activeDataMode"] in {"database", "staged"}
            else (deepcopy(DISTRICTS) if runtime["activeDataMode"] == "mock" else [])
        ),
        "pipeline_steps": deepcopy(PIPELINE_STEPS),
        "schemas": deepcopy(SCHEMAS),
        "system_strategy": system_strategy_payload()["system_strategy"],
        "data_sources": system_strategy_payload()["data_sources"],
        "runtime": runtime,
        "operations_overview": bootstrap_operations_payload(),
    }


@lru_cache(maxsize=1)
def _bootstrap_operations_payload_cached() -> dict[str, Any]:
    runtime = runtime_data_state()
    reference_runs = list_reference_runs()
    import_runs = list_import_runs()
    geo_asset_runs = list_geo_asset_runs()
    metrics_runs = list_metrics_runs()
    metrics_refresh_history = list_metrics_refresh_history(limit=8)
    browser_capture_runs = list_browser_capture_runs(limit=10)
    reference_index = reference_catalog_indices()
    city_community_count = len(reference_index["communities"])
    anchored_community_count = sum(
        1
        for item in reference_index["communities"].values()
        if item.get("centerLng") is not None and item.get("centerLat") is not None
    )
    return {
        "summary": {
            "sourceCount": len(runtime["providerReadiness"]),
            "readySourceCount": sum(
                1 for item in runtime["providerReadiness"] if item["connectionState"] in {"offline_ready", "credentials_ready", "connected_live"}
            ),
            "resolvedQueueCount": 0,
            "reviewQueueCount": 0,
            "matchingQueueCount": 0,
            "avgNormalizationPct": 0,
            "referenceRunCount": len(reference_runs),
            "importRunCount": len(import_runs),
            "geoAssetRunCount": len(geo_asset_runs),
            "metricsRunCount": len(metrics_runs),
            "browserCaptureRunCount": len(browser_capture_runs),
            "activeDataMode": runtime["activeDataMode"],
            "mockEnabled": runtime["mockEnabled"],
            "hasRealData": runtime["hasRealData"],
            "databaseConnected": runtime["databaseConnected"],
            "databaseReadable": runtime["databaseReadable"],
            "databaseSeeded": runtime["databaseSeeded"],
            "latestBootstrapAt": runtime.get("latestBootstrapAt"),
            "databaseCommunityCount": 0,
            "databaseBuildingCount": 0,
            "databaseSaleListingCount": 0,
            "databaseRentListingCount": 0,
            "databaseGeoAssetCount": 0,
            "cityCoveragePct": 0.0,
            "buildingCoveragePct": 0.0,
            "sampleFreshness": import_runs[0].get("createdAt") if import_runs else None,
            "latestSuccessfulRunAt": import_runs[0].get("createdAt") if import_runs else (reference_runs[0].get("createdAt") if reference_runs else None),
            "cityCommunityCount": city_community_count,
            "anchoredCommunityCount": anchored_community_count,
            "anchoredCommunityPct": round(anchored_community_count / max(city_community_count, 1) * 100, 1) if city_community_count else 0.0,
            "priorityDistrictBuildingCount": 0,
            "priorityDistrictGeoCoveragePct": 0.0,
            "latestReferenceRunAt": reference_runs[0].get("createdAt") if reference_runs else None,
            "latestListingRunAt": import_runs[0].get("createdAt") if import_runs else None,
            "latestGeoRunAt": geo_asset_runs[0].get("createdAt") if geo_asset_runs else None,
            "latestMetricsRunAt": metrics_runs[0].get("createdAt") if metrics_runs else None,
            "latestStagedMetricsRunAt": metrics_runs[0].get("createdAt") if metrics_runs else None,
            "latestBrowserCaptureAt": browser_capture_runs[0].get("createdAt") if browser_capture_runs else None,
            "latestMetricsRefreshAt": metrics_runs[0].get("createdAt") if metrics_runs else None,
            "latestDatabaseMetricsRefreshAt": runtime.get("databaseSnapshot", {}).get("latestMetricsRefreshAt"),
            "latestReferencePersistAt": None,
            "latestImportPersistAt": None,
            "latestGeoPersistAt": None,
            "pendingAnchorCount": 0,
            "candidateBackedAnchorCount": 0,
            "latestAnchorReviewAt": None,
            "browserCaptureAttentionCount": sum(int(item.get("attentionCount") or 0) for item in browser_capture_runs),
            "geoAssetCoveragePct": round(max((item.get("coveragePct") or 0.0) for item in geo_asset_runs), 1) if geo_asset_runs else 0.0,
            "geoAssetOpenTaskCount": sum(int(item.get("openTaskCount") or 0) for item in geo_asset_runs),
            "geoAssetCriticalTaskCount": 0,
            "geoAssetWatchlistLinkedTaskCount": 0,
        },
        "runtime": runtime,
        "sourceHealth": runtime["providerReadiness"],
        "addressQueue": [],
        "anchorWatchlist": [],
        "referenceRuns": reference_runs,
        "importRuns": import_runs,
        "geoAssetRuns": geo_asset_runs,
        "metricsRuns": metrics_runs,
        "metricsRefreshHistory": metrics_refresh_history,
        "browserCaptureRuns": browser_capture_runs,
    }


def bootstrap_operations_payload() -> dict[str, Any]:
    return deepcopy(_bootstrap_operations_payload_cached())


@lru_cache(maxsize=1)
def _system_strategy_payload_cached() -> dict[str, Any]:
    runtime = runtime_data_state()
    strategy = deepcopy(SYSTEM_STRATEGY)
    strategy["data_runtime"] = {
        "active_data_mode": runtime["activeDataMode"],
        "mock_enabled": runtime["mockEnabled"],
        "has_real_data": runtime["hasRealData"],
        "database_connected": runtime["databaseConnected"],
        "database_readable": runtime["databaseReadable"],
        "database_seeded": runtime["databaseSeeded"],
        "latest_bootstrap_at": runtime.get("latestBootstrapAt"),
        "daily_research_mode": True,
        "staged_import_run_count": runtime["stagedImportRunCount"],
        "staged_geo_run_count": runtime["stagedGeoRunCount"],
        "staged_metrics_run_count": runtime["stagedMetricsRunCount"],
    }
    strategy["priority_districts"] = priority_districts()
    strategy["browser_sampling_policy"] = {
        "provider_id": "public-browser-sampling",
        "scope": "staging_only",
        "read_only_public_pages": True,
        "login_required_pages": False,
        "bulk_scraping": False,
        "note": "只用于公开页面字段补洞与小批量浏览器辅助采样，最终仍统一落成标准批次。",
    }
    return {
        "system_strategy": strategy,
        "data_sources": runtime["providerReadiness"],
        "runtime": runtime,
    }


def system_strategy_payload() -> dict[str, Any]:
    return deepcopy(_system_strategy_payload_cached())


def bootstrap_local_database(
    *,
    reference_run_id: str | None = None,
    import_run_id: str | None = None,
    geo_run_id: str | None = None,
    apply_schema: bool = False,
    refresh_metrics: bool = True,
) -> dict[str, Any]:
    from .persistence import (
        persist_geo_asset_run_to_postgres,
        persist_import_run_to_postgres,
        persist_metrics_snapshot_to_postgres,
        persist_reference_dictionary_manifest_to_postgres,
        postgres_runtime_status,
    )
    from jobs.refresh_metrics import build_snapshot

    postgres_status = postgres_runtime_status()
    if not postgres_status.get("hasPostgresDsn"):
        raise RuntimeError("未配置 POSTGRES_DSN，无法执行本地数据库引导。")

    reference_runs = list_reference_runs()
    import_runs = list_import_runs()
    geo_runs = list_geo_asset_runs()
    selected_reference = next((item for item in reference_runs if item["runId"] == reference_run_id), None) if reference_run_id else (reference_runs[0] if reference_runs else None)
    selected_import = next((item for item in import_runs if item["runId"] == import_run_id), None) if import_run_id else (import_runs[0] if import_runs else None)
    selected_geo = next((item for item in geo_runs if item["runId"] == geo_run_id), None) if geo_run_id else (geo_runs[0] if geo_runs else None)

    if reference_run_id and not selected_reference:
        raise KeyError(f"Reference run not found: {reference_run_id}")
    if import_run_id and not selected_import:
        raise KeyError(f"Import run not found: {import_run_id}")
    if geo_run_id and not selected_geo:
        raise KeyError(f"Geo asset run not found: {geo_run_id}")
    if not selected_reference:
        raise RuntimeError("本地数据库引导至少需要一个 reference run。")

    schema_pending = apply_schema
    steps: list[dict[str, Any]] = []

    reference_manifest_path = reference_manifest_path_for_run(selected_reference["runId"])
    if reference_manifest_path is None:
        raise KeyError(f"Reference manifest not found for run: {selected_reference['runId']}")
    reference_summary = persist_reference_dictionary_manifest_to_postgres(
        reference_manifest_path,
        apply_schema=schema_pending,
    )
    steps.append({"step": "reference", "status": "completed", "runId": selected_reference["runId"], "summary": reference_summary})
    schema_pending = False

    if selected_import:
        import_summary = persist_import_run_to_postgres(selected_import["runId"], apply_schema=schema_pending)
        steps.append({"step": "import", "status": "completed", "runId": selected_import["runId"], "summary": import_summary})
    else:
        steps.append({"step": "import", "status": "skipped", "reason": "未找到 import run，跳过 listing 落库。"})

    if selected_geo:
        geo_summary = persist_geo_asset_run_to_postgres(selected_geo["runId"], apply_schema=schema_pending)
        steps.append({"step": "geo", "status": "completed", "runId": selected_geo["runId"], "summary": geo_summary})
    else:
        steps.append({"step": "geo", "status": "skipped", "reason": "未找到 geo run，跳过楼栋几何落库。"})

    metrics_summary: dict[str, Any] | None = None
    if refresh_metrics:
        snapshot = build_snapshot(datetime.now().astimezone().date())
        metrics_summary = persist_metrics_snapshot_to_postgres(snapshot, apply_schema=schema_pending)
        steps.append({"step": "metrics", "status": "completed", "summary": metrics_summary})
    else:
        steps.append({"step": "metrics", "status": "skipped", "reason": "调用方显式关闭 metrics 刷新。"})

    runtime = runtime_data_state()
    return {
        "status": "completed",
        "referenceRunId": selected_reference["runId"],
        "importRunId": selected_import["runId"] if selected_import else None,
        "geoRunId": selected_geo["runId"] if selected_geo else None,
        "metrics": metrics_summary,
        "steps": steps,
        "runtime": runtime,
        "databaseSnapshot": runtime.get("databaseSnapshot"),
    }


def community_visible(
    community: dict[str, Any],
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> bool:
    return (
        community["yield"] >= min_yield
        and community["avgPriceWan"] <= max_budget
        and community["sample"] >= min_samples
        and (district in (None, "", "all") or community["districtId"] == district)
    )


def flatten_communities(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    use_staged_metrics_overlay: bool = True,
) -> list[dict[str, Any]]:
    if database_mode_active():
        return [
            item
            for item in db_community_dataset()
            if community_visible(
                item,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            )
        ]
    if staged_mode_active():
        return [
            item
            for item in staged_community_dataset(use_metrics_overlay=use_staged_metrics_overlay)
            if community_visible(
                item,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            )
        ]
    if not demo_mode_active():
        return []
    communities: list[dict[str, Any]] = []
    for district_item in DISTRICTS:
        for community in district_item["communities"]:
            if community_visible(
                community,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            ):
                communities.append(enrich_community(community, district_item))
    return communities


@lru_cache(maxsize=2)
def _current_community_dataset_cached(use_staged_metrics_overlay: bool = True) -> tuple[dict[str, Any], ...]:
    if database_mode_active():
        return tuple(db_community_dataset())
    if staged_mode_active():
        return tuple(staged_community_dataset(use_metrics_overlay=use_staged_metrics_overlay))
    if demo_mode_active():
        return tuple(enrich_community(community, district_item) for district_item in DISTRICTS for community in district_item["communities"])
    return tuple()


def current_community_dataset(*, use_staged_metrics_overlay: bool = True) -> list[dict[str, Any]]:
    return deepcopy(list(_current_community_dataset_cached(use_staged_metrics_overlay)))


def map_communities_payload(
    *,
    district: str | None = None,
    sample_status: str | None = None,
    focus_scope: str | None = None,
    zoom: float | None = None,
    viewport: str | None = None,
) -> dict[str, Any]:
    del zoom, viewport
    dataset = current_community_dataset()
    items: list[dict[str, Any]] = []
    for community in dataset:
        if district not in (None, "", "all") and community["districtId"] != district:
            continue
        if sample_status not in (None, "", "all") and community.get("sampleStatus") != sample_status:
            continue
        if focus_scope == "priority" and community["districtId"] not in priority_districts():
            continue
        if community.get("centerLng") is None or community.get("centerLat") is None:
            continue
        items.append(
            {
                "community_id": community["id"],
                "district_id": community["districtId"],
                "district_name": community["districtName"],
                "name": community["name"],
                "center_lng": community.get("centerLng"),
                "center_lat": community.get("centerLat"),
                "anchor_source": community.get("anchorSource") or community.get("geometrySource"),
                "anchor_quality": community.get("anchorQuality"),
                "anchor_decision_state": community.get("anchorDecisionState"),
                "sample_status": community.get("sampleStatus") or "dictionary_only",
                "sample_status_label": community.get("sampleStatusLabel") or sample_status_label("dictionary_only"),
                "yield_pct": community.get("yield"),
                "sample_size": community.get("sample"),
                "data_freshness": community.get("dataFreshness"),
                "opportunity_score": community.get("score"),
                "building_count": community.get("buildingCount"),
            }
        )
    return {
        "items": items,
        "summary": {
            "communityCount": len(items),
            "activeMetricCount": sum(1 for item in items if item["sample_status"] == "active_metrics"),
            "sparseSampleCount": sum(1 for item in items if item["sample_status"] == "sparse_sample"),
            "dictionaryOnlyCount": sum(1 for item in items if item["sample_status"] == "dictionary_only"),
        },
    }


def anchor_watchlist_payload(
    *,
    district: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    reference_index = reference_catalog_indices()
    community_dataset = {item["id"]: item for item in current_community_dataset()}
    reference_runs = list_reference_runs()
    latest_reference_run = reference_runs[0] if reference_runs else None
    items: list[dict[str, Any]] = []
    for ref in reference_index["communities"].values():
        if district not in (None, "", "all") and ref["districtId"] != district:
            continue
        if ref.get("centerLng") is not None and ref.get("centerLat") is not None:
            continue
        community_item = community_dataset.get(ref["communityId"], {})
        sample_status = community_item.get("sampleStatus") or "dictionary_only"
        candidate_suggestions = list(ref.get("candidateSuggestions") or [])
        top_candidate = candidate_suggestions[0] if candidate_suggestions else None
        priority_score = 100 if ref["districtId"] in priority_districts() else 50
        if sample_status == "active_metrics":
            priority_score += 30
        elif sample_status == "sparse_sample":
            priority_score += 15
        priority_score += min(len(candidate_suggestions), 3) * 3
        items.append(
            {
                "communityId": ref["communityId"],
                "communityName": ref["communityName"],
                "districtId": ref["districtId"],
                "districtName": ref["districtName"],
                "districtShort": ref["districtShort"],
                "sampleStatus": sample_status,
                "sampleStatusLabel": sample_status_label(sample_status),
                "sourceRefs": list(ref.get("sourceRefs") or []),
                "candidateSuggestions": candidate_suggestions,
                "topCandidate": top_candidate,
                "previewCenterLng": ref.get("previewCenterLng"),
                "previewCenterLat": ref.get("previewCenterLat"),
                "previewAnchorSource": ref.get("previewAnchorSource"),
                "previewAnchorQuality": ref.get("previewAnchorQuality"),
                "previewAnchorName": ref.get("previewAnchorName"),
                "previewAnchorAddress": ref.get("previewAnchorAddress"),
                "anchorDecisionState": ref.get("anchorDecisionState") or "pending",
                "latestAnchorReview": deepcopy(ref.get("latestAnchorReview")),
                "referenceRunId": latest_reference_run.get("runId") if latest_reference_run else None,
                "priorityScore": priority_score,
                "priorityLabel": "重点区优先" if ref["districtId"] in priority_districts() else "常规待补",
                "focusScope": "priority" if ref["districtId"] in priority_districts() else "citywide",
            }
        )
    items.sort(
        key=lambda item: (
            -item["priorityScore"],
            item["districtId"],
            item["communityName"],
        )
    )
    return {
        "items": items[:limit],
        "summary": {
            "watchCount": len(items),
            "priorityCount": sum(1 for item in items if item["focusScope"] == "priority"),
            "candidateBackedCount": sum(1 for item in items if item["candidateSuggestions"]),
            "latestAnchorReviewAt": latest_anchor_review_at(
                [item.get("latestAnchorReview") for item in items if item.get("latestAnchorReview")]
            ),
        },
    }


def map_buildings_payload(
    *,
    district: str | None = None,
    focus_scope: str | None = None,
    geometry_quality: str | None = None,
    geo_run_id: str | None = None,
    viewport: str | None = None,
) -> dict[str, Any]:
    del viewport
    payload = build_building_geojson(
        district=district,
        min_yield=0.0,
        max_budget=10_000.0,
        min_samples=0,
        geo_run_id=geo_run_id,
        include_svg_props=True,
    )
    items: list[dict[str, Any]] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        if focus_scope == "priority" and properties.get("district_id") not in priority_districts():
            continue
        if geometry_quality == "real" and properties.get("geometry_source") not in {"database", "database_selected", "imported"}:
            continue
        if geometry_quality == "fallback" and properties.get("geometry_source") in {"database", "database_selected", "imported"}:
            continue
        items.append(feature)
    return {
        "type": "FeatureCollection",
        "name": payload.get("name") or "ShanghaiYieldBuildings",
        "features": items,
        "summary": {
            "buildingCount": len(items),
            "priorityDistricts": priority_districts(),
            "realGeometryCount": sum(
                1
                for feature in items
                if (feature.get("properties") or {}).get("geometry_source") in {"database", "database_selected", "imported"}
            ),
            "fallbackGeometryCount": sum(
                1
                for feature in items
                if (feature.get("properties") or {}).get("geometry_source") not in {"database", "database_selected", "imported"}
            ),
        },
    }


def list_districts(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> list[dict[str, Any]]:
    if database_mode_active():
        return db_district_dataset(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        )
    if staged_mode_active():
        return staged_district_dataset(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        )
    if not demo_mode_active():
        return []
    visible = []
    for district_item in DISTRICTS:
        if district not in (None, "", "all") and district_item["id"] != district:
            continue
        communities = [
            enrich_community(community, district_item)
            for community in district_item["communities"]
            if community_visible(
                community,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            )
        ]
        if communities:
            district_copy = {key: deepcopy(value) for key, value in district_item.items() if key != "communities"}
            district_copy["communities"] = communities
            visible.append(district_copy)
    return visible


def get_community(community_id: str) -> dict[str, Any] | None:
    if database_mode_active():
        community = next((item for item in db_community_dataset() if item["id"] == community_id), None)
        if not community:
            return None
        district = next((item for item in db_district_dataset() if item["id"] == community["districtId"]), None)
        return {
            **community,
            "districtMetrics": {
                "yield": district["yield"] if district else 0,
                "score": district["score"] if district else 0,
                "saleSample": district.get("saleSample", 0) if district else 0,
                "rentSample": district.get("rentSample", 0) if district else 0,
            },
        }
    if staged_mode_active():
        community = next((item for item in staged_community_dataset() if item["id"] == community_id), None)
        if not community:
            return None
        district = next((item for item in staged_district_dataset() if item["id"] == community["districtId"]), None)
        return {
            **community,
            "districtMetrics": {
                "yield": district["yield"] if district else 0,
                "score": district["score"] if district else 0,
                "saleSample": district.get("saleSample", 0) if district else 0,
                "rentSample": district.get("rentSample", 0) if district else 0,
            },
        }
    if not demo_mode_active():
        return None
    for district_item in DISTRICTS:
        for community in district_item["communities"]:
            if community["id"] == community_id:
                enriched = enrich_community(community, district_item)
                return {
                    **enriched,
                    "districtMetrics": {
                        "yield": district_item["yield"],
                        "score": district_item["score"],
                        "saleSample": district_item["saleSample"],
                        "rentSample": district_item["rentSample"],
                    },
                }
    return None


def get_building(building_id: str) -> dict[str, Any] | None:
    if database_mode_active():
        community = next((item for item in db_community_dataset() if any(building["id"] == building_id for building in item.get("buildings", []))), None)
        if not community:
            return None
        district = next((item for item in db_district_dataset() if item["id"] == community["districtId"]), None)
        building = next((item for item in community["buildings"] if item["id"] == building_id), None)
        if not building:
            return None
        avg_price_wan_estimate = round(building.get("saleMedianWan") or community["avgPriceWan"], 1)
        monthly_rent_estimate = round(building.get("rentMedianMonthly") or community["monthlyRent"])
        sample_size_estimate = int(building.get("sampleSize") or community["sample"])
        floor_metrics = [
            {"bucket": "low", "label": "低楼层", "yieldPct": building["low"]},
            {"bucket": "mid", "label": "中楼层", "yieldPct": building["mid"]},
            {"bucket": "high", "label": "高楼层", "yieldPct": building["high"]},
        ]
        score_breakdown = build_score_breakdown(
            building,
            community,
            district or {"yield": 0, "score": 0, "saleSample": 0, "rentSample": 0},
            sample_size_estimate=sample_size_estimate,
            avg_price_wan_estimate=avg_price_wan_estimate,
        )
        floor_curve, focus_floor_no = build_floor_curve(
            {
                **building,
                "score": building["score"],
                "low": building["low"],
                "mid": building["mid"],
                "high": building["high"],
                "yieldAvg": building["yieldAvg"],
                "totalFloors": max(int(building.get("totalFloors") or 1), 1),
            },
            avg_price_wan_estimate=avg_price_wan_estimate,
        )
        top_floors = sorted(
            floor_curve,
            key=lambda item: (item["opportunityScore"], item["yieldPct"], -item["estPriceWan"]),
            reverse=True,
        )[:5]
        return {
            **deepcopy(building),
            "communityYield": community["yield"],
            "communityScore": community["score"],
            "communitySample": community["sample"],
            "avgPriceWanEstimate": avg_price_wan_estimate,
            "monthlyRentEstimate": monthly_rent_estimate,
            "sampleSizeEstimate": sample_size_estimate,
            "yieldSpreadVsCommunity": round(building["yieldAvg"] - community["yield"], 2),
            "bestBucketLabel": floor_bucket_label(building["bestBucket"]),
            "floorMetrics": floor_metrics,
            "scoreBreakdown": score_breakdown,
            "floorCurve": floor_curve,
            "focusFloorNo": focus_floor_no,
            "topFloors": top_floors,
            "dataFreshness": building.get("dataFreshness"),
            "geometrySource": building.get("geometrySource"),
        }
    if staged_mode_active():
        community = next((item for item in staged_community_dataset() if any(building["id"] == building_id for building in item.get("buildings", []))), None)
        if not community:
            return None
        district = next((item for item in staged_district_dataset() if item["id"] == community["districtId"]), None)
        building = next((item for item in community["buildings"] if item["id"] == building_id), None)
        if not building:
            return None
        avg_price_wan_estimate = round(building.get("saleMedianWan") or community["avgPriceWan"], 1)
        monthly_rent_estimate = round(building.get("rentMedianMonthly") or community["monthlyRent"])
        sample_size_estimate = int(building.get("sampleSize") or community["sample"])
        floor_metrics = [
            {"bucket": "low", "label": "低楼层", "yieldPct": building["low"]},
            {"bucket": "mid", "label": "中楼层", "yieldPct": building["mid"]},
            {"bucket": "high", "label": "高楼层", "yieldPct": building["high"]},
        ]
        score_breakdown = build_score_breakdown(
            building,
            community,
            district or {"yield": 0, "score": 0, "saleSample": 0, "rentSample": 0},
            sample_size_estimate=sample_size_estimate,
            avg_price_wan_estimate=avg_price_wan_estimate,
        )
        floor_curve, focus_floor_no = build_floor_curve(
            {
                **building,
                "score": building["score"],
                "low": building["low"],
                "mid": building["mid"],
                "high": building["high"],
                "yieldAvg": building["yieldAvg"],
                "totalFloors": max(int(building.get("totalFloors") or 1), 1),
            },
            avg_price_wan_estimate=avg_price_wan_estimate,
        )
        top_floors = sorted(
            floor_curve,
            key=lambda item: (item["opportunityScore"], item["yieldPct"], -item["estPriceWan"]),
            reverse=True,
        )[:5]
        return {
            **deepcopy(building),
            "communityYield": community["yield"],
            "communityScore": community["score"],
            "communitySample": community["sample"],
            "avgPriceWanEstimate": avg_price_wan_estimate,
            "monthlyRentEstimate": monthly_rent_estimate,
            "sampleSizeEstimate": sample_size_estimate,
            "yieldSpreadVsCommunity": round(building["yieldAvg"] - community["yield"], 2),
            "bestBucketLabel": floor_bucket_label(building["bestBucket"]),
            "floorMetrics": floor_metrics,
            "scoreBreakdown": score_breakdown,
            "floorCurve": floor_curve,
            "focusFloorNo": focus_floor_no,
            "topFloors": top_floors,
            "dataFreshness": building.get("dataFreshness"),
            "geometrySource": building.get("geometrySource"),
        }
    if not demo_mode_active():
        return None
    for district_item in DISTRICTS:
        for community in district_item["communities"]:
            enriched_community = enrich_community(community, district_item)
            for building in enriched_community["buildings"]:
                if building["id"] != building_id:
                    continue

                avg_price_multiplier = 0.91 + building["sequenceNo"] * 0.035
                avg_price_wan_estimate = round(enriched_community["avgPriceWan"] * avg_price_multiplier, 0)
                monthly_rent_estimate = round(avg_price_wan_estimate * 10000 * (building["yieldAvg"] / 100) / 12)
                sample_size_estimate = max(6, round(enriched_community["sample"] / max(1, len(enriched_community["buildings"]))))
                floor_metrics = [
                    {"bucket": "low", "label": "低楼层", "yieldPct": building["low"]},
                    {"bucket": "mid", "label": "中楼层", "yieldPct": building["mid"]},
                    {"bucket": "high", "label": "高楼层", "yieldPct": building["high"]},
                ]
                score_breakdown = build_score_breakdown(
                    building,
                    enriched_community,
                    district_item,
                    sample_size_estimate=sample_size_estimate,
                    avg_price_wan_estimate=avg_price_wan_estimate,
                )
                floor_curve, focus_floor_no = build_floor_curve(
                    building,
                    avg_price_wan_estimate=avg_price_wan_estimate,
                )
                top_floors = sorted(
                    floor_curve,
                    key=lambda item: (item["opportunityScore"], item["yieldPct"], -item["estPriceWan"]),
                    reverse=True,
                )[:5]

                return {
                    **deepcopy(building),
                    "communityYield": enriched_community["yield"],
                    "communityScore": enriched_community["score"],
                    "communitySample": enriched_community["sample"],
                    "avgPriceWanEstimate": avg_price_wan_estimate,
                    "monthlyRentEstimate": monthly_rent_estimate,
                    "sampleSizeEstimate": sample_size_estimate,
                    "yieldSpreadVsCommunity": round(building["yieldAvg"] - enriched_community["yield"], 2),
                    "bestBucketLabel": floor_bucket_label(building["bestBucket"]),
                    "floorMetrics": floor_metrics,
                    "scoreBreakdown": score_breakdown,
                    "floorCurve": floor_curve,
                    "focusFloorNo": focus_floor_no,
                    "topFloors": top_floors,
                }
    return None


def get_floor_detail(building_id: str, floor_no: int) -> dict[str, Any] | None:
    if database_mode_active():
        building = get_building(building_id)
        if not building:
            return None
        floor_item = next((item for item in building["floorCurve"] if item["floorNo"] == floor_no), None)
        if not floor_item:
            return None
        history_payload = db_floor_history(building_id, floor_no)
        latest = (history_payload["timeline"] or [None])[0]
        pair_rows = query_rows(
            """
            SELECT
                p.pair_id,
                p.sale_source,
                p.rent_source,
                p.sale_price_wan,
                p.monthly_rent,
                p.annual_yield_pct,
                p.match_confidence,
                p.normalized_address,
                ir.batch_name,
                ir.created_at
            FROM floor_evidence_pairs p
            JOIN ingestion_runs ir ON ir.run_id = p.ingestion_run_id
            WHERE p.building_id = %s AND p.floor_no = %s
            ORDER BY ir.created_at DESC, p.match_confidence DESC, p.pair_id
            LIMIT 8
            """,
            (building_id, floor_no),
        )
        sample_pairs = [
            {
                "pairId": row.get("pair_id"),
                "unitNo": f"样本 {index + 1}",
                "layout": "待补户型",
                "orientation": "待补朝向",
                "areaSqm": None,
                "saleSourceName": source_name_by_id(row.get("sale_source")),
                "rentSourceName": source_name_by_id(row.get("rent_source")),
                "salePriceWan": row.get("sale_price_wan"),
                "monthlyRent": row.get("monthly_rent"),
                "yieldPct": row.get("annual_yield_pct"),
                "resolutionConfidence": float(row.get("match_confidence") or 0),
                "dedupConfidence": float(row.get("match_confidence") or 0),
                "reviewState": "已归一" if float(row.get("match_confidence") or 0) >= 0.85 else "待复核",
                "normalizedAddress": row.get("normalized_address"),
                "updatedAt": (row.get("created_at").isoformat() if row.get("created_at") else "").replace("T", " ")[:16],
            }
            for index, row in enumerate(pair_rows)
        ]
        queue_items = query_rows(
            """
            SELECT
                ir.external_run_id AS run_id,
                ir.batch_name,
                q.source,
                q.source_listing_id,
                q.raw_text,
                q.parse_status,
                q.confidence_score,
                q.resolution_notes,
                q.review_owner,
                q.reviewed_at
            FROM address_resolution_queue q
            JOIN ingestion_runs ir ON ir.run_id = q.ingestion_run_id
            WHERE q.parsed_building_id = %s AND q.parsed_floor_no = %s
            ORDER BY q.updated_at DESC
            LIMIT 8
            """,
            (building_id, floor_no),
        )
        normalized_queue_items = [
            {
                "queueId": f"{row.get('run_id')}::{row.get('source')}::{row.get('source_listing_id')}",
                "communityId": building["communityId"],
                "buildingId": building_id,
                "buildingNo": building["name"],
                "floorNo": floor_no,
                "sourceId": row.get("source"),
                "rawAddress": row.get("raw_text"),
                "normalizedPath": f"{building['districtName']} / {building['communityName']} / {building['name']} / 待识别单元 / {floor_no}层",
                "status": row.get("parse_status"),
                "confidence": float(row.get("confidence_score") or 0),
                "lastActionAt": (row.get("reviewed_at").isoformat() if row.get("reviewed_at") else "").replace("T", " ")[:16],
                "reviewHint": row.get("resolution_notes") or "等待人工复核。",
                "runId": row.get("run_id"),
                "batchName": row.get("batch_name"),
                "reviewOwner": row.get("review_owner"),
                "reviewedAt": row.get("reviewed_at").isoformat() if row.get("reviewed_at") else None,
            }
            for row in queue_items
        ]
        source_mix_counts: dict[str, int] = {}
        for pair in sample_pairs:
            for source_name in (pair["saleSourceName"], pair["rentSourceName"]):
                source_mix_counts[source_name] = source_mix_counts.get(source_name, 0) + 1
        source_mix = [{"name": key, "count": value} for key, value in sorted(source_mix_counts.items(), key=lambda item: item[1], reverse=True)]
        measured_metrics = (
            {
                "pairCount": latest.get("pairCount"),
                "saleMedianWan": latest.get("saleMedianWan"),
                "rentMedianMonthly": latest.get("rentMedianMonthly"),
                "yieldPct": latest.get("yieldPct"),
                "bestPairConfidence": latest.get("bestPairConfidence"),
            }
            if latest
            else None
        )
        resolution_trace = (
            build_import_resolution_trace(
                building,
                floor_item,
                {
                    "batchName": latest.get("batchName"),
                    "createdAt": latest.get("createdAt"),
                } if latest else {"batchName": "待接入", "createdAt": None},
                normalized_queue_items,
                measured_metrics.get("pairCount", len(sample_pairs)) if measured_metrics else len(sample_pairs),
            )
            if latest
            else build_resolution_trace(building, floor_item, normalized_queue_items)
        )
        return {
            "buildingId": building["id"],
            "buildingName": building["name"],
            "communityId": building["communityId"],
            "communityName": building["communityName"],
            "districtId": building["districtId"],
            "districtName": building["districtName"],
            "floorNo": floor_item["floorNo"],
            "bucket": floor_item["bucket"],
            "bucketLabel": floor_item["bucketLabel"],
            "yieldPct": floor_item["yieldPct"],
            "yieldSpreadVsBuilding": floor_item["yieldSpreadVsBuilding"],
            "estPriceWan": floor_item["estPriceWan"],
            "estMonthlyRent": floor_item["estMonthlyRent"],
            "pricePremiumPct": floor_item["pricePremiumPct"],
            "opportunityScore": floor_item["opportunityScore"],
            "arbitrageTag": floor_item["arbitrageTag"],
            "samplePairs": sample_pairs,
            "sourceMix": source_mix,
            "resolutionTrace": resolution_trace,
            "queueItems": normalized_queue_items,
            "evidenceSource": "imported" if latest else "insufficient_samples",
            "importRun": {"batchName": latest.get("batchName"), "createdAt": latest.get("createdAt")} if latest else None,
            "historyTimeline": history_payload["timeline"],
            "historySummary": history_payload["summary"],
            "measuredMetrics": measured_metrics,
        }
    if staged_mode_active():
        building = get_building(building_id)
        if not building:
            return None
        floor_item = next((item for item in building["floorCurve"] if item["floorNo"] == floor_no), None)
        if not floor_item:
            return None

        queue_items = queue_items_for(building["communityId"], building["name"], floor_no)
        imported_evidence = import_floor_evidence_for(building_id, floor_no)
        history_payload = staged_floor_history(building_id, floor_no)
        if imported_evidence:
            sample_pairs = imported_evidence["samplePairs"]
            queue_items = imported_evidence["queueItems"] or queue_items
            resolution_trace = build_import_resolution_trace(
                building,
                floor_item,
                imported_evidence["runSummary"],
                queue_items,
                imported_evidence["evidence"].get("pair_count", len(sample_pairs)),
            )
            source_mix = imported_evidence["sourceMix"]
            measured_metrics = {
                "pairCount": imported_evidence["evidence"].get("pair_count"),
                "saleMedianWan": imported_evidence["evidence"].get("sale_median_wan"),
                "rentMedianMonthly": imported_evidence["evidence"].get("rent_median_monthly"),
                "yieldPct": imported_evidence["evidence"].get("yield_pct"),
                "bestPairConfidence": imported_evidence["evidence"].get("best_pair_confidence"),
            }
            evidence_source = "imported"
            import_run = imported_evidence["runSummary"]
        else:
            sample_pairs = []
            resolution_trace = build_resolution_trace(building, floor_item, queue_items)
            source_mix = []
            measured_metrics = None
            evidence_source = "insufficient_samples"
            import_run = None
        headline_yield_pct = measured_metrics["yieldPct"] if measured_metrics and measured_metrics.get("yieldPct") is not None else floor_item["yieldPct"]
        headline_price_wan = measured_metrics["saleMedianWan"] if measured_metrics and measured_metrics.get("saleMedianWan") is not None else floor_item["estPriceWan"]
        headline_rent = measured_metrics["rentMedianMonthly"] if measured_metrics and measured_metrics.get("rentMedianMonthly") is not None else floor_item["estMonthlyRent"]

        return {
            "buildingId": building["id"],
            "buildingName": building["name"],
            "communityId": building["communityId"],
            "communityName": building["communityName"],
            "districtId": building["districtId"],
            "districtName": building["districtName"],
            "floorNo": floor_item["floorNo"],
            "bucket": floor_item["bucket"],
            "bucketLabel": floor_item["bucketLabel"],
            "yieldPct": headline_yield_pct,
            "yieldSpreadVsBuilding": round(headline_yield_pct - building["yieldAvg"], 2),
            "estPriceWan": headline_price_wan,
            "estMonthlyRent": headline_rent,
            "pricePremiumPct": floor_item["pricePremiumPct"],
            "opportunityScore": floor_item["opportunityScore"],
            "arbitrageTag": floor_item["arbitrageTag"],
            "samplePairs": sample_pairs,
            "sourceMix": source_mix,
            "resolutionTrace": resolution_trace,
            "queueItems": queue_items,
            "evidenceSource": evidence_source,
            "importRun": import_run,
            "historyTimeline": history_payload["timeline"],
            "historySummary": history_payload["summary"],
            "measuredMetrics": measured_metrics,
        }
    if not demo_mode_active():
        return None
    building = get_building(building_id)
    if not building:
        return None

    floor_item = next((item for item in building["floorCurve"] if item["floorNo"] == floor_no), None)
    if not floor_item:
        return None

    queue_items = queue_items_for(building["communityId"], building["name"], floor_no)
    imported_evidence = import_floor_evidence_for(building_id, floor_no)
    history_payload = import_floor_history_for(building_id, floor_no)
    if imported_evidence:
        sample_pairs = imported_evidence["samplePairs"]
        queue_items = imported_evidence["queueItems"] or queue_items
        resolution_trace = build_import_resolution_trace(
            building,
            floor_item,
            imported_evidence["runSummary"],
            queue_items,
            imported_evidence["evidence"].get("pair_count", len(sample_pairs)),
        )
        source_mix = imported_evidence["sourceMix"]
    else:
        sample_pairs = build_floor_sample_pairs(building, floor_item)
        resolution_trace = build_resolution_trace(building, floor_item, queue_items)
        source_mix: dict[str, int] = {}
        for pair in sample_pairs:
            for source_name in (pair["saleSourceName"], pair["rentSourceName"]):
                source_mix[source_name] = source_mix.get(source_name, 0) + 1
        source_mix = [
            {"name": name, "count": count}
            for name, count in sorted(source_mix.items(), key=lambda item: item[1], reverse=True)
        ]

    return {
        "buildingId": building["id"],
        "buildingName": building["name"],
        "communityId": building["communityId"],
        "communityName": building["communityName"],
        "districtId": building["districtId"],
        "districtName": building["districtName"],
        "floorNo": floor_item["floorNo"],
        "bucket": floor_item["bucket"],
        "bucketLabel": floor_item["bucketLabel"],
        "yieldPct": floor_item["yieldPct"],
        "yieldSpreadVsBuilding": floor_item["yieldSpreadVsBuilding"],
        "estPriceWan": floor_item["estPriceWan"],
        "estMonthlyRent": floor_item["estMonthlyRent"],
        "pricePremiumPct": floor_item["pricePremiumPct"],
        "opportunityScore": floor_item["opportunityScore"],
        "arbitrageTag": floor_item["arbitrageTag"],
        "samplePairs": sample_pairs,
        "sourceMix": source_mix,
        "resolutionTrace": resolution_trace,
        "queueItems": queue_items,
        "evidenceSource": "imported" if imported_evidence else "simulated",
        "importRun": imported_evidence["runSummary"] if imported_evidence else None,
        "historyTimeline": history_payload["timeline"],
        "historySummary": history_payload["summary"],
        "measuredMetrics": (
            {
                "pairCount": imported_evidence["evidence"].get("pair_count"),
                "saleMedianWan": imported_evidence["evidence"].get("sale_median_wan"),
                "rentMedianMonthly": imported_evidence["evidence"].get("rent_median_monthly"),
                "yieldPct": imported_evidence["evidence"].get("yield_pct"),
                "bestPairConfidence": imported_evidence["evidence"].get("best_pair_confidence"),
            }
            if imported_evidence
            else None
        ),
    }


def summarize(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> dict[str, Any]:
    communities = flatten_communities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    )
    if not communities:
        return {
            "communityCount": 0,
            "avgYield": 0,
            "avgBudget": 0,
            "avgMonthlyRent": 0,
            "bestScore": 0,
        }

    return {
        "communityCount": len(communities),
        "avgYield": round(sum(item["yield"] for item in communities) / len(communities), 2),
        "avgBudget": round(sum(item["avgPriceWan"] for item in communities) / len(communities), 0),
        "avgMonthlyRent": round(sum(item["monthlyRent"] for item in communities) / len(communities), 0),
        "bestScore": max(item["score"] for item in communities),
    }


def opportunities(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    min_score: int = 0,
) -> list[dict[str, Any]]:
    communities = flatten_communities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    )
    return sorted(
        [
            community
            for community in communities
            if community["score"] >= min_score
            and community.get("sampleStatus") in {"active_metrics", "sparse_sample"}
        ],
        key=lambda item: (item["score"], item["yield"]),
        reverse=True,
    )


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
    run_ids = [geo_run_id] if geo_run_id else [run_summary["runId"] for run_summary in list_geo_asset_runs()]
    for run_id in run_ids:
        detail = geo_asset_run_detail_full(run_id)
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
    for community in flatten_communities(
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
    return {"type": "FeatureCollection", "name": "ShanghaiYieldAtlas", "features": features}


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
    for community in flatten_communities(
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
    return {"type": "FeatureCollection", "name": "ShanghaiYieldBuildings", "features": features}


def build_kml(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
) -> str:
    placemarks = []
    for community in flatten_communities(
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
    <name>Shanghai Yield Atlas</name>
{joined}
  </Document>
</kml>
"""


def floor_watchlist_point(item: dict[str, Any]) -> tuple[float, float]:
    community = get_community(item["communityId"])
    building = get_building(item["buildingId"])
    if not community:
        return 121.4737, 31.2304

    floor_no = max(int(item.get("floorNo") or 1), 1)
    x, y = floor_svg_point(community, building or {"totalFloors": floor_no, "sequenceNo": 1}, floor_no)
    return normalize_svg_to_lon_lat(x, y)


def geo_task_watchlist_point(item: dict[str, Any]) -> tuple[float, float]:
    community = get_community(item.get("communityId"))
    building = get_building(item.get("buildingId")) if item.get("buildingId") else None
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
        community = get_community(item.get("communityId"))
        building = get_building(item.get("buildingId")) if item.get("buildingId") else None
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
    imported_assets = imported_building_geo_asset_index(geo_run_id)
    for item in geo_task_watchlist(
        district=district,
        geo_run_id=geo_run_id,
        limit=limit,
        include_resolved=include_resolved,
    ):
        community = get_community(item.get("communityId"))
        building = get_building(item.get("buildingId")) if item.get("buildingId") else None
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
    for item in floor_watchlist(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        limit=limit,
    ):
        community = get_community(item["communityId"])
        building = get_building(item["buildingId"])
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
    <name>Shanghai Yield Floor Watchlist</name>
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
