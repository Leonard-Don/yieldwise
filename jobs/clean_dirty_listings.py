#!/usr/bin/env python3
"""Quarantine UI-corruption artifacts in staged sale + rent rows.

Two known systemic bugs in the public-browser-sampling UI capture path
(see docs/public-sampling-backlog.md P0 section, 2026-04-29):

1. RENT corruption — total_floors leaks into monthly_rent. Symptom: rent
   values like 1, 16, 19 元/月 across 22 communities (24% of all rent rows).
   Rule: any rent row where 0 < monthly_rent < threshold (default 1000)
   gets monthly_rent set to None.

2. SALE corruption — UI form default leaks into price_total_wan +
   unit_price_yuan. Symptom: 2913 rows with the exact tuple
   (price_total_wan=323.0, unit_price_yuan=36292.13). Rule: any sale row
   matching that exact signature gets BOTH price fields set to None.

This script does NOT delete rows; it nulls the offending price fields
so downstream aggregation (compute_yield_pct, median rollups) treats them
as "no signal" — which is exactly what the staged path already does for
zero/null prices.

Backups (originals) are written next to each run as
    normalized_rent.json.bak-<TS>
    normalized_sale.json.bak-<TS>
unless --no-backup is passed.

Run:
    # dry-run, just report what would be cleaned:
    python3 jobs/clean_dirty_listings.py --dry-run

    # actually clean (with .bak files):
    python3 jobs/clean_dirty_listings.py
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RUNS_ROOT = ROOT_DIR / "tmp" / "import-runs"

# Sale-bug signature — exact UI-default tuple. Both fields must match.
SALE_BUG_WAN = 323.0
SALE_BUG_UNIT = 36292.13


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--rent-threshold", type=float, default=1000.0,
                   help="Floor below which monthly_rent is suspicious (default: 1000 元/月)")
    p.add_argument("--sale-bug-wan", type=float, default=SALE_BUG_WAN)
    p.add_argument("--sale-bug-unit", type=float, default=SALE_BUG_UNIT)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--runs-root", type=Path, default=RUNS_ROOT)
    p.add_argument("--rent-only", action="store_true", help="Skip sale cleanup")
    p.add_argument("--sale-only", action="store_true", help="Skip rent cleanup")
    return p.parse_args()


def _safe_float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def clean_rent(rows, threshold, dry_run, affected_communities) -> int:
    cleaned = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        rent = _safe_float(row.get("monthly_rent"))
        if rent is None or rent <= 0 or rent >= threshold:
            continue
        cleaned += 1
        key = (row.get("resolved_district_name") or "?", row.get("resolved_community_name") or row.get("raw_community_name") or "?")
        affected_communities[key] = affected_communities.get(key, 0) + 1
        if not dry_run:
            row["monthly_rent"] = None
            row["resolution_notes"] = (
                (row.get("resolution_notes") or "")
                + f" | clean_dirty: rent original={rent} threshold={threshold}"
            ).strip(" |")
    return cleaned


def clean_sale(rows, bug_wan, bug_unit, dry_run, affected_communities) -> int:
    cleaned = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        wan = _safe_float(row.get("price_total_wan"))
        unit = _safe_float(row.get("unit_price_yuan"))
        if wan is None or unit is None:
            continue
        if abs(wan - bug_wan) > 0.01 or abs(unit - bug_unit) > 0.01:
            continue
        cleaned += 1
        key = (row.get("resolved_district_name") or "?", row.get("resolved_community_name") or row.get("raw_community_name") or "?")
        affected_communities[key] = affected_communities.get(key, 0) + 1
        if not dry_run:
            row["price_total_wan"] = None
            row["unit_price_yuan"] = None
            row["resolution_notes"] = (
                (row.get("resolution_notes") or "")
                + f" | clean_dirty: sale original_wan={wan} unit={unit} (UI-default)"
            ).strip(" |")
    return cleaned


def process_file(path: Path, *, kind: str, dry_run: bool, no_backup: bool, ts: str, **opts) -> tuple[int, int]:
    """Return (rows_in_file, rows_cleaned)."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0, 0
    if not isinstance(rows, list):
        return 0, 0

    affected = opts.get("affected_communities") or {}
    if kind == "rent":
        cleaned = clean_rent(rows, opts["threshold"], dry_run, affected)
    else:
        cleaned = clean_sale(rows, opts["bug_wan"], opts["bug_unit"], dry_run, affected)

    if cleaned > 0 and not dry_run:
        if not no_backup:
            (path.with_name(f"{path.name}.bak-{ts}")).write_text(
                json.dumps(json.loads(path.with_name(path.name).read_bytes()), ensure_ascii=False, indent=2)
                if False else path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rows), cleaned


def main() -> int:
    args = parse_args()
    if not args.runs_root.exists():
        raise SystemExit(f"runs root not found: {args.runs_root}")

    ts = datetime.now().strftime("%Y%m%d%H%M%S")

    rent_files = [] if args.sale_only else sorted(args.runs_root.glob("*/normalized_rent.json"))
    sale_files = [] if args.rent_only else sorted(args.runs_root.glob("*/normalized_sale.json"))

    rent_affected: dict[tuple[str, str], int] = {}
    sale_affected: dict[tuple[str, str], int] = {}
    rent_total_cleaned = 0
    sale_total_cleaned = 0
    rent_runs_touched = 0
    sale_runs_touched = 0

    for path in rent_files:
        _, n = process_file(
            path, kind="rent", dry_run=args.dry_run, no_backup=args.no_backup, ts=ts,
            threshold=args.rent_threshold, affected_communities=rent_affected,
        )
        if n > 0:
            rent_total_cleaned += n
            rent_runs_touched += 1

    for path in sale_files:
        _, n = process_file(
            path, kind="sale", dry_run=args.dry_run, no_backup=args.no_backup, ts=ts,
            bug_wan=args.sale_bug_wan, bug_unit=args.sale_bug_unit,
            affected_communities=sale_affected,
        )
        if n > 0:
            sale_total_cleaned += n
            sale_runs_touched += 1

    mode = "[DRY RUN] " if args.dry_run else ""

    if rent_files:
        print(f"\n{mode}rent: cleaned {rent_total_cleaned} rows below {args.rent_threshold} 元/月 across {rent_runs_touched} runs")
        if rent_affected:
            print(f"  affected communities ({len(rent_affected)}):")
            for (d, c), n in sorted(rent_affected.items(), key=lambda kv: -kv[1])[:10]:
                print(f"    {d} / {c}: {n}")
            if len(rent_affected) > 10:
                print(f"    … +{len(rent_affected) - 10} more")

    if sale_files:
        print(f"\n{mode}sale: cleaned {sale_total_cleaned} rows matching UI-default tuple "
              f"(wan={args.sale_bug_wan}, unit={args.sale_bug_unit}) across {sale_runs_touched} runs")
        if sale_affected:
            print(f"  affected communities ({len(sale_affected)}):")
            for (d, c), n in sorted(sale_affected.items(), key=lambda kv: -kv[1])[:10]:
                print(f"    {d} / {c}: {n}")
            if len(sale_affected) > 10:
                print(f"    … +{len(sale_affected) - 10} more")

    if not args.dry_run and not args.no_backup and (rent_runs_touched or sale_runs_touched):
        print(f"\nbackups: {rent_runs_touched + sale_runs_touched} files with suffix .bak-{ts}")
        print("revert with:")
        print(f"  for f in tmp/import-runs/*/normalized_*.json.bak-{ts}; do mv \"$f\" \"${{f%.bak-{ts}}}\"; done")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
