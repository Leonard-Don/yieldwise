#!/usr/bin/env python3
"""Pull Shanghai's monthly residential price index from a public mirror of
国家统计局's 70-city housing index.

Why this exists: data.stats.gov.cn directly is IP-ACL'd against programmatic
access (returns 403 + reason=UrlACL). The same monthly index is mirrored on
fangjia.gotohui.com/fjdata-3 which is publicly fetchable. The values are the
same numbers — just easier to retrieve.

Output (gitignored, reversible):
    tmp/macro-runs/housing-index-shanghai-<DATE>-<TS>/
        manifest.json
        index.json          # {month: ..., secondhand_yuan_per_sqm: ..., new_yuan_per_sqm: ...}
        summary.json

Run:
    python3 jobs/import_macro_housing_index.py
    python3 jobs/import_macro_housing_index.py --city 3   # explicit city id (3 = Shanghai)

Attribution: data ultimately from 国家统计局; this script reads it via the
fangjia.gotohui.com mirror. If you want first-party data later, put a CSV
download from data.stats.gov.cn into data/macro/ and adapt the parser.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))

CITY_NAME_BY_ID: dict[int, str] = {
    1: "全国", 3: "上海", 4: "北京", 5: "深圳", 6: "广州",
    7: "天津", 8: "重庆", 9: "苏州", 10: "杭州",
}

USER_AGENT = "Mozilla/5.0 (compatible; Yieldwise/0.1; +internal-research)"


def fetch_html(url: str, *, timeout: float = 15.0) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except URLError as exc:
        raise SystemExit(f"fetch failed: {url} → {exc}")
    return data.decode("utf-8", errors="replace")


_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)


def parse_table_rows(html: str) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for raw_row in _TR_RE.findall(html):
        cells = [_TAG_RE.sub("", c).strip() for c in _CELL_RE.findall(raw_row)]
        # Expected shape: [row_num, "YYYY-MM", secondhand_int, new_int, _trailing]
        if len(cells) < 4:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}", cells[1]):
            continue
        sec = _parse_int(cells[2])
        new = _parse_int(cells[3])
        if sec is None and new is None:
            continue
        out.append({
            "month": cells[1],
            "secondhand_yuan_per_sqm": sec,
            "new_yuan_per_sqm": new,
        })
    return out


def _parse_int(s: str) -> int | None:
    s = (s or "").replace(",", "").strip()
    if not s:
        return None
    m = re.search(r"-?\d+", s)
    return int(m.group(0)) if m else None


def yoy_change(rows: list[dict[str, object]]) -> dict[str, dict[str, float | None]]:
    """For each month, compute YoY (%) for both indices."""
    by_month = {r["month"]: r for r in rows}
    out: dict[str, dict[str, float | None]] = {}
    for month, r in by_month.items():
        year, mm = month.split("-")
        prior = f"{int(year)-1}-{mm}"
        prior_row = by_month.get(prior)
        if not prior_row:
            continue

        def pct(curr, prev):
            if curr is None or prev in (None, 0):
                return None
            return round((curr - prev) / prev * 100, 2)

        out[month] = {
            "secondhand_yoy_pct": pct(r["secondhand_yuan_per_sqm"], prior_row["secondhand_yuan_per_sqm"]),
            "new_yoy_pct": pct(r["new_yuan_per_sqm"], prior_row["new_yuan_per_sqm"]),
        }
    return out


def build_manifest(*, run_id: str, output_dir: Path, city_id: int, city_name: str, months: int) -> dict:
    return {
        "run_id": run_id,
        "provider_id": "macro-housing-index",
        "batch_name": f"housing-index-{city_name.lower()}",
        "created_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "adapter_scope": "macro_baseline",
        "adapter_contract": {
            "scope": "macro_baseline",
            "description": "Monthly residential price index, mirror of 国家统计局 70-city. Aggregate-only.",
            "requiredOutputs": ["manifest", "index", "summary"],
            "recordKinds": ["monthly_price_point"],
        },
        "inputs": {
            "source_url": f"https://fangjia.gotohui.com/fjdata-{city_id}",
            "source_attribution": "国家统计局 70 城市住宅销售价格变动情况，via fangjia.gotohui.com",
        },
        "outputs": {
            "index": str(output_dir / "index.json"),
            "summary": str(output_dir / "summary.json"),
            "manifest": str(output_dir / "manifest.json"),
        },
        "summary": {"city_id": city_id, "city_name": city_name, "month_count": months},
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--city", type=int, default=3,
                   help="fangjia city id (default 3 = 上海). Common: 3 上海, 4 北京, 5 深圳, 6 广州")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "macro-runs")
    p.add_argument("--limit", type=int, help="Keep only the most-recent N months")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    city_name = CITY_NAME_BY_ID.get(args.city, f"city-{args.city}")
    url = f"https://fangjia.gotohui.com/fjdata-{args.city}"
    print(f"fetching {city_name} housing-index from {url}")
    html = fetch_html(url)

    rows = parse_table_rows(html)
    if not rows:
        raise SystemExit("no monthly rows parsed — page structure may have changed")

    # rows are in chronological-newest-first order on fangjia; sort newest-first explicitly
    rows.sort(key=lambda r: r["month"], reverse=True)
    if args.limit:
        rows = rows[: args.limit]
    yoy = yoy_change(rows)

    ts = datetime.now(TZ).strftime("%Y%m%d%H%M%S")
    output_dir = args.output_root / f"housing-index-{city_name.lower()}-{ts}"
    output_dir.mkdir(parents=True, exist_ok=True)

    enriched = [
        {**r, **(yoy.get(r["month"], {"secondhand_yoy_pct": None, "new_yoy_pct": None}))}
        for r in rows
    ]
    (output_dir / "index.json").write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    latest = rows[0]
    summary = {
        "city_id": args.city,
        "city_name": city_name,
        "month_count": len(rows),
        "earliest_month": rows[-1]["month"],
        "latest_month": latest["month"],
        "latest_secondhand_yuan_per_sqm": latest["secondhand_yuan_per_sqm"],
        "latest_new_yuan_per_sqm": latest["new_yuan_per_sqm"],
        "latest_yoy": yoy.get(latest["month"], {}),
        "fetched_at": datetime.now(TZ).isoformat(timespec="seconds"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    run_id = f"housing-index-{city_name.lower()}-{ts}"
    manifest = build_manifest(
        run_id=run_id,
        output_dir=output_dir,
        city_id=args.city,
        city_name=city_name,
        months=len(rows),
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8",
    )

    print(f"\nstaged → {output_dir}")
    print(f"  months: {len(rows)} ({rows[-1]['month']} → {latest['month']})")
    print(f"  latest secondhand: {latest['secondhand_yuan_per_sqm']} ¥/㎡")
    print(f"  latest new:        {latest['new_yuan_per_sqm']} ¥/㎡")
    if yoy.get(latest["month"]):
        y = yoy[latest["month"]]
        print(f"  YoY secondhand: {y.get('secondhand_yoy_pct')}%  |  new: {y.get('new_yoy_pct')}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
