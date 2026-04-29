"""City manifest loader — resolves active city from ATLAS_CITY env var.

Default: 'shanghai'. Cached for process lifetime.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .manifest import CityManifest, parse_manifest_yaml

_MANIFEST_DIR = Path(__file__).resolve().parent


def _manifest_path(city_id: str) -> Path:
    return _MANIFEST_DIR / f"{city_id}.yaml"


@lru_cache(maxsize=8)
def load_city(city_id: str) -> CityManifest:
    path = _manifest_path(city_id)
    if not path.is_file():
        raise FileNotFoundError(f"city manifest not found: {path}")
    return parse_manifest_yaml(path.read_text(encoding="utf-8"))


def load_active_city() -> CityManifest:
    """Return the manifest for the city named by ATLAS_CITY (default: shanghai)."""
    city_id = os.environ.get("ATLAS_CITY", "shanghai")
    return load_city(city_id)
