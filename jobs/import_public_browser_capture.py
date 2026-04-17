from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.provider_adapters import normalize_provider_id, validate_provider_scope


CAPTURE_REQUIRED_FIELDS = {
    "source_listing_id",
    "business_type",
    "url",
    "community_name",
    "address_text",
    "raw_text",
    "published_at",
}

SALE_OUTPUT_FIELDS = [
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
    "price_total_wan",
    "unit_price_yuan",
    "published_at",
]

RENT_OUTPUT_FIELDS = [
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
    "monthly_rent",
    "published_at",
]

ORIENTATION_OPTIONS = [
    "南北通透",
    "东南",
    "西南",
    "东北",
    "西北",
    "南北",
    "朝南",
    "朝北",
    "朝东",
    "朝西",
    "南",
    "北",
    "东",
    "西",
]

DECORATION_OPTIONS = ["豪装", "精装", "简装", "毛坯"]

BUILDING_PATTERNS = [
    re.compile(r"([A-Za-zＡ-Ｚａ-ｚ]座)"),
    re.compile(r"(\d{1,3}(?:号楼|栋|幢|座))"),
]

UNIT_PATTERNS = [
    re.compile(r"([A-Za-zＡ-Ｚａ-ｚ0-9]+单元)"),
]

FLOOR_FRACTION_PATTERN = re.compile(r"((?:高楼层|中楼层|低楼层|高层|中层|低层|\d{1,2}(?:\s*层)?))\s*/\s*(\d{1,2})(?:\s*层)?")
FLOOR_LAYER_PATTERN = re.compile(r"(\d{1,2}层)")
TOTAL_FLOOR_PATTERN = re.compile(r"(?:总高|总层高|总楼层|共)\s*(\d{1,2})\s*层")
ROOM_PATTERN = re.compile(r"(\d)\s*室\s*(\d)\s*厅\s*(\d)\s*卫")
AREA_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:㎡|平米|平方米|平)")
SALE_PRICE_PATTERN = re.compile(r"(?:总价|售价|挂牌价)?\s*(\d+(?:\.\d+)?)\s*万")
UNIT_PRICE_PATTERN = re.compile(r"(?:单价|均价)?\s*(\d+(?:\.\d+)?)\s*元(?:/平|/㎡)")
RENT_PRICE_PATTERN = re.compile(r"(?:月租|租金)?\s*(\d+(?:\.\d+)?)\s*(万)?\s*元?(?:/月)?")


def load_capture_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_fields = sorted(CAPTURE_REQUIRED_FIELDS - set(reader.fieldnames or []))
        if missing_fields:
            raise SystemExit(f"{path.name} 缺少必要字段: {', '.join(missing_fields)}")
        return [{key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()} for row in reader]


def normalize_business_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"sale", "sell", "出售", "sale_listing"}:
        return "sale"
    if normalized in {"rent", "rental", "出租", "rent_listing"}:
        return "rent"
    raise SystemExit(f"无法识别 business_type: {value}")


def parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def parse_int(value: str | None) -> int | None:
    parsed = parse_float(value)
    return int(parsed) if parsed is not None else None


def first_match(texts: list[str], patterns: list[re.Pattern[str]]) -> str | None:
    for text in texts:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
    return None


def detect_orientation(texts: list[str]) -> str:
    for text in texts:
        for option in ORIENTATION_OPTIONS:
            if option in text:
                return option.replace("朝", "")
    return ""


def detect_decoration(texts: list[str]) -> str:
    for text in texts:
        for option in DECORATION_OPTIONS:
            if option in text:
                return option
    return ""


def parse_floor_fraction(text: str) -> tuple[str, int] | None:
    match = FLOOR_FRACTION_PATTERN.search(text)
    if not match:
        return None
    floor_token = match.group(1).replace(" ", "")
    total_floors = int(match.group(2))
    if re.fullmatch(r"\d{1,2}(?:层)?", floor_token):
        floor_no = int(re.search(r"\d{1,2}", floor_token).group(0))
        return f"{floor_no}层", total_floors
    return floor_token, total_floors


def parse_floor_text(explicit_floor_text: str, texts: list[str], explicit_total: int | None) -> tuple[str, int | None]:
    if explicit_floor_text:
        text = explicit_floor_text
        total = explicit_total
        fraction = parse_floor_fraction(explicit_floor_text)
        if fraction:
            floor_text, detected_total = fraction
            return floor_text, total or detected_total
        return text, total

    for text in texts:
        fraction = parse_floor_fraction(text)
        if fraction:
            return fraction

    for text in texts:
        layer_match = FLOOR_LAYER_PATTERN.search(text)
        if layer_match:
            total = explicit_total
            total_match = TOTAL_FLOOR_PATTERN.search(text)
            if total_match:
                total = int(total_match.group(1))
            return layer_match.group(1), total

    for label in ("高楼层", "中楼层", "低楼层"):
        for text in texts:
            if label in text:
                total = explicit_total
                total_match = TOTAL_FLOOR_PATTERN.search(text)
                if total_match:
                    total = int(total_match.group(1))
                return label, total

    return "", explicit_total


def parse_room_tuple(texts: list[str], explicit_row: dict[str, str]) -> tuple[int | None, int | None, int | None]:
    bedrooms = parse_int(explicit_row.get("bedrooms"))
    living_rooms = parse_int(explicit_row.get("living_rooms"))
    bathrooms = parse_int(explicit_row.get("bathrooms"))
    if bedrooms is not None and living_rooms is not None and bathrooms is not None:
        return bedrooms, living_rooms, bathrooms
    for text in texts:
        match = ROOM_PATTERN.search(text)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return bedrooms, living_rooms, bathrooms


def parse_area(texts: list[str], explicit_value: str | None) -> float | None:
    explicit = parse_float(explicit_value)
    if explicit is not None:
        return explicit
    for text in texts:
        match = AREA_PATTERN.search(text)
        if match:
            return float(match.group(1))
    return None


def parse_sale_price(texts: list[str], explicit_value: str | None) -> float | None:
    explicit = parse_float(explicit_value)
    if explicit is not None:
        return explicit
    for text in texts:
        match = SALE_PRICE_PATTERN.search(text)
        if match:
            return float(match.group(1))
    return None


def parse_unit_price(texts: list[str], explicit_value: str | None, sale_price_wan: float | None, area_sqm: float | None) -> float | None:
    explicit = parse_float(explicit_value)
    if explicit is not None:
        return explicit
    for text in texts:
        match = UNIT_PRICE_PATTERN.search(text)
        if match:
            return float(match.group(1))
    if sale_price_wan is not None and area_sqm:
        return round(sale_price_wan * 10000 / area_sqm, 2)
    return None


def parse_monthly_rent(texts: list[str], explicit_value: str | None) -> float | None:
    explicit = parse_float(explicit_value)
    if explicit is not None:
        return explicit
    for text in texts:
        match = RENT_PRICE_PATTERN.search(text)
        if match:
            amount = float(match.group(1))
            return round(amount * 10000, 2) if match.group(2) else round(amount, 2)
    return None


def build_structured_row(row: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    business_type = normalize_business_type(row.get("business_type"))
    source = row.get("source") or "public-browser-sampling"
    raw_text = row.get("raw_text") or ""
    texts = [value for value in [row.get("address_text") or "", raw_text, row.get("capture_notes") or ""] if value]

    building_text = row.get("building_text") or first_match(texts, BUILDING_PATTERNS) or ""
    unit_text = row.get("unit_text") or first_match(texts, UNIT_PATTERNS) or ""
    explicit_total = parse_int(row.get("total_floors"))
    floor_text, total_floors = parse_floor_text(row.get("floor_text") or "", texts, explicit_total)
    area_sqm = parse_area(texts, row.get("area_sqm"))
    bedrooms, living_rooms, bathrooms = parse_room_tuple(texts, row)
    orientation = row.get("orientation") or detect_orientation(texts)
    decoration = row.get("decoration") or detect_decoration(texts)

    structured = {
        "source": source,
        "source_listing_id": row.get("source_listing_id") or "",
        "url": row.get("url") or "",
        "community_name": row.get("community_name") or "",
        "address_text": row.get("address_text") or "",
        "building_text": building_text,
        "unit_text": unit_text,
        "floor_text": floor_text,
        "total_floors": total_floors if total_floors is not None else "",
        "area_sqm": area_sqm if area_sqm is not None else "",
        "bedrooms": bedrooms if bedrooms is not None else "",
        "living_rooms": living_rooms if living_rooms is not None else "",
        "bathrooms": bathrooms if bathrooms is not None else "",
        "orientation": orientation,
        "decoration": decoration,
        "published_at": row.get("published_at") or "",
    }

    attention: list[str] = []
    if not building_text:
        attention.append("缺少楼栋文本")
    if not floor_text:
        attention.append("缺少楼层文本")
    if not total_floors:
        attention.append("缺少总层数")

    if business_type == "sale":
        sale_price_wan = parse_sale_price(texts, row.get("price_total_wan"))
        unit_price_yuan = parse_unit_price(texts, row.get("unit_price_yuan"), sale_price_wan, area_sqm)
        structured["price_total_wan"] = sale_price_wan if sale_price_wan is not None else ""
        structured["unit_price_yuan"] = unit_price_yuan if unit_price_yuan is not None else ""
        if sale_price_wan is None:
            attention.append("缺少挂牌总价")
    else:
        monthly_rent = parse_monthly_rent(texts, row.get("monthly_rent"))
        structured["monthly_rent"] = monthly_rent if monthly_rent is not None else ""
        if monthly_rent is None:
            attention.append("缺少月租")

    parse_record = {
        "source_listing_id": structured["source_listing_id"],
        "business_type": business_type,
        "community_name": structured["community_name"],
        "building_text": building_text,
        "unit_text": unit_text,
        "floor_text": floor_text,
        "total_floors": structured["total_floors"],
        "area_sqm": structured["area_sqm"],
        "orientation": orientation,
        "decoration": decoration,
        "attention": attention,
        "raw_text": raw_text,
    }
    return structured, parse_record


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert manually captured public browser notes into sale/rent staging CSVs, then optionally run the standard import pipeline.")
    parser.add_argument("--provider-id", default="public-browser-sampling")
    parser.add_argument("--batch-name", required=True)
    parser.add_argument("--capture-file", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--import-output-dir", type=Path, default=None)
    parser.add_argument("--skip-import", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    provider_id = normalize_provider_id(args.provider_id)
    validate_provider_scope(provider_id, "sale_rent_batch")

    capture_file = args.capture_file if args.capture_file.is_absolute() else ROOT_DIR / args.capture_file
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT_DIR / args.output_dir
    import_output_dir = args.import_output_dir
    if import_output_dir is None:
        import_output_dir = ROOT_DIR / "tmp" / "import-runs" / args.batch_name
    elif not import_output_dir.is_absolute():
        import_output_dir = ROOT_DIR / import_output_dir

    rows = load_capture_rows(capture_file)
    sale_rows: list[dict[str, Any]] = []
    rent_rows: list[dict[str, Any]] = []
    parsed_rows: list[dict[str, Any]] = []

    for row in rows:
        structured, parse_record = build_structured_row(row)
        parsed_rows.append(parse_record)
        business_type = normalize_business_type(row.get("business_type"))
        if business_type == "sale":
            sale_rows.append(structured)
        else:
            rent_rows.append(structured)

    output_dir.mkdir(parents=True, exist_ok=True)
    sale_path = output_dir / "captured_sale.csv"
    rent_path = output_dir / "captured_rent.csv"
    parsed_path = output_dir / "parsed_captures.json"
    manifest_path = output_dir / "manifest.json"

    write_csv(sale_path, SALE_OUTPUT_FIELDS, sale_rows)
    write_csv(rent_path, RENT_OUTPUT_FIELDS, rent_rows)
    parsed_path.write_text(json.dumps(parsed_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    import_result: dict[str, Any] | None = None
    if not args.skip_import:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT_DIR / "jobs" / "import_authorized_listings.py"),
                "--provider-id",
                provider_id,
                "--batch-name",
                args.batch_name,
                "--sale-file",
                str(sale_path),
                "--rent-file",
                str(rent_path),
                "--output-dir",
                str(import_output_dir),
            ],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        import_result = json.loads(completed.stdout.strip() or "{}")

    attention_items = [item for item in parsed_rows if item.get("attention")]
    manifest = {
        "batch_name": args.batch_name,
        "provider_id": provider_id,
        "capture_file": str(capture_file),
        "outputs": {
            "sale_csv": str(sale_path),
            "rent_csv": str(rent_path),
            "parsed_captures": str(parsed_path),
        },
        "summary": {
            "capture_count": len(rows),
            "sale_capture_count": len(sale_rows),
            "rent_capture_count": len(rent_rows),
            "attention_count": len(attention_items),
            "ready_sale_count": sum(1 for row in sale_rows if row.get("price_total_wan")),
            "ready_rent_count": sum(1 for row in rent_rows if row.get("monthly_rent")),
        },
        "attention": attention_items[:10],
        "import_result": import_result,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
