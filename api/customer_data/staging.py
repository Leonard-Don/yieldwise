"""Staged-run storage for customer data uploads.

Layout:
  <runs_dir>/<run_id>/
    portfolio.json        rows: [{...}, ...]
    errors.json
    summary.json          {run_id, client_id, type, row_count, error_count, created_at}
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .parser import ParseResult


@dataclass(frozen=True)
class StagedRun:
    run_id: str
    client_id: str
    type_: str
    row_count: int
    error_count: int
    created_at: str


def _runs_dir() -> Path:
    override = os.environ.get("ATLAS_CUSTOMER_DATA_RUNS_DIR")
    base = Path(override) if override else Path(__file__).resolve().parents[2] / "tmp" / "customer-data-runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _new_run_id() -> str:
    # Lexicographically sortable: ISO timestamp with microseconds + short suffix.
    # Microsecond precision keeps newest-first listing deterministic when callers
    # save several runs in quick succession (otherwise same-second runs would
    # tie-break on the random uuid suffix).
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    suffix = uuid.uuid4().hex[:6]
    return f"{ts}-{suffix}"


def save_run(*, client_id: str, type_: str, parsed: ParseResult) -> StagedRun:
    run_id = _new_run_id()
    run_dir = _runs_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    rows_payload = [r.model_dump(mode="json") for r in parsed.rows]
    (run_dir / f"{type_}.json").write_text(
        json.dumps(rows_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "errors.json").write_text(
        json.dumps(parsed.errors, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "client_id": client_id,
        "type": type_,
        "row_count": len(parsed.rows),
        "error_count": len(parsed.errors),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return StagedRun(
        run_id=run_id,
        client_id=client_id,
        type_=type_,
        row_count=len(parsed.rows),
        error_count=len(parsed.errors),
        created_at=summary["created_at"],
    )


def load_run(run_id: str) -> StagedRun | None:
    summary_path = _runs_dir() / run_id / "summary.json"
    if not summary_path.is_file():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return StagedRun(
        run_id=summary["run_id"],
        client_id=summary["client_id"],
        type_=summary["type"],
        row_count=summary["row_count"],
        error_count=summary["error_count"],
        created_at=summary["created_at"],
    )


def load_run_rows(run_id: str) -> list[dict]:
    """Return raw row dicts from <run_id>/<type>.json."""
    run = load_run(run_id)
    if run is None:
        return []
    rows_path = _runs_dir() / run_id / f"{run.type_}.json"
    if not rows_path.is_file():
        return []
    return json.loads(rows_path.read_text(encoding="utf-8"))


def list_runs(*, client_id: str | None = None) -> list[StagedRun]:
    """Return all runs, newest first. Optionally filtered by client_id."""
    runs: list[StagedRun] = []
    base = _runs_dir()
    if not base.is_dir():
        return runs
    for entry in sorted(base.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        run = load_run(entry.name)
        if run is None:
            continue
        if client_id is not None and run.client_id != client_id:
            continue
        runs.append(run)
    return runs
