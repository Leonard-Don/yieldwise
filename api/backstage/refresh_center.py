"""
Refresh-center readiness and dry-run reporting for the backstage workbench.

This module keeps the "can I safely refresh/import now?" decision close to
ops-facing run metadata without growing api.service.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .runs import list_geo_asset_runs, list_import_runs, list_metrics_runs, list_reference_runs, runtime_data_state
from ..data_quality import build_data_quality_gate


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "tmp" / "refresh-reports"
JOB_DIR = ROOT_DIR / "tmp" / "refresh-jobs"
JOB_HISTORY_PATH = JOB_DIR / "jobs.json"
EXECUTION_LOCK_PATH = JOB_DIR / "execution.lock.json"
ANOMALY_REVIEW_PATH = JOB_DIR / "anomaly-review.json"
LOW_CONFIDENCE_THRESHOLD = 0.72
LOW_PAIR_COUNT_THRESHOLD = 1
LOW_YIELD_PCT = 1.5
HIGH_YIELD_PCT = 8.0


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _timestamp_slug() -> str:
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%f%z")


def _relative_path_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR))
    except ValueError:
        return str(path)


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


def _read_json_payload(path: Path, fallback: Any) -> Any:
    from ..service import read_json_file

    payload = read_json_file(path)
    return payload if payload is not None else deepcopy(fallback)


def _write_json_payload(path: Path, payload: Any) -> None:
    from ..service import write_json_file

    write_json_file(path, payload)


def _load_job_history() -> list[dict[str, Any]]:
    payload = _read_json_payload(JOB_HISTORY_PATH, [])
    return payload if isinstance(payload, list) else []


def _write_job_history(jobs: list[dict[str, Any]]) -> None:
    _write_json_payload(JOB_HISTORY_PATH, jobs[:50])


def list_refresh_center_jobs(limit: int = 20) -> dict[str, Any]:
    jobs = _load_job_history()
    jobs.sort(key=lambda item: str(item.get("startedAt") or item.get("createdAt") or ""), reverse=True)
    return {"items": jobs[: max(1, limit)]}


def refresh_center_job_detail(job_id: str) -> dict[str, Any] | None:
    return next((item for item in _load_job_history() if item.get("jobId") == job_id), None)


def _save_job(job: dict[str, Any]) -> dict[str, Any]:
    jobs = [item for item in _load_job_history() if item.get("jobId") != job.get("jobId")]
    jobs.insert(0, deepcopy(job))
    _write_job_history(jobs)
    return job


def _lock_payload() -> dict[str, Any] | None:
    payload = _read_json_payload(EXECUTION_LOCK_PATH, None)
    return payload if isinstance(payload, dict) else None


def _acquire_execution_lock(job_id: str) -> None:
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with EXECUTION_LOCK_PATH.open("x", encoding="utf-8") as handle:
            handle.write(f'{{"jobId":"{job_id}","startedAt":"{_now_iso()}"}}')
    except FileExistsError as exc:
        lock = _lock_payload() or {}
        raise RuntimeError(f"刷新中心已有执行中的任务：{lock.get('jobId') or 'unknown'}") from exc


def _release_execution_lock(job_id: str) -> None:
    lock = _lock_payload() or {}
    if lock.get("jobId") in {None, job_id}:
        try:
            EXECUTION_LOCK_PATH.unlink(missing_ok=True)
        except OSError:
            pass


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
            action="把这些楼层放入浏览器公开页抓取补样。",
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


def _load_anomaly_review_state() -> dict[str, dict[str, Any]]:
    payload = _read_json_payload(ANOMALY_REVIEW_PATH, {})
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, dict)}


def _write_anomaly_review_state(payload: dict[str, dict[str, Any]]) -> None:
    _write_json_payload(ANOMALY_REVIEW_PATH, payload)


def _anomaly_id(*parts: Any) -> str:
    return "::".join(str(part or "-").strip().replace("::", "--") for part in parts)


def _anomaly_status(review_state: dict[str, dict[str, Any]], anomaly_id: str) -> str:
    return str(review_state.get(anomaly_id, {}).get("status") or "pending")


def list_refresh_center_anomalies(limit: int = 200) -> dict[str, Any]:
    latest_import = _latest(list_import_runs())
    detail = latest_import_anomaly_detail(latest_import)
    review_state = _load_anomaly_review_state()
    items: list[dict[str, Any]] = []
    if detail:
        run_ref = _run_ref(detail)
        for queue_item in detail.get("reviewQueue") or []:
            anomaly_id = _anomaly_id("review_queue", queue_item.get("queueId"))
            items.append(
                {
                    "anomalyId": anomaly_id,
                    "type": "review_queue",
                    "typeLabel": "地址复核队列",
                    "severity": "warn",
                    "status": _anomaly_status(review_state, anomaly_id),
                    "label": queue_item.get("normalizedPath") or queue_item.get("queueId"),
                    "detail": f"状态 {queue_item.get('status') or 'pending'} · 置信度 {queue_item.get('confidence') or '待补'}",
                    "run": run_ref,
                    "queueId": queue_item.get("queueId"),
                    "suggestedAction": "确认地址归一后标记已复核，或转入补样。",
                    "review": review_state.get(anomaly_id),
                }
            )
        attention = detail.get("attention") or {}
        for pair_item in attention.get("low_confidence_pairs") or []:
            anomaly_id = _anomaly_id("low_confidence_pairs", detail.get("runId"), pair_item.get("pair_id"))
            items.append(
                {
                    "anomalyId": anomaly_id,
                    "type": "low_confidence_pairs",
                    "typeLabel": "低置信样本配对",
                    "severity": "warn",
                    "status": _anomaly_status(review_state, anomaly_id),
                    "label": pair_item.get("normalized_address") or pair_item.get("pair_id"),
                    "detail": f"match_confidence={pair_item.get('match_confidence')}",
                    "run": run_ref,
                    "suggestedAction": "核对 sale/rent 是否同楼栋同楼层。",
                    "review": review_state.get(anomaly_id),
                }
            )
        for evidence in detail.get("floorEvidence") or []:
            pair_count = int(evidence.get("pair_count") or evidence.get("pairCount") or 0)
            confidence = float(evidence.get("best_pair_confidence") or evidence.get("bestPairConfidence") or 0)
            yield_pct = float(evidence.get("yield_pct") or evidence.get("yieldPct") or 0)
            shared = {
                "run": run_ref,
                "communityId": evidence.get("community_id") or evidence.get("communityId"),
                "buildingId": evidence.get("building_id") or evidence.get("buildingId"),
                "floorNo": evidence.get("floor_no") or evidence.get("floorNo"),
                "pairCount": pair_count,
                "yieldPct": round(yield_pct, 2),
                "bestPairConfidence": round(confidence, 3),
            }
            label = _evidence_label(evidence)
            if pair_count <= LOW_PAIR_COUNT_THRESHOLD:
                anomaly_id = _anomaly_id("single_pair_floors", detail.get("runId"), shared["buildingId"], shared["floorNo"])
                items.append(
                    {
                        **shared,
                        "anomalyId": anomaly_id,
                        "type": "single_pair_floors",
                        "typeLabel": "单样本楼层",
                        "severity": "warn",
                        "status": _anomaly_status(review_state, anomaly_id),
                        "label": label,
                        "detail": f"pair_count={pair_count}",
                        "suggestedAction": "进入浏览器公开页抓取补样。",
                        "review": review_state.get(anomaly_id),
                    }
                )
            if confidence and confidence < LOW_CONFIDENCE_THRESHOLD:
                anomaly_id = _anomaly_id("low_confidence_floors", detail.get("runId"), shared["buildingId"], shared["floorNo"])
                items.append(
                    {
                        **shared,
                        "anomalyId": anomaly_id,
                        "type": "low_confidence_floors",
                        "typeLabel": "楼层最佳配对偏低",
                        "severity": "warn",
                        "status": _anomaly_status(review_state, anomaly_id),
                        "label": label,
                        "detail": f"best_pair_confidence={confidence:.3f}",
                        "suggestedAction": "优先复核楼栋、单元和楼层归一。",
                        "review": review_state.get(anomaly_id),
                    }
                )
            if yield_pct and (yield_pct < LOW_YIELD_PCT or yield_pct > HIGH_YIELD_PCT):
                anomaly_id = _anomaly_id("yield_outliers", detail.get("runId"), shared["buildingId"], shared["floorNo"])
                items.append(
                    {
                        **shared,
                        "anomalyId": anomaly_id,
                        "type": "yield_outliers",
                        "typeLabel": "回报率异常值",
                        "severity": "high",
                        "status": _anomaly_status(review_state, anomaly_id),
                        "label": label,
                        "detail": f"yield_pct={yield_pct:.2f}",
                        "suggestedAction": "核对总价、月租和面积口径。",
                        "review": review_state.get(anomaly_id),
                    }
                )
    status_order = {"pending": 0, "needs_sample": 1, "reviewed": 2, "waived": 3}
    items.sort(key=lambda item: (status_order.get(str(item.get("status")), 9), str(item.get("type")), str(item.get("label"))))
    summary = {
        "totalCount": len(items),
        "pendingCount": sum(1 for item in items if item.get("status") == "pending"),
        "needsSampleCount": sum(1 for item in items if item.get("status") == "needs_sample"),
        "reviewedCount": sum(1 for item in items if item.get("status") == "reviewed"),
        "waivedCount": sum(1 for item in items if item.get("status") == "waived"),
    }
    return {"summary": summary, "items": items[: max(1, limit)]}


def update_refresh_center_anomaly(anomaly_id: str, *, status: str, resolution_notes: str | None = None, reviewer: str = "atlas-ui") -> dict[str, Any]:
    if status not in {"pending", "reviewed", "needs_sample", "waived"}:
        raise ValueError("Unsupported anomaly status")
    review_state = _load_anomaly_review_state()
    review_state[anomaly_id] = {
        "anomalyId": anomaly_id,
        "status": status,
        "resolutionNotes": resolution_notes,
        "reviewer": reviewer,
        "reviewedAt": _now_iso(),
    }
    _write_anomaly_review_state(review_state)
    queue = list_refresh_center_anomalies()
    item = next((entry for entry in queue["items"] if entry.get("anomalyId") == anomaly_id), None)
    return {"status": "updated", "item": item or review_state[anomaly_id], "summary": queue["summary"]}


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
    from ..service import current_community_dataset

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
    data_quality_gate = build_data_quality_gate(
        communities=current_community_dataset(),
        import_runs=import_runs,
    )

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
            "补一轮浏览器公开页抓取样本。" if not latest_import else "可进入异常过滤与指标刷新。",
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
            "data_quality_gate",
            "数据质量闸门",
            data_quality_gate["status"],
            (
                f"均分 {data_quality_gate['score']}/100，"
                f"脏挂牌 {data_quality_gate['dirtyListings']['totalIssueCount']}，"
                f"待补样 {data_quality_gate['statusCounts']['blocked']}。"
            ),
            "先清理脏挂牌并补齐阻断小区样本。" if data_quality_gate["status"] == "blocker" else "继续按质量薄弱项补样。",
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
        "dataQualityGate": data_quality_gate,
        "geometryQa": geometry_qa,
        "anomalyFilters": anomaly_filters,
        "reports": {
            "nextReportDir": _relative_path_label(REPORT_DIR),
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
    payload["reportPath"] = _relative_path_label(report_path)
    write_json_file(report_path, payload)
    return payload


def _execution_step(step: str, label: str, status: str, detail: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "step": step,
        "label": label,
        "status": status,
        "detail": detail,
        "payload": payload or {},
        "completedAt": _now_iso(),
    }


def execute_refresh_center_plan(
    *,
    write_postgres: bool = False,
    apply_schema: bool = False,
    refresh_metrics: bool = True,
    bootstrap_database: bool = False,
    force: bool = False,
    retry_job_id: str | None = None,
) -> dict[str, Any]:
    from ..service import bootstrap_local_database, refresh_metrics_snapshot

    job_id = f"refresh-center-{_timestamp_slug()}"
    started_at = _now_iso()
    job = {
        "jobId": job_id,
        "status": "running",
        "createdAt": started_at,
        "startedAt": started_at,
        "completedAt": None,
        "retryOfJobId": retry_job_id,
        "options": {
            "writePostgres": write_postgres,
            "applySchema": apply_schema,
            "refreshMetrics": refresh_metrics,
            "bootstrapDatabase": bootstrap_database,
            "force": force,
        },
        "steps": [],
        "error": None,
    }
    _save_job(job)
    try:
        _acquire_execution_lock(job_id)
    except RuntimeError as exc:
        job["status"] = "locked"
        job["error"] = str(exc)
        job["completedAt"] = _now_iso()
        job["steps"].append(_execution_step("lock", "执行锁", "locked", str(exc)))
        return _save_job(job)
    try:
        report = build_refresh_center_report()
        job["report"] = {
            "status": report.get("status"),
            "generatedAt": report.get("generatedAt"),
            "selectedRuns": report.get("selectedRuns"),
            "readiness": report.get("readiness"),
            "dataQualityGate": report.get("dataQualityGate"),
        }
        blocker_checks = [item for item in report.get("dryRunChecks", []) if item.get("status") == "blocker"]
        if blocker_checks and not force:
            job["status"] = "blocked"
            job["steps"].append(
                _execution_step(
                    "dry_run",
                    "Dry-run 检查",
                    "blocked",
                    f"存在 {len(blocker_checks)} 个阻断项，未执行刷新。",
                    {"blockers": blocker_checks},
                )
            )
            return job

        selected_runs = report.get("selectedRuns") or {}
        for step_key, label in [("reference", "Reference 主档"), ("import", "Sale/Rent 样本"), ("geo", "楼栋几何")]:
            run = selected_runs.get(step_key)
            job["steps"].append(
                _execution_step(
                    step_key,
                    label,
                    "validated" if run else "skipped",
                    f"使用批次 {run.get('batchName') or run.get('runId')}" if run else "没有可用批次，跳过。",
                    {"run": run},
                )
            )

        readiness = report.get("readiness") or {}
        if bootstrap_database:
            if not readiness.get("canBootstrap"):
                job["steps"].append(_execution_step("bootstrap", "本地数据库引导", "skipped", "当前未配置可执行 Bootstrap 的 DSN 或 reference run。"))
            else:
                bootstrap_payload = bootstrap_local_database(
                    reference_run_id=(selected_runs.get("reference") or {}).get("runId"),
                    import_run_id=(selected_runs.get("import") or {}).get("runId"),
                    geo_run_id=(selected_runs.get("geo") or {}).get("runId"),
                    apply_schema=apply_schema,
                    refresh_metrics=False,
                )
                job["steps"].append(_execution_step("bootstrap", "本地数据库引导", "completed", "Bootstrap 已完成。", bootstrap_payload))
        else:
            job["steps"].append(_execution_step("bootstrap", "本地数据库引导", "skipped", "调用方未要求 Bootstrap。"))

        if refresh_metrics:
            snapshot_date = date.today().isoformat()
            metrics_payload = refresh_metrics_snapshot(
                snapshot_date=snapshot_date,
                batch_name=f"refresh-center-{snapshot_date}-{datetime.now().strftime('%H%M%S')}",
                write_postgres=bool(write_postgres and readiness.get("canWriteMetricsToPostgres")),
                apply_schema=apply_schema,
                trigger_source="refresh-center",
            )
            job["steps"].append(_execution_step("metrics", "指标快照", "completed", "指标快照已刷新。", metrics_payload))
        else:
            job["steps"].append(_execution_step("metrics", "指标快照", "skipped", "调用方关闭 metrics 刷新。"))

        persisted_report = persist_refresh_center_report(build_refresh_center_report())
        job["steps"].append(_execution_step("report", "刷新报告", "completed", "执行后报告已落盘。", {"reportPath": persisted_report.get("reportPath")}))
        job["status"] = "completed"
        return job
    except Exception as exc:
        job["status"] = "failed"
        job["error"] = str(exc)
        job["steps"].append(_execution_step("error", "执行错误", "failed", str(exc)))
        return job
    finally:
        job["completedAt"] = _now_iso()
        _save_job(job)
        _release_execution_lock(job_id)
