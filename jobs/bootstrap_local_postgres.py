from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.service import bootstrap_local_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the local Docker PostGIS database for Shanghai Yield Atlas.")
    parser.add_argument("--reference-run-id", help="Optional reference run id. Defaults to the latest available run.")
    parser.add_argument("--import-run-id", help="Optional import run id. Defaults to the latest available run.")
    parser.add_argument("--geo-run-id", help="Optional geo asset run id. Defaults to the latest available run.")
    parser.add_argument("--no-refresh-metrics", action="store_true", help="Skip the metrics snapshot refresh step.")
    parser.add_argument("--no-apply-schema", action="store_true", help="Skip applying db/schema.sql before the bootstrap.")
    args = parser.parse_args()

    result = bootstrap_local_database(
        reference_run_id=args.reference_run_id,
        import_run_id=args.import_run_id,
        geo_run_id=args.geo_run_id,
        apply_schema=not args.no_apply_schema,
        refresh_metrics=not args.no_refresh_metrics,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
