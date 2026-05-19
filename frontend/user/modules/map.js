import { api } from "./api.js";
import { loadAmap } from "./runtime.js";
import {
  yieldColorFor,
  districtColorFor,
  filtersToApiParams,
  resolveDefaultFilters,
} from "./modes.js?v=20260519-single-yield";
import { getActiveCityConfig } from "./config-bootstrap.js";

export async function initMap({ container, store }) {
  const placeholder = container.querySelector('[data-role="map-placeholder"]');
  const runtime = await api.runtimeConfig();
  store.set({ runtime });

  if (!runtime.hasAmapKey || !runtime.amapApiKey) {
    showError(container, "地图底图暂未启用。可先使用右侧榜单筛选，配置本机地图服务后会自动显示。");
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
    showError(container, "地图加载失败，可先使用右侧榜单筛选，稍后刷新重试。");
    return null;
  }

  const cityCfg = getActiveCityConfig();
  const map = new AMap.Map(container.id, {
    center: cityCfg.center,
    zoom: cityCfg.defaultZoom,
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
  let currentMapKey = null;
  let renderToken = 0;
  const opportunitySelections = new Map();

  function clearOverlays() {
    if (currentOverlays.length === 0) return;
    map.remove(currentOverlays);
    currentOverlays = [];
  }

  async function renderForState(state) {
    const myToken = ++renderToken;
    clearOverlays();
    if (state.mode === "city") {
      opportunitySelections.clear();
      const next = await renderDistricts({ AMap, map, store });
      if (myToken !== renderToken) {
        // a newer mode-change won — discard these overlays
        map.remove(next);
        return;
      }
      currentOverlays = next;
    } else {
      const next = await renderOpportunities({ AMap, map, store, state, opportunitySelections });
      if (myToken !== renderToken) {
        map.remove(next);
        return;
      }
      currentOverlays = next;
    }
  }

  currentMapKey = mapKeyFor(store.get());
  await renderForState(store.get());

  store.subscribe((state) => {
    const nextKey = mapKeyFor(state);
    if (nextKey !== currentMapKey) {
      currentMapKey = nextKey;
      renderForState(state).catch((err) =>
        console.error("[atlas:map] renderForState failed", err),
      );
    }
  });

  const handlePinActivation = (event) => {
    const pin = event.target.closest("[data-map-pin-id]");
    if (!pin) return;
    const selection = opportunitySelections.get(pin.dataset.mapPinId);
    if (!selection) return;
    event.preventDefault();
    event.stopPropagation();
    store.set({ selection });
  };
  const handlePinKeyActivation = (event) => {
    if (!["Enter", " "].includes(event.key)) return;
    handlePinActivation(event);
  };
  container.addEventListener("pointerdown", handlePinActivation);
  container.addEventListener("mousedown", handlePinActivation);
  container.addEventListener("touchstart", handlePinActivation, { passive: false });
  container.addEventListener("click", handlePinActivation);
  container.addEventListener("keydown", handlePinKeyActivation);
  document.addEventListener("pointerdown", handlePinActivation, true);
  document.addEventListener("mousedown", handlePinActivation, true);
  document.addEventListener("touchstart", handlePinActivation, { capture: true, passive: false });
  document.addEventListener("click", handlePinActivation, true);
  document.addEventListener("keydown", handlePinKeyActivation, true);

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
  // One reusable InfoWindow — opens at the click point on each polygon.
  const infoWindow = new AMap.InfoWindow({
    isCustom: false,
    autoMove: true,
    offset: new AMap.Pixel(0, -4),
  });

  function clear() {
    if (overlays.length === 0) return;
    map.remove(overlays);
    overlays = [];
  }

  function polygonCentroidLngLat(path) {
    if (!Array.isArray(path) || path.length === 0) return null;
    let sx = 0;
    let sy = 0;
    for (const p of path) {
      sx += Number(p[0]);
      sy += Number(p[1]);
    }
    return [sx / path.length, sy / path.length];
  }

  function buildPopupHtml(props) {
    const district = props.districtName || "—";
    const community = props.communityName;
    const distance = props.matchDistanceM;
    const buildingName = props.buildingName;
    const osmId = props.osmId || "";
    const matchLine = community
      ? `<div class="atlas-osm-pop-row"><span>归属小区</span><strong>${escape(community)}</strong></div>` +
        (distance != null
          ? `<div class="atlas-osm-pop-row"><span>centroid 距离</span><strong>${Number(distance).toFixed(1)} m</strong></div>`
          : "")
      : `<div class="atlas-osm-pop-row atlas-osm-pop-unmatched"><span>归属小区</span><strong>未匹配（200m 内无目录小区）</strong></div>`;
    const buildingLine = buildingName
      ? `<div class="atlas-osm-pop-row"><span>OSM 名称</span><strong>${escape(buildingName)}</strong></div>`
      : "";
    return `
      <div class="atlas-osm-pop">
        <div class="atlas-osm-pop-title">楼栋足迹</div>
        <div class="atlas-osm-pop-row"><span>所属区</span><strong>${escape(district)}</strong></div>
        ${matchLine}
        ${buildingLine}
        <div class="atlas-osm-pop-row atlas-osm-pop-meta"><span>来源</span><strong>OpenStreetMap (${escape(osmId)})</strong></div>
      </div>
    `;
  }

  function escape(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]),
    );
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
      const ring = geom.coordinates[0];
      const poly = new AMap.Polygon({
        path: ring,
        strokeColor: "#7a8da0",
        strokeWeight: 0.6,
        strokeOpacity: 0.55,
        fillColor: props.communityId ? "#5d8aa8" : "#3b4754",
        fillOpacity: 0.18,
        bubble: true,
        zIndex: 5,
        cursor: "pointer",
      });
      poly.on("click", (event) => {
        const center = polygonCentroidLngLat(ring);
        const position = event?.lnglat || (center ? new AMap.LngLat(center[0], center[1]) : null);
        infoWindow.setContent(buildPopupHtml(props));
        if (position) infoWindow.open(map, position);
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

async function renderOpportunities({ AMap, map, store, state, opportunitySelections }) {
  const overlays = [];
  const markerOverlays = [];
  opportunitySelections.clear();
  const modeId = state.mode;
  const persisted = state && state.filters ? state.filters[modeId] : null;
  const filters =
    persisted && Object.keys(persisted).length > 0
      ? persisted
      : resolveDefaultFilters(modeId, (state && state.userPrefs) || null);
  const params = filtersToApiParams(filters);

  let payload;
  try {
    payload = await api.opportunities(params);
  } catch (err) {
    console.error("[atlas:map] opportunities load failed", err);
    return renderBuildings({ AMap, map, store });
  }

  for (const [index, item] of (payload.items || []).entries()) {
    const building = primaryBuildingFor(item);
    const position = positionForOpportunity(item);
    if (!position) continue;
    const geometry = building?.geometryJson;
    const yieldPct = numericYieldPct(item.yield ?? building?.yieldAvg);
    const color = yieldColorFor(yieldPct);
    const footprint = geometry ? createOverlay({ AMap, geometry, color }) : null;
    const selection = {
      type: "community",
      id: item.id,
      props: item,
      primaryBuildingId: item.primaryBuildingId || building?.id,
    };
    opportunitySelections.set(String(item.id), selection);
    if (footprint) {
      footprint.setExtData({ communityId: item.id, buildingId: building?.id, props: item });
      footprint.on("click", () => store.set({ selection }));
      overlays.push(footprint);
    }
    const marker = createOpportunityMarker({
      AMap,
      item,
      index,
      position,
      color,
      onSelect: () => store.set({ selection }),
    });
    marker.on("click", () => store.set({ selection }));
    overlays.push(marker);
    markerOverlays.push(marker);
  }

  if (overlays.length > 0) {
    map.add(overlays);
    fitMarkerOverlays(map, markerOverlays);
  }
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
      strokeWeight: 1.4,
      strokeOpacity: 0.85,
      fillColor: color,
      fillOpacity: 0.18,
      bubble: true,
      zIndex: 20,
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
      zIndex: 40,
    });
  }
  return null;
}

function createOpportunityMarker({ AMap, item, index, position, color, onSelect }) {
  const rank = index + 1;
  const label = rank <= 99 ? String(rank) : "99+";
  const content = document.createElement("button");
  content.type = "button";
  content.className = "atlas-map-pin";
  content.dataset.mapPinId = String(item.id);
  content.style.setProperty("--pin-color", color);
  content.title = item.name || "";
  content.setAttribute("aria-label", `定位 ${item.name || item.id || "机会点位"}`);
  content.setAttribute("aria-haspopup", "dialog");
  content.innerHTML = `<span>${escapeText(label)}</span>`;
  const select = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (typeof onSelect === "function") onSelect();
  };
  content.addEventListener("pointerdown", select);
  content.addEventListener("mousedown", select);
  content.addEventListener("touchstart", select, { passive: false });
  content.addEventListener("click", select);
  return new AMap.Marker({
    position,
    title: item.name || item.id || "机会点位",
    offset: new AMap.Pixel(-12, -30),
    zIndex: 80 + Math.max(0, 99 - Math.min(rank, 99)),
    content,
  });
}

function numericYieldPct(raw) {
  if (raw === null || raw === undefined) return null;
  const value = Number(raw);
  if (Number.isNaN(value)) return null;
  // Backend stores yield as a percentage already (e.g. 4.16 = 4.16%). Some
  // staged sources return a fraction (0.04). Detect by magnitude.
  return value < 1 ? value * 100 : value;
}

function mapKeyFor(state) {
  const mode = state?.mode || "yield";
  const filters = (state && state.filters && state.filters[mode]) || {};
  const prefsKey =
    state && state.userPrefs && state.userPrefs.updated_at
      ? state.userPrefs.updated_at
      : "";
  return `${mode}|${JSON.stringify(filters)}|${prefsKey}`;
}

function fitMarkerOverlays(map, markers) {
  if (!Array.isArray(markers) || markers.length === 0) return;
  if (markers.length === 1) {
    const position = markers[0].getPosition?.();
    if (position) map.setCenter(position);
    return;
  }
  map.setFitView(markers, false, [48, 48, 48, 48], 11);
}

function primaryBuildingFor(item) {
  const buildings = Array.isArray(item?.buildings) ? item.buildings : [];
  if (buildings.length === 0) return null;
  if (item.primaryBuildingId) {
    const found = buildings.find((building) => String(building.id) === String(item.primaryBuildingId));
    if (found) return found;
  }
  return buildings[0];
}

export function positionForOpportunity(item) {
  const building = primaryBuildingFor(item);
  const explicit = lngLatPair(building?.centerLng, building?.centerLat);
  if (explicit) return explicit;
  return centroidFromGeometry(building?.geometryJson);
}

export function centroidFromGeometry(geometry) {
  if (!geometry || geometry.type !== "Polygon" || !Array.isArray(geometry.coordinates)) {
    return null;
  }
  const ring = geometry.coordinates[0];
  if (!Array.isArray(ring) || ring.length === 0) return null;
  let lngSum = 0;
  let latSum = 0;
  let count = 0;
  for (const point of ring) {
    if (!Array.isArray(point) || point.length < 2) continue;
    const lng = Number(point[0]);
    const lat = Number(point[1]);
    if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue;
    lngSum += lng;
    latSum += lat;
    count += 1;
  }
  if (count === 0) return null;
  return [lngSum / count, latSum / count];
}

function lngLatPair(lngValue, latValue) {
  if (lngValue === null || lngValue === undefined || lngValue === "") return null;
  if (latValue === null || latValue === undefined || latValue === "") return null;
  const lng = Number(lngValue);
  const lat = Number(latValue);
  return Number.isFinite(lng) && Number.isFinite(lat) ? [lng, lat] : null;
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  }[c]));
}

function syncSelectionHighlight({ map, AMap, store }) {
  let lastMarker = null;
  store.subscribe((state) => {
    const sel = state.selection;
    if (lastMarker) {
      map.remove(lastMarker);
      lastMarker = null;
    }
    if (!sel || !["building", "community"].includes(sel.type)) return;
    const props = sel.props || {};
    const position =
      sel.type === "community"
        ? positionForOpportunity(props)
        : lngLatPair(props.center_lng, props.center_lat);
    if (!position) return;
    lastMarker = new AMap.CircleMarker({
      center: position,
      radius: 8,
      strokeColor: "#ffffff",
      strokeWeight: 2,
      fillColor: "#00d68f",
      fillOpacity: 0.0,
      bubble: false,
      zIndex: 120,
    });
    map.add(lastMarker);
    map.setCenter(position);
  });
}
