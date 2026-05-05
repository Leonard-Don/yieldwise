"""
Public-browser sampling capture submit pipeline.

Extracted from api/backstage/review.py. Owns the heavy submit-capture
workflow: receives UI capture payloads, parses, merges, runs the
import + metrics jobs and computes the next-step workflow hint.
"""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime
from typing import Any


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
    from .review import (
        browser_capture_review_summary,
        browser_capture_runs_root,
        browser_review_inbox_payload,
        browser_sampling_current_count,
        browser_sampling_missing_count,
        browser_sampling_pack,
        browser_sampling_progress_status,
        browser_sampling_target_count,
        browser_sampling_task_lookup,
        build_browser_capture_detail_rows,
        build_browser_capture_review_queue,
        latest_public_browser_import_run,
        merge_structured_capture_rows,
        supersede_browser_capture_review_items,
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
        str(ROOT_DIR / "jobs" / "import_browser_scraped_listings.py"),
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
