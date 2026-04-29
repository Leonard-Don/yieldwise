"""Staged-run storage tests."""
from __future__ import annotations

import json

import pytest

from api.customer_data.parser import parse_csv
from api.customer_data.staging import (
    StagedRun,
    list_runs,
    load_run,
    save_run,
)


_GOOD_PORTFOLIO_CSV = (
    "project_name,address,building_no,unit_type,monthly_rent_cny,"
    "occupancy_rate_pct,move_in_date,longitude,latitude\n"
    "Alpha,addr1,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
)


@pytest.fixture(autouse=True)
def runs_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "customer-data-runs"))
    yield tmp_path / "customer-data-runs"


def test_save_run_writes_json_files_and_summary(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    run = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    assert isinstance(run, StagedRun)
    assert run.run_id
    files = sorted(p.name for p in (runs_dir / run.run_id).iterdir())
    assert "portfolio.json" in files
    assert "summary.json" in files
    summary = json.loads((runs_dir / run.run_id / "summary.json").read_text())
    assert summary["row_count"] == 1
    assert summary["error_count"] == 0
    assert summary["client_id"] == "alice"


def test_load_run_round_trips(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    saved = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    loaded = load_run(saved.run_id)
    assert loaded is not None
    assert loaded.run_id == saved.run_id
    assert loaded.row_count == 1
    assert loaded.error_count == 0


def test_load_unknown_run_returns_none(runs_dir):
    assert load_run("does-not-exist") is None


def test_list_runs_returns_recent_first(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    a = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    b = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    c = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    runs = list_runs(client_id="alice")
    ids = [r.run_id for r in runs]
    assert ids == [c.run_id, b.run_id, a.run_id]
