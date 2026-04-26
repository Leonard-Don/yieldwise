from __future__ import annotations

from api.schemas.districts import DistrictSummary


def test_district_summary_round_trip_minimal() -> None:
    payload = {
        "id": "pudong",
        "name": "浦东新区",
        "yield": 4.5,
        "score": 80,
        "sample": 100,
        "community_count": 12,
        "communities": [],
    }
    summary = DistrictSummary.model_validate(payload)
    assert summary.name == "浦东新区"
    assert summary.yield_pct == 4.5
    assert summary.community_count == 12


def test_district_summary_serialises_yield_alias() -> None:
    summary = DistrictSummary(
        id="pudong",
        name="浦东新区",
        yield_pct=4.5,
        score=80,
        sample=100,
        community_count=0,
        communities=[],
    )
    dump = summary.model_dump(by_alias=True)
    assert dump["yield"] == 4.5
    assert "yield_pct" not in dump


def test_district_summary_communities_default_empty() -> None:
    summary = DistrictSummary.model_validate(
        {"id": "x", "name": "Y", "yield": 0.0, "score": 0, "sample": 0, "community_count": 0}
    )
    assert summary.communities == []
