from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.provider_adapters import adapter_contract, validate_provider_scope
from api.reference_catalog import BuildingReference, load_reference_catalog


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = value.strip().lower()
    normalized = normalized.replace("号楼", "栋").replace("幢", "栋").replace("座", "栋")
    normalized = re.sub(r"[\s,，.。/（）()·\-_:：]", "", normalized)
    return normalized


@dataclass(frozen=True)
class BuildingCatalogEntry(BuildingReference):
    pass


def build_catalog() -> tuple[dict[str, BuildingCatalogEntry], dict[tuple[str, str], BuildingCatalogEntry], dict[tuple[str, str], BuildingCatalogEntry]]:
    by_building_id: dict[str, BuildingCatalogEntry] = {}
    by_community_and_building: dict[tuple[str, str], BuildingCatalogEntry] = {}
    by_name_pair: dict[tuple[str, str], BuildingCatalogEntry] = {}
    catalog = load_reference_catalog()
    for building in catalog.get("building_refs", []):
        entry = BuildingCatalogEntry(
            district_id=building.district_id,
            district_name=building.district_name,
            district_short_name=building.district_short_name,
            community_id=building.community_id,
            community_name=building.community_name,
            building_id=building.building_id,
            building_name=building.building_name,
            total_floors=building.total_floors,
        )
        by_building_id[entry.building_id] = entry
        community_tokens = {normalize_text(entry.community_name), *(normalize_text(alias) for alias in building.community_aliases if alias)}
        building_tokens = {
            normalize_text(entry.building_name),
            *(normalize_text(alias) for alias in building.building_aliases if alias),
            *(normalize_text(alias) for alias in building.source_refs if alias),
        }
        for building_token in {token for token in building_tokens if token}:
            by_community_and_building[(entry.community_id, building_token)] = entry
            for community_token in {token for token in community_tokens if token}:
                by_name_pair[(community_token, building_token)] = entry
    return by_building_id, by_community_and_building, by_name_pair


def load_geojson(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("type") != "FeatureCollection":
        raise SystemExit(f"{path.name} 不是 FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list):
        raise SystemExit(f"{path.name} 缺少 features 数组")
    return features


def resolve_catalog_entry(
    feature: dict[str, Any],
    *,
    by_building_id: dict[str, BuildingCatalogEntry],
    by_community_and_building: dict[tuple[str, str], BuildingCatalogEntry],
    by_name_pair: dict[tuple[str, str], BuildingCatalogEntry],
) -> tuple[BuildingCatalogEntry | None, str]:
    properties = feature.get("properties", {})
    building_id = properties.get("building_id")
    if building_id and building_id in by_building_id:
        return by_building_id[building_id], "命中 building_id"

    community_id = properties.get("community_id")
    building_name = properties.get("building_name") or properties.get("building_no") or properties.get("name")
    if community_id and building_name:
        matched = by_community_and_building.get((community_id, normalize_text(str(building_name))))
        if matched:
            return matched, "命中 community_id + building_name"

    community_name = properties.get("community_name")
    if community_name and building_name:
        matched = by_name_pair.get((normalize_text(str(community_name)), normalize_text(str(building_name))))
        if matched:
            return matched, "命中 community_name + building_name"

    return None, "未命中楼栋词典"


def normalized_feature(
    feature: dict[str, Any],
    entry: BuildingCatalogEntry,
    *,
    provider_id: str,
    captured_at: str,
    resolution_notes: str,
) -> dict[str, Any]:
    properties = feature.get("properties", {})
    source_ref = (
        properties.get("source_ref")
        or properties.get("id")
        or properties.get("name")
        or entry.building_id
    )
    normalized_properties = {
        "provider_id": provider_id,
        "source_ref": str(source_ref),
        "captured_at": captured_at,
        "district_id": entry.district_id,
        "district_name": entry.district_name,
        "community_id": entry.community_id,
        "community_name": entry.community_name,
        "building_id": entry.building_id,
        "building_name": entry.building_name,
        "resolution_notes": resolution_notes,
    }
    return {
        "type": "Feature",
        "properties": normalized_properties,
        "geometry": feature.get("geometry"),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_coverage_tasks(
    *,
    run_id: str,
    provider_id: str,
    captured_at: str,
    resolved_features: list[dict[str, Any]],
    unresolved_features: list[dict[str, Any]],
    catalog: dict[str, BuildingCatalogEntry],
) -> list[dict[str, Any]]:
    resolved_building_ids = {
        (feature.get("properties") or {}).get("building_id")
        for feature in resolved_features
        if (feature.get("properties") or {}).get("building_id")
    }
    tasks: list[dict[str, Any]] = []

    for index, item in enumerate(unresolved_features, start=1):
        tasks.append(
            {
                "task_id": f"{run_id}::unresolved::{index}",
                "task_scope": "unresolved_feature",
                "status": "needs_review",
                "priority": "high",
                "provider_id": provider_id,
                "district_id": None,
                "district_name": None,
                "community_id": None,
                "community_name": item.get("community_name"),
                "building_id": None,
                "building_name": item.get("building_name"),
                "source_ref": item.get("source_ref"),
                "resolution_notes": item.get("resolution_notes") or "未命中楼栋词典，建议人工复核。",
                "review_owner": None,
                "reviewed_at": None,
                "updated_at": captured_at,
            }
        )

    for entry in catalog.values():
        if entry.building_id in resolved_building_ids:
            continue
        tasks.append(
            {
                "task_id": f"{run_id}::missing::{entry.building_id}",
                "task_scope": "missing_building",
                "status": "needs_capture",
                "priority": "medium",
                "provider_id": provider_id,
                "district_id": entry.district_id,
                "district_name": entry.district_name,
                "community_id": entry.community_id,
                "community_name": entry.community_name,
                "building_id": entry.building_id,
                "building_name": entry.building_name,
                "source_ref": entry.building_id,
                "resolution_notes": "当前批次未提供该楼栋 footprint，建议补采或人工勾绘。",
                "review_owner": None,
                "reviewed_at": None,
                "updated_at": captured_at,
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


def build_summary(
    *,
    feature_count: int,
    resolved_features: list[dict[str, Any]],
    unresolved_features: list[dict[str, Any]],
    coverage_tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    open_task_statuses = {"needs_review", "needs_capture", "scheduled"}
    return {
        "feature_count": feature_count,
        "resolved_building_count": len(resolved_features),
        "unresolved_feature_count": len(unresolved_features),
        "community_count": len({item["properties"]["community_id"] for item in resolved_features}),
        "coverage_pct": round(len(resolved_features) / max(feature_count, 1) * 100, 1),
        "coverage_task_count": len(coverage_tasks),
        "open_task_count": sum(1 for item in coverage_tasks if item.get("status") in open_task_statuses),
        "review_task_count": sum(1 for item in coverage_tasks if item.get("status") == "needs_review"),
        "capture_task_count": sum(1 for item in coverage_tasks if item.get("status") == "needs_capture"),
        "scheduled_task_count": sum(1 for item in coverage_tasks if item.get("status") == "scheduled"),
        "resolved_task_count": sum(1 for item in coverage_tasks if item.get("status") in {"resolved", "captured"}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import open-map or AOI GeoJSON building footprints into a geo-assets batch.")
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--geojson-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider = validate_provider_scope(args.provider_id, "geometry_batch")
    timestamp = datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    run_id = f"{args.batch_name}-{timestamp}"

    features = load_geojson(args.geojson_file)
    by_building_id, by_community_and_building, by_name_pair = build_catalog()
    if not by_building_id:
        raise SystemExit(
            "当前没有可用的楼栋 reference catalog。请先写入 PostgreSQL 主字典，"
            "或设置 ATLAS_REFERENCE_CATALOG_FILE，开发联调时也可以显式开启 ATLAS_ENABLE_DEMO_MOCK=true。"
        )
    resolved_features: list[dict[str, Any]] = []
    unresolved_features: list[dict[str, Any]] = []

    for feature in features:
        entry, resolution_notes = resolve_catalog_entry(
            feature,
            by_building_id=by_building_id,
            by_community_and_building=by_community_and_building,
            by_name_pair=by_name_pair,
        )
        if not entry:
            unresolved_features.append(
                {
                    "source_ref": (feature.get("properties") or {}).get("source_ref") or (feature.get("properties") or {}).get("name"),
                    "community_name": (feature.get("properties") or {}).get("community_name"),
                    "building_name": (feature.get("properties") or {}).get("building_name") or (feature.get("properties") or {}).get("name"),
                    "resolution_notes": resolution_notes,
                }
            )
            continue
        resolved_features.append(
            normalized_feature(
                feature,
                entry,
                provider_id=provider["id"],
                captured_at=created_at,
                resolution_notes=resolution_notes,
            )
        )

    coverage_tasks = build_coverage_tasks(
        run_id=run_id,
        provider_id=provider["id"],
        captured_at=created_at,
        resolved_features=resolved_features,
        unresolved_features=unresolved_features,
        catalog=by_building_id,
    )
    review_history: list[dict[str, Any]] = []
    summary = build_summary(
        feature_count=len(features),
        resolved_features=resolved_features,
        unresolved_features=unresolved_features,
        coverage_tasks=coverage_tasks,
    )
    attention = {
        "unresolved_examples": unresolved_features[:12],
    }

    output_dir = args.output_dir
    feature_path = output_dir / "building_footprints.geojson"
    unresolved_path = output_dir / "unresolved_features.json"
    coverage_tasks_path = output_dir / "coverage_tasks.json"
    review_history_path = output_dir / "review_history.json"
    work_orders_path = output_dir / "work_orders.json"
    work_order_events_path = output_dir / "work_order_events.json"
    summary_path = output_dir / "summary.json"
    manifest_path = output_dir / "manifest.json"

    write_json(
        feature_path,
        {
            "type": "FeatureCollection",
            "name": f"{args.batch_name}-building-footprints",
            "features": resolved_features,
        },
    )
    write_json(unresolved_path, unresolved_features)
    write_json(coverage_tasks_path, coverage_tasks)
    write_json(review_history_path, review_history)
    write_json(work_orders_path, [])
    write_json(work_order_events_path, [])
    write_json(summary_path, summary)
    write_json(
        manifest_path,
        {
            "run_id": run_id,
            "provider_id": provider["id"],
            "adapter_scope": "geometry_batch",
            "adapter_contract": adapter_contract("geometry_batch"),
            "batch_name": args.batch_name,
            "asset_type": "building_footprint",
            "created_at": created_at,
            "input": {
                "geojson_file": str(args.geojson_file.resolve()),
            },
            "summary": summary,
            "attention": attention,
            "outputs": {
                "building_footprints": str(feature_path.resolve()),
                "unresolved_features": str(unresolved_path.resolve()),
                "coverage_tasks": str(coverage_tasks_path.resolve()),
                "review_history": str(review_history_path.resolve()),
                "work_orders": str(work_orders_path.resolve()),
                "work_order_events": str(work_order_events_path.resolve()),
                "summary": str(summary_path.resolve()),
            },
        },
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "batch_name": args.batch_name,
                "resolved_building_count": len(resolved_features),
                "unresolved_feature_count": len(unresolved_features),
                "open_task_count": summary["open_task_count"],
                "output_dir": str(output_dir.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
