from __future__ import annotations

import math
from pathlib import Path

import pytest

from api.map_layers import (
    ColorScale,
    DatasetLayer,
    FilterState,
    LayerConfig,
    LayerRegistry,
    ViewportPreset,
)


# ---------- LayerRegistry ----------

def _make_layer(layer_id: str = "districts", **overrides) -> DatasetLayer:
    base = dict(
        layer_id=layer_id,
        kind="districts",
        geometry_type="Polygon",
        properties={"name": "string", "yield": "number"},
        source_health={"status": "fresh", "freshness": "新鲜", "sample": 12},
    )
    base.update(overrides)
    return DatasetLayer(**base)


def test_registry_register_and_get_round_trip() -> None:
    registry = LayerRegistry()
    layer = _make_layer("districts")

    registry.register(layer)

    assert registry.get("districts") is layer
    assert registry.has("districts") is True
    assert registry.has("missing") is False


def test_registry_lists_layers_in_insertion_order() -> None:
    registry = LayerRegistry()
    a = _make_layer("districts")
    b = _make_layer("communities", kind="communities")
    c = _make_layer("buildings", kind="buildings", geometry_type="MultiPolygon")

    registry.register(a)
    registry.register(b)
    registry.register(c)

    assert [layer.layer_id for layer in registry.list()] == [
        "districts",
        "communities",
        "buildings",
    ]
    assert len(registry) == 3
    assert "buildings" in registry


def test_registry_rejects_duplicate_layer_ids() -> None:
    registry = LayerRegistry()
    registry.register(_make_layer("districts"))

    with pytest.raises(ValueError) as excinfo:
        registry.register(_make_layer("districts", kind="communities"))

    assert "districts" in str(excinfo.value)
    # The original layer still wins.
    assert registry.get("districts").kind == "districts"


def test_registry_get_unknown_raises_keyerror() -> None:
    registry = LayerRegistry()

    with pytest.raises(KeyError):
        registry.get("nope")


def test_registry_unregister_removes_layer() -> None:
    registry = LayerRegistry()
    registry.register(_make_layer("districts"))
    registry.register(_make_layer("communities", kind="communities"))

    registry.unregister("districts")

    assert "districts" not in registry
    assert [layer.layer_id for layer in registry.list()] == ["communities"]


# ---------- DatasetLayer ----------

def test_dataset_layer_validates_geometry_type() -> None:
    with pytest.raises(ValueError) as excinfo:
        _make_layer(geometry_type="Banana")
    assert "geometry" in str(excinfo.value).lower()


def test_dataset_layer_requires_non_empty_layer_id() -> None:
    with pytest.raises(ValueError):
        _make_layer(layer_id="")
    with pytest.raises(ValueError):
        _make_layer(layer_id="   ")


def test_dataset_layer_requires_property_schema_dict() -> None:
    with pytest.raises(TypeError):
        _make_layer(properties=["name", "yield"])  # type: ignore[arg-type]


def test_dataset_layer_rejects_unknown_property_type_token() -> None:
    with pytest.raises(ValueError) as excinfo:
        _make_layer(properties={"name": "potato"})
    assert "potato" in str(excinfo.value)


def test_dataset_layer_source_health_must_have_status() -> None:
    with pytest.raises(ValueError) as excinfo:
        _make_layer(source_health={"freshness": "新鲜"})
    assert "status" in str(excinfo.value)


def test_dataset_layer_serialize_redacts_absolute_user_path() -> None:
    layer = _make_layer(
        source_path=Path("/Users/leonardodon/secret/run/manifest.json"),
    )
    payload = layer.to_dict()
    assert "/Users/" not in str(payload)
    assert "leonardodon" not in str(payload)
    assert payload["sourcePath"] == "manifest.json"


def test_dataset_layer_serialize_redacts_any_absolute_local_path() -> None:
    layer = _make_layer(source_path="/home/alice/secret/run/manifest.json")
    payload = layer.to_dict()
    assert "/home/" not in str(payload)
    assert "alice" not in str(payload)
    assert payload["sourcePath"] == "manifest.json"


def test_dataset_layer_serialize_keeps_project_relative_path(tmp_path: Path) -> None:
    layer = _make_layer(source_path="data/import/run-1/manifest.json")
    payload = layer.to_dict()
    assert payload["sourcePath"] == "data/import/run-1/manifest.json"


def test_dataset_layer_to_dict_round_trip() -> None:
    layer = _make_layer(
        "districts",
        config=LayerConfig(visible=True, order=10, opacity=0.85, color_scale_id="yield"),
    )
    payload = layer.to_dict()
    restored = DatasetLayer.from_dict(payload)

    assert restored.layer_id == layer.layer_id
    assert restored.kind == layer.kind
    assert restored.geometry_type == layer.geometry_type
    assert restored.properties == layer.properties
    assert restored.source_health == layer.source_health
    assert restored.config.visible is True
    assert restored.config.order == 10
    assert restored.config.opacity == pytest.approx(0.85)
    assert restored.config.color_scale_id == "yield"


# ---------- LayerConfig ----------

def test_layer_config_defaults_are_safe() -> None:
    cfg = LayerConfig()
    assert cfg.visible is True
    assert cfg.order == 0
    assert cfg.opacity == pytest.approx(1.0)
    assert cfg.color_scale_id is None


def test_layer_config_rejects_invalid_opacity() -> None:
    with pytest.raises(ValueError):
        LayerConfig(opacity=1.5)
    with pytest.raises(ValueError):
        LayerConfig(opacity=-0.1)


# ---------- ColorScale ----------

def test_color_scale_buckets_are_left_inclusive_right_exclusive() -> None:
    scale = ColorScale(
        thresholds=[3.5, 5.0],
        colors=["#down", "#warn", "#up"],
        default="#dim",
    )
    assert scale.color_for(0) == "#down"
    assert scale.color_for(3.49) == "#down"
    assert scale.color_for(3.5) == "#warn"
    assert scale.color_for(4.99) == "#warn"
    assert scale.color_for(5.0) == "#up"
    assert scale.color_for(99.0) == "#up"


def test_color_scale_returns_default_for_missing_values() -> None:
    scale = ColorScale(
        thresholds=[3.5, 5.0],
        colors=["#down", "#warn", "#up"],
        default="#dim",
    )
    assert scale.color_for(None) == "#dim"
    assert scale.color_for(float("nan")) == "#dim"


def test_color_scale_requires_one_more_color_than_thresholds() -> None:
    with pytest.raises(ValueError) as excinfo:
        ColorScale(thresholds=[3.5, 5.0], colors=["#down", "#up"], default="#dim")
    assert "color" in str(excinfo.value).lower()


def test_color_scale_rejects_non_ascending_thresholds() -> None:
    with pytest.raises(ValueError):
        ColorScale(thresholds=[5.0, 3.5], colors=["#a", "#b", "#c"], default="#dim")
    with pytest.raises(ValueError):
        ColorScale(thresholds=[3.5, 3.5], colors=["#a", "#b", "#c"], default="#dim")


def test_color_scale_bucket_for_returns_index() -> None:
    scale = ColorScale(
        thresholds=[3.5, 5.0],
        colors=["#down", "#warn", "#up"],
        default="#dim",
    )
    assert scale.bucket_for(0.0) == 0
    assert scale.bucket_for(4.0) == 1
    assert scale.bucket_for(10.0) == 2
    assert scale.bucket_for(None) is None


def test_color_scale_to_dict_round_trip() -> None:
    scale = ColorScale(
        scale_id="yield",
        thresholds=[3.5, 5.0],
        colors=["#down", "#warn", "#up"],
        default="#dim",
    )
    payload = scale.to_dict()
    restored = ColorScale.from_dict(payload)
    assert restored.scale_id == "yield"
    assert restored.thresholds == [3.5, 5.0]
    assert restored.colors == ["#down", "#warn", "#up"]
    assert restored.default == "#dim"
    # Determinism: two calls produce identical payloads.
    assert scale.to_dict() == scale.to_dict()


# ---------- FilterState ----------

def test_filter_state_serialize_only_includes_non_default_values() -> None:
    state = FilterState(
        defaults={
            "min_yield": 0,
            "max_budget": 10000,
            "min_samples": 0,
            "district": "all",
        }
    )
    state.set("min_yield", 4)
    state.set("district", "static_huangpu")

    serialized = state.serialize()
    assert serialized == {"min_yield": 4, "district": "static_huangpu"}


def test_filter_state_set_default_value_drops_from_serialize() -> None:
    state = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    state.set("min_yield", 4)
    state.set("min_yield", 0)
    assert state.serialize() == {}
    assert state.is_default() is True


def test_filter_state_reset_returns_to_defaults() -> None:
    state = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    state.set("min_yield", 4)
    state.set("max_budget", 1500)
    state.set("custom_flag", True)

    state.reset()

    assert state.serialize() == {}
    assert state.get("min_yield") == 0
    assert state.get("max_budget") == 10000
    assert state.get("custom_flag") is None


def test_filter_state_reset_single_key_keeps_others() -> None:
    state = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    state.set("min_yield", 4)
    state.set("max_budget", 1500)

    state.reset("min_yield")

    assert state.serialize() == {"max_budget": 1500}
    assert state.get("min_yield") == 0


def test_filter_state_serialize_is_deterministic() -> None:
    state = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    state.set("max_budget", 1500)
    state.set("min_yield", 4)

    first = list(state.serialize().keys())
    second = list(state.serialize().keys())
    assert first == second
    assert first == sorted(first)


def test_filter_state_to_dict_round_trip() -> None:
    state = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    state.set("min_yield", 4)

    restored = FilterState.from_dict(state.to_dict())
    assert restored.serialize() == {"min_yield": 4}
    assert restored.get("max_budget") == 10000


def test_filter_state_unknown_key_get_returns_none() -> None:
    state = FilterState(defaults={"min_yield": 0})
    assert state.get("anything") is None


# ---------- ViewportPreset ----------

def test_viewport_preset_serialize_round_trip() -> None:
    filters = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    filters.set("min_yield", 4)

    preset = ViewportPreset(
        preset_id="hunter-default",
        label="Hunter — high-yield communities",
        view_mode="map",
        center=(121.4737, 31.2304),
        zoom=11.5,
        layer_ids=["districts", "communities"],
        filters=filters,
    )

    payload = preset.to_dict()
    restored = ViewportPreset.from_dict(payload)

    assert restored.preset_id == "hunter-default"
    assert restored.label == "Hunter — high-yield communities"
    assert restored.view_mode == "map"
    assert restored.center == (121.4737, 31.2304)
    assert restored.zoom == pytest.approx(11.5)
    assert restored.layer_ids == ["districts", "communities"]
    assert restored.filters.serialize() == {"min_yield": 4}


def test_viewport_preset_supports_table_and_candidate_pool_views() -> None:
    table_preset = ViewportPreset(
        preset_id="table-defaults",
        label="Table — community board",
        view_mode="table",
        center=(121.4737, 31.2304),
        zoom=11.0,
        layer_ids=["communities"],
        filters=FilterState(defaults={}),
    )
    pool_preset = ViewportPreset(
        preset_id="pool-shortlist",
        label="Candidate pool — shortlist",
        view_mode="candidate-pool",
        center=(121.4737, 31.2304),
        zoom=11.0,
        layer_ids=["candidates"],
        filters=FilterState(defaults={}),
    )

    assert table_preset.view_mode == "table"
    assert pool_preset.view_mode == "candidate-pool"
    assert table_preset.to_dict()["viewMode"] == "table"
    assert pool_preset.to_dict()["viewMode"] == "candidate-pool"


def test_viewport_preset_rejects_unknown_view_mode() -> None:
    with pytest.raises(ValueError):
        ViewportPreset(
            preset_id="bad",
            label="bad",
            view_mode="hologram",
            center=(0.0, 0.0),
            zoom=10.0,
            layer_ids=[],
            filters=FilterState(defaults={}),
        )


def test_viewport_preset_rejects_invalid_zoom() -> None:
    with pytest.raises(ValueError):
        ViewportPreset(
            preset_id="bad-zoom",
            label="bad",
            view_mode="map",
            center=(121.4737, 31.2304),
            zoom=-1.0,
            layer_ids=[],
            filters=FilterState(defaults={}),
        )


def test_viewport_preset_rejects_layer_ids_not_in_registry_when_supplied() -> None:
    registry = LayerRegistry()
    registry.register(_make_layer("communities", kind="communities"))
    filters = FilterState(defaults={})

    with pytest.raises(ValueError) as excinfo:
        ViewportPreset(
            preset_id="bad-layer",
            label="missing",
            view_mode="map",
            center=(0.0, 0.0),
            zoom=10.0,
            layer_ids=["districts"],
            filters=filters,
            registry=registry,
        )
    assert "districts" in str(excinfo.value)


# ---------- Sanity: a full registry composes cleanly ----------

def test_registry_with_color_scales_and_filters_and_preset_compose() -> None:
    registry = LayerRegistry()
    registry.register(
        _make_layer(
            "districts",
            config=LayerConfig(order=0, color_scale_id="yield"),
        )
    )
    registry.register(
        _make_layer(
            "communities",
            kind="communities",
            geometry_type="Polygon",
            config=LayerConfig(order=1, color_scale_id="yield"),
        )
    )

    yield_scale = ColorScale(
        scale_id="yield",
        thresholds=[3.5, 5.0],
        colors=["#down", "#warn", "#up"],
        default="#dim",
    )
    filters = FilterState(defaults={"min_yield": 0, "max_budget": 10000})
    filters.set("min_yield", 4.5)

    preset = ViewportPreset(
        preset_id="hunter-default",
        label="Hunter — high-yield communities",
        view_mode="map",
        center=(121.4737, 31.2304),
        zoom=11.5,
        layer_ids=["districts", "communities"],
        filters=filters,
        registry=registry,
    )

    assert yield_scale.color_for(4.0) == "#warn"
    assert preset.filters.serialize() == {"min_yield": 4.5}
    assert [layer.layer_id for layer in registry.list()] == ["districts", "communities"]
    assert not math.isnan(preset.zoom)
