#!/usr/bin/env python3
"""Read docs/public-sampling-backlog.md, emit a per-task worklist CSV.

This is NOT a scraper — it does not fetch listing pages. It only converts
the human-curated backlog markdown into a structured CSV that lets you
work through targets one at a time without re-reading the prose.

For each backlog target it produces:
- community + building/floor context
- desired sale + rent counts (to know when you can move on)
- a pre-built 安居客 search URL (the same source that public-open-snapshot
  used: mobile.anjuke.com/sh/...) so you can open the right page in one click

Output:
    tmp/sampling-tasks/<TS>/worklist.csv
    tmp/sampling-tasks/<TS>/worklist.json   # same data, easier to read in code

You then:
1. Open each suggested URL in a regular browser (no automation).
2. Use the existing workbench `/backstage/` 公开页面采样执行台 to capture.
3. After capturing, mark the task done in your own way (the CSV is a worklist
   not a state machine).

Run:
    python3 scripts/guided_sampling_helper.py
    python3 scripts/guided_sampling_helper.py --priorities 1     # only P1
    python3 scripts/guided_sampling_helper.py --backlog-file path/to/different.md
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG = ROOT_DIR / "docs" / "public-sampling-backlog.md"

# Section detection: which markdown headings count as priority groupings.
PRIORITY_HEADERS: dict[str, int] = {
    "🔴 P0": 0,
    "P0": 0,
    "当前第一优先级": 1,
    "当前第二优先级": 2,
}

# Item-line patterns we recognize, e.g.:
#   - 松江大学城嘉和休闲广场 `B座 9层`
#   - 七宝云庭 `3幢`
#   - 联洋年华 `小区补面`
ITEM_PATTERN = re.compile(
    r"^- \s*(?P<community>[一-鿿]+(?:[A-Za-z0-9·\-_/]+)*[一-鿿]*)\s+`(?P<scope>[^`]+)`\s*$"
)

# Goal patterns inside each item, e.g.: "目标：从当前 `3` 组 pair 补到 `4` 组"
# (the live backlog wraps digits in backticks; older format is plain digits)
GOAL_FROM_TO = re.compile(r"从.*?`?(\d+)`?\s*(?:组|条|套).*?补到\s*`?(\d+)`?\s*(?:组|条|套)")


def parse_backlog(text: str) -> list[dict]:
    items: list[dict] = []
    current_priority: int | None = None
    current_section: str | None = None
    pending: dict | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        # Section heading?
        if line.startswith("##"):
            heading = line.lstrip("# ").strip()
            current_section = heading
            current_priority = None
            for needle, level in PRIORITY_HEADERS.items():
                if needle in heading:
                    current_priority = level
                    break
            continue
        if current_priority is None:
            continue

        # New item line?
        m = ITEM_PATTERN.match(line)
        if m:
            if pending:
                items.append(pending)
            pending = {
                "priority": current_priority,
                "section": current_section,
                "community": m.group("community"),
                "scope": m.group("scope"),
                "current_count": None,
                "target_count": None,
                "scope_kind": _infer_scope_kind(m.group("scope")),
            }
            continue

        # Goal line under an existing item?
        if pending and "目标" in line:
            gm = GOAL_FROM_TO.search(line)
            if gm:
                pending["current_count"] = int(gm.group(1))
                pending["target_count"] = int(gm.group(2))

    if pending:
        items.append(pending)
    return items


def _infer_scope_kind(scope: str) -> str:
    if "层" in scope:
        return "floor_pair"
    if "幢" in scope or "号楼" in scope or "栋" in scope or "座" in scope:
        return "building_depth"
    if "小区" in scope or "补面" in scope:
        return "community_profile"
    return "other"


def build_anjuke_url(community: str, business: str = "sale") -> str:
    base = "https://shanghai.anjuke.com/sale/?kw=" if business == "sale" else "https://shanghai.anjuke.com/zu/?kw="
    return base + quote(community)


def items_to_rows(items: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for it in items:
        community = it["community"]
        sale_url = build_anjuke_url(community, "sale")
        rent_url = build_anjuke_url(community, "rent")
        delta = (it["target_count"] or 0) - (it["current_count"] or 0) if it["target_count"] else None
        rows.append({
            "priority": it["priority"],
            "scope_kind": it["scope_kind"],
            "community": community,
            "scope": it["scope"],
            "current_count": it["current_count"],
            "target_count": it["target_count"],
            "delta_to_target": delta,
            "anjuke_sale_search": sale_url,
            "anjuke_rent_search": rent_url,
        })
    return rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--backlog-file", type=Path, default=DEFAULT_BACKLOG)
    p.add_argument("--priorities", type=int, nargs="+", default=None,
                   help="Only emit these priority levels (0=P0, 1=first, 2=second)")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "sampling-tasks")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not args.backlog_file.exists():
        raise SystemExit(f"backlog file not found: {args.backlog_file}")
    text = args.backlog_file.read_text(encoding="utf-8")
    items = parse_backlog(text)
    if args.priorities is not None:
        items = [i for i in items if i["priority"] in args.priorities]
    if not items:
        print("no items parsed — check backlog format or --priorities filter", file=sys.stderr)
        return 1

    rows = items_to_rows(items)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    out_dir = args.output_root / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "worklist.csv"
    json_path = out_dir / "worklist.json"
    fields = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    by_priority: dict[int, int] = {}
    for r in rows:
        by_priority[r["priority"]] = by_priority.get(r["priority"], 0) + 1
    print(f"\nworklist → {csv_path}")
    for level in sorted(by_priority):
        label = {0: "P0", 1: "第一优先级", 2: "第二优先级"}.get(level, f"P{level}")
        print(f"  {label}: {by_priority[level]} tasks")
    print("\n  next 3 tasks to work on:")
    for r in rows[:3]:
        delta = r["delta_to_target"]
        suffix = f" ({delta} more to go)" if delta else ""
        print(f"    • {r['community']} {r['scope']}{suffix}")
        print(f"      sale: {r['anjuke_sale_search']}")
        print(f"      rent: {r['anjuke_rent_search']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
