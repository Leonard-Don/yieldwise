import { api } from "./api.js";

let _active = null;

export function applyCityConfig(cfg) {
  if (!cfg || !cfg.cityId || !Array.isArray(cfg.center) || cfg.center.length !== 2) {
    throw new Error("invalid city config");
  }
  _active = Object.freeze({
    cityId: cfg.cityId,
    displayName: cfg.displayName,
    countryCode: cfg.countryCode,
    center: [cfg.center[0], cfg.center[1]],
    defaultZoom: cfg.defaultZoom,
    districts: Object.freeze((cfg.districts || []).map((d) => Object.freeze({ ...d }))),
  });
  return _active;
}

export function getActiveCityConfig() {
  if (!_active) {
    throw new Error("city config not loaded — call applyCityConfig() at boot");
  }
  return _active;
}

export async function bootstrapCityConfig() {
  const cfg = await api.cityConfig();
  return applyCityConfig(cfg);
}
