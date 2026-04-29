"""GET /api/v2/config/city — returns active city manifest summary."""
from __future__ import annotations


def test_get_city_config_returns_shanghai_by_default(client):
    resp = client.get("/api/v2/config/city")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cityId"] == "shanghai"
    assert data["displayName"] == "上海"
    assert data["center"] == [121.4737, 31.2304]
    assert data["defaultZoom"] == 10.8
    assert isinstance(data["districts"], list)
    assert len(data["districts"]) == 16
    sample = data["districts"][0]
    assert "districtCode" in sample
    assert "displayName" in sample
