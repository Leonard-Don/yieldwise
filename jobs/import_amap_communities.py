#!/usr/bin/env python3
"""Discover real Shanghai residential communities via AMAP Place Search and
materialize them as a pure reference run (no listings).

Difference from the earlier (deleted) generate_amap_seed_data.py:
- That one produced both reference + synthetic listings (12k fake rows that
  contaminated yields).
- This one produces ONLY the reference catalog (community names + GCJ-02
  coords + district mapping). No fake listings. Useful as match targets
  for OSM footprint association and as a richer community catalog.

Output (gitignored, reversible):
    tmp/reference-runs/amap-communities-<DATE>-<TS>/
        community_dictionary.json
        district_dictionary.json
        building_dictionary.json    (empty — AMAP gives community-level only)
        reference_catalog.json
        manifest.json + summary.json + anchor_report/history (empty)

Revert:
    rm -rf tmp/reference-runs/amap-communities-*

Run:
    python3 jobs/import_amap_communities.py                    # 4 pages × 25/page = ~100 per district
    python3 jobs/import_amap_communities.py --pages 8          # ~200 per district
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.env import load_local_env  # noqa: E402

load_local_env()

TZ = timezone(timedelta(hours=8))
NOW = datetime.now(TZ).replace(microsecond=0)
TS_FILE = NOW.strftime("%Y%m%d%H%M%S")
TS_ISO = NOW.isoformat()
RUN_NAME = f"amap-communities-{NOW.strftime('%Y-%m-%d')}-{TS_FILE}"
REF_DIR = ROOT / "tmp" / "reference-runs" / RUN_NAME

PLACE_ENDPOINT = "https://restapi.amap.com/v3/place/text"
RESIDENTIAL_TYPES = "120300|120301|120302"

DISTRICTS: dict[str, dict[str, str]] = {
    "huangpu":   {"name": "黄浦区",   "short": "黄浦"},
    "jingan":    {"name": "静安区",   "short": "静安"},
    "xuhui":     {"name": "徐汇区",   "short": "徐汇"},
    "changning": {"name": "长宁区",   "short": "长宁"},
    "putuo":     {"name": "普陀区",   "short": "普陀"},
    "hongkou":   {"name": "虹口区",   "short": "虹口"},
    "yangpu":    {"name": "杨浦区",   "short": "杨浦"},
    "minhang":   {"name": "闵行区",   "short": "闵行"},
    "baoshan":   {"name": "宝山区",   "short": "宝山"},
    "jiading":   {"name": "嘉定区",   "short": "嘉定"},
    "pudong":    {"name": "浦东新区", "short": "浦东"},
    "jinshan":   {"name": "金山区",   "short": "金山"},
    "songjiang": {"name": "松江区",   "short": "松江"},
    "qingpu":    {"name": "青浦区",   "short": "青浦"},
    "fengxian":  {"name": "奉贤区",   "short": "奉贤"},
    "chongming": {"name": "崇明区",   "short": "崇明"},
}

REJECT_TOKENS = ("停车场", "出入口", "售楼处", "地块", "用地", "工地", "样板", "管理处", "物业", "服务中心")


def fetch_district_pois(key: str, district_name: str, *, pages: int, offset: int, pause_ms: int) -> list[dict]:
    rows: list[dict] = []
    for page in range(1, pages + 1):
        q = urlencode({
            "key": key, "keywords": "住宅小区", "city": district_name, "citylimit": "true",
            "types": RESIDENTIAL_TYPES, "offset": offset, "page": page,
        })
        url = f"{PLACE_ENDPOINT}?{q}"
        try:
            with urlopen(url, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"  [{district_name} p{page}] error: {exc}", file=sys.stderr)
            break
        if str(data.get("status")) != "1":
            print(f"  [{district_name} p{page}] non-success: {data.get('info')}", file=sys.stderr)
            break
        pois = data.get("pois") or []
        if not pois:
            break
        rows.extend(pois)
        if len(pois) < offset:
            break
        time.sleep(pause_ms / 1000)
    return rows


def slugify(name: str, district_id: str, used: set[str]) -> str:
    cleaned = re.sub(r"[\s（）()【】\[\]：:·\-—,，.。!！?？]+", "", name)
    digest = format(abs(hash((district_id, cleaned))) % 10**9, "09d")
    base = f"{district_id}-{digest}"
    cid = base
    n = 2
    while cid in used:
        cid = f"{base}-{n}"
        n += 1
    used.add(cid)
    return cid


def parse_loc(loc) -> tuple[float, float] | None:
    if not isinstance(loc, str) or "," not in loc:
        return None
    a, b = loc.split(",", 1)
    try:
        return float(a), float(b)
    except ValueError:
        return None


def normalize_pois(pois: list[dict], district_id: str, used_ids: set[str], used_names: set[str]) -> list[dict]:
    meta = DISTRICTS[district_id]
    out: list[dict] = []
    for p in pois:
        name = (p.get("name") or "").strip()
        if not name:
            continue
        if any(tok in name for tok in REJECT_TOKENS):
            continue
        adname = (p.get("adname") or "").strip()
        if adname and adname != meta["name"]:
            continue
        loc = parse_loc(p.get("location"))
        if not loc:
            continue
        lng, lat = loc
        key = f"{district_id}::{name}"
        if key in used_names:
            continue
        used_names.add(key)
        cid = slugify(name, district_id, used_ids)
        out.append({
            "district_id": district_id,
            "district_name": meta["name"],
            "short_name": meta["short"],
            "community_id": cid,
            "community_name": name,
            "aliases": [name],
            "source_confidence": 0.93,
            "center_lng": f"{lng:.6f}",
            "center_lat": f"{lat:.6f}",
            "anchor_source": "amap_place",
            "anchor_quality": "0.92",
            "source_refs": [f"amap-place://{p.get('id') or name}"],
            "alias_source": "amap-place",
            "alias_confidence": 0.92,
        })
    return out


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("|".join(v) if isinstance(v, list) else v) for k, v in r.items() if k in fieldnames})


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--pages", type=int, default=4)
    p.add_argument("--offset", type=int, default=25)
    p.add_argument("--pause-ms", type=int, default=120)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    key = (os.getenv("AMAP_WEB_SERVICE_KEY") or os.getenv("AMAP_API_KEY") or "").strip()
    if not key:
        raise SystemExit("missing AMAP_WEB_SERVICE_KEY / AMAP_API_KEY")

    print(f"Discovering communities — {args.pages} pages × {args.offset}/page × {len(DISTRICTS)} districts")
    used_ids: set[str] = set()
    used_names: set[str] = set()
    all_communities: list[dict] = []
    for did, meta in DISTRICTS.items():
        raw = fetch_district_pois(
            key, district_name=meta["name"],
            pages=args.pages, offset=args.offset, pause_ms=args.pause_ms,
        )
        normalized = normalize_pois(raw, did, used_ids, used_names)
        all_communities.extend(normalized)
        print(f"  {meta['name']:<8} raw={len(raw):>3} kept={len(normalized):>3}")
        time.sleep(args.pause_ms / 1000)

    if not all_communities:
        raise SystemExit("no communities fetched")

    districts_payload = [
        {"district_id": did, "district_name": meta["name"], "short_name": meta["short"], "alias_source": "amap-place"}
        for did, meta in DISTRICTS.items()
    ]

    REF_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REF_DIR / "district_dictionary.json", districts_payload)
    write_json(REF_DIR / "community_dictionary.json", all_communities)
    write_json(REF_DIR / "building_dictionary.json", [])
    write_json(REF_DIR / "reference_catalog.json", {
        "districts": districts_payload, "communities": all_communities, "buildings": [],
    })

    csv_fields = [
        "district_id", "community_id", "community_name", "aliases",
        "center_lng", "center_lat", "anchor_source", "anchor_quality",
        "source_confidence", "alias_source", "alias_confidence",
    ]
    write_csv(REF_DIR / "community_dictionary_enriched.csv", all_communities, csv_fields)
    write_json(REF_DIR / "anchor_report.json", {
        "community_count": len(all_communities),
        "anchored_count": len(all_communities),
        "anchored_pct": 100.0,
        "items": [],
    })
    write_json(REF_DIR / "anchor_review_history.json", [])

    summary = {
        "district_count": len(districts_payload),
        "community_count": len(all_communities),
        "building_count": 0,
        "community_alias_count": sum(len(c["aliases"]) for c in all_communities),
        "building_alias_count": 0,
        "source_ref_count": len(all_communities),
        "anchored_community_count": len(all_communities),
        "anchored_building_count": 0,
    }
    write_json(REF_DIR / "summary.json", summary)
    write_json(REF_DIR / "manifest.json", {
        "run_id": RUN_NAME,
        "provider_id": "amap-aoi-poi",
        "batch_name": RUN_NAME,
        "created_at": TS_ISO,
        "adapter_scope": "dictionary_batch",
        "adapter_contract": {
            "scope": "dictionary_batch",
            "description": "AMAP-discovered residential communities (real names + GCJ-02 coords). No listings.",
            "requiredOutputs": [
                "manifest", "district_dictionary", "community_dictionary",
                "building_dictionary", "reference_catalog", "summary",
            ],
            "recordKinds": ["district", "community", "community_alias", "community_anchor"],
        },
        "inputs": {
            "amap_endpoint": PLACE_ENDPOINT, "amap_types": RESIDENTIAL_TYPES,
            "pages_per_district": args.pages,
        },
        "outputs": {k: str(REF_DIR / f"{k}.json" if k != "community_dictionary_enriched"
                           else REF_DIR / f"{k}.csv") for k in [
            "district_dictionary", "community_dictionary", "building_dictionary",
            "reference_catalog", "summary", "community_dictionary_enriched",
            "anchor_report", "anchor_review_history",
        ]} | {"manifest": str(REF_DIR / "manifest.json")},
        "summary": summary,
    })
    print(f"\nstaged → {REF_DIR}")
    print(f"  communities: {len(all_communities)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
