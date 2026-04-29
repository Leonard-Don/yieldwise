"""Unit tests for AMAP catalog import normalization helpers."""
from __future__ import annotations

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
