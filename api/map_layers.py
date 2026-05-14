"""Map layer contracts for Yieldwise candidate-pool and atlas surfaces."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

_ALLOWED_GEOMETRY = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"}
_ALLOWED_PROPERTY_TYPES = {"string", "number", "integer", "boolean", "object", "array"}
_ALLOWED_VIEW_MODES = {"map", "table", "candidate-pool"}


def _non_empty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _sanitize_path(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    # Never expose workstation-local absolute paths in API/UI payloads.
    # Keep project-relative paths intact because those are useful provenance.
    if Path(text).is_absolute():
        return Path(text).name
    return text


@dataclass(frozen=True)
class LayerConfig:
    visible: bool = True
    order: int = 0
    opacity: float = 1.0
    color_scale_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.visible, bool):
            raise TypeError("visible must be bool")
        if not isinstance(self.order, int):
            raise TypeError("order must be int")
        if not isinstance(self.opacity, (int, float)) or not math.isfinite(float(self.opacity)):
            raise ValueError("opacity must be finite")
        if not 0.0 <= float(self.opacity) <= 1.0:
            raise ValueError("opacity must be in [0, 1]")
        object.__setattr__(self, "opacity", float(self.opacity))
        if self.color_scale_id is not None:
            object.__setattr__(self, "color_scale_id", _non_empty(self.color_scale_id, "color_scale_id"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "visible": self.visible,
            "order": self.order,
            "opacity": self.opacity,
            "colorScaleId": self.color_scale_id,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None) -> "LayerConfig":
        payload = payload or {}
        return cls(
            visible=payload.get("visible", True),
            order=payload.get("order", 0),
            opacity=payload.get("opacity", 1.0),
            color_scale_id=payload.get("colorScaleId"),
        )


@dataclass(frozen=True)
class DatasetLayer:
    layer_id: str
    kind: str
    geometry_type: str
    properties: Mapping[str, str]
    source_health: Mapping[str, Any]
    config: LayerConfig = field(default_factory=LayerConfig)
    source_path: str | Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "layer_id", _non_empty(self.layer_id, "layer_id"))
        object.__setattr__(self, "kind", _non_empty(self.kind, "kind"))
        if self.geometry_type not in _ALLOWED_GEOMETRY:
            raise ValueError(f"unknown geometry type: {self.geometry_type}")
        if not isinstance(self.properties, Mapping):
            raise TypeError("properties must be a mapping")
        clean_props: dict[str, str] = {}
        for key, token in self.properties.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("property names must be non-empty strings")
            if token not in _ALLOWED_PROPERTY_TYPES:
                raise ValueError(f"unknown property type token: {token}")
            clean_props[key] = token
        object.__setattr__(self, "properties", clean_props)
        if not isinstance(self.source_health, Mapping) or "status" not in self.source_health:
            raise ValueError("source_health must include status")
        object.__setattr__(self, "source_health", dict(self.source_health))
        if not isinstance(self.config, LayerConfig):
            object.__setattr__(self, "config", LayerConfig.from_dict(self.config))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "layerId": self.layer_id,
            "kind": self.kind,
            "geometryType": self.geometry_type,
            "properties": dict(self.properties),
            "sourceHealth": dict(self.source_health),
            "config": self.config.to_dict(),
        }
        source_path = _sanitize_path(self.source_path)
        if source_path is not None:
            payload["sourcePath"] = source_path
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DatasetLayer":
        return cls(
            layer_id=payload["layerId"],
            kind=payload["kind"],
            geometry_type=payload["geometryType"],
            properties=payload["properties"],
            source_health=payload["sourceHealth"],
            config=LayerConfig.from_dict(payload.get("config")),
            source_path=payload.get("sourcePath"),
        )


class LayerRegistry:
    def __init__(self) -> None:
        self._layers: dict[str, DatasetLayer] = {}

    def register(self, layer: DatasetLayer) -> None:
        if not isinstance(layer, DatasetLayer):
            raise TypeError("layer must be a DatasetLayer")
        if layer.layer_id in self._layers:
            raise ValueError(f"duplicate layer id: {layer.layer_id}")
        self._layers[layer.layer_id] = layer

    def unregister(self, layer_id: str) -> None:
        self._layers.pop(layer_id)

    def get(self, layer_id: str) -> DatasetLayer:
        if layer_id not in self._layers:
            raise KeyError(layer_id)
        return self._layers[layer_id]

    def has(self, layer_id: str) -> bool:
        return layer_id in self._layers

    def list(self) -> list[DatasetLayer]:
        return list(self._layers.values())

    def __len__(self) -> int:
        return len(self._layers)

    def __contains__(self, layer_id: str) -> bool:
        return self.has(layer_id)


@dataclass(frozen=True)
class ColorScale:
    thresholds: Sequence[float]
    colors: Sequence[str]
    default: str
    scale_id: str | None = None

    def __post_init__(self) -> None:
        thresholds = [float(x) for x in self.thresholds]
        if any(not math.isfinite(x) for x in thresholds):
            raise ValueError("thresholds must be finite")
        if any(thresholds[i] <= thresholds[i - 1] for i in range(1, len(thresholds))):
            raise ValueError("thresholds must be strictly ascending")
        colors = [str(c) for c in self.colors]
        if len(colors) != len(thresholds) + 1:
            raise ValueError("color count must be one more than thresholds")
        object.__setattr__(self, "thresholds", thresholds)
        object.__setattr__(self, "colors", colors)
        object.__setattr__(self, "default", str(self.default))
        if self.scale_id is not None:
            object.__setattr__(self, "scale_id", _non_empty(self.scale_id, "scale_id"))

    def bucket_for(self, value: float | None) -> int | None:
        if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return None
        val = float(value)
        idx = 0
        while idx < len(self.thresholds) and val >= self.thresholds[idx]:
            idx += 1
        return idx

    def color_for(self, value: float | None) -> str:
        bucket = self.bucket_for(value)
        if bucket is None:
            return self.default
        return self.colors[bucket]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scaleId": self.scale_id,
            "thresholds": list(self.thresholds),
            "colors": list(self.colors),
            "default": self.default,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ColorScale":
        return cls(
            scale_id=payload.get("scaleId"),
            thresholds=payload["thresholds"],
            colors=payload["colors"],
            default=payload["default"],
        )


class FilterState:
    def __init__(self, *, defaults: Mapping[str, Any]) -> None:
        self.defaults = dict(defaults)
        self._values: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        if key in self.defaults and value == self.defaults[key]:
            self._values.pop(key, None)
        else:
            self._values[key] = value

    def get(self, key: str) -> Any:
        if key in self._values:
            return self._values[key]
        return self.defaults.get(key)

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._values.clear()
        else:
            self._values.pop(key, None)

    def serialize(self) -> dict[str, Any]:
        return {key: self._values[key] for key in sorted(self._values)}

    def is_default(self) -> bool:
        return not self._values

    def to_dict(self) -> dict[str, Any]:
        return {"defaults": dict(self.defaults), "values": self.serialize()}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FilterState":
        state = cls(defaults=payload.get("defaults", {}))
        for key, value in payload.get("values", {}).items():
            state.set(key, value)
        return state


@dataclass(frozen=True)
class ViewportPreset:
    preset_id: str
    label: str
    view_mode: str
    center: tuple[float, float]
    zoom: float
    layer_ids: list[str]
    filters: FilterState
    registry: LayerRegistry | None = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "preset_id", _non_empty(self.preset_id, "preset_id"))
        object.__setattr__(self, "label", _non_empty(self.label, "label"))
        if self.view_mode not in _ALLOWED_VIEW_MODES:
            raise ValueError(f"unknown view mode: {self.view_mode}")
        if len(self.center) != 2 or any(not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in self.center):
            raise ValueError("center must be a finite lon/lat pair")
        object.__setattr__(self, "center", (float(self.center[0]), float(self.center[1])))
        if not isinstance(self.zoom, (int, float)) or not math.isfinite(float(self.zoom)) or float(self.zoom) < 0:
            raise ValueError("zoom must be a non-negative finite number")
        object.__setattr__(self, "zoom", float(self.zoom))
        layer_ids = [str(x) for x in self.layer_ids]
        if self.registry is not None:
            missing = [layer_id for layer_id in layer_ids if not self.registry.has(layer_id)]
            if missing:
                raise ValueError(f"unknown layer id(s): {missing}")
        object.__setattr__(self, "layer_ids", layer_ids)
        if not isinstance(self.filters, FilterState):
            raise TypeError("filters must be FilterState")

    def to_dict(self) -> dict[str, Any]:
        return {
            "presetId": self.preset_id,
            "label": self.label,
            "viewMode": self.view_mode,
            "center": list(self.center),
            "zoom": self.zoom,
            "layerIds": list(self.layer_ids),
            "filters": self.filters.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ViewportPreset":
        return cls(
            preset_id=payload["presetId"],
            label=payload["label"],
            view_mode=payload["viewMode"],
            center=tuple(payload["center"]),
            zoom=payload["zoom"],
            layer_ids=list(payload["layerIds"]),
            filters=FilterState.from_dict(payload["filters"]),
        )
