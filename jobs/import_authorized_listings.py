from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.provider_adapters import adapter_contract, normalize_provider_id, validate_provider_scope
from api.reference_catalog import BuildingReference, load_reference_catalog


CHINESE_DIGIT_MAP = {
    "零": "0",
    "一": "1",
    "二": "2",
    "两": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
}


SALE_FIELD_CASTERS = {
    "total_floors": int,
    "area_sqm": float,
    "bedrooms": int,
    "living_rooms": int,
    "bathrooms": int,
    "price_total_wan": float,
    "unit_price_yuan": float,
}

RENT_FIELD_CASTERS = {
    "total_floors": int,
    "area_sqm": float,
    "bedrooms": int,
    "living_rooms": int,
    "bathrooms": int,
    "monthly_rent": float,
}

REQUIRED_SHARED_FIELDS = {
    "source",
    "source_listing_id",
    "url",
    "community_name",
    "address_text",
    "building_text",
    "unit_text",
    "floor_text",
    "total_floors",
    "area_sqm",
    "bedrooms",
    "living_rooms",
    "bathrooms",
    "orientation",
    "decoration",
    "published_at",
}

REQUIRED_SALE_FIELDS = REQUIRED_SHARED_FIELDS | {"price_total_wan", "unit_price_yuan"}
REQUIRED_RENT_FIELDS = REQUIRED_SHARED_FIELDS | {"monthly_rent"}
FLOOR_FRACTION_PATTERN = re.compile(r"((?:高楼层|中楼层|低楼层|高层|中层|低层|\d{1,2}(?:\s*层)?))\s*/\s*(\d{1,2})(?:\s*层)?")
TOTAL_FLOOR_TEXT_PATTERN = re.compile(r"(?:总高|总层高|总楼层|共)\s*(\d{1,2})\s*层")


@dataclass(frozen=True)
class CatalogBuildingReference:
    district_id: str
    district_name: str
    community_id: str
    community_name: str
    building_id: str
    building_name: str
    total_floors: int | None
    community_aliases: tuple[str, ...]
    building_aliases: tuple[str, ...]
    source_refs: tuple[str, ...]
    community_tokens: tuple[str, ...]
    building_tokens: tuple[str, ...]
    source_ref_tokens: tuple[str, ...]


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    normalized = value.strip().lower()
    normalized = normalized.replace("　", " ")
    normalized = normalized.replace("－", "-")
    normalized = normalized.replace("号楼", "栋")
    normalized = normalized.replace("号", "")
    normalized = normalized.replace("幢", "栋")
    normalized = normalized.replace("座", "栋")
    normalized = normalized.replace("f", "层")
    normalized = re.sub(r"[\s,，.。/（）()·\-_:：]", "", normalized)
    for chinese_digit, arabic in CHINESE_DIGIT_MAP.items():
        normalized = normalized.replace(chinese_digit, arabic)
    return normalized


def safe_cast(value: str | None, caster: type) -> Any:
    if value in (None, ""):
        return None
    cleaned = value.replace(",", "").strip() if isinstance(value, str) else value
    return caster(cleaned)


def load_csv_rows(path: Path, casters: dict[str, type], required_fields: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_fields = sorted(required_fields - set(reader.fieldnames or []))
        if missing_fields:
            missing_display = ", ".join(missing_fields)
            raise SystemExit(f"{path.name} 缺少必要字段: {missing_display}")

        for row_no, row in enumerate(reader, start=2):
            parsed = {key: value.strip() if isinstance(value, str) else value for key, value in row.items()}
            for key, caster in casters.items():
                try:
                    parsed[key] = safe_cast(parsed.get(key), caster)
                except ValueError as exc:
                    raise SystemExit(f"{path.name} 第 {row_no} 行字段 {key} 无法转换: {exc}") from exc
            rows.append(parsed)
    return rows


def build_catalog() -> tuple[list[CatalogBuildingReference], dict[str, str]]:
    catalog = load_reference_catalog()
    building_refs: list[CatalogBuildingReference] = []
    community_name_map: dict[str, str] = {}
    for building in catalog.get("building_refs", []):
        community_token_set = {normalize_text(building.community_name)}
        community_token_set.update(normalize_text(alias) for alias in building.community_aliases if alias)
        building_token_set = {normalize_text(building.building_name)}
        building_token_set.update(normalize_text(alias) for alias in building.building_aliases if alias)
        source_ref_tokens = tuple(normalize_text(source_ref) for source_ref in building.source_refs if source_ref)
        community_name_map[building.community_id] = building.community_name
        building_refs.append(
            CatalogBuildingReference(
                district_id=building.district_id,
                district_name=building.district_name,
                community_id=building.community_id,
                community_name=building.community_name,
                building_id=building.building_id,
                building_name=building.building_name,
                total_floors=building.total_floors,
                community_aliases=building.community_aliases,
                building_aliases=building.building_aliases,
                source_refs=building.source_refs,
                community_tokens=tuple(token for token in community_token_set if token),
                building_tokens=tuple(token for token in building_token_set if token),
                source_ref_tokens=tuple(token for token in source_ref_tokens if token),
            )
        )
    return building_refs, community_name_map


def parse_floor_info(floor_text: str | None, total_floors: int | None) -> tuple[int | None, int | None, str, float]:
    text = floor_text or ""
    total = total_floors
    floor_no = None
    confidence = 0.55

    fraction_match = FLOOR_FRACTION_PATTERN.search(text)
    if fraction_match:
        floor_token = fraction_match.group(1).replace(" ", "")
        total = int(fraction_match.group(2))
        if re.fullmatch(r"\d{1,2}(?:层)?", floor_token):
            floor_no = int(re.search(r"\d{1,2}", floor_token).group(0))
            confidence = 0.96
        elif floor_token in {"高楼层", "高层"}:
            floor_no = max(1, round(total * 0.82))
            confidence = 0.74
        elif floor_token in {"中楼层", "中层"}:
            floor_no = max(1, round(total * 0.55))
            confidence = 0.74
        elif floor_token in {"低楼层", "低层"}:
            floor_no = max(1, round(total * 0.22))
            confidence = 0.74
    else:
        if not total:
            total_match = TOTAL_FLOOR_TEXT_PATTERN.search(text)
            if total_match:
                total = int(total_match.group(1))
        layer_match = re.search(r"(\d{1,2})\s*层", text)
        if layer_match:
            floor_no = int(layer_match.group(1))
            confidence = 0.9
        elif "高楼层" in text and total:
            floor_no = max(1, round(total * 0.82))
            confidence = 0.68
        elif "中楼层" in text and total:
            floor_no = max(1, round(total * 0.55))
            confidence = 0.68
        elif "低楼层" in text and total:
            floor_no = max(1, round(total * 0.22))
            confidence = 0.68
        else:
            digit_match = re.search(r"(\d{1,2})", text)
            if digit_match:
                floor_no = int(digit_match.group(1))
                confidence = 0.72

    if total and floor_no and floor_no > total:
        floor_no = total
        confidence = min(confidence, 0.6)

    bucket = "unknown"
    if total and floor_no:
        if floor_no <= max(1, round(total * 0.33)):
            bucket = "low"
        elif floor_no >= max(2, round(total * 0.67)):
            bucket = "high"
        else:
            bucket = "mid"

    return floor_no, total, bucket, confidence


def match_building_reference(
    raw_community_name: str,
    address_text: str,
    raw_building_text: str,
    total_floors: int | None,
    building_refs: list[CatalogBuildingReference],
) -> tuple[CatalogBuildingReference | None, float, str]:
    community_token = normalize_text(raw_community_name)
    address_token = normalize_text(address_text)
    building_token = normalize_text(raw_building_text)
    best_ref = None
    best_score = -1.0
    best_notes: list[str] = []

    for ref in building_refs:
        score = 0.0
        notes: list[str] = []

        if any(token and token in community_token for token in ref.community_tokens):
            score += 0.54
            notes.append("命中小区名")
        elif any(token and token in address_token for token in ref.community_tokens):
            score += 0.42
            notes.append("命中地址内小区别名")
        else:
            continue

        building_exact = building_token and building_token in ref.building_tokens
        building_via_source_ref = building_token and building_token in ref.source_ref_tokens

        if building_exact:
            score += 0.3
            notes.append("楼栋文本精确命中")
        elif building_via_source_ref:
            score += 0.28
            notes.append("命中楼栋 source_ref")
        elif building_token and building_token in address_token and building_token in ref.building_tokens:
            score += 0.26
            notes.append("楼栋文本来自地址")
        elif any(token and token in address_token for token in ref.building_tokens):
            score += 0.18
            notes.append("地址包含楼栋号")

        if total_floors and ref.total_floors and abs(total_floors - ref.total_floors) <= 2:
            score += 0.08
            notes.append("总层数接近")

        if score > best_score:
            best_ref = ref
            best_score = score
            best_notes = notes

    if not best_ref:
        return None, 0.0, "未命中小区/楼栋词典"

    return best_ref, min(best_score, 0.99), "；".join(best_notes) or "规则命中"


def normalize_listing_rows(
    rows: list[dict[str, Any]],
    *,
    business_type: str,
    building_refs: list[CatalogBuildingReference],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_rows: list[dict[str, Any]] = []
    queue_rows: list[dict[str, Any]] = []

    for row in rows:
        floor_no, total_floors, floor_bucket, floor_conf = parse_floor_info(row.get("floor_text"), row.get("total_floors"))
        ref, address_conf, match_notes = match_building_reference(
            row.get("community_name", ""),
            row.get("address_text", ""),
            row.get("building_text", ""),
            total_floors,
            building_refs,
        )

        resolution_confidence = round(min(0.99, 0.55 * address_conf + 0.45 * floor_conf), 2)
        parse_status = "resolved" if ref and resolution_confidence >= 0.82 else "needs_review" if ref else "matching"
        normalized_address = (
            f"{ref.district_name} / {ref.community_name} / {ref.building_name} / "
            f"{row.get('unit_text') or '待识别单元'} / {floor_no or '待识别'}层"
            if ref
            else None
        )
        resolution_notes = match_notes
        if floor_no is None:
            resolution_notes = f"{resolution_notes}；楼层解析不完整"

        base_payload = {
            "business_type": business_type,
            "source": row.get("source"),
            "source_listing_id": row.get("source_listing_id"),
            "url": row.get("url"),
            "community_id": ref.community_id if ref else None,
            "building_id": ref.building_id if ref else None,
            "district_id": ref.district_id if ref else None,
            "resolved_district_name": ref.district_name if ref else None,
            "resolved_community_name": ref.community_name if ref else None,
            "resolved_building_name": ref.building_name if ref else None,
            "raw_community_name": row.get("community_name"),
            "raw_address": row.get("address_text"),
            "raw_building_text": row.get("building_text"),
            "parsed_unit": row.get("unit_text") or None,
            "floor_no": floor_no,
            "total_floors": total_floors,
            "floor_bucket": floor_bucket,
            "area_sqm": row.get("area_sqm"),
            "bedrooms": row.get("bedrooms"),
            "living_rooms": row.get("living_rooms"),
            "bathrooms": row.get("bathrooms"),
            "orientation": row.get("orientation"),
            "decoration": row.get("decoration"),
            "published_at": row.get("published_at"),
            "normalized_address": normalized_address,
            "resolution_confidence": resolution_confidence,
            "parse_status": parse_status,
            "resolution_notes": resolution_notes,
            "raw_row": row,
        }

        if business_type == "sale":
            base_payload["price_total_wan"] = row.get("price_total_wan")
            base_payload["unit_price_yuan"] = row.get("unit_price_yuan")
        else:
            base_payload["monthly_rent"] = row.get("monthly_rent")

        normalized_rows.append(base_payload)
        queue_rows.append(
            {
                "source": row.get("source"),
                "source_listing_id": row.get("source_listing_id"),
                "raw_text": row.get("address_text") or row.get("community_name"),
                "parsed_district_id": ref.district_id if ref else None,
                "parsed_community_id": ref.community_id if ref else None,
                "parsed_building_id": ref.building_id if ref else None,
                "parsed_unit": row.get("unit_text") or None,
                "parsed_floor_no": floor_no,
                "parse_status": parse_status,
                "confidence_score": resolution_confidence,
                "resolution_notes": resolution_notes,
            }
        )

    return normalized_rows, queue_rows


def listing_match_score(sale: dict[str, Any], rent: dict[str, Any]) -> float:
    if sale["community_id"] != rent["community_id"] or sale["building_id"] != rent["building_id"]:
        return 0.0

    area_gap = abs((sale.get("area_sqm") or 0) - (rent.get("area_sqm") or 0))
    floor_gap = abs((sale.get("floor_no") or 0) - (rent.get("floor_no") or 0))
    bedroom_gap = abs((sale.get("bedrooms") or 0) - (rent.get("bedrooms") or 0))

    if area_gap > 24:
        return 0.0
    if sale.get("floor_no") and rent.get("floor_no") and floor_gap > 4:
        return 0.0
    if bedroom_gap > 1:
        return 0.0

    area_score = max(0.0, 1 - area_gap / 24)
    floor_score = max(0.0, 1 - floor_gap / 4) if sale.get("floor_no") and rent.get("floor_no") else 0.55
    bedroom_score = 1.0 if bedroom_gap == 0 else 0.7
    orientation_score = 1.0 if sale.get("orientation") == rent.get("orientation") else 0.78
    confidence_score = min(sale.get("resolution_confidence", 0.0), rent.get("resolution_confidence", 0.0))

    return round(
        area_score * 0.28
        + floor_score * 0.28
        + bedroom_score * 0.14
        + orientation_score * 0.1
        + confidence_score * 0.2,
        4,
    )


def build_floor_pairs(
    sale_rows: list[dict[str, Any]],
    rent_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved_sales = [item for item in sale_rows if item["community_id"] and item["building_id"]]
    resolved_rents = [item for item in rent_rows if item["community_id"] and item["building_id"]]
    rent_pool: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for rent in resolved_rents:
        rent_pool[(rent["community_id"], rent["building_id"])].append(rent)

    pair_rows: list[dict[str, Any]] = []
    used_rent_ids: set[tuple[str, str]] = set()

    for sale in resolved_sales:
        candidates = []
        for rent in rent_pool[(sale["community_id"], sale["building_id"])]:
            rent_key = (rent["source"], rent["source_listing_id"])
            if rent_key in used_rent_ids:
                continue
            match_confidence = listing_match_score(sale, rent)
            if match_confidence < 0.58:
                continue
            candidates.append((match_confidence, rent))

        if not candidates:
            continue

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_confidence, best_rent = candidates[0]
        used_rent_ids.add((best_rent["source"], best_rent["source_listing_id"]))
        annual_yield_pct = round(best_rent["monthly_rent"] * 12 / max((sale["price_total_wan"] or 0) * 10000, 1) * 100, 2)
        floor_no = sale.get("floor_no") or best_rent.get("floor_no")

        pair_rows.append(
            {
                "pair_id": f"{sale['source']}-{sale['source_listing_id']}__{best_rent['source']}-{best_rent['source_listing_id']}",
                "community_id": sale["community_id"],
                "building_id": sale["building_id"],
                "floor_no": floor_no,
                "sale_source": sale["source"],
                "sale_source_listing_id": sale["source_listing_id"],
                "rent_source": best_rent["source"],
                "rent_source_listing_id": best_rent["source_listing_id"],
                "sale_price_wan": sale["price_total_wan"],
                "monthly_rent": best_rent["monthly_rent"],
                "annual_yield_pct": annual_yield_pct,
                "area_gap_sqm": round(abs((sale.get("area_sqm") or 0) - (best_rent.get("area_sqm") or 0)), 2),
                "floor_gap": abs((sale.get("floor_no") or 0) - (best_rent.get("floor_no") or 0)),
                "match_confidence": best_confidence,
                "normalized_address": sale.get("normalized_address") or best_rent.get("normalized_address"),
            }
        )

    return pair_rows


def build_floor_evidence(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_rows:
        if pair["floor_no"] is None:
            continue
        grouped[(pair["community_id"], pair["building_id"], pair["floor_no"])].append(pair)

    evidence_rows = []
    for (community_id, building_id, floor_no), pairs in grouped.items():
        sale_prices = [item["sale_price_wan"] for item in pairs if item["sale_price_wan"]]
        rents = [item["monthly_rent"] for item in pairs if item["monthly_rent"]]
        evidence_rows.append(
            {
                "community_id": community_id,
                "building_id": building_id,
                "floor_no": floor_no,
                "pair_count": len(pairs),
                "sale_median_wan": round(sorted(sale_prices)[len(sale_prices) // 2], 2) if sale_prices else None,
                "rent_median_monthly": round(sorted(rents)[len(rents) // 2], 2) if rents else None,
                "yield_pct": round(sum(item["annual_yield_pct"] for item in pairs) / len(pairs), 2),
                "best_pair_confidence": max(item["match_confidence"] for item in pairs),
                "pairs": pairs,
            }
        )

    evidence_rows.sort(key=lambda item: (item["yield_pct"], item["best_pair_confidence"]), reverse=True)
    return evidence_rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_summary(
    sale_rows: list[dict[str, Any]],
    rent_rows: list[dict[str, Any]],
    queue_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    resolved_rows = [item for item in queue_rows if item["parse_status"] == "resolved"]
    resolved_communities = {item["parsed_community_id"] for item in queue_rows if item["parsed_community_id"]}
    resolved_buildings = {item["parsed_building_id"] for item in queue_rows if item["parsed_building_id"]}
    return {
        "sale_input_count": len(sale_rows),
        "rent_input_count": len(rent_rows),
        "resolved_count": len(resolved_rows),
        "review_count": sum(1 for item in queue_rows if item["parse_status"] == "needs_review"),
        "matching_count": sum(1 for item in queue_rows if item["parse_status"] == "matching"),
        "resolved_rate": round(len(resolved_rows) / max(len(queue_rows), 1), 4),
        "resolved_community_count": len(resolved_communities),
        "resolved_building_count": len(resolved_buildings),
        "floor_pair_count": len(pair_rows),
        "floor_evidence_count": len(evidence_rows),
    }


def collect_attention_items(queue_rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = [
        {
            "source": item["source"],
            "source_listing_id": item["source_listing_id"],
            "parse_status": item["parse_status"],
            "raw_text": item["raw_text"],
            "resolution_notes": item["resolution_notes"],
        }
        for item in queue_rows
        if item["parse_status"] != "resolved"
    ][:8]

    low_confidence_pairs = [
        {
            "pair_id": item["pair_id"],
            "match_confidence": item["match_confidence"],
            "normalized_address": item["normalized_address"],
        }
        for item in pair_rows
        if item["match_confidence"] < 0.72
    ][:8]

    return {
        "unresolved_examples": unresolved,
        "low_confidence_pairs": low_confidence_pairs,
    }


def build_manifest(
    *,
    provider_id: str,
    batch_name: str | None,
    sale_file: Path | None,
    rent_file: Path | None,
    output_dir: Path,
    summary: dict[str, Any],
    queue_rows: list[dict[str, Any]],
    pair_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    run_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", (batch_name or "authorized-import").strip()).strip("-").lower()
    return {
        "run_id": f"{run_slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "provider_id": provider_id,
        "adapter_scope": "sale_rent_batch",
        "adapter_contract": adapter_contract("sale_rent_batch"),
        "batch_name": batch_name or "authorized-import",
        "created_at": timestamp,
        "inputs": {
            "sale_file": str(sale_file) if sale_file else None,
            "rent_file": str(rent_file) if rent_file else None,
        },
        "outputs": {
            "normalized_sale": str(output_dir / "normalized_sale.json"),
            "normalized_rent": str(output_dir / "normalized_rent.json"),
            "address_resolution_queue": str(output_dir / "address_resolution_queue.json"),
            "floor_pairs": str(output_dir / "floor_pairs.json"),
            "floor_evidence": str(output_dir / "floor_evidence.json"),
            "review_history": str(output_dir / "review_history.json"),
            "summary": str(output_dir / "summary.json"),
            "manifest": str(output_dir / "manifest.json"),
        },
        "summary": summary,
        "attention": collect_attention_items(queue_rows, pair_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import authorized sale/rent listing CSV files into normalized MVP payloads.")
    parser.add_argument("--sale-file", type=Path, help="CSV file for sale listings.")
    parser.add_argument("--rent-file", type=Path, help="CSV file for rent listings.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory where normalized outputs will be written.")
    parser.add_argument("--provider-id", default="authorized-import", help="Data source provider id for the import run.")
    parser.add_argument("--batch-name", help="Optional human-readable batch name.")
    args = parser.parse_args()

    if not args.sale_file and not args.rent_file:
        raise SystemExit("At least one of --sale-file or --rent-file is required.")

    provider = validate_provider_scope(args.provider_id, "sale_rent_batch")
    building_refs, _ = build_catalog()
    if not building_refs:
        raise SystemExit(
            "当前没有可用的小区 / 楼栋 reference catalog。请先写入 PostgreSQL 主字典，"
            "或设置 ATLAS_REFERENCE_CATALOG_FILE，开发联调时也可以显式开启 ATLAS_ENABLE_DEMO_MOCK=true。"
        )
    sale_input_rows = (
        load_csv_rows(args.sale_file, SALE_FIELD_CASTERS, REQUIRED_SALE_FIELDS)
        if args.sale_file
        else []
    )
    rent_input_rows = (
        load_csv_rows(args.rent_file, RENT_FIELD_CASTERS, REQUIRED_RENT_FIELDS)
        if args.rent_file
        else []
    )

    normalized_sale_rows, sale_queue_rows = normalize_listing_rows(sale_input_rows, business_type="sale", building_refs=building_refs)
    normalized_rent_rows, rent_queue_rows = normalize_listing_rows(rent_input_rows, business_type="rent", building_refs=building_refs)
    queue_rows = sale_queue_rows + rent_queue_rows
    floor_pairs = build_floor_pairs(normalized_sale_rows, normalized_rent_rows)
    floor_evidence = build_floor_evidence(floor_pairs)
    summary = build_summary(normalized_sale_rows, normalized_rent_rows, queue_rows, floor_pairs, floor_evidence)
    manifest = build_manifest(
        provider_id=provider["id"],
        batch_name=args.batch_name,
        sale_file=args.sale_file,
        rent_file=args.rent_file,
        output_dir=args.output_dir,
        summary=summary,
        queue_rows=queue_rows,
        pair_rows=floor_pairs,
    )

    write_json(args.output_dir / "normalized_sale.json", normalized_sale_rows)
    write_json(args.output_dir / "normalized_rent.json", normalized_rent_rows)
    write_json(args.output_dir / "address_resolution_queue.json", queue_rows)
    write_json(args.output_dir / "floor_pairs.json", floor_pairs)
    write_json(args.output_dir / "floor_evidence.json", floor_evidence)
    write_json(args.output_dir / "review_history.json", [])
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "manifest.json", manifest)

    print(json.dumps({"output_dir": str(args.output_dir), **summary, "run_id": manifest["run_id"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
