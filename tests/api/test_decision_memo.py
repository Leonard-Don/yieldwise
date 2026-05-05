from __future__ import annotations

from api.service import current_community_dataset


def _first_decision_target() -> dict:
    items = current_community_dataset()
    assert items
    return items[0]


def test_decision_memo_requires_targets(client) -> None:
    response = client.post("/api/v2/decision-memo", json={"targets": []})
    assert response.status_code == 400


def test_decision_memo_returns_markdown_for_opportunity(client) -> None:
    candidate = _first_decision_target()

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
    candidate = _first_decision_target()

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


def test_decision_memo_uses_candidate_context_for_committee_sections(client) -> None:
    candidate = _first_decision_target()

    response = client.post(
        "/api/v2/decision-memo",
        json={
            "targets": [
                {
                    "target_id": candidate["id"],
                    "target_type": "community",
                }
            ],
            "candidate_contexts": [
                {
                    "target_id": candidate["id"],
                    "target_type": "community",
                    "status": "shortlisted",
                    "priority": 1,
                    "thesis": "租售比稳定且预算内",
                    "notes": "约看前先复核同小区租金",
                    "target_price_wan": 800,
                    "target_monthly_rent": 18000,
                    "target_yield_pct": 4.2,
                    "review_due_at": "2026-05-10",
                    "task_labels": ["到期复核"],
                    "trigger_labels": ["总价低于目标"],
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    memo = response.json()["memo"]
    assert "投资假设：租售比稳定且预算内" in memo
    assert "买入理由：" in memo
    assert "总价低于目标" in memo
    assert "待核验项：到期复核" in memo
    assert "下一步：约看前先复核同小区租金" in memo
