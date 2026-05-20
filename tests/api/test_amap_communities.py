"""Unit tests for AMAP catalog import normalization helpers."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from jobs.import_amap_communities import normalize_pois, parse_loc, slugify


def test_slugify_produces_unique_ids() -> None:
    used: set[str] = set()
    a = slugify("汤臣一品", "pudong", used)
    b = slugify("汤臣一品", "pudong", used)  # same name → must collide-resolve
    c = slugify("瑞虹新城", "hongkou", used)
    assert a != b
    assert c != a
    # All three are distinct ids and recorded in `used`
    assert len(used) == 3


def test_parse_loc_handles_amap_format() -> None:
    assert parse_loc("121.500000,31.200000") == (121.5, 31.2)


def test_parse_loc_rejects_bad_input() -> None:
    assert parse_loc("not-a-coord") is None
    assert parse_loc("") is None
    assert parse_loc(None) is None
    assert parse_loc("121.5") is None


def test_normalize_pois_drops_blacklisted_names() -> None:
    pois = [
        {"name": "汤臣一品", "adname": "浦东新区", "location": "121.5,31.2", "id": "1"},
        {"name": "汤臣一品停车场", "adname": "浦东新区", "location": "121.5,31.2", "id": "2"},
        {"name": "汤臣一品售楼处", "adname": "浦东新区", "location": "121.5,31.2", "id": "3"},
    ]
    out = normalize_pois(pois, "pudong", set(), set())
    names = [r["community_name"] for r in out]
    assert "汤臣一品" in names
    assert "汤臣一品停车场" not in names
    assert "汤臣一品售楼处" not in names


def test_normalize_pois_drops_cross_district_results() -> None:
    pois = [
        {"name": "对的", "adname": "浦东新区", "location": "121.5,31.2", "id": "1"},
        {"name": "错区域", "adname": "黄浦区", "location": "121.5,31.2", "id": "2"},
    ]
    out = normalize_pois(pois, "pudong", set(), set())
    assert [r["community_name"] for r in out] == ["对的"]


def test_normalize_pois_dedup_within_district() -> None:
    pois = [{"name": "X", "adname": "浦东新区", "location": "121.5,31.2", "id": "1"}] * 3
    out = normalize_pois(pois, "pudong", set(), set())
    assert len(out) == 1


def test_normalize_pois_emits_both_datums() -> None:
    # AMAP location is GCJ-02. The row must keep it as center_lng/center_lat
    # (datum-tagged) AND carry a converted WGS-84 pair so OSM matching is
    # datum-consistent.
    pois = [{"name": "汤臣一品", "adname": "浦东新区", "location": "121.500000,31.200000", "id": "1"}]
    out = normalize_pois(pois, "pudong", set(), set())
    row = out[0]
    assert row["coordinate_datum"] == "gcj02"
    assert row["center_lng"] == "121.500000"
    assert row["center_lat"] == "31.200000"
    # WGS-84 pair is present, parseable, and genuinely offset from GCJ-02
    # (Shanghai datum gap is hundreds of metres → ~1e-3° in each axis).
    wgs_lng = float(row["center_lng_wgs84"])
    wgs_lat = float(row["center_lat_wgs84"])
    assert abs(wgs_lng - 121.5) > 1e-4
    assert abs(wgs_lat - 31.2) > 1e-4
    # For this Shanghai point, WGS-84 longitude sits below GCJ-02 while
    # latitude sits above it; both assertions pin that this is a real
    # conversion, not a copied coordinate pair.
    assert wgs_lng < 121.5
    assert wgs_lat > 31.2


def test_slugify_id_is_stable_across_processes() -> None:
    """community_id must not depend on PYTHONHASHSEED.

    The builtin hash() is salted per process, so a hash()-based id makes every
    re-import assign fresh ids for the same community — breaking ON CONFLICT
    upserts and orphaning downstream references (watchlist, OSM matches).
    """
    repo_root = Path(__file__).resolve().parents[2]
    snippet = "from jobs.import_amap_communities import slugify\nprint(slugify('汤臣一品', 'pudong', set()))"

    def run_with_seed(seed: str) -> str:
        result = subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=repo_root,
            env={**os.environ, "PYTHONHASHSEED": seed},
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    assert run_with_seed("0") == run_with_seed("1") == run_with_seed("2")
