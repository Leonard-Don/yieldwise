from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.persistence import persist_reference_dictionary_manifest_to_postgres


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persist a reference dictionary batch into PostgreSQL.")
    parser.add_argument("--manifest", required=True, type=Path, help="Path to dictionary manifest.json")
    parser.add_argument("--dsn", help="Optional PostgreSQL DSN. Falls back to POSTGRES_DSN env var.")
    parser.add_argument("--apply-schema", action="store_true", help="Apply db/schema.sql before persisting.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = persist_reference_dictionary_manifest_to_postgres(
        args.manifest,
        dsn=args.dsn,
        apply_schema=args.apply_schema,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
