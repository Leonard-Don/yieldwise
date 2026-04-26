from __future__ import annotations

from api.domains.search_scoring import rank_hits, score


def test_score_no_match_returns_zero() -> None:
    assert score("浦东新区", "宝山") == 0


def test_score_contains_returns_one() -> None:
    assert score("中海建国里", "建国") == 1


def test_score_starts_with_returns_two() -> None:
    assert score("浦东新区", "浦东") == 2


def test_score_exact_match_returns_three() -> None:
    assert score("浦东新区", "浦东新区") == 3


def test_score_is_case_insensitive_for_ascii() -> None:
    assert score("Daning Park", "daning") == 2
    assert score("Daning Park", "PARK") == 1


def test_rank_hits_orders_by_score_then_name() -> None:
    items = [
        {"name": "浦东新区", "kind": "x"},
        {"name": "浦江华侨城", "kind": "y"},
        {"name": "新华联", "kind": "z"},
        {"name": "宝山", "kind": "w"},
    ]
    ranked = rank_hits(items, "浦", limit=10)
    # 浦东新区 starts-with → score 2; 浦江华侨城 starts-with → score 2;
    # 新华联 contains → score 0 (no '浦'); wait — "新华联" doesn't contain
    # 浦, so score is 0 and it should be dropped. 宝山 also score 0, dropped.
    names = [hit["name"] for hit in ranked]
    assert names == ["浦东新区", "浦江华侨城"]


def test_rank_hits_truncates_to_limit() -> None:
    items = [{"name": f"匹配{i}"} for i in range(10)]
    ranked = rank_hits(items, "匹配", limit=3)
    assert len(ranked) == 3


def test_rank_hits_drops_zero_score_items() -> None:
    items = [
        {"name": "完全匹配", "kind": "a"},
        {"name": "无关词", "kind": "b"},
    ]
    ranked = rank_hits(items, "完全", limit=10)
    assert [hit["name"] for hit in ranked] == ["完全匹配"]


def test_rank_hits_empty_query_returns_empty() -> None:
    items = [{"name": "anything"}]
    assert rank_hits(items, "", limit=10) == []
    assert rank_hits(items, "   ", limit=10) == []
