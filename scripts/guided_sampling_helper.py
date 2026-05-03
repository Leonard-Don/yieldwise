#!/usr/bin/env python3
"""Emit a per-task public sampling worklist CSV.

This is NOT a scraper — it does not fetch listing pages. It only converts
the live browser-sampling task pack, or the human-curated backlog markdown,
into a structured CSV that lets you work through targets one at a time.

For each target it produces:
- community + building/floor context
- desired sale + rent counts (to know when you can move on)
- sale + rent search keywords you can paste into any regular browser

Output:
    tmp/sampling-tasks/<TS>/worklist.csv
    tmp/sampling-tasks/<TS>/worklist.json   # same data, easier to read in code

You then:
1. Open each suggested URL in a regular browser (no automation).
2. Use the existing workbench `/backstage/` 公开页面采样执行台 to capture.
3. After capturing, mark the task done in your own way (the CSV is a worklist
   not a state machine).

Run:
    python3 scripts/guided_sampling_helper.py --live-pack
    python3 scripts/guided_sampling_helper.py --live-pack --limit 20
    python3 scripts/guided_sampling_helper.py --live-pack --limit 20 --sync-backlog
    python3 scripts/guided_sampling_helper.py --priorities 1     # markdown backlog only
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

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG = ROOT_DIR / "docs" / "internal" / "public-sampling-backlog.md"

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


def build_public_search_query(community: str, business: str = "sale") -> str:
    suffix = "二手房" if business == "sale" else "租房"
    return f"上海 {community} {suffix}"


def _compact_target_scope(item: dict) -> str:
    parts = []
    building = str(item.get("buildingName") or "").strip()
    floor_no = item.get("floorNo")
    if building:
        parts.append(building)
    if floor_no not in (None, ""):
        parts.append(f"{int(floor_no)}层")
    if not parts:
        target_granularity = str(item.get("targetGranularity") or "")
        if target_granularity == "community":
            return "小区补面"
        return str(item.get("taskTypeLabel") or target_granularity or "补样")
    return " ".join(parts)


def _target_counts(item: dict) -> tuple[int | None, int | None, int | None]:
    if str(item.get("targetGranularity") or "") == "floor":
        current = item.get("currentPairCount")
        target = item.get("targetPairCount")
        missing = item.get("missingPairCount")
    else:
        current = item.get("currentSampleSize")
        target = item.get("targetSampleSize")
        missing = item.get("missingSampleCount")
    return (
        int(current) if current not in (None, "") else None,
        int(target) if target not in (None, "") else None,
        int(missing) if missing not in (None, "") else None,
    )


def live_pack_items_to_rows(items: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for item in items:
        current_count, target_count, missing_count = _target_counts(item)
        rows.append(
            {
                "source_mode": "live_pack",
                "task_id": item.get("taskId"),
                "priority_score": item.get("priorityScore"),
                "priority_label": item.get("priorityLabel"),
                "task_type_label": item.get("taskTypeLabel"),
                "target_granularity": item.get("targetGranularity"),
                "district": item.get("districtName"),
                "community": item.get("communityName"),
                "scope": _compact_target_scope(item),
                "building": item.get("buildingName") or "",
                "floor": item.get("floorNo") or "",
                "current_count": current_count,
                "target_count": target_count,
                "delta_to_target": missing_count,
                "pending_attention_count": item.get("pendingAttentionCount") or 0,
                "task_lifecycle_label": item.get("taskLifecycleLabel") or "",
                "capture_goal": item.get("captureGoal") or "",
                "sale_search_query": item.get("saleQuery")
                or build_public_search_query(str(item.get("communityName") or ""), "sale"),
                "rent_search_query": item.get("rentQuery")
                or build_public_search_query(str(item.get("communityName") or ""), "rent"),
                "recommended_action": item.get("recommendedAction") or "",
                "required_fields": " / ".join(item.get("requiredFields") or []),
            }
        )
    return rows


def items_to_rows(items: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for it in items:
        community = it["community"]
        sale_query = build_public_search_query(community, "sale")
        rent_query = build_public_search_query(community, "rent")
        delta = (it["target_count"] or 0) - (it["current_count"] or 0) if it["target_count"] else None
        rows.append(
            {
                "source_mode": "markdown_backlog",
                "priority": it["priority"],
                "scope_kind": it["scope_kind"],
                "community": community,
                "scope": it["scope"],
                "current_count": it["current_count"],
                "target_count": it["target_count"],
                "delta_to_target": delta,
                "sale_search_query": sale_query,
                "rent_search_query": rent_query,
            }
        )
    return rows


def live_rows_to_backlog_sections(rows: list[dict], *, generated_at: str | None = None) -> dict[str, str]:
    timestamp = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    groups = {
        "当前第一优先级": [],
        "当前第二优先级": [],
    }
    for row in rows:
        priority_score = int(row.get("priority_score") or 0)
        priority_label = str(row.get("priority_label") or "")
        section = "当前第一优先级" if priority_score >= 90 or "极高" in priority_label else "当前第二优先级"
        groups[section].append(row)

    sections: dict[str, str] = {}
    for section, section_rows in groups.items():
        lines = [
            f"## {section}",
            "",
            f"`{timestamp}` 从实时 `browser_sampling_pack` 同步；继续补样前可重新运行 `python3 scripts/guided_sampling_helper.py --live-pack --limit 20 --sync-backlog`。",
            "",
        ]
        if not section_rows:
            lines.append("- 当前实时任务包没有该优先级未完成项。")
        for row in section_rows:
            community = row.get("community") or "未知小区"
            scope = row.get("scope") or row.get("target_granularity") or "补样"
            current = row.get("current_count")
            target = row.get("target_count")
            delta = row.get("delta_to_target")
            pending = row.get("pending_attention_count") or 0
            capture_goal = str(row.get("capture_goal") or "").strip()
            recommended_action = str(row.get("recommended_action") or "").strip()
            sale_query = str(row.get("sale_search_query") or "").strip()
            rent_query = str(row.get("rent_search_query") or "").strip()
            target_bits = []
            if current not in (None, ""):
                target_bits.append(f"当前 `{current}`")
            if target not in (None, ""):
                target_bits.append(f"目标 `{target}`")
            if delta not in (None, "", 0):
                target_bits.append(f"还差 `{delta}`")
            if pending:
                target_bits.append(f"待复核 `{pending}`")
            goal = " / ".join(target_bits) or capture_goal or "按实时任务包继续补样"
            lines.append(f"- {community} `{scope}`")
            lines.append(f"  - 目标：{goal}。")
            if capture_goal:
                lines.append(f"  - 补样口径：{capture_goal}")
            if recommended_action:
                lines.append(f"  - 建议：{recommended_action}")
            if sale_query:
                lines.append(f"  - sale query：`{sale_query}`")
            if rent_query:
                lines.append(f"  - rent query：`{rent_query}`")
        sections[section] = "\n".join(lines).rstrip() + "\n"
    return sections


def replace_backlog_priority_sections(text: str, sections: dict[str, str]) -> str:
    updated = text
    ordered_headings = ["当前第一优先级", "当前第二优先级"]
    for heading in ordered_headings:
        body = sections.get(heading)
        if body is None:
            continue
        pattern = re.compile(
            rf"^## {re.escape(heading)}\n.*?(?=^## |\Z)",
            re.S | re.M,
        )
        if pattern.search(updated):
            updated = pattern.sub(body.rstrip() + "\n\n", updated, count=1)
        else:
            insert_at = updated.find("\n## 已完成")
            if insert_at == -1:
                updated = updated.rstrip() + "\n\n" + body.rstrip() + "\n"
            else:
                updated = updated[:insert_at].rstrip() + "\n\n" + body.rstrip() + "\n" + updated[insert_at:]
    return updated.rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--live-pack", action="store_true",
                   help="Read the current backend browser_sampling_pack instead of the markdown backlog")
    p.add_argument("--backlog-file", type=Path, default=DEFAULT_BACKLOG)
    p.add_argument("--priorities", type=int, nargs="+", default=None,
                   help="Only emit these priority levels (0=P0, 1=first, 2=second)")
    p.add_argument("--limit", type=int, default=20, help="Maximum live-pack tasks to emit")
    p.add_argument("--district", default=None, help="Optional live-pack district filter")
    p.add_argument("--focus-scope", default=None, help="Optional live-pack focus scope filter")
    p.add_argument("--min-yield", type=float, default=0.0, help="Optional live-pack minimum yield filter")
    p.add_argument("--max-budget", type=float, default=10_000.0, help="Optional live-pack max budget filter")
    p.add_argument("--min-samples", type=int, default=0, help="Optional live-pack minimum sample filter")
    p.add_argument("--output-root", type=Path, default=ROOT_DIR / "tmp" / "sampling-tasks")
    p.add_argument("--sync-backlog", action="store_true",
                   help="With --live-pack, replace current priority sections in the markdown backlog.")
    p.add_argument("--dry-run", action="store_true",
                   help="Print the synchronized backlog instead of writing it.")
    return p.parse_args()


def _load_live_pack(args: argparse.Namespace) -> dict:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from api.backstage.review import browser_sampling_pack_payload

    return browser_sampling_pack_payload(
        district=args.district,
        min_yield=args.min_yield,
        max_budget=args.max_budget,
        min_samples=args.min_samples,
        focus_scope=args.focus_scope,
        limit=args.limit,
    )


def main() -> int:
    args = parse_args()
    pack_summary: dict | None = None
    if args.live_pack:
        payload = _load_live_pack(args)
        items = payload.get("items") or []
        pack_summary = payload.get("summary") or {}
        rows = live_pack_items_to_rows(items)
    else:
        if not args.backlog_file.exists():
            raise SystemExit(f"backlog file not found: {args.backlog_file}")
        text = args.backlog_file.read_text(encoding="utf-8")
        items = parse_backlog(text)
        if args.priorities is not None:
            items = [i for i in items if i["priority"] in args.priorities]
        rows = items_to_rows(items)
    if not rows:
        print("no items parsed — check live filters, backlog format, or --priorities filter", file=sys.stderr)
        return 1

    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")
    mode = "live-pack" if args.live_pack else "backlog"
    out_dir = args.output_root / f"{ts}-{mode}"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "worklist.csv"
    json_path = out_dir / "worklist.json"
    fields = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.sync_backlog:
        if not args.live_pack:
            raise SystemExit("--sync-backlog requires --live-pack")
        if not args.backlog_file.exists():
            raise SystemExit(f"backlog file not found: {args.backlog_file}")
        sections = live_rows_to_backlog_sections(rows)
        synced = replace_backlog_priority_sections(args.backlog_file.read_text(encoding="utf-8"), sections)
        if args.dry_run:
            print(synced)
        else:
            args.backlog_file.write_text(synced, encoding="utf-8")
            print(f"backlog synced → {args.backlog_file}")

    if args.live_pack and pack_summary:
        print(f"\nworklist → {csv_path}")
        print(
            "  live pack: "
            f"{pack_summary.get('taskCount')} tasks, "
            f"{pack_summary.get('floorTaskCount')} floor / "
            f"{pack_summary.get('buildingTaskCount')} building / "
            f"{pack_summary.get('communityTaskCount')} community, "
            f"pending review queue {pack_summary.get('pendingReviewQueueCount')}"
        )
        print("\n  next 5 tasks to work on:")
        for r in rows[:5]:
            delta = r["delta_to_target"]
            suffix = f" ({delta} more to go)" if delta else ""
            print(f"    • {r['priority_label']} · {r['community']} {r['scope']}{suffix}")
            print(f"      goal: {r['capture_goal']}")
            print(f"      sale query: {r['sale_search_query']}")
            print(f"      rent query: {r['rent_search_query']}")
        return 0

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
        print(f"      sale query: {r['sale_search_query']}")
        print(f"      rent query: {r['rent_search_query']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
