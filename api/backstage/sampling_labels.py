"""
Browser-sampling label, priority, required-fields and query helpers.

Extracted from api/backstage/review.py to keep that module focused on the
heavier capture-run, review-inbox, sampling-pack and submit/update workflows.
"""

from __future__ import annotations

from api.config.cities.loader import load_active_city


BROWSER_SAMPLING_REQUIRED_FIELDS = {
    "floor_pair_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "朝向",
        "装修",
        "挂牌总价或月租",
        "抓取时间",
    ],
    "building_depth_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "朝向",
        "装修",
        "挂牌总价或月租",
        "抓取时间",
    ],
    "community_profile_capture": [
        "来源平台",
        "页面 URL",
        "小区名",
        "楼栋名",
        "所在楼层 / 总楼层",
        "面积",
        "户型",
        "挂牌总价或月租",
        "抓取时间",
    ],
}


def browser_sampling_task_type_label(task_type: str) -> str:
    return {
        "floor_pair_capture": "楼层补样",
        "building_depth_capture": "楼栋加深",
        "community_profile_capture": "小区补面",
    }.get(task_type, task_type)


def browser_sampling_priority_label(priority_score: float) -> str:
    if priority_score >= 88:
        return "极高优先"
    if priority_score >= 76:
        return "高优先"
    if priority_score >= 62:
        return "中优先"
    return "常规优先"


def browser_sampling_required_fields(task_type: str) -> list[str]:
    return list(BROWSER_SAMPLING_REQUIRED_FIELDS.get(task_type, BROWSER_SAMPLING_REQUIRED_FIELDS["floor_pair_capture"]))


def browser_sampling_query(
    *,
    district_name: str | None,
    community_name: str,
    building_name: str | None = None,
    floor_no: int | None = None,
    business_type: str | None = None,
) -> str:
    parts = [load_active_city().display_name]
    if district_name:
        parts.append(str(district_name))
    parts.append(str(community_name))
    if building_name:
        parts.append(str(building_name))
    if floor_no is not None:
        parts.append(f"{int(floor_no)}层")
    if business_type == "sale":
        parts.append("二手房")
    elif business_type == "rent":
        parts.append("租房")
    elif business_type:
        parts.append(str(business_type))
    return " ".join(part for part in parts if part)
