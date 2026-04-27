"""
Geo asset / coverage task / work-order helpers for the backstage tool.

Phase 7e1+7e2+7e3 extraction from api/service.py — covers manifest path
defaults, db_*_rows queries, baseline-run lookup, task derivation/
summary/enrichment, work-order summary/sort/filter helpers, label/
status/priority helpers, the impact-score enrichment pipeline, the
detail/comparison/watchlist cluster, and the work-order CRUD pipeline
(rebuild_geo_asset_summary, update_geo_asset_task_review, geo_asset_work_orders,
create/update_geo_asset_work_order). Re-exported from api.service for
back-compat.
"""

from __future__ import annotations

import json
import math
from copy import deepcopy
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..persistence import postgres_data_snapshot, query_row, query_rows


def default_geo_task_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "coverage_tasks.json"


def default_geo_review_history_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "review_history.json"


def default_geo_work_order_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "work_orders.json"


def default_geo_work_order_event_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "work_order_events.json"


def db_geo_asset_rows(geo_run_id: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    where_clause = ""
    if geo_run_id:
        where_clause = "AND ir.external_run_id = %s"
        params.append(geo_run_id)
    return query_rows(
        f"""
        SELECT
            ir.external_run_id AS run_id,
            ir.batch_name,
            ga.provider_id,
            ga.community_id,
            ga.building_id,
            c.name AS community_name,
            b.building_no AS building_name,
            c.district_id,
            d.district_name,
            ST_AsGeoJSON(COALESCE(ga.geom_wgs84, b.geom_wgs84)) AS geometry_json,
            ga.source_ref,
            ga.captured_at
        FROM geo_assets ga
        JOIN ingestion_runs ir ON ir.run_id = ga.ingestion_run_id
        LEFT JOIN communities c ON c.community_id = ga.community_id
        LEFT JOIN buildings b ON b.building_id = ga.building_id
        LEFT JOIN districts d ON d.district_id = c.district_id
        WHERE ga.asset_type = 'building_footprint'
        {where_clause}
        ORDER BY ir.created_at DESC, ga.captured_at DESC NULLS LAST, ga.asset_id DESC
        """,
        tuple(params),
    )


def db_geo_task_rows(geo_run_id: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    where_clause = ""
    if geo_run_id:
        where_clause = "AND ir.external_run_id = %s"
        params.append(geo_run_id)
    return query_rows(
        f"""
        SELECT
            ir.external_run_id AS run_id,
            ir.batch_name,
            t.task_id,
            t.task_scope,
            t.status,
            t.priority,
            t.provider_id,
            t.district_id,
            COALESCE(d.district_name, t.payload_json ->> 'district_name') AS district_name,
            t.community_id,
            COALESCE(c.name, t.community_name) AS community_name,
            t.building_id,
            COALESCE(b.building_no, t.building_name) AS building_name,
            t.source_ref,
            t.resolution_notes,
            t.review_owner,
            t.reviewed_at,
            t.updated_at,
            t.payload_json
        FROM geo_asset_capture_tasks t
        JOIN ingestion_runs ir ON ir.run_id = t.ingestion_run_id
        LEFT JOIN districts d ON d.district_id = t.district_id
        LEFT JOIN communities c ON c.community_id = t.community_id
        LEFT JOIN buildings b ON b.building_id = t.building_id
        WHERE 1 = 1
        {where_clause}
        ORDER BY ir.created_at DESC, t.updated_at DESC, t.task_id
        """,
        tuple(params),
    )


def db_geo_work_order_rows(geo_run_id: str | None = None) -> list[dict[str, Any]]:
    params: list[Any] = []
    where_clause = ""
    if geo_run_id:
        where_clause = "AND ir.external_run_id = %s"
        params.append(geo_run_id)
    return query_rows(
        f"""
        SELECT
            ir.external_run_id AS run_id,
            ir.batch_name,
            wo.work_order_id,
            wo.status,
            wo.provider_id,
            wo.district_id,
            COALESCE(d.district_name, wo.payload_json ->> 'district_name') AS district_name,
            wo.community_id,
            COALESCE(c.name, wo.payload_json ->> 'community_name') AS community_name,
            wo.building_id,
            COALESCE(b.building_no, wo.payload_json ->> 'building_name') AS building_name,
            wo.title,
            wo.assignee,
            wo.task_ids_json,
            wo.task_count,
            wo.primary_task_id,
            wo.focus_floor_no,
            wo.focus_yield_pct,
            wo.watchlist_hits,
            wo.impact_score,
            wo.impact_band,
            wo.notes,
            wo.due_at,
            wo.created_by,
            wo.created_at,
            wo.updated_at,
            wo.payload_json
        FROM geo_capture_work_orders wo
        JOIN ingestion_runs ir ON ir.run_id = wo.ingestion_run_id
        LEFT JOIN districts d ON d.district_id = wo.district_id
        LEFT JOIN communities c ON c.community_id = wo.community_id
        LEFT JOIN buildings b ON b.building_id = wo.building_id
        WHERE 1 = 1
        {where_clause}
        ORDER BY ir.created_at DESC, wo.updated_at DESC, wo.work_order_id
        """,
        tuple(params),
    )


def available_geo_baseline_runs_for(run_id: str) -> list[dict[str, Any]]:
    from ..service import created_at_is_before
    from .runs import list_geo_asset_runs

    runs = list_geo_asset_runs()
    selected_run = next((item for item in runs if item.get("runId") == run_id), None)
    if not selected_run:
        return []
    provider_id = selected_run.get("providerId")
    asset_type = selected_run.get("assetType")
    return [
        item
        for item in runs
        if item.get("runId") != run_id
        and item.get("providerId") == provider_id
        and item.get("assetType") == asset_type
        and created_at_is_before(item.get("createdAt"), selected_run.get("createdAt"))
    ]


def derive_geo_asset_tasks(
    run_summary: dict[str, Any],
    features: list[dict[str, Any]],
    unresolved_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from ..service import flatten_communities

    resolved_building_ids = {
        (feature.get("properties") or {}).get("building_id")
        for feature in features
        if (feature.get("properties") or {}).get("building_id")
    }
    tasks: list[dict[str, Any]] = []
    created_at = run_summary.get("createdAt")

    for index, item in enumerate(unresolved_features, start=1):
        tasks.append(
            {
                "task_id": f"{run_summary['runId']}::unresolved::{index}",
                "task_scope": "unresolved_feature",
                "status": item.get("status", "needs_review"),
                "priority": item.get("priority", "high"),
                "provider_id": run_summary.get("providerId"),
                "district_id": item.get("district_id"),
                "district_name": item.get("district_name"),
                "community_id": item.get("community_id"),
                "community_name": item.get("community_name"),
                "building_id": item.get("building_id"),
                "building_name": item.get("building_name"),
                "source_ref": item.get("source_ref"),
                "resolution_notes": item.get("resolution_notes") or "未命中楼栋词典，建议人工复核。",
                "review_owner": item.get("review_owner"),
                "reviewed_at": item.get("reviewed_at"),
                "updated_at": item.get("updated_at") or created_at,
            }
        )

    for community in flatten_communities():
        for building in community.get("buildings", []):
            if building.get("id") in resolved_building_ids:
                continue
            tasks.append(
                {
                    "task_id": f"{run_summary['runId']}::missing::{building['id']}",
                    "task_scope": "missing_building",
                    "status": "needs_capture",
                    "priority": "medium",
                    "provider_id": run_summary.get("providerId"),
                    "district_id": community["districtId"],
                    "district_name": community["districtName"],
                    "community_id": community["id"],
                    "community_name": community["name"],
                    "building_id": building["id"],
                    "building_name": building["name"],
                    "source_ref": building["id"],
                    "resolution_notes": "当前批次未提供该楼栋 footprint，建议补采或人工勾绘。",
                    "review_owner": None,
                    "reviewed_at": None,
                    "updated_at": created_at,
                }
            )

    priority_rank = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(
        key=lambda item: (
            priority_rank.get(str(item.get("priority")), 9),
            str(item.get("district_name") or ""),
            str(item.get("community_name") or ""),
            str(item.get("building_name") or ""),
        )
    )
    return tasks


def summarize_geo_asset_tasks(task_rows: list[dict[str, Any]]) -> dict[str, Any]:
    open_statuses = {"needs_review", "needs_capture", "scheduled"}
    return {
        "taskCount": len(task_rows),
        "openTaskCount": sum(1 for item in task_rows if item.get("status") in open_statuses),
        "reviewTaskCount": sum(1 for item in task_rows if item.get("status") == "needs_review"),
        "captureTaskCount": sum(1 for item in task_rows if item.get("status") == "needs_capture"),
        "scheduledTaskCount": sum(1 for item in task_rows if item.get("status") == "scheduled"),
        "resolvedTaskCount": sum(1 for item in task_rows if item.get("status") in {"resolved", "captured"}),
    }


def enrich_geo_asset_task_for_ui(run_summary: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": item.get("task_id"),
        "taskScope": item.get("task_scope"),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "providerId": item.get("provider_id") or run_summary.get("providerId"),
        "districtId": item.get("district_id"),
        "districtName": item.get("district_name"),
        "communityId": item.get("community_id"),
        "communityName": item.get("community_name"),
        "buildingId": item.get("building_id"),
        "buildingName": item.get("building_name"),
        "sourceRef": item.get("source_ref"),
        "resolutionNotes": item.get("resolution_notes"),
        "reviewOwner": item.get("review_owner"),
        "reviewedAt": item.get("reviewed_at"),
        "updatedAt": item.get("updated_at") or run_summary.get("createdAt"),
        "runId": run_summary.get("runId"),
        "batchName": run_summary.get("batchName"),
    }


def enrich_geo_asset_review_event_for_ui(run_summary: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": item.get("eventId") or item.get("event_id"),
        "taskId": item.get("taskId") or item.get("task_id"),
        "taskScope": item.get("taskScope") or item.get("task_scope"),
        "communityId": item.get("communityId") or item.get("community_id"),
        "communityName": item.get("communityName") or item.get("community_name"),
        "buildingId": item.get("buildingId") or item.get("building_id"),
        "buildingName": item.get("buildingName") or item.get("building_name"),
        "sourceRef": item.get("sourceRef") or item.get("source_ref"),
        "previousStatus": item.get("previousStatus") or item.get("previous_status"),
        "newStatus": item.get("newStatus") or item.get("new_status"),
        "reviewOwner": item.get("reviewOwner") or item.get("review_owner") or "atlas-ui",
        "reviewedAt": item.get("reviewedAt") or item.get("reviewed_at"),
        "resolutionNotes": item.get("resolutionNotes") or item.get("resolution_notes"),
        "runId": run_summary.get("runId"),
        "batchName": run_summary.get("batchName"),
    }


def enrich_geo_work_order_event_for_ui(run_summary: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "eventId": item.get("eventId") or item.get("event_id"),
        "workOrderId": item.get("workOrderId") or item.get("work_order_id"),
        "previousStatus": item.get("previousStatus") or item.get("previous_status"),
        "newStatus": item.get("newStatus") or item.get("new_status"),
        "changedBy": item.get("changedBy") or item.get("changed_by") or "atlas-ui",
        "changedAt": item.get("changedAt") or item.get("changed_at"),
        "notes": item.get("notes"),
        "runId": run_summary.get("runId"),
        "batchName": run_summary.get("batchName"),
    }


def geo_manifest_path_for_run(run_id: str) -> Path | None:
    from ..service import geo_asset_manifest_paths, read_json_file

    for manifest_path in geo_asset_manifest_paths():
        manifest = read_json_file(manifest_path)
        if isinstance(manifest, dict) and manifest.get("run_id") == run_id:
            return manifest_path
    return None


def enrich_geo_work_order_for_ui(
    run_summary: dict[str, Any],
    item: dict[str, Any],
    *,
    task_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    status_value = item.get("status") or "assigned"
    task_ids = [
        str(task_id)
        for task_id in (item.get("task_ids") or item.get("taskIds") or [])
        if task_id
    ]
    linked_tasks = [deepcopy(task_index[task_id]) for task_id in task_ids if task_id in task_index]
    linked_tasks.sort(
        key=lambda entry: (
            -float(entry.get("impactScore") or 0),
            -int(entry.get("watchlistHits") or 0),
            str(entry.get("communityName") or ""),
            str(entry.get("buildingName") or ""),
        )
    )
    primary_task = linked_tasks[0] if linked_tasks else {}
    focus_floor_no = item.get("focus_floor_no")
    if focus_floor_no is None and linked_tasks:
        focus_floor_no = next(
            (
                task.get("focusFloorNo")
                for task in linked_tasks
                if task.get("focusFloorNo") is not None
            ),
            None,
        )
    focus_yield_pct = item.get("focus_yield_pct")
    if focus_yield_pct is None and linked_tasks:
        focus_yield_pct = next(
            (
                task.get("focusYieldPct")
                for task in linked_tasks
                if task.get("focusYieldPct") is not None
            ),
            None,
        )
    watchlist_hits = item.get("watchlist_hits")
    if watchlist_hits is None:
        watchlist_hits = max((int(task.get("watchlistHits") or 0) for task in linked_tasks), default=0)
    impact_score = item.get("impact_score")
    if impact_score is None:
        impact_score = max((float(task.get("impactScore") or 0) for task in linked_tasks), default=0.0)

    return {
        "workOrderId": item.get("work_order_id") or item.get("workOrderId"),
        "status": status_value,
        "statusLabel": geo_work_order_status_label(status_value),
        "assignee": item.get("assignee") or "gis-team",
        "title": item.get("title")
        or (
            f"{primary_task.get('communityName', '待识别小区')} · {primary_task.get('buildingName', '待识别楼栋')} 补采工单"
        ),
        "taskIds": task_ids,
        "taskCount": len(task_ids),
        "districtId": item.get("district_id") or primary_task.get("districtId"),
        "districtName": item.get("district_name") or primary_task.get("districtName"),
        "communityId": item.get("community_id") or primary_task.get("communityId"),
        "communityName": item.get("community_name") or primary_task.get("communityName"),
        "buildingId": item.get("building_id") or primary_task.get("buildingId"),
        "buildingName": item.get("building_name") or primary_task.get("buildingName"),
        "primaryTaskId": item.get("primary_task_id") or primary_task.get("taskId"),
        "focusFloorNo": focus_floor_no,
        "focusYieldPct": focus_yield_pct,
        "impactScore": round(float(impact_score or 0), 1),
        "impactBand": item.get("impact_band") or primary_task.get("impactBand"),
        "watchlistHits": watchlist_hits,
        "notes": item.get("notes"),
        "createdBy": item.get("created_by") or "atlas-ui",
        "createdAt": item.get("created_at") or run_summary.get("createdAt"),
        "updatedAt": item.get("updated_at") or item.get("created_at") or run_summary.get("createdAt"),
        "dueAt": item.get("due_at"),
        "linkedTasks": linked_tasks[:4],
        "runId": run_summary.get("runId"),
        "batchName": run_summary.get("batchName"),
    }


def summarize_geo_work_orders(
    work_orders: list[dict[str, Any]],
    *,
    coverage_tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    active_statuses = {"assigned", "in_progress", "delivered"}
    linked_task_ids = {
        str(task_id)
        for item in work_orders
        if item.get("status") in active_statuses
        for task_id in item.get("taskIds", [])
        if task_id
    }
    open_tasks = coverage_tasks or []
    open_unassigned_count = sum(
        1
        for item in open_tasks
        if item.get("status") in {"needs_review", "needs_capture", "scheduled"}
        and item.get("taskId") not in linked_task_ids
    )
    return {
        "workOrderCount": len(work_orders),
        "activeWorkOrderCount": sum(1 for item in work_orders if item.get("status") in active_statuses),
        "assignedWorkOrderCount": sum(1 for item in work_orders if item.get("status") == "assigned"),
        "inProgressWorkOrderCount": sum(1 for item in work_orders if item.get("status") == "in_progress"),
        "deliveredWorkOrderCount": sum(1 for item in work_orders if item.get("status") == "delivered"),
        "closedWorkOrderCount": sum(1 for item in work_orders if item.get("status") == "closed"),
        "linkedTaskCount": len(linked_task_ids),
        "unassignedOpenTaskCount": open_unassigned_count,
    }


def geo_work_order_status_sort_key(status: str | None) -> int:
    return {
        "assigned": 0,
        "in_progress": 1,
        "delivered": 2,
        "closed": 3,
    }.get(status or "", 9)


def geo_work_order_matches_filters(
    item: dict[str, Any],
    *,
    district: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
) -> bool:
    if district not in (None, "", "all") and item.get("districtId") != district:
        return False

    normalized_status = (status or "").strip()
    if normalized_status and normalized_status != "all":
        item_status = str(item.get("status") or "")
        if normalized_status == "open":
            if item_status == "closed":
                return False
        elif item_status != normalized_status:
            return False

    normalized_assignee = (assignee or "").strip().lower()
    if normalized_assignee and normalized_assignee != "all":
        if (item.get("assignee") or "").strip().lower() != normalized_assignee:
            return False
    return True


def geo_task_scope_label(task_scope: str | None) -> str:
    return {
        "missing_building": "楼栋缺口",
        "unresolved_feature": "未命中归一",
    }.get(task_scope or "", task_scope or "待处理")


def geo_task_status_label(status: str | None) -> str:
    return {
        "needs_review": "待复核",
        "needs_capture": "待补采",
        "scheduled": "已派工",
        "resolved": "已归一",
        "captured": "已补齐",
    }.get(status or "", status or "待处理")


def geo_work_order_status_label(status: str | None) -> str:
    return {
        "assigned": "已派单",
        "in_progress": "执行中",
        "delivered": "待验收",
        "closed": "已关闭",
    }.get(status or "", status or "待处理")


def geo_task_priority_band(score: float) -> str:
    if score >= 82:
        return "critical"
    if score >= 64:
        return "high"
    if score >= 42:
        return "medium"
    return "low"


def geo_task_priority_label(score: float) -> str:
    return {
        "critical": "立即补齐",
        "high": "本周优先",
        "medium": "排入本轮",
        "low": "常规处理",
    }[geo_task_priority_band(score)]


def geo_task_recommended_action(
    *,
    task_scope: str | None,
    status: str | None,
    watchlist_hits: int,
    impact_score: float,
) -> str:
    if status == "scheduled":
        return "跟进 GIS 派工结果，优先确认下一版 footprint 已包含该楼栋。"
    if status in {"resolved", "captured"}:
        return "这条任务已关闭，可转入质量抽查。"
    if task_scope == "unresolved_feature":
        if watchlist_hits > 0 or impact_score >= 70:
            return "先人工复核楼栋归一，再补挂 footprint，避免高收益楼层误定位。"
        return "先处理楼栋归一和 source_ref 映射，再决定是否需要补采几何。"
    if watchlist_hits > 0 or impact_score >= 70:
        return "优先补采 footprint，这栋楼已影响套利楼层定位和导出。"
    return "可与同小区缺口楼栋合并补采，降低 GIS 往返成本。"


def enrich_geo_asset_tasks_with_priority(
    task_rows: list[dict[str, Any]],
    *,
    coverage_gaps: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from ..service import clamp, floor_watchlist, get_building, get_community

    building_cache: dict[str, dict[str, Any] | None] = {}
    community_cache: dict[str, dict[str, Any] | None] = {}
    watchlist_items = floor_watchlist(limit=60)
    watchlist_index: dict[str, list[dict[str, Any]]] = {}
    for item in watchlist_items:
        watchlist_index.setdefault(item["buildingId"], []).append(item)
    gap_index = {item["communityId"]: item for item in coverage_gaps}
    enriched_rows: list[dict[str, Any]] = []

    for item in task_rows:
        building_id = item.get("buildingId")
        community_id = item.get("communityId")
        building = None
        community = None
        if building_id:
            if building_id not in building_cache:
                building_cache[building_id] = get_building(building_id)
            building = building_cache.get(building_id)
        if community_id:
            if community_id not in community_cache:
                community_cache[community_id] = get_community(community_id)
            community = community_cache.get(community_id)
        if not community and building:
            community_id = building.get("communityId")
            if community_id:
                if community_id not in community_cache:
                    community_cache[community_id] = get_community(community_id)
                community = community_cache.get(community_id)

        watchlist_hits = list(watchlist_index.get(building_id or "", []))
        top_watchlist = sorted(
            watchlist_hits,
            key=lambda entry: (
                entry.get("persistenceScore", 0),
                entry.get("latestYieldPct", 0),
                entry.get("observedRuns", 0),
            ),
            reverse=True,
        )
        best_watchlist = top_watchlist[0] if top_watchlist else None
        community_gap = gap_index.get(community_id or "")
        top_floor_score = 0
        if building and building.get("topFloors"):
            top_floor_score = max(item.get("opportunityScore", 0) for item in building["topFloors"])
        community_score = (community or {}).get("score", 0)
        coverage_gap_count = community_gap.get("missingBuildingCount", 0) if community_gap else 0
        status = item.get("status")
        status_penalty = {
            "scheduled": -9,
            "resolved": -18,
            "captured": -24,
        }.get(status, 0)
        scope_boost = 18 if item.get("taskScope") == "unresolved_feature" else 10
        impact_score = round(
            clamp(
                scope_boost
                + community_score * 0.18
                + top_floor_score * 0.26
                + len(watchlist_hits) * 11
                + (best_watchlist.get("latestYieldPct", 0) if best_watchlist else 0) * 8
                + (best_watchlist.get("persistenceScore", 0) if best_watchlist else 0) * 0.18
                + max(coverage_gap_count - 1, 0) * 2.5
                + (6 if item.get("priority") == "high" else 0)
                + status_penalty,
                0,
                99,
            )
        )
        priority_band = geo_task_priority_band(impact_score)
        enriched_rows.append(
            {
                **item,
                "taskScopeLabel": geo_task_scope_label(item.get("taskScope")),
                "impactScore": impact_score,
                "impactBand": priority_band,
                "impactLabel": geo_task_priority_label(impact_score),
                "watchlistHits": len(watchlist_hits),
                "watchlistFloors": [
                    {
                        "floorNo": entry.get("floorNo"),
                        "latestYieldPct": entry.get("latestYieldPct"),
                        "persistenceScore": entry.get("persistenceScore"),
                        "trendLabel": entry.get("trendLabel"),
                    }
                    for entry in top_watchlist[:3]
                ],
                "recommendedAction": geo_task_recommended_action(
                    task_scope=item.get("taskScope"),
                    status=status,
                    watchlist_hits=len(watchlist_hits),
                    impact_score=impact_score,
                ),
                "communityScore": community_score,
                "buildingOpportunityScore": top_floor_score,
                "coverageGapCount": coverage_gap_count,
            }
        )

    status_rank = {"needs_review": 0, "needs_capture": 1, "scheduled": 2, "resolved": 3, "captured": 4}
    enriched_rows.sort(
        key=lambda item: (
            status_rank.get(str(item.get("status")), 9),
            -float(item.get("impactScore") or 0),
            -int(item.get("watchlistHits") or 0),
            str(item.get("communityName") or ""),
            str(item.get("buildingName") or ""),
        )
    )
    task_summary = summarize_geo_asset_tasks(task_rows)
    open_rows = [item for item in enriched_rows if item.get("status") in {"needs_review", "needs_capture", "scheduled"}]
    task_summary.update(
        {
            "criticalOpenTaskCount": sum(1 for item in open_rows if item.get("impactBand") == "critical"),
            "highPriorityOpenTaskCount": sum(1 for item in open_rows if item.get("impactBand") in {"critical", "high"}),
            "watchlistLinkedTaskCount": sum(1 for item in open_rows if (item.get("watchlistHits") or 0) > 0),
            "avgImpactScore": round(
                sum(float(item.get("impactScore") or 0) for item in open_rows) / max(len(open_rows), 1),
                1,
            )
            if open_rows
            else 0.0,
        }
    )
    return enriched_rows, task_summary


def db_geo_asset_run_detail_full(run_id: str) -> dict[str, Any] | None:
    from ..service import db_summary_json, existing_output_manifest_path, read_json_file

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
    from ..service import read_json_file, resolve_artifact_path
    from .runs import geo_asset_run_summary_from_manifest

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
    from ..service import flatten_communities

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
    from ..service import ring_without_close

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
    from ..service import feature_ring, polygon_center_lon_lat, ring_without_close

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
    from ..service import clamp, floor_watchlist, get_building, get_community
    from .runs import database_mode_active, list_geo_asset_runs

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
    from ..service import write_json_file

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
        from ..persistence import persist_geo_asset_run_to_postgres, postgres_runtime_status

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
    from ..service import write_json_file

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
        from ..persistence import persist_geo_asset_run_to_postgres, postgres_runtime_status

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
    from ..service import write_json_file

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
        from ..persistence import persist_geo_asset_run_to_postgres, postgres_runtime_status

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
