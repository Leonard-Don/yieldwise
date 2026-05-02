from __future__ import annotations

import os
from copy import deepcopy
from typing import Any


MOCK_ENV_FLAG = "ATLAS_ENABLE_DEMO_MOCK"
REFERENCE_CATALOG_ENV = "ATLAS_REFERENCE_CATALOG_FILE"

PROVIDER_ALIASES = {
    "shanghai-open-data-community": "shanghai-open-data",
    "authorized-import": "authorized-batch-import",
    "official-export": "authorized-batch-import",
    "authorized-export": "authorized-batch-import",
}

PROVIDER_REGISTRY = [
    {
        "id": "shanghai-open-data",
        "name": "上海开放数据",
        "category": "open_data",
        "priority": "medium",
        "role": "小区字典与地址归一底座",
        "coverage": "行政区 / 小区主档 / 地址字典 / 小区别名导入。",
        "connectionState": "not_connected",
        "supportsLivePull": False,
        "requiredEnv": [],
        "scopes": ["dictionary_batch"],
        "platformUrl": "https://data.sh.gov.cn/view/",
        "applyUrl": "https://data.sh.gov.cn/view/sandbox/index.html",
        "docsUrl": "https://data.sh.gov.cn/assets/data/%E4%B8%8A%E6%B5%B7%E5%B8%82%E5%85%AC%E5%85%B1%E6%95%B0%E6%8D%AE%E5%BC%80%E6%94%BE%E5%B9%B3%E5%8F%B0%E6%93%8D%E4%BD%9C%E6%8C%87%E5%8D%9720210729V2.2.5.pdf",
        "guideUrl": "/docs/import-reference-dictionary.md",
        "applicationMode": "catalog_apply_or_download",
        "recommendedNextStep": "先检索公开数据集；无条件开放直接下载或接口调用，有条件开放点申请，敏感场景走安全沙箱。",
        "contactLabel": "客服邮箱",
        "contactValue": "sjkf@shanghai.gov.cn",
    },
    {
        "id": "amap-aoi-poi",
        "name": "高德 AOI / POI",
        "category": "map_enrichment",
        "priority": "medium",
        "role": "主地图增强与楼栋 / AOI 几何来源",
        "coverage": "行政区边界、AOI、小区与楼栋 footprint 几何批次，以及小区锚点 enrichment。",
        "connectionState": "not_connected",
        "supportsLivePull": False,
        "requiredEnv": ["AMAP_API_KEY"],
        "scopes": ["dictionary_batch", "geometry_batch"],
        "platformUrl": "https://lbs.amap.com/",
        "applyUrl": "https://lbs.amap.com/",
        "docsUrl": "https://a.amap.com/jsapi/static/doc/index.html",
        "guideUrl": "/docs/import-geo-assets.md",
        "applicationMode": "console_key",
        "recommendedNextStep": "先登录高德开放平台，在应用管理创建 JSAPI / Web 服务 Key；AOI / footprint 继续通过几何批次导入。",
        "contactLabel": "控制台动作",
        "contactValue": "登录后进入 应用管理 创建应用与 Key",
    },
    {
        "id": "public-browser-sampling",
        "name": "公开页面辅助采样",
        "category": "staging_only",
        "priority": "medium",
        "role": "公开页面只读采样、字段补洞与浏览器辅助录入",
        "coverage": "公开房源页、小区详情页、地图点位和楼栋 / 楼层文本的人工 capture CSV、手工或半自动 staging 样本。",
        "connectionState": "offline_ready",
        "supportsLivePull": False,
        "requiredEnv": [],
        "scopes": ["sale_rent_batch", "dictionary_batch"],
        "platformUrl": "/docs/internal/import-public-browser-capture.md",
        "docsUrl": "/docs/internal/import-public-browser-capture.md",
        "guideUrl": "/docs/internal/import-public-browser-capture.md",
        "applicationMode": "browser_staging",
        "recommendedNextStep": "先把浏览器人工采样文本整理成 capture CSV，再跑 import_public_browser_capture.py 落成标准 sale_rent_batch / dictionary_batch 产物。",
        "contactLabel": "使用边界",
        "contactValue": "只读公开页面 / 不依赖登录态 / 不做高频自动化",
    },
    {
        "id": "manual-geometry-staging",
        "name": "手工几何 staging",
        "category": "staging_only",
        "priority": "medium",
        "role": "研究阶段楼栋 footprint / anchor 手工勾绘与导入",
        "coverage": "重点区楼栋 footprint、多边形草图、人工校正后的楼栋 geometry 批次。",
        "connectionState": "offline_ready",
        "supportsLivePull": False,
        "requiredEnv": [],
        "scopes": ["geometry_batch"],
        "platformUrl": "/docs/import-geo-assets.md",
        "docsUrl": "/docs/import-geo-assets.md",
        "guideUrl": "/docs/import-geo-assets.md",
        "applicationMode": "manual_sketch",
        "recommendedNextStep": "当官方 AOI / footprint 还没接通时，先把重点区楼栋手工勾绘成 GeoJSON，统一走 geometry_batch 导入。",
        "contactLabel": "使用边界",
        "contactValue": "显式标注为 staging 几何 / 不伪装成官方 AOI",
    },
    {
        "id": "authorized-batch-import",
        "name": "授权离线批次",
        "category": "offline_authorized",
        "priority": "medium",
        "role": "自有 CSV / 已授权样本的离线 staging 通道",
        "coverage": "出售 / 出租 CSV、字典 CSV、GeoJSON footprint 批次与联调 conformance harness。",
        "connectionState": "offline_ready",
        "supportsLivePull": False,
        "requiredEnv": [],
        "scopes": ["sale_rent_batch", "dictionary_batch", "geometry_batch"],
        "platformUrl": "/docs/import-authorized-data.md",
        "docsUrl": "/docs/import-authorized-data.md",
        "guideUrl": "/docs/import-authorized-data.md",
        "applicationMode": "internal_staging",
        "recommendedNextStep": "拿到官方导出 CSV / GeoJSON 后先走离线 staging，再写入 PostgreSQL 作为主读数据。",
        "contactLabel": "内部链路",
        "contactValue": "jobs/import_* + PostgreSQL",
    },
]

ADAPTER_CONTRACTS = {
    "sale_rent_batch": {
        "scope": "sale_rent_batch",
        "description": "出售 / 出租 listing 批次导入。用于授权 CSV、平台导出文件和后续官方 API 拉平后的离线落地。",
        "requiredOutputs": [
            "manifest",
            "normalized_sale",
            "normalized_rent",
            "address_resolution_queue",
            "floor_pairs",
            "floor_evidence",
            "review_history",
            "summary",
        ],
        "recordKinds": ["sale_listing", "rent_listing", "address_resolution", "floor_pair", "floor_snapshot"],
    },
    "dictionary_batch": {
        "scope": "dictionary_batch",
        "description": "行政区 / 小区 / 楼栋主档与别名字典导入。",
        "requiredOutputs": [
            "manifest",
            "district_dictionary",
            "community_dictionary",
            "building_dictionary",
            "reference_catalog",
            "summary",
        ],
        "recordKinds": ["district", "community", "community_alias", "community_anchor", "building", "building_alias"],
    },
    "geometry_batch": {
        "scope": "geometry_batch",
        "description": "AOI / building footprint / geometry version 批次导入。",
        "requiredOutputs": [
            "manifest",
            "building_footprints",
            "coverage_tasks",
            "review_history",
            "work_orders",
            "work_order_events",
            "summary",
        ],
        "recordKinds": ["geo_asset", "geo_capture_task", "geo_review_event", "geo_work_order"],
    },
}


def truthy_env(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def mock_enabled() -> bool:
    return truthy_env(MOCK_ENV_FLAG)


def normalize_provider_id(provider_id: str | None) -> str | None:
    if not provider_id:
        return None
    provider_id = provider_id.strip()
    return PROVIDER_ALIASES.get(provider_id, provider_id)


def provider_definition(provider_id: str | None) -> dict[str, Any] | None:
    normalized = normalize_provider_id(provider_id)
    if not normalized:
        return None
    return next((deepcopy(item) for item in PROVIDER_REGISTRY if item["id"] == normalized), None)


def validate_provider_scope(provider_id: str | None, scope: str) -> dict[str, Any]:
    provider = provider_definition(provider_id)
    if not provider:
        raise ValueError(f"未知 provider_id: {provider_id}")
    if scope not in provider.get("scopes", []):
        raise ValueError(f"{provider['id']} 不支持 {scope} 批次。")
    return provider


def adapter_contract(scope: str) -> dict[str, Any]:
    contract = ADAPTER_CONTRACTS.get(scope)
    if not contract:
        raise ValueError(f"未知 adapter scope: {scope}")
    return deepcopy(contract)


def provider_readiness_snapshot(
    *,
    staged_listing_runs: int = 0,
    staged_geometry_runs: int = 0,
    has_real_data: bool = False,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in PROVIDER_REGISTRY:
        readiness = deepcopy(item)
        credential_sets = list(readiness.get("credentialSets", []))
        matched_credential_set_label: str | None = None
        required_env = list(readiness.get("requiredEnv", []))
        configured_env: list[str] = []
        missing_env: list[str] = []
        env_ready = False

        if credential_sets:
            best_score = (-1, -1)
            for credential_set in credential_sets:
                env_names = list(credential_set.get("env", []))
                configured = [name for name in env_names if os.getenv(name, "").strip()]
                missing = [name for name in env_names if name not in configured]
                score = (len(configured), -len(missing))
                if score > best_score:
                    best_score = score
                    matched_credential_set_label = credential_set.get("label")
                    configured_env = configured
                    missing_env = missing
                    required_env = env_names
                    env_ready = bool(env_names) and not missing
        else:
            configured_env = [name for name in required_env if os.getenv(name, "").strip()]
            missing_env = [name for name in required_env if name not in configured_env]
            env_ready = bool(required_env) and not missing_env
        connection_state = readiness.get("connectionState", "not_connected")
        note = "等待本地数据文件、公开数据下载或手工批次。"
        if readiness["id"] == "authorized-batch-import":
            note = "离线导入通道已可用，用于 staging 和 conformance harness。"
        elif readiness["id"] == "public-browser-sampling":
            note = "公开页面辅助采样通道已可用，只做只读补洞与小批量 staging。"
        elif readiness["id"] == "manual-geometry-staging":
            note = "手工几何 staging 通道已可用，适合重点区楼栋 footprint 人工勾绘与研究校正。"
        elif env_ready:
            connection_state = "credentials_ready"
            note = "凭证位已配置，可用于本地数据辅助任务。"
        elif configured_env:
            connection_state = "credentials_partial"
            note = f"已配置部分凭证：{', '.join(configured_env)}；仍缺少 {', '.join(missing_env)}。"
        if readiness["id"] == "amap-aoi-poi" and os.getenv("AMAP_API_KEY", "").strip():
            connection_state = "credentials_ready"
            note = (
                "地图 key 与安全密钥已配置，可直接接 JSAPI，几何导入仍走离线批次。"
                if os.getenv("AMAP_SECURITY_JSCODE", "").strip()
                else "地图 key 已配置，可直接接 JSAPI；如控制台启用了安全密钥，请补 AMAP_SECURITY_JSCODE。"
            )

        staged_count = 0
        if "sale_rent_batch" in readiness.get("scopes", []) or "dictionary_batch" in readiness.get("scopes", []):
            staged_count += staged_listing_runs if readiness["id"] == "authorized-batch-import" else 0
        if "geometry_batch" in readiness.get("scopes", []):
            staged_count += staged_geometry_runs if readiness["id"] in {"authorized-batch-import", "amap-aoi-poi", "manual-geometry-staging"} else 0

        readiness["connectionState"] = connection_state
        readiness["readinessLabel"] = {
            "offline_ready": "离线可接入",
            "credentials_ready": "凭证位已就绪",
            "credentials_partial": "部分凭证已就绪",
            "connected_live": "在线接通",
            "not_connected": "待接入",
        }.get(connection_state, "待接入")
        readiness["hasCredentials"] = env_ready
        readiness["configuredRequiredEnv"] = configured_env
        readiness["missingRequiredEnv"] = missing_env
        readiness["matchedCredentialSetLabel"] = matched_credential_set_label
        readiness["stagedRunCount"] = staged_count
        readiness["isPrimaryCandidate"] = readiness["priority"] == "high"
        readiness["activeDataRole"] = (
            "active_database"
            if has_real_data
            and readiness["id"]
            in {"shanghai-open-data", "amap-aoi-poi", "authorized-batch-import", "public-browser-sampling", "manual-geometry-staging"}
            else "staging"
            if staged_count
            else "planned"
        )
        readiness["note"] = note
        items.append(readiness)
    return items
