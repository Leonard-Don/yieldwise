import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import { yieldColorFor, districtColorFor } from "./modes.js";

const SHANGHAI_CENTER = [121.4737, 31.2304];
const DEFAULT_ZOOM = 10.8;

export async function initMap({ container, store }) {
  const placeholder = container.querySelector('[data-role="map-placeholder"]');
  const runtime = await api.runtimeConfig();
  store.set({ runtime });

  if (!runtime.hasAmapKey || !runtime.amapApiKey) {
    showError(container, "AMap key 未配置 — 设置 AMAP_API_KEY 后重启");
    return null;
  }

  let AMap;
  try {
    AMap = await loadAmap({
      apiKey: runtime.amapApiKey,
      securityJsCode: runtime.amapSecurityJsCode,
    });
  } catch (err) {
    console.error("[atlas:map] AMap load failed", err);
    showError(container, `AMap 加载失败：${err.message}`);
    return null;
  }

  const map = new AMap.Map(container.id, {
    center: SHANGHAI_CENTER,
    zoom: DEFAULT_ZOOM,
    viewMode: "2D",
    mapStyle: "amap://styles/dark",
    showLabel: true,
    zooms: [8, 18],
  });
  map.addControl(new AMap.Scale());
  map.addControl(new AMap.ToolBar({ position: "RB" }));
  container.classList.add("is-ready");
  if (placeholder) placeholder.remove();

  let currentOverlays = [];
  let currentMode = null;
  let renderToken = 0;

  function clearOverlays() {
    if (currentOverlays.length === 0) return;
    map.remove(currentOverlays);
    currentOverlays = [];
  }

  async function renderForMode(modeId) {
    const myToken = ++renderToken;
    clearOverlays();
    if (modeId === "city") {
      const next = await renderDistricts({ AMap, map, store });
      if (myToken !== renderToken) {
        // a newer mode-change won — discard these overlays
        map.remove(next);
        return;
      }
      currentOverlays = next;
    } else {
      const next = await renderBuildings({ AMap, map, store });
      if (myToken !== renderToken) {
        map.remove(next);
        return;
      }
      currentOverlays = next;
    }
  }

  currentMode = store.get().mode;
  await renderForMode(currentMode);

  store.subscribe((state) => {
    if (state.mode !== currentMode) {
      currentMode = state.mode;
      renderForMode(currentMode).catch((err) =>
        console.error("[atlas:map] renderForMode failed", err),
      );
    }
  });

  syncSelectionHighlight({ map, AMap, store });
  attachOsmFootprintLayer({ map, AMap });

  return map;
}

// ─────────────────────────────────────────────────────────────────────
// OSM building-footprint background layer.
//
// Renders polygons from /api/v2/map/osm-footprints when the user has zoomed
// in enough that footprints are large enough to read (zoom ≥ 15). Each
// move/zoom event re-fetches with the current viewport bbox so we never
// load the full 69k city-wide payload. Polygons are subtle (low fill alpha,
// 1px stroke) so they sit BEHIND the district / building / community
// overlays, not on top of them.
// ─────────────────────────────────────────────────────────────────────
const FOOTPRINT_MIN_ZOOM = 15;
const FOOTPRINT_REQUEST_LIMIT = 1500;

function attachOsmFootprintLayer({ map, AMap }) {
  let overlays = [];
  let pendingToken = 0;

  function clear() {
    if (overlays.length === 0) return;
    map.remove(overlays);
    overlays = [];
  }

  async function refresh() {
    const myToken = ++pendingToken;
    const zoom = map.getZoom();
    if (zoom < FOOTPRINT_MIN_ZOOM) {
      clear();
      return;
    }
    const bounds = map.getBounds();
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    const viewport = `${sw.getLng().toFixed(4)},${sw.getLat().toFixed(4)},${ne.getLng().toFixed(4)},${ne.getLat().toFixed(4)}`;
    let payload;
    try {
      payload = await api.mapOsmFootprints({ viewport, limit: FOOTPRINT_REQUEST_LIMIT });
    } catch (err) {
      console.warn("[atlas:map] osm-footprints fetch failed", err);
      return;
    }
    if (myToken !== pendingToken) return; // newer request superseded us
    clear();
    const next = [];
    for (const feat of payload.features || []) {
      const geom = feat.geometry;
      const props = feat.properties || {};
      if (!geom || geom.type !== "Polygon") continue;
      const poly = new AMap.Polygon({
        path: geom.coordinates[0],
        strokeColor: "#7a8da0",
        strokeWeight: 0.6,
        strokeOpacity: 0.55,
        fillColor: props.communityId ? "#5d8aa8" : "#3b4754",
        fillOpacity: 0.18,
        bubble: true,
        zIndex: 5,
      });
      next.push(poly);
    }
    if (next.length > 0) map.add(next);
    overlays = next;
  }

  map.on("moveend", refresh);
  map.on("zoomend", refresh);
  // initial pass after slight delay so the renderForMode pass paints first
  setTimeout(refresh, 150);
}

function showError(container, message) {
  const div = document.createElement("div");
  div.className = "atlas-map-error";
  div.textContent = message;
  container.appendChild(div);
}

async function renderBuildings({ AMap, map, store }) {
  const overlays = [];
  let buildings;
  try {
    buildings = await api.mapBuildings();
  } catch (err) {
    console.error("[atlas:map] buildings load failed", err);
    return overlays;
  }
  for (const feature of buildings.features || []) {
    const geometry = feature.geometry;
    const props = feature.properties || {};
    if (!geometry) continue;
    const yieldPct = numericYieldPct(props.yield_avg_pct);
    const color = yieldColorFor(yieldPct);
    const overlay = createOverlay({ AMap, geometry, color });
    if (!overlay) continue;
    overlay.setExtData({ buildingId: props.building_id, props });
    overlay.on("click", () => {
      store.set({
        selection: { type: "building", id: props.building_id, props },
      });
    });
    overlays.push(overlay);
  }
  if (overlays.length > 0) map.add(overlays);
  return overlays;
}

const districtBoundaryCache = new Map();

async function renderDistricts({ AMap, map, store }) {
  const overlays = [];
  let payload;
  try {
    payload = await api.mapDistricts();
  } catch (err) {
    console.error("[atlas:map] districts load failed", err);
    return overlays;
  }

  const districts = payload.districts || [];
  const summary = payload.summary || {};
  const meanYield = summary.avgYield;

  if (!AMap.DistrictSearch) {
    console.warn("[atlas:map] AMap.DistrictSearch unavailable — falling back to label markers");
    for (const district of districts) {
      // No polygon plugin — skip silently. Phase 6 may add label markers fallback.
    }
    return overlays;
  }

  const search = new AMap.DistrictSearch({
    level: "district",
    extensions: "all",
    subdistrict: 0,
    showbiz: false,
  });

  await Promise.all(
    districts.map(async (district) => {
      const boundaries = await fetchBoundariesCached(search, district.name);
      const color = districtColorFor(district.yield, meanYield);
      for (const path of boundaries) {
        const polygon = new AMap.Polygon({
          path,
          strokeColor: color,
          strokeWeight: 1,
          strokeOpacity: 0.85,
          fillColor: color,
          fillOpacity: 0.25,
          bubble: false,
        });
        polygon.setExtData({ districtId: district.id, props: district });
        polygon.on("click", () => {
          store.set({
            selection: { type: "district", id: district.id, props: district },
          });
        });
        overlays.push(polygon);
      }
    }),
  );

  if (overlays.length > 0) map.add(overlays);
  return overlays;
}

function fetchBoundariesCached(search, districtName) {
  if (districtBoundaryCache.has(districtName)) {
    return Promise.resolve(districtBoundaryCache.get(districtName));
  }
  return new Promise((resolve) => {
    search.search(districtName, (status, result) => {
      if (status !== "complete") {
        districtBoundaryCache.set(districtName, []);
        resolve([]);
        return;
      }
      const first = result?.districtList?.[0];
      const boundaries = first?.boundaries ?? [];
      districtBoundaryCache.set(districtName, boundaries);
      resolve(boundaries);
    });
  });
}

function createOverlay({ AMap, geometry, color }) {
  if (geometry.type === "Polygon") {
    return new AMap.Polygon({
      path: geometry.coordinates[0],
      strokeColor: color,
      strokeWeight: 1,
      strokeOpacity: 0.9,
      fillColor: color,
      fillOpacity: 0.35,
      bubble: true,
    });
  }
  if (geometry.type === "Point") {
    return new AMap.CircleMarker({
      center: geometry.coordinates,
      radius: 6,
      strokeColor: color,
      strokeWeight: 1,
      fillColor: color,
      fillOpacity: 0.7,
      bubble: true,
    });
  }
  return null;
}

function numericYieldPct(raw) {
  if (raw === null || raw === undefined) return null;
  const value = Number(raw);
  if (Number.isNaN(value)) return null;
  // Backend stores yield as a percentage already (e.g. 4.16 = 4.16%). Some
  // staged sources return a fraction (0.04). Detect by magnitude.
  return value < 1 ? value * 100 : value;
}

function syncSelectionHighlight({ map, AMap, store }) {
  let lastMarker = null;
  store.subscribe((state) => {
    const sel = state.selection;
    if (lastMarker) {
      map.remove(lastMarker);
      lastMarker = null;
    }
    if (!sel || sel.type !== "building") return;
    const props = sel.props || {};
    const lng = Number(props.center_lng);
    const lat = Number(props.center_lat);
    if (Number.isNaN(lng) || Number.isNaN(lat)) return;
    lastMarker = new AMap.CircleMarker({
      center: [lng, lat],
      radius: 8,
      strokeColor: "#ffffff",
      strokeWeight: 2,
      fillColor: "var(--up)",
      fillOpacity: 0.0,
      bubble: false,
    });
    map.add(lastMarker);
    map.setCenter([lng, lat]);
  });
}
