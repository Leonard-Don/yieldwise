"""M1 city manifest schema tests."""
from __future__ import annotations

import pytest

from api.config.cities.manifest import CityManifest, parse_manifest_yaml


def test_parse_minimal_manifest():
    yaml_text = """
city_id: testcity
display_name: 测试市
country_code: CN
center: [121.0, 31.0]
default_zoom: 11.0
districts:
  - district_code: 999
    display_name: 测试区
"""
    m = parse_manifest_yaml(yaml_text)
    assert isinstance(m, CityManifest)
    assert m.city_id == "testcity"
    assert m.display_name == "测试市"
    assert m.center == (121.0, 31.0)
    assert m.default_zoom == 11.0
    assert len(m.districts) == 1
    assert m.districts[0].district_code == 999


def test_manifest_rejects_missing_required_field():
    yaml_text = """
city_id: broken
display_name: 缺中心
country_code: CN
default_zoom: 10
districts: []
"""
    with pytest.raises(ValueError, match="center"):
        parse_manifest_yaml(yaml_text)


def test_manifest_center_must_have_two_floats():
    yaml_text = """
city_id: broken2
display_name: 中心格式错
country_code: CN
center: [121.0]
default_zoom: 10
districts: []
"""
    with pytest.raises(ValueError, match="center"):
        parse_manifest_yaml(yaml_text)
