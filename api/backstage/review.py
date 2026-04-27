"""
Browser sampling + capture review aggregation for the backstage tool.

Phase 7b/7c/7d extraction from api/service.py — covers browser_sampling
labels/query helpers, browser_capture run-summary/detail/manifest helpers,
review-queue build/supersede pipeline, review inbox + workflow + fixture
helpers, and the sampling-pack/submit/update workflow. Re-exported from
api.service for back-compat.
"""

from __future__ import annotations

import csv
import io
import json
import math
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


BROWSER_SAMPLING_REQUIRED_FIELDS = {
    "floor_pair_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "朝向",
        "装修",
        "挂牌总价或月租",
        "抓取时间",
    ],
    "building_depth_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "朝向",
        "装修",
        "挂牌总价或月租",
        "抓取时间",
    ],
    "community_profile_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "挂牌总价或月租",
        "抓取时间",
    ],
}


def browser_sampling_task_type_label(task_type: str) -> str:
    return {
        "floor_pair_capture": "楼层补样",
        "building_depth_capture": "楼栋加深",
        "community_profile_capture": "小区补面",
    }.get(task_type, task_type)


def browser_sampling_priority_label(priority_score: float) -> str:
    if priority_score >= 88:
        return "极高优先"
    if priority_score >= 76:
        return "高优先"
    if priority_score >= 62:
        return "中优先"
    return "常规优先"


def browser_sampling_required_fields(task_type: str) -> list[str]:
    return list(BROWSER_SAMPLING_REQUIRED_FIELDS.get(task_type, BROWSER_SAMPLING_REQUIRED_FIELDS["floor_pair_capture"]))


def browser_sampling_query(
    *,
    district_name: str | None,
    community_name: str,
    building_name: str | None = None,
    floor_no: int | None = None,
    business_type: str | None = None,
) -> str:
    parts = ["上海"]
    if district_name:
        parts.append(str(district_name))
    parts.append(str(community_name))
    if building_name:
        parts.append(str(building_name))
    if floor_no is not None:
        parts.append(f"{int(floor_no)}层")
    if business_type == "sale":
        parts.append("二手房")
    elif business_type == "rent":
        parts.append("租房")
    elif business_type:
        parts.append(str(business_type))
    return " ".join(part for part in parts if part)


def browser_capture_runs_root() -> Path:
    from ..service import ROOT_DIR

    return ROOT_DIR / "tmp" / "browser-capture-runs"


def browser_capture_manifest_paths() -> list[Path]:
    from ..service import manifest_paths_under

    return manifest_paths_under(browser_capture_runs_root())


def browser_capture_review_queue_id(business_type: str | None, source_listing_id: str | None) -> str:
    return f"{str(business_type or '').strip().lower()}::{str(source_listing_id or '').strip()}"


def browser_capture_review_summary(review_queue: list[dict[str, Any]] | None) -> dict[str, int]:
    rows = review_queue if isinstance(review_queue, list) else []
    return {
        "pendingCount": sum(1 for item in rows if str(item.get("status") or "pending") == "pending"),
        "resolvedCount": sum(1 for item in rows if str(item.get("status") or "") == "resolved"),
        "waivedCount": sum(1 for item in rows if str(item.get("status") or "") == "waived"),
        "supersededCount": sum(1 for item in rows if str(item.get("status") or "") == "superseded"),
    }


def build_browser_capture_detail_rows(
    input_rows: list[dict[str, Any]] | None,
    parsed_rows: list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parsed_by_key = {
        f'{item.get("business_type")}::{item.get("source_listing_id")}': item
        for item in (parsed_rows or [])
        if isinstance(item, dict)
    }
    capture_rows: list[dict[str, Any]] = []
    attention_rows: list[dict[str, Any]] = []
    for row in input_rows or []:
        if not isinstance(row, dict):
            continue
        business_type = str(row.get("business_type") or "").strip().lower()
        source_listing_id = str(row.get("source_listing_id") or "").strip()
        parsed = parsed_by_key.get(f"{business_type}::{source_listing_id}") or {}
        attention = parsed.get("attention") or []
        detail_row = {
            "queueId": browser_capture_review_queue_id(business_type, source_listing_id),
            "businessType": business_type,
            "businessTypeLabel": "出售" if business_type == "sale" else "出租" if business_type == "rent" else business_type,
            "sourceListingId": source_listing_id,
            "url": row.get("url"),
            "publishedAt": row.get("published_at"),
            "communityName": row.get("community_name"),
            "addressText": row.get("address_text"),
            "buildingText": parsed.get("building_text") or row.get("building_text") or "",
            "unitText": parsed.get("unit_text") or row.get("unit_text") or "",
            "floorText": parsed.get("floor_text") or row.get("floor_text") or "",
            "totalFloors": parsed.get("total_floors") or row.get("total_floors") or "",
            "areaSqm": parsed.get("area_sqm") or row.get("area_sqm") or "",
            "orientation": parsed.get("orientation") or row.get("orientation") or "",
            "decoration": parsed.get("decoration") or row.get("decoration") or "",
            "priceTotalWan": row.get("price_total_wan") or "",
            "unitPriceYuan": row.get("unit_price_yuan") or "",
            "monthlyRent": row.get("monthly_rent") or "",
            "rawText": row.get("raw_text") or "",
            "captureNotes": row.get("capture_notes") or "",
            "attention": attention,
            "attentionCount": len(attention),
        }
        capture_rows.append(detail_row)
        if attention:
            attention_rows.append(detail_row)
    return capture_rows, attention_rows


def build_browser_capture_review_queue(
    attention_rows: list[dict[str, Any]] | None,
    existing_rows: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    existing_index = {
        str(item.get("queueId") or ""): item
        for item in (existing_rows or [])
        if isinstance(item, dict) and item.get("queueId")
    }
    review_queue: list[dict[str, Any]] = []
    for item in attention_rows or []:
        queue_id = str(item.get("queueId") or browser_capture_review_queue_id(item.get("businessType"), item.get("sourceListingId")))
        existing = existing_index.get(queue_id) or {}
        review_queue.append(
            {
                **item,
                "queueId": queue_id,
                "status": existing.get("status") or "pending",
                "resolutionNotes": existing.get("resolutionNotes") or None,
                "reviewOwner": existing.get("reviewOwner") or None,
                "reviewedAt": existing.get("reviewedAt") or None,
                "replacementRunId": existing.get("replacementRunId") or None,
            }
        )
    review_queue.sort(
        key=lambda item: (
            0 if str(item.get("status") or "pending") == "pending" else 1,
            0 if str(item.get("businessType") or "") == "sale" else 1,
            str(item.get("sourceListingId") or ""),
        )
    )
    return review_queue


def browser_capture_run_artifacts(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    from ..service import default_browser_capture_review_queue_path, read_csv_rows, read_json_file, resolve_artifact_path

    outputs = manifest.get("outputs") or {}
    capture_csv_path = resolve_artifact_path(outputs.get("capture_csv"))
    parsed_captures_path = resolve_artifact_path(outputs.get("parsed_captures"))
    input_rows = read_csv_rows(capture_csv_path) if capture_csv_path and capture_csv_path.exists() else []
    parsed_rows = read_json_file(parsed_captures_path) if parsed_captures_path and parsed_captures_path.exists() else []
    capture_rows, attention_rows = build_browser_capture_detail_rows(input_rows, parsed_rows)
    review_queue_path = resolve_artifact_path(outputs.get("review_queue")) or default_browser_capture_review_queue_path(manifest_path)
    existing_review_queue = read_json_file(review_queue_path) if review_queue_path.exists() else []
    review_queue = build_browser_capture_review_queue(attention_rows, existing_rows=existing_review_queue)
    return {
        "captureRows": capture_rows,
        "attentionRows": attention_rows,
        "reviewQueue": review_queue,
        "reviewSummary": browser_capture_review_summary(review_queue),
        "reviewQueuePath": review_queue_path,
    }


def supersede_browser_capture_review_items(
    *,
    task_id: str | None,
    replacement_run_id: str,
    review_queue: list[dict[str, Any]] | None,
) -> None:
    from ..service import read_json_file, resolve_artifact_path, write_json_file

    normalized_task_id = str(task_id or "").strip()
    if not normalized_task_id or not review_queue:
        return
    pending_ids = {
        str(item.get("queueId") or "")
        for item in review_queue
        if str(item.get("status") or "pending") == "pending" and item.get("queueId")
    }
    if not pending_ids:
        return
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for run in list_browser_capture_runs():
        if str(run.get("runId") or "") == replacement_run_id or str(run.get("taskId") or "") != normalized_task_id:
            continue
        manifest_path = resolve_artifact_path(run.get("manifestPath"))
        if not manifest_path or not manifest_path.exists():
            continue
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict):
            continue
        artifacts = browser_capture_run_artifacts(manifest, manifest_path)
        queue_rows = deepcopy(artifacts["reviewQueue"])
        changed = False
        for item in queue_rows:
            if str(item.get("queueId") or "") not in pending_ids:
                continue
            if str(item.get("status") or "pending") != "pending":
                continue
            item["status"] = "superseded"
            item["resolutionNotes"] = f"已由后续修正采样 {replacement_run_id} 接管。"
            item["reviewOwner"] = "atlas-ui"
            item["reviewedAt"] = reviewed_at
            item["replacementRunId"] = replacement_run_id
            changed = True
        if not changed:
            continue
        manifest.setdefault("outputs", {})
        manifest["outputs"]["review_queue"] = str(artifacts["reviewQueuePath"])
        write_json_file(artifacts["reviewQueuePath"], queue_rows)
        write_json_file(manifest_path, manifest)


def browser_capture_run_summary_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> dict[str, Any]:
    summary = manifest.get("summary", {})
    task_snapshot = manifest.get("task_snapshot") or {}
    artifacts = browser_capture_run_artifacts(manifest, manifest_path)
    review_summary = artifacts["reviewSummary"]
    pending_attention_preview = [
        item
        for item in artifacts["reviewQueue"]
        if str(item.get("status") or "pending") == "pending"
    ][:3]
    attention_rows = manifest.get("attention") or []
    return {
        "runId": manifest.get("run_id"),
        "providerId": manifest.get("provider_id"),
        "createdAt": manifest.get("created_at"),
        "taskId": manifest.get("task_id"),
        "taskType": task_snapshot.get("taskType"),
        "taskTypeLabel": task_snapshot.get("taskTypeLabel")
        or browser_sampling_task_type_label(str(task_snapshot.get("taskType") or "")),
        "districtId": task_snapshot.get("districtId"),
        "districtName": task_snapshot.get("districtName"),
        "communityId": task_snapshot.get("communityId"),
        "communityName": task_snapshot.get("communityName"),
        "buildingId": task_snapshot.get("buildingId"),
        "buildingName": task_snapshot.get("buildingName"),
        "floorNo": task_snapshot.get("floorNo"),
        "captureCount": int(summary.get("capture_count") or 0),
        "saleCaptureCount": int(summary.get("sale_capture_count") or 0),
        "rentCaptureCount": int(summary.get("rent_capture_count") or 0),
        "attentionCount": int(summary.get("attention_count") or 0),
        "mergedSaleCount": int(summary.get("merged_sale_count") or 0),
        "mergedRentCount": int(summary.get("merged_rent_count") or 0),
        "attentionPreview": attention_rows[:3],
        "pendingAttentionPreview": pending_attention_preview,
        "reviewSummary": review_summary,
        "importRunId": (manifest.get("import_result") or {}).get("run_id"),
        "metricsRunId": (manifest.get("metrics_result") or {}).get("runId"),
        "outputDir": str(manifest_path.parent),
        "manifestPath": str(manifest_path),
    }


@lru_cache(maxsize=8)
def _list_browser_capture_runs_cached(limit: int | None = None) -> tuple[dict[str, Any], ...]:
    from ..service import comparable_created_at_value, read_json_file

    runs: list[dict[str, Any]] = []
    for manifest_path in browser_capture_manifest_paths():
        manifest = read_json_file(manifest_path)
        if not isinstance(manifest, dict) or not manifest.get("run_id"):
            continue
        runs.append(browser_capture_run_summary_from_manifest(manifest, manifest_path))
    runs.sort(key=lambda item: comparable_created_at_value(item.get("createdAt")), reverse=True)
    if limit is not None:
        return tuple(runs[:limit])
    return tuple(runs)


def list_browser_capture_runs(limit: int | None = None) -> list[dict[str, Any]]:
    return deepcopy(list(_list_browser_capture_runs_cached(limit)))


@lru_cache(maxsize=64)
def _browser_capture_run_detail_cached(run_id: str) -> dict[str, Any] | None:
    from ..service import read_json_file

    run_summary = next((item for item in list_browser_capture_runs() if item.get("runId") == run_id), None)
    if not run_summary:
        return None
    manifest_path = Path(str(run_summary.get("manifestPath") or ""))
    manifest = read_json_file(manifest_path)
    if not isinstance(manifest, dict):
        return None
    artifacts = browser_capture_run_artifacts(manifest, manifest_path)
    return {
        **run_summary,
        "task": manifest.get("task_snapshot") or {},
        "baseImportRunId": manifest.get("base_import_run_id"),
        "captures": artifacts["captureRows"],
        "attention": artifacts["attentionRows"],
        "reviewQueue": artifacts["reviewQueue"],
        "reviewSummary": artifacts["reviewSummary"],
        "captureCount": len(artifacts["captureRows"]),
        "attentionCount": len(artifacts["attentionRows"]),
        "reviewQueuePath": str(artifacts["reviewQueuePath"]),
    }


def browser_capture_run_detail(run_id: str) -> dict[str, Any] | None:
    detail = _browser_capture_run_detail_cached(run_id)
    return deepcopy(detail) if detail else None


def browser_sampling_task_display_label(task: dict[str, Any] | None) -> str:
    if not isinstance(task, dict):
        return "当前任务"
    community_name = str(task.get("communityName") or task.get("community_name") or "待识别小区").strip() or "待识别小区"
    parts = [community_name]
    building_name = str(task.get("buildingName") or task.get("building_name") or "").strip()
    if building_name:
        parts.append(building_name)
    floor_no = task.get("floorNo")
    if floor_no not in (None, ""):
        parts.append(f"{floor_no}层")
    return " · ".join(parts)


def browser_review_inbox_summary(items: list[dict[str, Any]] | None) -> dict[str, Any]:
    from ..service import comparable_created_at_value

    normalized_items = [item for item in (items or []) if isinstance(item, dict)]
    timestamps = sorted(
        [str(item.get("runCreatedAt") or "") for item in normalized_items if item.get("runCreatedAt")],
        key=comparable_created_at_value,
    )
    task_ids = {str(item.get("taskId") or "") for item in normalized_items if item.get("taskId")}
    district_ids = {str(item.get("districtId") or "") for item in normalized_items if item.get("districtId")}
    return {
        "pendingQueueCount": len(normalized_items),
        "pendingTaskCount": len(task_ids),
        "pendingDistrictCount": len(district_ids),
        "oldestPendingAt": min(timestamps) if timestamps else None,
        "latestPendingAt": max(timestamps) if timestamps else None,
    }


def browser_capture_review_workflow_item_payload(
    *,
    run_id: str,
    run_created_at: str | None,
    review_item: dict[str, Any] | None,
    task_snapshot: dict[str, Any] | None,
    run_pending_count: int,
    task_pending_count: int,
) -> dict[str, Any] | None:
    if not isinstance(review_item, dict):
        return None
    queue_id = str(review_item.get("queueId") or "").strip()
    if not queue_id:
        return None
    normalized_task = deepcopy(task_snapshot or {})
    task_id = str(normalized_task.get("taskId") or "").strip()
    if task_id:
        normalized_task["taskId"] = task_id
    normalized_task.setdefault("taskTypeLabel", browser_sampling_task_type_label(str(normalized_task.get("taskType") or "")))
    normalized_task["taskLifecycleStatus"] = "needs_review"
    normalized_task["taskLifecycleLabel"] = "已采待复核"
    return {
        "inboxItemId": f"{run_id}:{queue_id}",
        "runId": run_id,
        "queueId": queue_id,
        "taskId": normalized_task.get("taskId"),
        "taskLabel": browser_sampling_task_display_label(normalized_task),
        "districtId": normalized_task.get("districtId"),
        "districtName": normalized_task.get("districtName"),
        "communityId": normalized_task.get("communityId"),
        "communityName": normalized_task.get("communityName"),
        "buildingId": normalized_task.get("buildingId"),
        "buildingName": normalized_task.get("buildingName"),
        "floorNo": normalized_task.get("floorNo"),
        "taskType": normalized_task.get("taskType"),
        "taskTypeLabel": normalized_task.get("taskTypeLabel"),
        "targetGranularity": normalized_task.get("targetGranularity"),
        "focusScope": normalized_task.get("focusScope"),
        "priorityScore": normalized_task.get("priorityScore"),
        "priorityLabel": normalized_task.get("priorityLabel"),
        "taskLifecycleStatus": normalized_task.get("taskLifecycleStatus"),
        "taskLifecycleLabel": normalized_task.get("taskLifecycleLabel"),
        "businessType": review_item.get("businessType"),
        "businessTypeLabel": review_item.get("businessTypeLabel"),
        "sourceListingId": review_item.get("sourceListingId"),
        "attention": review_item.get("attention") or [],
        "buildingText": review_item.get("buildingText"),
        "unitText": review_item.get("unitText"),
        "floorText": review_item.get("floorText"),
        "totalFloors": review_item.get("totalFloors"),
        "areaSqm": review_item.get("areaSqm"),
        "url": review_item.get("url"),
        "publishedAt": review_item.get("publishedAt"),
        "rawText": review_item.get("rawText"),
        "captureNotes": review_item.get("captureNotes"),
        "runCreatedAt": run_created_at,
        "taskPendingAttentionCount": task_pending_count,
        "runPendingCount": run_pending_count,
        "task": deepcopy(normalized_task),
    }


def browser_capture_review_workflow_payload(
    action: str,
    reason: str,
    *,
    task: dict[str, Any] | None = None,
    item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow_item = deepcopy(item) if isinstance(item, dict) else None
    workflow_task = deepcopy((workflow_item or {}).get("task") or task or {})
    if workflow_item:
        workflow_task.setdefault("taskId", workflow_item.get("taskId"))
        workflow_task.setdefault("districtId", workflow_item.get("districtId"))
        workflow_task.setdefault("districtName", workflow_item.get("districtName"))
        workflow_task.setdefault("communityId", workflow_item.get("communityId"))
        workflow_task.setdefault("communityName", workflow_item.get("communityName"))
        workflow_task.setdefault("buildingId", workflow_item.get("buildingId"))
        workflow_task.setdefault("buildingName", workflow_item.get("buildingName"))
        workflow_task.setdefault("floorNo", workflow_item.get("floorNo"))
        workflow_task.setdefault("taskType", workflow_item.get("taskType"))
        workflow_task.setdefault("taskTypeLabel", workflow_item.get("taskTypeLabel"))
        workflow_task.setdefault("targetGranularity", workflow_item.get("targetGranularity"))
        workflow_task.setdefault("focusScope", workflow_item.get("focusScope"))
        workflow_task.setdefault("priorityScore", workflow_item.get("priorityScore"))
        workflow_task.setdefault("priorityLabel", workflow_item.get("priorityLabel"))
        workflow_task.setdefault("taskLifecycleStatus", workflow_item.get("taskLifecycleStatus"))
        workflow_task.setdefault("taskLifecycleLabel", workflow_item.get("taskLifecycleLabel"))
        workflow_task.setdefault("pendingReviewRunId", workflow_item.get("runId"))
        workflow_task.setdefault("pendingReviewQueueId", workflow_item.get("queueId"))
        workflow_task.setdefault("pendingAttentionCount", workflow_item.get("taskPendingAttentionCount"))
    return {
        "action": action,
        "reason": reason,
        "runId": (workflow_item or {}).get("runId") or workflow_task.get("pendingReviewRunId"),
        "queueId": (workflow_item or {}).get("queueId") or workflow_task.get("pendingReviewQueueId"),
        "taskId": workflow_task.get("taskId"),
        "task": workflow_task or None,
        "item": workflow_item,
    }


@lru_cache(maxsize=1)
def _browser_review_inbox_all_cached() -> dict[str, Any]:
    from ..service import comparable_created_at_value

    task_type_rank = {"floor_pair_capture": 0, "building_depth_capture": 1, "community_profile_capture": 2}
    items: list[dict[str, Any]] = []
    for run in list_browser_capture_runs(limit=80):
        run_id = str(run.get("runId") or "")
        if not run_id or int((run.get("reviewSummary") or {}).get("pendingCount") or 0) <= 0:
            continue
        detail = browser_capture_run_detail(run_id)
        if not detail:
            continue
        task_id = str(detail.get("task", {}).get("taskId") or run.get("taskId") or "")
        task_snapshot = deepcopy(detail.get("task") or {})
        if task_id:
            task_snapshot.setdefault("taskId", task_id)
        task_snapshot.setdefault("districtId", run.get("districtId"))
        task_snapshot.setdefault("districtName", run.get("districtName"))
        task_snapshot.setdefault("communityId", run.get("communityId"))
        task_snapshot.setdefault("communityName", run.get("communityName"))
        task_snapshot.setdefault("buildingId", run.get("buildingId"))
        task_snapshot.setdefault("buildingName", run.get("buildingName"))
        task_snapshot.setdefault("floorNo", run.get("floorNo"))
        task_snapshot.setdefault("taskType", run.get("taskType"))
        task_snapshot.setdefault(
            "taskTypeLabel",
            run.get("taskTypeLabel") or browser_sampling_task_type_label(str(run.get("taskType") or "")),
        )
        task_snapshot["taskLifecycleStatus"] = "needs_review"
        task_snapshot["taskLifecycleLabel"] = "已采待复核"
        run_pending_count = int((detail.get("reviewSummary") or {}).get("pendingCount") or 0)
        task_pending_count = int(task_snapshot.get("pendingAttentionCount") or run_pending_count)
        for queue_index, review_item in enumerate(detail.get("reviewQueue") or []):
            if str(review_item.get("status") or "pending") != "pending":
                continue
            queue_id = str(review_item.get("queueId") or "")
            if not queue_id:
                continue
            item = {
                "inboxItemId": f"{run_id}:{queue_id}",
                "runId": run_id,
                "queueId": queue_id,
                "taskId": task_snapshot.get("taskId"),
                "taskLabel": browser_sampling_task_display_label(task_snapshot),
                "districtId": task_snapshot.get("districtId"),
                "districtName": task_snapshot.get("districtName"),
                "communityId": task_snapshot.get("communityId"),
                "communityName": task_snapshot.get("communityName"),
                "buildingId": task_snapshot.get("buildingId"),
                "buildingName": task_snapshot.get("buildingName"),
                "floorNo": task_snapshot.get("floorNo"),
                "taskType": task_snapshot.get("taskType"),
                "taskTypeLabel": task_snapshot.get("taskTypeLabel"),
                "targetGranularity": task_snapshot.get("targetGranularity"),
                "focusScope": task_snapshot.get("focusScope"),
                "priorityScore": task_snapshot.get("priorityScore"),
                "priorityLabel": task_snapshot.get("priorityLabel"),
                "taskLifecycleStatus": task_snapshot.get("taskLifecycleStatus"),
                "taskLifecycleLabel": task_snapshot.get("taskLifecycleLabel"),
                "businessType": review_item.get("businessType"),
                "businessTypeLabel": review_item.get("businessTypeLabel"),
                "sourceListingId": review_item.get("sourceListingId"),
                "attention": review_item.get("attention") or [],
                "buildingText": review_item.get("buildingText"),
                "unitText": review_item.get("unitText"),
                "floorText": review_item.get("floorText"),
                "totalFloors": review_item.get("totalFloors"),
                "areaSqm": review_item.get("areaSqm"),
                "url": review_item.get("url"),
                "publishedAt": review_item.get("publishedAt"),
                "rawText": review_item.get("rawText"),
                "captureNotes": review_item.get("captureNotes"),
                "runCreatedAt": run.get("createdAt"),
                "taskPendingAttentionCount": task_pending_count,
                "runPendingCount": run_pending_count,
                "task": deepcopy(task_snapshot),
                "__queueIndex": queue_index,
            }
            items.append(item)

    items.sort(key=lambda item: int(item.get("__queueIndex") or 0))
    items.sort(key=lambda item: comparable_created_at_value(item.get("runCreatedAt")), reverse=True)
    items.sort(
        key=lambda item: (
            -float(item.get("priorityScore") or 0),
            task_type_rank.get(str(item.get("taskType") or ""), 9),
            str(item.get("districtName") or ""),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
            str(item.get("taskId") or ""),
        )
    )
    task_pending_counts: dict[str, int] = {}
    for item in items:
        task_id = str(item.get("taskId") or "")
        if task_id:
            task_pending_counts[task_id] = task_pending_counts.get(task_id, 0) + 1
    for item in items:
        task_id = str(item.get("taskId") or "")
        if task_id:
            item["taskPendingAttentionCount"] = task_pending_counts.get(task_id, item.get("taskPendingAttentionCount") or 0)
    public_items = []
    for item in items:
        public_item = deepcopy(item)
        public_item.pop("__queueIndex", None)
        public_items.append(public_item)
    return {
        "items": public_items,
        "summary": browser_review_inbox_summary(public_items),
    }


def browser_review_inbox_payload(
    *,
    district: str | None = None,
    limit: int | None = 20,
) -> dict[str, Any]:
    cached = _browser_review_inbox_all_cached()
    filtered_items = [
        deepcopy(item)
        for item in cached.get("items") or []
        if district in (None, "", "all") or item.get("districtId") == district
    ]
    summary = browser_review_inbox_summary(filtered_items)
    if limit is not None:
        filtered_items = filtered_items[:limit]
    return {
        "summary": summary,
        "items": filtered_items,
    }


def browser_review_fixture_root() -> Path:
    from ..service import ROOT_DIR

    return ROOT_DIR / "tmp" / "browser-review-fixtures"


def _browser_review_items_by_task(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    items_by_task: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("taskId") or "")
        if not task_id:
            continue
        items_by_task.setdefault(task_id, []).append(item)
    return items_by_task


def _browser_review_items_by_task_run(items: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    items_by_task_run: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("taskId") or "")
        run_id = str(item.get("runId") or "")
        if not task_id or not run_id:
            continue
        items_by_task_run.setdefault((task_id, run_id), []).append(item)
    return items_by_task_run


def _browser_review_current_task_fixture_candidate() -> dict[str, Any] | None:
    review_inbox = browser_review_inbox_payload(limit=None)
    items = [item for item in (review_inbox.get("items") or []) if isinstance(item, dict)]
    items_by_task = _browser_review_items_by_task(items)
    items_by_task_run = _browser_review_items_by_task_run(items)
    pack_items = browser_sampling_pack(limit=200)
    for task_snapshot in pack_items:
        task_id = str(task_snapshot.get("taskId") or "")
        if not task_id or int(task_snapshot.get("pendingAttentionCount") or 0) < 3:
            continue
        preferred_run_id = str(task_snapshot.get("pendingReviewRunId") or "")
        task_items = items_by_task.get(task_id) or []
        if len(task_items) < 3:
            continue
        task_run_ids = []
        seen_task_runs: set[str] = set()
        for item in task_items:
            run_id = str(item.get("runId") or "")
            if not run_id or run_id in seen_task_runs:
                continue
            seen_task_runs.add(run_id)
            task_run_ids.append(run_id)
        if len(task_run_ids) < 2:
            continue
        candidate_run_ids = []
        if preferred_run_id:
            candidate_run_ids.append(preferred_run_id)
        candidate_run_ids.extend(run_id for run_id in task_run_ids if run_id != preferred_run_id)
        for run_id in candidate_run_ids:
            run_items = items_by_task_run.get((task_id, run_id)) or []
            other_task_items = [item for item in task_items if str(item.get("runId") or "") != run_id]
            if len(run_items) < 2 or not other_task_items:
                continue
            source_item = deepcopy(run_items[0])
            seeded_items = [deepcopy(item) for item in run_items[1:]]
            return {
                "task": deepcopy(task_snapshot),
                "taskId": task_id,
                "sourceItem": source_item,
                "seededItems": seeded_items,
                "otherTaskItems": [deepcopy(item) for item in other_task_items],
            }
    return None


def create_browser_review_current_task_fixture() -> dict[str, Any]:
    from ..service import (
        browser_sampling_task_lookup,
        default_browser_capture_review_queue_path,
        read_json_file,
        resolve_artifact_path,
        write_json_file,
    )

    candidate = _browser_review_current_task_fixture_candidate()
    if not candidate:
        raise ValueError("当前没有可用于 review_current_task 的 browser review fixture 候选。")

    source_item = deepcopy(candidate.get("sourceItem") or {})
    seeded_items = [deepcopy(item) for item in (candidate.get("seededItems") or []) if isinstance(item, dict)]
    source_run_id = str(source_item.get("runId") or "")
    source_queue_id = str(source_item.get("queueId") or "")
    task_id = str(candidate.get("taskId") or "")
    if not source_run_id or not source_queue_id or not task_id or not seeded_items:
        raise ValueError("review_current_task fixture 候选缺少必要字段。")

    detail = browser_capture_run_detail(source_run_id)
    if not detail:
        raise ValueError(f"找不到 source run 详情：{source_run_id}")
    review_queue_path = resolve_artifact_path(detail.get("reviewQueuePath")) or default_browser_capture_review_queue_path(
        Path(str(detail.get("manifestPath") or ""))
    )
    if not review_queue_path or not review_queue_path.exists():
        raise ValueError(f"找不到 source run 的 review_queue.json：{source_run_id}")
    original_review_queue = read_json_file(review_queue_path)
    if not isinstance(original_review_queue, list):
        raise ValueError(f"source run 的 review_queue.json 无法读取：{review_queue_path}")

    seed_queue_ids = {str(item.get("queueId") or "") for item in seeded_items if item.get("queueId")}
    if not seed_queue_ids:
        raise ValueError("review_current_task fixture 没有可预处理的 queue。")

    seeded_review_queue = deepcopy(original_review_queue)
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for item in seeded_review_queue:
        queue_id = str(item.get("queueId") or "")
        if queue_id not in seed_queue_ids:
            continue
        item["status"] = "resolved"
        item["resolutionNotes"] = "browser review smoke fixture: 预先收口同 run attention，制造 current-task relay 场景。"
        item["reviewOwner"] = "atlas-smoke-fixture"
        item["reviewedAt"] = reviewed_at
        item["replacementRunId"] = None
    write_json_file(review_queue_path, seeded_review_queue)

    try:
        refreshed_inbox = browser_review_inbox_payload(limit=None)
        refreshed_items = [item for item in (refreshed_inbox.get("items") or []) if isinstance(item, dict)]
        expected_target_item = next(
            (
                deepcopy(item)
                for item in refreshed_items
                if str(item.get("taskId") or "") == task_id and str(item.get("queueId") or "") != source_queue_id
            ),
            None,
        )
        if not expected_target_item:
            raise ValueError("fixture 写入后仍然找不到 review_current_task 的接力目标。")
        refreshed_source_detail = browser_capture_run_detail(source_run_id) or {}
        refreshed_pending_count = int((refreshed_source_detail.get("reviewSummary") or {}).get("pendingCount") or 0)
        if refreshed_pending_count != 1:
            raise ValueError(f"fixture 写入后 source run pendingCount 不是 1：{refreshed_pending_count}")
        task_snapshot = browser_sampling_task_lookup(task_id)
        if not task_snapshot or int(task_snapshot.get("pendingAttentionCount") or 0) <= 0:
            raise ValueError("fixture 写入后 task snapshot 没有保留 pending review 状态。")

        fixture_id = f"browser-review-current-task-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        fixture_manifest_path = browser_review_fixture_root() / f"{fixture_id}.json"
        fixture_manifest = {
            "fixtureId": fixture_id,
            "fixtureType": "review_current_task",
            "createdAt": reviewed_at,
            "sourceItem": source_item,
            "expectedTargetItem": expected_target_item,
            "seededQueueIds": sorted(seed_queue_ids),
            "task": deepcopy(task_snapshot),
            "reviewQueueBackup": {
                "runId": source_run_id,
                "reviewQueuePath": str(review_queue_path),
                "reviewQueue": original_review_queue,
            },
        }
        write_json_file(fixture_manifest_path, fixture_manifest)
        return {
            "fixtureId": fixture_id,
            "fixtureType": "review_current_task",
            "selectionReason": "seeded_review_current_task_fixture",
            "sourceItem": source_item,
            "expectedTargetItem": expected_target_item,
            "seededQueueIds": sorted(seed_queue_ids),
            "task": deepcopy(task_snapshot),
            "reviewInboxSummary": refreshed_inbox.get("summary") or {},
        }
    except Exception:
        write_json_file(review_queue_path, original_review_queue)
        raise


def restore_browser_review_fixture(fixture_id: str) -> dict[str, Any]:
    from ..service import clear_runtime_caches, read_json_file, write_json_file

    normalized_fixture_id = str(fixture_id or "").strip()
    if not normalized_fixture_id:
        raise ValueError("fixture_id 不能为空。")
    fixture_manifest_path = browser_review_fixture_root() / f"{normalized_fixture_id}.json"
    fixture_manifest = read_json_file(fixture_manifest_path)
    if not isinstance(fixture_manifest, dict):
        raise ValueError(f"找不到 browser review fixture：{normalized_fixture_id}")

    review_queue_backup = fixture_manifest.get("reviewQueueBackup") or {}
    review_queue_path = Path(str(review_queue_backup.get("reviewQueuePath") or ""))
    review_queue_payload = review_queue_backup.get("reviewQueue")
    if not review_queue_path or not isinstance(review_queue_payload, list):
        raise ValueError(f"browser review fixture 缺少有效备份：{normalized_fixture_id}")

    write_json_file(review_queue_path, review_queue_payload)
    try:
        fixture_manifest_path.unlink(missing_ok=True)
    except OSError:
        pass
    clear_runtime_caches()
    return {
        "fixtureId": normalized_fixture_id,
        "fixtureType": fixture_manifest.get("fixtureType"),
        "restored": True,
        "runId": review_queue_backup.get("runId"),
        "reviewQueuePath": str(review_queue_path),
    }


@lru_cache(maxsize=1)
def _browser_capture_task_history_index_cached() -> dict[str, dict[str, Any]]:
    from ..service import created_at_is_before

    latest_by_task: dict[str, dict[str, Any]] = {}
    capture_runs = list_browser_capture_runs(limit=80)
    grouped_counts: dict[str, int] = {}
    for item in capture_runs:
        task_id = str(item.get("taskId") or "")
        if not task_id:
            continue
        grouped_counts[task_id] = grouped_counts.get(task_id, 0) + 1
        current = latest_by_task.get(task_id)
        if current and not created_at_is_before(current.get("createdAt"), item.get("createdAt")):
            pass
        else:
            latest_by_task[task_id] = deepcopy(item)
    pending_by_task: dict[str, dict[str, Any]] = {}
    for inbox_item in browser_review_inbox_payload(limit=None).get("items") or []:
        task_id = str(inbox_item.get("taskId") or "")
        if not task_id:
            continue
        aggregate = pending_by_task.setdefault(
            task_id,
            {
                "pendingAttentionCount": 0,
                "pendingAttentionPreview": [],
                "pendingReviewRunId": None,
                "pendingReviewQueueId": None,
            },
        )
        aggregate["pendingAttentionCount"] += 1
        preview = aggregate["pendingAttentionPreview"]
        if len(preview) < 3:
            preview.append(
                {
                    "queueId": inbox_item.get("queueId"),
                    "runId": inbox_item.get("runId"),
                    "businessType": inbox_item.get("businessType"),
                    "businessTypeLabel": inbox_item.get("businessTypeLabel"),
                    "sourceListingId": inbox_item.get("sourceListingId"),
                    "attention": inbox_item.get("attention") or [],
                    "publishedAt": inbox_item.get("publishedAt"),
                }
            )
        if not aggregate.get("pendingReviewRunId"):
            aggregate["pendingReviewRunId"] = inbox_item.get("runId")
            aggregate["pendingReviewQueueId"] = inbox_item.get("queueId")
    for task_id, item in latest_by_task.items():
        history_count = grouped_counts.get(task_id, 0)
        pending_state = pending_by_task.get(task_id) or {}
        pending_attention_count = int(pending_state.get("pendingAttentionCount") or 0)
        item["captureHistoryCount"] = history_count
        item["pendingAttentionCount"] = pending_attention_count
        item["pendingAttentionPreview"] = pending_state.get("pendingAttentionPreview") or []
        item["pendingReviewRunId"] = pending_state.get("pendingReviewRunId")
        item["pendingReviewQueueId"] = pending_state.get("pendingReviewQueueId")
        item["taskLifecycleStatus"] = "needs_review" if pending_attention_count > 0 else "captured"
        item["taskLifecycleLabel"] = "已采待复核" if pending_attention_count > 0 else "已采仍需补采"
    return latest_by_task


def browser_capture_task_history_index() -> dict[str, dict[str, Any]]:
    return deepcopy(_browser_capture_task_history_index_cached())


def browser_sampling_pack(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    focus_scope: str | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    from ..service import (
        clamp,
        community_visible,
        current_community_dataset,
        floor_watchlist,
        import_run_detail_full,
        list_import_runs,
        opportunities,
        priority_districts,
        sample_status_label,
    )

    community_items = opportunities(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    )
    community_index = {item["id"]: item for item in current_community_dataset()}
    building_index = {
        building["id"]: (community, building)
        for community in community_index.values()
        for building in community.get("buildings", [])
    }
    capture_history_index = browser_capture_task_history_index()
    tasks: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str | None, int | None, str]] = set()
    priority_set = set(priority_districts())

    def in_scope(district_id: str | None) -> bool:
        if district not in (None, "", "all") and district_id != district:
            return False
        if focus_scope == "priority" and district_id not in priority_set:
            return False
        return True

    def register_task(task: dict[str, Any]) -> None:
        task_key = (
            str(task.get("communityId") or ""),
            str(task.get("buildingId") or "") or None,
            int(task["floorNo"]) if task.get("floorNo") is not None else None,
            str(task.get("taskType") or ""),
        )
        if task_key in seen_keys:
            return
        seen_keys.add(task_key)
        tasks.append(task)

    latest_import_run = list_import_runs()[0] if list_import_runs() else None
    latest_import_detail = import_run_detail_full(latest_import_run["runId"]) if latest_import_run else None
    floor_candidates = []
    if latest_import_detail:
        for evidence in latest_import_detail.get("floorEvidence", []):
            building_lookup = building_index.get(evidence.get("building_id"))
            if not building_lookup:
                continue
            community, building = building_lookup
            if not in_scope(community.get("districtId")):
                continue
            if not community_visible(
                community,
                district=district,
                min_yield=min_yield,
                max_budget=max_budget,
                min_samples=min_samples,
            ):
                continue
            floor_candidates.append(
                {
                    "communityId": community.get("id"),
                    "communityName": community.get("name"),
                    "districtId": community.get("districtId"),
                    "districtName": community.get("districtName"),
                    "buildingId": building.get("id"),
                    "buildingName": building.get("name"),
                    "floorNo": int(evidence.get("floor_no") or 0),
                    "latestYieldPct": float(evidence.get("yield_pct") or 0),
                    "latestPairCount": int(evidence.get("pair_count") or 0),
                    "latestBatchName": latest_import_detail.get("batchName"),
                    "latestCreatedAt": latest_import_detail.get("createdAt"),
                    "communityScore": float(community.get("score") or 0),
                    "buildingScore": float(building.get("score") or 0),
                    "yieldSpreadVsCommunity": round(float(evidence.get("yield_pct") or 0) - float(community.get("yield") or 0), 2),
                }
            )
    else:
        for item in floor_watchlist(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
            limit=max(limit * 2, 16),
        ):
            floor_candidates.append(item)

    floor_candidates.sort(
        key=lambda item: (
            float(item.get("buildingScore") or item.get("persistenceScore") or 0),
            float(item.get("latestYieldPct") or 0),
            -int(item.get("latestPairCount") or 0),
        ),
        reverse=True,
    )

    for item in floor_candidates:
        if not in_scope(item.get("districtId")):
            continue
        latest_pair_count = int(item.get("latestPairCount") or 0)
        target_pair_count = 4 if float(item.get("buildingScore") or item.get("persistenceScore") or 0) >= 82 else 3
        if latest_pair_count >= target_pair_count:
            continue
        missing_pair_count = max(target_pair_count - latest_pair_count, 1)
        priority_bonus = 12 if item.get("districtId") in priority_set else 0
        momentum_bonus = 8 if float(item.get("yieldSpreadVsCommunity") or item.get("windowYieldDeltaPct") or 0) > 0.08 else 0
        thin_sample_bonus = 12 if latest_pair_count <= 1 else 6 if latest_pair_count == 2 else 0
        priority_score = round(
            clamp(
                float(item.get("buildingScore") or item.get("communityScore") or item.get("persistenceScore") or 0)
                + priority_bonus
                + momentum_bonus
                + thin_sample_bonus,
                0,
                99,
            )
        )
        target_query = browser_sampling_query(
            district_name=item.get("districtName"),
            community_name=item.get("communityName") or "",
            building_name=item.get("buildingName"),
            floor_no=item.get("floorNo"),
        )
        register_task(
            {
                "taskId": f'browser-floor::{item.get("buildingId")}::{item.get("floorNo")}',
                "providerId": "public-browser-sampling",
                "taskType": "floor_pair_capture",
                "taskTypeLabel": browser_sampling_task_type_label("floor_pair_capture"),
                "targetGranularity": "floor",
                "focusScope": "priority" if item.get("districtId") in priority_set else "citywide",
                "priorityScore": priority_score,
                "priorityLabel": browser_sampling_priority_label(priority_score),
                "districtId": item.get("districtId"),
                "districtName": item.get("districtName"),
                "communityId": item.get("communityId"),
                "communityName": item.get("communityName"),
                "buildingId": item.get("buildingId"),
                "buildingName": item.get("buildingName"),
                "floorNo": item.get("floorNo"),
                "sampleStatus": "active_metrics",
                "sampleStatusLabel": sample_status_label("active_metrics"),
                "currentYieldPct": item.get("latestYieldPct"),
                "currentPairCount": latest_pair_count,
                "targetPairCount": target_pair_count,
                "missingPairCount": missing_pair_count,
                "currentSampleSize": latest_pair_count,
                "targetSampleSize": target_pair_count,
                "missingSampleCount": missing_pair_count,
                "trendLabel": item.get("trendLabel") or ("高于小区均值" if float(item.get("yieldSpreadVsCommunity") or 0) > 0 else "公开页补样"),
                "dataFreshness": item.get("latestCreatedAt"),
                "reason": f'{item.get("buildingName")} {item.get("floorNo")}层已经进入持续套利楼层榜，但当前只有 {latest_pair_count} 组配对样本，需要补齐公开 sale/rent 文本验证持续性。',
                "captureGoal": f'至少再补 {missing_pair_count} 组 sale/rent 配对，把该层样本提升到 {target_pair_count} 组。',
                "requiredFields": browser_sampling_required_fields("floor_pair_capture"),
                "targetQuery": target_query,
                "saleQuery": browser_sampling_query(
                    district_name=item.get("districtName"),
                    community_name=item.get("communityName") or "",
                    building_name=item.get("buildingName"),
                    floor_no=item.get("floorNo"),
                    business_type="sale",
                ),
                "rentQuery": browser_sampling_query(
                    district_name=item.get("districtName"),
                    community_name=item.get("communityName") or "",
                    building_name=item.get("buildingName"),
                    floor_no=item.get("floorNo"),
                    business_type="rent",
                ),
                "recommendedAction": "优先各补 1-2 条公开 sale / rent 页面文本，重点确认楼层、总层数、面积与挂牌总价 / 月租。",
            }
        )

    for community in community_items:
        if not in_scope(community.get("districtId")):
            continue
        building_candidates = sorted(
            community.get("buildings", []),
            key=lambda item: (
                float(item.get("score") or 0),
                float(item.get("yieldAvg") or 0),
                -int(item.get("sequenceNo") or 0),
            ),
            reverse=True,
        )
        for building in building_candidates:
            current_sample_size = int(building.get("sampleSize") or community.get("sample") or 0)
            target_sample_size = 6 if community.get("districtId") in priority_set else 5
            if current_sample_size >= target_sample_size:
                continue
            missing_sample_count = max(target_sample_size - current_sample_size, 1)
            priority_bonus = 10 if community.get("districtId") in priority_set else 0
            geometry_bonus = 0 if building.get("geometrySource") in {"database", "database_selected", "imported", "building_anchor"} else 6
            priority_score = round(
                clamp(
                    float(building.get("score") or community.get("score") or 0)
                    + priority_bonus
                    + missing_sample_count * 5
                    + geometry_bonus,
                    0,
                    99,
                )
            )
            register_task(
                {
                    "taskId": f'browser-building::{building.get("id")}',
                    "providerId": "public-browser-sampling",
                    "taskType": "building_depth_capture",
                    "taskTypeLabel": browser_sampling_task_type_label("building_depth_capture"),
                    "targetGranularity": "building",
                    "focusScope": "priority" if community.get("districtId") in priority_set else "citywide",
                    "priorityScore": priority_score,
                    "priorityLabel": browser_sampling_priority_label(priority_score),
                    "districtId": community.get("districtId"),
                    "districtName": community.get("districtName"),
                    "communityId": community.get("id"),
                    "communityName": community.get("name"),
                    "buildingId": building.get("id"),
                    "buildingName": building.get("name"),
                    "floorNo": None,
                    "sampleStatus": community.get("sampleStatus"),
                    "sampleStatusLabel": community.get("sampleStatusLabel") or sample_status_label(community.get("sampleStatus") or "dictionary_only"),
                    "currentYieldPct": building.get("yieldAvg"),
                    "currentPairCount": None,
                    "targetPairCount": None,
                    "missingPairCount": None,
                    "currentSampleSize": current_sample_size,
                    "targetSampleSize": target_sample_size,
                    "missingSampleCount": missing_sample_count,
                    "trendLabel": "楼栋样本偏薄",
                    "dataFreshness": building.get("dataFreshness") or community.get("dataFreshness"),
                    "reason": f'{community.get("name")} 的 {building.get("name")} 当前只有 {current_sample_size} 条聚合样本，楼栋分还高，适合继续向公开页面补深。',
                    "captureGoal": f'再补 {missing_sample_count} 条楼栋级公开样本，尽量覆盖两个楼层与 sale / rent 两个方向。',
                    "requiredFields": browser_sampling_required_fields("building_depth_capture"),
                    "targetQuery": browser_sampling_query(
                        district_name=community.get("districtName"),
                        community_name=community.get("name") or "",
                        building_name=building.get("name"),
                    ),
                    "saleQuery": browser_sampling_query(
                        district_name=community.get("districtName"),
                        community_name=community.get("name") or "",
                        building_name=building.get("name"),
                        business_type="sale",
                    ),
                    "rentQuery": browser_sampling_query(
                        district_name=community.get("districtName"),
                        community_name=community.get("name") or "",
                        building_name=building.get("name"),
                        business_type="rent",
                    ),
                    "recommendedAction": "优先补不同楼层的 sale / rent 公开号牌，确认楼栋内的回报梯度是否稳定存在。",
                }
            )
            break

    for community in community_items:
        if not in_scope(community.get("districtId")):
            continue
        current_sample_size = int(community.get("sample") or 0)
        target_sample_size = 6 if community.get("districtId") in priority_set else 5
        if current_sample_size >= target_sample_size:
            continue
        missing_sample_count = max(target_sample_size - current_sample_size, 1)
        priority_bonus = 8 if community.get("districtId") in priority_set else 0
        priority_score = round(
            clamp(
                float(community.get("score") or 0) + priority_bonus + missing_sample_count * 5,
                0,
                99,
            )
        )
        register_task(
            {
                "taskId": f'browser-community::{community.get("id")}',
                "providerId": "public-browser-sampling",
                "taskType": "community_profile_capture",
                "taskTypeLabel": browser_sampling_task_type_label("community_profile_capture"),
                "targetGranularity": "community",
                "focusScope": "priority" if community.get("districtId") in priority_set else "citywide",
                "priorityScore": priority_score,
                "priorityLabel": browser_sampling_priority_label(priority_score),
                "districtId": community.get("districtId"),
                "districtName": community.get("districtName"),
                "communityId": community.get("id"),
                "communityName": community.get("name"),
                "buildingId": None,
                "buildingName": None,
                "floorNo": None,
                "sampleStatus": community.get("sampleStatus"),
                "sampleStatusLabel": community.get("sampleStatusLabel") or sample_status_label(community.get("sampleStatus") or "dictionary_only"),
                "currentYieldPct": community.get("yield"),
                "currentPairCount": None,
                "targetPairCount": None,
                "missingPairCount": None,
                "currentSampleSize": current_sample_size,
                "targetSampleSize": target_sample_size,
                "missingSampleCount": missing_sample_count,
                "trendLabel": "小区样本偏薄",
                "dataFreshness": community.get("dataFreshness"),
                "reason": f'{community.get("name")} 已经进入全市研究盘面，但当前只有 {current_sample_size} 套聚合样本，建议继续扩到更稳的观察面。',
                "captureGoal": f'再补 {missing_sample_count} 条公开样本，尽量覆盖不同楼栋与不同总价带。',
                "requiredFields": browser_sampling_required_fields("community_profile_capture"),
                "targetQuery": browser_sampling_query(
                    district_name=community.get("districtName"),
                    community_name=community.get("name") or "",
                ),
                "saleQuery": browser_sampling_query(
                    district_name=community.get("districtName"),
                    community_name=community.get("name") or "",
                    business_type="sale",
                ),
                "rentQuery": browser_sampling_query(
                    district_name=community.get("districtName"),
                    community_name=community.get("name") or "",
                    business_type="rent",
                ),
                "recommendedAction": "先把小区层公开 sale / rent 页面补到可重复观察，再决定是否继续向楼栋和楼层下钻。",
            }
        )

    task_rank = {"floor_pair_capture": 0, "building_depth_capture": 1, "community_profile_capture": 2}
    tasks.sort(
        key=lambda item: (
            -float(item.get("priorityScore") or 0),
            task_rank.get(str(item.get("taskType")), 9),
            str(item.get("districtName") or ""),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )
    floor_quota = min(limit, max(4, math.ceil(limit * 0.5)))
    building_quota = min(limit, max(3, math.floor(limit * 0.3)))
    community_quota = min(limit, max(2, limit - floor_quota - building_quota))
    quotas = {
        "floor_pair_capture": floor_quota,
        "building_depth_capture": building_quota,
        "community_profile_capture": community_quota,
    }
    bucketed: dict[str, list[dict[str, Any]]] = {
        "floor_pair_capture": [],
        "building_depth_capture": [],
        "community_profile_capture": [],
    }
    for item in tasks:
        bucketed.setdefault(str(item.get("taskType")), []).append(item)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for task_type in ("floor_pair_capture", "building_depth_capture", "community_profile_capture"):
        for item in bucketed.get(task_type, [])[: quotas[task_type]]:
            selected.append(item)
            selected_ids.add(str(item.get("taskId")))
    if len(selected) < limit:
        for item in tasks:
            if str(item.get("taskId")) in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(str(item.get("taskId")))
            if len(selected) >= limit:
                break
    selected.sort(
        key=lambda item: (
            -float(item.get("priorityScore") or 0),
            task_rank.get(str(item.get("taskType")), 9),
            str(item.get("districtName") or ""),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )
    for item in selected:
        capture_history = capture_history_index.get(str(item.get("taskId") or ""))
        if capture_history:
            item.update(
                {
                    "captureHistoryCount": int(capture_history.get("captureHistoryCount") or 0),
                    "latestCaptureAt": capture_history.get("createdAt"),
                    "latestCaptureRunId": capture_history.get("runId"),
                    "latestCaptureImportRunId": capture_history.get("importRunId"),
                    "latestCaptureMetricsRunId": capture_history.get("metricsRunId"),
                    "latestCaptureAttentionCount": int(capture_history.get("attentionCount") or 0),
                    "latestCaptureAttentionPreview": capture_history.get("attentionPreview") or [],
                    "pendingReviewRunId": capture_history.get("pendingReviewRunId"),
                    "pendingReviewQueueId": capture_history.get("pendingReviewQueueId"),
                    "pendingAttentionCount": int(capture_history.get("pendingAttentionCount") or 0),
                    "pendingAttentionPreview": capture_history.get("pendingAttentionPreview") or [],
                    "taskLifecycleStatus": capture_history.get("taskLifecycleStatus") or "captured",
                    "taskLifecycleLabel": capture_history.get("taskLifecycleLabel") or "已采仍需补采",
                }
            )
        else:
            item.update(
                {
                    "captureHistoryCount": 0,
                    "latestCaptureAt": None,
                    "latestCaptureRunId": None,
                    "latestCaptureImportRunId": None,
                    "latestCaptureMetricsRunId": None,
                    "latestCaptureAttentionCount": 0,
                    "latestCaptureAttentionPreview": [],
                    "pendingReviewRunId": None,
                    "pendingReviewQueueId": None,
                    "pendingAttentionCount": 0,
                    "pendingAttentionPreview": [],
                    "taskLifecycleStatus": "needs_capture",
                    "taskLifecycleLabel": "待采样",
                }
            )
    return selected[:limit]


def browser_sampling_pack_payload(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    focus_scope: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    items = browser_sampling_pack(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        focus_scope=focus_scope,
        limit=limit,
    )
    recent_captures = list_browser_capture_runs(limit=8)
    review_inbox = browser_review_inbox_payload(district=district, limit=None)
    review_summary = review_inbox.get("summary") or {}
    return {
        "items": items,
        "recentCaptures": recent_captures,
        "reviewInbox": {
            "summary": review_summary,
            "items": (review_inbox.get("items") or [])[: min(limit, 8)],
        },
        "summary": {
            "taskCount": len(items),
            "floorTaskCount": sum(1 for item in items if item.get("taskType") == "floor_pair_capture"),
            "buildingTaskCount": sum(1 for item in items if item.get("taskType") == "building_depth_capture"),
            "communityTaskCount": sum(1 for item in items if item.get("taskType") == "community_profile_capture"),
            "priorityDistrictCount": sum(1 for item in items if item.get("focusScope") == "priority"),
            "latestDataFreshness": max((item.get("dataFreshness") or "" for item in items), default=None),
            "capturedTaskCount": sum(1 for item in items if int(item.get("captureHistoryCount") or 0) > 0),
            "attentionTaskCount": sum(1 for item in items if int(item.get("pendingAttentionCount") or 0) > 0),
            "pendingReviewQueueCount": int(review_summary.get("pendingQueueCount") or 0),
            "pendingReviewTaskCount": int(review_summary.get("pendingTaskCount") or 0),
            "recentCaptureCount": len(recent_captures),
            "latestCaptureAt": recent_captures[0].get("createdAt") if recent_captures else None,
        },
    }


def build_browser_sampling_pack_csv(
    *,
    district: str | None = None,
    min_yield: float = 0.0,
    max_budget: float = 10_000.0,
    min_samples: int = 0,
    focus_scope: str | None = None,
    limit: int = 50,
) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "task_id",
            "provider_id",
            "task_type",
            "task_type_label",
            "target_granularity",
            "focus_scope",
            "priority_score",
            "priority_label",
            "district_name",
            "community_name",
            "building_name",
            "floor_no",
            "sample_status",
            "sample_status_label",
            "current_yield_pct",
            "current_pair_count",
            "target_pair_count",
            "missing_pair_count",
            "current_sample_size",
            "target_sample_size",
            "missing_sample_count",
            "data_freshness",
            "reason",
            "capture_goal",
            "target_query",
            "sale_query",
            "rent_query",
            "required_fields",
            "recommended_action",
        ],
    )
    writer.writeheader()
    for item in browser_sampling_pack(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        focus_scope=focus_scope,
        limit=limit,
    ):
        writer.writerow(
            {
                "task_id": item.get("taskId"),
                "provider_id": item.get("providerId"),
                "task_type": item.get("taskType"),
                "task_type_label": item.get("taskTypeLabel"),
                "target_granularity": item.get("targetGranularity"),
                "focus_scope": item.get("focusScope"),
                "priority_score": item.get("priorityScore"),
                "priority_label": item.get("priorityLabel"),
                "district_name": item.get("districtName"),
                "community_name": item.get("communityName"),
                "building_name": item.get("buildingName"),
                "floor_no": item.get("floorNo"),
                "sample_status": item.get("sampleStatus"),
                "sample_status_label": item.get("sampleStatusLabel"),
                "current_yield_pct": item.get("currentYieldPct"),
                "current_pair_count": item.get("currentPairCount"),
                "target_pair_count": item.get("targetPairCount"),
                "missing_pair_count": item.get("missingPairCount"),
                "current_sample_size": item.get("currentSampleSize"),
                "target_sample_size": item.get("targetSampleSize"),
                "missing_sample_count": item.get("missingSampleCount"),
                "data_freshness": item.get("dataFreshness"),
                "reason": item.get("reason"),
                "capture_goal": item.get("captureGoal"),
                "target_query": item.get("targetQuery"),
                "sale_query": item.get("saleQuery"),
                "rent_query": item.get("rentQuery"),
                "required_fields": " / ".join(item.get("requiredFields") or []),
                "recommended_action": item.get("recommendedAction"),
            }
        )
    return output.getvalue()


def latest_public_browser_import_run() -> dict[str, Any] | None:
    from .runs import list_import_runs

    return next((item for item in list_import_runs() if item.get("providerId") == "public-browser-sampling"), None)


def browser_sampling_task_lookup(task_id: str | None) -> dict[str, Any] | None:
    if not task_id:
        return None
    return next((item for item in browser_sampling_pack(limit=200) if item.get("taskId") == task_id), None)


def browser_sampling_target_count(task: dict[str, Any] | None) -> int:
    if not isinstance(task, dict):
        return 0
    value = task.get("targetPairCount") if task.get("targetGranularity") == "floor" else task.get("targetSampleSize")
    return int(value or 0)


def browser_sampling_current_count(task: dict[str, Any] | None) -> int:
    if not isinstance(task, dict):
        return 0
    value = task.get("currentPairCount") if task.get("targetGranularity") == "floor" else task.get("currentSampleSize")
    return int(value or 0)


def browser_sampling_missing_count(task: dict[str, Any] | None) -> int:
    target_count = browser_sampling_target_count(task)
    current_count = browser_sampling_current_count(task)
    return max(target_count - current_count, 0)


def browser_sampling_progress_status(
    task: dict[str, Any] | None,
    *,
    pending_attention_count: int | None = None,
    current_count: int | None = None,
    target_count: int | None = None,
) -> str:
    resolved_current_count = browser_sampling_current_count(task) if current_count is None else int(current_count)
    resolved_target_count = browser_sampling_target_count(task) if target_count is None else int(target_count)
    resolved_pending_attention_count = int((task or {}).get("pendingAttentionCount") or 0) if pending_attention_count is None else int(pending_attention_count)
    if resolved_pending_attention_count > 0:
        return "needs_review"
    if resolved_target_count > 0 and resolved_current_count >= resolved_target_count:
        return "resolved"
    if resolved_current_count > 0 or int((task or {}).get("captureHistoryCount") or 0) > 0:
        return "in_progress"
    return "needs_capture"


def merge_structured_capture_rows(
    base_rows: list[dict[str, Any]],
    new_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from ..service import BROWSER_CAPTURE_INPUT_FIELDS

    row_index: dict[tuple[str, str], dict[str, Any]] = {}
    merged_rows: list[dict[str, Any]] = []

    for row in base_rows:
        key = (str(row.get("source") or ""), str(row.get("source_listing_id") or ""))
        if key in row_index:
            continue
        normalized_row = {field: row.get(field, "") for field in set(BROWSER_CAPTURE_INPUT_FIELDS) | set(row.keys())}
        row_index[key] = normalized_row
        merged_rows.append(normalized_row)

    for row in new_rows:
        key = (str(row.get("source") or ""), str(row.get("source_listing_id") or ""))
        normalized_row = {field: row.get(field, "") for field in set(BROWSER_CAPTURE_INPUT_FIELDS) | set(row.keys())}
        if key in row_index:
            existing = row_index[key]
            existing.update(normalized_row)
            continue
        row_index[key] = normalized_row
        merged_rows.append(normalized_row)

    return merged_rows


def submit_browser_sampling_capture(payload: dict[str, Any]) -> dict[str, Any]:
    from jobs.import_public_browser_capture import RENT_OUTPUT_FIELDS, SALE_OUTPUT_FIELDS, build_structured_row

    from ..service import (
        BROWSER_CAPTURE_INPUT_FIELDS,
        ROOT_DIR,
        import_manifest_path_for_run,
        read_csv_rows,
        read_json_file,
        refresh_metrics_snapshot,
        resolve_artifact_path,
        slugify_identifier,
        write_csv_rows,
        write_json_file,
    )

    captures = payload.get("captures")
    if not isinstance(captures, list) or not captures:
        raise ValueError("至少需要 1 条公开页面采样记录。")

    task_snapshot = payload.get("task") if isinstance(payload.get("task"), dict) else None
    task_lookup = browser_sampling_task_lookup(payload.get("task_id")) or task_snapshot or {}
    before_task_snapshot = deepcopy(task_lookup if isinstance(task_lookup, dict) else task_snapshot if isinstance(task_snapshot, dict) else {})
    community_name_default = (
        payload.get("community_name")
        or task_lookup.get("communityName")
        or task_snapshot.get("communityName")
        if isinstance(task_snapshot, dict)
        else task_lookup.get("communityName")
    )
    building_name_default = (
        payload.get("building_name")
        or task_lookup.get("buildingName")
        or task_snapshot.get("buildingName")
        if isinstance(task_snapshot, dict)
        else task_lookup.get("buildingName")
    )
    floor_no_default = payload.get("floor_no") or task_lookup.get("floorNo")
    address_text_default = " ".join(
        part
        for part in [community_name_default, building_name_default]
        if part
    )
    batch_hint = payload.get("batch_name") or payload.get("batchName") or "public-browser-sampling-ui"
    batch_slug = slugify_identifier(batch_hint)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    capture_run_id = f"{batch_slug}-{timestamp}"
    capture_run_dir = browser_capture_runs_root() / capture_run_id
    import_output_dir = ROOT_DIR / "tmp" / "import-runs" / capture_run_id
    metrics_batch_name = f"staged-metrics-{datetime.now().date().isoformat()}-capture-{timestamp}"

    latest_run = latest_public_browser_import_run()
    if not latest_run:
        raise ValueError("当前还没有可作为基线的 public-browser-sampling import run。请先物化一版 staged 公开样本。")
    latest_manifest_path = import_manifest_path_for_run(str(latest_run.get("runId")))
    latest_manifest = read_json_file(latest_manifest_path) if latest_manifest_path else None
    if not isinstance(latest_manifest, dict):
        raise ValueError("找不到最新 public-browser-sampling 批次的 manifest，无法合并新采样。")
    latest_inputs = latest_manifest.get("inputs", {})
    base_sale_path = resolve_artifact_path(latest_inputs.get("sale_file"))
    base_rent_path = resolve_artifact_path(latest_inputs.get("rent_file"))
    if not base_sale_path or not base_sale_path.exists() or not base_rent_path or not base_rent_path.exists():
        raise ValueError("最新 public-browser-sampling 批次缺少原始 sale/rent CSV 输入，暂时无法继续追加采样。")

    input_rows: list[dict[str, Any]] = []
    parsed_rows: list[dict[str, Any]] = []
    structured_sale_rows: list[dict[str, Any]] = []
    structured_rent_rows: list[dict[str, Any]] = []
    attention_items: list[dict[str, Any]] = []

    for index, capture in enumerate(captures, start=1):
        if not isinstance(capture, dict):
            raise ValueError(f"第 {index} 条采样记录格式无效。")
        business_type = str(capture.get("business_type") or "").strip().lower()
        if business_type not in {"sale", "rent"}:
            raise ValueError(f"第 {index} 条采样记录缺少合法的 business_type。")
        raw_text = str(capture.get("raw_text") or "").strip()
        if not raw_text:
            raise ValueError(f"第 {index} 条采样记录缺少 raw_text。")
        source_listing_id = str(capture.get("source_listing_id") or "").strip()
        if not source_listing_id:
            raise ValueError(f"第 {index} 条采样记录缺少 source_listing_id。")
        url = str(capture.get("url") or "").strip()
        if not url:
            raise ValueError(f"第 {index} 条采样记录缺少 url。")
        published_at = str(capture.get("published_at") or "").strip()
        if not published_at:
            raise ValueError(f"第 {index} 条采样记录缺少 published_at。")
        community_name = str(capture.get("community_name") or community_name_default or "").strip()
        if not community_name:
            raise ValueError(f"第 {index} 条采样记录缺少 community_name，且当前任务也没有提供默认小区。")

        input_row = {
            "source": str(capture.get("source") or "public-browser-sampling").strip() or "public-browser-sampling",
            "source_listing_id": source_listing_id,
            "business_type": business_type,
            "url": url,
            "community_name": community_name,
            "address_text": str(capture.get("address_text") or address_text_default or community_name).strip(),
            "building_text": str(capture.get("building_text") or building_name_default or "").strip(),
            "unit_text": str(capture.get("unit_text") or "").strip(),
            "floor_text": str(capture.get("floor_text") or "").strip(),
            "total_floors": capture.get("total_floors") or "",
            "area_sqm": capture.get("area_sqm") or "",
            "bedrooms": capture.get("bedrooms") or "",
            "living_rooms": capture.get("living_rooms") or "",
            "bathrooms": capture.get("bathrooms") or "",
            "orientation": str(capture.get("orientation") or "").strip(),
            "decoration": str(capture.get("decoration") or "").strip(),
            "price_total_wan": capture.get("price_total_wan") or "",
            "unit_price_yuan": capture.get("unit_price_yuan") or "",
            "monthly_rent": capture.get("monthly_rent") or "",
            "published_at": published_at,
            "raw_text": raw_text,
            "capture_notes": str(capture.get("capture_notes") or capture.get("note") or "").strip(),
        }
        structured_row, parse_record = build_structured_row(input_row)
        input_rows.append(input_row)
        parsed_rows.append(parse_record)
        if parse_record.get("attention"):
            attention_items.append(parse_record)
        if business_type == "sale":
            structured_sale_rows.append(structured_row)
        else:
            structured_rent_rows.append(structured_row)

    capture_run_dir.mkdir(parents=True, exist_ok=True)
    capture_csv_path = capture_run_dir / "capture_rows.csv"
    review_queue_path = capture_run_dir / "review_queue.json"
    write_csv_rows(capture_csv_path, BROWSER_CAPTURE_INPUT_FIELDS, input_rows)
    write_json_file(capture_run_dir / "task_context.json", task_lookup or task_snapshot or {})
    write_json_file(capture_run_dir / "parsed_captures.json", parsed_rows)
    write_csv_rows(capture_run_dir / "captured_sale.csv", SALE_OUTPUT_FIELDS, structured_sale_rows)
    write_csv_rows(capture_run_dir / "captured_rent.csv", RENT_OUTPUT_FIELDS, structured_rent_rows)
    _, attention_detail_rows = build_browser_capture_detail_rows(input_rows, parsed_rows)
    review_queue = build_browser_capture_review_queue(attention_detail_rows)
    write_json_file(review_queue_path, review_queue)

    merged_sale_rows = merge_structured_capture_rows(read_csv_rows(base_sale_path), structured_sale_rows)
    merged_rent_rows = merge_structured_capture_rows(read_csv_rows(base_rent_path), structured_rent_rows)
    merged_sale_path = capture_run_dir / "merged_sale.csv"
    merged_rent_path = capture_run_dir / "merged_rent.csv"
    write_csv_rows(merged_sale_path, SALE_OUTPUT_FIELDS, merged_sale_rows)
    write_csv_rows(merged_rent_path, RENT_OUTPUT_FIELDS, merged_rent_rows)

    import_command = [
        sys.executable,
        str(ROOT_DIR / "jobs" / "import_authorized_listings.py"),
        "--provider-id",
        "public-browser-sampling",
        "--batch-name",
        capture_run_id,
        "--sale-file",
        str(merged_sale_path),
        "--rent-file",
        str(merged_rent_path),
        "--output-dir",
        str(import_output_dir),
    ]
    try:
        import_completed = subprocess.run(
            import_command,
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - surfaced via API
        stderr = (exc.stderr or exc.stdout or "").strip()
        raise ValueError(f"公开页面采样导入失败: {stderr or exc}") from exc
    import_result = json.loads(import_completed.stdout.strip() or "{}")

    refresh_metrics = bool(payload.get("refresh_metrics", True))
    metrics_result: dict[str, Any] | None = None
    if refresh_metrics:
        try:
            metrics_result = refresh_metrics_snapshot(
                snapshot_date=datetime.now().date(),
                batch_name=metrics_batch_name,
                trigger_source="browser-sampling",
            ).get("metricsRun")
        except Exception as exc:  # pragma: no cover - surfaced via API
            raise ValueError(f"指标快照刷新失败: {exc}") from exc

    manifest = {
        "run_id": capture_run_id,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "provider_id": "public-browser-sampling",
        "task_id": payload.get("task_id"),
        "task_snapshot": task_lookup or task_snapshot or {},
        "base_import_run_id": latest_run.get("runId"),
        "summary": {
            "capture_count": len(input_rows),
            "sale_capture_count": len(structured_sale_rows),
            "rent_capture_count": len(structured_rent_rows),
            "attention_count": len(attention_items),
            "merged_sale_count": len(merged_sale_rows),
            "merged_rent_count": len(merged_rent_rows),
        },
        "outputs": {
            "capture_csv": str(capture_csv_path),
            "captured_sale_csv": str(capture_run_dir / "captured_sale.csv"),
            "captured_rent_csv": str(capture_run_dir / "captured_rent.csv"),
            "merged_sale_csv": str(merged_sale_path),
            "merged_rent_csv": str(merged_rent_path),
            "parsed_captures": str(capture_run_dir / "parsed_captures.json"),
            "review_queue": str(review_queue_path),
            "task_context": str(capture_run_dir / "task_context.json"),
            "import_run_dir": str(import_output_dir),
        },
        "attention": attention_items[:10],
        "import_result": import_result,
        "metrics_result": metrics_result,
    }
    write_json_file(capture_run_dir / "manifest.json", manifest)
    supersede_browser_capture_review_items(
        task_id=payload.get("task_id"),
        replacement_run_id=capture_run_id,
        review_queue=review_queue,
    )

    refreshed_pack = browser_sampling_pack(limit=200)
    refreshed_task_snapshot = next(
        (item for item in refreshed_pack if item.get("taskId") == payload.get("task_id")),
        None,
    )

    before_count = browser_sampling_current_count(before_task_snapshot)
    before_target_count = browser_sampling_target_count(before_task_snapshot)
    inferred_increment = (
        1
        if str(before_task_snapshot.get("targetGranularity") or "") == "floor" and captures
        else len(captures)
    )
    fallback_target_count = before_target_count
    fallback_after_count = before_count + inferred_increment
    if fallback_target_count > 0:
        fallback_after_count = min(fallback_after_count, fallback_target_count)

    after_count = (
        browser_sampling_current_count(refreshed_task_snapshot)
        if refreshed_task_snapshot is not None
        else fallback_after_count
    )
    target_count = (
        browser_sampling_target_count(refreshed_task_snapshot)
        if refreshed_task_snapshot is not None
        else fallback_target_count
    )
    missing_count = (
        browser_sampling_missing_count(refreshed_task_snapshot)
        if refreshed_task_snapshot is not None
        else max(target_count - after_count, 0)
    )
    attention_count = len(attention_items)
    review_summary = browser_capture_review_summary(review_queue)
    pending_attention_count = int(review_summary.get("pendingCount") or 0)
    effective_pending_attention_count = (
        int((refreshed_task_snapshot or {}).get("pendingAttentionCount") or 0)
        if refreshed_task_snapshot is not None
        else pending_attention_count
    )
    task_progress_status = browser_sampling_progress_status(
        refreshed_task_snapshot or before_task_snapshot,
        pending_attention_count=effective_pending_attention_count,
        current_count=after_count,
        target_count=target_count,
    )

    candidate_capture_tasks = [
        item
        for item in refreshed_pack
        if item.get("taskId") != payload.get("task_id")
        and browser_sampling_progress_status(item) in {"needs_capture", "in_progress"}
    ]
    same_district_capture_tasks = [
        item for item in candidate_capture_tasks if item.get("districtId") == before_task_snapshot.get("districtId")
    ]
    workflow_task = deepcopy(refreshed_task_snapshot or before_task_snapshot)
    if pending_attention_count > 0:
        workflow_action = "review_current_capture"
        workflow_reason = "attention_detected"
    elif same_district_capture_tasks:
        workflow_action = "advance_next_capture"
        workflow_reason = "same_district_queue_available"
        workflow_task = deepcopy(same_district_capture_tasks[0])
    elif candidate_capture_tasks:
        workflow_action = "advance_next_capture"
        workflow_reason = "global_queue_available"
        workflow_task = deepcopy(candidate_capture_tasks[0])
    else:
        workflow_action = "stay_current"
        workflow_reason = "no_pending_task"

    task_response = deepcopy(refreshed_task_snapshot or before_task_snapshot)
    if task_response:
        if str(task_response.get("targetGranularity") or "") == "floor":
            task_response["currentPairCount"] = after_count
            task_response["targetPairCount"] = target_count
            task_response["missingPairCount"] = missing_count
        task_response["currentSampleSize"] = after_count
        task_response["targetSampleSize"] = target_count
        task_response["missingSampleCount"] = missing_count
        if refreshed_task_snapshot is None:
            task_response["captureHistoryCount"] = int(task_response.get("captureHistoryCount") or 0) + 1
        task_response["latestCaptureAt"] = manifest["created_at"]
        task_response["latestCaptureRunId"] = capture_run_id
        task_response["latestCaptureImportRunId"] = import_result.get("run_id")
        task_response["latestCaptureMetricsRunId"] = metrics_result.get("runId") if metrics_result else None
        task_response["latestCaptureAttentionCount"] = attention_count
        task_response["latestCaptureAttentionPreview"] = attention_items[:3]
        task_response["pendingReviewRunId"] = (
            refreshed_task_snapshot.get("pendingReviewRunId")
            if refreshed_task_snapshot is not None
            else (capture_run_id if pending_attention_count > 0 else None)
        )
        task_response["pendingReviewQueueId"] = (
            refreshed_task_snapshot.get("pendingReviewQueueId")
            if refreshed_task_snapshot is not None
            else (
                next(
                    (
                        item.get("queueId")
                        for item in review_queue
                        if str(item.get("status") or "pending") == "pending" and item.get("queueId")
                    ),
                    None,
                )
                if pending_attention_count > 0
                else None
            )
        )
        task_response["pendingAttentionCount"] = (
            int(refreshed_task_snapshot.get("pendingAttentionCount") or 0)
            if refreshed_task_snapshot is not None
            else pending_attention_count
        )
        task_response["pendingAttentionPreview"] = (
            refreshed_task_snapshot.get("pendingAttentionPreview") or []
            if refreshed_task_snapshot is not None
            else review_queue[:3]
        )
        task_response["taskLifecycleStatus"] = "needs_review" if int(task_response.get("pendingAttentionCount") or 0) > 0 else "captured"
        task_response["taskLifecycleLabel"] = "已采待复核" if int(task_response.get("pendingAttentionCount") or 0) > 0 else "已采仍需补采"

    return {
        "captureRunId": capture_run_id,
        "captureOutputDir": str(capture_run_dir),
        "baseImportRunId": latest_run.get("runId"),
        "importRunId": import_result.get("run_id"),
        "importOutputDir": import_result.get("output_dir"),
        "metricsRun": metrics_result,
        "summary": manifest["summary"],
        "attention": manifest["attention"],
        "reviewSummary": review_summary,
        "reviewInboxSummary": browser_review_inbox_payload(limit=None).get("summary") or {},
        "workflow": {
            "action": workflow_action,
            "reason": workflow_reason,
            "taskId": workflow_task.get("taskId") if isinstance(workflow_task, dict) else None,
            "task": workflow_task,
        },
        "taskProgress": {
            "beforeCount": before_count,
            "afterCount": after_count,
            "targetCount": target_count,
            "missingCount": missing_count,
            "status": task_progress_status,
        },
        "task": task_response,
    }


def normalize_browser_capture_review_update(
    status: str,
    resolution_notes: str | None = None,
) -> tuple[str, str]:
    normalized_status = str(status or "").strip().lower()
    if normalized_status not in {"resolved", "waived"}:
        raise ValueError("公开页采样 review queue 只支持 resolved / waived。")
    normalized_notes = str(resolution_notes or "").strip()
    if normalized_status == "waived" and not normalized_notes:
        raise ValueError("标记豁免时必须填写原因。")
    return normalized_status, normalized_notes


def default_browser_capture_review_resolution_note(status: str) -> str:
    return "已由工作台人工确认并完成修正。" if status == "resolved" else "已人工确认当前缺失可接受。"


def browser_capture_review_workflow(
    detail: dict[str, Any] | None,
    task_state: dict[str, Any] | None,
    review_inbox: dict[str, Any] | None,
) -> dict[str, Any]:
    review_items = (review_inbox or {}).get("items") or []
    current_detail = detail or {}
    current_task_snapshot = deepcopy(task_state or current_detail.get("task") or {})
    current_task_id = str(current_task_snapshot.get("taskId") or current_detail.get("task", {}).get("taskId") or current_detail.get("taskId") or "")
    if current_task_id:
        current_task_snapshot.setdefault("taskId", current_task_id)
    current_task_snapshot.setdefault("districtId", current_detail.get("task", {}).get("districtId") or current_detail.get("districtId"))
    current_task_snapshot.setdefault("districtName", current_detail.get("task", {}).get("districtName") or current_detail.get("districtName"))
    current_task_snapshot.setdefault("communityId", current_detail.get("task", {}).get("communityId") or current_detail.get("communityId"))
    current_task_snapshot.setdefault("communityName", current_detail.get("task", {}).get("communityName") or current_detail.get("communityName"))
    current_task_snapshot.setdefault("buildingId", current_detail.get("task", {}).get("buildingId") or current_detail.get("buildingId"))
    current_task_snapshot.setdefault("buildingName", current_detail.get("task", {}).get("buildingName") or current_detail.get("buildingName"))
    current_task_snapshot.setdefault("floorNo", current_detail.get("task", {}).get("floorNo") or current_detail.get("floorNo"))
    current_task_snapshot.setdefault("taskType", current_detail.get("task", {}).get("taskType") or current_detail.get("taskType"))
    current_task_snapshot.setdefault(
        "taskTypeLabel",
        current_detail.get("task", {}).get("taskTypeLabel")
        or current_detail.get("taskTypeLabel")
        or browser_sampling_task_type_label(str(current_task_snapshot.get("taskType") or "")),
    )
    current_task_snapshot["taskLifecycleStatus"] = "needs_review"
    current_task_snapshot["taskLifecycleLabel"] = "已采待复核"
    current_district_id = str(
        current_task_snapshot.get("districtId")
        or current_detail.get("task", {}).get("districtId")
        or current_detail.get("districtId")
        or ""
    )
    current_run_id = str(current_detail.get("runId") or "")
    current_run_created_at = str(current_detail.get("createdAt") or "") or None
    current_run_pending_count = int((current_detail.get("reviewSummary") or {}).get("pendingCount") or 0)
    current_task_pending_count = int(current_task_snapshot.get("pendingAttentionCount") or current_run_pending_count or 0)
    current_run_pending_item = next(
        (
            item
            for item in current_detail.get("reviewQueue") or []
            if isinstance(item, dict) and str(item.get("status") or "pending") == "pending" and item.get("queueId")
        ),
        None,
    )
    if current_run_pending_count > 0 and current_run_pending_item:
        workflow_item = browser_capture_review_workflow_item_payload(
            run_id=current_run_id,
            run_created_at=current_run_created_at,
            review_item=current_run_pending_item,
            task_snapshot=current_task_snapshot,
            run_pending_count=current_run_pending_count,
            task_pending_count=current_task_pending_count or current_run_pending_count,
        )
        return browser_capture_review_workflow_payload(
            "review_current_run",
            "current_run_pending_remaining",
            task=current_task_snapshot,
            item=workflow_item,
        )
    current_task_item = next(
        (
            item
            for item in review_items
            if str(item.get("taskId") or "") == current_task_id
            and (
                not str((task_state or {}).get("pendingReviewRunId") or "")
                or str(item.get("runId") or "") == str((task_state or {}).get("pendingReviewRunId") or "")
                or (
                    str((task_state or {}).get("pendingReviewQueueId") or "")
                    and str(item.get("queueId") or "") == str((task_state or {}).get("pendingReviewQueueId") or "")
                )
            )
        ),
        None,
    )
    if int((task_state or {}).get("pendingAttentionCount") or 0) > 0 and (task_state or {}).get("pendingReviewRunId"):
        return browser_capture_review_workflow_payload(
            "review_current_task",
            "current_task_pending_remaining",
            task=current_task_snapshot,
            item=current_task_item,
        )
    same_district_next = next(
        (
            item
            for item in review_items
            if str(item.get("taskId") or "") != current_task_id
            and current_district_id
            and str(item.get("districtId") or "") == current_district_id
        ),
        None,
    )
    global_next = next((item for item in review_items if str(item.get("taskId") or "") != current_task_id), None)
    if same_district_next:
        return browser_capture_review_workflow_payload(
            "advance_next_review",
            "same_district_review_available",
            task=current_task_snapshot,
            item=same_district_next,
        )
    if global_next:
        return browser_capture_review_workflow_payload(
            "advance_next_review",
            "global_review_available",
            task=current_task_snapshot,
            item=global_next,
        )
    return browser_capture_review_workflow_payload(
        "stay_current",
        "review_queue_cleared",
        task=current_task_snapshot,
    )


def apply_browser_capture_review_queue_update(
    run_id: str,
    queue_ids: list[str] | tuple[str, ...],
    *,
    status: str,
    resolution_notes: str | None = None,
    review_owner: str = "atlas-ui",
    pending_only: bool = False,
) -> dict[str, Any] | None:
    from ..service import default_browser_capture_review_queue_path, resolve_artifact_path, write_json_file

    normalized_status, normalized_notes = normalize_browser_capture_review_update(status, resolution_notes)
    detail = browser_capture_run_detail(run_id)
    if not detail:
        return None
    if isinstance(queue_ids, (str, bytes)) or not isinstance(queue_ids, (list, tuple)):
        raise ValueError("公开页采样 review queue 必须指定至少一个 queueId。")

    normalized_queue_ids: list[str] = []
    seen_queue_ids: set[str] = set()
    for queue_id in queue_ids:
        normalized_queue_id = str(queue_id or "").strip()
        if not normalized_queue_id or normalized_queue_id in seen_queue_ids:
            continue
        seen_queue_ids.add(normalized_queue_id)
        normalized_queue_ids.append(normalized_queue_id)
    if not normalized_queue_ids:
        raise ValueError("公开页采样 review queue 必须指定至少一个 queueId。")

    review_queue = deepcopy(detail.get("reviewQueue") or [])
    review_queue_index = {
        str(item.get("queueId") or ""): item
        for item in review_queue
        if isinstance(item, dict) and item.get("queueId")
    }
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    default_note = default_browser_capture_review_resolution_note(normalized_status)
    updated_items: list[dict[str, Any]] = []
    skipped_items: list[dict[str, Any]] = []

    for queue_id in normalized_queue_ids:
        target_item = review_queue_index.get(queue_id)
        if not target_item:
            skipped_items.append(
                {
                    "queueId": queue_id,
                    "reason": "not_found",
                }
            )
            continue
        current_status = str(target_item.get("status") or "pending")
        if current_status == "superseded":
            skipped_items.append(
                {
                    "queueId": queue_id,
                    "reason": "superseded",
                    "queueItem": deepcopy(target_item),
                }
            )
            continue
        if pending_only and current_status != "pending":
            skipped_items.append(
                {
                    "queueId": queue_id,
                    "reason": "not_pending",
                    "queueItem": deepcopy(target_item),
                }
            )
            continue
        target_item["status"] = normalized_status
        target_item["resolutionNotes"] = normalized_notes or default_note
        target_item["reviewOwner"] = review_owner
        target_item["reviewedAt"] = reviewed_at
        target_item["replacementRunId"] = None
        updated_items.append(deepcopy(target_item))

    if updated_items:
        review_queue_path = resolve_artifact_path(detail.get("reviewQueuePath")) or default_browser_capture_review_queue_path(
            Path(str(detail.get("manifestPath") or ""))
        )
        write_json_file(review_queue_path, review_queue)

    updated_detail = browser_capture_run_detail(run_id)
    task_state = browser_sampling_task_lookup(str(detail.get("task", {}).get("taskId") or detail.get("taskId") or ""))
    review_inbox = browser_review_inbox_payload(limit=None)
    workflow = browser_capture_review_workflow(updated_detail or detail, task_state, review_inbox)
    return {
        "runId": run_id,
        "queueIds": normalized_queue_ids,
        "status": normalized_status,
        "reviewOwner": review_owner,
        "reviewedAt": reviewed_at,
        "updatedQueueItems": updated_items,
        "skippedQueueItems": skipped_items,
        "reviewSummary": (updated_detail or {}).get("reviewSummary") or browser_capture_review_summary(review_queue),
        "reviewInboxSummary": review_inbox.get("summary") or {},
        "workflow": workflow,
        "task": task_state,
        "detail": updated_detail,
    }


def update_browser_capture_review_queue(
    run_id: str,
    queue_id: str,
    *,
    status: str,
    resolution_notes: str | None = None,
    review_owner: str = "atlas-ui",
) -> dict[str, Any] | None:
    result = apply_browser_capture_review_queue_update(
        run_id,
        [queue_id],
        status=status,
        resolution_notes=resolution_notes,
        review_owner=review_owner,
        pending_only=False,
    )
    if not result:
        return None
    if not result.get("updatedQueueItems"):
        skipped_item = (result.get("skippedQueueItems") or [{}])[0]
        if str(skipped_item.get("reason") or "") == "superseded":
            raise ValueError("该 attention 已由后续修正采样接管，不能再手动复核。")
        return None
    queue_item = deepcopy((result.get("updatedQueueItems") or [None])[0])
    return {
        "runId": run_id,
        "queueId": queue_id,
        "status": result.get("status"),
        "reviewOwner": result.get("reviewOwner"),
        "reviewedAt": result.get("reviewedAt"),
        "queueItem": queue_item,
        "reviewSummary": result.get("reviewSummary") or {},
        "reviewInboxSummary": result.get("reviewInboxSummary") or {},
        "workflow": result.get("workflow") or {},
        "task": result.get("task"),
        "detail": result.get("detail"),
    }


def update_browser_capture_review_queue_batch(
    run_id: str,
    queue_ids: list[str] | tuple[str, ...],
    *,
    status: str,
    resolution_notes: str | None = None,
    review_owner: str = "atlas-ui",
) -> dict[str, Any] | None:
    return apply_browser_capture_review_queue_update(
        run_id,
        queue_ids,
        status=status,
        resolution_notes=resolution_notes,
        review_owner=review_owner,
        pending_only=True,
    )
