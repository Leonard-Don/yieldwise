"""
Run-state aggregation for the backstage research tool.

Phase 7a extraction from api/service.py — covers reference / import /
metrics / geo_asset run lists and the runtime_data_state mode summary.
Re-exported from api.service for back-compat.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..persistence import database_has_real_data, postgres_data_snapshot, postgres_runtime_status, query_rows
from ..provider_adapters import mock_enabled, provider_readiness_snapshot


# Shared utilities are imported lazily inside functions to avoid the
# api.service ↔ api.backstage.runs circular import at module load time.


def import_run_summary_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    summary = manifest.get("summary", {})
    return {
        "runId": manifest.get("run_id"),
        "providerId": manifest.get("provider_id"),
        "batchName": manifest.get("batch_name") or manifest.get("run_id"),
        "createdAt": manifest.get("created_at"),
        "outputDir": str(manifest_path.parent),
        "resolvedRate": summary.get("resolved_rate", 0.0),
        "resolvedCount": summary.get("resolved_count", 0),
        "reviewCount": summary.get("review_count", 0),
        "matchingCount": summary.get("matching_count", 0),
        "pairCount": summary.get("floor_pair_count", 0),
        "evidenceCount": summary.get("floor_evidence_count", 0),
        "manifestPath": str(manifest_path),
        "storageMode": "file",
    }


def db_import_run_rows() -> list[dict[str, Any]]:
    snapshot = postgres_data_snapshot()
    if not snapshot.get("databaseReadable"):
        return []
    try:
        return query_rows(
            """
            SELECT
                external_run_id AS run_id,
                provider_id,
                batch_name,
                output_manifest_path,
                summary_json,
                created_at,
                completed_at
            FROM ingestion_runs
            WHERE business_scope = 'sale_rent'
            ORDER BY created_at DESC, run_id DESC
            """
        )
    except Exception:
        return []


def import_run_summary_from_db_row(row: dict[str, Any]) -> dict[str, Any]:
    from ..service import db_summary_json, existing_output_manifest_path

    summary = db_summary_json(row.get("summary_json"))
    manifest_path = existing_output_manifest_path(row.get("output_manifest_path"))
    created_at = row.get("created_at")
    return {
        "runId": row.get("run_id"),
        "providerId": row.get("provider_id"),
        "batchName": row.get("batch_name") or row.get("run_id"),
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        "outputDir": str(manifest_path.parent) if manifest_path else None,
        "resolvedRate": summary.get("resolved_rate", 0.0),
        "resolvedCount": summary.get("resolved_count", 0),
        "reviewCount": summary.get("review_count", 0),
        "matchingCount": summary.get("matching_count", 0),
        "pairCount": summary.get("floor_pair_count", 0),
        "evidenceCount": summary.get("floor_evidence_count", 0),
        "manifestPath": str(manifest_path) if manifest_path else row.get("output_manifest_path"),
        "storageMode": "database+file" if manifest_path else "database",
    }


@lru_cache(maxsize=1)
def _list_import_runs_cached() -> tuple[dict[str, Any], ...]:
    from ..service import comparable_created_at_value, import_manifest_paths, read_json_file

    runs_by_id: dict[str, dict[str, Any]] = {}
    for row in db_import_run_rows():
        run_summary = import_run_summary_from_db_row(row)
        if run_summary.get("runId"):
            runs_by_id[run_summary["runId"]] = run_summary
    for manifest_path in import_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            continue
        run_summary = import_run_summary_from_manifest(manifest, manifest_path)
        existing = runs_by_id.get(run_summary["runId"])
        if existing:
            existing["outputDir"] = existing.get("outputDir") or run_summary.get("outputDir")
            existing["manifestPath"] = existing.get("manifestPath") or run_summary.get("manifestPath")
            existing["storageMode"] = "database+file"
            continue
        runs_by_id[run_summary["runId"]] = run_summary
    runs = list(runs_by_id.values())
    runs.sort(key=lambda item: comparable_created_at_value(item.get("createdAt")), reverse=True)
    return tuple(runs)


def list_import_runs() -> list[dict[str, Any]]:
    return deepcopy(list(_list_import_runs_cached()))


def reference_run_summary_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    summary = manifest.get("summary", {})
    return {
        "runId": manifest.get("run_id"),
        "providerId": manifest.get("provider_id"),
        "batchName": manifest.get("batch_name") or manifest.get("run_id"),
        "createdAt": manifest.get("created_at"),
        "outputDir": str(manifest_path.parent),
        "districtCount": summary.get("district_count", 0),
        "communityCount": summary.get("community_count", 0),
        "buildingCount": summary.get("building_count", 0),
        "anchoredCommunityCount": summary.get("anchored_community_count", 0),
        "anchoredBuildingCount": summary.get("anchored_building_count", 0),
        "manifestPath": str(manifest_path),
        "storageMode": "file",
    }


def db_reference_run_rows() -> list[dict[str, Any]]:
    snapshot = postgres_data_snapshot()
    if not snapshot.get("databaseReadable"):
        return []
    try:
        return query_rows(
            """
            SELECT
                external_run_id AS run_id,
                provider_id,
                batch_name,
                output_manifest_path,
                summary_json,
                created_at,
                completed_at
            FROM ingestion_runs
            WHERE business_scope = 'dictionary'
            ORDER BY created_at DESC, run_id DESC
            """
        )
    except Exception:
        return []


def reference_run_summary_from_db_row(row: dict[str, Any]) -> dict[str, Any]:
    from ..service import db_summary_json, existing_output_manifest_path

    summary = db_summary_json(row.get("summary_json"))
    manifest_path = existing_output_manifest_path(row.get("output_manifest_path"))
    created_at = row.get("created_at")
    return {
        "runId": row.get("run_id"),
        "providerId": row.get("provider_id"),
        "batchName": row.get("batch_name") or row.get("run_id"),
        "createdAt": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        "outputDir": str(manifest_path.parent) if manifest_path else None,
        "districtCount": summary.get("district_count", 0),
        "communityCount": summary.get("community_count", 0),
        "buildingCount": summary.get("building_count", 0),
        "anchoredCommunityCount": summary.get("anchored_community_count", 0),
        "anchoredBuildingCount": summary.get("anchored_building_count", 0),
        "manifestPath": str(manifest_path) if manifest_path else row.get("output_manifest_path"),
        "storageMode": "database+file" if manifest_path else "database",
    }


@lru_cache(maxsize=1)
def _list_reference_runs_cached() -> tuple[dict[str, Any], ...]:
    from ..service import comparable_created_at_value, read_json_file, reference_manifest_paths

    runs_by_id: dict[str, dict[str, Any]] = {}
    for row in db_reference_run_rows():
        run_summary = reference_run_summary_from_db_row(row)
        if run_summary.get("runId"):
            runs_by_id[run_summary["runId"]] = run_summary
    for manifest_path in reference_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            continue
        run_summary = reference_run_summary_from_manifest(manifest, manifest_path)
        existing = runs_by_id.get(run_summary["runId"])
        if existing:
            existing["outputDir"] = existing.get("outputDir") or run_summary.get("outputDir")
            existing["manifestPath"] = existing.get("manifestPath") or run_summary.get("manifestPath")
            existing["storageMode"] = "database+file"
            continue
        runs_by_id[run_summary["runId"]] = run_summary
    runs = list(runs_by_id.values())
    runs.sort(key=lambda item: comparable_created_at_value(item.get("createdAt")), reverse=True)
    return tuple(runs)


def list_reference_runs() -> list[dict[str, Any]]:
    return deepcopy(list(_list_reference_runs_cached()))


def metrics_run_summary_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    summary = manifest.get("summary", {})
    return {
        "runId": manifest.get("run_id"),
        "batchName": manifest.get("batch_name") or manifest.get("run_id"),
        "createdAt": manifest.get("created_at"),
        "snapshotDate": manifest.get("snapshot_date"),
        "communityMetricCount": summary.get("community_metric_count", 0),
        "buildingFloorMetricCount": summary.get("building_floor_metric_count", 0),
        "communityCoverageCount": summary.get("community_coverage_count", 0),
        "buildingCoverageCount": summary.get("building_coverage_count", 0),
        "outputDir": str(manifest_path.parent),
        "manifestPath": str(manifest_path),
        "storageMode": "file",
        "source": "file",
    }


@lru_cache(maxsize=1)
def _list_metrics_runs_cached() -> tuple[dict[str, Any], ...]:
    from ..service import comparable_created_at_value, metrics_manifest_paths, read_json_file

    runs: list[dict[str, Any]] = []
    for manifest_path in metrics_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            continue
        runs.append(metrics_run_summary_from_manifest(manifest, manifest_path))
    runs.sort(key=lambda item: comparable_created_at_value(item.get("createdAt")), reverse=True)
    return tuple(runs)


def list_metrics_runs() -> list[dict[str, Any]]:
    return deepcopy(list(_list_metrics_runs_cached()))


def geo_asset_run_summary_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    summary = manifest.get("summary", {})
    return {
        "runId": manifest.get("run_id"),
        "providerId": manifest.get("provider_id"),
        "batchName": manifest.get("batch_name") or manifest.get("run_id"),
        "assetType": manifest.get("asset_type", "building_footprint"),
        "createdAt": manifest.get("created_at"),
        "outputDir": str(manifest_path.parent),
        "featureCount": summary.get("feature_count", 0),
        "resolvedBuildingCount": summary.get("resolved_building_count", 0),
        "unresolvedFeatureCount": summary.get("unresolved_feature_count", 0),
        "communityCount": summary.get("community_count", 0),
        "coveragePct": summary.get("coverage_pct", 0.0),
        "taskCount": summary.get("coverage_task_count", 0),
        "openTaskCount": summary.get("open_task_count", 0),
        "reviewTaskCount": summary.get("review_task_count", 0),
        "captureTaskCount": summary.get("capture_task_count", 0),
        "manifestPath": str(manifest_path),
        "storageMode": "file",
    }


def db_geo_asset_run_rows() -> list[dict[str, Any]]:
    snapshot = postgres_data_snapshot()
    if not snapshot.get("databaseReadable"):
        return []
    try:
        return query_rows(
            """
            SELECT
                external_run_id AS run_id,
                provider_id,
                batch_name,
                output_manifest_path,
                summary_json,
                created_at,
                completed_at
            FROM ingestion_runs
            WHERE business_scope = 'geo_assets'
            ORDER BY created_at DESC, run_id DESC
            """
        )
    except Exception:
        return []


def geo_asset_run_summary_from_db_row(row: dict[str, Any]) -> dict[str, Any]:
    from ..service import db_summary_json, existing_output_manifest_path

    summary = db_summary_json(row.get("summary_json"))
    manifest_path = existing_output_manifest_path(row.get("output_manifest_path"))
    created_at = row.get("created_at")
    return {
        "runId": row.get("run_id"),
        "providerId": row.get("provider_id"),
        "batchName": row.get("batch_name") or row.get("run_id"),
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
        "manifestPath": str(manifest_path) if manifest_path else row.get("output_manifest_path"),
        "storageMode": "database+file" if manifest_path else "database",
    }


@lru_cache(maxsize=1)
def _list_geo_asset_runs_cached() -> tuple[dict[str, Any], ...]:
    from ..service import comparable_created_at_value, geo_asset_manifest_paths, read_json_file

    runs_by_id: dict[str, dict[str, Any]] = {}
    for row in db_geo_asset_run_rows():
        run_summary = geo_asset_run_summary_from_db_row(row)
        if run_summary.get("runId"):
            runs_by_id[run_summary["runId"]] = run_summary
    for manifest_path in geo_asset_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            continue
        run_summary = geo_asset_run_summary_from_manifest(manifest, manifest_path)
        existing = runs_by_id.get(run_summary["runId"])
        if existing:
            existing["outputDir"] = existing.get("outputDir") or run_summary.get("outputDir")
            existing["manifestPath"] = existing.get("manifestPath") or run_summary.get("manifestPath")
            existing["storageMode"] = "database+file"
            continue
        runs_by_id[run_summary["runId"]] = run_summary
    runs = list(runs_by_id.values())
    runs.sort(key=lambda item: comparable_created_at_value(item.get("createdAt")), reverse=True)
    return tuple(runs)


def list_geo_asset_runs() -> list[dict[str, Any]]:
    return deepcopy(list(_list_geo_asset_runs_cached()))


@lru_cache(maxsize=1)
def _runtime_data_state_cached() -> dict[str, Any]:
    postgres_status = postgres_runtime_status()
    db_snapshot = postgres_data_snapshot()
    staged_reference_runs = list_reference_runs()
    staged_import_runs = list_import_runs()
    staged_geo_runs = list_geo_asset_runs()
    staged_metrics_runs = list_metrics_runs()
    database_connected = bool(db_snapshot.get("databaseConnected"))
    database_readable = bool(db_snapshot.get("databaseReadable"))
    database_seeded = bool(db_snapshot.get("databaseSeeded"))
    has_real_data = database_has_real_data()
    active_mode = (
        "database"
        if database_seeded
        else "staged"
        if (staged_reference_runs or staged_import_runs or staged_geo_runs)
        else "mock"
        if mock_enabled()
        else "empty"
    )
    return {
        **postgres_status,
        "mockEnabled": mock_enabled(),
        "activeDataMode": active_mode,
        "hasRealData": has_real_data,
        "databaseConnected": database_connected,
        "databaseReadable": database_readable,
        "databaseSeeded": database_seeded,
        "latestBootstrapAt": db_snapshot.get("latestBootstrapAt"),
        "databaseSnapshot": db_snapshot,
        "stagedReferenceRunCount": len(staged_reference_runs),
        "stagedImportRunCount": len(staged_import_runs),
        "stagedGeoRunCount": len(staged_geo_runs),
        "stagedMetricsRunCount": len(staged_metrics_runs),
        "stagedArtifactsPresent": bool(staged_reference_runs or staged_import_runs or staged_geo_runs or staged_metrics_runs),
        "providerReadiness": provider_readiness_snapshot(
            staged_listing_runs=len(staged_import_runs) + len(staged_reference_runs),
            staged_geometry_runs=len(staged_geo_runs),
            has_real_data=has_real_data,
        ),
    }


def runtime_data_state() -> dict[str, Any]:
    return deepcopy(_runtime_data_state_cached())


def database_mode_active() -> bool:
    return runtime_data_state()["activeDataMode"] == "database"


def demo_mode_active() -> bool:
    return runtime_data_state()["activeDataMode"] == "mock"


def staged_mode_active() -> bool:
    return runtime_data_state()["activeDataMode"] == "staged"
