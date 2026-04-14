from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.provider_adapters import adapter_contract, validate_provider_scope


DISTRICT_REQUIRED_FIELDS = {"district_id", "district_name", "short_name"}
COMMUNITY_REQUIRED_FIELDS = {"district_id", "community_id", "community_name", "aliases", "source_confidence"}
BUILDING_REQUIRED_FIELDS = {"community_id", "building_id", "building_name", "total_floors", "unit_count", "aliases", "source_ref"}


def load_csv_rows(path: Path, required_fields: set[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(required_fields - set(reader.fieldnames or []))
        if missing:
            raise SystemExit(f"{path.name} 缺少必要字段: {', '.join(missing)}")
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({key: (value.strip() if isinstance(value, str) else "") for key, value in row.items()})
        return rows


def split_aliases(value: str | None) -> list[str]:
    if not value:
        return []
    aliases = [item.strip() for item in re.split(r"[|,，;；]", value) if item.strip()]
    deduped: list[str] = []
    for alias in aliases:
        if alias not in deduped:
            deduped.append(alias)
    return deduped


def parse_optional_int(value: str | None) -> int | None:
    if not value:
        return None
    return int(value)


def parse_optional_float(value: str | None) -> float | None:
    if not value:
        return None
    return float(value)


def validate_unique_ids(rows: list[dict[str, Any]], key: str, label: str) -> None:
    duplicates = [item for item, count in Counter(str(row.get(key) or "") for row in rows).items() if item and count > 1]
    if duplicates:
        raise SystemExit(f"{label} 存在重复 {key}: {', '.join(sorted(duplicates)[:5])}")


def normalize_district_rows(rows: list[dict[str, str]], provider_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "district_id": row["district_id"],
                "district_name": row["district_name"],
                "short_name": row["short_name"],
                "alias_source": provider_id,
            }
        )
    validate_unique_ids(normalized, "district_id", "行政区字典")
    return normalized


def normalize_community_rows(rows: list[dict[str, str]], district_ids: set[str], provider_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if row["district_id"] not in district_ids:
            raise SystemExit(f"小区 {row['community_id']} 引用了不存在的 district_id: {row['district_id']}")
        aliases = split_aliases(row.get("aliases"))
        if row["community_name"] not in aliases:
            aliases.insert(0, row["community_name"])
        normalized.append(
            {
                "district_id": row["district_id"],
                "community_id": row["community_id"],
                "community_name": row["community_name"],
                "aliases": aliases,
                "source_confidence": parse_optional_float(row.get("source_confidence")) or 0.9,
                "center_lng": parse_optional_float(row.get("center_lng")),
                "center_lat": parse_optional_float(row.get("center_lat")),
                "anchor_source": row.get("anchor_source") or None,
                "anchor_quality": parse_optional_float(row.get("anchor_quality")),
                "source_refs": split_aliases(row.get("source_refs")),
                "alias_source": provider_id,
                "alias_confidence": 0.92,
            }
        )
    validate_unique_ids(normalized, "community_id", "小区字典")
    return normalized


def normalize_building_rows(rows: list[dict[str, str]], community_ids: set[str], provider_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if row["community_id"] not in community_ids:
            raise SystemExit(f"楼栋 {row['building_id']} 引用了不存在的 community_id: {row['community_id']}")
        aliases = split_aliases(row.get("aliases"))
        if row["building_name"] not in aliases:
            aliases.insert(0, row["building_name"])
        normalized.append(
            {
                "community_id": row["community_id"],
                "building_id": row["building_id"],
                "building_name": row["building_name"],
                "total_floors": parse_optional_int(row.get("total_floors")),
                "unit_count": parse_optional_int(row.get("unit_count")),
                "aliases": aliases,
                "source_ref": row.get("source_ref") or None,
                "center_lng": parse_optional_float(row.get("center_lng")),
                "center_lat": parse_optional_float(row.get("center_lat")),
                "anchor_source": row.get("anchor_source") or None,
                "anchor_quality": parse_optional_float(row.get("anchor_quality")),
                "alias_source": provider_id,
                "alias_confidence": 0.92,
            }
        )
    validate_unique_ids(normalized, "building_id", "楼栋字典")
    return normalized


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import district / community / building dictionary files into a normalized reference batch.")
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--district-file", required=True, type=Path)
    parser.add_argument("--community-file", required=True, type=Path)
    parser.add_argument("--building-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider = validate_provider_scope(args.provider_id, "dictionary_batch")
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    timestamp = datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
    run_id = f"{args.batch_name}-{timestamp}"

    district_rows = normalize_district_rows(load_csv_rows(args.district_file, DISTRICT_REQUIRED_FIELDS), provider["id"])
    community_rows = normalize_community_rows(
        load_csv_rows(args.community_file, COMMUNITY_REQUIRED_FIELDS),
        {row["district_id"] for row in district_rows},
        provider["id"],
    )
    building_rows = normalize_building_rows(
        load_csv_rows(args.building_file, BUILDING_REQUIRED_FIELDS),
        {row["community_id"] for row in community_rows},
        provider["id"],
    )

    output_dir = args.output_dir
    district_path = output_dir / "district_dictionary.json"
    community_path = output_dir / "community_dictionary.json"
    building_path = output_dir / "building_dictionary.json"
    reference_catalog_path = output_dir / "reference_catalog.json"
    summary_path = output_dir / "summary.json"
    manifest_path = output_dir / "manifest.json"

    summary = {
        "district_count": len(district_rows),
        "community_count": len(community_rows),
        "building_count": len(building_rows),
        "community_alias_count": sum(len(item["aliases"]) for item in community_rows),
        "building_alias_count": sum(len(item["aliases"]) for item in building_rows),
        "source_ref_count": sum(1 for item in building_rows if item.get("source_ref")),
        "anchored_community_count": sum(1 for item in community_rows if item.get("center_lng") is not None and item.get("center_lat") is not None),
        "anchored_building_count": sum(1 for item in building_rows if item.get("center_lng") is not None and item.get("center_lat") is not None),
    }
    attention: list[str] = []
    if not building_rows:
        attention.append("当前字典批次没有楼栋记录，后续 listing / geometry 归一会失去楼栋锚点。")
    if summary["building_alias_count"] <= len(building_rows):
        attention.append("楼栋别名数量偏少，建议补充 source_ref / 外部楼栋写法，提升地址归一命中率。")

    write_json(district_path, district_rows)
    write_json(community_path, community_rows)
    write_json(building_path, building_rows)
    write_json(
        reference_catalog_path,
        {
            "districts": district_rows,
            "communities": community_rows,
            "buildings": building_rows,
        },
    )
    write_json(summary_path, summary)

    manifest = {
        "run_id": run_id,
        "provider_id": provider["id"],
        "batch_name": args.batch_name,
        "created_at": created_at,
        "adapter_scope": "dictionary_batch",
        "adapter_contract": adapter_contract("dictionary_batch"),
        "inputs": {
            "district_file": str(args.district_file),
            "community_file": str(args.community_file),
            "building_file": str(args.building_file),
        },
        "outputs": {
            "district_dictionary": str(district_path),
            "community_dictionary": str(community_path),
            "building_dictionary": str(building_path),
            "reference_catalog": str(reference_catalog_path),
            "summary": str(summary_path),
        },
        "summary": summary,
        "attention": attention,
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"run_id": run_id, "summary": summary, "manifest": str(manifest_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
