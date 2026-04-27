"""
Geo asset / coverage task / work-order helpers for the backstage tool.

Phase 7e1 extraction from api/service.py — covers the lighter geo helpers:
manifest path defaults, db_*_rows queries, baseline-run lookup, task
derivation/summary/enrichment, work-order summary/sort/filter helpers,
label/status/priority helpers, and the impact-score enrichment pipeline.
Heavier detail/comparison/watchlist + work-order CRUD clusters move in
subsequent sub-phases. Re-exported from api.service for back-compat.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from ..persistence import query_rows


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
    from ..service import created_at_is_before, list_geo_asset_runs

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
