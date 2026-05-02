from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

SALE_BUG_WAN = 323.0
SALE_BUG_UNIT = 36292.13
RENT_BUG_THRESHOLD = 1000.0

QUALITY_LABELS = {
    "strong": "高可信",
    "usable": "可用",
    "thin": "样本薄",
    "blocked": "待补样",
}

GATE_LABELS = {
    "ok": "通过",
    "warn": "需关注",
    "blocker": "阻断",
}


def attach_quality_to_communities(communities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach shared quality summaries to community and building records."""
    for community in communities:
        community_quality = quality_summary(community, target_type="community")
        community["quality"] = community_quality
        community["qualityStatus"] = community_quality["status"]
        community["qualityLabel"] = community_quality["label"]
        community["qualityScore"] = community_quality["score"]
        for building in community.get("buildings") or []:
            building_quality = quality_summary(building, target_type="building", community=community)
            building["quality"] = building_quality
            building["qualityStatus"] = building_quality["status"]
            building["qualityLabel"] = building_quality["label"]
            building["qualityScore"] = building_quality["score"]
    return communities


def quality_summary(
    item: dict[str, Any],
    *,
    target_type: str = "community",
    community: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sale_sample = _optional_int(item.get("saleSample"))
    rent_sample = _optional_int(item.get("rentSample"))
    sample_size = _optional_int(item.get("sampleSize") or item.get("sample") or item.get("sampleSizeEstimate")) or 0
    sample_status = str(
        item.get("sampleStatus")
        or ((community or {}).get("sampleStatus"))
        or ""
    )
    yield_pct = _optional_float(item.get("yieldAvg") if target_type == "building" else item.get("yield"))
    if yield_pct is None:
        yield_pct = _optional_float(item.get("yield"))
    if yield_pct is None and community:
        yield_pct = _optional_float(community.get("yield"))
    anchor_quality = _optional_float(item.get("anchorQuality"))
    if anchor_quality is None and community:
        anchor_quality = _optional_float(community.get("anchorQuality"))
    freshness = item.get("dataFreshness") or (community or {}).get("dataFreshness")

    checks: list[dict[str, str]] = []
    score = 48
    reasons: list[str] = []

    if sale_sample is not None or rent_sample is not None:
        sale = sale_sample or 0
        rent = rent_sample or 0
        balanced = min(sale, rent)
        sample_size = max(sample_size, sale, rent)
        if sale == 0 or rent == 0:
            checks.append(_quality_check("sample_balance", "租售样本", "blocker", f"售 {sale} / 租 {rent}"))
            score -= 22
            reasons.append("租售一侧缺样")
        elif balanced < 3:
            checks.append(_quality_check("sample_balance", "租售样本", "warn", f"售 {sale} / 租 {rent}"))
            score += 6
            reasons.append("租售样本偏薄")
        else:
            checks.append(_quality_check("sample_balance", "租售样本", "ok", f"售 {sale} / 租 {rent}"))
            score += 24 if balanced >= 5 else 16
    else:
        if sample_size <= 0 or sample_status == "dictionary_only":
            checks.append(_quality_check("sample_size", "样本量", "blocker", f"样本 {sample_size}"))
            score -= 20
            reasons.append("当前仅有主档")
        elif sample_size < 3:
            checks.append(_quality_check("sample_size", "样本量", "warn", f"样本 {sample_size}"))
            score += 6
            reasons.append("样本量不足")
        else:
            checks.append(_quality_check("sample_size", "样本量", "ok", f"样本 {sample_size}"))
            score += 18 if sample_size >= 6 else 12

    if yield_pct is None or yield_pct <= 0:
        checks.append(_quality_check("yield_signal", "收益信号", "blocker", "缺少有效租售比"))
        score -= 24
        reasons.append("收益信号缺失")
    elif yield_pct < 1.5 or yield_pct > 8.0:
        checks.append(_quality_check("yield_signal", "收益信号", "warn", f"{yield_pct:.2f}%"))
        score += 5
        reasons.append("租售比异常")
    else:
        checks.append(_quality_check("yield_signal", "收益信号", "ok", f"{yield_pct:.2f}%"))
        score += 16

    if anchor_quality is None:
        checks.append(_quality_check("anchor_quality", "挂图可信度", "info", "未记录"))
    elif anchor_quality < 0.55:
        checks.append(_quality_check("anchor_quality", "挂图可信度", "warn", f"{anchor_quality:.2f}"))
        score -= 6
        reasons.append("挂图置信偏低")
    elif anchor_quality < 0.8:
        checks.append(_quality_check("anchor_quality", "挂图可信度", "warn", f"{anchor_quality:.2f}"))
        score += 4
    else:
        checks.append(_quality_check("anchor_quality", "挂图可信度", "ok", f"{anchor_quality:.2f}"))
        score += 8

    if freshness:
        checks.append(_quality_check("freshness", "样本时间", "ok", _freshness_label(freshness)))
        score += 4
    else:
        checks.append(_quality_check("freshness", "样本时间", "info", "未记录"))

    score = int(max(0, min(100, round(score))))
    blocker_count = sum(1 for item_check in checks if item_check["status"] == "blocker")
    warn_count = sum(1 for item_check in checks if item_check["status"] == "warn")
    if blocker_count:
        status = "blocked"
    elif score >= 84 and warn_count == 0:
        status = "strong"
    elif score >= 66:
        status = "usable"
    else:
        status = "thin"

    if not reasons:
        reasons.append("租售样本、收益信号和挂图状态一致")

    return {
        "status": status,
        "label": QUALITY_LABELS[status],
        "score": score,
        "summary": _quality_summary_sentence(status, sample_size, yield_pct),
        "sampleLabel": _sample_label(sale_sample, rent_sample, sample_size),
        "badges": _badges_for(status, sample_size, yield_pct),
        "reasons": reasons[:3],
        "checks": checks,
    }


def build_data_quality_gate(
    *,
    communities: list[dict[str, Any]],
    import_runs: list[dict[str, Any]] | None = None,
    latest_only: bool = False,
) -> dict[str, Any]:
    community_items = []
    counts = {"strong": 0, "usable": 0, "thin": 0, "blocked": 0}
    total_score = 0
    for community in communities:
        quality = deepcopy(community.get("quality") or quality_summary(community, target_type="community"))
        status = str(quality.get("status") or "thin")
        if status not in counts:
            status = "thin"
        counts[status] += 1
        total_score += int(quality.get("score") or 0)
        if status in {"thin", "blocked"}:
            community_items.append(
                {
                    "communityId": community.get("id"),
                    "name": community.get("name"),
                    "districtName": community.get("districtName"),
                    "status": status,
                    "label": quality.get("label"),
                    "score": quality.get("score"),
                    "sampleLabel": quality.get("sampleLabel"),
                    "reason": (quality.get("reasons") or ["待补样本"])[0],
                }
            )
    community_count = len(communities)
    avg_score = int(round(total_score / community_count)) if community_count else 0
    dirty = dirty_listing_summary_for_import_runs(import_runs or [], latest_only=latest_only)
    status = "ok"
    if dirty["totalIssueCount"] > 0 or counts["blocked"] > 0:
        status = "blocker"
    elif counts["thin"] > 0 or community_count == 0:
        status = "warn"

    checks = [
        _gate_check(
            "dirty_listing_rows",
            "脏挂牌值",
            "blocker" if dirty["totalIssueCount"] else "ok",
            f"租金污染 {dirty['rentIssueCount']} / 售价默认值 {dirty['saleIssueCount']}",
        ),
        _gate_check(
            "community_quality",
            "小区质量",
            "blocker" if counts["blocked"] else "warn" if counts["thin"] else "ok",
            f"高可信 {counts['strong']} / 可用 {counts['usable']} / 薄样本 {counts['thin']} / 待补样 {counts['blocked']}",
        ),
        _gate_check(
            "quality_score",
            "平均分",
            "ok" if avg_score >= 66 else "warn",
            f"{avg_score}/100",
        ),
    ]

    community_items.sort(key=lambda item: (item["status"] != "blocked", item.get("score") or 0, item.get("name") or ""))
    return {
        "status": status,
        "label": GATE_LABELS[status],
        "score": avg_score,
        "communityCount": community_count,
        "statusCounts": counts,
        "dirtyListings": dirty,
        "checks": checks,
        "items": community_items[:8],
    }


def dirty_listing_summary_for_import_runs(
    import_runs: list[dict[str, Any]],
    *,
    latest_only: bool = False,
) -> dict[str, Any]:
    selected_runs = import_runs[:1] if latest_only else import_runs
    rent_issue_count = 0
    sale_issue_count = 0
    affected_runs: list[dict[str, Any]] = []
    for run in selected_runs:
        output_dir = Path(str(run.get("outputDir") or "")).expanduser()
        if not output_dir.exists():
            continue
        rent_count = _count_dirty_rent(output_dir / "normalized_rent.json")
        sale_count = _count_dirty_sale(output_dir / "normalized_sale.json")
        if rent_count or sale_count:
            affected_runs.append(
                {
                    "runId": run.get("runId"),
                    "batchName": run.get("batchName"),
                    "createdAt": run.get("createdAt"),
                    "rentIssueCount": rent_count,
                    "saleIssueCount": sale_count,
                }
            )
        rent_issue_count += rent_count
        sale_issue_count += sale_count
    return {
        "latestOnly": latest_only,
        "runCount": len(selected_runs),
        "rentIssueCount": rent_issue_count,
        "saleIssueCount": sale_issue_count,
        "totalIssueCount": rent_issue_count + sale_issue_count,
        "affectedRuns": affected_runs[:10],
    }


def _count_dirty_rent(path: Path) -> int:
    rows = _read_rows(path)
    count = 0
    for row in rows:
        rent = _optional_float(row.get("monthly_rent"))
        if rent is not None and 0 < rent < RENT_BUG_THRESHOLD:
            count += 1
    return count


def _count_dirty_sale(path: Path) -> int:
    rows = _read_rows(path)
    count = 0
    for row in rows:
        wan = _optional_float(row.get("price_total_wan"))
        unit = _optional_float(row.get("unit_price_yuan"))
        if wan is None or unit is None:
            continue
        if abs(wan - SALE_BUG_WAN) <= 0.01 and abs(unit - SALE_BUG_UNIT) <= 0.01:
            count += 1
    return count


def _read_rows(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(payload, list):
        return []
    return [row for row in payload if isinstance(row, dict)]


def _quality_check(check_id: str, label: str, status: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "label": label, "status": status, "detail": detail}


def _gate_check(check_id: str, label: str, status: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "label": label, "status": status, "detail": detail}


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _sample_label(sale_sample: int | None, rent_sample: int | None, sample_size: int) -> str:
    if sale_sample is not None or rent_sample is not None:
        return f"售 {sale_sample or 0} / 租 {rent_sample or 0}"
    return f"样本 {sample_size}"


def _badges_for(status: str, sample_size: int, yield_pct: float | None) -> list[str]:
    badges = [QUALITY_LABELS[status], f"样本 {sample_size}"]
    if yield_pct is not None and yield_pct > 0:
        badges.append(f"{yield_pct:.2f}%")
    return badges


def _quality_summary_sentence(status: str, sample_size: int, yield_pct: float | None) -> str:
    yield_label = f"{yield_pct:.2f}%" if yield_pct is not None and yield_pct > 0 else "缺收益信号"
    return f"{QUALITY_LABELS[status]} · 样本 {sample_size} · {yield_label}"


def _freshness_label(value: Any) -> str:
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text[:10]
    return parsed.date().isoformat()
