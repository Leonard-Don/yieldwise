from __future__ import annotations

from typing import Any


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def score(name: str, query: str) -> int:
    n = normalize(name)
    q = normalize(query)
    if not n or not q:
        return 0
    if n == q:
        return 3
    if n.startswith(q):
        return 2
    if q in n:
        return 1
    return 0


def rank_hits(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    if not query or not query.strip():
        return []
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for item in items:
        name = item.get("name", "")
        s = score(name, query)
        if s == 0:
            continue
        scored.append((s, name, item))
    # Higher score first; ties break alphabetically by name.
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [row[2] for row in scored[:limit]]
