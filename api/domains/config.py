"""Yieldwise active city config endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from api.config.cities.loader import load_active_city
from api.schemas.city_config import CityConfigResponse, DistrictSummary

router = APIRouter()


@router.get(
    "/config/city",
    response_model=CityConfigResponse,
    response_model_by_alias=True,
)
def get_city_config() -> CityConfigResponse:
    manifest = load_active_city()
    return CityConfigResponse(
        city_id=manifest.city_id,
        display_name=manifest.display_name,
        country_code=manifest.country_code,
        center=manifest.center,
        default_zoom=manifest.default_zoom,
        districts=[
            DistrictSummary(district_code=d.district_code, display_name=d.display_name)
            for d in manifest.districts
        ],
    )
