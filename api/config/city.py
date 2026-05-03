"""Inlined Shanghai city constants.

Replaces the previous YAML-driven api.config.cities package. The project is
intentionally Shanghai-only — there is no per-city manifest abstraction.
"""

from __future__ import annotations

from typing import NamedTuple


class CityDistrict(NamedTuple):
    district_code: int
    display_name: str


CITY_ID = "shanghai"
DISPLAY_NAME = "上海"
COUNTRY_CODE = "CN"
CENTER: tuple[float, float] = (121.4737, 31.2304)
DEFAULT_ZOOM = 10.8

DISTRICTS: list[CityDistrict] = [
    CityDistrict(310101, "黄浦区"),
    CityDistrict(310104, "徐汇区"),
    CityDistrict(310105, "长宁区"),
    CityDistrict(310106, "静安区"),
    CityDistrict(310107, "普陀区"),
    CityDistrict(310109, "虹口区"),
    CityDistrict(310110, "杨浦区"),
    CityDistrict(310112, "闵行区"),
    CityDistrict(310113, "宝山区"),
    CityDistrict(310114, "嘉定区"),
    CityDistrict(310115, "浦东新区"),
    CityDistrict(310116, "金山区"),
    CityDistrict(310117, "松江区"),
    CityDistrict(310118, "青浦区"),
    CityDistrict(310120, "奉贤区"),
    CityDistrict(310151, "崇明区"),
]
