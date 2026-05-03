from __future__ import annotations


def test_decision_memo_requires_targets(client) -> None:
    response = client.post("/api/v2/decision-memo", json={"targets": []})
    assert response.status_code == 400


def test_decision_memo_returns_markdown_for_opportunity(client) -> None:
    opportunities = client.get("/api/v2/opportunities")
    assert opportunities.status_code == 200, opportunities.text
    items = opportunities.json()["items"]
    assert items
    candidate = items[0]

    response = client.post(
        "/api/v2/decision-memo",
        json={
            "targets": [
                {
                    "target_id": candidate["id"],
                    "target_type": "community",
                }
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["targetCount"] == 1
    assert body["items"][0]["targetId"] == candidate["id"]
    assert body["items"][0]["decisionBrief"]["label"]
    assert "# Yieldwise 本地决策备忘录" in body["memo"]
    assert candidate["name"] in body["memo"]


def test_decision_memo_reports_missing_targets_when_some_resolve(client) -> None:
    opportunities = client.get("/api/v2/opportunities").json()["items"]
    candidate = opportunities[0]

    response = client.post(
        "/api/v2/decision-memo",
        json={
            "targets": [
                {"target_id": candidate["id"], "target_type": "community"},
                {"target_id": "missing-target", "target_type": "building"},
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["targetCount"] == 1
    assert body["missingTargets"] == [{"targetId": "missing-target", "targetType": "building"}]
