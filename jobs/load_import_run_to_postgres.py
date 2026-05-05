from __future__ import annotations

import argparse
import json
from pathlib import Path

from api.persistence import persist_import_run_to_postgres
from api.service import read_json_file


def run_id_from_manifest(path: Path) -> str:
    manifest = read_json_file(path)
    if not isinstance(manifest, dict) or not manifest.get("run_id"):
        raise SystemExit(f"{path} 不是合法的 manifest.json，缺少 run_id。")
    return str(manifest["run_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Persist a browser-scraped import run into PostgreSQL.")
    parser.add_argument("--run-id", help="Import run id, e.g. pudong-demo-2026-04-11-20260411223336.")
    parser.add_argument("--manifest", type=Path, help="Path to manifest.json. If provided, run_id will be read from it.")
    parser.add_argument("--apply-schema", action="store_true", help="Apply db/schema.sql before writing data.")
    parser.add_argument("--dsn", help="Optional PostgreSQL DSN. Falls back to POSTGRES_DSN env var.")
    args = parser.parse_args()

    run_id = args.run_id
    if args.manifest:
        run_id = run_id_from_manifest(args.manifest)
    if not run_id:
        raise SystemExit("需要提供 --run-id 或 --manifest。")

    result = persist_import_run_to_postgres(run_id, dsn=args.dsn, apply_schema=args.apply_schema)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
