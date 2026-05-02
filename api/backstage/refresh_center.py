"""
Refresh-center readiness and dry-run reporting for the backstage workbench.

This module keeps the "can I safely refresh/import now?" decision close to
ops-facing run metadata without growing api.service.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .runs import list_geo_asset_runs, list_import_runs, list_metrics_runs, list_reference_runs, runtime_data_state


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "tmp" / "refresh-reports"
LOW_CONFIDENCE_THRESHOLD = 0.72
LOW_PAIR_COUNT_THRESHOLD = 1
LOW_YIELD_PCT = 1.5
HIGH_YIELD_PCT = 8.0


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _latest(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    return items[0] if items else None


def _run_ref(run: dict[str, Any] | None) -> dict[str, Any] | None:
    if not run:
        return None
    return {
        "runId": run.get("runId"),
        "batchName": run.get("batchName"),
        "createdAt": run.get("createdAt"),
        "providerId": run.get("providerId"),
        "storageMode": run.get("storageMode"),
    }


def _check(check_id: str, label: str, status: str, detail: str, next_action: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "detail": detail,
        "nextAction": next_action,
    }


def _plan_step(
    step: str,
    label: str,
    run: dict[str, Any] | None,
    *,
    required: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    if run:
        status = "ready"
    elif required:
        status = "blocked"
    else:
        status = "skipped"
    return {
        "step": step,
        "label": label,
        "status": status,
        "runId": run.get("runId") if run else None,
        "batchName": run.get("batchName") if run else None,
        "createdAt": run.get("createdAt") if run else None,
        "reason": reason if reason else ("已选择最新批次。" if run else "当前没有可用批次。"),
    }


def _count_open_geo_tasks(detail: dict[str, Any] | None) -> dict[str, int]:
    if not detail:
        return {
            "taskCount": 0,
            "openTaskCount": 0,
            "criticalOpenTaskCount": 0,
            "watchlistLinkedTaskCount": 0,
            "workOrderCount": 0,
            "openWorkOrderCount": 0,
        }
    task_summary = detail.get("taskSummary") or {}
    work_order_summary = detail.get("workOrderSummary") or {}
    return {
        "taskCount": int(task_summary.get("taskCount") or 0),
        "openTaskCount": int(task_summary.get("openTaskCount") or 0),
        "criticalOpenTaskCount": int(task_summary.get("criticalOpenTaskCount") or 0),
        "watchlistLinkedTaskCount": int(task_summary.get("watchlistLinkedTaskCount") or 0),
        "workOrderCount": int(work_order_summary.get("workOrderCount") or 0),
        "openWorkOrderCount": int(work_order_summary.get("openWorkOrderCount") or 0),
    }


def geometry_qa_summary(geo_detail: dict[str, Any] | None, latest_geo_run: dict[str, Any] | None) -> dict[str, Any]:
    counts = _count_open_geo_tasks(geo_detail)
    if latest_geo_run and not geo_detail:
        counts.update(
            {
                "taskCount": int(latest_geo_run.get("taskCount") or 0),
                "openTaskCount": int(latest_geo_run.get("openTaskCount") or 0),
            }
        )
    coverage = geo_detail.get("coverage") if geo_detail else {}
    coverage_pct = (
        coverage.get("catalogCoveragePct")
        if isinstance(coverage, dict) and coverage.get("catalogCoveragePct") is not None
        else (latest_geo_run or {}).get("coveragePct")
    )
    open_count = counts["openTaskCount"]
    critical_count = counts["criticalOpenTaskCount"]
    status = "blocked" if critical_count else "warn" if open_count else "ok"
    return {
        "status": status,
        "run": _run_ref(latest_geo_run),
        "coveragePct": round(float(coverage_pct or 0), 1),
        "catalogBuildingCount": int((coverage or {}).get("catalogBuildingCount") or 0) if isinstance(coverage, dict) else 0,
        "resolvedBuildingCount": int(
            ((coverage or {}).get("resolvedBuildingCount") if isinstance(coverage, dict) else None)
            or (latest_geo_run or {}).get("resolvedBuildingCount")
            or 0
        ),
        "missingBuildingCount": int((coverage or {}).get("missingBuildingCount") or 0) if isinstance(coverage, dict) else 0,
        "taskCount": counts["taskCount"],
        "openTaskCount": open_count,
        "criticalOpenTaskCount": critical_count,
        "watchlistLinkedTaskCount": counts["watchlistLinkedTaskCount"],
        "workOrderCount": counts["workOrderCount"],
        "openWorkOrderCount": counts["openWorkOrderCount"],
        "qaFields": [
            {
                "id": "coordinateCorrection",
                "label": "坐标系校正",
                "status": "ready" if latest_geo_run else "waiting",
                "detail": "几何批次统一进入 GCJ-02 / WGS-84 导出口径检查。",
            },
            {
                "id": "qualityScore",
                "label": "质量评分",
                "status": "warn" if open_count else "ready",
                "detail": "打开任务会压低该批次质量分，优先处理榜单关联与紧急任务。",
            },
            {
                "id": "gisReturn",
                "label": "GIS 回传",
                "status": "ready" if counts["workOrderCount"] else "waiting",
                "detail": "工单状态可作为下一轮 footprint 回传与验收闭环。",
            },
        ],
    }


def _evidence_label(item: dict[str, Any]) -> str:
    parts = [
        item.get("community_name") or item.get("communityName") or item.get("community_id") or item.get("communityId"),
        item.get("building_name") or item.get("buildingName") or item.get("building_id") or item.get("buildingId"),
    ]
    floor_no = item.get("floor_no", item.get("floorNo"))
    if floor_no is not None:
        parts.append(f"{floor_no}层")
    return " · ".join(str(part) for part in parts if part) or "未标注楼层证据"


def _anomaly_filter(
    filter_id: str,
    label: str,
    count: int,
    *,
    status: str | None = None,
    threshold: str,
    action: str,
    examples: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved_status = status or ("warn" if count else "ok")
    return {
        "id": filter_id,
        "label": label,
        "count": int(count),
        "status": resolved_status,
        "threshold": threshold,
        "action": action,
        "examples": examples or [],
    }


def summarize_import_anomaly_filters(import_detail: dict[str, Any] | None) -> dict[str, Any]:
    if not import_detail:
        return {
            "status": "waiting",
            "run": None,
            "totalCandidateCount": 0,
            "filters": [
                _anomaly_filter(
                    "review_queue",
                    "地址复核队列",
                    0,
                    status="waiting",
                    threshold="parse_status != resolved",
                    action="等待首个 import run 后再打开复核队列。",
                )
            ],
        }

    review_queue = import_detail.get("reviewQueue") or []
    attention = import_detail.get("attention") or {}
    floor_evidence = import_detail.get("floorEvidence") or []
    low_confidence_pairs = attention.get("low_confidence_pairs") or []

    low_pair_examples: list[dict[str, Any]] = []
    low_confidence_floor_examples: list[dict[str, Any]] = []
    yield_outlier_examples: list[dict[str, Any]] = []
    for item in floor_evidence:
        pair_count = int(item.get("pair_count") or item.get("pairCount") or 0)
        confidence = float(item.get("best_pair_confidence") or item.get("bestPairConfidence") or 0)
        yield_pct = float(item.get("yield_pct") or item.get("yieldPct") or 0)
        common = {
            "label": _evidence_label(item),
            "yieldPct": round(yield_pct, 2),
            "pairCount": pair_count,
            "bestPairConfidence": round(confidence, 3),
        }
        if pair_count <= LOW_PAIR_COUNT_THRESHOLD:
            low_pair_examples.append(common)
        if confidence and confidence < LOW_CONFIDENCE_THRESHOLD:
            low_confidence_floor_examples.append(common)
        if yield_pct and (yield_pct < LOW_YIELD_PCT or yield_pct > HIGH_YIELD_PCT):
            yield_outlier_examples.append(common)

    filters = [
        _anomaly_filter(
            "review_queue",
            "地址复核队列",
            len(review_queue),
            threshold="parse_status != resolved",
            action="先关闭 needs_review / matching，再进入数据库主读或对外汇报。",
            examples=[
                {
                    "label": item.get("normalizedPath") or item.get("rawText") or item.get("queueId"),
                    "status": item.get("status"),
                    "confidence": item.get("confidence"),
                }
                for item in review_queue[:6]
            ],
        ),
        _anomaly_filter(
            "low_confidence_pairs",
            "低置信样本配对",
            len(low_confidence_pairs),
            threshold=f"match_confidence < {LOW_CONFIDENCE_THRESHOLD}",
            action="回到 Import Detail 检查 sale/rent 是否同楼栋同楼层。",
            examples=[
                {
                    "label": item.get("normalized_address") or item.get("pair_id"),
                    "matchConfidence": item.get("match_confidence"),
                }
                for item in low_confidence_pairs[:6]
            ],
        ),
        _anomaly_filter(
            "single_pair_floors",
            "单样本楼层",
            len(low_pair_examples),
            threshold=f"pair_count <= {LOW_PAIR_COUNT_THRESHOLD}",
            action="把这些楼层放入公开页采样或授权批次补样。",
            examples=low_pair_examples[:6],
        ),
        _anomaly_filter(
            "low_confidence_floors",
            "楼层最佳配对偏低",
            len(low_confidence_floor_examples),
            threshold=f"best_pair_confidence < {LOW_CONFIDENCE_THRESHOLD}",
            action="优先复核楼栋、单元和楼层归一。",
            examples=low_confidence_floor_examples[:6],
        ),
        _anomaly_filter(
            "yield_outliers",
            "回报率异常值",
            len(yield_outlier_examples),
            threshold=f"yield_pct < {LOW_YIELD_PCT} 或 > {HIGH_YIELD_PCT}",
            action="核对总价、月租和面积口径，必要时标记豁免。",
            examples=yield_outlier_examples[:6],
        ),
    ]
    total = sum(item["count"] for item in filters)
    status = "warn" if total else "ok"
    return {
        "status": status,
        "run": _run_ref(import_detail),
        "totalCandidateCount": total,
        "filters": filters,
    }


def latest_import_anomaly_detail(latest_import: dict[str, Any] | None) -> dict[str, Any] | None:
    if not latest_import:
        return None
    from ..service import (
        _import_run_floor_evidence_cached,
        import_manifest_path_for_run,
        import_run_queue_rows,
        read_json_file,
    )

    run_id = str(latest_import.get("runId") or "")
    evidence_payload = _import_run_floor_evidence_cached(run_id) or {}
    manifest = read_json_file(import_manifest_path_for_run(run_id)) or {}
    queue_rows = import_run_queue_rows(latest_import)
    return {
        **latest_import,
        "attention": manifest.get("attention") or {},
        "reviewQueue": [
            {
                "queueId": f"{latest_import.get('runId')}::{item.get('source')}::{item.get('source_listing_id')}",
                "normalizedPath": item.get("normalized_address") or item.get("raw_text") or item.get("source_listing_id"),
                "status": item.get("parse_status"),
                "confidence": item.get("confidence") or item.get("match_confidence"),
            }
            for item in queue_rows
            if item.get("parse_status") != "resolved"
        ],
        "floorEvidence": evidence_payload.get("floorEvidence") or [],
    }


def build_refresh_center_report() -> dict[str, Any]:
    runtime = runtime_data_state()
    reference_runs = list_reference_runs()
    import_runs = list_import_runs()
    geo_runs = list_geo_asset_runs()
    metrics_runs = list_metrics_runs()
    latest_reference = _latest(reference_runs)
    latest_import = _latest(import_runs)
    latest_geo = _latest(geo_runs)
    latest_metrics = _latest(metrics_runs)
    import_detail = latest_import_anomaly_detail(latest_import)
    geo_detail = None
    anomaly_filters = summarize_import_anomaly_filters(import_detail)
    geometry_qa = geometry_qa_summary(geo_detail, latest_geo)

    postgres_ready = bool(runtime.get("hasPostgresDsn"))
    database_connected = bool(runtime.get("databaseConnected"))
    database_seeded = bool(runtime.get("databaseSeeded"))
    can_bootstrap = bool(postgres_ready and latest_reference)
    can_refresh_staged = bool(latest_reference or latest_import)
    can_write_metrics = bool(postgres_ready and database_connected and database_seeded)

    dry_run_checks = [
        _check(
            "reference_run",
            "主档批次",
            "ok" if latest_reference else "blocker",
            f"最新 reference run: {latest_reference['batchName']}" if latest_reference else "没有 reference run。",
            "先导入小区 / 楼栋主档。" if not latest_reference else "可作为本轮引导基线。",
        ),
        _check(
            "listing_run",
            "样本批次",
            "ok" if latest_import else "warn",
            f"最新 import run: {latest_import['batchName']}" if latest_import else "没有 sale/rent import run。",
            "补一轮授权离线样本或公开页采样。" if not latest_import else "可进入异常过滤与指标刷新。",
        ),
        _check(
            "geo_run",
            "几何批次",
            "ok" if latest_geo and not geometry_qa["criticalOpenTaskCount"] else "warn" if latest_geo else "warn",
            f"覆盖 {geometry_qa['coveragePct']}%，打开任务 {geometry_qa['openTaskCount']}。"
            if latest_geo
            else "没有独立几何批次。",
            "处理紧急几何任务。" if geometry_qa["criticalOpenTaskCount"] else "可继续用最新几何口径。",
        ),
        _check(
            "postgres",
            "PostgreSQL 写库",
            "ok" if can_write_metrics else "warn" if postgres_ready else "info",
            "数据库已可写入 metrics。" if can_write_metrics else "当前只能稳定刷新 staged 口径。",
            "配置 POSTGRES_DSN 并完成 Bootstrap。" if not can_write_metrics else "可同步 PostgreSQL。",
        ),
        _check(
            "anomaly_filters",
            "异常过滤",
            "warn" if anomaly_filters["totalCandidateCount"] else "ok",
            f"发现 {anomaly_filters['totalCandidateCount']} 个候选异常。",
            "先处理 review queue、低置信配对和单样本楼层。" if anomaly_filters["totalCandidateCount"] else "当前没有阻断级样本异常。",
        ),
        _check(
            "mock_policy",
            "Demo 回退",
            "warn" if runtime.get("activeDataMode") == "mock" else "ok",
            "当前正在使用 Demo Mock。" if runtime.get("activeDataMode") == "mock" else f"当前数据模式: {runtime.get('activeDataMode')}",
            "只在显式演示时开启 Mock。" if runtime.get("activeDataMode") == "mock" else "继续保持真实 / staged 口径。",
        ),
    ]

    refresh_plan = [
        _plan_step("reference", "Reference 主档", latest_reference, required=True),
        _plan_step("import", "Sale/Rent 样本", latest_import, reason="没有样本批次时只可做主档引导。"),
        _plan_step("geo", "楼栋几何", latest_geo, reason="没有几何批次时地图会退回推导 footprint。"),
        _plan_step(
            "metrics",
            "指标快照",
            latest_metrics,
            reason="没有历史快照时，本轮会生成新的 staged metrics run。",
        ),
    ]
    status = (
        "blocked"
        if any(item["status"] == "blocker" for item in dry_run_checks)
        else "needs_review"
        if any(item["status"] == "warn" for item in dry_run_checks)
        else "ready"
    )
    generated_at = _now_iso()
    return {
        "status": status,
        "generatedAt": generated_at,
        "persisted": False,
        "reportPath": None,
        "selectedRuns": {
            "reference": _run_ref(latest_reference),
            "import": _run_ref(latest_import),
            "geo": _run_ref(latest_geo),
            "metrics": _run_ref(latest_metrics),
        },
        "readiness": {
            "activeDataMode": runtime.get("activeDataMode"),
            "mockEnabled": bool(runtime.get("mockEnabled")),
            "postgresReady": postgres_ready,
            "databaseConnected": database_connected,
            "databaseSeeded": database_seeded,
            "canBootstrap": can_bootstrap,
            "canRefreshStaged": can_refresh_staged,
            "canWriteMetricsToPostgres": can_write_metrics,
            "stagedReferenceRunCount": int(runtime.get("stagedReferenceRunCount") or 0),
            "stagedImportRunCount": int(runtime.get("stagedImportRunCount") or 0),
            "stagedGeoRunCount": int(runtime.get("stagedGeoRunCount") or 0),
            "stagedMetricsRunCount": int(runtime.get("stagedMetricsRunCount") or 0),
        },
        "dryRunChecks": dry_run_checks,
        "refreshPlan": refresh_plan,
        "geometryQa": geometry_qa,
        "anomalyFilters": anomaly_filters,
        "reports": {
            "nextReportDir": str(REPORT_DIR.relative_to(ROOT_DIR)),
            "suggestedFilename": f"refresh-center-{generated_at.replace(':', '').replace('-', '').replace('+', '-')}.json",
        },
    }


def persist_refresh_center_report(report: dict[str, Any] | None = None) -> dict[str, Any]:
    from ..service import write_json_file

    payload = deepcopy(report) if report is not None else build_refresh_center_report()
    generated_at = str(payload.get("generatedAt") or _now_iso())
    filename = f"refresh-center-{generated_at.replace(':', '').replace('-', '').replace('+', '-')}.json"
    report_path = REPORT_DIR / filename
    payload["persisted"] = True
    payload["reportPath"] = str(report_path.relative_to(ROOT_DIR))
    write_json_file(report_path, payload)
    return payload
