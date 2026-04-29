"""CityManifest — typed shape for per-city configuration loaded from YAML.

Spec §5.1 M1.

A manifest declares everything that was historically hardcoded as "Shanghai":
- map center + default zoom
- ordered district list (code + display name)
- (future) reference rentals, metro stations, comp anchor points

The schema is intentionally minimal in v0.1 — it only covers what the current
code already uses. Add fields here as we migrate more callers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass(frozen=True)
class CityDistrict:
    district_code: int
    display_name: str


@dataclass(frozen=True)
class CityManifest:
    city_id: str
    display_name: str
    country_code: str
    center: tuple[float, float]
    default_zoom: float
    districts: tuple[CityDistrict, ...] = field(default_factory=tuple)


def _require(obj: dict[str, Any], key: str) -> Any:
    if key not in obj:
        raise ValueError(f"city manifest missing required field: {key}")
    return obj[key]


def parse_manifest_yaml(yaml_text: str) -> CityManifest:
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError("city manifest must be a YAML mapping at the top level")

    center_raw = _require(raw, "center")
    if not (isinstance(center_raw, list) and len(center_raw) == 2):
        raise ValueError("city manifest 'center' must be [lng, lat]")
    try:
        center = (float(center_raw[0]), float(center_raw[1]))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"city manifest 'center' values must be numeric: {center_raw!r}") from exc

    try:
        default_zoom = float(_require(raw, "default_zoom"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"city manifest 'default_zoom' must be numeric: {raw.get('default_zoom')!r}") from exc

    districts = tuple(
        CityDistrict(
            district_code=int(_require(d, "district_code")),
            display_name=str(_require(d, "display_name")),
        )
        for d in raw.get("districts", []) or []
    )

    return CityManifest(
        city_id=str(_require(raw, "city_id")),
        display_name=str(_require(raw, "display_name")),
        country_code=str(_require(raw, "country_code")),
        center=center,
        default_zoom=default_zoom,
        districts=districts,
    )
