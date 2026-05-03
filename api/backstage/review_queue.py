"""
Browser-capture review-queue mutation helpers.

Extracted from api/backstage/review.py. Owns the normalization, single-update,
batch-update and workflow-resolution paths used when an operator marks
attention items as resolved/waived.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from .sampling_labels import browser_sampling_task_type_label


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
    from .review import (
        browser_capture_review_workflow_item_payload,
        browser_capture_review_workflow_payload,
    )

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
    from .review import (
        browser_capture_review_summary,
        browser_capture_run_detail,
        browser_review_inbox_payload,
        browser_sampling_task_lookup,
    )

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
