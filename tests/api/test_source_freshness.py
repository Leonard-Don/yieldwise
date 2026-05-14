from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from api.data_quality import audit_source_freshness, source_freshness_row


NOW = datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc)


def _set_mtime(path: Path, when: datetime) -> None:
    ts = when.timestamp()
    os.utime(path, (ts, ts))


def test_fresh_manifest_marked_fresh(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
    _set_mtime(manifest, NOW - timedelta(days=1))

    row = source_freshness_row(
        "import-run-r1",
        manifest,
        label="Import Run r1",
        now=NOW,
        fresh_within_days=14,
    )

    assert row["source"] == "import-run-r1"
    assert row["label"] == "Import Run r1"
    assert row["exists"] is True
    assert row["ok"] is True
    assert row["status"] == "fresh"
    assert row["freshness"] == "新鲜"
    assert row["ageDays"] is not None
    assert 0.5 < row["ageDays"] < 2
    assert row["modifiedAt"] is not None
    assert row["safePath"] is not None
    assert not row["safePath"].startswith("/")


def test_missing_manifest_marked_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope" / "manifest.json"

    row = source_freshness_row("import-run-missing", missing, now=NOW)

    assert row["exists"] is False
    assert row["ok"] is False
    assert row["status"] == "missing"
    assert row["freshness"] == "缺失"
    assert row["modifiedAt"] is None
    assert row["ageDays"] is None
    assert "缺失" in row["reason"]
    safe = row["safePath"]
    assert safe is not None
    assert not safe.startswith("/")


def test_missing_source_with_generated_at_preserves_metadata(tmp_path: Path) -> None:
    spec_generated_at = "2026-04-12T00:00:00+00:00"
    row = source_freshness_row(
        "snapshot",
        tmp_path / "missing.json",
        generated_at=spec_generated_at,
        now=NOW,
    )

    assert row["status"] == "missing"
    assert row["generatedAt"] == spec_generated_at


def test_stale_artifact_marked_stale(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    _set_mtime(manifest, NOW - timedelta(days=60))

    row = source_freshness_row(
        "import-run-old",
        manifest,
        now=NOW,
        fresh_within_days=14,
    )

    assert row["status"] == "stale"
    assert row["freshness"] == "陈旧"
    assert row["ok"] is False
    assert row["ageDays"] is not None and row["ageDays"] > 14
    assert "陈旧" in row["reason"] or "stale" in row["reason"].lower()


def test_future_mtime_marked_invalid(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}", encoding="utf-8")
    _set_mtime(manifest, NOW + timedelta(days=30))

    row = source_freshness_row("import-run-future", manifest, now=NOW)

    assert row["status"] == "invalid"
    assert row["freshness"] == "异常"
    assert row["ok"] is False
    assert row["exists"] is True
    assert "异常" in row["reason"] or "future" in row["reason"].lower()


def test_absolute_user_path_is_sanitized() -> None:
    user_like = Path("/Users/leonardodon/secret/run/manifest.json")

    row = source_freshness_row("leak-check", user_like, now=NOW)

    safe = row["safePath"]
    assert safe is not None
    assert "/Users/" not in safe
    assert "leonardodon" not in safe
    assert not safe.startswith("/")
    assert safe == "manifest.json"


def test_audit_source_freshness_summarises_rows(tmp_path: Path) -> None:
    fresh_dir = tmp_path / "fresh"
    fresh_dir.mkdir()
    fresh_manifest = fresh_dir / "manifest.json"
    fresh_manifest.write_text("{}", encoding="utf-8")
    _set_mtime(fresh_manifest, NOW - timedelta(hours=2))

    stale_dir = tmp_path / "stale"
    stale_dir.mkdir()
    stale_manifest = stale_dir / "manifest.json"
    stale_manifest.write_text("{}", encoding="utf-8")
    _set_mtime(stale_manifest, NOW - timedelta(days=45))

    payload = audit_source_freshness(
        [
            {"source": "fresh-run", "label": "Fresh Run", "path": str(fresh_manifest)},
            {"source": "stale-run", "path": str(stale_manifest)},
            {
                "source": "missing-run",
                "path": str(tmp_path / "nope" / "manifest.json"),
                "generatedAt": "2026-04-12T00:00:00+00:00",
            },
        ],
        now=NOW,
        fresh_within_days=14,
    )

    rows_by_source = {row["source"]: row for row in payload["rows"]}
    assert rows_by_source["fresh-run"]["status"] == "fresh"
    assert rows_by_source["stale-run"]["status"] == "stale"
    assert rows_by_source["missing-run"]["status"] == "missing"
    assert rows_by_source["missing-run"]["generatedAt"] == "2026-04-12T00:00:00+00:00"

    counts = payload["statusCounts"]
    assert counts == {"fresh": 1, "stale": 1, "missing": 1, "invalid": 0}
    assert payload["totalCount"] == 3
    assert payload["status"] == "blocker"
    assert payload["label"] in {"阻断", "需关注", "通过"}

    for row in payload["rows"]:
        safe = row["safePath"]
        assert safe is None or not safe.startswith("/")
