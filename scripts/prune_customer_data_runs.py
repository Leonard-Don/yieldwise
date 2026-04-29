"""Delete tmp/customer-data-runs/<run_id>/ folders older than a threshold."""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


def runs_dir() -> Path:
    override = os.environ.get("ATLAS_CUSTOMER_DATA_RUNS_DIR")
    return Path(override) if override else Path(__file__).resolve().parents[1] / "tmp" / "customer-data-runs"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    base = runs_dir()
    if not base.is_dir():
        print(f"runs dir does not exist: {base}")
        return 0
    pruned = 0
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        try:
            mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime < cutoff:
            print(f"{'DRY RUN: ' if args.dry_run else ''}removing {entry.name} (mtime {mtime.isoformat()})")
            if not args.dry_run:
                shutil.rmtree(entry, ignore_errors=True)
            pruned += 1
    print(f"pruned {pruned} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
