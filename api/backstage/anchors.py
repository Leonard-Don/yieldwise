"""
Reference catalog anchor confirmation + audit history helpers.

Phase 7f extraction from api/service.py — covers anchor manifest path
defaults, anchor lookups (latest review / report), decision-state
classification, anchor presence checks, anchor report rebuild,
target_reference_run_id resolver, the confirm_community_anchor write
pipeline, the database-side latest-review lookup, and the GIS
anchor_watchlist_payload aggregation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from ..persistence import query_rows


def default_anchor_review_history_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "anchor_review_history.json"


def default_reference_anchor_report_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "anchor_report.json"


def latest_reference_anchor_review_lookup() -> dict[str, dict[str, Any]]:
    from ..service import list_reference_runs, reference_run_detail_full

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


def latest_reference_anchor_report_lookup() -> dict[str, dict[str, Any]]:
    from ..service import list_reference_runs, reference_run_detail_full

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
    from ..service import latest_datetime_iso

    timestamps = [item.get("reviewedAt") for item in review_history if isinstance(item, dict)]
    return latest_datetime_iso(timestamps)


def target_reference_run_id(reference_run_id: str | None = None) -> str | None:
    from ..service import list_reference_runs

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
    from ..service import (
        get_community,
        normalize_alias_list,
        rebuild_reference_summary,
        reference_run_detail_full,
        serialize_alias_list,
        to_float_or_none,
        write_csv_rows,
        write_json_file,
    )

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
        from ..persistence import postgres_runtime_status, sync_anchor_confirmation_to_postgres

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


def db_latest_anchor_review_lookup() -> dict[str, dict[str, Any]]:
    from ..service import database_mode_active

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


def anchor_watchlist_payload(
    *,
    district: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    from ..service import (
        current_community_dataset,
        list_reference_runs,
        priority_districts,
        reference_catalog_indices,
        sample_status_label,
    )

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
