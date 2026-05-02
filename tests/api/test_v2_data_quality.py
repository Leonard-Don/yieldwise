from __future__ import annotations


def test_v2_data_quality_gate_exposes_summary(client) -> None:
    response = client.get("/api/v2/data-quality")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] in {"ok", "warn", "blocker"}
    assert payload["label"] in {"通过", "需关注", "阻断"}
    assert payload["communityCount"] >= 0
    assert payload["statusCounts"].keys() >= {"strong", "usable", "thin", "blocked"}
    assert payload["dirtyListings"].keys() >= {"totalIssueCount", "rentIssueCount", "saleIssueCount"}
    assert {item["id"] for item in payload["checks"]} >= {
        "dirty_listing_rows",
        "community_quality",
        "quality_score",
    }
