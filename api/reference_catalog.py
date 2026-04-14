from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .provider_adapters import REFERENCE_CATALOG_ENV, mock_enabled


ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class DistrictReference:
    district_id: str
    district_name: str
    short_name: str


@dataclass(frozen=True)
class CommunityReference:
    district_id: str
    district_name: str
    district_short_name: str
    community_id: str
    community_name: str
    aliases: tuple[str, ...] = ()
    source_confidence: float | None = None
    center_lng: float | None = None
    center_lat: float | None = None
    anchor_source: str | None = None
    anchor_quality: float | None = None
    source_refs: tuple[str, ...] = ()
    candidate_suggestions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class BuildingReference:
    district_id: str
    district_name: str
    district_short_name: str
    community_id: str
    community_name: str
    building_id: str
    building_name: str
    total_floors: int | None
    community_aliases: tuple[str, ...] = ()
    building_aliases: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    center_lng: float | None = None
    center_lat: float | None = None
    anchor_source: str | None = None
    anchor_quality: float | None = None


def _catalog_file_path() -> Path | None:
    value = os.getenv(REFERENCE_CATALOG_ENV, "").strip()
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else ROOT_DIR / path


def _latest_reference_catalog_path() -> Path | None:
    reference_root = ROOT_DIR / "tmp" / "reference-runs"
    if not reference_root.exists():
        return None
    candidates = sorted(reference_root.rglob("reference_catalog.json"), reverse=True)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _coerce_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _dedupe_strings(values: list[Any]) -> tuple[str, ...]:
    items: list[str] = []
    for value in values:
        if value in (None, ""):
            continue
        text = str(value).strip()
        if text and text not in items:
            items.append(text)
    return tuple(items)


def _normalize_candidate_suggestions(values: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(values, list):
        return ()
    suggestions: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, dict):
            continue
        query = str(value.get("query") or "").strip()
        name = str(value.get("name") or "").strip()
        address = str(value.get("address") or "").strip()
        score = _coerce_float(value.get("score"))
        match_source = str(value.get("match_source") or "").strip()
        payload = {
            "query": query or None,
            "name": name or None,
            "address": address or None,
            "score": score,
            "matchSource": match_source or None,
        }
        if any(payload.values()):
            suggestions.append(payload)
    return tuple(suggestions)


def _catalog_from_payload(payload: dict[str, Any], *, source: str) -> dict[str, Any] | None:
    district_rows = payload.get("districts") if isinstance(payload.get("districts"), list) else []
    community_rows = payload.get("communities") if isinstance(payload.get("communities"), list) else []
    building_rows = payload.get("buildings") if isinstance(payload.get("buildings"), list) else []

    districts: list[DistrictReference] = []
    for row in district_rows:
        if not isinstance(row, dict) or not row.get("district_id") or not row.get("district_name"):
            continue
        districts.append(
            DistrictReference(
                district_id=str(row["district_id"]),
                district_name=str(row["district_name"]),
                short_name=str(row.get("short_name") or row.get("district_name")),
            )
        )

    district_index = {item.district_id: item for item in districts}
    communities: list[CommunityReference] = []
    for row in community_rows:
        if not isinstance(row, dict) or not row.get("community_id") or not row.get("community_name") or not row.get("district_id"):
            continue
        district_ref = district_index.get(str(row["district_id"]))
        district_name = str(row.get("district_name") or (district_ref.district_name if district_ref else row["district_id"]))
        short_name = str(row.get("district_short_name") or (district_ref.short_name if district_ref else district_name))
        aliases = _dedupe_strings(
            [
                row.get("community_name"),
                *(row.get("aliases") or row.get("community_aliases") or []),
            ]
        )
        communities.append(
            CommunityReference(
                district_id=str(row["district_id"]),
                district_name=district_name,
                district_short_name=short_name,
                community_id=str(row["community_id"]),
                community_name=str(row["community_name"]),
                aliases=aliases,
                source_confidence=_coerce_float(row.get("source_confidence")),
                center_lng=_coerce_float(row.get("center_lng")),
                center_lat=_coerce_float(row.get("center_lat")),
                anchor_source=str(row.get("anchor_source")) if row.get("anchor_source") else None,
                anchor_quality=_coerce_float(row.get("anchor_quality")),
                source_refs=_dedupe_strings(row.get("source_refs") or []),
                candidate_suggestions=_normalize_candidate_suggestions(row.get("candidate_suggestions")),
            )
        )

    community_index = {item.community_id: item for item in communities}
    buildings: list[BuildingReference] = []
    for row in building_rows:
        if not isinstance(row, dict) or not row.get("building_id") or not row.get("building_name") or not row.get("community_id"):
            continue
        community_ref = community_index.get(str(row["community_id"]))
        district_id = str(row.get("district_id") or (community_ref.district_id if community_ref else ""))
        district_name = str(row.get("district_name") or (community_ref.district_name if community_ref else district_id))
        district_short_name = str(
            row.get("district_short_name") or (community_ref.district_short_name if community_ref else district_name)
        )
        community_name = str(row.get("community_name") or (community_ref.community_name if community_ref else row["community_id"]))
        community_aliases = _dedupe_strings(
            [
                community_name,
                *(row.get("community_aliases") or []),
                *(community_ref.aliases if community_ref else ()),
            ]
        )
        building_aliases = _dedupe_strings([row.get("building_name"), *(row.get("aliases") or row.get("building_aliases") or [])])
        buildings.append(
            BuildingReference(
                district_id=district_id,
                district_name=district_name,
                district_short_name=district_short_name,
                community_id=str(row["community_id"]),
                community_name=community_name,
                building_id=str(row["building_id"]),
                building_name=str(row["building_name"]),
                total_floors=_coerce_int(row.get("total_floors")),
                community_aliases=community_aliases,
                building_aliases=building_aliases,
                source_refs=_dedupe_strings([row.get("source_ref"), *(row.get("source_refs") or [])]),
                center_lng=_coerce_float(row.get("center_lng")),
                center_lat=_coerce_float(row.get("center_lat")),
                anchor_source=str(row.get("anchor_source")) if row.get("anchor_source") else None,
                anchor_quality=_coerce_float(row.get("anchor_quality")),
            )
        )

    if not districts and not communities and not buildings:
        return None
    return {
        "source": source,
        "district_refs": districts,
        "community_refs": communities,
        "building_refs": buildings,
    }


def _load_from_catalog_file() -> dict[str, Any] | None:
    path = _catalog_file_path() or _latest_reference_catalog_path()
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return _catalog_from_payload(payload, source=f"catalog_file:{path}")


def _load_from_database() -> dict[str, Any] | None:
    try:
        from .persistence import query_rows
    except Exception:
        return None

    try:
        district_rows = query_rows(
            """
            SELECT district_id, district_name, short_name
            FROM districts
            ORDER BY district_id
            """
        )
        community_rows = query_rows(
            """
            SELECT
                c.community_id,
                c.district_id,
                d.district_name,
                d.short_name AS district_short_name,
                c.name AS community_name,
                COALESCE(c.aliases_json, '[]'::jsonb) AS aliases,
                c.source_confidence,
                COALESCE(ST_X(c.centroid_gcj02), ST_X(c.centroid_wgs84)) AS center_lng,
                COALESCE(ST_Y(c.centroid_gcj02), ST_Y(c.centroid_wgs84)) AS center_lat,
                COALESCE(
                    c.anchor_source,
                    CASE
                        WHEN c.centroid_gcj02 IS NOT NULL THEN 'community_centroid_gcj02'
                        WHEN c.centroid_wgs84 IS NOT NULL THEN 'community_centroid_wgs84'
                        ELSE NULL
                    END
                ) AS anchor_source,
                COALESCE(
                    c.anchor_quality,
                    CASE
                        WHEN c.centroid_gcj02 IS NOT NULL OR c.centroid_wgs84 IS NOT NULL THEN COALESCE(c.source_confidence, 0.92)
                        ELSE NULL
                    END
                ) AS anchor_quality
            FROM communities c
            JOIN districts d ON d.district_id = c.district_id
            ORDER BY c.district_id, c.community_id
            """
        )
        building_rows = query_rows(
            """
            SELECT
                b.building_id,
                b.community_id,
                c.district_id,
                d.district_name,
                d.short_name AS district_short_name,
                c.name AS community_name,
                b.building_no AS building_name,
                b.total_floors,
                COALESCE(
                    ARRAY_AGG(DISTINCT ca.alias_name) FILTER (WHERE ca.alias_name IS NOT NULL),
                    ARRAY[]::TEXT[]
                ) AS community_aliases,
                COALESCE(
                    ARRAY_AGG(DISTINCT ba.alias_name) FILTER (WHERE ba.alias_name IS NOT NULL),
                    ARRAY[]::TEXT[]
                ) AS building_aliases,
                COALESCE(
                    ARRAY_AGG(DISTINCT ba.source_ref) FILTER (WHERE ba.source_ref IS NOT NULL),
                    ARRAY[]::TEXT[]
                ) AS source_refs,
                COALESCE(ST_X(b.geom_gcj02), ST_X(b.geom_wgs84)) AS center_lng,
                COALESCE(ST_Y(b.geom_gcj02), ST_Y(b.geom_wgs84)) AS center_lat,
                CASE
                    WHEN b.geom_gcj02 IS NOT NULL THEN 'building_anchor_gcj02'
                    WHEN b.geom_wgs84 IS NOT NULL THEN 'building_anchor_wgs84'
                    ELSE NULL
                END AS anchor_source
            FROM buildings b
            JOIN communities c ON c.community_id = b.community_id
            JOIN districts d ON d.district_id = c.district_id
            LEFT JOIN community_aliases ca ON ca.community_id = c.community_id
            LEFT JOIN building_aliases ba ON ba.building_id = b.building_id
            GROUP BY
                b.building_id,
                b.community_id,
                c.district_id,
                d.district_name,
                d.short_name,
                c.name,
                b.building_no,
                b.total_floors,
                b.geom_gcj02,
                b.geom_wgs84
            ORDER BY c.district_id, c.community_id, b.building_no
            """
        )
    except Exception:
        return None

    return _catalog_from_payload(
        {
            "districts": district_rows,
            "communities": community_rows,
            "buildings": building_rows,
        },
        source="database",
    )


def _load_from_mock() -> dict[str, Any]:
    from .service import flatten_communities

    districts: dict[str, dict[str, Any]] = {}
    communities: list[dict[str, Any]] = []
    buildings: list[dict[str, Any]] = []
    for community in flatten_communities():
        districts.setdefault(
            community["districtId"],
            {
                "district_id": community["districtId"],
                "district_name": community["districtName"],
                "short_name": community.get("districtShort") or community["districtName"],
            },
        )
        communities.append(
            {
                "district_id": community["districtId"],
                "district_name": community["districtName"],
                "district_short_name": community.get("districtShort") or community["districtName"],
                "community_id": community["id"],
                "community_name": community["name"],
                "aliases": [],
                "source_confidence": 0.72,
            }
        )
        for building in community.get("buildings", []):
            buildings.append(
                {
                    "district_id": community["districtId"],
                    "district_name": community["districtName"],
                    "district_short_name": community.get("districtShort") or community["districtName"],
                    "community_id": community["id"],
                    "community_name": community["name"],
                    "building_id": building["id"],
                    "building_name": building["name"],
                    "total_floors": building.get("totalFloors"),
                    "community_aliases": [],
                    "building_aliases": [],
                    "source_refs": [],
                }
            )
    return _catalog_from_payload(
        {
            "districts": list(districts.values()),
            "communities": communities,
            "buildings": buildings,
        },
        source="mock",
    ) or {"source": "mock", "district_refs": [], "community_refs": [], "building_refs": []}


def load_reference_catalog(*, allow_mock: bool | None = None) -> dict[str, Any]:
    database_catalog = _load_from_database()
    if database_catalog:
        return database_catalog

    file_catalog = _load_from_catalog_file()
    if file_catalog:
        return file_catalog

    should_allow_mock = mock_enabled() if allow_mock is None else allow_mock
    if should_allow_mock:
        return _load_from_mock()

    return {"source": "empty", "district_refs": [], "community_refs": [], "building_refs": []}
