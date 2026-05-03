"""Yieldwise active city config endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from api.config import city
from api.schemas.city_config import CityConfigResponse, CityDistrictSummary

router = APIRouter(tags=["config"])


@router.get(
    "/config/city",
    response_model=CityConfigResponse,
    response_model_by_alias=True,
)
def get_city_config() -> CityConfigResponse:
    return CityConfigResponse(
        city_id=city.CITY_ID,
        display_name=city.DISPLAY_NAME,
        country_code=city.COUNTRY_CODE,
        center=city.CENTER,
        default_zoom=city.DEFAULT_ZOOM,
        districts=[
            CityDistrictSummary(district_code=d.district_code, display_name=d.display_name)
            for d in city.DISTRICTS
        ],
    )
