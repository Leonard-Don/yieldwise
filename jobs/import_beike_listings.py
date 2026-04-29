#!/usr/bin/env python3
"""Pull sale + rent listings from 贝壳开放平台 and stage them as an import run.

This is a SKELETON. The token-acquisition signature and the listing-endpoint
shapes are gated behind a login on https://open.ke.com — once you have those
docs, fill in the four TODO sections marked below. Everything else (output
shape, run-slug, error handling, --dry-run, --district filter) is wired up.

Handoff: see docs/beike-adapter-handoff.md for step-by-step.

Run:
    # one-time test, no real API calls (for shape verification only):
    python3 jobs/import_beike_listings.py --dry-run --district baoshan

    # real fetch, target the three rent-deficient districts (Option C):
    python3 jobs/import_beike_listings.py --district baoshan --district jingan --district jinshan
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.env import load_local_env  # noqa: E402
from api.provider_adapters import adapter_contract  # noqa: E402

load_local_env()


# ── Project-known district id → 上海行政区 mapping (mirrors generate_amap_seed_data) ──
DISTRICTS = {
    "huangpu": "黄浦区", "jingan": "静安区", "xuhui": "徐汇区", "changning": "长宁区",
    "putuo": "普陀区", "hongkou": "虹口区", "yangpu": "杨浦区", "minhang": "闵行区",
    "baoshan": "宝山区", "jiading": "嘉定区", "pudong": "浦东新区", "jinshan": "金山区",
    "songjiang": "松江区", "qingpu": "青浦区", "fengxian": "奉贤区", "chongming": "崇明区",
}

# When the user asks for Option C (rent backfill for sparse districts) by default.
RENT_DEFICIT_DISTRICTS = ["baoshan", "jingan", "jinshan"]


# ───────────────────────────────────────────────────────────────────────
# TODO #1 — TOKEN endpoint + signature
# ───────────────────────────────────────────────────────────────────────
# Reference: https://open.ke.com/serviceSupport/getToken/ (login required)
#
# Most Chinese open-platforms use one of these patterns. After you read the
# real spec, replace this function. Until then it raises so callers can't
# silently misbehave.
def acquire_token(app_id: str, app_ak: str) -> str:
    """Return a bearer/access token for subsequent API calls.

    Common pattern (verify against actual docs):
      POST https://api.ke.com/oauth/token
      Body (form): app_id=...&app_ak=...&timestamp=...&signature=<sign(app_id+app_ak+timestamp, secret)>
      Response: {"code": 0, "data": {"access_token": "...", "expires_in": 7200}}
    """
    raise NotImplementedError(
        "Beike token endpoint not wired yet. See docs/beike-adapter-handoff.md "
        "for the four-step handoff. Until then, --dry-run works for shape verification."
    )


# ───────────────────────────────────────────────────────────────────────
# TODO #2 — LISTING SEARCH endpoint shape
# ───────────────────────────────────────────────────────────────────────
# Replace with whatever Beike's listing-search endpoint expects. The function
# should return raw JSON (parsed). Pagination is handled by the caller via
# `page` parameter.
def fetch_listings_page(
    *,
    token: str,
    business_type: str,            # "sale" | "rent"
    district_id: str,              # internal id (e.g. "baoshan")
    page: int,
    page_size: int,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """One page of search results from Beike. Returns the parsed JSON body."""
    # PLACEHOLDER values — confirm against the real API:
    base = os.getenv("BEIKE_LISTING_ENDPOINT", "https://api.ke.com/v1/listing/search")
    district_name = DISTRICTS.get(district_id, district_id)
    params = {
        "city_id": "310000",            # 上海 administrative code
        "district": district_name,
        "biz_type": business_type,      # often called "transType" / "biz" in Chinese APIs
        "page": page,
        "page_size": page_size,
    }
    url = f"{base}?{urlencode(params)}"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ───────────────────────────────────────────────────────────────────────
# TODO #3 — LISTING ROW NORMALIZATION
# ───────────────────────────────────────────────────────────────────────
# Once you see one real listing, map its fields to the project's schema.
# Schema reference: tmp/import-runs/<any>/normalized_sale.json (sale rows) and
# normalized_rent.json (rent rows). The two share most fields and differ only
# at the price (sale: price_total_wan + unit_price_yuan; rent: monthly_rent).
def normalize_listing(raw: dict[str, Any], business_type: str, district_id: str) -> dict[str, Any] | None:
    """Map one raw Beike row → project's normalized listing shape. Return None to skip."""
    # PLACEHOLDER mapping — adapt to the real Beike field names:
    community_id = raw.get("resblock_id") or raw.get("community_id")
    if not community_id:
        return None
    listing_id = raw.get("house_code") or raw.get("listing_id") or raw.get("id")
    if not listing_id:
        return None

    base = {
        "business_type": business_type,
        "source": "beike-open-platform",
        "source_listing_id": str(listing_id),
        "url": raw.get("source_url") or raw.get("url") or f"beike://{listing_id}",
        "community_id": str(community_id),
        "building_id": str(raw.get("building_id") or f"{community_id}-unknown"),
        "district_id": district_id,
        "resolved_district_name": DISTRICTS.get(district_id, district_id),
        "resolved_community_name": raw.get("resblock_name") or raw.get("community_name") or "",
        "resolved_building_name": raw.get("building_name") or "",
        "raw_community_name": raw.get("resblock_name") or raw.get("community_name") or "",
        "raw_address": raw.get("address") or "",
        "raw_building_text": raw.get("building_name") or "",
        "parsed_unit": raw.get("unit_name") or "",
        "floor_no": int(raw.get("floor") or 0) or None,
        "total_floors": int(raw.get("total_floors") or 0) or None,
        "floor_bucket": _floor_bucket(raw.get("floor"), raw.get("total_floors")),
        "area_sqm": float(raw.get("area_sqm") or raw.get("area") or 0) or None,
        "bedrooms": int(raw.get("bedrooms") or 0) or None,
        "living_rooms": int(raw.get("living_rooms") or 0) or None,
        "bathrooms": int(raw.get("bathrooms") or 0) or None,
        "orientation": raw.get("orientation") or "",
        "decoration": raw.get("decoration") or "",
        "published_at": raw.get("published_at") or raw.get("publish_time") or "",
        "normalized_address": "",
        "resolution_confidence": 0.95,
        "parse_status": "resolved",
        "resolution_notes": "beike-open-platform: fetched via API",
        "raw_row": raw,
    }
    if business_type == "sale":
        base["price_total_wan"] = float(raw.get("total_price_wan") or raw.get("total_price") or 0) or None
        base["unit_price_yuan"] = float(raw.get("unit_price") or raw.get("unit_price_yuan") or 0) or None
    else:
        base["monthly_rent"] = float(raw.get("rent_price") or raw.get("monthly_rent") or 0) or None
    return base


# ───────────────────────────────────────────────────────────────────────
# TODO #4 — RESPONSE PARSING (locate the rows + total-count fields)
# ───────────────────────────────────────────────────────────────────────
# Most Chinese open APIs wrap their payload as `{"code": 0, "data": {"list": [...], "total": N}}`.
def extract_rows(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Return (rows, total_records) from a single search-page response."""
    if not isinstance(payload, dict):
        return [], 0
    code = payload.get("code") or payload.get("status")
    if code not in (0, "0", "ok", "success"):
        raise RuntimeError(f"beike API non-success: code={code} msg={payload.get('msg') or payload.get('message')}")
    data = payload.get("data") or {}
    rows = data.get("list") or data.get("items") or data.get("listings") or []
    total = int(data.get("total") or data.get("count") or len(rows))
    return rows, total


# ── Helpers (pure / safe to keep) ──
def _floor_bucket(floor, total) -> str:
    try:
        f, t = int(floor or 0), int(total or 0)
    except (TypeError, ValueError):
        return ""
    if f <= 0 or t <= 0:
        return ""
    pct = f / t
    if pct < 0.34:
        return "low"
    if pct < 0.67:
        return "mid"
    return "high"


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_manifest(*, run_slug: str, output_dir: Path, district_ids: list[str], summary: dict[str, Any]) -> dict[str, Any]:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "run_id": f"{run_slug}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "provider_id": "beike-open-platform",
        "adapter_scope": "sale_rent_batch",
        "adapter_contract": adapter_contract("sale_rent_batch"),
        "batch_name": run_slug,
        "created_at": timestamp,
        "inputs": {"districts": district_ids, "endpoint": "beike-open-platform://api"},
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
    }


def fetch_for_district(
    *,
    token: str,
    business_type: str,
    district_id: str,
    max_pages: int,
    page_size: int,
    pause_ms: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        payload = fetch_listings_page(
            token=token,
            business_type=business_type,
            district_id=district_id,
            page=page,
            page_size=page_size,
        )
        page_rows, total = extract_rows(payload)
        if not page_rows:
            break
        for raw in page_rows:
            normalized = normalize_listing(raw, business_type, district_id)
            if normalized:
                rows.append(normalized)
        if len(rows) >= total:
            break
        time.sleep(pause_ms / 1000)
    return rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--district",
        action="append",
        choices=sorted(DISTRICTS.keys()),
        help="Limit fetch to one or more districts. Repeat for multiple. "
             f"Default: rent-deficit fix ({', '.join(RENT_DEFICIT_DISTRICTS)})",
    )
    p.add_argument("--max-pages", type=int, default=10, help="Pagination cap per (district × business-type)")
    p.add_argument("--page-size", type=int, default=20, help="Records per page")
    p.add_argument("--pause-ms", type=int, default=200, help="Sleep between paged calls")
    p.add_argument("--batch-name", default="beike-import", help="Run-id slug prefix")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "import-runs", help="Where to stage the run")
    p.add_argument("--dry-run", action="store_true", help="Skip all API calls; emit empty run with manifest only")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    districts = args.district or list(RENT_DEFICIT_DISTRICTS)
    run_slug_safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", args.batch_name).strip("-").lower() or "beike-import"
    output_dir = args.output_root / f"{run_slug_safe}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    sale_rows: list[dict[str, Any]] = []
    rent_rows: list[dict[str, Any]] = []

    if args.dry_run:
        print(f"[dry-run] would fetch districts={districts} max_pages={args.max_pages}")
    else:
        app_id = (os.getenv("BEIKE_APP_ID") or "").strip()
        app_ak = (os.getenv("BEIKE_APP_AK") or "").strip()
        if not app_id or not app_ak:
            raise SystemExit("BEIKE_APP_ID + BEIKE_APP_AK must both be set in env / .env.local")
        token = acquire_token(app_id, app_ak)
        for did in districts:
            print(f"[{did}] fetching sale ...", flush=True)
            sale_rows.extend(fetch_for_district(
                token=token, business_type="sale", district_id=did,
                max_pages=args.max_pages, page_size=args.page_size, pause_ms=args.pause_ms,
            ))
            print(f"[{did}] fetching rent ...", flush=True)
            rent_rows.extend(fetch_for_district(
                token=token, business_type="rent", district_id=did,
                max_pages=args.max_pages, page_size=args.page_size, pause_ms=args.pause_ms,
            ))

    _write_json(output_dir / "normalized_sale.json", sale_rows)
    _write_json(output_dir / "normalized_rent.json", rent_rows)
    _write_json(output_dir / "address_resolution_queue.json", [])
    _write_json(output_dir / "floor_pairs.json", [])
    _write_json(output_dir / "floor_evidence.json", [])
    _write_json(output_dir / "review_history.json", [])

    summary = {
        "sale_input_count": len(sale_rows),
        "rent_input_count": len(rent_rows),
        "resolved_count": len(sale_rows) + len(rent_rows),
        "review_count": 0,
        "matching_count": 0,
        "resolved_rate": 1.0 if (sale_rows or rent_rows) else 0.0,
        "resolved_community_count": len({r["community_id"] for r in sale_rows + rent_rows}),
        "resolved_building_count": len({r["building_id"] for r in sale_rows + rent_rows}),
        "districts": districts,
        "dry_run": args.dry_run,
    }
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "manifest.json", _build_manifest(
        run_slug=run_slug_safe, output_dir=output_dir, district_ids=districts, summary=summary,
    ))

    print(f"\nstaged → {output_dir}")
    print(f"  sale rows: {len(sale_rows)}")
    print(f"  rent rows: {len(rent_rows)}")
    if args.dry_run:
        print("\n[dry-run] no API calls were made. Wire up acquire_token / fetch_listings_page / normalize_listing,")
        print("then re-run without --dry-run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
