#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.backstage.runs import list_import_runs  # noqa: E402
from api.data_quality import build_data_quality_gate  # noqa: E402
from api.service import current_community_dataset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Atlas staged data quality before refresh/import work.")
    parser.add_argument("--latest-only", action="store_true", help="Only inspect the latest import run for dirty listing rows.")
    parser.add_argument("--allow-blocker", action="store_true", help="Return 0 even when the gate is blocked.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_data_quality_gate(
        communities=current_community_dataset(),
        import_runs=list_import_runs(),
        latest_only=args.latest_only,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if payload.get("status") == "blocker" and not args.allow_blocker:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
