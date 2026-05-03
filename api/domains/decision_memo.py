from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException

from ..schemas.decision_memo import DecisionMemoRequest, DecisionMemoTarget
from ..service import compute_payback_years, current_community_dataset

router = APIRouter(tags=["decision-memo"])


@router.post("/decision-memo")
def create_decision_memo(payload: DecisionMemoRequest) -> dict[str, Any]:
    if not payload.targets:
        raise HTTPException(status_code=400, detail="targets cannot be empty")

    communities = current_community_dataset()
    resolved, missing = resolve_decision_targets(payload.targets, communities)
    if not resolved:
        raise HTTPException(status_code=404, detail="No decision memo targets found")

    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "generatedAt": generated_at,
        "targetCount": len(resolved),
        "missingTargets": missing,
        "items": resolved,
        "memo": build_decision_memo_markdown(resolved, generated_at=generated_at),
    }


def resolve_decision_targets(
    targets: list[DecisionMemoTarget],
    communities: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    community_index = {str(item.get("id")): item for item in communities if item.get("id")}
    building_index: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    district_ids = {str(item.get("districtId")) for item in communities if item.get("districtId")}
    for community in communities:
        for building in community.get("buildings") or []:
            if building.get("id"):
                building_index[str(building["id"])] = (building, community)

    resolved: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for target in targets:
        key = (target.target_type, target.target_id)
        if key in seen:
            continue
        seen.add(key)
        item = None
        if target.target_type == "community":
            community = community_index.get(target.target_id)
            item = memo_item_from_record(community, target_type="community") if community else None
        elif target.target_type == "building":
            pair = building_index.get(target.target_id)
            item = memo_item_from_record(pair[0], target_type="building", community=pair[1]) if pair else None
        elif target.target_type == "district" and target.target_id in district_ids:
            item = memo_item_from_district(target.target_id, communities)

        if item:
            resolved.append(item)
        else:
            missing.append({"targetId": target.target_id, "targetType": target.target_type})
    return resolved, missing


def memo_item_from_record(
    record: dict[str, Any] | None,
    *,
    target_type: str,
    community: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not record:
        return None
    quality = record.get("quality") if isinstance(record.get("quality"), dict) else {}
    brief = record.get("decisionBrief") if isinstance(record.get("decisionBrief"), dict) else {}
    yield_pct = record.get("yieldAvg") if target_type == "building" else record.get("yield")
    sale_median_wan = record.get("saleMedianWan") if target_type == "building" else record.get("avgPriceWan")
    rent_median_monthly = record.get("rentMedianMonthly") if target_type == "building" else record.get("monthlyRent")
    payback_years = record.get("paybackYears") or compute_payback_years(sale_median_wan, rent_median_monthly)
    return {
        "targetId": record.get("id"),
        "targetType": target_type,
        "name": record.get("name") or record.get("communityName") or record.get("id"),
        "districtName": record.get("districtName") or (community or {}).get("districtName"),
        "communityName": record.get("communityName") or (record.get("name") if target_type == "community" else None),
        "yieldPct": yield_pct,
        "paybackYears": payback_years,
        "score": record.get("score"),
        "sampleLabel": quality.get("sampleLabel") or _sample_label_from_record(record),
        "saleMedianWan": sale_median_wan,
        "rentMedianMonthly": rent_median_monthly,
        "quality": quality,
        "decisionBrief": brief,
        "primaryBuildingId": record.get("primaryBuildingId"),
        "buildingFocus": record.get("buildingFocus"),
        "nextSteps": brief.get("nextAction") or "继续补齐样本并复核质量状态。",
        "risks": list(brief.get("risks") or []),
    }


def memo_item_from_district(district_id: str, communities: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = [item for item in communities if str(item.get("districtId")) == district_id]
    if not rows:
        return None
    sale_sample = sum(int(item.get("saleSample") or 0) for item in rows)
    rent_sample = sum(int(item.get("rentSample") or 0) for item in rows)
    avg_budget = sum(float(item.get("avgPriceWan") or 0) for item in rows) / max(len(rows), 1)
    avg_rent = sum(float(item.get("monthlyRent") or 0) for item in rows) / max(len(rows), 1)
    avg_yield = sum(float(item.get("yield") or 0) for item in rows) / max(len(rows), 1)
    avg_quality = sum(int((item.get("quality") or {}).get("score") or 0) for item in rows) / max(len(rows), 1)
    blocked = sum(1 for item in rows if (item.get("quality") or {}).get("status") == "blocked")
    thin = sum(1 for item in rows if (item.get("quality") or {}).get("status") == "thin")
    label = "可用" if blocked == 0 and thin == 0 else "需补样"
    stance = "watch" if label == "可用" else "sample_first"
    return {
        "targetId": district_id,
        "targetType": "district",
        "name": rows[0].get("districtName") or district_id,
        "districtName": rows[0].get("districtName") or district_id,
        "communityName": None,
        "yieldPct": round(avg_yield, 2),
        "paybackYears": compute_payback_years(avg_budget, avg_rent),
        "score": max(int(item.get("score") or 0) for item in rows),
        "sampleLabel": f"售 {sale_sample} / 租 {rent_sample}",
        "saleMedianWan": round(avg_budget, 1),
        "rentMedianMonthly": round(avg_rent),
        "quality": {
            "status": "usable" if label == "可用" else "thin",
            "label": label,
            "score": round(avg_quality),
            "summary": f"{len(rows)} 个小区 · 薄样本 {thin} / 待补样 {blocked}",
            "sampleLabel": f"售 {sale_sample} / 租 {rent_sample}",
        },
        "decisionBrief": {
            "stance": stance,
            "label": "继续观察" if stance == "watch" else "先补样",
            "summary": "区级视角适合做范围筛选，最终仍需回到小区和楼栋验证。",
            "nextAction": "挑选区内前 3 个小区进入候选对比。",
            "factors": [f"{len(rows)} 个小区", f"区均租售比 {avg_yield:.2f}%", f"售 {sale_sample} / 租 {rent_sample}"],
            "risks": ["区级均值会掩盖楼栋和楼层差异"],
        },
        "primaryBuildingId": None,
        "buildingFocus": None,
        "nextSteps": "挑选区内前 3 个小区进入候选对比。",
        "risks": ["区级均值会掩盖楼栋和楼层差异"],
    }


def build_decision_memo_markdown(items: list[dict[str, Any]], *, generated_at: str) -> str:
    ordered = sorted(items, key=lambda item: (int(item.get("score") or 0), float(item.get("yieldPct") or 0)), reverse=True)
    top = ordered[0] if ordered else None
    lines = [
        "# Yieldwise 本地决策备忘录",
        "",
        f"- 生成时间：{generated_at}",
        f"- 候选数量：{len(items)}",
        f"- 优先关注：{top['name'] if top else '—'}",
        "",
        "## 候选对比",
        "",
        "| 候选 | 区域 | 类型 | 租售比 | 回本 | 机会分 | 质量 | 样本 |",
        "|---|---|---|---:|---:|---:|---|---|",
    ]
    for item in ordered:
        quality = item.get("quality") or {}
        lines.append(
            "| {name} | {district} | {target_type} | {yield_pct} | {payback} | {score} | {quality} | {sample} |".format(
                name=_md(item.get("name")),
                district=_md(item.get("districtName") or "—"),
                target_type=_target_type_label(str(item.get("targetType") or "")),
                yield_pct=_fmt_pct(item.get("yieldPct")),
                payback=_fmt_years(item.get("paybackYears")),
                score=_fmt_int(item.get("score")),
                quality=_md(str(quality.get("label") or "—")),
                sample=_md(str(item.get("sampleLabel") or "—")),
            )
        )
    lines.extend(["", "## 单项记录", ""])
    for index, item in enumerate(ordered, start=1):
        brief = item.get("decisionBrief") or {}
        lines.extend(
            [
                f"### {index}. {item.get('name') or item.get('targetId')}",
                "",
                f"- 决策：{brief.get('label') or '继续观察'}",
                f"- 摘要：{brief.get('summary') or '暂无摘要'}",
                f"- 依据：{'；'.join(brief.get('factors') or []) or '—'}",
                f"- 风险：{'；'.join(item.get('risks') or brief.get('risks') or []) or '—'}",
                f"- 下一步：{item.get('nextSteps') or brief.get('nextAction') or '继续观察'}",
                "",
            ]
        )
    lines.extend(["---", "仅供本地研究使用。"])
    return "\n".join(lines)


def _sample_label_from_record(record: dict[str, Any]) -> str:
    sale = record.get("saleSample")
    rent = record.get("rentSample")
    if sale is not None or rent is not None:
        return f"售 {sale or 0} / 租 {rent or 0}"
    return f"样本 {record.get('sampleSize') or record.get('sample') or 0}"


def _fmt_pct(value: Any) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_years(value: Any) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "—"
    return f"{num:.1f} 年" if num > 0 else "—"


def _fmt_int(value: Any) -> str:
    try:
        return str(round(float(value)))
    except (TypeError, ValueError):
        return "—"


def _target_type_label(value: str) -> str:
    return {"building": "楼栋", "community": "小区", "district": "区"}.get(value, value or "—")


def _md(value: Any) -> str:
    return str(value or "—").replace("|", "\\|").replace("\n", " ")
