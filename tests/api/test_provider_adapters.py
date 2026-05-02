from __future__ import annotations

from api.provider_adapters import provider_readiness_snapshot


def test_readiness_snapshot_uses_local_first_status_fields(monkeypatch) -> None:
    monkeypatch.setenv("AMAP_API_KEY", "local-map-key")

    items = provider_readiness_snapshot(staged_listing_runs=2, staged_geometry_runs=1)
    by_id = {item["id"]: item for item in items}

    assert by_id["amap-aoi-poi"]["connectionState"] == "local_config_ready"
    assert by_id["amap-aoi-poi"]["readinessLabel"] == "本地配置已就绪"
    assert by_id["shanghai-open-data"]["connectionState"] == "planned"
    assert by_id["public-browser-sampling"]["connectionState"] == "offline_ready"

    old_keys = {
        "supports" + "LivePull",
        "has" + "Credentials",
        "configured" + "RequiredEnv",
        "missing" + "RequiredEnv",
        "matched" + "CredentialSetLabel",
    }
    old_states = {"credentials" + "_ready", "credentials" + "_partial", "connected" + "_live"}

    for item in items:
        assert "supportsLocalAutomation" in item
        assert "hasLocalConfig" in item
        assert "configuredLocalEnv" in item
        assert "missingLocalEnv" in item
        assert "matchedLocalConfigSetLabel" in item
        assert old_keys.isdisjoint(item)
        assert item["connectionState"] not in old_states
