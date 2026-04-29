from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CityDistrictSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    district_code: int = Field(serialization_alias="districtCode")
    display_name: str = Field(serialization_alias="displayName")


class CityConfigResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    city_id: str = Field(serialization_alias="cityId")
    display_name: str = Field(serialization_alias="displayName")
    country_code: str = Field(serialization_alias="countryCode")
    center: tuple[float, float]
    default_zoom: float = Field(serialization_alias="defaultZoom")
    districts: list[CityDistrictSummary]
