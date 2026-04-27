"""
Browser sampling + capture review aggregation for the backstage tool.

Phase 7b extraction from api/service.py — covers browser_sampling labels
and query helpers, browser_capture run-summary/detail/manifest helpers,
and the review-queue build/supersede pipeline. Re-exported from api.service
for back-compat. Inbox/workflow/sampling-pack/submit clusters remain in
api/service.py and will move in subsequent sub-phases.
"""

from __future__ import annotations

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
