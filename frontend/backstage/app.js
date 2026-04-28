const amapState = {
  status: "fallback",
  map: null,
  districtSearch: null,
  districtBoundaryCache: new Map(),
  districtOverlays: [],
  communityOverlays: [],
  infoWindow: null,
  scriptPromise: null,
  hasInitialFit: false,
  modeNote: "未检测到 AMAP_API_KEY，当前只保留真地图容器。",
  transitionTimer: null,
  transitionToken: 0
};













function shouldInitializeMapExperienceForCurrentView() {
  return normalizeWorkspaceView(state.workspaceView) === "frontstage";
}

const state = {
  workspaceView: initialWorkspaceViewFromLocation(),
  districtFilter: "all",
  minYield: 0,
  maxBudget: 10000,
  minSamples: 1,
  granularity: "community",
  researchSearchQuery: "",
  researchSearchOpen: false,
  searchSelectedIndex: 0,
  selectedDistrictId: "pudong",
  selectedCommunityId: "zhangjiang-park",
  selectedBuildingId: null,
  selectedFloorNo: null,
  selectedImportRunId: initialOperationsSelectionParamFromLocation("opsImportRun"),
  selectedBaselineRunId: initialOperationsSelectionParamFromLocation("opsImportBaseline"),
  selectedGeoAssetRunId: initialOperationsSelectionParamFromLocation("opsGeoRun"),
  selectedGeoBaselineRunId: initialOperationsSelectionParamFromLocation("opsGeoBaseline"),
  selectedGeoTaskId: null,
  geoWorkOrderStatusFilter: "all",
  geoWorkOrderAssigneeFilter: "all",
  summary: null,
  opportunityItems: [],
  floorWatchlistItems: [],
  floorWatchlistLoading: false,
  browserSamplingPackItems: [],
  browserReviewInboxItems: [],
  browserReviewInboxSummary: {
    pendingQueueCount: 0,
    pendingTaskCount: 0,
    pendingDistrictCount: 0,
    oldestPendingAt: null,
    latestPendingAt: null,
  },
  mobileInspectorPanel: "detail",
  filterPanelTab: "scope",
  researchBackstageTab: initialBackstageTabFromLocation(),
  operationsHistoryTab: initialOperationsHistoryTabFromLocation(),
  operationsDetailTab: initialOperationsDetailTabFromLocation(),
  operationsQualityTab: initialOperationsQualityTabFromLocation(),
  selectedBrowserSamplingTaskId: null,
  selectedCommunityDetail: null,
  selectedBuildingDetail: null,
  selectedFloorDetail: null,
  selectedImportRunDetail: null,
  selectedGeoAssetRunDetail: null,
  selectedBrowserCaptureRunId: null,
  selectedBrowserCaptureRunDetail: null,
  selectedBrowserCaptureReviewQueueId: null,
  selectedBrowserCaptureReviewQueueIds: [],
  mapWaypoint: null,
  mapCommunities: [],
  buildingGeoFeatures: [],
  floorGeoFeatures: [],
  geoAssetSource: "fallback",
  opsMessage: null,
  opsMessageTone: "info",
  opsMessageContext: "import",
  busyReferencePersistRunId: null,
  busyBootstrapDatabase: false,
  busyMetricsRefresh: false,
  busyMetricsRefreshMode: null,
  busyPersistRunId: null,
  busyReviewQueueId: null,
  busyBrowserCaptureReviewQueueId: null,
  busyBrowserCaptureReviewBatch: false,
  busyAnchorCommunityId: null,
  busyGeoPersistRunId: null,
  busyGeoTaskId: null,
  busyGeoWorkOrderTaskId: null,
  busyGeoWorkOrderId: null,
  busyBrowserSamplingSubmit: false,
  busyBrowserCaptureRunId: null,
  lastBrowserCaptureSubmission: null,
  optimisticBrowserCaptureRunSummary: null,
  lastBrowserCaptureReviewAction: null,
  anchorEditorCommunityId: null,
  browserCaptureDraft: {
    sale: {
      sourceListingId: "",
      url: "",
      publishedAt: "",
      rawText: "",
      note: ""
    },
    rent: {
      sourceListingId: "",
      url: "",
      publishedAt: "",
      rawText: "",
      note: ""
    }
  },
  anchorDraft: {
    lng: "",
    lat: "",
    note: "",
    aliasHint: "",
    sourceLabel: "manual_override_gcj02"
  }
};

let mapRequestId = 0;
let detailRequestId = 0;
let buildingRequestId = 0;
let floorRequestId = 0;
let amapRenderRequestId = 0;
let geoAssetRequestId = 0;
let floorWatchlistRequestId = 0;
let mapWaypointTimer = null;













function seedAnchorDraft(community) {
  const preview = communityAnchorPreview(community);
  state.anchorDraft = {
    lng: preview?.centerLng != null ? String(preview.centerLng) : community?.centerLng != null ? String(community.centerLng) : "",
    lat: preview?.centerLat != null ? String(preview.centerLat) : community?.centerLat != null ? String(community.centerLat) : "",
    note: "",
    aliasHint: "",
    sourceLabel: "manual_override_gcj02"
  };
}

function openAnchorManualEditor(community) {
  if (!community) {
    return;
  }
  state.anchorEditorCommunityId = community.id;
  seedAnchorDraft(community);
}

function closeAnchorManualEditor() {
  state.anchorEditorCommunityId = null;
  state.anchorDraft = {
    lng: "",
    lat: "",
    note: "",
    aliasHint: "",
    sourceLabel: "manual_override_gcj02"
  };
}

async function init() {
  await Promise.all([loadRuntimeConfig(), loadBootstrapData()]);
  applyDataModeDefaults();
  buildFilters();
  setGranularity(state.granularity);
  renderPipeline();
  renderSchemas();
  renderStrategy();
  render();
  scheduleUiHydrationRetry();
  attachEvents();
  scheduleMapInitializationRetry();
  void refreshData()
    .then(() => {
      render();
      scheduleUiHydrationRetry();
      scheduleMapInitializationRetry();
    })
    .catch(() => {
      render();
      scheduleUiHydrationRetry();
      scheduleMapInitializationRetry();
    });
  void refreshOperationsWorkbench({ reloadFloor: false })
    .then(() => {
      render();
      scheduleUiHydrationRetry();
      scheduleMapInitializationRetry();
    })
    .catch(() => {
      render();
      scheduleUiHydrationRetry();
      scheduleMapInitializationRetry();
    });
  if (shouldInitializeMapExperienceForCurrentView()) {
    void initializeMapExperience()
      .then(() => {
        render();
        scheduleUiHydrationRetry();
      })
      .catch(() => {
        render();
        scheduleUiHydrationRetry();
      });
  } else {
    setMapMode("standby", "当前打开的是研究后台。切回展示台后再初始化前台地图与区块图层。");
    render();
  }
}

async function loadRuntimeConfig() {
  try {
    const response = await fetch("/api/runtime-config", {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Runtime config failed with ${response.status}`);
    }
    runtimeConfig = await response.json();
  } catch (error) {
    runtimeConfig = {
      amapApiKey: null,
      hasAmapKey: false,
      amapSecurityJsCode: null,
      hasAmapSecurityJsCode: false,
      hasPostgresDsn: false,
      postgresDsnMasked: null,
      databaseConnected: false,
      databaseReadable: false,
      databaseSeeded: false,
      latestBootstrapAt: null,
      mockEnabled: false,
      activeDataMode: "empty",
      hasRealData: false,
      stagedArtifactsPresent: false,
      stagedReferenceRunCount: 0,
      stagedImportRunCount: 0,
      stagedGeoRunCount: 0,
      stagedMetricsRunCount: 0
    };
  }
}

async function loadBootstrapData() {
  try {
    const response = await fetch("/api/bootstrap", {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Bootstrap failed with ${response.status}`);
    }
    const payload = await response.json();
    districts = hydrateDistrictsPayload(payload.districts ?? (canUseDemoFallback() ? fallbackDistricts : []));
    pipelineSteps = payload.pipeline_steps ?? fallbackPipelineSteps;
    schemas = payload.schemas ?? fallbackSchemas;
    systemStrategy = payload.system_strategy ?? null;
    dataSources = payload.data_sources ?? [];
    operationsOverview = payload.operations_overview ?? emptyOperationsOverview;
  } catch (error) {
    districts = hydrateDistrictsPayload(canUseDemoFallback() ? fallbackDistricts : []);
    pipelineSteps = fallbackPipelineSteps;
    schemas = fallbackSchemas;
    systemStrategy = null;
    dataSources = [];
    operationsOverview = canUseDemoFallback() ? fallbackOperationsOverview : emptyOperationsOverview;
  }
}

async function loadOperationsOverview() {
  try {
    const response = await fetch("/api/ops/overview", {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Ops overview failed with ${response.status}`);
    }
    operationsOverview = await response.json();
    if (state.optimisticBrowserCaptureRunSummary?.runId) {
      upsertBrowserCaptureRunSummary(state.optimisticBrowserCaptureRunSummary);
    }
  } catch (error) {
    operationsOverview = canUseDemoFallback() ? fallbackOperationsOverview : emptyOperationsOverview;
  }
}

async function refreshOperationsWorkbench({ reloadFloor = false } = {}) {
  await loadOperationsOverview();
  ensureImportRunSelection();
  ensureGeoAssetRunSelection();
  syncOperationsBackstageLocationIfNeeded();
  if (
    state.selectedBrowserCaptureRunId &&
    !(effectiveOperationsOverview().browserCaptureRuns ?? []).some((item) => item.runId === state.selectedBrowserCaptureRunId)
  ) {
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
    state.selectedBrowserCaptureReviewQueueId = null;
  }
  // Render immediately after ops overview refresh so recent run lists do not lag
  // behind slower import/floor detail hydration.
  render();
  scheduleUiHydrationRetry();
  await Promise.all([
    loadSelectedImportRunDetail({ reloadFloorWatchlist: false }),
    loadFloorWatchlist()
  ]);
  void Promise.allSettled([
    loadSelectedGeoAssetRunDetail(),
    state.selectedBrowserCaptureRunId ? loadSelectedBrowserCaptureRunDetail(state.selectedBrowserCaptureRunId) : Promise.resolve(),
    reloadFloor && state.selectedBuildingId && state.selectedFloorNo ? loadSelectedFloorDetail() : Promise.resolve()
  ]).then(() => {
    render();
    scheduleUiHydrationRetry();
  });
}




async function loadSelectedImportRunDetail({ reloadFloorWatchlist = true } = {}) {
  if (!state.selectedImportRunId) {
    state.selectedImportRunDetail = null;
    if (reloadFloorWatchlist) {
      await loadFloorWatchlist();
    }
    return;
  }

  try {
    const params = new URLSearchParams();
    if (state.selectedBaselineRunId) {
      params.set("baseline_run_id", state.selectedBaselineRunId);
    }
    const response = await fetch(`/api/import-runs/${state.selectedImportRunId}${params.toString() ? `?${params.toString()}` : ""}`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Import run detail failed with ${response.status}`);
    }
    state.selectedImportRunDetail = await response.json();
  } catch (error) {
    state.selectedImportRunDetail = buildFallbackImportRunDetail(state.selectedImportRunId);
  }
  if (reloadFloorWatchlist) {
    await loadFloorWatchlist();
  }
}

async function loadSelectedGeoAssetRunDetail() {
  if (!state.selectedGeoAssetRunId) {
    state.selectedGeoAssetRunDetail = null;
    return;
  }

  try {
    const params = new URLSearchParams();
    if (state.selectedGeoBaselineRunId) {
      params.set("baseline_run_id", state.selectedGeoBaselineRunId);
    }
    const response = await fetch(
      `/api/geo-assets/runs/${state.selectedGeoAssetRunId}${params.toString() ? `?${params.toString()}` : ""}`,
      {
        headers: { Accept: "application/json" }
      }
    );
    if (!response.ok) {
      throw new Error(`Geo asset run detail failed with ${response.status}`);
    }
    state.selectedGeoAssetRunDetail = await response.json();
  } catch (error) {
    state.selectedGeoAssetRunDetail = buildFallbackGeoAssetRunDetail(
      state.selectedGeoAssetRunId,
      state.selectedGeoBaselineRunId
    );
  }
  normalizeGeoWorkOrderFilters();
}



async function loadFloorWatchlist() {
  const requestId = ++floorWatchlistRequestId;
  state.floorWatchlistLoading = true;
  const params = new URLSearchParams({
    district: state.districtFilter,
    min_yield: String(state.minYield),
    max_budget: String(state.maxBudget),
    min_samples: String(state.minSamples)
  });
  if (state.selectedImportRunId) {
    params.set("run_id", state.selectedImportRunId);
  }
  if (state.selectedBaselineRunId) {
    params.set("baseline_run_id", state.selectedBaselineRunId);
  }

  try {
    const response = await fetch(`/api/floor-watchlist?${params.toString()}`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Floor watchlist failed with ${response.status}`);
    }
    const payload = await response.json();
    if (requestId !== floorWatchlistRequestId) {
      return;
    }
    state.floorWatchlistItems = payload.items ?? [];
    state.floorWatchlistLoading = false;
  } catch (error) {
    if (requestId !== floorWatchlistRequestId) {
      return;
    }
    state.floorWatchlistItems = canUseDemoFallback() ? getFallbackFloorWatchlistItems() : [];
    state.floorWatchlistLoading = false;
  }

  if (requestId !== floorWatchlistRequestId) {
    return;
  }
  await loadGeoAssets();
}

async function fetchGeoAssetCollection(url) {
  const response = await fetch(url, {
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`Geo asset request failed with ${response.status}`);
  }
  const payload = await response.json();
  return Array.isArray(payload?.features) ? payload.features : [];
}

async function loadGeoAssets() {
  const requestId = ++geoAssetRequestId;
  const buildingParams = new URLSearchParams({
    district: state.districtFilter,
    focus_scope: state.districtFilter === "all" ? "priority" : "all",
    geometry_quality: "all"
  });
  if (state.selectedGeoAssetRunId) {
    buildingParams.set("geo_run_id", state.selectedGeoAssetRunId);
  }
  const [buildingResult, floorResult] = await Promise.allSettled([
    fetchGeoAssetCollection(`/api/map/buildings?${buildingParams.toString()}`),
    fetchGeoAssetCollection(`/api/geo-assets/floor-watchlist?${buildFloorWatchlistExportQuery()}`)
  ]);

  if (requestId !== geoAssetRequestId) {
    return;
  }

  state.buildingGeoFeatures = buildingResult.status === "fulfilled" ? buildingResult.value : [];
  state.floorGeoFeatures = floorResult.status === "fulfilled" ? floorResult.value : [];
  state.geoAssetSource =
    state.buildingGeoFeatures.length || state.floorGeoFeatures.length
      ? "api"
      : currentDataMode() === "database"
        ? "gap"
        : canUseDemoFallback()
          ? "fallback"
          : "empty";
}

async function initializeMapExperience() {
  if (!runtimeConfig.hasAmapKey || !runtimeConfig.amapApiKey) {
    setMapMode("fallback", "未检测到 AMAP_API_KEY，当前仅保留真地图容器。配置 key 后即可启用高德底图。");
    return;
  }

  setMapMode(
    "loading",
    runtimeConfig.hasAmapSecurityJsCode
      ? "正在加载高德底图与行政区图层能力。已检测到 Web 端安全密钥。"
      : "正在加载高德底图与行政区图层能力。请确认 key、白名单与安全密钥配置正确。"
  );

  try {
    await loadAmapScript(runtimeConfig.amapApiKey, runtimeConfig.amapSecurityJsCode);
    createAmapInstance();
    requestAnimationFrame(() => {
      amapState.map?.resize?.();
    });
    setMapMode("ready", "当前为高德真地图模式。区块边界、小区点位和楼栋下钻会同步到真实底图。");
  } catch (error) {
    setMapMode("error", "高德底图加载失败。请检查 key、域名白名单、安全密钥或网络环境。");
  }
}

function scheduleMapInitializationRetry() {
  if (!runtimeConfig?.hasAmapKey || !runtimeConfig?.amapApiKey) {
    return;
  }
  if (!shouldInitializeMapExperienceForCurrentView()) {
    if (
      !amapState.map &&
      !amapState.scriptPromise &&
      amapState.status !== "loading" &&
      amapState.status !== "ready" &&
      amapState.status !== "standby"
    ) {
      setMapMode("standby", "当前打开的是研究后台。切回展示台后再初始化前台地图与区块图层。");
    }
    return;
  }
  if (amapState.map || amapState.scriptPromise || amapState.status === "loading" || amapState.status === "ready") {
    return;
  }
  requestAnimationFrame(() => {
    if (!runtimeConfig?.hasAmapKey || !runtimeConfig?.amapApiKey) {
      return;
    }
    if (!shouldInitializeMapExperienceForCurrentView()) {
      if (
        !amapState.map &&
        !amapState.scriptPromise &&
        amapState.status !== "loading" &&
        amapState.status !== "ready" &&
        amapState.status !== "standby"
      ) {
        setMapMode("standby", "当前打开的是研究后台。切回展示台后再初始化前台地图与区块图层。");
      }
      return;
    }
    if (amapState.map || amapState.scriptPromise || amapState.status === "loading" || amapState.status === "ready") {
      return;
    }
    void initializeMapExperience()
      .then(() => {
        render();
      })
      .catch(() => {
        render();
      });
  });
}

function scheduleUiHydrationRetry() {
  requestAnimationFrame(() => {
    const summaryRendered = Boolean(summaryGrid?.textContent?.trim());
    const noteRendered = Boolean(mapNote?.textContent?.trim() && !mapNote.textContent.includes("交互原型示意"));
    const hasStateSummary = Boolean(state?.summary && typeof state.summary.communityCount === "number");
    const hasMapData =
      Array.isArray(state?.mapCommunities) ||
      Array.isArray(state?.opportunityItems) ||
      Array.isArray(state?.floorWatchlistItems);

    if ((hasStateSummary || hasMapData) && (!summaryRendered || !noteRendered)) {
      render();
    }
    scheduleMapInitializationRetry();
  });
}

function setMapMode(mode, noteText) {
  amapState.status = mode;
  amapState.modeNote = noteText;
  const labelMap = {
    loading: "地图加载中",
    ready: "AMap Live",
    standby: "前台待启用",
    fallback: "地图待接入",
    error: "地图异常"
  };

  mapModeBadge.textContent = labelMap[mode] ?? "地图待接入";
  mapModeBadge.style.borderColor = mode === "ready" ? "rgba(117, 240, 207, 0.6)" : "rgba(151, 191, 226, 0.14)";
  mapModeBadge.style.background =
    mode === "ready"
      ? "linear-gradient(180deg, rgba(117, 240, 207, 0.2), rgba(117, 240, 207, 0.08))"
      : "rgba(255, 255, 255, 0.04)";

  amapContainer.dataset.mapStage = mode;
  amapContainer.setAttribute("aria-busy", mode === "loading" ? "true" : "false");
  updateMapNote();
}

function loadAmapScript(apiKey, securityJsCode) {
  if (window.AMap) {
    return Promise.resolve(window.AMap);
  }

  if (amapState.scriptPromise) {
    return amapState.scriptPromise;
  }

  if (securityJsCode) {
    window._AMapSecurityConfig = {
      securityJsCode
    };
  }

  amapState.scriptPromise = new Promise((resolve, reject) => {
    const timeoutId = window.setTimeout(() => {
      reject(new Error("AMap script timeout"));
    }, 8000);
    const existing = document.querySelector('script[data-amap-loader="true"]');
    if (existing) {
      existing.addEventListener("load", () => {
        window.clearTimeout(timeoutId);
        resolve(window.AMap);
      });
      existing.addEventListener("error", () => {
        window.clearTimeout(timeoutId);
        reject(new Error("AMap script failed"));
      });
      return;
    }

    const script = document.createElement("script");
    script.async = true;
    script.defer = true;
    script.dataset.amapLoader = "true";
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(apiKey)}&plugin=AMap.DistrictSearch,AMap.Scale,AMap.ToolBar`;
    script.onload = () => {
      window.clearTimeout(timeoutId);
      if (window.AMap) {
        resolve(window.AMap);
        return;
      }
      reject(new Error("AMap unavailable after script load"));
    };
    script.onerror = () => {
      window.clearTimeout(timeoutId);
      reject(new Error("AMap script failed"));
    };
    document.head.appendChild(script);
  });

  return amapState.scriptPromise;
}

function createAmapInstance() {
  if (!window.AMap || amapState.map) {
    return;
  }

  amapState.map = new window.AMap.Map("amapContainer", {
    center: [121.4737, 31.2304],
    zoom: 10.8,
    viewMode: "2D",
    resizeEnable: true,
    zooms: [8, 18],
    mapStyle: "amap://styles/normal",
    showLabel: true
  });
  amapState.map.setCity?.("上海");
  amapState.map.setZoomAndCenter?.(10.8, [121.4737, 31.2304]);
  window.setTimeout(() => {
    amapState.map?.resize?.();
  }, 80);

  amapState.infoWindow = new window.AMap.InfoWindow({
    isCustom: true,
    offset: new window.AMap.Pixel(0, -20),
    closeWhenClickMap: true
  });

  if (window.AMap.Scale) {
    amapState.map.addControl(new window.AMap.Scale());
  }
  if (window.AMap.ToolBar) {
    amapState.map.addControl(new window.AMap.ToolBar({ position: "RB" }));
  }
  if (window.AMap.DistrictSearch) {
    amapState.districtSearch = new window.AMap.DistrictSearch({
      level: "district",
      extensions: "all",
      subdistrict: 0,
      showbiz: false
    });
  }
}

async function refreshData(
  {
    backgroundHydration = false,
    preserveBrowserSamplingTaskId = state.selectedBrowserSamplingTaskId,
  } = {}
) {
  const requestId = ++mapRequestId;
  const query = buildExportQuery();
  const communityQuery = new URLSearchParams();
  communityQuery.set("district", state.districtFilter);
  communityQuery.set("sample_status", "all");
  communityQuery.set("focus_scope", "all");

  try {
    const [mapResponse, communityResponse, opportunitiesResponse, browserPackResponse, browserReviewInboxResponse] = await Promise.all([
      fetch(`/api/map/districts?${query}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/map/communities?${communityQuery.toString()}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/opportunities?${query}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/browser-sampling-pack?${query}`, { headers: { Accept: "application/json" } }),
      fetch("/api/browser-review-inbox?limit=40", { headers: { Accept: "application/json" } }),
    ]);

    if (!mapResponse.ok || !communityResponse.ok || !opportunitiesResponse.ok || !browserPackResponse.ok || !browserReviewInboxResponse.ok) {
      throw new Error("API data refresh failed");
    }

    const [mapPayload, communityPayload, opportunitiesPayload, browserPackPayload, browserReviewInboxPayload] = await Promise.all([
      mapResponse.json(),
      communityResponse.json(),
      opportunitiesResponse.json(),
      browserPackResponse.json(),
      browserReviewInboxResponse.json(),
    ]);
    if (requestId !== mapRequestId) {
      return;
    }

    districts = hydrateDistrictsPayload(mapPayload.districts ?? []);
    mapCommunities = (communityPayload.items ?? []).map((item) =>
      hydrateCommunity({
        ...item,
        id: item.community_id,
        districtId: item.district_id,
        districtName: item.district_name,
        name: item.name,
        x: item.center_lng != null && item.center_lat != null ? normalizeLonLatToSvg(item.center_lng, item.center_lat).x : 380,
        y: item.center_lng != null && item.center_lat != null ? normalizeLonLatToSvg(item.center_lng, item.center_lat).y : 260,
        avgPriceWan: item.yield_pct ? 0 : 0,
        monthlyRent: 0,
        yield: Number(item.yield_pct ?? 0),
        score: Number(item.opportunity_score ?? 0),
        sample: Number(item.sample_size ?? 0),
        buildingCount: Number(item.building_count ?? 0),
        note: item.sample_status === "dictionary_only" ? "已挂图，待补真实 listing 样本。" : "当前已有研究样本。",
        buildings: []
      })
    );
    state.mapCommunities = mapCommunities;
    state.summary = mapPayload.summary ?? null;
    state.opportunityItems = (opportunitiesPayload.items ?? []).map(hydrateCommunity);
    state.browserSamplingPackItems = browserPackPayload.items ?? [];
    if (
      preserveBrowserSamplingTaskId &&
      (state.browserSamplingPackItems ?? []).some((item) => item?.taskId === preserveBrowserSamplingTaskId)
    ) {
      state.selectedBrowserSamplingTaskId = preserveBrowserSamplingTaskId;
    }
    state.browserReviewInboxItems = browserReviewInboxPayload.items ?? [];
    state.browserReviewInboxSummary = browserReviewInboxPayload.summary ?? {
      pendingQueueCount: 0,
      pendingTaskCount: 0,
      pendingDistrictCount: 0,
      oldestPendingAt: null,
      latestPendingAt: null,
    };
    ensureBrowserSamplingTaskSelection();
    render();
    scheduleUiHydrationRetry();
    scheduleMapInitializationRetry();
  } catch (error) {
    districts = hydrateDistrictsPayload(canUseDemoFallback() ? fallbackDistricts : []);
    mapCommunities = canUseDemoFallback() ? getFilteredCommunities() : [];
    state.mapCommunities = mapCommunities;
    state.summary = currentDataMode() === "empty"
      ? {
          communityCount: 0,
          avgYield: 0,
          avgBudget: 0,
          avgMonthlyRent: 0,
          bestScore: 0
        }
      : null;
    state.opportunityItems = canUseDemoFallback() ? getFallbackOpportunityItems() : [];
    state.browserSamplingPackItems = [];
    state.browserReviewInboxItems = [];
    state.browserReviewInboxSummary = {
      pendingQueueCount: 0,
      pendingTaskCount: 0,
      pendingDistrictCount: 0,
      oldestPendingAt: null,
      latestPendingAt: null,
    };
    ensureBrowserSamplingTaskSelection();
    render();
    scheduleUiHydrationRetry();
    scheduleMapInitializationRetry();
  }

  buildFilters();
  ensureValidSelection();
  if (backgroundHydration) {
    void Promise.allSettled([loadSelectedCommunityDetail(), loadFloorWatchlist()]).then(() => {
      render();
      scheduleUiHydrationRetry();
      scheduleMapInitializationRetry();
    });
    render();
    scheduleUiHydrationRetry();
    scheduleMapInitializationRetry();
    return;
  }
  await loadSelectedCommunityDetail();
  await loadFloorWatchlist();
  render();
  scheduleUiHydrationRetry();
  scheduleMapInitializationRetry();
}

function getFallbackOpportunityItems() {
  return getFilteredCommunities()
    .slice()
    .sort((left, right) => right.score - left.score)
    .map(hydrateCommunity);
}

function getFallbackFloorWatchlistItems() {
  return [
    {
      communityId: "qibao-yunting",
      communityName: "七宝云庭",
      districtId: "minhang",
      districtName: "闵行区",
      buildingId: "qibao-yunting-b2",
      buildingName: "9幢",
      floorNo: 15,
      latestYieldPct: 2.89,
      yieldDeltaSinceFirst: 0.1,
      latestPairCount: 1,
      observedRuns: 2,
      totalPairCount: 2,
      latestBatchName: "pudong-demo-2026-04-12",
      latestCreatedAt: "2026-04-12T10:20:30+08:00",
      baselineBatchName: "pudong-demo-2026-04-11",
      baselineCreatedAt: "2026-04-11T22:33:36+08:00",
      windowYieldDeltaPct: 0.1,
      windowPairCountDelta: 0,
      latestStatus: "improved",
      latestStatusLabel: "回报抬升",
      persistenceScore: 92,
      trendLabel: "持续走强"
    },
    {
      communityId: "zhangjiang-park",
      communityName: "张江汤臣豪园",
      districtId: "pudong",
      districtName: "浦东新区",
      buildingId: "zhangjiang-park-b2",
      buildingName: "5号楼",
      floorNo: 17,
      latestYieldPct: 2.92,
      yieldDeltaSinceFirst: 0.07,
      latestPairCount: 1,
      observedRuns: 2,
      totalPairCount: 2,
      latestBatchName: "pudong-demo-2026-04-12",
      latestCreatedAt: "2026-04-12T10:20:30+08:00",
      baselineBatchName: "pudong-demo-2026-04-11",
      baselineCreatedAt: "2026-04-11T22:33:36+08:00",
      windowYieldDeltaPct: 0.07,
      windowPairCountDelta: 0,
      latestStatus: "stable",
      latestStatusLabel: "基本持平",
      persistenceScore: 88,
      trendLabel: "稳定高收益"
    },
    {
      communityId: "qibao-yunting",
      communityName: "七宝云庭",
      districtId: "minhang",
      districtName: "闵行区",
      buildingId: "qibao-yunting-b2",
      buildingName: "9幢",
      floorNo: 11,
      latestYieldPct: 2.83,
      yieldDeltaSinceFirst: null,
      latestPairCount: 1,
      observedRuns: 1,
      totalPairCount: 1,
      latestBatchName: "pudong-demo-2026-04-12",
      latestCreatedAt: "2026-04-12T10:20:30+08:00",
      baselineBatchName: null,
      baselineCreatedAt: null,
      windowYieldDeltaPct: null,
      windowPairCountDelta: null,
      latestStatus: "new",
      latestStatusLabel: "新增楼层",
      persistenceScore: 84,
      trendLabel: "新增样本"
    }
  ];
}

function buildFilters() {
  minYieldFilter.min = "0";
  minYieldFilter.max = "5";
  minYieldFilter.step = "0.1";
  maxBudgetFilter.min = "300";
  maxBudgetFilter.max = "10000";
  maxBudgetFilter.step = "50";
  minSamplesFilter.min = "1";
  minSamplesFilter.max = "60";
  minSamplesFilter.step = "1";
  const districtOptions = districtDirectory();
  districtFilter.innerHTML = [
    '<option value="all">全上海</option>',
    ...districtOptions.map((district) => `<option value="${district.id}">${district.name}</option>`)
  ].join("");
  districtFilter.value = state.districtFilter;
  minYieldFilter.value = String(state.minYield);
  maxBudgetFilter.value = String(state.maxBudget);
  minSamplesFilter.value = String(state.minSamples);
  minYieldValue.textContent = `${state.minYield.toFixed(1)}%`;
  maxBudgetValue.textContent = `${state.maxBudget} 万`;
  minSamplesValue.textContent = `${state.minSamples} 套`;
}

function setGranularity(granularity) {
  state.granularity = granularity;
  granularityGroup
    .querySelectorAll("button")
    .forEach((item) => {
      const active = item.dataset.granularity === granularity;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
  renderMapChromeState();
  triggerMapTransition("granularity");
}

function renderGlobalFeedback() {
  if (!globalFeedback) {
    return;
  }
  const show = Boolean(state.opsMessage && state.opsMessageContext === "global");
  globalFeedback.hidden = !show;
  globalFeedback.className = `ops-feedback global-feedback ${state.opsMessageTone ?? "info"}`;
  globalFeedback.textContent = show ? state.opsMessage : "";
}

function renderInspectorPanels() {
  document.querySelectorAll("[data-inspector-panel]").forEach((panel) => {
    const key = panel.dataset.inspectorPanel;
    const expanded = state.mobileInspectorPanel === key;
    panel.classList.toggle("is-collapsed", !expanded);
    const button = panel.querySelector("[data-inspector-toggle]");
    if (button) {
      button.setAttribute("aria-expanded", String(expanded));
      button.textContent = expanded ? "收起" : "展开";
    }
  });
}

function syncWorkspaceViewLocation() {
  if (typeof window === "undefined") {
    return;
  }
  const url = new URL(window.location.href);
  if (state.workspaceView === "backstage") {
    url.searchParams.set("view", "backstage");
    url.searchParams.set("backstage", normalizeBackstageTab(state.researchBackstageTab));
    if (normalizeBackstageTab(state.researchBackstageTab) === "operations") {
      url.searchParams.set("opsHistory", normalizeOperationsHistoryTab(state.operationsHistoryTab));
      url.searchParams.set("opsDetail", normalizeOperationsDetailTab(state.operationsDetailTab));
      url.searchParams.set("opsQuality", normalizeOperationsQualityTab(state.operationsQualityTab));
      if (state.selectedImportRunId) {
        url.searchParams.set("opsImportRun", state.selectedImportRunId);
      } else {
        url.searchParams.delete("opsImportRun");
      }
      if (state.selectedBaselineRunId) {
        url.searchParams.set("opsImportBaseline", state.selectedBaselineRunId);
      } else {
        url.searchParams.delete("opsImportBaseline");
      }
      if (state.selectedGeoAssetRunId) {
        url.searchParams.set("opsGeoRun", state.selectedGeoAssetRunId);
      } else {
        url.searchParams.delete("opsGeoRun");
      }
      if (state.selectedGeoBaselineRunId) {
        url.searchParams.set("opsGeoBaseline", state.selectedGeoBaselineRunId);
      } else {
        url.searchParams.delete("opsGeoBaseline");
      }
    } else {
      url.searchParams.delete("opsHistory");
      url.searchParams.delete("opsDetail");
      url.searchParams.delete("opsQuality");
      url.searchParams.delete("opsImportRun");
      url.searchParams.delete("opsImportBaseline");
      url.searchParams.delete("opsGeoRun");
      url.searchParams.delete("opsGeoBaseline");
    }
  } else {
    url.searchParams.delete("view");
    url.searchParams.delete("backstage");
    url.searchParams.delete("opsHistory");
    url.searchParams.delete("opsDetail");
    url.searchParams.delete("opsQuality");
    url.searchParams.delete("opsImportRun");
    url.searchParams.delete("opsImportBaseline");
    url.searchParams.delete("opsGeoRun");
    url.searchParams.delete("opsGeoBaseline");
  }
  const nextUrl = `${url.pathname}${url.search}${url.hash}`;
  const currentUrl = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (nextUrl !== currentUrl) {
    window.history.replaceState({}, "", nextUrl);
  }
}

function requestMapResizeSoon() {
  if (typeof window === "undefined" || typeof amapState.map?.resize !== "function") {
    return;
  }
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      amapState.map?.resize?.();
    });
  });
}

function setWorkspaceView(
  nextView,
  {
    backstageTab = null,
    operationsHistoryTab = null,
    operationsDetailTab = null,
    operationsQualityTab = null
  } = {}
) {
  const normalizedView = normalizeWorkspaceView(nextView);
  const normalizedBackstageTab = normalizeBackstageTab(backstageTab ?? state.researchBackstageTab);
  const normalizedOperationsHistoryTab =
    operationsHistoryTab == null ? state.operationsHistoryTab : normalizeOperationsHistoryTab(operationsHistoryTab);
  const normalizedOperationsDetailTab =
    operationsDetailTab == null ? state.operationsDetailTab : normalizeOperationsDetailTab(operationsDetailTab);
  const normalizedOperationsQualityTab =
    operationsQualityTab == null ? state.operationsQualityTab : normalizeOperationsQualityTab(operationsQualityTab);
  const didViewChange = normalizedView !== state.workspaceView;
  const didTabChange = normalizedView === "backstage" && normalizedBackstageTab !== state.researchBackstageTab;
  const didOperationsTabChange =
    normalizedView === "backstage"
    && normalizedBackstageTab === "operations"
    && (
      normalizedOperationsHistoryTab !== state.operationsHistoryTab
      || normalizedOperationsDetailTab !== state.operationsDetailTab
      || normalizedOperationsQualityTab !== state.operationsQualityTab
    );
  if (!didViewChange && !didTabChange && !didOperationsTabChange) {
    return;
  }
  state.workspaceView = normalizedView;
  if (normalizedView === "backstage") {
    state.researchBackstageTab = normalizedBackstageTab;
    if (normalizedBackstageTab === "operations") {
      state.operationsHistoryTab = normalizedOperationsHistoryTab;
      state.operationsDetailTab = normalizedOperationsDetailTab;
      state.operationsQualityTab = normalizedOperationsQualityTab;
    }
  }
  syncWorkspaceViewLocation();
  render();
  if (normalizedView === "frontstage") {
    scheduleMapInitializationRetry();
    requestMapResizeSoon();
  } else {
    scheduleMapInitializationRetry();
  }
}

function renderWorkspaceView() {
  const currentView = normalizeWorkspaceView(state.workspaceView);
  state.workspaceView = currentView;
  if (appShell) {
    appShell.dataset.workspaceView = currentView;
  }
  if (overviewBand) {
    overviewBand.hidden = currentView !== "frontstage";
  }
  if (frontstageWorkspace) {
    frontstageWorkspace.hidden = currentView !== "frontstage";
  }
  if (backstageWorkspace) {
    backstageWorkspace.hidden = currentView !== "backstage";
  }

  document.querySelectorAll("[data-workspace-view]").forEach((button) => {
    const key = normalizeWorkspaceView(button.dataset.workspaceView);
    const isActive = key === currentView;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      setWorkspaceView(key, {
        backstageTab: key === "backstage" ? state.researchBackstageTab : null
      });
    };
  });
}

function renderResearchBackstage() {
  const availableTabs = backstageTabs;
  if (!availableTabs.includes(state.researchBackstageTab)) {
    state.researchBackstageTab = "operations";
  }

  document.querySelectorAll("[data-research-backstage-tab]").forEach((button) => {
    const key = button.dataset.researchBackstageTab;
    const isActive = key === state.researchBackstageTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      if (!availableTabs.includes(key) || key === state.researchBackstageTab) {
        return;
      }
      state.researchBackstageTab = key;
      if (state.workspaceView === "backstage") {
        syncWorkspaceViewLocation();
      }
      renderResearchBackstage();
    };
  });

  document.querySelectorAll("[data-research-panel]").forEach((panel) => {
    const isActive = panel.dataset.researchPanel === state.researchBackstageTab;
    panel.hidden = !isActive;
    panel.classList.toggle("is-active-backstage", isActive);
  });
}

function syncOperationsBackstageLocationIfNeeded() {
  if (
    normalizeWorkspaceView(state.workspaceView) === "backstage"
    && normalizeBackstageTab(state.researchBackstageTab) === "operations"
  ) {
    syncWorkspaceViewLocation();
  }
}

function renderFilterPanel() {
  const availableTabs = ["scope", "threshold", "display"];
  if (!availableTabs.includes(state.filterPanelTab)) {
    state.filterPanelTab = "scope";
  }

  document.querySelectorAll("[data-filter-tab]").forEach((button) => {
    const key = button.dataset.filterTab;
    const isActive = key === state.filterPanelTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      if (!availableTabs.includes(key) || key === state.filterPanelTab) {
        return;
      }
      state.filterPanelTab = key;
      renderFilterPanel();
    };
  });

  document.querySelectorAll("[data-filter-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.filterPanel !== state.filterPanelTab;
  });
}

function bindKeyboardActivation(element, callback) {
  if (!element) {
    return;
  }
  element.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }
    if (event.target.closest("button, a, input, textarea, select") && event.currentTarget !== event.target) {
      return;
    }
    event.preventDefault();
    await callback();
  });
}

async function runExportAction(
  button,
  pendingLabel,
  successLabel,
  endpoint,
  filename,
  fallbackBuilder,
  mimeType,
  queryString = buildExportQuery()
) {
  if (!button) {
    return;
  }
  const defaultLabel = button.dataset.defaultLabel || button.textContent.trim();
  button.dataset.defaultLabel = defaultLabel;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.textContent = pendingLabel;
  state.opsMessage = null;
  state.opsMessageTone = "info";
  state.opsMessageContext = "global";
  renderGlobalFeedback();
  try {
    const mode = await exportWithFallback(endpoint, filename, fallbackBuilder, mimeType, queryString);
    state.opsMessage = `${successLabel}${mode === "fallback" ? "（本地兜底）" : ""}`;
    state.opsMessageTone = mode === "fallback" ? "info" : "success";
    state.opsMessageContext = "global";
  } catch (error) {
    state.opsMessage = error.message || "导出失败。";
    state.opsMessageTone = "error";
    state.opsMessageContext = "global";
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.textContent = defaultLabel;
    render();
  }
}

function attachEvents() {
  districtFilter.addEventListener("change", async (event) => {
    await applyDistrictScope(event.target.value);
    render();
  });

  minYieldFilter.addEventListener("input", async (event) => {
    state.minYield = Number(event.target.value);
    minYieldValue.textContent = `${state.minYield.toFixed(1)}%`;
    await refreshData();
    render();
  });

  maxBudgetFilter.addEventListener("input", async (event) => {
    state.maxBudget = Number(event.target.value);
    maxBudgetValue.textContent = `${state.maxBudget} 万`;
    await refreshData();
    render();
  });

  minSamplesFilter.addEventListener("input", async (event) => {
    state.minSamples = Number(event.target.value);
    minSamplesValue.textContent = `${state.minSamples} 套`;
    await refreshData();
    render();
  });

  granularityGroup.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-granularity]");
    if (!button) {
      return;
    }
    setGranularity(button.dataset.granularity);
    render();
  });

  inspectorToggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.inspectorToggle;
      state.mobileInspectorPanel = state.mobileInspectorPanel === key ? null : key;
      renderInspectorPanels();
    });
  });

  exportKmlButton.addEventListener("click", async () => {
    await runExportAction(
      exportKmlButton,
      "导出中…",
      "KML 已导出",
      "/api/export/kml",
      "shanghai-yield-atlas.kml",
      buildKml,
      "application/vnd.google-earth.kml+xml"
    );
  });

  exportGeoJsonButton.addEventListener("click", async () => {
    await runExportAction(
      exportGeoJsonButton,
      "导出中…",
      "GeoJSON 已导出",
      "/api/export/geojson",
      "shanghai-yield-atlas.geojson",
      buildGeoJson,
      "application/geo+json"
    );
  });

  exportFloorWatchlistKmlButton.addEventListener("click", async () => {
    await runExportAction(
      exportFloorWatchlistKmlButton,
      "导出中…",
      "楼层 KML 已导出",
      "/api/export/floor-watchlist.kml",
      buildFloorWatchlistExportFilename("kml"),
      buildFloorWatchlistKml,
      "application/vnd.google-earth.kml+xml",
      buildFloorWatchlistExportQuery()
    );
  });

  exportFloorWatchlistGeoJsonButton.addEventListener("click", async () => {
    await runExportAction(
      exportFloorWatchlistGeoJsonButton,
      "导出中…",
      "楼层 GeoJSON 已导出",
      "/api/export/floor-watchlist.geojson",
      buildFloorWatchlistExportFilename("geojson"),
      buildFloorWatchlistGeoJson,
      "application/geo+json",
      buildFloorWatchlistExportQuery()
    );
  });

  exportGeoTaskWatchlistGeoJsonButton.addEventListener("click", async () => {
    await runExportAction(
      exportGeoTaskWatchlistGeoJsonButton,
      "导出中…",
      "补采 GeoJSON 已导出",
      "/api/export/geo-task-watchlist.geojson",
      buildGeoTaskWatchlistExportFilename("geojson"),
      buildGeoTaskWatchlistGeoJson,
      "application/geo+json",
      buildGeoTaskWatchlistExportQuery()
    );
  });

  exportGeoTaskWatchlistCsvButton.addEventListener("click", async () => {
    await runExportAction(
      exportGeoTaskWatchlistCsvButton,
      "导出中…",
      "补采 CSV 已导出",
      "/api/export/geo-task-watchlist.csv",
      buildGeoTaskWatchlistExportFilename("csv"),
      buildGeoTaskWatchlistCsv,
      "text/csv;charset=utf-8",
      buildGeoTaskWatchlistExportQuery()
    );
  });

  exportBrowserSamplingPackCsvButton.addEventListener("click", async () => {
    await runExportAction(
      exportBrowserSamplingPackCsvButton,
      "导出中…",
      "采样 CSV 已导出",
      "/api/export/browser-sampling-pack.csv",
      buildBrowserSamplingPackExportFilename("csv"),
      buildBrowserSamplingPackCsv,
      "text/csv;charset=utf-8",
      buildBrowserSamplingPackExportQuery()
    );
  });

  researchSearchInput.addEventListener("input", (event) => {
    state.researchSearchQuery = event.target.value;
    state.researchSearchOpen = true;
    state.searchSelectedIndex = 0;
    renderSearchResults();
  });

  researchSearchInput.addEventListener("focus", () => {
    state.researchSearchOpen = true;
    renderSearchResults();
  });

  researchSearchInput.addEventListener("keydown", async (event) => {
    const results = getSearchResults();
    if (!results.length && event.key !== "Escape") {
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      state.researchSearchOpen = true;
      state.searchSelectedIndex = (state.searchSelectedIndex + 1) % results.length;
      renderSearchResults();
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      state.researchSearchOpen = true;
      state.searchSelectedIndex = (state.searchSelectedIndex - 1 + results.length) % results.length;
      renderSearchResults();
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      const target = results[state.searchSelectedIndex] ?? results[0];
      if (target) {
        await openSearchResult(target);
      }
      return;
    }
    if (event.key === "Escape") {
      state.researchSearchOpen = false;
      renderSearchResults();
    }
  });

  searchClearButton.addEventListener("click", () => {
    clearSearch();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-field")) {
      state.researchSearchOpen = false;
      renderSearchResults();
    }
  });
}

function ensureValidSelection() {
  const communities = getVisibleMapCommunities();
  if (!communities.some((community) => community.id === state.selectedCommunityId)) {
    state.selectedCommunityId = communities[0]?.id ?? null;
  }
  if (state.selectedCommunityId) {
    state.selectedDistrictId = communities.find((community) => community.id === state.selectedCommunityId)?.districtId ?? state.selectedDistrictId;
  }
}

async function loadSelectedCommunityDetail() {
  if (!state.selectedCommunityId) {
    state.selectedCommunityDetail = null;
    state.selectedBuildingId = null;
    state.selectedFloorNo = null;
    state.selectedBuildingDetail = null;
    state.selectedFloorDetail = null;
    return;
  }

  const requestId = ++detailRequestId;

  try {
    const response = await fetch(`/api/communities/${state.selectedCommunityId}`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Community detail failed with ${response.status}`);
    }
    const community = hydrateCommunity(await response.json());
    if (requestId !== detailRequestId) {
      return;
    }
    state.selectedCommunityDetail = community;
  } catch (error) {
    const fallback = canUseDemoFallback() ? getSelectedCommunity() : null;
    state.selectedCommunityDetail = fallback ? hydrateCommunity(fallback) : null;
  }

  const buildingIds = state.selectedCommunityDetail?.buildings?.map((building) => building.id) ?? [];
  if (!buildingIds.includes(state.selectedBuildingId)) {
    state.selectedBuildingId = state.selectedCommunityDetail?.primaryBuildingId ?? buildingIds[0] ?? null;
  }
  await loadSelectedBuildingDetail();
}

async function loadSelectedBuildingDetail() {
  if (!state.selectedBuildingId) {
    state.selectedBuildingDetail = null;
    state.selectedFloorNo = null;
    state.selectedFloorDetail = null;
    return;
  }

  const requestId = ++buildingRequestId;

  try {
    const response = await fetch(`/api/buildings/${state.selectedBuildingId}`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Building detail failed with ${response.status}`);
    }
    const building = await response.json();
    if (requestId !== buildingRequestId) {
      return;
    }
    state.selectedBuildingDetail = building;
  } catch (error) {
    state.selectedBuildingDetail = canUseDemoFallback() ? buildFallbackBuildingDetail(state.selectedBuildingId) : null;
  }

  const floorNos = state.selectedBuildingDetail?.floorCurve?.map((floor) => floor.floorNo) ?? [];
  if (!floorNos.includes(state.selectedFloorNo)) {
    state.selectedFloorNo = state.selectedBuildingDetail?.focusFloorNo ?? floorNos[0] ?? null;
  }
  await loadSelectedFloorDetail();
}


async function loadSelectedFloorDetail() {
  if (!state.selectedBuildingId || !state.selectedFloorNo) {
    state.selectedFloorDetail = null;
    return;
  }

  const requestId = ++floorRequestId;
  try {
    const response = await fetch(`/api/buildings/${state.selectedBuildingId}/floors/${state.selectedFloorNo}`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) {
      throw new Error(`Floor detail failed with ${response.status}`);
    }
    const floorDetail = await response.json();
    if (requestId !== floorRequestId) {
      return;
    }
    state.selectedFloorDetail = floorDetail;
  } catch (error) {
    state.selectedFloorDetail = canUseDemoFallback() ? buildFallbackFloorDetail(state.selectedFloorNo) : null;
  }
}












function render() {
  renderGlobalFeedback();
  renderInspectorPanels();
  renderFilterPanel();
  renderWorkspaceView();
  renderResearchBackstage();
  renderSummary();
  renderSearchResults();
  renderDetail();
  renderFloorEvidence();
  renderRanking();
  renderMatrix();
  renderOperations();
  renderMapChromeState();
  renderMapWaypointBadge();
  renderMapExperience();
}

function renderMapChromeState() {
  if (!mapFrame || !amapContainer) {
    return;
  }
  mapFrame.dataset.granularity = state.granularity;
  amapContainer.dataset.granularity = state.granularity;

  const hasCommunitySelection = Boolean(state.selectedCommunityId);
  const hasBuildingSelection = Boolean(state.selectedBuildingId);
  const hasFloorSelection = Boolean(state.selectedBuildingId && state.selectedFloorNo != null);
  const hasGeoTaskSelection = Boolean(state.selectedGeoTaskId);
  const hasBrowserTaskSelection = Boolean(state.selectedBrowserSamplingTaskId);
  const hasWaypointSelection = Boolean(state.mapWaypoint?.label);

  mapFrame.classList.toggle("has-community-focus", hasCommunitySelection);
  mapFrame.classList.toggle("has-building-focus", hasBuildingSelection);
  mapFrame.classList.toggle("has-floor-focus", hasFloorSelection);
  mapFrame.classList.toggle("has-geo-task-focus", hasGeoTaskSelection);
  mapFrame.classList.toggle("has-browser-task-focus", hasBrowserTaskSelection);
  mapFrame.classList.toggle("has-waypoint-focus", hasWaypointSelection);

  amapContainer.classList.toggle("has-community-focus", hasCommunitySelection);
  amapContainer.classList.toggle("has-building-focus", hasBuildingSelection);
  amapContainer.classList.toggle("has-floor-focus", hasFloorSelection);
  amapContainer.classList.toggle("has-geo-task-focus", hasGeoTaskSelection);
  amapContainer.classList.toggle("has-browser-task-focus", hasBrowserTaskSelection);
  amapContainer.classList.toggle("has-waypoint-focus", hasWaypointSelection);
}

function triggerMapTransition(mode = "focus") {
  if (!mapFrame || !amapContainer) {
    return;
  }
  const token = ++amapState.transitionToken;
  if (amapState.transitionTimer) {
    window.clearTimeout(amapState.transitionTimer);
    amapState.transitionTimer = null;
  }

  mapFrame.classList.remove("is-shifting", "is-granularity-shift", "is-focus-shift");
  amapContainer.classList.remove("is-shifting", "is-granularity-shift", "is-focus-shift");

  const className = mode === "granularity" ? "is-granularity-shift" : "is-focus-shift";
  mapFrame.classList.add("is-shifting", className);
  amapContainer.classList.add("is-shifting", className);

  amapState.transitionTimer = window.setTimeout(() => {
    if (token !== amapState.transitionToken) {
      return;
    }
    mapFrame.classList.remove("is-shifting", "is-granularity-shift", "is-focus-shift");
    amapContainer.classList.remove("is-shifting", "is-granularity-shift", "is-focus-shift");
    amapState.transitionTimer = null;
  }, mode === "granularity" ? 520 : 420);
}



function renderMapWaypointBadge() {
  if (!mapWaypointBadge) {
    return;
  }
  const waypoint = state.mapWaypoint;
  if (!waypoint?.label) {
    mapWaypointBadge.className = "map-waypoint-badge is-hidden";
    mapWaypointBadge.innerHTML = "";
    return;
  }
  mapWaypointBadge.className = `map-waypoint-badge is-visible tone-${waypoint.tone ?? "yield"}`;
  mapWaypointBadge.innerHTML = `
    <span class="map-waypoint-badge__eyebrow">${waypoint.sourceLabel ?? "研究台跳转"}</span>
    <strong>${waypoint.label}</strong>
    ${waypoint.detail ? `<span class="map-waypoint-badge__detail">${waypoint.detail}</span>` : ""}
  `;
}

function clearMapWaypoint({ silent = false } = {}) {
  if (mapWaypointTimer) {
    window.clearTimeout(mapWaypointTimer);
    mapWaypointTimer = null;
  }
  state.mapWaypoint = null;
  if (!silent) {
    renderDetail();
    renderMapWaypointBadge();
    renderMapChromeState();
    updateMapNote();
  }
}

function announceMapWaypoint({ source = "queue", label, detail = "" } = {}) {
  if (!label) {
    clearMapWaypoint();
    return;
  }
  if (mapWaypointTimer) {
    window.clearTimeout(mapWaypointTimer);
    mapWaypointTimer = null;
  }
  state.mapWaypoint = {
    source,
    sourceLabel: mapWaypointSourceLabel(source),
    tone: mapWaypointTone(source),
    label,
    detail
  };
  renderDetail();
  renderMapWaypointBadge();
  renderMapChromeState();
  updateMapNote();
  mapWaypointTimer = window.setTimeout(() => {
    clearMapWaypoint();
  }, 4200);
}

function normalizeSearchText(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
}

function tokenizeSearchQuery(value) {
  return String(value ?? "")
    .split(/[\s·•|/]+/g)
    .map((token) => normalizeSearchText(token))
    .filter(Boolean);
}


function collectSearchCandidates() {
  const candidates = [];
  const seen = new Set();
  const pushCandidate = (candidate) => {
    if (!candidate?.id || seen.has(candidate.id)) {
      return;
    }
    candidate.keywords = Array.from(
      new Set([candidate.label, candidate.subtitle, ...(candidate.keywords ?? [])].filter(Boolean))
    );
    seen.add(candidate.id);
    candidates.push(candidate);
  };
  const pushBuildingCandidate = ({
    communityId,
    buildingId,
    districtId,
    districtName,
    communityName,
    buildingName,
    totalFloors,
    buildingAliases = [],
    communityAliases = []
  }) => {
    if (!communityId || !buildingId || !buildingName) {
      return;
    }
    pushCandidate({
      type: "building",
      id: `building:${buildingId}`,
      communityId,
      buildingId,
      districtId,
      label: `${communityName} · ${buildingName}`,
      subtitle: `${districtName ?? "未知行政区"} · 楼栋 · ${totalFloors ?? "?"}层`,
      keywords: [communityName, buildingName, districtName, ...buildingAliases, ...communityAliases]
    });
  };

  const communities = mapCommunities ?? [];
  communities.forEach((community) => {
    pushCandidate({
      type: "community",
      id: `community:${community.id}`,
      communityId: community.id,
      districtId: community.districtId,
      label: community.name,
      subtitle: `${community.districtName ?? "未知行政区"} · ${community.sampleStatusLabel ?? "状态待补"}`,
      keywords: [community.name, community.districtName, community.districtShort, ...(community.communityAliases ?? [])]
    });
    (community.buildings ?? []).forEach((building) => {
      pushBuildingCandidate({
        communityId: community.id,
        buildingId: building.id,
        districtId: community.districtId,
        districtName: community.districtName,
        communityName: community.name,
        buildingName: building.name,
        totalFloors: building.totalFloors,
        buildingAliases: building.buildingAliases ?? [],
        communityAliases: community.communityAliases ?? []
      });
    });
  });
  (state.selectedCommunityDetail?.buildings ?? []).forEach((building) => {
    pushBuildingCandidate({
      communityId: state.selectedCommunityDetail.id,
      buildingId: building.id,
      districtId: state.selectedCommunityDetail.districtId,
      districtName: state.selectedCommunityDetail.districtName,
      communityName: state.selectedCommunityDetail.name,
      buildingName: building.name,
      totalFloors: building.totalFloors,
      buildingAliases: building.buildingAliases ?? [],
      communityAliases: state.selectedCommunityDetail.communityAliases ?? []
    });
  });
  (state.floorWatchlistItems ?? []).forEach((item) => {
    pushBuildingCandidate({
      communityId: item.communityId,
      buildingId: item.buildingId,
      districtId: item.districtId,
      districtName: item.districtName,
      communityName: item.communityName,
      buildingName: item.buildingName,
      totalFloors: item.totalFloors
    });
    pushCandidate({
      type: "floor",
      id: `floor:${item.buildingId}:${item.floorNo}`,
      communityId: item.communityId,
      buildingId: item.buildingId,
      floorNo: item.floorNo,
      districtId: item.districtId,
      label: `${item.communityName} · ${item.buildingName} · ${item.floorNo}层`,
      subtitle: `${item.districtName ?? "未知行政区"} · 楼层机会 ${Number(item.latestYieldPct ?? 0).toFixed(2)}%`,
      keywords: [item.communityName, item.buildingName, `${item.floorNo}层`, item.districtName]
    });
  });
  (state.browserSamplingPackItems ?? []).forEach((task) => {
    pushBuildingCandidate({
      communityId: task.communityId,
      buildingId: task.buildingId,
      districtId: task.districtId,
      districtName: task.districtName,
      communityName: task.communityName,
      buildingName: task.buildingName,
      totalFloors: task.totalFloors
    });
    pushCandidate({
      type: "sampling",
      id: `sampling:${task.taskId}`,
      taskId: task.taskId,
      communityId: task.communityId,
      buildingId: task.buildingId ?? null,
      floorNo: task.floorNo ?? null,
      districtId: task.districtId,
      label: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}`,
      subtitle: `${task.districtName ?? "未知行政区"} · 采样任务 · ${task.taskLifecycleLabel ?? "待采样"}`,
      keywords: [
        task.communityName,
        task.buildingName,
        task.districtName,
        task.taskTypeLabel,
        `${task.floorNo ?? ""}层`
      ]
    });
  });
  return candidates;
}

function getSearchResults(limit = 10) {
  const query = normalizeSearchText(state.researchSearchQuery);
  const queryTokens = tokenizeSearchQuery(state.researchSearchQuery);
  const candidates = collectSearchCandidates();
  if (!query) {
    return candidates
      .slice()
      .sort((left, right) => String(left.label).localeCompare(String(right.label), "zh-Hans-CN"))
      .slice(0, limit);
  }
  return candidates
    .map((candidate) => {
      const normalizedKeywords = candidate.keywords.map((keyword) => normalizeSearchText(keyword)).filter(Boolean);
      const combinedText = normalizedKeywords.join(" ");
      const score = Math.max(
        ...normalizedKeywords.map((keyword) => searchScore(keyword, query)),
        queryTokens.length > 1 && queryTokens.every((token) => combinedText.includes(token)) ? 88 + queryTokens.length : 0,
        0
      );
      return { ...candidate, score };
    })
    .filter((candidate) => candidate.score > 0)
    .sort((left, right) => right.score - left.score || String(left.label).localeCompare(String(right.label), "zh-Hans-CN"))
    .slice(0, limit);
}


async function openSearchResult(result) {
  if (!result) {
    return;
  }
  state.researchSearchQuery = result.label;
  state.researchSearchOpen = false;
  state.searchSelectedIndex = 0;
  if (researchSearchInput) {
    researchSearchInput.value = result.label;
    researchSearchInput.blur();
  }
  renderSearchResults();
  if (result.type === "community") {
    setGranularity("community");
    await selectCommunity(result.communityId, result.districtId);
    announceMapWaypoint({
      source: "search",
      label: result.label,
      detail: "小区研究摘要与楼栋矩阵"
    });
    return;
  }
  if (result.type === "building") {
    setGranularity("building");
    await selectCommunity(result.communityId, result.districtId);
    await selectBuilding(result.buildingId);
    announceMapWaypoint({
      source: "search",
      label: result.label,
      detail: "楼栋研究摘要与楼层机会带"
    });
    return;
  }
  if (result.type === "floor") {
    setGranularity("floor");
    await navigateToEvidenceTarget(result.communityId, result.buildingId, result.floorNo, {
      waypoint: {
        source: "search",
        label: result.label,
        detail: "楼层证据、批次历史与样本配对"
      }
    });
    return;
  }
  if (result.type === "sampling") {
    await navigateToBrowserSamplingTask(result, {
      waypoint: {
        source: "search",
        label: result.label,
        detail: "公开页采样执行台与对应证据"
      }
    });
  }
}

function clearSearch() {
  state.researchSearchQuery = "";
  state.researchSearchOpen = false;
  state.searchSelectedIndex = 0;
  if (researchSearchInput) {
    researchSearchInput.value = "";
  }
  renderSearchResults();
}

function renderSearchResults() {
  if (!researchSearchResults) {
    return;
  }
  const results = getSearchResults();
  if (state.searchSelectedIndex >= results.length) {
    state.searchSelectedIndex = 0;
  }
  researchSearchInput?.setAttribute("aria-expanded", String(state.researchSearchOpen));
  if (!state.researchSearchOpen) {
    researchSearchResults.innerHTML = "";
    researchSearchResults.classList.remove("is-open");
    researchSearchInput?.removeAttribute("aria-activedescendant");
    return;
  }
  researchSearchResults.classList.add("is-open");
  if (!results.length) {
    researchSearchResults.innerHTML = `<div class="search-empty">没有找到匹配对象，试试小区名、楼栋名、楼层或采样任务。</div>`;
    researchSearchInput?.removeAttribute("aria-activedescendant");
    return;
  }
  const activeResult = results[state.searchSelectedIndex] ?? results[0];
  const activeDescendantId = activeResult ? `search-result-${activeResult.id.replace(/[^a-zA-Z0-9_-]/g, "-")}` : "";
  researchSearchResults.innerHTML = results
    .map(
      (result, index) => `
        <button
          type="button"
          id="search-result-${result.id.replace(/[^a-zA-Z0-9_-]/g, "-")}"
          class="search-result-item ${index === state.searchSelectedIndex ? "is-active" : ""}"
          data-search-result-id="${result.id}"
          role="option"
          aria-selected="${index === state.searchSelectedIndex ? "true" : "false"}"
        >
          <div class="search-result-top">
            <strong>${result.label}</strong>
            <span class="search-result-type">${searchTypeLabel(result.type)}</span>
          </div>
          <p>${result.subtitle}</p>
        </button>
      `
    )
    .join("");
  if (activeDescendantId) {
    researchSearchInput?.setAttribute("aria-activedescendant", activeDescendantId);
  } else {
    researchSearchInput?.removeAttribute("aria-activedescendant");
  }
  researchSearchResults.querySelectorAll("[data-search-result-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      const result = results.find((item) => item.id === button.dataset.searchResultId);
      await openSearchResult(result);
    });
  });
}

function renderMapExperience() {
  if (amapState.status !== "ready" || !amapState.map || !window.AMap) {
    updateMapNote();
    return;
  }

  const visibleDistricts = getFilteredDistricts();
  const visibleCommunities = getVisibleMapCommunities();
  const requestId = ++amapRenderRequestId;
  updateMapNote();

  void renderAmapDistricts(visibleDistricts, requestId).then(() => {
    if (requestId !== amapRenderRequestId) {
      return;
    }
    renderAmapCommunities(visibleCommunities);
    updateMapNote();
  });
}

async function renderAmapDistricts(visibleDistricts, requestId) {
  clearAmapDistricts();
  const overlays = [];

  if (!visibleDistricts.length) {
    const boundaryGroups = await Promise.all(
      fallbackDistricts.map(async (district) => ({
        district,
        boundaries: await fetchDistrictBoundaries(district.name)
      }))
    );
    if (requestId !== amapRenderRequestId) {
      return;
    }
    boundaryGroups.forEach(({ district, boundaries }) => {
      boundaries.forEach((path) => {
        overlays.push(
          new window.AMap.Polygon({
            path,
            strokeColor: "rgba(226, 241, 255, 0.78)",
            strokeWeight: 1.8,
            fillColor: getYieldColor(district.yield),
            fillOpacity: 0.08,
            bubble: false,
            zIndex: 26
          })
        );
      });
      const labelPosition =
        polygonCenterLonLat(boundaries[0]) ?? normalizeSvgToLonLat(district.labelX, district.labelY);
      const label = createAmapDistrictChip(district, labelPosition, { selected: district.id === state.selectedDistrictId });
      if (label) {
        overlays.push(label);
      }
    });
    if (!overlays.length) {
      fallbackDistricts.forEach((district) => {
        const path = fallbackDistrictPolygonPath(district);
        if (!path.length) {
          return;
        }
        overlays.push(
          new window.AMap.Polygon({
            path,
            strokeColor: "rgba(226, 241, 255, 0.74)",
            strokeWeight: 2.2,
            fillColor: getYieldColor(district.yield),
            fillOpacity: 0.14,
            bubble: false,
            zIndex: 24
          })
        );
      });
    }
    if (overlays.length) {
      amapState.map.add(overlays);
      amapState.map.setFitView(overlays, false, [72, 72, 72, 72]);
    }
    amapState.districtOverlays = overlays;
    return;
  }

  for (const district of visibleDistricts) {
    const boundaries = await fetchDistrictBoundaries(district.name);
    if (requestId !== amapRenderRequestId) {
      return;
    }
    boundaries.forEach((path) => {
      const polygon = new window.AMap.Polygon({
        path,
        strokeColor: district.id === state.selectedDistrictId ? "#f4f8fb" : "rgba(216,231,247,0.62)",
        strokeWeight: district.id === state.selectedDistrictId ? 2.2 : 1.4,
        fillColor: getYieldColor(district.yield),
        fillOpacity: district.id === state.selectedDistrictId ? 0.18 : 0.11,
        bubble: true,
        cursor: "pointer",
        zIndex: district.id === state.selectedDistrictId ? 60 : 40
      });
      polygon.on("click", async () => {
        state.selectedDistrictId = district.id;
        const firstCommunity = district.communities.find(isCommunityVisible) ?? district.communities[0];
        if (firstCommunity) {
          await selectCommunity(firstCommunity.id, district.id);
          return;
        }
        render();
      });
      overlays.push(polygon);
    });
    const labelPosition =
      polygonCenterLonLat(boundaries[0]) ?? normalizeSvgToLonLat(district.labelX, district.labelY);
    const label = createAmapDistrictChip(district, labelPosition, { selected: district.id === state.selectedDistrictId });
    if (label) {
      label.on("click", async () => {
        state.selectedDistrictId = district.id;
        const firstCommunity = district.communities.find(isCommunityVisible) ?? district.communities[0];
        if (firstCommunity) {
          await selectCommunity(firstCommunity.id, district.id);
          return;
        }
        render();
      });
      overlays.push(label);
    }
  }

  if (overlays.length) {
    amapState.map.add(overlays);
  }
  amapState.districtOverlays = overlays;
}

function renderAmapCommunities(visibleCommunities) {
  clearAmapCommunities();
  const overlays = [];
  const geoTaskItems = getGeoTaskMapItems();
  const browserSamplingTasks = getBrowserSamplingTaskMaps();
  const geoTaskByBuildingId = new Map(
    geoTaskItems.filter((item) => item.buildingId).map((item) => [item.buildingId, item])
  );
  const geoTaskByCommunityId = new Map(
    geoTaskItems.filter((item) => item.communityId).map((item) => [item.communityId, item])
  );
  const browserTaskByBuildingId = browserSamplingTasks.buildingMap;
  const browserTaskByCommunityId = browserSamplingTasks.communityMap;
  const browserTaskByFloorKey = browserSamplingTasks.floorMap;

  if (state.granularity === "building") {
    getVisibleBuildingItems().forEach(({ community, building, isSelected }) => {
      const geometry = resolveBuildingGeometry(community, building);
      const position = geometry.position;
      const path = geometry.lonLatPath;
      const geoTask = geoTaskByBuildingId.get(building.id) ?? null;
      const browserTask = browserTaskByBuildingId.get(building.id) ?? null;
      const isSelectedGeo = isSelectedGeoTask(geoTask);
      const isSelectedBrowser = isSelectedBrowserSamplingTask(browserTask);
      if (isSelected) {
        overlays.push(
          new window.AMap.CircleMarker({
            center: position,
            radius: 16,
            strokeColor: "rgba(255,255,255,0.86)",
            strokeWeight: 1.4,
            fillColor: getYieldColor(building.yieldAvg ?? community.yield),
            fillOpacity: 0.12,
            zIndex: 111,
            bubble: false
          })
        );
      }
      if (isSelectedGeo) {
        const halo = createAmapTaskFocusHalo(position, { tone: "geo", radius: 22, zIndex: 114 });
        if (halo) {
          overlays.push(halo);
        }
      }
      if (isSelectedBrowser) {
        const halo = createAmapTaskFocusHalo(position, { tone: "sampling", radius: 24, zIndex: 115 });
        if (halo) {
          overlays.push(halo);
        }
      }
      const polygon = new window.AMap.Polygon({
        path,
        strokeColor: isSelectedBrowser ? "#ffd166" : isSelectedGeo ? "#ff9966" : "#ffffff",
        strokeWeight: isSelected ? 2.6 : isSelectedBrowser || isSelectedGeo ? 2.1 : 1.4,
        fillColor: getYieldColor(building.yieldAvg ?? community.yield),
        fillOpacity: isSelected ? 0.72 : isSelectedBrowser || isSelectedGeo ? 0.62 : 0.54,
        zIndex: isSelected ? 126 : 112,
        bubble: true,
        cursor: "pointer"
      });

      polygon.on("click", async () => {
        openAmapInfoWindowAt(
          position,
          renderAmapInfoCard({
            kicker: "楼栋研究对象",
            title: `${community.name} · ${building.name}`,
            subtitle: community.districtName,
            stats: [
              { label: "楼栋均值", value: `${(building.yieldAvg ?? community.yield).toFixed(2)}%`, tone: "yield" },
              { label: "总层数", value: `${building.totalFloors}`, tone: "neutral" },
              { label: "机会分", value: `${building.score ?? community.score}分`, tone: "score" },
              { label: "几何", value: building.geometrySourceLabel ?? building.geometrySource ?? "待补", tone: "neutral" }
            ],
            note:
              building.dataFreshnessLabel ??
              building.dataFreshness ??
              `${community.sampleStatusLabel ?? "样本状态待补"} · ${community.latestBatchName ? `批次 ${community.latestBatchName}` : "批次待补"}`,
            actionHint: "点击后右侧会切到这栋楼的楼层机会带和样本证据。"
          })
        );
        await selectCommunity(community.id, community.districtId);
        await selectBuilding(building.id);
        focusAmapPosition(position, 13);
      });

      overlays.push(polygon);
      if (isSelected) {
        const chip = createAmapContextChip(building.name, position, { tone: "yield", zIndex: 135, offsetY: -30 });
        if (chip) {
          chip.on("click", async () => {
            await selectCommunity(community.id, community.districtId);
            await selectBuilding(building.id);
            focusAmapPosition(position, 13);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedGeo) {
        const chip = createAmapContextChip("几何任务", position, { tone: "geo", zIndex: 136, offsetY: isSelected ? -56 : -30 });
        if (chip) {
          chip.on("click", async () => {
            await navigateToGeoTask(geoTask);
            focusAmapPosition(position, 13);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedBrowser) {
        const chip = createAmapContextChip(browserSamplingCoverageLabel(browserTask), position, {
          tone: "sampling",
          zIndex: 137,
          offsetY: isSelected || isSelectedGeo ? -56 : -30
        });
        if (chip) {
          chip.on("click", async () => {
            await navigateToBrowserSamplingTask(browserTask);
            focusAmapPosition(position, 13);
          });
          overlays.push(chip);
        }
      }
      if (geoTask) {
        const badge = new window.AMap.CircleMarker({
          center: position,
          radius: geoTask.impactBand === "critical" ? 10 : geoTask.impactBand === "high" ? 8.5 : 7,
          strokeColor: "#08121d",
          strokeWeight: 2,
          fillColor: geoTaskColor(geoTask.impactBand),
          fillOpacity: 0.92,
          zIndex: isSelected ? 136 : 124,
          bubble: true,
          cursor: "pointer"
        });
        badge.on("click", async () => {
          openAmapInfoWindowAt(
            position,
            renderAmapInfoCard({
              kicker: "几何补采任务",
              title: `${geoTask.communityName ?? community.name} · ${geoTask.buildingName ?? building.name}`,
              subtitle: `${geoTask.impactLabel} · ${geoTask.taskScopeLabel ?? "几何任务"}`,
            stats: [
              { label: "任务状态", value: geoTaskStatusLabel(geoTask.status), tone: "warning" },
              { label: "影响分", value: `${geoTask.impactScore ?? 0}`, tone: "score" },
              { label: "榜单命中", value: `${geoTask.watchlistHits ?? 0}`, tone: "neutral" }
            ],
            note: geoTask.geometryGapNote ?? geoTask.captureGoal ?? "优先补齐这栋楼的真实 footprint。",
            actionHint: "点击后会跳到几何补采工作台，并把地图聚焦到当前楼栋。"
          })
        );
          await navigateToGeoTask(geoTask);
          focusAmapPosition(position, 13);
        });
        overlays.push(badge);
      }
      if (browserTask) {
        const badge = createAmapBrowserSamplingBadge(browserTask, position, {
          hasGeoTask: Boolean(geoTask),
          zIndex: isSelected ? 138 : 128
        });
        badge?.on("click", async () => {
          openAmapInfoWindowAt(position, browserSamplingTaskInfoHtml(browserTask));
          await navigateToBrowserSamplingTask(browserTask);
          focusAmapPosition(position, 13);
        });
        if (badge) {
          overlays.push(badge);
        }
      }
    });
  } else if (state.granularity === "floor") {
    getVisibleFloorWatchlistItems().forEach((item) => {
      const geometry = resolveFloorGeometry(item);
      if (!geometry) {
        return;
      }
      const position = geometry.position;
      const isSelected = item.buildingId === state.selectedBuildingId && Number(item.floorNo) === Number(state.selectedFloorNo);
      const path = geometry.lonLatPath;
      const geoTask = geoTaskByBuildingId.get(item.buildingId) ?? null;
      const browserTask = browserTaskByFloorKey.get(`${item.buildingId}:${item.floorNo}`) ?? browserTaskByBuildingId.get(item.buildingId) ?? null;
      const isSelectedGeo = isSelectedGeoTask(geoTask);
      const isSelectedBrowser = isSelectedBrowserSamplingTask(browserTask);
      if (isSelected) {
        overlays.push(
          new window.AMap.CircleMarker({
            center: position,
            radius: 17,
            strokeColor: "rgba(255,255,255,0.9)",
            strokeWeight: 1.4,
            fillColor: getYieldColor(item.latestYieldPct),
            fillOpacity: 0.14,
            zIndex: 117,
            bubble: false
          })
        );
      }
      if (isSelectedGeo) {
        const halo = createAmapTaskFocusHalo(position, { tone: "geo", radius: 22, zIndex: 119 });
        if (halo) {
          overlays.push(halo);
        }
      }
      if (isSelectedBrowser) {
        const halo = createAmapTaskFocusHalo(position, { tone: "sampling", radius: 24, zIndex: 120 });
        if (halo) {
          overlays.push(halo);
        }
      }
      const polygon = new window.AMap.Polygon({
        path,
        strokeColor: isSelectedBrowser ? "#ffd166" : isSelectedGeo ? "#ff9966" : "#ffffff",
        strokeWeight: isSelected ? 2.8 : isSelectedBrowser || isSelectedGeo ? 2.2 : 1.4,
        fillColor: getYieldColor(item.latestYieldPct),
        fillOpacity: isSelected ? 0.86 : isSelectedBrowser || isSelectedGeo ? 0.76 : 0.68,
        zIndex: isSelected ? 132 : 118,
        bubble: true,
        cursor: "pointer"
      });

      polygon.on("click", async () => {
        openAmapInfoWindowAt(
          position,
          renderAmapInfoCard({
            kicker: "楼层证据对象",
            title: `${item.communityName} · ${item.buildingName} · ${item.floorNo}层`,
            subtitle: `${item.districtName} · ${item.trendLabel}`,
            stats: [
              { label: "当前回报", value: `${Number(item.latestYieldPct).toFixed(2)}%`, tone: "yield" },
              { label: "持续分", value: `${item.persistenceScore}`, tone: "score" },
              { label: "样本对", value: `${item.latestPairCount ?? item.pairCount ?? 0}`, tone: "neutral" },
              { label: "基线", value: item.baselineBatchName ?? "首批样本", tone: "neutral" }
            ],
            note: item.latestBatchName ? `当前批次 ${item.latestBatchName}` : "当前批次待补",
            actionHint: "点击后右侧会直接展开这一层的样本配对、历史批次和地址归一路径。"
          })
        );
        await navigateToEvidenceTarget(item.communityId, item.buildingId, item.floorNo);
        focusAmapPosition(position, 13.8);
      });

      overlays.push(polygon);
      if (isSelected) {
        const chip = createAmapContextChip(`${item.floorNo}层`, position, { tone: "yield", zIndex: 141, offsetY: -30 });
        if (chip) {
          chip.on("click", async () => {
            await navigateToEvidenceTarget(item.communityId, item.buildingId, item.floorNo);
            focusAmapPosition(position, 13.8);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedGeo) {
        const chip = createAmapContextChip("几何任务", position, {
          tone: "geo",
          zIndex: 142,
          offsetY: isSelected ? -56 : -30
        });
        if (chip) {
          chip.on("click", async () => {
            await navigateToGeoTask(geoTask);
            focusAmapPosition(position, 13.8);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedBrowser) {
        const chip = createAmapContextChip(browserSamplingCoverageLabel(browserTask), position, {
          tone: "sampling",
          zIndex: 143,
          offsetY: isSelected || isSelectedGeo ? -56 : -30
        });
        if (chip) {
          chip.on("click", async () => {
            await navigateToBrowserSamplingTask(browserTask);
            focusAmapPosition(position, 13.8);
          });
          overlays.push(chip);
        }
      }
      if (geoTask) {
        const badge = new window.AMap.CircleMarker({
          center: position,
          radius: geoTask.impactBand === "critical" ? 10 : geoTask.impactBand === "high" ? 8.5 : 7,
          strokeColor: "#08121d",
          strokeWeight: 2,
          fillColor: geoTaskColor(geoTask.impactBand),
          fillOpacity: 0.92,
          zIndex: isSelected ? 140 : 126,
          bubble: true,
          cursor: "pointer"
        });
        badge.on("click", async () => {
          openAmapInfoWindowAt(
            position,
            renderAmapInfoCard({
              kicker: "几何补采任务",
              title: `${geoTask.communityName ?? item.communityName} · ${geoTask.buildingName ?? item.buildingName}`,
              subtitle: `${geoTask.impactLabel} · ${geoTask.taskScopeLabel ?? "几何任务"}`,
            stats: [
              { label: "任务状态", value: geoTaskStatusLabel(geoTask.status), tone: "warning" },
              { label: "影响分", value: `${geoTask.impactScore ?? 0}`, tone: "score" },
              { label: "榜单命中", value: `${geoTask.watchlistHits ?? 0}`, tone: "neutral" }
            ],
            note: geoTask.geometryGapNote ?? geoTask.captureGoal ?? "优先补齐这栋楼的真实 footprint。",
            actionHint: "点击后会切到几何补采任务，并把楼层证据保持在当前对象上。"
          })
        );
          await navigateToGeoTask(geoTask);
          focusAmapPosition(position, 13.8);
        });
        overlays.push(badge);
      }
      if (browserTask) {
        const badge = createAmapBrowserSamplingBadge(browserTask, position, {
          hasGeoTask: Boolean(geoTask),
          zIndex: isSelected ? 142 : 130
        });
        badge?.on("click", async () => {
          openAmapInfoWindowAt(position, browserSamplingTaskInfoHtml(browserTask));
          await navigateToBrowserSamplingTask(browserTask);
          focusAmapPosition(position, 13.8);
        });
        if (badge) {
          overlays.push(badge);
        }
      }
    });
  } else {
    visibleCommunities.forEach((community) => {
      const position = communityCenter(community);
      const selected = community.id === state.selectedCommunityId;
      const geoTask = geoTaskByCommunityId.get(community.id) ?? null;
      const browserTask = browserTaskByCommunityId.get(community.id) ?? null;
      const isSelectedGeo = isSelectedGeoTask(geoTask);
      const isSelectedBrowser = isSelectedBrowserSamplingTask(browserTask);
      const isDictionaryOnly = community.sampleStatus === "dictionary_only";
      const isSparse = community.sampleStatus === "sparse_sample";
      const halo = new window.AMap.CircleMarker({
        center: position,
        radius: selected
          ? (isDictionaryOnly ? 15 : isSparse ? 17 : sizeByScore(community.score) + 9)
          : isDictionaryOnly
          ? 11
          : isSparse
          ? 12
          : sizeByScore(community.score) + 6,
        strokeColor: "rgba(255,255,255,0)",
        strokeWeight: 0,
        fillColor: isDictionaryOnly ? "#95a8bb" : getYieldColor(community.yield),
        fillOpacity: selected ? 0.18 : isSelectedBrowser || isSelectedGeo ? 0.14 : isDictionaryOnly ? 0.06 : 0.08,
        zIndex: selected ? 98 : 90,
        bubble: false
      });
      if (isSelectedGeo) {
        const taskHalo = createAmapTaskFocusHalo(position, { tone: "geo", radius: 19, zIndex: 96 });
        if (taskHalo) {
          overlays.push(taskHalo);
        }
      }
      if (isSelectedBrowser) {
        const taskHalo = createAmapTaskFocusHalo(position, { tone: "sampling", radius: 21, zIndex: 97 });
        if (taskHalo) {
          overlays.push(taskHalo);
        }
      }
      const marker = new window.AMap.CircleMarker({
        center: position,
        radius: selected
          ? (isDictionaryOnly ? 6 : isSparse ? 7.5 : sizeByScore(community.score)) + 2
          : isDictionaryOnly
          ? 6
          : isSparse
          ? 7.5
          : sizeByScore(community.score),
        strokeColor: isSelectedBrowser ? "#ffd166" : isSelectedGeo ? "#ff9966" : "#ffffff",
        strokeWeight: selected ? 2.2 : isSelectedBrowser || isSelectedGeo ? 1.8 : 1,
        fillColor: isDictionaryOnly ? "#95a8bb" : getYieldColor(community.yield),
        fillOpacity: isDictionaryOnly ? (selected ? 0.66 : 0.42) : selected ? 0.92 : isSparse ? 0.68 : 0.76,
        zIndex: selected ? 120 : 100,
        bubble: true,
        cursor: "pointer"
      });

      marker.on("click", async () => {
        openAmapInfoWindow(community, position);
        await selectCommunity(community.id, community.districtId);
        focusAmapOnCommunity(community);
      });

      overlays.push(halo, marker);
      if (selected) {
        const chip = createAmapContextChip(community.name, position, {
          tone: isDictionaryOnly ? "pending" : "yield",
          zIndex: 121,
          offsetY: -30
        });
        if (chip) {
          chip.on("click", async () => {
            await selectCommunity(community.id, community.districtId);
            focusAmapOnCommunity(community);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedGeo) {
        const chip = createAmapContextChip("几何任务", position, {
          tone: "geo",
          zIndex: 122,
          offsetY: selected ? -56 : -30
        });
        if (chip) {
          chip.on("click", async () => {
            await navigateToGeoTask(geoTask);
            focusAmapPosition(position, 12.5);
          });
          overlays.push(chip);
        }
      }
      if (isSelectedBrowser) {
        const chip = createAmapContextChip(browserSamplingCoverageLabel(browserTask), position, {
          tone: "sampling",
          zIndex: 123,
          offsetY: selected || isSelectedGeo ? -56 : -30
        });
        if (chip) {
          chip.on("click", async () => {
            await navigateToBrowserSamplingTask(browserTask);
            focusAmapPosition(position, 12.5);
          });
          overlays.push(chip);
        }
      }
      if (geoTask) {
        const badge = new window.AMap.CircleMarker({
          center: position,
          radius: geoTask.impactBand === "critical" ? 9.5 : 8,
          strokeColor: "#08121d",
          strokeWeight: 2,
          fillColor: geoTaskColor(geoTask.impactBand),
          fillOpacity: 0.9,
          zIndex: selected ? 126 : 108,
          bubble: true,
          cursor: "pointer"
        });
        badge.on("click", async () => {
          openAmapInfoWindowAt(
            position,
            renderAmapInfoCard({
              kicker: "几何补采任务",
              title: geoTask.communityName ?? community.name,
              subtitle: `${geoTask.impactLabel} · ${geoTask.taskScopeLabel ?? "几何任务"}`,
              stats: [
                { label: "楼栋对象", value: geoTask.buildingName ?? "待识别楼栋", tone: "neutral" },
                { label: "影响分", value: `${geoTask.impactScore ?? 0}`, tone: "score" },
                { label: "榜单命中", value: `${geoTask.watchlistHits ?? 0}`, tone: "neutral" }
              ],
              note: geoTask.geometryGapNote ?? geoTask.captureGoal ?? "当前这条任务会优先影响研究窗口里的对象判断。"
            })
          );
          await navigateToGeoTask(geoTask);
          focusAmapPosition(position, 12.5);
        });
        overlays.push(badge);
      }
      if (browserTask) {
        const badge = createAmapBrowserSamplingBadge(browserTask, position, {
          hasGeoTask: Boolean(geoTask),
          zIndex: selected ? 128 : 110
        });
        badge?.on("click", async () => {
          openAmapInfoWindowAt(position, browserSamplingTaskInfoHtml(browserTask));
          await navigateToBrowserSamplingTask(browserTask);
          focusAmapPosition(position, 12.5);
        });
        if (badge) {
          overlays.push(badge);
        }
      }
    });

    const selectedCommunity = state.selectedCommunityDetail ?? getSelectedCommunity();
    const preview = communityAnchorPreview(selectedCommunity);
    if (selectedCommunity && preview) {
      const position = [preview.centerLng, preview.centerLat];
      const halo = new window.AMap.CircleMarker({
        center: position,
        radius: 16,
        strokeColor: "#ffd166",
        strokeWeight: 2,
        fillColor: "#ffd166",
        fillOpacity: 0.08,
        strokeStyle: "dashed",
        zIndex: 122,
        bubble: true,
        cursor: "pointer"
      });
      const marker = new window.AMap.CircleMarker({
        center: position,
        radius: 8.5,
        strokeColor: "#08121d",
        strokeWeight: 2,
        fillColor: "#ffd166",
        fillOpacity: 0.92,
        zIndex: 124,
        bubble: true,
        cursor: "pointer"
      });
      const label = new window.AMap.Text({
        text: "",
        position,
        offset: new window.AMap.Pixel(0, 0),
        anchor: "bottom-center",
        zIndex: 126,
        style: { background: "transparent", border: "0", padding: "0" }
      });
      label.setText?.("");
      const openPreview = () => {
        openAmapInfoWindowAt(
          position,
          renderAmapInfoCard({
            kicker: "锚点待确认",
            title: `${selectedCommunity.name} · 预锚点`,
            subtitle: `${selectedCommunity.districtName ?? ""}${preview.anchorSource ? ` · ${preview.anchorSource}` : ""}`,
            stats: [
              { label: "候选名", value: preview.anchorName ?? "待确认候选", tone: "warning" },
              {
                label: "置信度",
                value: preview.anchorQuality != null ? `${Math.round(Number(preview.anchorQuality) * 100)}%` : "待人工确认",
                tone: "warning"
              }
            ],
            note: preview.anchorAddress ?? "当前只作为预锚点预览，确认后才会正式写回主档。"
          })
        );
        focusAmapPosition(position, 12.5);
      };
      halo.on("click", openPreview);
      marker.on("click", openPreview);
      const previewChip = createAmapContextChip(`${selectedCommunity.name} · 预锚点`, position, {
        tone: "pending",
        zIndex: 126,
        offsetY: -32
      });
      previewChip?.on("click", openPreview);
      if (previewChip) {
        overlays.push(halo, marker, previewChip);
      } else {
        label.on?.("click", openPreview);
        overlays.push(halo, marker, label);
      }
    }
  }

  if (overlays.length) {
    amapState.map.add(overlays);
  }
  amapState.communityOverlays = overlays;

  if (!amapState.hasInitialFit && overlays.length) {
    amapState.map.setFitView(overlays, false, [80, 80, 80, 80]);
    amapState.hasInitialFit = true;
  }
}

function clearAmapDistricts() {
  if (amapState.districtOverlays.length && amapState.map) {
    amapState.map.remove(amapState.districtOverlays);
  }
  amapState.districtOverlays = [];
}

function clearAmapCommunities() {
  if (amapState.communityOverlays.length && amapState.map) {
    amapState.map.remove(amapState.communityOverlays);
  }
  amapState.communityOverlays = [];
}

function openAmapInfoWindowAt(position, content) {
  if (!amapState.infoWindow || !amapState.map) {
    return;
  }
  amapState.infoWindow.setContent(content);
  amapState.infoWindow.open(amapState.map, position);
}

function openAmapInfoWindow(community, position) {
  const statusLabel = community.sampleStatusLabel ?? "状态待补";
  const yieldText = community.sampleStatus === "dictionary_only" ? "待补样本" : `回报 ${Number(community.yield).toFixed(2)}%`;
  openAmapInfoWindowAt(
    position,
    renderAmapInfoCard({
      kicker: community.sampleStatus === "dictionary_only" ? "已挂图 · 待补样本" : "小区研究对象",
      title: community.name,
      subtitle: community.districtName ?? getSelectedDistrict()?.name ?? "",
      stats: [
        { label: "当前判断", value: yieldText, tone: community.sampleStatus === "dictionary_only" ? "warning" : "yield" },
        { label: "样本状态", value: statusLabel, tone: "neutral" },
        { label: "机会分", value: `${community.score ?? 0}分`, tone: "score" },
        { label: "坐标来源", value: community.anchorSource ? `${community.anchorSource}` : "待补", tone: "neutral" }
      ],
      note:
        community.sampleStatus === "dictionary_only"
          ? "这类小区已经挂图，但还没有足够出售/出租样本进入主榜。"
          : `${community.saleSample ?? community.sample ?? 0} 套出售样本 · ${community.rentSample ?? community.sample ?? 0} 套出租样本`,
      actionHint: "点击后会把右侧研究列切到这个小区，并联动楼栋 × 楼层表。"
    })
  );
}

function focusAmapOnCommunity(community) {
  if (!amapState.map) {
    return;
  }
  const preview = communityAnchorPreview(community);
  const center = preview ? [preview.centerLng, preview.centerLat] : communityCenter(community);
  focusAmapPosition(center, 12);
}

function focusAmapPosition(position, minZoom = 12) {
  if (!amapState.map) {
    return;
  }
  const zoom = Math.max(Number(amapState.map.getZoom?.() ?? 10.8), minZoom);
  const currentZoom = Number(amapState.map.getZoom?.() ?? 10.8);
  triggerMapTransition("focus");
  if (typeof amapState.map.panTo === "function") {
    amapState.map.panTo(position);
    if (currentZoom < zoom && typeof amapState.map.setZoom === "function") {
      window.setTimeout(() => {
        amapState.map?.setZoom?.(zoom);
      }, 90);
    }
    return;
  }
  amapState.map.setZoomAndCenter?.(zoom, position);
}

async function applyDistrictScope(
  districtId,
  {
    refresh = true,
    backgroundHydration = false,
    preserveBrowserSamplingTaskId = state.selectedBrowserSamplingTaskId,
  } = {}
) {
  const nextDistrictId = districtId || "all";
  const changed = state.districtFilter !== nextDistrictId;
  state.districtFilter = nextDistrictId;
  if (districtFilter) {
    districtFilter.value = nextDistrictId;
  }
  if (nextDistrictId !== "all") {
    state.selectedDistrictId = nextDistrictId;
  }
  if (refresh && changed) {
    await refreshData({
      backgroundHydration,
      preserveBrowserSamplingTaskId,
    });
  }
  return changed;
}

function updateMapNote() {
  if (!getVisibleMapCommunities().length && currentDataMode() === "empty") {
    mapNote.innerHTML = `
      <strong>说明</strong>
      <p>${amapState.modeNote ?? "当前地图用于展示上海租售比机会分布。"}</p>
      <p>当前还没有数据库主读数据，页面先保留真地图容器与 staged 说明。</p>
      <p>${runtimeConfig.hasPostgresDsn ? "本地库已配置，下一步补首轮 bootstrap。" : "下一步先配置 DSN 或导入 staged 批次。"}</p>
    `;
    return;
  }
  const baseNote = amapState.modeNote ?? "当前地图用于展示上海租售比机会分布。";
  const visibleCount =
    state.granularity === "community"
      ? getVisibleMapCommunities().length
      : state.granularity === "building"
      ? getVisibleBuildingItems().length
      : getVisibleFloorWatchlistItems().length;
  const mapCommunityItems = getVisibleMapCommunities();
  const dictionaryOnlyCount = mapCommunityItems.filter((community) => community.sampleStatus === "dictionary_only").length;
  const activeMetricCount = mapCommunityItems.filter((community) => community.sampleStatus === "active_metrics").length;
  const opsSummaryData = effectiveOperationsOverview().summary ?? {};
  const cityCommunityCount = Number(opsSummaryData.cityCommunityCount ?? mapCommunityItems.length);
  const anchoredCommunityCount = Number(opsSummaryData.anchoredCommunityCount ?? mapCommunityItems.length);
  const unanchoredCommunityCount = Math.max(cityCommunityCount - anchoredCommunityCount, 0);
  const latestAnchorReviewAt = opsSummaryData.latestAnchorReviewAt ?? null;
  const geoTaskItems = getGeoTaskMapItems();
  const topGeoTask = geoTaskItems[0] ?? null;
  const browserSamplingTaskMaps = getBrowserSamplingTaskMaps();
  const browserSamplingOpenTasks = browserSamplingTaskMaps.tasks;
  const browserSamplingVisibleCount =
    state.granularity === "community"
      ? browserSamplingTaskMaps.communityMap.size
      : state.granularity === "building"
      ? browserSamplingTaskMaps.buildingMap.size
      : browserSamplingTaskMaps.floorMap.size;
  const browserSamplingReviewCount = browserSamplingOpenTasks.filter((task) => browserSamplingCoverageState(task) === "needs_review").length;
  const topBrowserSamplingTask = browserSamplingOpenTasks[0] ?? null;
  const selectedCommunity = state.selectedCommunityDetail ?? getSelectedCommunity();
  const selectedPreview = communityAnchorPreview(selectedCommunity);
  const waypoint = state.mapWaypoint;
  const currentBatch = state.selectedImportRunDetail?.batchName ?? state.selectedImportRunDetail?.runId ?? "当前批次";
  const baselineBatch = state.selectedImportRunDetail?.comparison?.baselineBatchName ?? null;
  const isFloorWatchlistLoading = state.granularity === "floor" && state.floorWatchlistLoading;
  const geometrySource =
    state.granularity === "building"
      ? state.buildingGeoFeatures.length
        ? "api"
        : "fallback"
      : state.granularity === "floor"
      ? state.floorGeoFeatures.length
        ? "api"
        : "fallback"
      : state.geoAssetSource;
  const geometryBatchName =
    state.granularity === "building"
      ? state.buildingGeoFeatures[0]?.properties?.geo_asset_batch_name ?? state.selectedGeoAssetRunDetail?.batchName
      : state.granularity === "floor"
      ? state.floorGeoFeatures[0]?.properties?.geo_asset_batch_name ?? state.selectedGeoAssetRunDetail?.batchName
      : null;
  const geometryText =
    state.granularity === "community"
      ? `小区层使用真实经纬度挂图：${activeMetricCount} 个有指标样本，${unanchoredCommunityCount} 个待补坐标。`
      : geometrySource === "api"
      ? `楼栋与楼层 footprint 当前来自 geo-assets${geometryBatchName ? `（${geometryBatchName}）` : ""}。`
      : "楼栋与楼层 footprint 当前由前端推导，接入真实 geo-assets 后会自动切换。";
  const taskText = topGeoTask
    ? `当前最该补的几何缺口是 ${topGeoTask.communityName ?? "待识别小区"} · ${topGeoTask.buildingName ?? "待识别楼栋"}，${topGeoTask.impactLabel}。`
    : "当前筛选窗口下没有高影响几何缺口。";
  const samplingText = topBrowserSamplingTask
    ? `补样优先 ${topBrowserSamplingTask.communityName ?? "待识别小区"}${topBrowserSamplingTask.buildingName ? ` · ${topBrowserSamplingTask.buildingName}` : ""}${topBrowserSamplingTask.floorNo != null ? ` · ${topBrowserSamplingTask.floorNo}层` : ""}，${browserSamplingCoverageLabel(topBrowserSamplingTask)}。`
    : "当前筛选窗口下没有公开页采样缺口。";
  const waypointText = waypoint
    ? `当前焦点 ${waypoint.label}${waypoint.detail ? `，${waypoint.detail}` : ""}。`
    : null;
  const previewText = selectedPreview
    ? `${selectedCommunity?.name ?? "当前小区"} 正在使用候选锚点 ${selectedPreview.anchorName ?? "待确认候选"} 作为人工判断参考。`
    : `当前仍有 ${Number(opsSummaryData.pendingAnchorCount ?? unanchoredCommunityCount)} 个小区待确认锚点${latestAnchorReviewAt ? `，最近确认 ${formatTimestamp(latestAnchorReviewAt)}` : ""}。`;
  const compactScopeText =
    isFloorWatchlistLoading
      ? `楼层机会带仍在刷新，先保留 ${getVisibleBuildingItems().length} 个楼栋上下文，并同步 ${geoTaskItems.length} 个几何缺口与 ${browserSamplingVisibleCount} 个采样任务。`
      : state.granularity === "community"
      ? `当前显示 ${visibleCount} 个小区点；高影响几何缺口 ${geoTaskItems.length} 个，公开页采样缺口 ${browserSamplingVisibleCount} 个。`
      : state.granularity === "building"
      ? `当前显示 ${visibleCount} 个楼栋面；几何补采 ${geoTaskItems.length} 个，采样任务 ${browserSamplingVisibleCount} 个。`
      : `当前显示 ${visibleCount} 个楼层面；会影响逐层定位的几何缺口 ${geoTaskItems.length} 个，采样任务 ${browserSamplingVisibleCount} 个。`;
  const compactWindowText =
    state.granularity === "floor"
      ? `研究窗口 ${currentBatch}${baselineBatch ? ` 对比 ${baselineBatch}` : ""}。`
      : `当前粒度 ${granularityLabel(state.granularity)}；${activeMetricCount} 个小区已有指标样本，${unanchoredCommunityCount} 个待补坐标。`;
  const compactFocusText = waypointText ?? (topBrowserSamplingTask ? samplingText : topGeoTask ? taskText : previewText);
  mapNote.innerHTML = `
    <strong>说明</strong>
    <p>${baseNote}</p>
    <p>${compactScopeText}</p>
    <p>${compactWindowText} ${geometryText} ${compactFocusText}</p>
  `;
}

function fetchDistrictBoundaries(districtName) {
  if (!amapState.districtSearch) {
    return Promise.resolve([]);
  }
  if (amapState.districtBoundaryCache.has(districtName)) {
    return Promise.resolve(amapState.districtBoundaryCache.get(districtName));
  }

  return new Promise((resolve) => {
    amapState.districtSearch.search(districtName, (status, result) => {
      if (status !== "complete") {
        resolve([]);
        return;
      }

      const first = result?.districtList?.[0];
      const boundaries = first?.boundaries ?? [];
      amapState.districtBoundaryCache.set(districtName, boundaries);
      resolve(boundaries);
    });
  });
}

function getFilteredDistricts() {
  return districts.filter((district) => {
    if (state.districtFilter !== "all" && district.id !== state.districtFilter) {
      return false;
    }
    return district.communities.some(isCommunityVisible);
  });
}

function getVisibleMapCommunities() {
  return mapCommunities.filter((community) => state.districtFilter === "all" || community.districtId === state.districtFilter);
}

function getFilteredCommunities() {
  return districts.flatMap((district) =>
    district.communities
      .filter(isCommunityVisible)
      .map((community) => ({ ...community, districtName: district.name, districtShort: district.short }))
  );
}

function findCommunityById(communityId) {
  return (
    districts.flatMap((district) => district.communities).find((community) => community.id === communityId) ??
    mapCommunities.find((community) => community.id === communityId) ??
    null
  );
}

function findBuildingById(buildingId) {
  for (const district of districts) {
    for (const community of district.communities) {
      const building = (community.buildings ?? []).find((item) => item.id === buildingId);
      if (building) {
        return { community, building };
      }
    }
  }
  return null;
}
















function findBuildingGeoFeature(buildingId) {
  return state.buildingGeoFeatures.find((feature) => feature?.properties?.building_id === buildingId) ?? null;
}

function findFloorGeoFeature(buildingId, floorNo) {
  return (
    state.floorGeoFeatures.find(
      (feature) =>
        feature?.properties?.building_id === buildingId &&
        Number(feature?.properties?.floor_no) === Number(floorNo)
    ) ?? null
  );
}

function resolveBuildingGeometry(community, building) {
  const fallbackPoints = buildingFootprintPoints(community, building);
  const fallbackCenter = buildingSvgPoint(community, building);
  const feature = findBuildingGeoFeature(building.id);
  const svgPoints = featureSvgPoints(feature);
  const center = featureSvgCenter(feature) ?? fallbackCenter;
  const lonLatPath = featureLonLatPath(feature);
  return {
    center,
    svgPoints: svgPoints.length ? svgPoints : fallbackPoints,
    lonLatPath: lonLatPath.length ? lonLatPath : footprintPathToLonLat(fallbackPoints),
    position: featureLonLatCenter(feature) ?? normalizeSvgToLonLat(center.x, center.y)
  };
}

function resolveFloorGeometry(item) {
  const lookup = findBuildingById(item.buildingId);
  if (!lookup) {
    return null;
  }
  const fallbackPoints = floorFootprintPoints(lookup.community, lookup.building, item.floorNo);
  const fallbackCenter = floorSvgPoint(lookup.community, lookup.building, item.floorNo);
  const feature = findFloorGeoFeature(item.buildingId, item.floorNo);
  const svgPoints = featureSvgPoints(feature);
  const center = featureSvgCenter(feature) ?? fallbackCenter;
  const lonLatPath = featureLonLatPath(feature);
  return {
    center,
    svgPoints: svgPoints.length ? svgPoints : fallbackPoints,
    lonLatPath: lonLatPath.length ? lonLatPath : footprintPathToLonLat(fallbackPoints),
    position: featureLonLatCenter(feature) ?? normalizeSvgToLonLat(center.x, center.y)
  };
}

function createAmapBrowserSamplingBadge(task, position, { hasGeoTask = false, zIndex = 134 } = {}) {
  if (!task || !window.AMap) {
    return null;
  }
  return new window.AMap.Marker({
    position,
    anchor: "center",
    offset: new window.AMap.Pixel(hasGeoTask ? -14 : 24, -18),
    content: `
      <div class="amap-task-badge amap-task-badge--${browserSamplingCoverageState(task)}">
        <span class="amap-task-badge__dot"></span>
        <span class="amap-task-badge__text">${browserSamplingCoverageLabel(task)}</span>
        <span class="amap-task-badge__count">${browserSamplingBadgeCounter(task)}</span>
      </div>
    `,
    bubble: true,
    zIndex,
  });
}

function createAmapContextChip(text, position, { tone = "yield", zIndex = 132, offsetY = -28 } = {}) {
  if (!window.AMap || !text) {
    return null;
  }
  return new window.AMap.Marker({
    position,
    anchor: "center",
    offset: new window.AMap.Pixel(0, offsetY),
    content: `<div class="amap-context-chip amap-context-chip--${tone}">${text}</div>`,
    bubble: true,
    zIndex
  });
}

function createAmapTaskFocusHalo(position, { tone = "sampling", radius = 20, zIndex = 133 } = {}) {
  if (!window.AMap || !position) {
    return null;
  }
  const palette =
    tone === "geo"
      ? { stroke: "rgba(255, 153, 102, 0.92)", fill: "rgba(255, 153, 102, 0.16)" }
      : { stroke: "rgba(255, 209, 102, 0.94)", fill: "rgba(255, 209, 102, 0.14)" };

  return new window.AMap.CircleMarker({
    center: position,
    radius,
    strokeColor: palette.stroke,
    strokeWeight: 2,
    fillColor: palette.fill,
    fillOpacity: 0.42,
    strokeStyle: "dashed",
    zIndex,
    bubble: false
  });
}

function isSelectedGeoTask(task) {
  return Boolean(task?.taskId && task.taskId === state.selectedGeoTaskId);
}

function isSelectedBrowserSamplingTask(task) {
  return Boolean(task?.taskId && task.taskId === state.selectedBrowserSamplingTaskId);
}

function createAmapDistrictChip(district, position, { selected = false } = {}) {
  if (!window.AMap || !district || !position) {
    return null;
  }
  return new window.AMap.Marker({
    position,
    anchor: "center",
    offset: new window.AMap.Pixel(0, 0),
    content: `<div class="amap-context-chip amap-context-chip--${selected ? "district-active" : "district"}">${district.short ?? district.name}</div>`,
    bubble: true,
    zIndex: selected ? 66 : 44
  });
}

function getVisibleBuildingItems() {
  return getFilteredCommunities().flatMap((community) =>
    (community.buildings ?? []).map((building) => ({
      community,
      building,
      point: buildingSvgPoint(community, building),
      isSelected: building.id === state.selectedBuildingId
    }))
  );
}

function getVisibleFloorWatchlistItems() {
  const watchlistItems = state.floorWatchlistItems?.length ? state.floorWatchlistItems : canUseDemoFallback() ? getFallbackFloorWatchlistItems() : [];
  return watchlistItems.filter((item) => {
    const community = findCommunityById(item.communityId);
    return community ? isCommunityVisible(community) : state.districtFilter === "all" || item.districtId === state.districtFilter;
  });
}

function isCommunityVisible(community) {
  return (
    community.yield >= state.minYield &&
    community.avgPriceWan <= state.maxBudget &&
    community.sample >= state.minSamples &&
    (state.districtFilter === "all" || community.districtId === state.districtFilter)
  );
}

function getSelectedCommunity() {
  return findCommunityById(state.selectedCommunityId);
}

function getSelectedDistrict(preferredDistrictId = null) {
  const districtId = preferredDistrictId ?? state.selectedDistrictId;
  const knownDistrict =
    districts.find((district) => district.id === districtId) ??
    getFilteredDistricts().find((district) => district.id === districtId);
  if (knownDistrict) {
    return knownDistrict;
  }
  const fromDirectory = districtDirectory().find((district) => district.id === districtId) ?? districtDirectory()[0];
  if (fromDirectory) {
    return { ...fromDirectory, yield: 0, score: 0, saleSample: 0, rentSample: 0 };
  }
  const fallbackDistrict = getFilteredDistricts()[0] ?? districts[0];
  return fallbackDistrict
    ? fallbackDistrict
    : { id: "all", name: "上海", short: "上海", yield: 0, score: 0, saleSample: 0, rentSample: 0 };
}

async function selectCommunity(communityId, districtId, { preserveGeoTask = false } = {}) {
  if (!preserveGeoTask) {
    state.selectedGeoTaskId = null;
  }
  state.selectedCommunityId = communityId;
  state.selectedDistrictId = districtId ?? state.selectedDistrictId;
  state.selectedBuildingId = null;
  await loadSelectedCommunityDetail();
  const community = state.selectedCommunityDetail ?? getSelectedCommunity();
  if (community && amapState.status === "ready") {
    focusAmapOnCommunity(community);
  }
  render();
}

async function selectBuilding(buildingId, { preserveGeoTask = false } = {}) {
  if (!preserveGeoTask) {
    state.selectedGeoTaskId = null;
  }
  state.selectedBuildingId = buildingId;
  await loadSelectedBuildingDetail();
  render();
}

async function selectFloor(floorNo, { preserveGeoTask = false } = {}) {
  if (!preserveGeoTask) {
    state.selectedGeoTaskId = null;
  }
  state.selectedFloorNo = floorNo;
  await loadSelectedFloorDetail();
  render();
}




















function currentGeoTaskSourceDetail() {
  if (state.selectedGeoAssetRunDetail) {
    return state.selectedGeoAssetRunDetail;
  }
  if (state.selectedGeoAssetRunId && canUseDemoFallback()) {
    return buildFallbackGeoAssetRunDetail(state.selectedGeoAssetRunId, state.selectedGeoBaselineRunId);
  }
  return null;
}



function getGeoTaskWatchlistItems(limit = 8) {
  const detail = currentGeoTaskSourceDetail();
  const tasks = (detail?.coverageTasks ?? [])
    .filter((task) => geoTaskIsOpen(task))
    .filter((task) => state.districtFilter === "all" || task.districtId === state.districtFilter)
    .slice()
    .sort(compareGeoTaskPriority);
  return tasks.slice(0, limit);
}



function getBrowserSamplingPackItems(limit = 8) {
  const tasks = (state.browserSamplingPackItems ?? [])
    .filter((task) => state.districtFilter === "all" || task.districtId === state.districtFilter)
    .slice()
    .sort(compareBrowserSamplingTask);
  return tasks.slice(0, limit);
}

function getOpenBrowserSamplingTasks() {
  return (state.browserSamplingPackItems ?? [])
    .filter((task) => state.districtFilter === "all" || task.districtId === state.districtFilter)
    .filter((task) => browserSamplingCoverageState(task) !== "resolved")
    .slice()
    .sort(compareBrowserSamplingMapTask);
}



function getBrowserSamplingTaskMaps() {
  const tasks = getOpenBrowserSamplingTasks();
  const communityMap = new Map();
  const buildingMap = new Map();
  const floorMap = new Map();

  tasks.forEach((task) => {
    setBestBrowserSamplingTask(communityMap, task.communityId, task);
    setBestBrowserSamplingTask(buildingMap, task.buildingId, task);
    setBestBrowserSamplingTask(floorMap, browserSamplingTaskKey(task), task);
  });

  return { tasks, communityMap, buildingMap, floorMap };
}

function browserSamplingBadgeCounter(task) {
  const stateLabel = browserSamplingCoverageState(task);
  const reviewCount = browserCapturePendingAttentionCount(task);
  const missingCount = browserSamplingMissingCount(task);
  return String(
    stateLabel === "needs_review" ? reviewCount || 1 : missingCount > 9 ? "9+" : Math.max(missingCount, 1)
  );
}

function browserSamplingCountSummary(task) {
  const current = browserSamplingCurrentCount(task);
  const target = browserSamplingTargetCount(task);
  const prefix = task?.targetGranularity === "floor" ? "样本对" : "样本";
  return `${prefix} ${current}/${target || current || 0}`;
}

function browserSamplingTaskInfoHtml(task) {
  if (!task) {
    return "";
  }
  return renderAmapInfoCard({
    kicker: "公开页采样任务",
    title: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}`,
    subtitle: `${task.districtName ?? "未知行政区"} · ${task.taskTypeLabel ?? task.taskType ?? "公开页采样"}`,
    stats: [
      { label: "任务状态", value: browserSamplingCoverageLabel(task), tone: "warning" },
      { label: "覆盖进度", value: browserSamplingCountSummary(task), tone: "neutral" },
      { label: "优先分", value: `${task.priorityScore ?? 0}`, tone: "score" },
      task.currentYieldPct != null
        ? { label: "当前回报", value: `${Number(task.currentYieldPct).toFixed(2)}%`, tone: "yield" }
        : null
    ],
    note: task.captureGoal ?? task.reason ?? "等待补齐公开页原文。",
    footer: task.latestCaptureAt ? `最近采样 ${formatTimestamp(task.latestCaptureAt)}` : "最近采样待补",
    actionHint: "点击后会切到公开页采样执行台，并把对应楼栋/楼层证据一并展开。"
  });
}

function renderAmapInfoCard({ kicker = "", title = "", subtitle = "", stats = [], note = "", footer = "", actionHint = "" } = {}) {
  const cards = stats
    .filter(Boolean)
    .map(
      (item) => `
        <div class="amap-card__stat amap-card__stat--${item.tone ?? "neutral"}">
          <span class="amap-card__stat-label">${item.label}</span>
          <strong class="amap-card__stat-value">${item.value}</strong>
        </div>
      `
    )
    .join("");

  return `
    <div class="amap-info-window-shell">
      <section class="amap-card">
        ${kicker ? `<p class="amap-card__kicker">${kicker}</p>` : ""}
        ${title ? `<h3 class="amap-card__title">${title}</h3>` : ""}
        ${subtitle ? `<p class="amap-card__subtitle">${subtitle}</p>` : ""}
        ${cards ? `<div class="amap-card__stats">${cards}</div>` : ""}
        ${note ? `<p class="amap-card__note">${note}</p>` : ""}
        ${actionHint ? `<p class="amap-card__action">${actionHint}</p>` : ""}
        ${footer ? `<p class="amap-card__footer">${footer}</p>` : ""}
      </section>
    </div>
  `;
}

async function navigateToBrowserSamplingTask(
  task,
  {
    resetDraft = false,
    waypoint = null,
    revealLatestCaptureRun = "auto",
    preferredReviewRunId = null,
    preferredReviewQueueId = null,
    syncDistrictScope = true,
  } = {}
) {
  if (!task?.taskId) {
    return;
  }
  if (syncDistrictScope && task?.districtId && task.districtId !== state.districtFilter) {
    await applyDistrictScope(task.districtId, {
      backgroundHydration: true,
      preserveBrowserSamplingTaskId: task.taskId,
    });
  }
  if (!(state.browserSamplingPackItems ?? []).some((item) => item.taskId === task.taskId)) {
    upsertBrowserSamplingTask(task, { pinSelection: false });
  }
  selectBrowserSamplingTask(task.taskId, { resetDraft });
  await navigateToEvidenceTarget(task.communityId, task.buildingId || null, task.floorNo || null, {
    waypoint:
      waypoint ??
      {
        source: "browser_sampling",
        label: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}`,
        detail: "公开页采样执行台与对应证据"
      }
  });
  const reviewRunId = preferredReviewRunId ?? task.pendingReviewRunId ?? task.latestCaptureRunId ?? null;
  const shouldRevealAttentionRun =
    Boolean(reviewRunId) &&
    (revealLatestCaptureRun === true || (revealLatestCaptureRun === "auto" && browserCapturePendingAttentionCount(task) > 0));
  if (shouldRevealAttentionRun) {
    await loadSelectedBrowserCaptureRunDetail(reviewRunId, {
      preferredQueueId: preferredReviewQueueId ?? task.pendingReviewQueueId ?? null,
    });
  }
}

function currentBrowserSamplingTask() {
  const tasks = state.browserSamplingPackItems ?? [];
  return tasks.find((task) => task.taskId === state.selectedBrowserSamplingTaskId) ?? tasks[0] ?? null;
}

function getBrowserCaptureRunItems(limit = 6, { taskId = null, districtId = null } = {}) {
  const runs = (effectiveOperationsOverview().browserCaptureRuns ?? [])
    .filter((run) => !districtId || districtId === "all" || run.districtId === districtId)
    .filter((run) => !taskId || run.taskId === taskId)
    .slice()
    .sort(compareCreatedAtDesc);
  return runs.slice(0, limit);
}

function currentBrowserCaptureRun() {
  const selectedRunId = state.selectedBrowserCaptureRunId;
  if (!selectedRunId) {
    return null;
  }
  return state.selectedBrowserCaptureRunDetail?.runId === selectedRunId ? state.selectedBrowserCaptureRunDetail : null;
}





function currentBrowserCaptureReviewQueue() {
  return currentBrowserCaptureRun()?.reviewQueue ?? [];
}

function currentPendingBrowserCaptureReviewItems() {
  return currentBrowserCaptureReviewQueue().filter((item) => String(item?.status ?? "pending") === "pending");
}

function syncBrowserCaptureReviewBatchSelection(reviewQueue = currentBrowserCaptureReviewQueue()) {
  const pendingQueueIds = new Set(
    (reviewQueue ?? [])
      .filter((item) => String(item?.status ?? "pending") === "pending")
      .map((item) => item?.queueId)
      .filter(Boolean)
  );
  const nextSelection = (state.selectedBrowserCaptureReviewQueueIds ?? []).filter((queueId) => pendingQueueIds.has(queueId));
  if (nextSelection.length !== (state.selectedBrowserCaptureReviewQueueIds ?? []).length) {
    state.selectedBrowserCaptureReviewQueueIds = nextSelection;
  }
  return nextSelection;
}

function clearBrowserCaptureReviewBatchSelection() {
  state.selectedBrowserCaptureReviewQueueIds = [];
}

function currentBrowserCaptureReviewBatchSelection(reviewQueue = currentBrowserCaptureReviewQueue()) {
  return syncBrowserCaptureReviewBatchSelection(reviewQueue).slice();
}

function toggleBrowserCaptureReviewBatchSelection(queueId, selected = null, reviewQueue = currentBrowserCaptureReviewQueue()) {
  const normalizedQueueId = String(queueId || "").trim();
  if (!normalizedQueueId) {
    return currentBrowserCaptureReviewBatchSelection(reviewQueue);
  }
  const pendingQueueIds = new Set(
    (reviewQueue ?? [])
      .filter((item) => String(item?.status ?? "pending") === "pending")
      .map((item) => item?.queueId)
      .filter(Boolean)
  );
  if (!pendingQueueIds.has(normalizedQueueId)) {
    return currentBrowserCaptureReviewBatchSelection(reviewQueue);
  }
  const selection = new Set(currentBrowserCaptureReviewBatchSelection(reviewQueue));
  const shouldSelect = selected == null ? !selection.has(normalizedQueueId) : Boolean(selected);
  if (shouldSelect) {
    selection.add(normalizedQueueId);
  } else {
    selection.delete(normalizedQueueId);
  }
  state.selectedBrowserCaptureReviewQueueIds = Array.from(selection);
  return state.selectedBrowserCaptureReviewQueueIds.slice();
}

function selectAllBrowserCaptureReviewBatchItems(reviewQueue = currentBrowserCaptureReviewQueue()) {
  state.selectedBrowserCaptureReviewQueueIds = (reviewQueue ?? [])
    .filter((item) => String(item?.status ?? "pending") === "pending")
    .map((item) => item?.queueId)
    .filter(Boolean);
  return state.selectedBrowserCaptureReviewQueueIds.slice();
}

function currentBrowserReviewInboxItemId() {
  const runId = currentBrowserCaptureRun()?.runId ?? null;
  const queueId = state.selectedBrowserCaptureReviewQueueId ?? null;
  return runId && queueId ? `${runId}:${queueId}` : null;
}

function browserReviewInboxSummaryFallback() {
  return {
    pendingQueueCount: 0,
    pendingTaskCount: 0,
    pendingDistrictCount: 0,
    oldestPendingAt: null,
    latestPendingAt: null,
  };
}

function browserReviewInboxItems({ districtId = null, preferDistrict = false } = {}) {
  const items = state.browserReviewInboxItems ?? [];
  if (!districtId || districtId === "all") {
    return items.slice();
  }
  const sameDistrictItems = items.filter((item) => item?.districtId === districtId);
  if (preferDistrict && sameDistrictItems.length) {
    return sameDistrictItems;
  }
  return preferDistrict ? items.slice() : sameDistrictItems;
}

function browserReviewInboxTaskSnapshot(item) {
  if (!item) {
    return null;
  }
  return {
    ...(item.task ?? {}),
    taskId: item.taskId ?? item.task?.taskId ?? null,
    taskType: item.taskType ?? item.task?.taskType ?? null,
    taskTypeLabel: item.taskTypeLabel ?? item.task?.taskTypeLabel ?? "公开页采样",
    targetGranularity: item.targetGranularity ?? item.task?.targetGranularity ?? null,
    focusScope: item.focusScope ?? item.task?.focusScope ?? null,
    priorityScore: item.priorityScore ?? item.task?.priorityScore ?? 0,
    priorityLabel: item.priorityLabel ?? item.task?.priorityLabel ?? "公开页采样",
    districtId: item.districtId ?? item.task?.districtId ?? null,
    districtName: item.districtName ?? item.task?.districtName ?? null,
    communityId: item.communityId ?? item.task?.communityId ?? null,
    communityName: item.communityName ?? item.task?.communityName ?? null,
    buildingId: item.buildingId ?? item.task?.buildingId ?? null,
    buildingName: item.buildingName ?? item.task?.buildingName ?? null,
    floorNo: item.floorNo ?? item.task?.floorNo ?? null,
    pendingReviewRunId: item.runId ?? item.task?.pendingReviewRunId ?? null,
    pendingReviewQueueId: item.queueId ?? item.task?.pendingReviewQueueId ?? null,
    pendingAttentionCount: item.taskPendingAttentionCount ?? item.task?.pendingAttentionCount ?? 1,
    taskLifecycleStatus: "needs_review",
    taskLifecycleLabel: "已采待复核",
  };
}

function getBrowserReviewInboxQueue(task = currentBrowserSamplingTask(), { excludeCurrent = false } = {}) {
  const districtId = task?.districtId ?? (state.districtFilter !== "all" ? state.districtFilter : null);
  const allItems = state.browserReviewInboxItems ?? [];
  const districtItems = browserReviewInboxItems({ districtId });
  let preferredItems = browserReviewInboxItems({ districtId, preferDistrict: true });
  const currentInboxItemId = currentBrowserReviewInboxItemId();
  if (excludeCurrent && currentInboxItemId) {
    preferredItems = preferredItems.filter((item) => item.inboxItemId !== currentInboxItemId);
  }
  if (!preferredItems.length && excludeCurrent && currentInboxItemId) {
    preferredItems = allItems.filter((item) => item.inboxItemId !== currentInboxItemId);
  }
  if (!preferredItems.length) {
    preferredItems = excludeCurrent && currentInboxItemId ? allItems.filter((item) => item.inboxItemId !== currentInboxItemId) : allItems.slice();
  }
  return {
    allItems,
    districtItems,
    previewItems: browserReviewInboxItems({ districtId, preferDistrict: true }).slice(0, 4),
    nextItem: preferredItems[0] ?? null,
  };
}

async function navigateToBrowserReviewInboxItem(item, { resetDraft = false } = {}) {
  if (!item?.taskId) {
    return;
  }
  const task = browserReviewInboxTaskSnapshot(item);
  await navigateToBrowserSamplingTask(task, {
    resetDraft,
    revealLatestCaptureRun: true,
    preferredReviewRunId: item.runId ?? null,
    preferredReviewQueueId: item.queueId ?? null,
    syncDistrictScope: true,
  });
}

function currentBrowserCaptureSubmission() {
  const submission = state.lastBrowserCaptureSubmission;
  if (!submission?.taskId || submission.status !== "success") {
    return null;
  }
  return submission;
}

function currentBrowserCaptureReviewAction() {
  const action = state.lastBrowserCaptureReviewAction;
  if (!action?.runId || action.status !== "success") {
    return null;
  }
  return action;
}











function browserSamplingCaptureCandidateState(task) {
  return ["needs_capture", "in_progress"].includes(browserSamplingCoverageState(task));
}

function getBrowserSamplingWorkbenchQueue(task = currentBrowserSamplingTask()) {
  const openTasks = (state.browserSamplingPackItems ?? [])
    .filter((item) => item.taskId !== task?.taskId)
    .filter((item) => browserSamplingCoverageState(item) !== "resolved")
    .slice()
    .sort(compareBrowserSamplingMapTask);
  const sameDistrictOpenTasks = task?.districtId
    ? openTasks.filter((item) => item.districtId === task.districtId)
    : [];
  const captureTasks = openTasks.filter((item) => browserSamplingCaptureCandidateState(item));
  const sameDistrictCaptureTasks = sameDistrictOpenTasks.filter((item) => browserSamplingCaptureCandidateState(item));
  const previewTasks = (sameDistrictOpenTasks.length ? sameDistrictOpenTasks : openTasks).slice(0, 4);
  const taskPool = sameDistrictOpenTasks.length ? sameDistrictOpenTasks : openTasks;
  const reviewInbox = getBrowserReviewInboxQueue(task, { excludeCurrent: true });
  const nextReviewItem = reviewInbox.nextItem ?? null;
  const nextReviewTask = nextReviewItem ? browserReviewInboxTaskSnapshot(nextReviewItem) : null;
  return {
    districtTasks: taskPool,
    nextDistrictTask: sameDistrictCaptureTasks[0] ?? captureTasks[0] ?? sameDistrictOpenTasks[0] ?? openTasks[0] ?? null,
    nextReviewTask,
    nextReviewItem,
    nextCaptureTask: sameDistrictCaptureTasks[0] ?? captureTasks[0] ?? null,
    previewTasks,
    reviewPreviewItems: reviewInbox.previewItems,
    reviewDistrictCount: reviewInbox.districtItems.length,
    reviewTotalCount: reviewInbox.allItems.length,
  };
}

function findPostSubmitBrowserSamplingTask(sourceTask) {
  const sourceTaskId = sourceTask?.taskId ?? null;
  const sourceDistrictId = sourceTask?.districtId ?? null;
  const candidateTasks = (state.browserSamplingPackItems ?? [])
    .filter((item) => item?.taskId && item.taskId !== sourceTaskId && browserSamplingCaptureCandidateState(item))
    .slice()
    .sort(compareBrowserSamplingMapTask);
  const sameDistrictTasks = sourceDistrictId
    ? candidateTasks.filter((item) => item.districtId === sourceDistrictId)
    : [];
  return sameDistrictTasks[0] ?? candidateTasks[0] ?? null;
}

function browserSamplingTaskById(taskId) {
  if (!taskId) {
    return null;
  }
  return (state.browserSamplingPackItems ?? []).find((item) => item.taskId === taskId) ?? null;
}

function browserReviewInboxItemByTarget({ inboxItemId = null, runId = null, queueId = null, taskId = null } = {}) {
  const items = state.browserReviewInboxItems ?? [];
  if (inboxItemId) {
    const directMatch = items.find((item) => item?.inboxItemId === inboxItemId);
    if (directMatch) {
      return directMatch;
    }
  }
  if (runId && queueId) {
    const runQueueMatch = items.find((item) => item?.runId === runId && item?.queueId === queueId);
    if (runQueueMatch) {
      return runQueueMatch;
    }
  }
  if (taskId) {
    return items.find((item) => item?.taskId === taskId) ?? null;
  }
  return null;
}

function buildBrowserCaptureReviewWorkflowLocalItem(runId, queueItem, task) {
  if (!runId || !queueItem?.queueId || !task?.taskId) {
    return null;
  }
  return {
    inboxItemId: `${runId}:${queueItem.queueId}`,
    runId,
    queueId: queueItem.queueId,
    taskId: task.taskId,
    task: task,
    taskLabel: browserSamplingTaskLabel(task),
    districtId: task.districtId ?? null,
    districtName: task.districtName ?? null,
    communityId: task.communityId ?? null,
    communityName: task.communityName ?? null,
    buildingId: task.buildingId ?? null,
    buildingName: task.buildingName ?? null,
    floorNo: task.floorNo ?? null,
    taskPendingAttentionCount: browserCapturePendingAttentionCount(task),
    businessType: queueItem.businessType ?? null,
    businessTypeLabel: queueItem.businessTypeLabel ?? null,
    sourceListingId: queueItem.sourceListingId ?? null,
    attention: Array.isArray(queueItem.attention) ? queueItem.attention : [],
  };
}

function resolveBrowserCaptureReviewWorkflowTarget(
  {
    workflow = {},
    workflowAction = "stay_current",
    runId = null,
    sourceTask = null,
    refreshedSourceTask = null,
    refreshedCurrentRun = null,
  } = {}
) {
  const workflowItem = workflow?.item ?? null;
  const workflowRunId = workflow?.runId ?? workflowItem?.runId ?? null;
  const workflowQueueId = workflow?.queueId ?? workflowItem?.queueId ?? null;
  const workflowTaskId = workflow?.taskId ?? workflowItem?.taskId ?? workflow?.task?.taskId ?? null;
  const matchedWorkflowItem = browserReviewInboxItemByTarget({
    inboxItemId: workflowItem?.inboxItemId ?? null,
    runId: workflowRunId,
    queueId: workflowQueueId,
    taskId: workflowTaskId,
  });
  const resolvedWorkflowItem = matchedWorkflowItem ?? (workflowItem?.taskId ? workflowItem : null);
  const resolvedWorkflowTask =
    browserReviewInboxTaskSnapshot(resolvedWorkflowItem) ??
    browserSamplingTaskById(workflowTaskId) ??
    workflow?.task ??
    refreshedSourceTask ??
    sourceTask ??
    null;
  if (resolvedWorkflowItem?.taskId) {
    return {
      item: resolvedWorkflowItem,
      task: resolvedWorkflowTask,
      workflowRunId: workflowRunId ?? resolvedWorkflowItem.runId ?? null,
      workflowQueueId: workflowQueueId ?? resolvedWorkflowItem.queueId ?? null,
      workflowTaskId: workflowTaskId ?? resolvedWorkflowItem.taskId ?? resolvedWorkflowTask?.taskId ?? null,
      workflowItemProvided: Boolean(workflowItem),
      resolution: "workflow_item",
    };
  }
  if ((workflowRunId || workflowQueueId || workflowTaskId) && resolvedWorkflowTask?.taskId) {
    return {
      item: {
        inboxItemId:
          workflowRunId && workflowQueueId
            ? `${workflowRunId}:${workflowQueueId}`
            : `${resolvedWorkflowTask.taskId}:${workflowQueueId ?? "review-target"}`,
        runId: workflowRunId ?? resolvedWorkflowTask.pendingReviewRunId ?? null,
        queueId: workflowQueueId ?? resolvedWorkflowTask.pendingReviewQueueId ?? null,
        taskId: resolvedWorkflowTask.taskId,
        task: resolvedWorkflowTask,
        taskLabel: browserSamplingTaskLabel(resolvedWorkflowTask),
      },
      task: resolvedWorkflowTask,
      workflowRunId: workflowRunId ?? resolvedWorkflowTask.pendingReviewRunId ?? null,
      workflowQueueId: workflowQueueId ?? resolvedWorkflowTask.pendingReviewQueueId ?? null,
      workflowTaskId: workflowTaskId ?? resolvedWorkflowTask.taskId ?? null,
      workflowItemProvided: Boolean(workflowItem),
      resolution: "workflow_identifiers",
    };
  }
  if (workflowAction === "review_current_run") {
    const pendingQueueItem = (refreshedCurrentRun?.reviewQueue ?? []).find((item) => String(item?.status ?? "pending") === "pending");
    const localItem = buildBrowserCaptureReviewWorkflowLocalItem(runId, pendingQueueItem, refreshedSourceTask ?? sourceTask);
    if (localItem) {
      return {
        item: localItem,
        task: browserReviewInboxTaskSnapshot(localItem),
        workflowRunId: localItem.runId,
        workflowQueueId: localItem.queueId,
        workflowTaskId: localItem.taskId,
        workflowItemProvided: false,
        resolution: "fallback_current_run",
      };
    }
  }
  if (workflowAction === "review_current_task") {
    const currentTaskItem = browserReviewInboxItemByTarget({
      runId: refreshedSourceTask?.pendingReviewRunId ?? null,
      queueId: refreshedSourceTask?.pendingReviewQueueId ?? null,
      taskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    });
    if (currentTaskItem?.taskId) {
      return {
        item: currentTaskItem,
        task: browserReviewInboxTaskSnapshot(currentTaskItem),
        workflowRunId: currentTaskItem.runId ?? null,
        workflowQueueId: currentTaskItem.queueId ?? null,
        workflowTaskId: currentTaskItem.taskId ?? null,
        workflowItemProvided: false,
        resolution: "fallback_current_task",
      };
    }
  }
  if (workflowAction === "advance_next_review") {
    const nextReviewItem = getBrowserReviewInboxQueue(refreshedSourceTask ?? sourceTask, { excludeCurrent: true }).nextItem;
    if (nextReviewItem?.taskId) {
      return {
        item: nextReviewItem,
        task: browserReviewInboxTaskSnapshot(nextReviewItem),
        workflowRunId: nextReviewItem.runId ?? null,
        workflowQueueId: nextReviewItem.queueId ?? null,
        workflowTaskId: nextReviewItem.taskId ?? null,
        workflowItemProvided: false,
        resolution: "fallback_next_review",
      };
    }
  }
  return {
    item: null,
    task: refreshedSourceTask ?? sourceTask ?? null,
    workflowRunId: workflowRunId ?? null,
    workflowQueueId: workflowQueueId ?? null,
    workflowTaskId: workflowTaskId ?? refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    workflowItemProvided: false,
    resolution: "fallback_source_task",
  };
}

function resolvePostSubmitBrowserSamplingTask(
  {
    workflow = {},
    workflowAction = "stay_current",
    sourceTask = null,
    refreshedSourceTask = null,
  } = {}
) {
  const workflowTaskId = workflow?.taskId ?? workflow?.task?.taskId ?? null;
  const workflowTask = browserSamplingTaskById(workflowTaskId) ?? workflow?.task ?? null;
  if (workflowTask?.taskId) {
    return {
      task: workflowTask,
      workflowTaskId: workflowTask.taskId ?? workflowTaskId ?? null,
      workflowTaskProvided: true,
      resolution: "workflow_task",
    };
  }
  if (workflowTaskId) {
    return {
      task: refreshedSourceTask ?? sourceTask ?? null,
      workflowTaskId,
      workflowTaskProvided: true,
      resolution: "workflow_task_missing_snapshot",
    };
  }
  if (workflowAction === "advance_next_capture") {
    const fallbackTask = findPostSubmitBrowserSamplingTask(refreshedSourceTask ?? sourceTask);
    if (fallbackTask?.taskId) {
      return {
        task: fallbackTask,
        workflowTaskId: null,
        workflowTaskProvided: false,
        resolution: "fallback_queue_task",
      };
    }
  }
  return {
    task: refreshedSourceTask ?? sourceTask ?? null,
    workflowTaskId: null,
    workflowTaskProvided: false,
    resolution: "fallback_source_task",
  };
}

function applyBrowserSamplingTaskProgress(taskSnapshot, taskProgress) {
  if (!taskSnapshot || !taskProgress) {
    return taskSnapshot;
  }
  const nextSnapshot = { ...taskSnapshot };
  const afterCount = Number(taskProgress.afterCount ?? browserSamplingCurrentCount(taskSnapshot));
  const targetCount = Number(taskProgress.targetCount ?? browserSamplingTargetCount(taskSnapshot));
  const missingCount = Number(taskProgress.missingCount ?? Math.max(targetCount - afterCount, 0));
  if (nextSnapshot.targetGranularity === "floor") {
    nextSnapshot.currentPairCount = afterCount;
    nextSnapshot.targetPairCount = targetCount;
    nextSnapshot.missingPairCount = missingCount;
  }
  nextSnapshot.currentSampleSize = afterCount;
  nextSnapshot.targetSampleSize = targetCount;
  nextSnapshot.missingSampleCount = missingCount;
  return nextSnapshot;
}

function buildBrowserCaptureSubmission(task, body, optimisticRun, optimisticTask) {
  const workflow = body?.workflow ?? {};
  const taskProgress = body?.taskProgress ?? {};
  const taskLabel = browserSamplingTaskLabel(task);
  const workflowAction = workflow.action ?? (Number(optimisticRun?.attentionCount ?? 0) > 0 ? "review_current_capture" : "stay_current");
  const resolvedPostSubmitTask = resolvePostSubmitBrowserSamplingTask({
    workflow,
    workflowAction,
    sourceTask: task,
    refreshedSourceTask: optimisticTask ?? task,
  });
  return {
    status: "success",
    taskId: task?.taskId ?? null,
    taskLabel,
    taskProgress: {
      beforeCount: Number(taskProgress.beforeCount ?? browserSamplingCurrentCount(task)),
      afterCount: Number(taskProgress.afterCount ?? browserSamplingCurrentCount(optimisticTask ?? task)),
      targetCount: Number(taskProgress.targetCount ?? browserSamplingTargetCount(optimisticTask ?? task)),
      missingCount: Number(taskProgress.missingCount ?? browserSamplingMissingCount(optimisticTask ?? task)),
      status: taskProgress.status ?? browserSamplingCoverageState(optimisticTask ?? task),
    },
    workflowAction,
    workflowReason: workflow.reason ?? (Number(optimisticRun?.attentionCount ?? 0) > 0 ? "attention_detected" : "no_pending_task"),
    workflowTaskId: resolvedPostSubmitTask.workflowTaskId,
    workflowTaskProvided: resolvedPostSubmitTask.workflowTaskProvided,
    postSubmitTaskResolution: resolvedPostSubmitTask.resolution,
    postSubmitTaskId: resolvedPostSubmitTask.task?.taskId ?? task?.taskId ?? null,
    postSubmitTaskLabel: browserSamplingTaskLabel(resolvedPostSubmitTask.task ?? task),
    captureRunId: body.captureRunId ?? null,
    importRunId: body.importRunId ?? null,
    metricsRunId: body.metricsRun?.runId ?? null,
    createdAt: optimisticRun.createdAt ?? new Date().toISOString(),
    attentionCount: Number(optimisticRun.attentionCount ?? 0),
    reviewPendingCount: browserCapturePendingAttentionCount(optimisticRun),
    reviewInboxPendingCount: Number(body?.reviewInboxSummary?.pendingQueueCount ?? state.browserReviewInboxSummary?.pendingQueueCount ?? 0),
    metricsBatchName: body.metricsRun?.batchName ?? null,
    autoFilledChannels: [],
  };
}

function browserSamplingInstructionText(task) {
  if (!task) {
    return "";
  }
  return [
    `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""} · ${task.districtName ?? "未知行政区"}`,
    `状态：${browserSamplingCoverageLabel(task)} · ${task.sampleStatusLabel ?? "状态待补"}`,
    task.captureGoal ? `目标：${task.captureGoal}` : "",
    task.reason ? `原因：${task.reason}` : "",
    task.saleQuery ? `Sale 检索：${task.saleQuery}` : "",
    task.rentQuery ? `Rent 检索：${task.rentQuery}` : "",
    task.targetQuery ? `目标检索：${task.targetQuery}` : ""
  ]
    .filter(Boolean)
    .join("\n");
}

function browserCaptureLifecycleStatus(pendingAttentionCount) {
  return Number(pendingAttentionCount || 0) > 0 ? "needs_review" : "captured";
}

function browserCaptureLifecycleLabel(pendingAttentionCount) {
  return Number(pendingAttentionCount || 0) > 0 ? "已采待复核" : "已采仍需补采";
}







function browserSamplingCoveragePayload() {
  const tasks = (state.browserSamplingPackItems ?? [])
    .filter((task) => state.districtFilter === "all" || task.districtId === state.districtFilter)
    .slice();

  const districtsMap = new Map();
  const communitiesMap = new Map();

  tasks.forEach((task) => {
    const districtKey = task.districtId ?? task.districtName ?? "unknown";
    const districtEntry =
      districtsMap.get(districtKey) ??
      {
        districtId: task.districtId ?? null,
        districtName: task.districtName ?? "未知行政区",
        taskCount: 0,
        completedTaskCount: 0,
        reviewTaskCount: 0,
        inProgressTaskCount: 0,
        targetCount: 0,
        currentCount: 0,
        priorityScore: 0,
        latestCaptureAt: null,
        missingCount: 0,
        highestPriorityTask: task,
        outstandingTask: task
      };

    districtEntry.taskCount += 1;
    districtEntry.targetCount += browserSamplingTargetCount(task);
    districtEntry.currentCount += Math.min(browserSamplingCurrentCount(task), browserSamplingTargetCount(task) || browserSamplingCurrentCount(task));
    districtEntry.missingCount += browserSamplingMissingCount(task);
    districtEntry.priorityScore = Math.max(districtEntry.priorityScore, Number(task.priorityScore ?? 0));
    if (comparableTimestamp(task.latestCaptureAt) > comparableTimestamp(districtEntry.latestCaptureAt)) {
      districtEntry.latestCaptureAt = task.latestCaptureAt ?? districtEntry.latestCaptureAt;
    }
    if (compareBrowserSamplingTask(task, districtEntry.highestPriorityTask) < 0) {
      districtEntry.highestPriorityTask = task;
    }
    const currentDistrictOutstanding = districtEntry.outstandingTask;
    const currentDistrictOutstandingMissing = browserSamplingMissingCount(currentDistrictOutstanding);
    const candidateDistrictMissing = browserSamplingMissingCount(task);
    if (
      !currentDistrictOutstanding ||
      candidateDistrictMissing > currentDistrictOutstandingMissing ||
      (candidateDistrictMissing === currentDistrictOutstandingMissing && compareBrowserSamplingTask(task, currentDistrictOutstanding) < 0)
    ) {
      districtEntry.outstandingTask = task;
    }

    const taskState = browserSamplingCoverageState(task);
    if (taskState === "resolved") {
      districtEntry.completedTaskCount += 1;
    } else if (taskState === "needs_review") {
      districtEntry.reviewTaskCount += 1;
    } else if (taskState === "in_progress") {
      districtEntry.inProgressTaskCount += 1;
    }
    districtsMap.set(districtKey, districtEntry);

    const communityKey = task.communityId ?? `${districtKey}:${task.communityName ?? task.taskId ?? "unknown"}`;
    const communityEntry =
      communitiesMap.get(communityKey) ??
      {
        communityId: task.communityId ?? null,
        communityName: task.communityName ?? "待识别小区",
        districtId: task.districtId ?? null,
        districtName: task.districtName ?? "未知行政区",
        focusScope: task.focusScope ?? "citywide",
        taskCount: 0,
        completedTaskCount: 0,
        reviewTaskCount: 0,
        inProgressTaskCount: 0,
        targetCount: 0,
        currentCount: 0,
        missingCount: 0,
        latestCaptureAt: null,
        pendingAttentionCount: 0,
        highestPriorityTask: task,
        outstandingTask: task,
        taskItems: []
      };

    communityEntry.taskCount += 1;
    communityEntry.targetCount += browserSamplingTargetCount(task);
    communityEntry.currentCount += Math.min(browserSamplingCurrentCount(task), browserSamplingTargetCount(task) || browserSamplingCurrentCount(task));
    communityEntry.missingCount += browserSamplingMissingCount(task);
    communityEntry.taskItems.push(task);
    communityEntry.pendingAttentionCount += browserCapturePendingAttentionCount(task);
    if (comparableTimestamp(task.latestCaptureAt) > comparableTimestamp(communityEntry.latestCaptureAt)) {
      communityEntry.latestCaptureAt = task.latestCaptureAt ?? communityEntry.latestCaptureAt;
    }
    if (compareBrowserSamplingTask(task, communityEntry.highestPriorityTask) < 0) {
      communityEntry.highestPriorityTask = task;
    }
    const currentOutstanding = communityEntry.outstandingTask;
    const currentOutstandingMissing = browserSamplingMissingCount(currentOutstanding);
    const candidateMissing = browserSamplingMissingCount(task);
    if (
      !currentOutstanding ||
      candidateMissing > currentOutstandingMissing ||
      (candidateMissing === currentOutstandingMissing && compareBrowserSamplingTask(task, currentOutstanding) < 0)
    ) {
      communityEntry.outstandingTask = task;
    }

    if (taskState === "resolved") {
      communityEntry.completedTaskCount += 1;
    } else if (taskState === "needs_review") {
      communityEntry.reviewTaskCount += 1;
    } else if (taskState === "in_progress") {
      communityEntry.inProgressTaskCount += 1;
    }
    communitiesMap.set(communityKey, communityEntry);
  });

  const districts = Array.from(districtsMap.values())
    .map((entry) => ({
      ...entry,
      completionPct:
        entry.targetCount > 0
          ? Math.max(0, Math.min(100, Math.round((entry.currentCount / entry.targetCount) * 100)))
          : 0
    }))
    .sort(
      (left, right) =>
        Number(right.reviewTaskCount ?? 0) - Number(left.reviewTaskCount ?? 0) ||
        Number(left.completionPct ?? 0) - Number(right.completionPct ?? 0) ||
        Number(right.priorityScore ?? 0) - Number(left.priorityScore ?? 0) ||
        String(left.districtName ?? "").localeCompare(String(right.districtName ?? ""))
    );

  const communities = Array.from(communitiesMap.values())
    .map((entry) => ({
      ...entry,
      completionPct:
        entry.targetCount > 0
          ? Math.max(0, Math.min(100, Math.round((entry.currentCount / entry.targetCount) * 100)))
          : 0
    }))
    .sort(
      (left, right) =>
        Number(right.reviewTaskCount ?? 0) - Number(left.reviewTaskCount ?? 0) ||
        Number(right.missingCount ?? 0) - Number(left.missingCount ?? 0) ||
        compareBrowserSamplingTask(right.highestPriorityTask, left.highestPriorityTask) ||
        String(left.communityName ?? "").localeCompare(String(right.communityName ?? ""))
    );

  return {
    tasks,
    districts,
    communities,
    summary: {
      taskCount: tasks.length,
      districtCount: districts.length,
      communityCount: communities.length,
      resolvedTaskCount: tasks.filter((task) => browserSamplingCoverageState(task) === "resolved").length,
      reviewTaskCount: tasks.filter((task) => browserSamplingCoverageState(task) === "needs_review").length,
      inProgressTaskCount: tasks.filter((task) => browserSamplingCoverageState(task) === "in_progress").length,
      pendingTaskCount: tasks.filter((task) => browserSamplingCoverageState(task) === "needs_capture").length
    }
  };
}

function buildOptimisticBrowserCaptureRun(task, body) {
  const summary = body?.summary ?? {};
  const attentionCount = Number(summary.attention_count ?? (body?.attention ?? []).length ?? 0);
  const pendingAttentionCount = Number(body?.reviewSummary?.pendingCount ?? attentionCount);
  const taskSnapshot = body?.task ?? task ?? {};
  const createdAt = taskSnapshot?.latestCaptureAt ?? new Date().toISOString();
  return {
    runId: body?.captureRunId ?? null,
    providerId: "public-browser-sampling",
    taskId: taskSnapshot?.taskId ?? task?.taskId ?? null,
    taskType: taskSnapshot?.taskType ?? task?.taskType ?? null,
    taskTypeLabel: taskSnapshot?.taskTypeLabel ?? task?.taskTypeLabel ?? "公开页采样",
    districtId: taskSnapshot?.districtId ?? task?.districtId ?? null,
    districtName: taskSnapshot?.districtName ?? task?.districtName ?? null,
    communityId: taskSnapshot?.communityId ?? task?.communityId ?? null,
    communityName: taskSnapshot?.communityName ?? task?.communityName ?? null,
    buildingId: taskSnapshot?.buildingId ?? task?.buildingId ?? null,
    buildingName: taskSnapshot?.buildingName ?? task?.buildingName ?? null,
    floorNo: taskSnapshot?.floorNo ?? task?.floorNo ?? null,
    createdAt,
    captureCount: Number(summary.capture_count ?? 0),
    saleCaptureCount: Number(summary.sale_capture_count ?? 0),
    rentCaptureCount: Number(summary.rent_capture_count ?? 0),
    attentionCount,
    attentionPreview: Array.isArray(body?.attention) ? body.attention : [],
    pendingAttentionCount,
    pendingReviewQueueId: body?.task?.pendingReviewQueueId ?? null,
    pendingAttentionPreview: Array.isArray(body?.task?.pendingAttentionPreview) ? body.task.pendingAttentionPreview : Array.isArray(body?.attention) ? body.attention : [],
    reviewSummary: body?.reviewSummary ?? {
      pendingCount: pendingAttentionCount,
      resolvedCount: 0,
      waivedCount: 0,
      supersededCount: 0,
    },
    importRunId: body?.importRunId ?? null,
    metricsRunId: body?.metricsRun?.runId ?? null,
    metricsBatchName: body?.metricsRun?.batchName ?? null,
    taskLifecycleStatus: browserCaptureLifecycleStatus(pendingAttentionCount),
    taskLifecycleLabel: browserCaptureLifecycleLabel(pendingAttentionCount),
  };
}

function upsertBrowserCaptureRunSummary(runSummary) {
  if (!runSummary?.runId) {
    return;
  }
  const previousRuns = effectiveOperationsOverview().browserCaptureRuns ?? [];
  const nextRuns = [runSummary, ...previousRuns.filter((item) => item.runId !== runSummary.runId)].sort(compareCreatedAtDesc);
  const summary = effectiveOperationsOverview().summary ?? emptyOperationsOverview.summary;
  const existing = previousRuns.some((item) => item.runId === runSummary.runId);
  operationsOverview = {
    ...effectiveOperationsOverview(),
    browserCaptureRuns: nextRuns,
    summary: {
      ...summary,
      browserCaptureRunCount: existing ? Number(summary.browserCaptureRunCount ?? nextRuns.length) : Number(summary.browserCaptureRunCount ?? 0) + 1,
      latestBrowserCaptureAt: nextRuns[0]?.createdAt ?? summary.latestBrowserCaptureAt ?? null,
      browserCaptureAttentionCount: nextRuns.reduce((count, item) => count + Number(item?.attentionCount ?? 0), 0),
    }
  };
}

function buildOptimisticBrowserSamplingTask(task, runSummary, taskProgress = null) {
  if (!task?.taskId) {
    return null;
  }
  const attentionCount = Number(runSummary?.attentionCount ?? 0);
  const pendingAttentionCount = browserCapturePendingAttentionCount(runSummary);
  const previousHistoryCount = Number(task.captureHistoryCount ?? 0);
  const nextTask = applyBrowserSamplingTaskProgress(task, taskProgress) ?? { ...task };
  return {
    ...nextTask,
    captureHistoryCount: previousHistoryCount + (runSummary?.runId ? 1 : 0),
    latestCaptureAt: runSummary?.createdAt ?? task.latestCaptureAt ?? null,
    latestCaptureRunId: runSummary?.runId ?? task.latestCaptureRunId ?? null,
    latestCaptureImportRunId: runSummary?.importRunId ?? task.latestCaptureImportRunId ?? null,
    latestCaptureMetricsRunId: runSummary?.metricsRunId ?? task.latestCaptureMetricsRunId ?? null,
    latestCaptureAttentionCount: attentionCount,
    latestCaptureAttentionPreview: runSummary?.attentionPreview ?? [],
    pendingReviewRunId: pendingAttentionCount > 0 ? runSummary?.runId ?? task.pendingReviewRunId ?? null : null,
    pendingReviewQueueId: pendingAttentionCount > 0 ? runSummary?.pendingReviewQueueId ?? task.pendingReviewQueueId ?? null : null,
    pendingAttentionCount,
    pendingAttentionPreview: runSummary?.pendingAttentionPreview ?? [],
    taskLifecycleStatus: browserCaptureLifecycleStatus(pendingAttentionCount),
    taskLifecycleLabel: browserCaptureLifecycleLabel(pendingAttentionCount),
  };
}

function upsertBrowserSamplingTask(taskSnapshot, { pinSelection = true } = {}) {
  if (!taskSnapshot?.taskId) {
    return;
  }
  const currentItems = state.browserSamplingPackItems ?? [];
  const existingIndex = currentItems.findIndex((item) => item.taskId === taskSnapshot.taskId);
  if (existingIndex >= 0) {
    state.browserSamplingPackItems = currentItems.map((item, index) => (index === existingIndex ? { ...item, ...taskSnapshot } : item));
  } else {
    state.browserSamplingPackItems = [{ ...taskSnapshot }, ...currentItems];
  }
  if (pinSelection) {
    state.selectedBrowserSamplingTaskId = taskSnapshot.taskId;
  }
}

function updateLastBrowserCaptureSubmission(patch) {
  if (!state.lastBrowserCaptureSubmission) {
    return;
  }
  state.lastBrowserCaptureSubmission = {
    ...state.lastBrowserCaptureSubmission,
    ...patch
  };
}

function setLastBrowserCaptureReviewAction(action) {
  state.lastBrowserCaptureReviewAction = action;
}

function browserCaptureReviewSuccessMessage({ reviewMode = "single", reviewStatus = "resolved", affectedCount = 1, skippedCount = 0, outcome = "same_run" } = {}) {
  const baseMessage =
    reviewMode === "batch"
      ? affectedCount > 0
        ? `${reviewStatus === "waived" ? "已批量豁免" : "已批量标记已修正"} ${affectedCount} 条 attention。${skippedCount > 0 ? ` 跳过 ${skippedCount} 条无效或已处理项。` : ""}`
        : `本次没有可更新的 pending 条目。${skippedCount > 0 ? ` 已跳过 ${skippedCount} 条无效或已处理项。` : ""}`
      : reviewStatus === "waived"
        ? "该条 attention 已标记豁免。"
        : "该条 attention 已标记已修正。";
  if (outcome === "current_task") {
    return `${baseMessage} 当前批次已清空，继续处理当前任务的其他待复核 attention。`;
  }
  if (outcome === "next_review") {
    return `${baseMessage} 当前批次已清空，已接力到下一条待复核任务。`;
  }
  if (outcome === "cleared") {
    return `${baseMessage} 当前没有更多待复核 attention。`;
  }
  return baseMessage;
}

function browserCaptureReviewPrimaryQueueId(payload, fallbackQueueId = null) {
  return (
    payload?.queueItem?.queueId ??
    payload?.updatedQueueItems?.[0]?.queueId ??
    payload?.detail?.reviewQueue?.find((item) => String(item?.status ?? "pending") === "pending")?.queueId ??
    fallbackQueueId ??
    null
  );
}

async function finalizeBrowserCaptureReviewAction(
  runId,
  payload,
  {
    sourceTask = currentBrowserSamplingTask(),
    reviewStatus = "resolved",
    reviewMode = "single",
    selectedCount = 1,
    affectedCount = reviewMode === "batch" ? 0 : 1,
    skippedCount = 0,
    queueId = null,
  } = {}
) {
  await refreshData({
    backgroundHydration: true,
    preserveBrowserSamplingTaskId: sourceTask?.taskId ?? null,
  });
  void refreshOperationsWorkbench({ reloadFloor: true }).catch(() => {});

  const workflowAction = payload?.workflow?.action ?? "stay_current";
  const workflowReason = payload?.workflow?.reason ?? "review_queue_cleared";
  const reviewInboxPendingCount = Number(payload?.reviewInboxSummary?.pendingQueueCount ?? state.browserReviewInboxSummary?.pendingQueueCount ?? 0);
  const refreshedSourceTask =
    (state.browserSamplingPackItems ?? []).find((item) => item.taskId === sourceTask?.taskId) ??
    payload?.task ??
    sourceTask;
  const primaryQueueId = browserCaptureReviewPrimaryQueueId(payload, queueId);
  const refreshedCurrentRun = await loadSelectedBrowserCaptureRunDetail(runId, {
    preferredQueueId: payload?.detail?.reviewQueue?.find((item) => String(item?.status ?? "pending") === "pending")?.queueId ?? null,
  });
  const sameRunPendingItems = (refreshedCurrentRun?.reviewQueue ?? []).filter((item) => String(item?.status ?? "pending") === "pending");
  const resolvedReviewTarget = resolveBrowserCaptureReviewWorkflowTarget({
    workflow: payload?.workflow ?? {},
    workflowAction,
    runId,
    sourceTask,
    refreshedSourceTask,
    refreshedCurrentRun,
  });

  if (workflowAction === "review_current_run" && (resolvedReviewTarget.item?.queueId || sameRunPendingItems.length)) {
    const nextQueueId =
      resolvedReviewTarget.workflowQueueId ??
      resolvedReviewTarget.item?.queueId ??
      sameRunPendingItems[0].queueId ??
      null;
    state.selectedBrowserCaptureReviewQueueId = nextQueueId;
    const currentRunTask = resolvedReviewTarget.task ?? refreshedSourceTask ?? sourceTask;
    if (currentRunTask?.taskId) {
      upsertBrowserSamplingTask(currentRunTask, { pinSelection: true });
      state.selectedBrowserSamplingTaskId = currentRunTask.taskId;
    }
    await loadSelectedBrowserCaptureRunDetail(runId, {
      preferredQueueId: nextQueueId,
    });
    setLastBrowserCaptureReviewAction({
      status: "success",
      runId,
      queueId: primaryQueueId,
      action: workflowAction,
      reason: workflowReason,
      workflowRunId: resolvedReviewTarget.workflowRunId,
      workflowQueueId: resolvedReviewTarget.workflowQueueId,
      workflowTaskId: resolvedReviewTarget.workflowTaskId,
      workflowItemProvided: resolvedReviewTarget.workflowItemProvided,
      reviewResolution: resolvedReviewTarget.resolution,
      postReviewTaskId: resolvedReviewTarget.task?.taskId ?? refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
      postReviewTaskLabel: browserSamplingTaskLabel(resolvedReviewTarget.task ?? refreshedSourceTask ?? sourceTask),
      postReviewRunId: resolvedReviewTarget.item?.runId ?? resolvedReviewTarget.workflowRunId ?? null,
      postReviewQueueId: resolvedReviewTarget.item?.queueId ?? resolvedReviewTarget.workflowQueueId ?? null,
      pendingCount: sameRunPendingItems.length,
      taskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
      taskLabel: browserSamplingTaskLabel(refreshedSourceTask ?? sourceTask),
      reviewStatus,
      reviewMode,
      selectedCount,
      affectedCount,
      skippedCount,
      reviewInboxPendingCount,
    });
    state.opsMessage = browserCaptureReviewSuccessMessage({
      reviewMode,
      reviewStatus,
      affectedCount,
      skippedCount,
      outcome: "same_run",
    });
    state.opsMessageTone = "success";
    render();
    return;
  }

  if (
    workflowAction === "review_current_task" &&
    (resolvedReviewTarget.item?.taskId || (resolvedReviewTarget.task?.taskId && (resolvedReviewTarget.workflowRunId || refreshedSourceTask?.pendingReviewRunId)))
  ) {
    const reviewTargetTask = resolvedReviewTarget.task ?? refreshedSourceTask ?? sourceTask ?? null;
    const reviewTargetTaskId = reviewTargetTask?.taskId ?? null;
    const reviewTargetRunId =
      resolvedReviewTarget.item?.runId ??
      resolvedReviewTarget.workflowRunId ??
      refreshedSourceTask?.pendingReviewRunId ??
      null;
    const reviewTargetQueueId =
      resolvedReviewTarget.item?.queueId ??
      resolvedReviewTarget.workflowQueueId ??
      refreshedSourceTask?.pendingReviewQueueId ??
      null;
    const currentTaskId = currentBrowserSamplingTask()?.taskId ?? null;
    const canReuseCurrentTaskPanel =
      Boolean(reviewTargetTaskId) &&
      [currentTaskId, refreshedSourceTask?.taskId ?? null, sourceTask?.taskId ?? null].includes(reviewTargetTaskId);

    if (canReuseCurrentTaskPanel) {
      if (reviewTargetTask?.taskId) {
        upsertBrowserSamplingTask(reviewTargetTask, { pinSelection: true });
        state.selectedBrowserSamplingTaskId = reviewTargetTask.taskId;
      }
      if (reviewTargetRunId) {
        await loadSelectedBrowserCaptureRunDetail(reviewTargetRunId, {
          preferredQueueId: reviewTargetQueueId,
        });
      }
    } else if (resolvedReviewTarget.item?.taskId) {
      await navigateToBrowserReviewInboxItem(resolvedReviewTarget.item, { resetDraft: false });
    } else {
      await navigateToBrowserSamplingTask(resolvedReviewTarget.task ?? refreshedSourceTask, {
        resetDraft: false,
        revealLatestCaptureRun: true,
        preferredReviewRunId: resolvedReviewTarget.workflowRunId ?? refreshedSourceTask?.pendingReviewRunId ?? null,
        preferredReviewQueueId: resolvedReviewTarget.workflowQueueId ?? refreshedSourceTask?.pendingReviewQueueId ?? null,
      });
    }
    setLastBrowserCaptureReviewAction({
      status: "success",
      runId,
      queueId: primaryQueueId,
      action: workflowAction,
      reason: workflowReason,
      workflowRunId: resolvedReviewTarget.workflowRunId,
      workflowQueueId: resolvedReviewTarget.workflowQueueId,
      workflowTaskId: resolvedReviewTarget.workflowTaskId,
      workflowItemProvided: resolvedReviewTarget.workflowItemProvided,
      reviewResolution: resolvedReviewTarget.resolution,
      postReviewTaskId: resolvedReviewTarget.task?.taskId ?? refreshedSourceTask?.taskId ?? null,
      postReviewTaskLabel: browserSamplingTaskLabel(resolvedReviewTarget.task ?? refreshedSourceTask),
      postReviewRunId: resolvedReviewTarget.item?.runId ?? resolvedReviewTarget.workflowRunId ?? null,
      postReviewQueueId: resolvedReviewTarget.item?.queueId ?? resolvedReviewTarget.workflowQueueId ?? null,
      pendingCount: browserCapturePendingAttentionCount(resolvedReviewTarget.task ?? refreshedSourceTask),
      taskId: refreshedSourceTask?.taskId ?? null,
      taskLabel: browserSamplingTaskLabel(refreshedSourceTask),
      reviewStatus,
      reviewMode,
      selectedCount,
      affectedCount,
      skippedCount,
      reviewInboxPendingCount,
    });
    state.opsMessage = browserCaptureReviewSuccessMessage({
      reviewMode,
      reviewStatus,
      affectedCount,
      skippedCount,
      outcome: "current_task",
    });
    state.opsMessageTone = "success";
    render();
    return;
  }

  if (workflowAction === "advance_next_review" && (resolvedReviewTarget.item?.taskId || resolvedReviewTarget.task?.taskId)) {
    if (resolvedReviewTarget.item?.taskId) {
      await navigateToBrowserReviewInboxItem(resolvedReviewTarget.item, { resetDraft: false });
    } else {
      await navigateToBrowserSamplingTask(resolvedReviewTarget.task, {
        resetDraft: false,
        revealLatestCaptureRun: true,
        preferredReviewRunId: resolvedReviewTarget.workflowRunId ?? null,
        preferredReviewQueueId: resolvedReviewTarget.workflowQueueId ?? null,
      });
    }
    setLastBrowserCaptureReviewAction({
      status: "success",
      runId,
      queueId: primaryQueueId,
      action: workflowAction,
      reason: workflowReason,
      workflowRunId: resolvedReviewTarget.workflowRunId,
      workflowQueueId: resolvedReviewTarget.workflowQueueId,
      workflowTaskId: resolvedReviewTarget.workflowTaskId,
      workflowItemProvided: resolvedReviewTarget.workflowItemProvided,
      reviewResolution: resolvedReviewTarget.resolution,
      postReviewTaskId: resolvedReviewTarget.task?.taskId ?? refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
      postReviewTaskLabel: browserSamplingTaskLabel(resolvedReviewTarget.task ?? refreshedSourceTask ?? sourceTask),
      postReviewRunId: resolvedReviewTarget.item?.runId ?? resolvedReviewTarget.workflowRunId ?? null,
      postReviewQueueId: resolvedReviewTarget.item?.queueId ?? resolvedReviewTarget.workflowQueueId ?? null,
      pendingCount: reviewInboxPendingCount,
      taskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
      taskLabel: browserSamplingTaskLabel(refreshedSourceTask ?? sourceTask),
      reviewStatus,
      reviewMode,
      selectedCount,
      affectedCount,
      skippedCount,
      reviewInboxPendingCount,
    });
    state.opsMessage = browserCaptureReviewSuccessMessage({
      reviewMode,
      reviewStatus,
      affectedCount,
      skippedCount,
      outcome: "next_review",
    });
    state.opsMessageTone = "success";
    render();
    return;
  }

  if (refreshedSourceTask?.taskId) {
    upsertBrowserSamplingTask(refreshedSourceTask, { pinSelection: true });
    state.selectedBrowserSamplingTaskId = refreshedSourceTask.taskId;
    await navigateToBrowserSamplingTask(refreshedSourceTask, {
      resetDraft: false,
      revealLatestCaptureRun: false,
    });
  }
  setLastBrowserCaptureReviewAction({
    status: "success",
    runId,
    queueId: primaryQueueId,
    action: workflowAction === "advance_next_review" ? "stay_current" : workflowAction,
    reason: workflowAction === "advance_next_review" ? "review_queue_cleared" : workflowReason,
    workflowRunId: resolvedReviewTarget.workflowRunId,
    workflowQueueId: resolvedReviewTarget.workflowQueueId,
    workflowTaskId: resolvedReviewTarget.workflowTaskId,
    workflowItemProvided: resolvedReviewTarget.workflowItemProvided,
    reviewResolution: resolvedReviewTarget.resolution,
    postReviewTaskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    postReviewTaskLabel: browserSamplingTaskLabel(refreshedSourceTask ?? sourceTask),
    postReviewRunId: null,
    postReviewQueueId: null,
    pendingCount: 0,
    taskId: refreshedSourceTask?.taskId ?? sourceTask?.taskId ?? null,
    taskLabel: browserSamplingTaskLabel(refreshedSourceTask ?? sourceTask),
    reviewStatus,
    reviewMode,
    selectedCount,
    affectedCount,
    skippedCount,
    reviewInboxPendingCount,
  });
  state.opsMessage = browserCaptureReviewSuccessMessage({
    reviewMode,
    reviewStatus,
    affectedCount,
    skippedCount,
    outcome: "cleared",
  });
  state.opsMessageTone = "success";
}

async function finalizeBrowserSamplingCaptureRefresh(task, body, optimisticTask) {
  const refreshResults = await Promise.allSettled([
    refreshData({
      backgroundHydration: true,
      preserveBrowserSamplingTaskId: task?.taskId ?? optimisticTask?.taskId ?? null,
    }),
  ]);
  void refreshOperationsWorkbench({ reloadFloor: true }).catch(() => {});
  if (optimisticTask?.taskId && !(state.browserSamplingPackItems ?? []).some((item) => item.taskId === optimisticTask.taskId)) {
    upsertBrowserSamplingTask(optimisticTask, { pinSelection: true });
  }
  const rejected = refreshResults.find((item) => item.status === "rejected");
  if (rejected) {
    throw rejected.reason instanceof Error ? rejected.reason : new Error("公开页面采样刷新失败。");
  }

  const workflowAction = body?.workflow?.action ?? "stay_current";
  const workflowReason = body?.workflow?.reason ?? "no_pending_task";
  const refreshedSourceTask =
    browserSamplingTaskById(task?.taskId) ??
    optimisticTask ??
    task;
  const resolvedPostSubmitTask = resolvePostSubmitBrowserSamplingTask({
    workflow: body?.workflow ?? {},
    workflowAction,
    sourceTask: task,
    refreshedSourceTask,
  });

  if (workflowAction === "review_current_capture") {
    const reviewTask = resolvedPostSubmitTask.task ?? refreshedSourceTask ?? task;
    if (reviewTask?.taskId) {
      await navigateToBrowserSamplingTask(reviewTask, {
        resetDraft: false,
        revealLatestCaptureRun: true
      });
    }
    const reviewItems = currentPendingBrowserCaptureReviewItems();
    const filledChannels = fillBrowserCaptureDraftFromAttentionByChannel(reviewItems);
    updateLastBrowserCaptureSubmission({
      workflowAction,
      workflowReason,
      workflowTaskId: resolvedPostSubmitTask.workflowTaskId,
      workflowTaskProvided: resolvedPostSubmitTask.workflowTaskProvided,
      postSubmitTaskResolution: resolvedPostSubmitTask.resolution,
      postSubmitTaskId: reviewTask?.taskId ?? task?.taskId ?? null,
      postSubmitTaskLabel: browserSamplingTaskLabel(reviewTask ?? task),
      reviewPendingCount: browserCapturePendingAttentionCount(currentBrowserCaptureRun()),
      reviewInboxPendingCount: Number(state.browserReviewInboxSummary?.pendingQueueCount ?? 0),
      autoFilledChannels: filledChannels,
    });
    render();
    return;
  }

  if (workflowAction === "advance_next_capture") {
    const nextTask = resolvedPostSubmitTask.task;
    if (nextTask?.taskId) {
      const shouldSwitchTask = currentBrowserSamplingTask()?.taskId !== nextTask.taskId;
      if (shouldSwitchTask) {
        selectBrowserSamplingTask(nextTask.taskId, {
          resetDraft: true,
        });
      }
      updateLastBrowserCaptureSubmission({
        workflowAction,
        workflowReason,
        workflowTaskId: resolvedPostSubmitTask.workflowTaskId,
        workflowTaskProvided: resolvedPostSubmitTask.workflowTaskProvided,
        postSubmitTaskResolution: resolvedPostSubmitTask.resolution,
        postSubmitTaskId: nextTask.taskId,
        postSubmitTaskLabel: browserSamplingTaskLabel(nextTask),
        reviewPendingCount: Number(body?.reviewSummary?.pendingCount ?? browserCapturePendingAttentionCount(optimisticTask)),
        reviewInboxPendingCount: Number(state.browserReviewInboxSummary?.pendingQueueCount ?? 0),
        autoFilledChannels: [],
      });
      if (shouldSwitchTask) {
        render();
        await navigateToBrowserSamplingTask(nextTask, {
          resetDraft: false,
          revealLatestCaptureRun: false
        });
      }
      render();
      return;
    }
  }

  if (refreshedSourceTask?.taskId) {
    await navigateToBrowserSamplingTask(refreshedSourceTask, {
      resetDraft: false,
      revealLatestCaptureRun: false
    });
  }
  updateLastBrowserCaptureSubmission({
    workflowAction: "stay_current",
    workflowReason: workflowAction === "advance_next_capture" ? "no_pending_task" : workflowReason,
    workflowTaskId: resolvedPostSubmitTask.workflowTaskId,
    workflowTaskProvided: resolvedPostSubmitTask.workflowTaskProvided,
    postSubmitTaskResolution: resolvedPostSubmitTask.resolution,
    postSubmitTaskId: refreshedSourceTask?.taskId ?? task?.taskId ?? null,
    postSubmitTaskLabel: browserSamplingTaskLabel(refreshedSourceTask ?? task),
    reviewPendingCount: browserCapturePendingAttentionCount(currentBrowserCaptureRun() ?? refreshedSourceTask ?? {}),
    reviewInboxPendingCount: Number(state.browserReviewInboxSummary?.pendingQueueCount ?? 0),
    autoFilledChannels: [],
  });
  render();
}

async function loadSelectedBrowserCaptureRunDetail(runId, { preferredQueueId = null } = {}) {
  if (!runId) {
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
    state.selectedBrowserCaptureReviewQueueId = null;
    clearBrowserCaptureReviewBatchSelection();
    return null;
  }
  state.selectedBrowserCaptureRunId = runId;
  state.busyBrowserCaptureRunId = runId;
  render();
  try {
    const response = await fetch(`/api/browser-capture-runs/${encodeURIComponent(runId)}`, {
      headers: {
        Accept: "application/json"
      }
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `公开页采样批次读取失败 (${response.status})`);
    }
    state.selectedBrowserCaptureRunDetail = body;
    const reviewQueue = Array.isArray(body?.reviewQueue) ? body.reviewQueue : [];
    const nextQueueId =
      (preferredQueueId && reviewQueue.some((item) => item?.queueId === preferredQueueId) ? preferredQueueId : null) ??
      reviewQueue.find((item) => String(item?.status ?? "pending") === "pending")?.queueId ??
      reviewQueue[0]?.queueId ??
      null;
    const selectedQueueStillExists = reviewQueue.some((item) => item?.queueId === state.selectedBrowserCaptureReviewQueueId);
    state.selectedBrowserCaptureReviewQueueId =
      preferredQueueId && reviewQueue.some((item) => item?.queueId === preferredQueueId)
        ? preferredQueueId
        : selectedQueueStillExists
          ? state.selectedBrowserCaptureReviewQueueId
          : nextQueueId;
    syncBrowserCaptureReviewBatchSelection(reviewQueue);
    return body;
  } catch (error) {
    state.selectedBrowserCaptureRunDetail = null;
    state.selectedBrowserCaptureReviewQueueId = null;
    clearBrowserCaptureReviewBatchSelection();
    state.opsMessage = error.message || "公开页采样批次读取失败。";
    state.opsMessageTone = "error";
    state.opsMessageContext = "sampling";
    return null;
  } finally {
    state.busyBrowserCaptureRunId = null;
    render();
  }
}

function browserCaptureEmptyEntry() {
  return {
    sourceListingId: "",
    url: "",
    publishedAt: "",
    rawText: "",
    note: ""
  };
}

function resetBrowserCaptureDraft() {
  state.browserCaptureDraft = {
    sale: browserCaptureEmptyEntry(),
    rent: browserCaptureEmptyEntry()
  };
}

function ensureBrowserSamplingTaskSelection() {
  const tasks = state.browserSamplingPackItems ?? [];
  if (!tasks.length) {
    state.selectedBrowserSamplingTaskId = null;
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
    state.selectedBrowserCaptureReviewQueueId = null;
    clearBrowserCaptureReviewBatchSelection();
    resetBrowserCaptureDraft();
    return;
  }
  const selectedTask = tasks.find((task) => task.taskId === state.selectedBrowserSamplingTaskId);
  if (!selectedTask) {
    state.selectedBrowserSamplingTaskId = tasks[0].taskId;
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
    state.selectedBrowserCaptureReviewQueueId = null;
    clearBrowserCaptureReviewBatchSelection();
    resetBrowserCaptureDraft();
  }
}

function selectBrowserSamplingTask(taskId, { resetDraft = true } = {}) {
  if (!taskId || state.selectedBrowserSamplingTaskId === taskId) {
    return;
  }
  state.selectedBrowserSamplingTaskId = taskId;
  state.selectedBrowserCaptureRunId = null;
  state.selectedBrowserCaptureRunDetail = null;
  state.selectedBrowserCaptureReviewQueueId = null;
  clearBrowserCaptureReviewBatchSelection();
  if (resetDraft) {
    resetBrowserCaptureDraft();
  }
}

function dedupeGeoTasks(tasks, keyResolver) {
  const taskMap = new Map();
  tasks.forEach((task) => {
    const key = keyResolver(task);
    if (!key) {
      return;
    }
    const current = taskMap.get(key);
    if (!current || compareGeoTaskPriority(task, current) < 0) {
      taskMap.set(key, task);
    }
  });
  return Array.from(taskMap.values()).sort(compareGeoTaskPriority);
}

function getGeoTaskMapItems() {
  const tasks = getGeoTaskWatchlistItems(18);
  if (state.granularity === "community") {
    return dedupeGeoTasks(tasks, (task) => task.communityId);
  }
  return dedupeGeoTasks(tasks, (task) => task.buildingId ?? task.communityId);
}

function geoTaskTarget(task) {
  const focusFloor = task?.watchlistFloors?.[0]?.floorNo ?? null;
  return {
    floorNo: focusFloor,
    granularity: focusFloor ? "floor" : "building"
  };
}

async function navigateToEvidenceTarget(communityId, buildingId, floorNo, { preserveGeoTask = false, waypoint = null } = {}) {
  if (!communityId) {
    return;
  }
  const districtId =
    districts.flatMap((district) => district.communities ?? []).find((community) => community.id === communityId)?.districtId ??
    state.selectedDistrictId;
  await selectCommunity(communityId, districtId, { preserveGeoTask });
  if (buildingId) {
    await selectBuilding(buildingId, { preserveGeoTask });
  }
  if (floorNo) {
    await selectFloor(Number(floorNo), { preserveGeoTask });
  }
  if (waypoint?.label) {
    announceMapWaypoint(waypoint);
  }
}

async function navigateToGeoTask(task, { waypoint = null } = {}) {
  if (!task) {
    return;
  }
  state.selectedGeoTaskId = task.taskId ?? null;
  const target = geoTaskTarget(task);
  setGranularity(target.granularity);
  await navigateToEvidenceTarget(task.communityId, task.buildingId, target.floorNo, {
    preserveGeoTask: true,
    waypoint:
      waypoint ??
      (task.communityName
        ? {
            source: "geo_task",
            label: `${task.communityName}${task.buildingName ? ` · ${task.buildingName}` : ""}`,
            detail: target.floorNo != null ? `${target.floorNo}层证据与几何补采任务` : "楼栋证据与几何补采任务"
          }
        : null)
  });
}

async function submitAnchorConfirmation(communityId, payload, { closeEditor = false } = {}) {
  if (!communityId) {
    return;
  }

  state.busyAnchorCommunityId = communityId;
  state.opsMessage = null;
  state.opsMessageContext = "anchor";
  render();

  try {
    const response = await fetch(`/api/communities/${encodeURIComponent(communityId)}/anchor-confirmation`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        ...payload,
        review_owner: "atlas-ui"
      })
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `Anchor confirmation failed with ${response.status}`);
    }
    if (closeEditor) {
      closeAnchorManualEditor();
    }
    state.opsMessage =
      body.databaseSync?.message ||
      (payload.action === "manual_override" ? "小区锚点已手工覆盖。" : "小区锚点已确认写回。");
    state.opsMessageTone = body.databaseSync?.status === "error" ? "error" : "success";
    await Promise.all([refreshData(), refreshOperationsWorkbench({ reloadFloor: false })]);
    render();
  } catch (error) {
    state.opsMessage = error.message || "锚点确认失败。";
    state.opsMessageTone = "error";
    render();
  } finally {
    state.busyAnchorCommunityId = null;
    render();
  }
}

async function confirmCurrentAnchorCandidate(community, referenceRunId = null) {
  if (!community) {
    return;
  }
  await submitAnchorConfirmation(
    community.id,
    {
      action: "confirm_candidate",
      candidate_index: 0,
      reference_run_id: referenceRunId ?? null,
      review_note: "已在 Atlas 工作台确认当前候选锚点。"
    }
  );
}

async function saveManualAnchorOverride(community, referenceRunId = null) {
  if (!community) {
    return;
  }
  await submitAnchorConfirmation(
    community.id,
    {
      action: "manual_override",
      reference_run_id: referenceRunId ?? null,
      center_lng: state.anchorDraft.lng === "" ? null : Number(state.anchorDraft.lng),
      center_lat: state.anchorDraft.lat === "" ? null : Number(state.anchorDraft.lat),
      anchor_source_label: state.anchorDraft.sourceLabel || "manual_override_gcj02",
      review_note: state.anchorDraft.note || undefined,
      alias_hint: state.anchorDraft.aliasHint || undefined
    },
    { closeEditor: true }
  );
}

async function persistImportRun(runId, { applySchema = false } = {}) {
  if (!runId) {
    return;
  }

  state.busyPersistRunId = runId;
  state.opsMessage = null;
  state.opsMessageContext = "import";
  render();

  try {
    const response = await fetch(`/api/import-runs/${encodeURIComponent(runId)}/persist`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ applySchema })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Persist failed with ${response.status}`);
    }
    state.opsMessage = `批次 ${state.selectedImportRunDetail?.batchName ?? runId} 已写入 PostgreSQL。`;
    state.opsMessageTone = "success";
  } catch (error) {
    state.opsMessage = error.message || "写入 PostgreSQL 失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyPersistRunId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    render();
  }
}

async function persistReferenceRun(runId, { applySchema = false } = {}) {
  if (!runId) {
    return;
  }

  state.busyReferencePersistRunId = runId;
  state.opsMessage = null;
  state.opsMessageContext = "database";
  render();

  try {
    const response = await fetch(`/api/reference-runs/${encodeURIComponent(runId)}/persist`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ applySchema })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Reference persist failed with ${response.status}`);
    }
    state.opsMessage = `主档批次 ${runId} 已写入 PostgreSQL。`;
    state.opsMessageTone = "success";
  } catch (error) {
    state.opsMessage = error.message || "主档批次写入 PostgreSQL 失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyReferencePersistRunId = null;
    await Promise.all([loadRuntimeConfig(), refreshOperationsWorkbench({ reloadFloor: true }), refreshData()]);
    render();
  }
}

async function bootstrapLocalDatabaseRequest({
  referenceRunId = null,
  importRunId = null,
  geoRunId = null,
  applySchema = true,
  refreshMetrics = true
} = {}) {
  state.busyBootstrapDatabase = true;
  state.opsMessage = null;
  state.opsMessageContext = "database";
  render();

  try {
    const response = await fetch("/api/database/bootstrap-local", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        reference_run_id: referenceRunId,
        import_run_id: importRunId,
        geo_run_id: geoRunId,
        applySchema,
        refreshMetrics
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Database bootstrap failed with ${response.status}`);
    }
    const stepSummary = (payload.steps ?? [])
      .map((item) => `${item.step}:${item.status}`)
      .join(" / ");
    state.opsMessage = `本地数据库引导完成。${stepSummary ? ` ${stepSummary}` : ""}`;
    state.opsMessageTone = "success";
  } catch (error) {
    state.opsMessage = error.message || "本地数据库引导失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyBootstrapDatabase = false;
    await Promise.all([loadRuntimeConfig(), refreshOperationsWorkbench({ reloadFloor: true }), refreshData()]);
    render();
  }
}

async function refreshMetricsSnapshotRequest({
  writePostgres = false,
  applySchema = false
} = {}) {
  state.busyMetricsRefresh = true;
  state.busyMetricsRefreshMode = writePostgres ? "postgres" : "staged";
  state.opsMessage = null;
  state.opsMessageContext = "database";
  render();

  try {
    const response = await fetch("/api/jobs/refresh-metrics", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        write_postgres: writePostgres,
        apply_schema: applySchema
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Metrics refresh failed with ${response.status}`);
    }
    const metricsRun = payload.metricsRun ?? null;
    const refreshSummary = payload.summary ?? {};
    const summaryMessage =
      refreshSummary.communityMetricCount || refreshSummary.buildingFloorMetricCount
        ? `（小区 ${refreshSummary.communityMetricCount ?? 0} / 楼栋分桶 ${refreshSummary.buildingFloorMetricCount ?? 0}）`
        : "";
    const postgresMessage = payload.postgres ? "，并同步写入 PostgreSQL" : "";
    state.opsMessage = metricsRun?.batchName
      ? `已刷新指标快照 ${metricsRun.batchName}${summaryMessage}${postgresMessage}。`
      : `指标快照已刷新${summaryMessage}${postgresMessage}。`;
    state.opsMessageTone = "success";
  } catch (error) {
    state.opsMessage = error.message || "指标快照刷新失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyMetricsRefresh = false;
    state.busyMetricsRefreshMode = null;
    await Promise.all([loadRuntimeConfig(), refreshOperationsWorkbench({ reloadFloor: true }), refreshData()]);
    render();
  }
}

async function copyTextToClipboard(text, successMessage = "已复制。") {
  if (!text) {
    return;
  }
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "readonly");
      textarea.style.position = "absolute";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    }
    state.opsMessage = successMessage;
    state.opsMessageTone = "success";
    state.opsMessageContext = "sampling";
  } catch (error) {
    state.opsMessage = "复制失败，请手动复制当前检索词。";
    state.opsMessageTone = "error";
    state.opsMessageContext = "sampling";
  }
  render();
}

function updateBrowserCaptureDraft(channel, field, value) {
  if (!state.browserCaptureDraft[channel]) {
    return;
  }
  state.browserCaptureDraft = {
    ...state.browserCaptureDraft,
    [channel]: {
      ...state.browserCaptureDraft[channel],
      [field]: value
    }
  };
}

function fillBrowserCaptureDraftFromAttention(item) {
  const channel = item?.businessType === "rent" ? "rent" : "sale";
  const attentionNote = Array.isArray(item?.attention) && item.attention.length ? `attention: ${item.attention.join(" / ")}` : "";
  const parseSummary = [
    item?.buildingText ? `楼栋=${item.buildingText}` : "",
    item?.unitText ? `单元=${item.unitText}` : "",
    item?.floorText ? `楼层=${item.floorText}` : "",
    item?.totalFloors ? `总层数=${item.totalFloors}` : "",
    item?.areaSqm ? `面积=${item.areaSqm}` : "",
    item?.priceTotalWan ? `总价=${item.priceTotalWan}万` : "",
    item?.monthlyRent ? `月租=${item.monthlyRent}` : "",
  ]
    .filter(Boolean)
    .join("；");
  state.browserCaptureDraft = {
    ...state.browserCaptureDraft,
    [channel]: {
      sourceListingId: String(item?.sourceListingId ?? ""),
      url: String(item?.url ?? ""),
      publishedAt: String(item?.publishedAt ?? ""),
      rawText: String(item?.rawText ?? ""),
      note: [item?.captureNotes ?? "", attentionNote, parseSummary].filter(Boolean).join("\n"),
    },
  };
}

function fillBrowserCaptureDraftFromAttentionByChannel(items = []) {
  const filledChannels = [];
  const seenChannels = new Set();
  items.forEach((item) => {
    const channel = item?.businessType === "rent" ? "rent" : "sale";
    if (seenChannels.has(channel)) {
      return;
    }
    fillBrowserCaptureDraftFromAttention(item);
    seenChannels.add(channel);
    filledChannels.push(channel);
  });
  return filledChannels;
}

function buildBrowserCapturePayload(task) {
  const captures = ["sale", "rent"]
    .map((channel) => {
      const draft = state.browserCaptureDraft[channel];
      if (!draft?.rawText?.trim()) {
        return null;
      }
      return {
        business_type: channel,
        source_listing_id: draft.sourceListingId.trim(),
        url: draft.url.trim(),
        published_at: draft.publishedAt.trim(),
        raw_text: draft.rawText.trim(),
        capture_notes: draft.note.trim(),
        community_name: task?.communityName ?? "",
        building_text: task?.buildingName ?? "",
        address_text: [task?.communityName, task?.buildingName, task?.floorNo != null ? `${task.floorNo}层` : ""]
          .filter(Boolean)
          .join(" ")
      };
    })
    .filter(Boolean);
  return {
    task_id: task?.taskId ?? null,
    task,
    captures,
    refresh_metrics: true
  };
}

async function submitBrowserSamplingCapture(task) {
  if (!task) {
    return;
  }
  const payload = buildBrowserCapturePayload(task);
  if (!payload.captures.length) {
    state.opsMessage = "至少粘贴一条 sale 或 rent 公开页原文。";
    state.opsMessageTone = "error";
    state.opsMessageContext = "sampling";
    render();
    return;
  }

  state.busyBrowserSamplingSubmit = true;
  state.opsMessage = null;
  state.opsMessageContext = "sampling";
  render();

  try {
    const response = await fetch("/api/browser-sampling-captures", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(body.detail || `公开页面采样导入失败 (${response.status})`);
    }
    state.opsMessage = `已生成采样批次 ${body.importRunId ?? body.captureRunId}，并刷新 staged metrics。`;
    state.opsMessageTone = "success";
    if (body.importRunId) {
      state.selectedImportRunId = body.importRunId;
      state.selectedBaselineRunId = null;
      syncOperationsBackstageLocationIfNeeded();
    }
    const optimisticRun = buildOptimisticBrowserCaptureRun(task, body);
    const optimisticTask = buildOptimisticBrowserSamplingTask(task, optimisticRun, body?.taskProgress ?? null);
    state.lastBrowserCaptureSubmission = buildBrowserCaptureSubmission(task, body, optimisticRun, optimisticTask);
    state.optimisticBrowserCaptureRunSummary = optimisticRun;
    state.selectedBrowserCaptureRunId = body.captureRunId ?? null;
    state.selectedBrowserCaptureRunDetail = null;
    upsertBrowserCaptureRunSummary(optimisticRun);
    upsertBrowserSamplingTask(optimisticTask, { pinSelection: true });
    resetBrowserCaptureDraft();
    state.busyBrowserSamplingSubmit = false;
    render();
    void finalizeBrowserSamplingCaptureRefresh(task, body, optimisticTask).catch((error) => {
      state.opsMessage = error.message || "公开页面采样导入成功，但后续刷新失败。";
      state.opsMessageTone = "error";
      state.opsMessageContext = "sampling";
      render();
    });
  } catch (error) {
    state.lastBrowserCaptureSubmission = {
      status: "error",
      taskId: task.taskId,
      message: error.message || "公开页面采样导入失败。",
      createdAt: new Date().toISOString()
    };
    state.opsMessage = error.message || "公开页面采样导入失败。";
    state.opsMessageTone = "error";
    render();
  } finally {
    if (state.busyBrowserSamplingSubmit) {
      state.busyBrowserSamplingSubmit = false;
      render();
    }
  }
}

async function reviewBrowserCaptureQueueItem(runId, queueId, { status = "resolved", resolutionNotes = "" } = {}) {
  if (!runId || !queueId) {
    return;
  }

  state.busyBrowserCaptureReviewQueueId = queueId;
  state.opsMessage = null;
  state.opsMessageContext = "sampling";
  render();

  const sourceTask = currentBrowserSamplingTask();

  try {
    const response = await fetch(
      `/api/browser-capture-runs/${encodeURIComponent(runId)}/review-queue/${encodeURIComponent(queueId)}`,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          status,
          resolutionNotes: resolutionNotes || undefined,
          reviewOwner: "atlas-ui",
        }),
      }
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Browser capture review update failed with ${response.status}`);
    }
    await finalizeBrowserCaptureReviewAction(runId, payload, {
      sourceTask,
      reviewStatus: status,
      reviewMode: "single",
      selectedCount: 1,
      affectedCount: 1,
      skippedCount: 0,
      queueId,
    });
  } catch (error) {
    setLastBrowserCaptureReviewAction({
      status: "error",
      runId,
      queueId,
      message: error.message || "公开页采样复核失败。",
      createdAt: new Date().toISOString(),
    });
    state.opsMessage = error.message || "公开页采样复核失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyBrowserCaptureReviewQueueId = null;
    render();
  }
}

async function reviewBrowserCaptureQueueBatch(runId, queueIds, { status = "resolved", resolutionNotes = "" } = {}) {
  const normalizedQueueIds = Array.from(
    new Set(
      (queueIds ?? [])
        .map((queueId) => String(queueId || "").trim())
        .filter(Boolean)
    )
  );
  if (!runId || !normalizedQueueIds.length) {
    return;
  }

  state.busyBrowserCaptureReviewBatch = true;
  state.opsMessage = null;
  state.opsMessageContext = "sampling";
  render();

  const sourceTask = currentBrowserSamplingTask();

  try {
    const response = await fetch(
      `/api/browser-capture-runs/${encodeURIComponent(runId)}/review-queue/batch`,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          queueIds: normalizedQueueIds,
          status,
          resolutionNotes: resolutionNotes || undefined,
          reviewOwner: "atlas-ui",
        }),
      }
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Browser capture review batch update failed with ${response.status}`);
    }

    const affectedCount = Array.isArray(payload?.updatedQueueItems) ? payload.updatedQueueItems.length : 0;
    const skippedCount = Array.isArray(payload?.skippedQueueItems) ? payload.skippedQueueItems.length : 0;
    clearBrowserCaptureReviewBatchSelection();
    await finalizeBrowserCaptureReviewAction(runId, payload, {
      sourceTask,
      reviewStatus: status,
      reviewMode: "batch",
      selectedCount: normalizedQueueIds.length,
      affectedCount,
      skippedCount,
      queueId: normalizedQueueIds[0] ?? null,
    });
  } catch (error) {
    setLastBrowserCaptureReviewAction({
      status: "error",
      runId,
      queueId: normalizedQueueIds[0] ?? null,
      message: error.message || "公开页采样批量复核失败。",
      createdAt: new Date().toISOString(),
      reviewMode: "batch",
    });
    state.opsMessage = error.message || "公开页采样批量复核失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyBrowserCaptureReviewBatch = false;
    render();
  }
}

async function reviewQueueItem(runId, queueId, { status = "resolved", resolutionNotes = "已由工作台人工复核确认。" } = {}) {
  if (!runId || !queueId) {
    return;
  }

  state.busyReviewQueueId = queueId;
  state.opsMessage = null;
  state.opsMessageContext = "import";
  render();

  try {
    const response = await fetch(
      `/api/import-runs/${encodeURIComponent(runId)}/review-queue/${encodeURIComponent(queueId)}`,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status,
          resolutionNotes,
          reviewOwner: "atlas-ui"
        })
      }
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Review update failed with ${response.status}`);
    }
    state.opsMessage = payload.databaseSync?.message || "地址队列已回写。";
    state.opsMessageTone = payload.databaseSync?.status === "error" ? "error" : "success";
  } catch (error) {
    state.opsMessage = error.message || "复核回写失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyReviewQueueId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    render();
  }
}

async function persistGeoAssetRun(runId, { applySchema = false } = {}) {
  if (!runId) {
    return;
  }

  state.busyGeoPersistRunId = runId;
  state.opsMessage = null;
  state.opsMessageContext = "geo";
  render();

  try {
    const response = await fetch(`/api/geo-assets/runs/${encodeURIComponent(runId)}/persist`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ applySchema })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Geo persist failed with ${response.status}`);
    }
    state.opsMessage = `几何批次 ${state.selectedGeoAssetRunDetail?.batchName ?? runId} 已写入 PostgreSQL。`;
    state.opsMessageTone = "success";
  } catch (error) {
    state.opsMessage = error.message || "几何批次写入 PostgreSQL 失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyGeoPersistRunId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    render();
  }
}

async function reviewGeoAssetTask(runId, taskId, { status, resolutionNotes } = {}) {
  if (!runId || !taskId || !status) {
    return;
  }

  state.busyGeoTaskId = taskId;
  state.opsMessage = null;
  state.opsMessageContext = "geo";
  render();

  try {
    const response = await fetch(`/api/geo-assets/runs/${encodeURIComponent(runId)}/tasks/${encodeURIComponent(taskId)}`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        status,
        resolutionNotes,
        reviewOwner: "atlas-ui"
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Geo task update failed with ${response.status}`);
    }
    state.opsMessage = payload.databaseSync?.message || "几何任务已回写。";
    state.opsMessageTone = payload.databaseSync?.status === "error" ? "error" : "success";
  } catch (error) {
    state.opsMessage = error.message || "几何任务回写失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyGeoTaskId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    await loadGeoAssets();
    render();
  }
}


async function createGeoWorkOrder(runId, taskId) {
  if (!runId || !taskId) {
    return;
  }

  state.busyGeoWorkOrderTaskId = taskId;
  state.opsMessage = null;
  state.opsMessageContext = "geo";
  render();

  try {
    const response = await fetch(`/api/geo-assets/runs/${encodeURIComponent(runId)}/work-orders`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        taskIds: [taskId],
        assignee: "gis-team",
        createdBy: "atlas-ui"
      })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Geo work order create failed with ${response.status}`);
    }
    state.opsMessage = payload.databaseSync?.message || "几何补采工单已创建。";
    state.opsMessageTone = payload.databaseSync?.status === "error" ? "error" : "success";
  } catch (error) {
    state.opsMessage = error.message || "几何补采工单创建失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyGeoWorkOrderTaskId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    await loadGeoAssets();
    render();
  }
}


async function updateGeoWorkOrder(runId, workOrderId, { status } = {}) {
  if (!runId || !workOrderId || !status) {
    return;
  }

  state.busyGeoWorkOrderId = workOrderId;
  state.opsMessage = null;
  state.opsMessageContext = "geo";
  render();

  try {
    const response = await fetch(
      `/api/geo-assets/runs/${encodeURIComponent(runId)}/work-orders/${encodeURIComponent(workOrderId)}`,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status,
          changedBy: "atlas-ui",
          notes:
            status === "in_progress"
              ? "GIS 已开始补采 footprint。"
              : status === "delivered"
                ? "补采结果已交付，等待验收。"
                : "该补采工单已关闭，等待几何批次回灌。"
        })
      }
    );
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || `Geo work order update failed with ${response.status}`);
    }
    state.opsMessage = payload.databaseSync?.message || "几何补采工单已更新。";
    state.opsMessageTone = payload.databaseSync?.status === "error" ? "error" : "success";
  } catch (error) {
    state.opsMessage = error.message || "几何补采工单更新失败。";
    state.opsMessageTone = "error";
  } finally {
    state.busyGeoWorkOrderId = null;
    await refreshOperationsWorkbench({ reloadFloor: true });
    await loadGeoAssets();
    render();
  }
}

function renderSummary() {
  const communities = getFilteredCommunities();
  const fallbackSummary = {
    communityCount: communities.length,
    avgYield: communities.reduce((sum, item) => sum + item.yield, 0) / (communities.length || 1),
    avgBudget: communities.reduce((sum, item) => sum + item.avgPriceWan, 0) / (communities.length || 1),
    avgMonthlyRent: communities.reduce((sum, item) => sum + item.monthlyRent, 0) / (communities.length || 1),
    bestScore: Math.max(...communities.map((item) => item.score), 0)
  };
  const summary =
    state.summary ??
    (canUseDemoFallback()
      ? fallbackSummary
      : {
          communityCount: 0,
          avgYield: 0,
          avgBudget: 0,
          avgMonthlyRent: 0,
          bestScore: 0
        });

  const metrics = [
    { key: "community_count", label: "筛选后小区", value: summary.communityCount, suffix: "个", note: "当前筛选结果" },
    { key: "avg_yield", label: "平均年化回报", value: Number(summary.avgYield).toFixed(2), suffix: "%", note: "中位样本口径" },
    { key: "avg_budget", label: "平均挂牌总价", value: Number(summary.avgBudget).toFixed(0), suffix: "万", note: "出售样本均值" },
    { key: "avg_monthly_rent", label: "平均月租", value: Number(summary.avgMonthlyRent).toFixed(0), suffix: "元", note: "出租样本均值" },
    { key: "best_score", label: "最高机会分", value: summary.bestScore, suffix: "分", note: "筛选池 top1" },
    { key: "granularity", label: "导出粒度", value: granularityLabel(state.granularity), suffix: "", note: "当前导出对象" }
  ];

  summaryGrid.innerHTML = metrics
    .map(
      (metric) => `
        <article class="metric" data-summary-metric="${metric.key}">
          <span class="metric-label">${metric.label}</span>
          <strong>${metric.value}${metric.suffix}</strong>
          <small>${metric.note}</small>
        </article>
      `
    )
    .join("");
}

function renderDetail() {
  const community = state.selectedCommunityDetail ?? getSelectedCommunity();
  const district = getSelectedDistrict(community?.districtId ?? null);
  const building = state.selectedBuildingDetail;
  const waypoint = state.mapWaypoint;
  const anchorPreview = communityAnchorPreview(community);
  const anchorDecisionState =
    community?.anchorDecisionState ??
    (anchorPreview ? "pending" : community?.centerLng != null && community?.centerLat != null ? "confirmed" : "pending");
  const latestAnchorReview = community?.latestAnchorReview ?? null;
  const anchorEditorOpen = community ? state.anchorEditorCommunityId === community.id : false;
  const selectedFloor =
    building?.floorCurve?.find((floor) => floor.floorNo === state.selectedFloorNo) ??
    building?.floorCurve?.find((floor) => floor.floorNo === building?.focusFloorNo) ??
    building?.floorCurve?.[0] ??
    null;

  if (!community) {
    detailCard.innerHTML = `
      <p>${
        currentDataMode() === "empty"
          ? runtimeConfig.hasPostgresDsn
            ? "数据库 DSN 已配置，但还没完成首轮 bootstrap。先落 reference、import、geo，再刷新 metrics。"
            : "当前还没有数据库主读数据。请先导入授权 / 官方批次并写入 PostgreSQL，页面才会切到真实的全市楼栋研究模式。"
          : "当前筛选条件下没有可展示的小区，请适当放宽预算、回报率或样本量。"
      }</p>
    `;
    return;
  }

  detailCard.innerHTML = `
    ${
      waypoint?.label
        ? `
          <div class="detail-origin-banner tone-${waypoint.tone ?? "yield"}">
            <span class="detail-origin-banner__eyebrow">来自 ${waypoint.sourceLabel ?? "研究台"}</span>
            <strong>${waypoint.label}</strong>
            ${
              waypoint.detail
                ? `<p>当前正在联动 ${waypoint.detail}。</p>`
                : `<p>当前对象已经同步到地图与右侧研究列。</p>`
            }
          </div>
        `
        : ""
    }
    <div class="detail-hero">
      <div class="detail-hero-copy">
        <div class="detail-title">
          <div>
            <strong>${community.name}</strong>
            <p class="detail-subtitle">${district.name} · 聚焦 ${building?.name ?? community.buildingFocus ?? "小区层"} · ${granularityLabel(state.granularity)}视图</p>
          </div>
          <span class="yield-chip ${yieldClass(community.yield)}">${community.sampleStatus === "dictionary_only" ? "待补样本" : `${community.yield.toFixed(2)}%`}</span>
        </div>
        <p class="detail-insight">${community.note}</p>
      </div>
      <div class="detail-kpi-strip">
        <article class="detail-kpi">
          <span>机会评分</span>
          <strong>${community.score} 分</strong>
          <small>当前研究窗口 top signal</small>
        </article>
        <article class="detail-kpi">
          <span>有效样本</span>
          <strong>${community.sample} 套</strong>
          <small>${community.sampleStatusLabel ?? "状态待补"}</small>
        </article>
        <article class="detail-kpi">
          <span>楼栋覆盖</span>
          <strong>${community.buildingCount} 栋</strong>
          <small>${["pudong", "jingan", "minhang"].includes(community.districtId) ? "重点区追踪中" : "小区级为主"}</small>
        </article>
      </div>
    </div>

    <div class="detail-meta-strip">
      <span class="source-pill">${district.name}</span>
      <span class="source-pill">行政区均值 ${district.yield.toFixed(2)}%</span>
      <span class="source-pill">${community.sampleStatusLabel ?? "状态待补"}</span>
      <span class="source-pill">最近有效批次 ${community.dataFreshness ? formatTimestamp(community.dataFreshness) : "待补样本"}</span>
    </div>

    <div class="detail-stats detail-stats--secondary">
      <div class="detail-stat">
        <span>挂牌均价</span>
        <strong>${community.avgPriceWan} 万</strong>
      </div>
      <div class="detail-stat">
        <span>月租中位数</span>
        <strong>${community.monthlyRent.toLocaleString()} 元</strong>
      </div>
      <div class="detail-stat">
        <span>坐标来源</span>
        <strong>${community.anchorSource ?? "待补"}</strong>
      </div>
      <div class="detail-stat">
        <span>坐标质量</span>
        <strong>${community.anchorQuality != null ? `${Math.round(Number(community.anchorQuality) * 100)}%` : "待补"}</strong>
      </div>
      <div class="detail-stat">
        <span>锚点状态</span>
        <strong>${anchorDecisionLabel(anchorDecisionState)}</strong>
      </div>
      <div class="detail-stat">
        <span>最近有效批次</span>
        <strong>${community.dataFreshness ? formatTimestamp(community.dataFreshness) : "待补样本"}</strong>
      </div>
      <div class="detail-stat">
        <span>重点楼栋追踪</span>
        <strong>${["pudong", "jingan", "minhang"].includes(community.districtId) ? "已纳入" : "待排入"}</strong>
      </div>
    </div>
    ${
      anchorPreview || (community.candidateSuggestions ?? []).length || latestAnchorReview || (!community.centerLng && !community.centerLat)
        ? `
          <div class="detail-breakdown">
            <div class="detail-breakdown-head">
              <strong>锚点确认工作台</strong>
              <span class="badge">${anchorDecisionLabel(anchorDecisionState)}</span>
            </div>
            ${
              anchorPreview
                ? `
                  <div class="detail-breakdown-list">
                    <article class="breakdown-item">
                      <div class="breakdown-top">
                        <strong>${anchorPreview.anchorName ?? "候选锚点"}</strong>
                        <span>${anchorPreview.anchorSource ?? "candidate_preview"}</span>
                      </div>
                      <p>${anchorPreview.anchorAddress ?? "地图已投出预锚点，等待人工确认后写回主档。"}</p>
                    </article>
                  </div>
                `
                : ""
            }
            ${
              (community.candidateSuggestions ?? []).length
                ? `
                  <div class="detail-breakdown-list">
                    ${community.candidateSuggestions
                      .slice(0, 3)
                      .map(
                        (item, index) => `
                          <article class="breakdown-item">
                            <div class="breakdown-top">
                              <strong>${item.name ?? "候选 POI"}</strong>
                              <span>${item.score != null ? `${Math.round(Number(item.score) * 100)}%` : "待确认"}</span>
                            </div>
                            <p>${item.address ?? item.query ?? "等待人工确认该候选锚点。"}</p>
                            ${
                              index === 0
                                ? `<div class="queue-item-footer"><button class="action compact primary" data-anchor-confirm-community-id="${community.id}">${state.busyAnchorCommunityId === community.id ? "写回中..." : "确认当前候选"}</button></div>`
                                : ""
                            }
                          </article>
                        `
                      )
                      .join("")}
                  </div>
                `
                : `
                  <p class="helper-text">当前没有可靠候选，建议直接手工覆盖坐标。</p>
                `
            }
            <div class="queue-item-footer anchor-action-row">
              <button class="action compact" data-anchor-open-editor-community-id="${community.id}">
                ${anchorEditorOpen ? "收起手工覆盖" : "手工覆盖坐标"}
              </button>
            </div>
            ${
              latestAnchorReview
                ? `
                  <div class="detail-breakdown-list">
                    <article class="breakdown-item">
                      <div class="breakdown-top">
                        <strong>最近一次锚点确认</strong>
                        <span>${anchorDecisionLabel(latestAnchorReview.decisionState ?? anchorDecisionState)}</span>
                      </div>
                      <p>${latestAnchorReview.reviewOwner ?? "atlas-ui"} · ${formatTimestamp(latestAnchorReview.reviewedAt)}</p>
                      <small class="evidence-address">
                        ${latestAnchorReview.reviewNote ?? latestAnchorReview.candidateName ?? "已写回最新 reference 主档。"}
                      </small>
                    </article>
                  </div>
                `
                : ""
            }
            ${
              anchorEditorOpen
                ? `
                  <div class="anchor-manual-editor">
                    <div class="field compact">
                      <span>手工覆盖坐标（GCJ-02 / 当前高德坐标系）</span>
                      <div class="anchor-manual-grid">
                        <label class="anchor-input">
                          <span>Lng</span>
                          <input type="text" data-anchor-draft-field="lng" value="${state.anchorDraft.lng}" placeholder="121.588979" />
                        </label>
                        <label class="anchor-input">
                          <span>Lat</span>
                          <input type="text" data-anchor-draft-field="lat" value="${state.anchorDraft.lat}" placeholder="31.261385" />
                        </label>
                        <label class="anchor-input">
                          <span>来源标签</span>
                          <input type="text" data-anchor-draft-field="sourceLabel" value="${state.anchorDraft.sourceLabel}" placeholder="manual_override_gcj02" />
                        </label>
                        <label class="anchor-input">
                          <span>别名提示（可选）</span>
                          <input type="text" data-anchor-draft-field="aliasHint" value="${state.anchorDraft.aliasHint}" placeholder="碧云新天地家园" />
                        </label>
                      </div>
                    </div>
                    <div class="field compact">
                      <span>备注（可选）</span>
                      <textarea data-anchor-draft-field="note" rows="3" placeholder="例如：已在高德地图和公开页面人工核验。">${state.anchorDraft.note}</textarea>
                    </div>
                    <div class="queue-item-footer anchor-action-row">
                      <button class="action compact primary" data-anchor-save-manual-community-id="${community.id}">
                        ${state.busyAnchorCommunityId === community.id ? "写回中..." : "保存手工覆盖"}
                      </button>
                      <button class="action compact" data-anchor-close-editor-community-id="${community.id}">取消</button>
                    </div>
                  </div>
                `
                : ""
            }
          </div>
        `
        : ""
    }
    ${
      building
        ? `
      <div class="detail-building">
        <div class="detail-section-label">楼栋研究摘要</div>
        <div class="detail-title">
          <div>
            <strong>${building.name}</strong>
            <p class="detail-subtitle">主推楼栋 · 最强桶 ${building.bestBucketLabel} · 相对小区 ${building.yieldSpreadVsCommunity >= 0 ? "+" : ""}${building.yieldSpreadVsCommunity.toFixed(2)}%</p>
          </div>
          <span class="yield-chip ${yieldClass(building.yieldAvg ?? community.yield)}">${(building.yieldAvg ?? community.yield).toFixed(2)}%</span>
        </div>
        <div class="detail-meta-strip">
          <span class="source-pill">楼栋评分 ${building.score} 分</span>
          <span class="source-pill">总层数 ${building.totalFloors} 层</span>
          <span class="source-pill">样本 ${building.sampleSizeEstimate} 套</span>
        </div>
        <div class="detail-stats detail-stats--secondary">
          <div class="detail-stat">
            <span>估算总价</span>
            <strong>${building.avgPriceWanEstimate} 万</strong>
          </div>
          <div class="detail-stat">
            <span>估算月租</span>
            <strong>${Number(building.monthlyRentEstimate).toLocaleString()} 元</strong>
          </div>
          <div class="detail-stat">
            <span>楼栋样本</span>
            <strong>${building.sampleSizeEstimate} 套</strong>
          </div>
          <div class="detail-stat">
            <span>总层数</span>
            <strong>${building.totalFloors} 层</strong>
          </div>
        </div>
        <div class="detail-breakdown">
          <div class="detail-breakdown-head">
            <strong>机会评分拆解</strong>
            <span class="badge">${building.score} 分</span>
          </div>
          <div class="detail-breakdown-list">
            ${building.scoreBreakdown
              .map(
                (item) => `
                  <article class="breakdown-item">
                    <div class="breakdown-top">
                      <strong>${item.label}</strong>
                      <span>${item.contribution.toFixed(1)} 分</span>
                    </div>
                    <div class="breakdown-track">
                      <span style="width: ${item.score}%"></span>
                    </div>
                    <p>${item.summary}</p>
                  </article>
                `
              )
              .join("")}
          </div>
        </div>
        ${
          selectedFloor
            ? `
          <div class="floor-focus-card">
            <div class="detail-title">
              <div>
                <strong>${selectedFloor.floorNo} 层 · ${selectedFloor.arbitrageTag}</strong>
                <p class="detail-subtitle">
                  ${selectedFloor.bucketLabel} · 相对楼栋 ${selectedFloor.yieldSpreadVsBuilding >= 0 ? "+" : ""}${selectedFloor.yieldSpreadVsBuilding.toFixed(2)}%
                  · 溢价 ${selectedFloor.pricePremiumPct >= 0 ? "+" : ""}${selectedFloor.pricePremiumPct.toFixed(2)}%
                </p>
              </div>
              <span class="yield-chip ${yieldClass(selectedFloor.yieldPct)}">${selectedFloor.yieldPct.toFixed(2)}%</span>
            </div>
            <div class="detail-stats">
              <div class="detail-stat">
                <span>逐层机会分</span>
                <strong>${selectedFloor.opportunityScore} 分</strong>
              </div>
              <div class="detail-stat">
                <span>估算总价</span>
                <strong>${selectedFloor.estPriceWan.toFixed(1)} 万</strong>
              </div>
              <div class="detail-stat">
                <span>估算月租</span>
                <strong>${selectedFloor.estMonthlyRent.toLocaleString()} 元</strong>
              </div>
              <div class="detail-stat">
                <span>楼层桶</span>
                <strong>${selectedFloor.bucketLabel}</strong>
              </div>
            </div>
          </div>
          <div class="floor-ladder">
            <div class="detail-breakdown-head">
              <strong>逐层机会带</strong>
              <span class="detail-subtitle">点击楼层切换</span>
            </div>
            <div class="floor-ladder-grid">
              ${building.floorCurve
                .map(
                  (floor) => `
                    <button
                      type="button"
                      class="floor-chip ${floor.floorNo === selectedFloor.floorNo ? "is-active" : ""}"
                      data-floor-no="${floor.floorNo}"
                    >
                      <span>${floor.floorNo}F</span>
                      <strong>${floor.yieldPct.toFixed(2)}%</strong>
                      <small>${floor.opportunityScore}分</small>
                    </button>
                  `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }
      </div>
    `
        : ""
    }
  `;

  detailCard.querySelectorAll("[data-floor-no]").forEach((button) => {
    button.addEventListener("click", async () => {
      await selectFloor(Number(button.dataset.floorNo));
    });
  });
}

function renderFloorEvidence() {
  const floorDetail = state.selectedFloorDetail;
  if (!floorDetail) {
    floorEvidence.innerHTML = "<p>先选择楼栋和楼层，这里会展示该层的样本对、地址归一路径和复核状态。</p>";
    return;
  }

  floorEvidence.innerHTML = `
    <div class="evidence-summary">
      <div class="detail-title">
        <div>
          <strong>${floorDetail.buildingName} · ${floorDetail.floorNo} 层</strong>
          <p class="detail-subtitle">${floorDetail.bucketLabel} · ${floorDetail.arbitrageTag} · 机会分 ${floorDetail.opportunityScore}</p>
        </div>
        <span class="yield-chip ${yieldClass(floorDetail.yieldPct)}">${floorDetail.yieldPct.toFixed(2)}%</span>
      </div>
      ${
        floorDetail.measuredMetrics
          ? `
            <div class="detail-stats">
              <div class="detail-stat">
                <span>真实配对数</span>
                <strong>${floorDetail.measuredMetrics.pairCount}</strong>
              </div>
              <div class="detail-stat">
                <span>真实出售中位</span>
                <strong>${Number(floorDetail.measuredMetrics.saleMedianWan).toFixed(1)} 万</strong>
              </div>
              <div class="detail-stat">
                <span>真实出租中位</span>
                <strong>${Math.round(floorDetail.measuredMetrics.rentMedianMonthly).toLocaleString()} 元</strong>
              </div>
              <div class="detail-stat">
                <span>最佳配对置信</span>
                <strong>${Math.round(floorDetail.measuredMetrics.bestPairConfidence * 100)}%</strong>
              </div>
            </div>
          `
          : ""
      }
      <div class="source-meta">
        ${floorDetail.sourceMix.map((item) => `<span class="source-pill">${item.name} × ${item.count}</span>`).join("")}
        <span class="source-pill">${
          floorDetail.evidenceSource === "imported"
            ? "真实导入证据"
            : floorDetail.evidenceSource === "insufficient_samples"
              ? "真实楼层样本不足"
              : "模拟样本"
        }</span>
        ${
          floorDetail.importRun
            ? `<span class="source-pill">批次 ${floorDetail.importRun.batchName}</span>`
            : ""
        }
      </div>
    </div>
    ${
      (floorDetail.historyTimeline ?? []).length
        ? `
          <div class="trace-panel evidence-section">
            <div class="detail-breakdown-head">
              <strong>批次历史</strong>
              <span class="detail-subtitle">${floorDetail.historySummary?.observedRuns ?? floorDetail.historyTimeline.length} 个批次</span>
            </div>
            <div class="source-meta history-summary">
              <span class="source-pill">起点 ${floorDetail.historySummary?.firstBatchName ?? "待补"}</span>
              <span class="source-pill">当前 ${floorDetail.historySummary?.latestBatchName ?? "待补"}</span>
              <span class="source-pill">累计样本对 ${floorDetail.historySummary?.totalPairCount ?? 0}</span>
              <span class="source-pill">均值 ${floorDetail.historySummary?.avgYieldPct != null ? `${Number(floorDetail.historySummary.avgYieldPct).toFixed(2)}%` : "待补"}</span>
              <span class="source-pill">较首批 ${formatSignedDelta(floorDetail.historySummary?.yieldDeltaSinceFirst, {
                suffix: "%",
                digits: 2,
                emptyLabel: "首批即当前"
              })}</span>
            </div>
            <div class="history-timeline">
              ${(floorDetail.historyTimeline ?? [])
                .map(
                  (item) => `
                    <article class="history-card ${item.isLatest ? "is-active" : ""}">
                      <div class="breakdown-top">
                        <strong>${item.batchName}</strong>
                        <span class="trace-status ${item.isLatest ? "resolved" : comparisonToneClass(item.status)}">
                          ${item.isLatest ? "当前快照" : item.statusLabel}
                        </span>
                      </div>
                      <p>${formatTimestamp(item.createdAt)} · 样本对 ${item.pairCount}</p>
                      <div class="evidence-meta">
                        <span>回报 ${item.yieldPct != null ? `${Number(item.yieldPct).toFixed(2)}%` : "待补"}</span>
                        <span>售价 ${item.saleMedianWan != null ? `${Number(item.saleMedianWan).toFixed(1)} 万` : "待补"}</span>
                        <span>租金 ${item.rentMedianMonthly != null ? `${Math.round(item.rentMedianMonthly).toLocaleString()} 元` : "待补"}</span>
                      </div>
                      <div class="source-meta">
                        <span class="source-pill">
                          ${item.yieldDeltaVsPrevious != null ? `较上批 ${formatSignedDelta(item.yieldDeltaVsPrevious, { suffix: "%", digits: 2 })}` : "首个观测"}
                        </span>
                        <span class="source-pill">
                          ${item.pairCountDeltaVsPrevious != null ? `样本对 ${formatSignedDelta(item.pairCountDeltaVsPrevious)}` : "样本对基线"}
                        </span>
                        <span class="source-pill">
                          ${item.bestPairConfidence != null ? `最佳置信 ${Math.round(item.bestPairConfidence * 100)}%` : "置信待补"}
                        </span>
                      </div>
                    </article>
                  `
                )
                .join("")}
            </div>
          </div>
        `
        : ""
    }
    <div class="evidence-section">
      <div class="detail-breakdown-head">
        <strong>样本配对</strong>
        <span class="detail-subtitle">${floorDetail.samplePairs.length} 组</span>
      </div>
    <div class="evidence-card-grid">
      ${floorDetail.samplePairs
        .map(
          (pair) => `
            <article class="evidence-card">
              <div class="breakdown-top">
                <strong>${pair.unitNo}</strong>
                <span>${pair.reviewState}</span>
              </div>
              <div class="evidence-meta">
                <span>${pair.layout}</span>
                <span>${pair.areaSqm != null ? `${pair.areaSqm} m²` : "面积待补"}</span>
                <span>${pair.orientation}</span>
              </div>
              <div class="evidence-pricing">
                <div>
                  <span>出售</span>
                  <strong>${pair.salePriceWan != null ? `${Number(pair.salePriceWan).toFixed(1)} 万` : "待补"}</strong>
                  <small>${pair.saleSourceName}</small>
                </div>
                <div>
                  <span>出租</span>
                  <strong>${pair.monthlyRent != null ? `${Math.round(pair.monthlyRent).toLocaleString()} 元` : "待补"}</strong>
                  <small>${pair.rentSourceName}</small>
                </div>
                <div>
                  <span>测算回报</span>
                  <strong>${pair.yieldPct != null ? `${Number(pair.yieldPct).toFixed(2)}%` : "待补"}</strong>
                  <small>去重 ${Math.round(pair.dedupConfidence * 100)}%</small>
                </div>
              </div>
              <p class="evidence-address">${pair.normalizedAddress}</p>
              <div class="source-meta">
                <span class="source-pill">归一 ${Math.round(pair.resolutionConfidence * 100)}%</span>
                <span class="source-pill">去重 ${Math.round(pair.dedupConfidence * 100)}%</span>
                <span class="source-pill">${pair.updatedAt}</span>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
    </div>
    <div class="trace-panel evidence-section">
      <div class="detail-breakdown-head">
        <strong>地址标准化路径</strong>
        <span class="detail-subtitle">district → resblock → building → unit → floor</span>
      </div>
      <div class="trace-list">
        ${floorDetail.resolutionTrace
          .map(
            (item) => `
              <article class="trace-item">
                <div class="breakdown-top">
                  <strong>${item.step}</strong>
                  <span class="trace-status ${item.status}">${resolutionStatusLabel(item.status)}</span>
                </div>
                <p>${item.detail}</p>
              </article>
            `
        )
        .join("")}
      </div>
    </div>
    <div class="trace-panel evidence-section">
      <div class="detail-breakdown-head">
        <strong>相关地址队列</strong>
        <span class="detail-subtitle">${floorDetail.queueItems.length} 条</span>
      </div>
      <div class="queue-list compact">
        ${
          floorDetail.queueItems.length
            ? floorDetail.queueItems
                .map(
                  (item) => `
                    <article class="queue-item">
                      <div class="breakdown-top">
                        <strong>${item.buildingNo} · ${item.floorNo} 层</strong>
                        <span class="trace-status ${item.status}">${queueStatusLabel(item.status)}</span>
                      </div>
                      <p>${item.normalizedPath}</p>
                      <small>${sourceLabelById(item.sourceId)} · 置信度 ${Math.round(item.confidence * 100)}% · ${item.lastActionAt}</small>
                    </article>
                  `
                )
                .join("")
            : "<p>当前楼层附近没有挂起的地址标准化队列项。</p>"
        }
      </div>
    </div>
  `;
}

function renderRanking() {
  const communities = (
    state.opportunityItems?.length
      ? state.opportunityItems
      : canUseDemoFallback()
        ? getFilteredCommunities().sort((a, b) => b.score - a.score)
        : getFilteredCommunities()
  ).slice();
  rankingCount.textContent = `${communities.length}`;

  rankingList.innerHTML = communities.length
      ? communities
    .map(
      (community, index) => `
        <article
          class="ranking-item ${community.id === state.selectedCommunityId ? "is-active" : ""} ${index < 3 ? "is-top-tier" : ""}"
          data-community-id="${community.id}"
          role="button"
          tabindex="0"
          aria-pressed="${community.id === state.selectedCommunityId ? "true" : "false"}"
        >
          <div class="ranking-title">
            <strong>${index + 1}. ${community.name}</strong>
            <span class="yield-chip ${yieldClass(community.yield)}">${community.score}分</span>
          </div>
          <div class="ranking-meta">
            <span>${community.districtName}</span>
            <span>总价 ${community.avgPriceWan} 万</span>
            <span>回报 ${community.yield.toFixed(2)}%</span>
          </div>
          <div class="source-meta">
            <span class="source-pill">样本 ${community.sample} 套</span>
            <span class="source-pill">${community.sampleStatusLabel ?? "状态待补"}</span>
            <span class="source-pill">${community.dataFreshness ? formatTimestamp(community.dataFreshness) : "待补样本"}</span>
          </div>
          <small class="ranking-note">${community.note}</small>
        </article>
      `
    )
    .join("")
    : `<p class="helper-text">${
        currentDataMode() === "empty"
          ? runtimeConfig.hasPostgresDsn
            ? "数据库已连接，但还没完成首轮 bootstrap。先写入 reference / import / geo，再刷新 metrics。"
            : "当前还没有落库的小区 / 楼栋数据。请先导入授权批次并写入 PostgreSQL，或显式开启 demo mock。"
          : "当前筛选窗口下没有命中的小区机会。"
      }</p>`;

  rankingList.querySelectorAll(".ranking-item").forEach((item) => {
    const activate = async () => {
      const community = communities.find((communityItem) => communityItem.id === item.dataset.communityId) ?? getSelectedCommunity();
      if (community) {
        await selectCommunity(community.id, community.districtId);
        announceMapWaypoint({
          source: "opportunity",
          label: community.name,
          detail: "小区研究摘要与楼栋矩阵"
        });
        return;
      }
    };
    item.addEventListener("click", activate);
    bindKeyboardActivation(item, activate);
  });

  const watchlistItems = state.floorWatchlistItems?.length ? state.floorWatchlistItems : canUseDemoFallback() ? getFallbackFloorWatchlistItems() : [];
  floorWatchlistCount.textContent = state.floorWatchlistLoading ? "加载中" : `${watchlistItems.length}`;
  floorWatchlist.innerHTML = watchlistItems.length
    ? watchlistItems
    .map(
      (item, index) => `
        <article
          class="ranking-item ${item.buildingId === state.selectedBuildingId && Number(item.floorNo) === Number(state.selectedFloorNo) ? "is-active" : ""}"
          data-community-id="${item.communityId}"
          data-building-id="${item.buildingId}"
          data-floor-no="${item.floorNo}"
          role="button"
          tabindex="0"
          aria-pressed="${item.buildingId === state.selectedBuildingId && Number(item.floorNo) === Number(state.selectedFloorNo) ? "true" : "false"}"
        >
          <div class="ranking-title">
            <strong>${index + 1}. ${item.communityName} · ${item.buildingName} · ${item.floorNo} 层</strong>
            <span class="yield-chip ${yieldClass(item.latestYieldPct)}">${item.persistenceScore}分</span>
          </div>
          <div class="ranking-meta">
            <span>${item.districtName}</span>
            <span>当前 ${Number(item.latestYieldPct).toFixed(2)}%</span>
            <span>${item.trendLabel}</span>
          </div>
          <div class="source-meta">
            <span class="source-pill">批次 ${item.latestBatchName}</span>
            ${
              item.baselineBatchName
                ? `<span class="source-pill">基线 ${item.baselineBatchName}</span>`
                : ""
            }
            <span class="source-pill">${item.observedRuns} 次观测</span>
            <span class="source-pill">
              ${
                item.windowYieldDeltaPct != null
                  ? `较基线 ${formatSignedDelta(item.windowYieldDeltaPct, { suffix: "%", digits: 2 })}`
                  : item.yieldDeltaSinceFirst != null
                  ? `较首批 ${formatSignedDelta(item.yieldDeltaSinceFirst, { suffix: "%", digits: 2 })}`
                  : "首批样本"
              }
            </span>
          </div>
        </article>
      `
    )
    .join("")
    : state.floorWatchlistLoading
      ? `<p class="helper-text">持续套利楼层榜正在加载中。公开页样本与跨批次历史都已命中，列表会在后台计算完成后自动刷新。</p>`
    : `<p class="helper-text">${
        currentDataMode() === "database"
          ? "当前数据库里还没有满足阈值的逐层真实证据，所以楼层榜暂时为空。"
          : "楼层榜会在授权批次落库后出现。"
      }</p>`;

  floorWatchlist.querySelectorAll(".ranking-item").forEach((item) => {
    const activate = async () => {
      await navigateToEvidenceTarget(item.dataset.communityId, item.dataset.buildingId, item.dataset.floorNo, {
        waypoint: {
          source: "floor_watchlist",
          label: item.querySelector("strong")?.textContent?.replace(/^\d+\.\s*/, "") ?? "持续套利楼层",
          detail: "楼层证据、批次历史与样本配对"
        }
      });
    };
    item.addEventListener("click", activate);
    bindKeyboardActivation(item, activate);
  });

  const geoTasks = getGeoTaskWatchlistItems(6);
  geoTaskWatchlistCount.textContent = `${geoTasks.length}`;
  geoTaskWatchlist.innerHTML = geoTasks.length
    ? geoTasks
        .map((item, index) => {
          const active =
            item.taskId === state.selectedGeoTaskId ||
            (item.buildingId === state.selectedBuildingId && item.communityId === state.selectedCommunityId);
          const focusFloor = item.watchlistFloors?.[0]?.floorNo ?? null;
          return `
            <article
              class="ranking-item geo-task ${active ? "is-active" : ""}"
              data-geo-task-id="${item.taskId ?? ""}"
              data-community-id="${item.communityId ?? ""}"
              data-building-id="${item.buildingId ?? ""}"
              data-floor-no="${focusFloor ?? ""}"
              role="button"
              tabindex="0"
              aria-pressed="${active ? "true" : "false"}"
            >
              <div class="ranking-title">
                <strong>${index + 1}. ${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"}</strong>
                <span class="trace-status ${geoImpactBandClass(item.impactBand)}">${item.impactLabel}</span>
              </div>
              <div class="ranking-meta">
                <span>${item.districtName ?? "未知行政区"}</span>
                <span>影响 ${item.impactScore ?? 0}</span>
                <span>${item.taskScopeLabel ?? "几何任务"}</span>
              </div>
              <div class="source-meta">
                <span class="source-pill">状态 ${geoTaskStatusLabel(item.status)}</span>
                <span class="source-pill">榜单 ${item.watchlistHits ?? 0}</span>
                <span class="source-pill">小区分 ${item.communityScore ?? 0}</span>
                <span class="source-pill">楼栋分 ${item.buildingOpportunityScore ?? 0}</span>
                ${
                  item.workOrderId
                    ? `<span class="source-pill">工单 ${geoWorkOrderStatusLabel(item.workOrderStatus)} · ${item.workOrderAssignee ?? "待分配"}</span>`
                    : ""
                }
              </div>
              ${
                (item.watchlistFloors ?? []).length
                  ? `
                    <div class="source-meta">
                      ${(item.watchlistFloors ?? [])
                        .map(
                          (floor) => `
                            <span class="source-pill">
                              ${floor.floorNo}层 · ${Number(floor.latestYieldPct ?? 0).toFixed(2)}% · ${floor.trendLabel}
                            </span>
                          `
                        )
                        .join("")}
                    </div>
                  `
                  : ""
              }
              <small class="ranking-note">${item.recommendedAction ?? item.resolutionNotes ?? "等待处理。"}</small>
              ${
                canCreateGeoWorkOrder(item)
                  ? `
                    <div class="queue-item-footer">
                      <button
                        class="action compact"
                        data-geo-create-work-order-run-id="${item.runId}"
                        data-geo-create-work-order-task-id="${item.taskId}"
                      >
                        ${state.busyGeoWorkOrderTaskId === item.taskId ? "创建中..." : "生成工单"}
                      </button>
                    </div>
                  `
                  : ""
              }
            </article>
          `;
        })
        .join("")
    : "<p class=\"helper-text\">当前筛选窗口下没有高影响几何缺口，楼栋 / 楼层 footprint 可以继续往更真实的 AOI 质量提升推进。</p>";

  geoTaskWatchlist.querySelectorAll(".ranking-item[data-geo-task-id]").forEach((item) => {
    const activate = async () => {
      const task = geoTasks.find((taskItem) => taskItem.taskId === item.dataset.geoTaskId);
      if (task) {
        await navigateToGeoTask(task, {
          waypoint: {
            source: "geo_task",
            label: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}`,
            detail: task.watchlistFloors?.[0]?.floorNo != null ? `${task.watchlistFloors[0].floorNo}层证据与几何补采任务` : "楼栋证据与几何补采任务"
          }
        });
      }
    };
    item.addEventListener("click", activate);
    bindKeyboardActivation(item, activate);
  });

  geoTaskWatchlist.querySelectorAll("[data-geo-create-work-order-task-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await createGeoWorkOrder(button.dataset.geoCreateWorkOrderRunId, button.dataset.geoCreateWorkOrderTaskId);
    });
  });

  const samplingTasks = getBrowserSamplingPackItems(8);
  browserSamplingPackCount.textContent = `${samplingTasks.length}`;
  browserSamplingPack.innerHTML = samplingTasks.length
    ? samplingTasks
        .map((item, index) => {
          const active = item.taskId === state.selectedBrowserSamplingTaskId;
          return `
            <article
              class="ranking-item browser-task ${active ? "is-active" : ""}"
              data-task-id="${item.taskId ?? ""}"
              data-community-id="${item.communityId ?? ""}"
              data-building-id="${item.buildingId ?? ""}"
              data-floor-no="${item.floorNo ?? ""}"
              role="button"
              tabindex="0"
              aria-pressed="${active ? "true" : "false"}"
            >
              <div class="ranking-title">
                <strong>${index + 1}. ${item.communityName}${item.buildingName ? ` · ${item.buildingName}` : ""}${item.floorNo != null ? ` · ${item.floorNo}层` : ""}</strong>
                <span class="trace-status ${geoImpactBandClass(item.priorityScore >= 88 ? "critical" : item.priorityScore >= 76 ? "high" : item.priorityScore >= 62 ? "medium" : "low")}">${item.priorityLabel}</span>
              </div>
              <div class="ranking-meta">
                <span>${item.districtName}</span>
                <span>${item.taskTypeLabel}</span>
                <span>${item.targetGranularity === "floor" ? `样本对 ${item.currentPairCount ?? 0}/${item.targetPairCount ?? 0}` : `样本 ${item.currentSampleSize ?? 0}/${item.targetSampleSize ?? 0}`}</span>
              </div>
              <div class="source-meta">
                <span class="trace-status ${item.taskLifecycleStatus ?? "needs_capture"}">${item.taskLifecycleLabel ?? "待采样"}</span>
                <span class="source-pill">优先分 ${item.priorityScore ?? 0}</span>
                <span class="source-pill">${item.sampleStatusLabel ?? "状态待补"}</span>
                <span class="source-pill">${item.focusScope === "priority" ? "重点区任务" : "全市任务"}</span>
                ${item.currentYieldPct != null ? `<span class="source-pill">回报 ${Number(item.currentYieldPct).toFixed(2)}%</span>` : ""}
                ${item.dataFreshness ? `<span class="source-pill">样本 ${formatTimestamp(item.dataFreshness)}</span>` : ""}
              </div>
              ${
                item.captureHistoryCount
                  ? `
                    <div class="source-meta">
                      <span class="source-pill">已采 ${item.captureHistoryCount} 次</span>
                      <span class="source-pill">最近 ${formatTimestamp(item.latestCaptureAt)}</span>
                      ${
                        browserCapturePendingAttentionCount(item)
                          ? `<span class="source-pill">待复核 ${browserCapturePendingAttentionCount(item)}</span>`
                          : item.latestCaptureAttentionCount
                            ? `<span class="source-pill">raw attention ${item.latestCaptureAttentionCount}</span>`
                          : `<span class="source-pill">已并入 ${item.latestCaptureImportRunId ?? "最新批次"}</span>`
                      }
                    </div>
                  `
                  : ""
              }
              <div class="source-meta">
                <span class="source-pill">Sale: ${item.saleQuery}</span>
                <span class="source-pill">Rent: ${item.rentQuery}</span>
              </div>
              <small class="ranking-note">${item.reason} ${item.captureGoal}</small>
              <div class="queue-item-footer anchor-action-row">
                <button class="action compact" data-browser-copy-sale="${item.taskId}">复制 Sale</button>
                <button class="action compact" data-browser-copy-rent="${item.taskId}">复制 Rent</button>
                <button class="action compact primary" data-browser-open-capture="${item.taskId}">录入原文</button>
              </div>
            </article>
          `;
        })
        .join("")
    : `<p class="helper-text">${
        currentDataMode() === "empty"
          ? "当前还没有 staged 研究样本，采样任务包会在 reference / import / metrics 就绪后出现。"
          : "当前筛选窗口下没有需要优先补的公开页面采样任务。"
      }</p>`;

  browserSamplingPack.querySelectorAll(".ranking-item[data-community-id]").forEach((item) => {
    const activate = async () => {
      const task = samplingTasks.find((taskItem) => taskItem.taskId === item.dataset.taskId);
      if (!task?.taskId) {
        return;
      }
      await navigateToBrowserSamplingTask(task, {
        resetDraft: false,
        waypoint: {
          source: "browser_sampling",
          label: item.querySelector("strong")?.textContent?.replace(/^\d+\.\s*/, "") ?? "公开页采样任务",
          detail: "公开页采样执行台与对应证据"
        }
      });
    };
    item.addEventListener("click", activate);
    bindKeyboardActivation(item, activate);
  });

  browserSamplingPack.querySelectorAll("[data-browser-copy-sale]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = samplingTasks.find((item) => item.taskId === button.dataset.browserCopySale);
      await copyTextToClipboard(task?.saleQuery, "Sale 检索词已复制。");
    });
  });

  browserSamplingPack.querySelectorAll("[data-browser-copy-rent]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = samplingTasks.find((item) => item.taskId === button.dataset.browserCopyRent);
      await copyTextToClipboard(task?.rentQuery, "Rent 检索词已复制。");
    });
  });

  browserSamplingPack.querySelectorAll("[data-browser-open-capture]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = samplingTasks.find((item) => item.taskId === button.dataset.browserOpenCapture);
      if (!task) {
        return;
      }
      await navigateToBrowserSamplingTask(task, {
        resetDraft: true,
        waypoint: {
          source: "browser_sampling",
          label: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}`,
          detail: "公开页采样执行台与对应证据"
        }
      });
      render();
    });
  });
}

function renderMatrix() {
  const community = state.selectedCommunityDetail ?? getSelectedCommunity();
  if (!community) {
    matrixTitle.textContent = "楼栋 × 楼层回报率表";
    matrixTable.innerHTML = "<p>当前没有楼栋级样本。</p>";
    return;
  }

  matrixTitle.textContent = `${community.name} · 楼栋 × 楼层回报率表`;

  matrixTable.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>楼栋</th>
          <th>总层数</th>
          <th>低楼层</th>
          <th>中楼层</th>
          <th>高楼层</th>
          <th>机会分</th>
        </tr>
      </thead>
      <tbody>
        ${community.buildings
          .map(
            (building) => `
              <tr
                class="${building.id === state.selectedBuildingId ? "is-active" : ""}"
                data-building-id="${building.id}"
                role="button"
                tabindex="0"
                aria-pressed="${building.id === state.selectedBuildingId ? "true" : "false"}"
              >
                <td>${building.name}</td>
                <td>${building.totalFloors}</td>
                <td><span class="yield-chip ${yieldClass(building.low)}">${building.low.toFixed(2)}%</span></td>
                <td><span class="yield-chip ${yieldClass(building.mid)}">${building.mid.toFixed(2)}%</span></td>
                <td><span class="yield-chip ${yieldClass(building.high)}">${building.high.toFixed(2)}%</span></td>
                <td>${building.score}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;

  matrixTable.querySelectorAll("tbody tr[data-building-id]").forEach((row) => {
    const activate = async () => {
      await selectBuilding(row.dataset.buildingId);
      announceMapWaypoint({
        source: "matrix",
        label: `${community.name} · ${row.querySelector("td")?.textContent?.trim() ?? "楼栋"}`,
        detail: "楼栋研究摘要与楼层机会带"
      });
    };
    row.addEventListener("click", activate);
    bindKeyboardActivation(row, activate);
  });
}

function renderPipeline() {
  pipeline.innerHTML = pipelineSteps
    .map(
      (step, index) => `
        <article class="pipeline-step">
          <strong>${index + 1}. ${step.title}</strong>
          <p>${step.description}</p>
          <small>${step.meta}</small>
        </article>
      `
    )
    .join("");
}

function renderSchemas() {
  schemaList.innerHTML = schemas
    .map(
      (schema) => `
        <article class="schema-row">
          <strong>${schema.name}</strong>
          <p>${schema.description}</p>
          <small>${schema.fields}</small>
        </article>
      `
    )
    .join("");
}

function renderStrategy() {
  const fallbackStrategy = {
    map_stack: {
      primary: {
        name: "高德地图",
        role: "中国场景主前端底图与交互容器",
        why: "适合区级浏览、小区下钻和 GeoJSON 交互。"
      },
      secondary: {
        name: "Google Earth / KML",
        role: "内部分析、导出和巡检",
        why: "更适合研究、演示和结果分享。"
      }
    },
    coordinate_policy: {
      storage: "原始坐标 + 标准坐标双写",
      china_web: "GCJ-02 优先",
      google_earth: "WGS-84 导出"
    },
    data_policy: {
      priority: "官方合作 / 开放平台优先",
      fallback: "低频人工导入与校正",
      risk_note: "避免把长期产品建立在不稳定抓取链路上。"
    },
    address_model: ["district", "resblock", "building", "unit", "floor"]
  };

  const strategy = systemStrategy ?? fallbackStrategy;
  const fallbackSources = [
    {
      id: "amap-aoi-poi",
      name: "高德 AOI / POI / District",
      category: "map_enrichment",
      priority: "medium",
      coverage: "行政区、小区 AOI 和地图增强",
      role: "主地图增强"
    }
  ];
  const sources = dataSources.length ? dataSources : fallbackSources;

  strategyPanel.innerHTML = `
    <article class="strategy-item">
      <span class="strategy-kicker">Primary</span>
      <strong>${strategy.map_stack.primary.name}</strong>
      <p>${strategy.map_stack.primary.role}</p>
      <small>${strategy.map_stack.primary.why}</small>
    </article>
    <article class="strategy-item">
      <span class="strategy-kicker">Secondary</span>
      <strong>${strategy.map_stack.secondary.name}</strong>
      <p>${strategy.map_stack.secondary.role}</p>
      <small>${strategy.map_stack.secondary.why}</small>
    </article>
    <article class="strategy-item">
      <span class="strategy-kicker">Coordinate</span>
      <strong>${strategy.coordinate_policy.storage}</strong>
      <p>前端: ${strategy.coordinate_policy.china_web}</p>
      <small>导出: ${strategy.coordinate_policy.google_earth}</small>
    </article>
    <article class="strategy-item">
      <span class="strategy-kicker">Address</span>
      <strong>${strategy.address_model.join(" → ")}</strong>
      <p>${strategy.data_policy.priority}</p>
      <small>${strategy.data_policy.risk_note}</small>
    </article>
  `;

  dataSourceList.innerHTML = sources
    .map(
      (source) => `
        <article class="source-item">
          <strong>${source.name}</strong>
          <p>${source.role}</p>
          <div class="source-meta">
            <span class="source-pill">${source.category}</span>
            <span class="source-pill">priority: ${source.priority}</span>
          </div>
          <small>${source.coverage}</small>
          ${source.recommendedNextStep ? `<p class="source-hint">${source.recommendedNextStep}</p>` : ""}
          ${renderProviderActions(source)}
        </article>
      `
    )
    .join("");
}

function renderOperations() {
  const operations = effectiveOperationsOverview();
  const selectedCommunityId = state.selectedCommunityId;
  const summary = operations.summary;
  const sourceHealth = operations.sourceHealth ?? [];
  const importRuns = operations.importRuns ?? [];
  const metricsRuns = operations.metricsRuns ?? [];
  const metricsRefreshHistory = operations.metricsRefreshHistory ?? [];
  const geoAssetRuns = operations.geoAssetRuns ?? [];
  const queueItems = (operations.addressQueue ?? []).slice().sort((left, right) => {
    const leftScore = (left.communityId === selectedCommunityId ? 100 : 0) + left.confidence * 10;
    const rightScore = (right.communityId === selectedCommunityId ? 100 : 0) + right.confidence * 10;
    return rightScore - leftScore;
  });
  const selectedRunId = state.selectedImportRunId;
  const selectedRunDetail = state.selectedImportRunDetail;
  const selectedGeoRunId = state.selectedGeoAssetRunId;
  const selectedGeoRunDetail = state.selectedGeoAssetRunDetail;
  if (!operationsHistoryTabs.includes(state.operationsHistoryTab)) {
    state.operationsHistoryTab = "reference";
  }
  if (!operationsDetailTabs.includes(state.operationsDetailTab)) {
    state.operationsDetailTab = "geo";
  }
  if (!operationsQualityTabs.includes(state.operationsQualityTab)) {
    state.operationsQualityTab = "workbench";
  }
  const referenceRuns = operationsOverview?.referenceRuns ?? [];
  const postgresReady = runtimeConfig.hasPostgresDsn;
  const postgresLabel = runtimeConfig.postgresDsnMasked ?? "未配置 POSTGRES_DSN";
  const displayQueueItems = selectedRunId
    ? queueItems.filter((item) => !item.runId || item.runId === selectedRunId)
    : queueItems;
  const baselineOptions = selectedRunId ? availableBaselineRunsFor(selectedRunId) : [];
  const geoBaselineOptions = selectedGeoRunId ? availableGeoBaselineRunsFor(selectedGeoRunId) : [];
  const geoWorkOrderSummary = selectedGeoRunDetail?.workOrderSummary ?? {};
  const filteredGeoWorkOrders = getGeoWorkOrderItems();
  const geoWorkOrderAssignees = getGeoWorkOrderAssignees();
  const dataModeLabel =
    summary.activeDataMode === "database"
      ? "数据库主读"
      : summary.activeDataMode === "staged"
      ? "离线快照"
      : summary.activeDataMode === "mock"
      ? "Demo Mock"
      : "待接入";
  const dataModeHint = summary.hasRealData
    ? "地图与详情优先读 PostgreSQL"
    : summary.activeDataMode === "staged"
    ? "当前优先展示最新离线授权 / 公开样本批次"
    : summary.mockEnabled
    ? "当前允许 demo 回退"
    : "当前不会伪装成已有数据";
  const databaseStatusLabel = !postgresReady
    ? "未配置"
    : summary.databaseSeeded
    ? "已引导"
    : summary.databaseConnected
    ? "待引导"
    : "未连接";
  const databaseStatusHint = !postgresReady
    ? "先配置 POSTGRES_DSN。"
    : summary.databaseSeeded
    ? `当前主读 ${summary.databaseCommunityCount ?? 0} 个小区 / ${summary.databaseBuildingCount ?? 0} 栋楼。`
    : summary.databaseConnected
    ? "数据库已连通，但还没完成首轮 reference / import / geo / metrics 落库。"
    : "DSN 已配置，但当前数据库还不可读。";
  const canWriteMetricsToDatabase = postgresReady && summary.databaseConnected && summary.databaseSeeded;
  const stagedMetricsLabel = summary.latestStagedMetricsRunAt ? formatTimestamp(summary.latestStagedMetricsRunAt) : "未生成";
  const databaseMetricsLabel = summary.latestDatabaseMetricsRefreshAt ? formatTimestamp(summary.latestDatabaseMetricsRefreshAt) : "未写库";
  const metricsStatusHint = canWriteMetricsToDatabase
    ? "数据库已就绪，可选择只更新 staged 或连带同步 PostgreSQL。"
    : postgresReady && summary.databaseConnected
    ? "数据库已连通，但建议先完成本地 Bootstrap 再同步 metrics 表。"
    : "当前只刷新 staged metrics run，统一离线研究口径。";
  const anchoredCommunityCount = Number(summary.anchoredCommunityCount ?? 0);
  const cityCommunityCount = Number(summary.cityCommunityCount ?? 0);
  const anchoredCommunityPct = cityCommunityCount
    ? (anchoredCommunityCount / cityCommunityCount) * 100
    : Number(summary.anchoredCommunityPct ?? 0);
  const readySourceCount = Number(summary.readySourceCount ?? sourceHealth.length);
  const sourceCount = Number(summary.sourceCount ?? sourceHealth.length);
  const reviewQueueCount = Number(summary.reviewQueueCount ?? 0);
  const browserCaptureRunCount = Number(summary.browserCaptureRunCount ?? 0);
  const pendingAnchorCount = Number(summary.pendingAnchorCount ?? Math.max(cityCommunityCount - anchoredCommunityCount, 0));
  const providerPendingCount = Math.max(sourceCount - readySourceCount, 0);
  const samplingTaskCount = Number(state.browserSamplingPackItems?.length ?? 0);
  const prioritySamplingCount = (state.browserSamplingPackItems ?? []).filter((item) => item.focusScope === "priority").length;
  const geoOpenTaskCount = Number(summary.geoAssetOpenTaskCount ?? geoAssetRuns.reduce((sum, item) => sum + (item.openTaskCount ?? 0), 0));
  const geoCriticalTaskCount = Number(summary.geoAssetCriticalTaskCount ?? selectedGeoRunDetail?.taskSummary?.criticalOpenTaskCount ?? 0);
  const geoLinkedTaskCount = Number(summary.geoAssetWatchlistLinkedTaskCount ?? selectedGeoRunDetail?.taskSummary?.watchlistLinkedTaskCount ?? 0);
  const importRunCount = Number(summary.importRunCount ?? importRuns.length);
  const referenceRunCount = Number(summary.referenceRunCount ?? referenceRuns.length);
  const metricsRunCount = Number(summary.metricsRunCount ?? metricsRuns.length);
  const geoAssetRunCount = Number(summary.geoAssetRunCount ?? geoAssetRuns.length);
  const latestBootstrapLabel = summary.latestBootstrapAt ? formatTimestamp(summary.latestBootstrapAt) : "暂无";
  const latestAnchorLabel = summary.latestAnchorReviewAt ? formatTimestamp(summary.latestAnchorReviewAt) : "暂无";
  const latestMetricsLabel = summary.latestMetricsRefreshAt ? formatTimestamp(summary.latestMetricsRefreshAt) : "待刷新";
  const overviewStatusHint = `${dataModeHint}。`;
  const bootstrapActionHint = postgresReady ? "先把本地库引导成可主读，再切数据库口径。" : "先配置 POSTGRES_DSN，再打开数据库主读。";
  const metricsActionHint = canWriteMetricsToDatabase
    ? "可只刷 staged，也可同步 PostgreSQL。"
    : postgresReady && summary.databaseConnected
    ? "先做 Bootstrap，再同步 metrics 表。"
    : "当前只刷新 staged。";
  const stagedMetricsSummary =
    summary.activeDataMode === "database"
      ? `${summary.databaseSaleListingCount ?? 0} sale / ${summary.databaseRentListingCount ?? 0} rent`
      : `${metricsRunCount} 个 staged metrics run`;
  const providerHint = providerPendingCount ? `待补凭证 ${providerPendingCount} 个。` : "链路已就绪。";
  const coverageHint = pendingAnchorCount ? `待补锚点 ${pendingAnchorCount} 个。` : cityCommunityCount ? "已全部挂图。" : "等待首批锚点。";
  const samplingHint = `${browserCaptureRunCount} 次公开页采样${prioritySamplingCount ? ` · 重点区 ${prioritySamplingCount}` : ""}`;
  const batchHint = `批次 ${referenceRunCount}/${importRunCount}/${metricsRunCount}/${geoAssetRunCount}`;

  opsSummary.innerHTML = `
    ${
      state.opsMessage && state.opsMessageContext === "database"
        ? `<div class="ops-feedback ${state.opsMessageTone}">${state.opsMessage}</div>`
        : ""
    }
    <article class="ops-overview-hero">
      <div class="ops-overview-head">
        <span class="ops-overview-kicker">运行态势</span>
        <strong>${dataModeLabel} · ${databaseStatusLabel}</strong>
        <p>${overviewStatusHint}</p>
        <div class="comparison-strip">
          <span class="source-pill">Provider ${readySourceCount}/${sourceCount}</span>
          <span class="source-pill">挂图 ${anchoredCommunityCount}/${cityCommunityCount}</span>
          <span class="source-pill">待复核 ${reviewQueueCount}</span>
          <span class="source-pill">采样任务 ${samplingTaskCount}</span>
        </div>
      </div>
      <div class="ops-overview-stat-grid">
        <article class="ops-overview-stat tone-live">
          <span>最近指标快照</span>
          <strong>${latestMetricsLabel}</strong>
          <small>${stagedMetricsSummary}</small>
        </article>
        <article class="ops-overview-stat">
          <span>最近引导</span>
          <strong>${latestBootstrapLabel}</strong>
          <small>${postgresLabel}</small>
        </article>
      </div>
    </article>
    <article class="ops-overview-card ops-overview-card--coverage">
      <span class="ops-overview-kicker">地图覆盖</span>
      <strong>${anchoredCommunityCount}/${cityCommunityCount}</strong>
      <p>${anchoredCommunityPct.toFixed(1)}% 已锚定</p>
      <small>${coverageHint} 最近确认 ${latestAnchorLabel}。</small>
    </article>
    <article class="ops-overview-card ops-overview-card--sampling">
      <span class="ops-overview-kicker">采样与复核</span>
      <strong>${reviewQueueCount}</strong>
      <p>重点盯单元、门牌和 attention 队列</p>
      <small>${samplingTaskCount} 个采样任务 · ${samplingHint}</small>
    </article>
    <article class="ops-overview-card ops-overview-card--geo">
      <span class="ops-overview-kicker">几何补采</span>
      <strong>${geoOpenTaskCount}</strong>
      <p>缺口补采与未命中复核待处理</p>
      <small>紧急 ${geoCriticalTaskCount} · 榜单关联 ${geoLinkedTaskCount}</small>
    </article>
    <article class="ops-overview-card ops-overview-card--pipeline">
      <span class="ops-overview-kicker">数据链路</span>
      <strong>${readySourceCount}/${sourceCount}</strong>
      <p>provider readiness 与落地批次</p>
      <small>${providerHint} ${batchHint}</small>
    </article>
    <article class="ops-overview-card ops-overview-card--action">
      <div class="ops-overview-action-grid">
        <section class="ops-overview-action-block">
          <span class="ops-overview-kicker">引导</span>
          <strong>${postgresReady ? "reference → import → geo → metrics" : "等待 DSN"}</strong>
          <p>${bootstrapActionHint}</p>
          <button class="action compact primary" data-database-bootstrap ${postgresReady ? "" : "disabled"}>
            ${state.busyBootstrapDatabase ? "引导中..." : "本地 Bootstrap"}
          </button>
        </section>
        <section class="ops-overview-action-block">
          <span class="ops-overview-kicker">刷新</span>
          <strong>${latestMetricsLabel}</strong>
          <p>${metricsActionHint}</p>
          <div class="comparison-strip">
            <span class="source-pill">staged ${stagedMetricsLabel}</span>
            <span class="source-pill">${postgresReady ? `db ${databaseMetricsLabel}` : "db 未配置"}</span>
          </div>
          <div class="metric-action-buttons ops-overview-button-row">
            <button
              class="action compact primary"
              data-refresh-metrics
              ${state.busyMetricsRefresh ? "disabled" : ""}
              title="生成一批新的 staged metrics run，统一当前研究口径。"
            >
              ${state.busyMetricsRefresh && state.busyMetricsRefreshMode === "staged" ? "刷新中..." : "刷新 staged"}
            </button>
            ${
              postgresReady
                ? `
                  <button
                    class="action compact"
                    data-refresh-metrics-postgres
                    ${state.busyMetricsRefresh || !canWriteMetricsToDatabase ? "disabled" : ""}
                    title="${
                      canWriteMetricsToDatabase
                        ? "基于同一轮快照同时写入 PostgreSQL metrics 表。"
                        : "先完成本地 Bootstrap，让数据库具备可写的基础表与首轮数据。"
                    }"
                  >
                    ${state.busyMetricsRefresh && state.busyMetricsRefreshMode === "postgres" ? "写库中..." : "同步 PostgreSQL"}
                  </button>
                `
                : ""
            }
          </div>
        </section>
      </div>
    </article>
  `;

  referenceRunList.innerHTML = referenceRuns.length
    ? `
        <article class="import-run-section">
          <div class="breakdown-top">
            <strong>Reference 主档批次</strong>
            <span class="badge">${referenceRuns.length}</span>
          </div>
          <div class="import-run-grid">
            ${referenceRuns
              .map(
                (run, index) => `
                  <article class="import-run-card ${index === 0 ? "is-active" : ""}">
                    <div class="breakdown-top">
                      <strong>${run.batchName}</strong>
                      <span class="trace-status resolved">${run.storageMode === "database+file" ? "已写库" : "可写库"}</span>
                    </div>
                    <p>${sourceLabelById(run.providerId)} · ${formatTimestamp(run.createdAt)}</p>
                    <div class="import-run-metrics">
                      <span class="source-pill">行政区 ${run.districtCount ?? 0}</span>
                      <span class="source-pill">小区 ${run.communityCount ?? 0}</span>
                      <span class="source-pill">楼栋 ${run.buildingCount ?? 0}</span>
                      <span class="source-pill">已锚定 ${run.anchoredCommunityCount ?? 0}</span>
                    </div>
                    <div class="queue-item-footer">
                      <button class="action compact ${postgresReady ? "primary" : ""}" data-reference-persist-run-id="${run.runId}" ${postgresReady ? "" : "disabled"}>
                        ${state.busyReferencePersistRunId === run.runId ? "写入中..." : "写入 PostgreSQL"}
                      </button>
                    </div>
                  </article>
                `
              )
              .join("")}
          </div>
        </article>
      `
    : "<p class=\"helper-text\">当前还没有 reference 主档批次。先导入小区 / 楼栋主档，再执行数据库引导。</p>";

  importRunList.innerHTML = importRuns.length
    ? importRuns
        .map(
          (run) => `
            <article class="import-run-card ${run.runId === selectedRunId ? "is-active" : ""}" data-run-id="${run.runId}">
              <div class="breakdown-top">
                <strong>${run.batchName}</strong>
                <span class="trace-status ${run.reviewCount > 0 ? "needs_review" : "resolved"}">
                  ${Math.round((run.resolvedRate ?? 0) * 100)}%
                </span>
              </div>
              <p>${sourceLabelById(run.providerId)} · ${formatTimestamp(run.createdAt)}</p>
              <div class="import-run-metrics">
                <span class="source-pill">已归一 ${run.resolvedCount}</span>
                <span class="source-pill">待复核 ${run.reviewCount}</span>
                <span class="source-pill">配对 ${run.pairCount}</span>
                <span class="source-pill">逐层证据 ${run.evidenceCount}</span>
              </div>
            </article>
          `
        )
        .join("")
    : "<p class=\"helper-text\">当前还没有导入批次。先运行授权 CSV 导入任务，这里会出现批次记录。</p>";

  const metricsRefreshHistoryMarkup = metricsRefreshHistory.length
    ? `
        <article class="import-run-section">
          <div class="breakdown-top">
            <strong>最近指标刷新</strong>
            <span class="badge">${metricsRefreshHistory.length}</span>
          </div>
          <div class="import-run-grid">
            ${metricsRefreshHistory
              .map((item, index) => {
                const summaryCounts = item.summary ?? {};
                const statusLabel = escapeHtml(item.statusLabel ?? metricsRefreshStatusLabel(item.status));
                const triggerLabel = escapeHtml(item.triggerLabel ?? metricsRefreshTriggerLabel(item.triggerSource));
                const modeLabel = escapeHtml(item.modeLabel ?? metricsRefreshModeLabel(item.mode));
                const postgresLabel = escapeHtml(metricsRefreshPostgresLabel(item.postgresStatus));
                const batchName = escapeHtml(truncate(item.batchName ?? "未命名批次", 60));
                const snapshotDate = escapeHtml(item.snapshotDate ?? "待补");
                const errorMarkup = item.error ? `<p class="helper-text">${escapeHtml(truncate(item.error, 96))}</p>` : "";
                return `
                  <article class="import-run-card ${index === 0 ? "is-active" : ""}">
                    <div class="breakdown-top">
                      <strong>${batchName}</strong>
                      <span class="trace-status ${metricsRefreshStatusTone(item.status)}">${statusLabel}</span>
                    </div>
                    <p>${formatTimestamp(item.createdAt)} · ${triggerLabel} · ${modeLabel}</p>
                    <div class="import-run-metrics">
                      <span class="source-pill">快照日 ${snapshotDate}</span>
                      <span class="source-pill">${postgresLabel}</span>
                      <span class="source-pill">小区指标 ${Number(summaryCounts.communityMetricCount ?? 0)}</span>
                      <span class="source-pill">楼栋分桶 ${Number(summaryCounts.buildingFloorMetricCount ?? 0)}</span>
                      <span class="source-pill">小区覆盖 ${Number(summaryCounts.communityCoverageCount ?? 0)}</span>
                      <span class="source-pill">楼栋覆盖 ${Number(summaryCounts.buildingCoverageCount ?? 0)}</span>
                    </div>
                    ${errorMarkup}
                  </article>
                `;
              })
              .join("")}
          </div>
        </article>
      `
    : "";

  const metricsRunsMarkup = metricsRuns.length
    ? `
        <article class="import-run-section">
          <div class="breakdown-top">
            <strong>Metrics 快照批次</strong>
            <span class="badge">${metricsRuns.length}</span>
          </div>
          <div class="import-run-grid">
            ${metricsRuns
              .map(
                (run, index) => `
                  <article class="import-run-card ${index === 0 ? "is-active" : ""}">
                    <div class="breakdown-top">
                      <strong>${run.batchName}</strong>
                      <span class="trace-status resolved">${index === 0 ? "当前口径" : "历史快照"}</span>
                    </div>
                    <p>${formatTimestamp(run.createdAt)} · 快照日 ${run.snapshotDate ?? "待补"}</p>
                    <div class="import-run-metrics">
                      <span class="source-pill">小区指标 ${run.communityMetricCount ?? 0}</span>
                      <span class="source-pill">楼栋分桶 ${run.buildingFloorMetricCount ?? 0}</span>
                      <span class="source-pill">小区覆盖 ${run.communityCoverageCount ?? 0}</span>
                      <span class="source-pill">楼栋覆盖 ${run.buildingCoverageCount ?? 0}</span>
                    </div>
                  </article>
                `
              )
              .join("")}
          </div>
        </article>
      `
    : "<p class=\"helper-text\">当前还没有 staged metrics run。可以先运行 `python3 jobs/refresh_metrics.py --batch-name staged-metrics-YYYY-MM-DD` 生成统一指标口径。</p>";

  metricsRunList.innerHTML = `${metricsRefreshHistoryMarkup}${metricsRunsMarkup}`;

  geoAssetRunList.innerHTML = geoAssetRuns.length
    ? `
        <article class="import-run-section">
          <div class="breakdown-top">
            <strong>空间几何批次</strong>
            <span class="badge">${geoAssetRuns.length}</span>
          </div>
          <div class="import-run-grid">
            ${geoAssetRuns
              .map(
                (run, index) => `
                  <article class="import-run-card ${run.runId === selectedGeoRunId || (!selectedGeoRunId && index === 0) ? "is-active" : ""}" data-geo-run-id="${run.runId}">
                    <div class="breakdown-top">
                      <strong>${run.batchName}</strong>
                      <span class="trace-status resolved">${run.runId === selectedGeoRunId || (!selectedGeoRunId && index === 0) ? "当前地图" : "可回放"}</span>
                    </div>
                    <p>${sourceLabelById(run.providerId)} · ${formatTimestamp(run.createdAt)}</p>
                    <div class="import-run-metrics">
                      <span class="source-pill">要素 ${run.featureCount}</span>
                      <span class="source-pill">楼栋 ${run.resolvedBuildingCount}</span>
                      <span class="source-pill">小区 ${run.communityCount}</span>
                      <span class="source-pill">覆盖 ${run.coveragePct}%</span>
                      <span class="source-pill">打开任务 ${run.openTaskCount ?? 0}</span>
                    </div>
                  </article>
                `
              )
              .join("")}
          </div>
        </article>
      `
    : "<p class=\"helper-text\">当前还没有独立的空间几何批次，楼栋 / 楼层 footprint 会回退到本地推导。</p>";

  geoAssetRunDetail.innerHTML = selectedGeoRunDetail
    ? `
      ${
        state.opsMessage && state.opsMessageContext === "geo"
          ? `<div class="ops-feedback ${state.opsMessageTone}">${state.opsMessage}</div>`
          : ""
      }
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>几何批次详情 · ${selectedGeoRunDetail.batchName}</strong>
          <div class="section-actions">
            <span class="trace-status resolved">${selectedGeoRunDetail.assetType ?? "building_footprint"}</span>
            <button
              class="action compact ${postgresReady ? "primary" : ""}"
              data-geo-persist-run-id="${selectedGeoRunDetail.runId}"
              ${postgresReady ? "" : "disabled"}
              title="${postgresReady ? "把该几何批次写入 PostgreSQL geo_assets 表。" : "先配置 POSTGRES_DSN 才能写入 PostgreSQL。"}"
            >
              ${state.busyGeoPersistRunId === selectedGeoRunDetail.runId ? "写入中..." : "写入 PostgreSQL"}
            </button>
          </div>
        </div>
        <p>${sourceLabelById(selectedGeoRunDetail.providerId)} · ${formatTimestamp(selectedGeoRunDetail.createdAt)}</p>
        <div class="comparison-strip">
          <span class="source-pill">目录楼栋 ${selectedGeoRunDetail.coverage?.catalogBuildingCount ?? 0}</span>
          <span class="source-pill">已覆盖 ${selectedGeoRunDetail.coverage?.resolvedBuildingCount ?? 0}</span>
          <span class="source-pill">缺口 ${selectedGeoRunDetail.coverage?.missingBuildingCount ?? 0}</span>
          <span class="source-pill">目录覆盖 ${selectedGeoRunDetail.coverage?.catalogCoveragePct ?? selectedGeoRunDetail.coveragePct ?? 0}%</span>
          <span class="source-pill">打开任务 ${selectedGeoRunDetail.taskSummary?.openTaskCount ?? 0}</span>
        </div>
        <div class="field compact">
          <div class="field-header">
            <span>对比基线</span>
            <strong>${state.selectedGeoBaselineRunId ? "手动指定" : "自动上一批"}</strong>
          </div>
          <select data-geo-baseline-run-select>
            <option value="">自动选择上一批</option>
            ${geoBaselineOptions
              .map(
                (item) => `
                  <option value="${item.runId}" ${item.runId === state.selectedGeoBaselineRunId ? "selected" : ""}>
                    ${item.batchName} · ${formatTimestamp(item.createdAt)}
                  </option>
                `
              )
              .join("")}
          </select>
        </div>
      </article>
      ${
        selectedGeoRunDetail.comparison
          ? `
            <article class="import-run-section" data-browser-capture-current-task-runs="true">
              <div class="breakdown-top">
                <strong>相对基线几何批次的变化</strong>
                <span class="badge">${selectedGeoRunDetail.comparison.baselineBatchName}</span>
              </div>
              <p>对比基线 · ${selectedGeoRunDetail.comparison.baselineBatchName} · ${formatTimestamp(
                selectedGeoRunDetail.comparison.baselineCreatedAt
              )}</p>
              <div class="comparison-strip">
                <span class="source-pill">目录覆盖 ${formatSignedDelta(selectedGeoRunDetail.comparison.coveragePctDelta, {
                  suffix: "pt",
                  digits: 1
                })}</span>
                <span class="source-pill">已覆盖楼栋 ${formatSignedDelta(selectedGeoRunDetail.comparison.resolvedBuildingDelta)}</span>
                <span class="source-pill">覆盖缺口 ${formatSignedDelta(selectedGeoRunDetail.comparison.missingBuildingDelta)}</span>
                <span class="source-pill">打开任务 ${formatSignedDelta(selectedGeoRunDetail.comparison.openTaskDelta)}</span>
                <span class="source-pill">待补采 ${formatSignedDelta(selectedGeoRunDetail.comparison.captureTaskDelta)}</span>
                <span class="source-pill">已关闭 ${formatSignedDelta(selectedGeoRunDetail.comparison.resolvedTaskDelta)}</span>
                <span class="source-pill">紧急任务 ${formatSignedDelta(selectedGeoRunDetail.comparison.criticalOpenTaskDelta)}</span>
                <span class="source-pill">榜单关联 ${formatSignedDelta(selectedGeoRunDetail.comparison.watchlistLinkedTaskDelta)}</span>
                <span class="source-pill">新增覆盖 ${selectedGeoRunDetail.comparison.newBuildingCount}</span>
                <span class="source-pill">几何修正 ${selectedGeoRunDetail.comparison.changedGeometryCount}</span>
              </div>
              <div class="import-run-grid">
                ${(selectedGeoRunDetail.comparison.topBuildingChanges ?? []).length
                  ? (selectedGeoRunDetail.comparison.topBuildingChanges ?? [])
                      .map(
                        (item) => `
                          <article
                            class="import-run-evidence"
                            data-community-id="${item.communityId ?? ""}"
                            data-building-id="${item.buildingId ?? ""}"
                          >
                            <div class="breakdown-top">
                              <strong>${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"}</strong>
                              <span class="trace-status ${geoComparisonToneClass(item.status)}">${item.statusLabel}</span>
                            </div>
                            <p>${item.districtName ?? "未知行政区"} · ${item.sourceRef ?? "待补 source_ref"}</p>
                            <small>
                              ${
                                item.status === "changed"
                                  ? `中心漂移 ${
                                      item.centroidShiftMeters !== null && item.centroidShiftMeters !== undefined
                                        ? `${Number(item.centroidShiftMeters).toFixed(1)}m`
                                        : "待补"
                                    } · 面积变化 ${formatSignedDelta(item.areaDeltaPct, {
                                      suffix: "%",
                                      digits: 1,
                                      emptyLabel: "待补"
                                    })}`
                                  : item.status === "removed"
                                    ? "这栋楼在当前批次里未再提供 footprint，建议回看导出链路。"
                                    : "这栋楼是相对基线新增补齐的 footprint。"
                              }
                            </small>
                          </article>
                        `
                      )
                      .join("")
                  : "<p class=\"helper-text\">当前批次相对基线还没有显著几何变化。</p>"}
              </div>
            </article>
          `
          : ""
      }
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>几何任务队列</strong>
          <span class="badge">${selectedGeoRunDetail.taskSummary?.taskCount ?? (selectedGeoRunDetail.coverageTasks ?? []).length}</span>
        </div>
        <div class="comparison-strip">
          <span class="source-pill">待复核 ${selectedGeoRunDetail.taskSummary?.reviewTaskCount ?? 0}</span>
          <span class="source-pill">待补采 ${selectedGeoRunDetail.taskSummary?.captureTaskCount ?? 0}</span>
          <span class="source-pill">已派工 ${selectedGeoRunDetail.taskSummary?.scheduledTaskCount ?? 0}</span>
          <span class="source-pill">已关闭 ${selectedGeoRunDetail.taskSummary?.resolvedTaskCount ?? 0}</span>
          <span class="source-pill">紧急 ${selectedGeoRunDetail.taskSummary?.criticalOpenTaskCount ?? 0}</span>
          <span class="source-pill">榜单关联 ${selectedGeoRunDetail.taskSummary?.watchlistLinkedTaskCount ?? 0}</span>
          <span class="source-pill">均值 ${Number(selectedGeoRunDetail.taskSummary?.avgImpactScore ?? 0).toFixed(1)}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.coverageTasks ?? []).length
              ? (selectedGeoRunDetail.coverageTasks ?? [])
                  .slice()
                  .slice(0, 6)
                  .map((item) => {
                    const nextStatus = item.workOrderId ? null : nextGeoTaskStatus(item);
                    return `
                      <article
                        class="queue-item is-imported ${item.communityId === selectedCommunityId ? "is-related" : ""}"
                        data-geo-task-id="${item.taskId ?? ""}"
                        data-community-id="${item.communityId ?? ""}"
                        data-building-id="${item.buildingId ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"}</strong>
                          <span class="trace-status ${item.status}">${geoTaskStatusLabel(item.status)}</span>
                        </div>
                        <p>${item.taskScope === "unresolved_feature" ? "未命中楼栋词典" : `${item.districtName ?? "未知行政区"} · ${item.sourceRef ?? "待补 source_ref"}`}</p>
                        <div class="comparison-strip">
                          <span class="trace-status ${geoImpactBandClass(item.impactBand)}">${item.impactLabel}</span>
                          <span class="source-pill">影响 ${item.impactScore ?? 0}</span>
                          <span class="source-pill">${item.taskScopeLabel ?? geoTaskStatusLabel(item.taskScope)}</span>
                          <span class="source-pill">榜单 ${item.watchlistHits ?? 0}</span>
                          ${
                            item.workOrderId
                              ? `<span class="source-pill">工单 ${geoWorkOrderStatusLabel(item.workOrderStatus)} · ${item.workOrderAssignee ?? "待分配"}</span>`
                              : ""
                          }
                        </div>
                        <small>${item.recommendedAction ?? item.resolutionNotes ?? "等待处理。"}</small>
                        ${
                          (item.watchlistFloors ?? []).length
                            ? `
                              <div class="comparison-strip">
                                ${(item.watchlistFloors ?? [])
                                  .map(
                                    (floor) => `
                                      <span class="source-pill">
                                        ${floor.floorNo}层 · ${Number(floor.latestYieldPct ?? 0).toFixed(2)}% · ${floor.trendLabel}
                                      </span>
                                    `
                                  )
                                  .join("")}
                              </div>
                            `
                            : ""
                        }
                        ${
                          canCreateGeoWorkOrder(item)
                            ? `
                              <div class="queue-item-footer">
                                <button
                                  class="action compact"
                                  data-geo-create-work-order-run-id="${selectedGeoRunDetail.runId}"
                                  data-geo-create-work-order-task-id="${item.taskId}"
                                >
                                  ${state.busyGeoWorkOrderTaskId === item.taskId ? "创建中..." : "生成工单"}
                                </button>
                              </div>
                            `
                            : ""
                        }
                        ${
                          nextStatus
                            ? `
                              <div class="queue-item-footer">
                                <button
                                  class="action compact"
                                  data-geo-review-run-id="${selectedGeoRunDetail.runId}"
                                  data-geo-review-task-id="${item.taskId}"
                                  data-geo-next-status="${nextStatus}"
                                >
                                  ${state.busyGeoTaskId === item.taskId ? "回写中..." : geoTaskActionLabel(item)}
                                </button>
                              </div>
                            `
                            : ""
                        }
                      </article>
                    `;
                  })
                  .join("")
              : "<p class=\"helper-text\">这批几何暂时没有待处理任务。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>补采工单</strong>
          <span class="badge">${geoWorkOrderSummary.workOrderCount ?? (selectedGeoRunDetail.workOrders ?? []).length}</span>
        </div>
        <div class="comparison-strip">
          <span class="source-pill">打开 ${geoWorkOrderSummary.activeWorkOrderCount ?? 0}</span>
          <span class="source-pill">执行中 ${geoWorkOrderSummary.inProgressWorkOrderCount ?? 0}</span>
          <span class="source-pill">待验收 ${geoWorkOrderSummary.deliveredWorkOrderCount ?? 0}</span>
          <span class="source-pill">已关闭 ${geoWorkOrderSummary.closedWorkOrderCount ?? 0}</span>
          <span class="source-pill">已挂任务 ${geoWorkOrderSummary.linkedTaskCount ?? 0}</span>
          <span class="source-pill">未挂工单 ${geoWorkOrderSummary.unassignedOpenTaskCount ?? 0}</span>
        </div>
        <div class="work-order-toolbar">
          <label class="field compact">
            <div class="field-header">
              <span>工单状态</span>
              <strong>${geoWorkOrderFilterLabel(state.geoWorkOrderStatusFilter)}</strong>
            </div>
            <select data-geo-work-order-status-filter>
              ${["all", "open", "assigned", "in_progress", "delivered", "closed"]
                .map(
                  (status) => `
                    <option value="${status}" ${status === state.geoWorkOrderStatusFilter ? "selected" : ""}>
                      ${geoWorkOrderFilterLabel(status)}
                    </option>
                  `
                )
                .join("")}
            </select>
          </label>
          <label class="field compact">
            <div class="field-header">
              <span>责任人</span>
              <strong>${state.geoWorkOrderAssigneeFilter === "all" ? "全部" : state.geoWorkOrderAssigneeFilter}</strong>
            </div>
            <select data-geo-work-order-assignee-filter>
              <option value="all">全部责任人</option>
              ${geoWorkOrderAssignees
                .map(
                  (assignee) => `
                    <option value="${assignee}" ${assignee === state.geoWorkOrderAssigneeFilter ? "selected" : ""}>
                      ${assignee}
                    </option>
                  `
                )
                .join("")}
            </select>
          </label>
          <div class="action-row compact work-order-actions">
            <button class="action compact primary" data-geo-export-work-orders-geojson>导出工单 GeoJSON</button>
            <button class="action compact" data-geo-export-work-orders-csv>导出工单 CSV</button>
          </div>
        </div>
        <div class="comparison-strip">
          <span class="source-pill">当前显示 ${filteredGeoWorkOrders.length}/${(selectedGeoRunDetail.workOrders ?? []).length}</span>
          <span class="source-pill">筛选范围 ${state.districtFilter === "all" ? "全上海" : districtLabelById(state.districtFilter)}</span>
          <span class="source-pill">责任人 ${state.geoWorkOrderAssigneeFilter === "all" ? "全部" : state.geoWorkOrderAssigneeFilter}</span>
        </div>
        <div class="import-run-grid">
          ${
            filteredGeoWorkOrders.length
              ? filteredGeoWorkOrders
                  .map((item) => {
                    const nextStatus = nextGeoWorkOrderStatus(item);
                    return `
                      <article
                        class="queue-item is-imported work-order-card ${item.communityId === selectedCommunityId ? "is-related" : ""}"
                        data-community-id="${item.communityId ?? ""}"
                        data-building-id="${item.buildingId ?? ""}"
                        data-floor-no="${item.focusFloorNo ?? ""}"
                        data-geo-work-order-id="${item.workOrderId ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${item.title}</strong>
                          <span class="trace-status ${item.status}">${geoWorkOrderStatusLabel(item.status)}</span>
                        </div>
                        <p>${item.assignee ?? "待分配"} · ${item.taskCount ?? 0} 条任务${item.dueAt ? ` · 截止 ${formatTimestamp(item.dueAt)}` : ""}</p>
                        <div class="comparison-strip">
                          <span class="source-pill">影响 ${Number(item.impactScore ?? 0).toFixed(1)}</span>
                          <span class="source-pill">榜单 ${item.watchlistHits ?? 0}</span>
                          ${
                            item.focusFloorNo != null
                              ? `<span class="source-pill">${item.focusFloorNo}层 · ${Number(item.focusYieldPct ?? 0).toFixed(2)}%</span>`
                              : ""
                          }
                        </div>
                        ${
                          (item.linkedTasks ?? []).length
                            ? `
                              <div class="comparison-strip">
                                ${(item.linkedTasks ?? [])
                                  .map(
                                    (task) => `
                                      <span class="source-pill">${task.buildingName ?? "待识别楼栋"} · ${task.taskScopeLabel ?? "几何任务"}</span>
                                    `
                                  )
                                  .join("")}
                              </div>
                            `
                            : ""
                        }
                        <small>${item.notes ?? "等待 GIS 跟进。"}</small>
                        ${
                          nextStatus
                            ? `
                              <div class="queue-item-footer">
                                <button
                                  class="action compact"
                                  data-geo-update-work-order-run-id="${selectedGeoRunDetail.runId}"
                                  data-geo-update-work-order-id="${item.workOrderId}"
                                  data-geo-update-work-order-status="${nextStatus}"
                                >
                                  ${state.busyGeoWorkOrderId === item.workOrderId ? "回写中..." : geoWorkOrderActionLabel(item)}
                                </button>
                              </div>
                            `
                            : ""
                        }
                      </article>
                    `;
                  })
                  .join("")
              : (selectedGeoRunDetail.workOrders ?? []).length
                ? "<p class=\"helper-text\">当前筛选条件下没有匹配的补采工单，可以切换状态或责任人继续看。</p>"
              : "<p class=\"helper-text\">当前还没有几何补采工单。可以直接从上面的高影响任务生成。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>覆盖缺口</strong>
          <span class="badge">${(selectedGeoRunDetail.coverageGaps ?? []).filter((item) => item.missingBuildingCount > 0).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.coverageGaps ?? []).some((item) => item.missingBuildingCount > 0)
              ? (selectedGeoRunDetail.coverageGaps ?? [])
                  .filter((item) => item.missingBuildingCount > 0)
                  .slice(0, 6)
                  .map(
                    (item) => `
                      <article class="import-run-evidence" data-community-id="${item.communityId}" data-building-id="${item.missingBuildings?.[0]?.buildingId ?? ""}">
                        <div class="breakdown-top">
                          <strong>${item.communityName}</strong>
                          <span class="trace-status needs_review">缺 ${item.missingBuildingCount} 栋</span>
                        </div>
                        <p>${item.districtName} · 已覆盖 ${item.resolvedBuildingCount}/${item.totalBuildingCount} 栋 · ${item.coveragePct}% </p>
                        <small>${(item.missingBuildings ?? []).map((building) => building.buildingName).join(" / ") || "待补齐楼栋 footprint"}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这批 footprint 在当前目录里没有楼栋覆盖缺口，可继续往更真实的 AOI / 多批次回放推进。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>已命中楼栋预览</strong>
          <span class="badge">${(selectedGeoRunDetail.featurePreview ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.featurePreview ?? []).length
              ? (selectedGeoRunDetail.featurePreview ?? [])
                  .map(
                    (item) => `
                      <article class="import-run-evidence" data-community-id="${item.communityId ?? ""}" data-building-id="${item.buildingId ?? ""}">
                        <div class="breakdown-top">
                          <strong>${item.communityName} · ${item.buildingName}</strong>
                          <span class="trace-status resolved">${item.geometryType ?? "Polygon"}</span>
                        </div>
                        <p>${item.sourceRef ?? "未提供 source_ref"}</p>
                        <small>${item.resolutionNotes ?? "已命中楼栋词典"}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这批几何暂时还没有可预览的楼栋命中记录。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>未命中几何</strong>
          <span class="badge">${(selectedGeoRunDetail.unresolvedFeatures ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.unresolvedFeatures ?? []).length
              ? (selectedGeoRunDetail.unresolvedFeatures ?? [])
                  .slice(0, 6)
                  .map(
                    (item) => `
                      <article class="queue-item is-imported">
                        <div class="breakdown-top">
                          <strong>${item.community_name ?? "待识别小区"} · ${item.building_name ?? "待识别楼栋"}</strong>
                          <span class="trace-status needs_review">待归一</span>
                        </div>
                        <p>${item.source_ref ?? "未提供 source_ref"}</p>
                        <small>${item.resolution_notes ?? "未命中楼栋词典"}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这批几何没有未命中楼栋的 feature。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>几何任务历史</strong>
          <span class="badge">${selectedGeoRunDetail.reviewHistoryCount ?? (selectedGeoRunDetail.recentReviews ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.recentReviews ?? []).length
              ? (selectedGeoRunDetail.recentReviews ?? [])
                  .map(
                    (item) => `
                      <article class="import-run-evidence" data-community-id="${item.communityId ?? ""}" data-building-id="${item.buildingId ?? ""}">
                        <div class="breakdown-top">
                          <strong>${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"}</strong>
                          <span class="trace-status ${item.newStatus}">${geoTaskStatusLabel(item.newStatus)}</span>
                        </div>
                        <p>${item.previousStatus ? `${geoTaskStatusLabel(item.previousStatus)} → ` : ""}${geoTaskStatusLabel(item.newStatus)} · ${item.reviewOwner} · ${formatTimestamp(item.reviewedAt)}</p>
                        <small>${item.resolutionNotes ?? "已记录更新。"}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这批几何暂时还没有任务历史。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>工单流转历史</strong>
          <span class="badge">${selectedGeoRunDetail.workOrderEventCount ?? (selectedGeoRunDetail.recentWorkOrderEvents ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedGeoRunDetail.recentWorkOrderEvents ?? []).length
              ? (selectedGeoRunDetail.recentWorkOrderEvents ?? [])
                  .map(
                    (item) => `
                      <article class="import-run-evidence">
                        <div class="breakdown-top">
                          <strong>${item.workOrderId}</strong>
                          <span class="trace-status ${item.newStatus}">${geoWorkOrderStatusLabel(item.newStatus)}</span>
                        </div>
                        <p>${item.previousStatus ? `${geoWorkOrderStatusLabel(item.previousStatus)} → ` : ""}${geoWorkOrderStatusLabel(item.newStatus)} · ${item.changedBy} · ${formatTimestamp(item.changedAt)}</p>
                        <small>${item.notes ?? "已记录工单变更。"}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这批几何工单暂时还没有流转记录。</p>"
          }
        </div>
      </article>
    `
    : "<p class=\"helper-text\">选择一个几何批次后，这里会展示 footprint 覆盖率、缺口和未命中楼栋。</p>";

  importRunDetail.innerHTML = selectedRunDetail
    ? `
      ${
        state.opsMessage && ["import", "anchor"].includes(state.opsMessageContext)
          ? `<div class="ops-feedback ${state.opsMessageTone}">${state.opsMessage}</div>`
          : ""
      }
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>当前批次 · ${selectedRunDetail.batchName}</strong>
          <div class="section-actions">
            <span class="trace-status ${selectedRunDetail.reviewCount > 0 ? "needs_review" : "resolved"}">
              ${selectedRunDetail.reviewCount > 0 ? `${selectedRunDetail.reviewCount} 条待复核` : "已归一"}
            </span>
            <button
              class="action compact ${postgresReady ? "primary" : ""}"
              data-persist-run-id="${selectedRunDetail.runId}"
              ${postgresReady ? "" : "disabled"}
            >
              ${state.busyPersistRunId === selectedRunDetail.runId ? "写入中..." : "写入 PostgreSQL"}
            </button>
          </div>
        </div>
        <p>${sourceLabelById(selectedRunDetail.providerId)} · ${formatTimestamp(selectedRunDetail.createdAt)} · ${postgresLabel}</p>
        <div class="import-run-grid">
          ${
            (selectedRunDetail.reviewQueue ?? []).length
              ? (selectedRunDetail.reviewQueue ?? [])
                  .slice(0, 3)
                  .map(
                    (item) => `
                      <article
                        class="queue-item is-imported ${item.communityId === selectedCommunityId ? "is-related" : ""}"
                        data-community-id="${item.communityId ?? ""}"
                        data-building-id="${item.buildingId ?? ""}"
                        data-floor-no="${item.floorNo ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${item.buildingNo} · ${item.floorNo ?? "待识别"} 层</strong>
                          <span class="trace-status ${item.status}">${queueStatusLabel(item.status)}</span>
                        </div>
                        <p>${item.normalizedPath}</p>
                        <small>${item.reviewHint}</small>
                        ${
                          item.status !== "resolved"
                            ? `
                              <div class="queue-item-footer">
                                <button
                                  class="action compact"
                                  data-review-run-id="${selectedRunDetail.runId}"
                                  data-review-queue-id="${item.queueId}"
                                >
                                  ${state.busyReviewQueueId === item.queueId ? "回写中..." : "标记已复核"}
                                </button>
                              </div>
                            `
                            : ""
                        }
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这个批次当前没有挂起的地址复核项。</p>"
          }
        </div>
      </article>
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>批次高收益楼层</strong>
          <span class="badge">${(selectedRunDetail.topEvidence ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${(selectedRunDetail.topEvidence ?? [])
            .slice(0, 4)
            .map(
              (item) => `
                <article
                  class="import-run-evidence"
                  data-community-id="${item.communityId ?? ""}"
                  data-building-id="${item.buildingId ?? ""}"
                  data-floor-no="${item.floorNo ?? ""}"
                >
                  <div class="breakdown-top">
                    <strong>${item.communityName} · ${item.buildingName} · ${item.floorNo} 层</strong>
                    <span class="yield-chip ${yieldClass(item.yieldPct ?? 0)}">${Number(item.yieldPct ?? 0).toFixed(2)}%</span>
                  </div>
                  <p>样本对 ${item.pairCount} 组 · 最佳置信 ${Math.round((item.bestPairConfidence ?? 0) * 100)}%</p>
                </article>
              `
            )
            .join("")}
        </div>
      </article>
      ${
        selectedRunDetail.comparison
          ? `
            <article class="import-run-section" data-browser-capture-recent-runs="true">
              <div class="breakdown-top">
                <strong>相对基线批次的变化</strong>
                <span class="badge">${selectedRunDetail.comparison.baselineBatchName}</span>
              </div>
              <div class="field compact">
                <div class="field-header">
                  <span>对比基线</span>
                  <strong>${state.selectedBaselineRunId ? "手动指定" : "自动上一批"}</strong>
                </div>
                <select data-baseline-run-select>
                  <option value="">自动选择上一批</option>
                  ${baselineOptions
                    .map(
                      (item) => `
                        <option value="${item.runId}" ${item.runId === state.selectedBaselineRunId ? "selected" : ""}>
                          ${item.batchName} · ${formatTimestamp(item.createdAt)}
                        </option>
                      `
                    )
                    .join("")}
                </select>
              </div>
              <p>对比基线 · ${selectedRunDetail.comparison.baselineBatchName} · ${formatTimestamp(
                selectedRunDetail.comparison.baselineCreatedAt
              )}</p>
              <div class="comparison-strip">
                <span class="source-pill">归一率 ${formatSignedDelta(selectedRunDetail.comparison.resolvedRateDeltaPct, {
                  suffix: "pt",
                  digits: 1
                })}</span>
                <span class="source-pill">待复核 ${formatSignedDelta(selectedRunDetail.comparison.reviewCountDelta)}</span>
                <span class="source-pill">样本对 ${formatSignedDelta(selectedRunDetail.comparison.pairCountDelta)}</span>
                <span class="source-pill">逐层证据 ${formatSignedDelta(selectedRunDetail.comparison.evidenceCountDelta)}</span>
                <span class="source-pill">新增楼层 ${selectedRunDetail.comparison.newFloorCount}</span>
                <span class="source-pill">平均回报 ${formatSignedDelta(selectedRunDetail.comparison.avgYieldDeltaPct, {
                  suffix: "%",
                  digits: 2
                })}</span>
              </div>
              <div class="import-run-grid">
                ${(selectedRunDetail.comparison.topFloorChanges ?? [])
                  .map(
                    (item) => `
                      <article
                        class="import-run-evidence"
                        data-community-id="${item.communityId ?? ""}"
                        data-building-id="${item.buildingId ?? ""}"
                        data-floor-no="${item.floorNo ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${item.communityName} · ${item.buildingName} · ${item.floorNo} 层</strong>
                          <span class="trace-status ${comparisonToneClass(item.status)}">${item.statusLabel}</span>
                        </div>
                        <p>
                          当前 ${Number(item.currentYieldPct ?? 0).toFixed(2)}%
                          ${
                            item.previousYieldPct !== null && item.previousYieldPct !== undefined
                              ? ` · 上批 ${Number(item.previousYieldPct).toFixed(2)}%`
                              : " · 上批无同层样本"
                          }
                        </p>
                        <small>
                          回报 ${formatSignedDelta(item.yieldDelta, { suffix: "%", digits: 2 })} ·
                          样本对 ${formatSignedDelta(item.pairCountDelta)} ·
                          售价 ${formatSignedDelta(item.saleMedianDeltaWan, { suffix: "万", digits: 1 })} ·
                          租金 ${formatSignedDelta(item.rentMedianDeltaMonthly, { suffix: "元", digits: 0 })}
                        </small>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            </article>
          `
          : ""
      }
      <article class="import-run-section">
        <div class="breakdown-top">
          <strong>最近复核记录</strong>
          <span class="badge">${selectedRunDetail.reviewHistoryCount ?? (selectedRunDetail.recentReviews ?? []).length}</span>
        </div>
        <div class="import-run-grid">
          ${
            (selectedRunDetail.recentReviews ?? []).length
              ? (selectedRunDetail.recentReviews ?? [])
                  .map(
                    (item) => `
                      <article
                        class="import-run-evidence"
                        data-community-id="${item.communityId ?? ""}"
                        data-building-id="${item.buildingId ?? ""}"
                        data-floor-no="${item.floorNo ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${item.communityName} · ${item.buildingName} · ${item.floorNo ?? "待识别"} 层</strong>
                          <span class="trace-status ${item.newStatus}">${queueStatusLabel(item.newStatus)}</span>
                        </div>
                        <p>${item.previousStatus && item.previousStatus !== "unknown" ? `${queueStatusLabel(item.previousStatus)} → ` : ""}${queueStatusLabel(item.newStatus)} · ${item.reviewOwner} · ${formatTimestamp(item.reviewedAt)}</p>
                        <small>${item.resolutionNotes}</small>
                      </article>
                    `
                  )
                  .join("")
              : "<p class=\"helper-text\">这个批次暂时还没有复核历史。</p>"
          }
        </div>
      </article>
    `
    : "<p class=\"helper-text\">选择一个导入批次后，这里会展示待复核条目和高收益逐层证据。</p>";

  sourceHealthList.innerHTML = sourceHealth
    .map(
      (item) => `
        <article class="source-item">
          <div class="breakdown-top">
            <strong>${item.name}</strong>
            <span class="trace-status ${item.connectionState ?? item.status}">${item.readinessLabel ?? sourceStatusLabel(item.status)}</span>
          </div>
          <p>${item.note}</p>
          <div class="source-meta">
            <span class="source-pill">${item.category}</span>
            <span class="source-pill">priority ${item.priority}</span>
            <span class="source-pill">staging ${item.stagedRunCount ?? 0}</span>
            ${item.applicationMode ? `<span class="source-pill">${providerModeLabel(item.applicationMode)}</span>` : ""}
          </div>
          ${item.recommendedNextStep ? `<p class="source-hint">${item.recommendedNextStep}</p>` : ""}
          ${item.contactValue ? `<small>${item.contactLabel ?? "联系"} · ${item.contactValue}</small>` : ""}
          <small>${item.supportsLivePull ? "后续可切在线 adapter" : "本阶段以离线 / staging 接入为主"}</small>
          ${renderProviderActions(item, { compact: true })}
        </article>
      `
    )
    .join("");

  const selectedSamplingTask = currentBrowserSamplingTask();
  const selectedCaptureRunDetail = currentBrowserCaptureRun();
  const currentCaptureSubmission = currentBrowserCaptureSubmission();
  const currentReviewAction = currentBrowserCaptureReviewAction();
  const pendingReviewItems = (selectedCaptureRunDetail?.reviewQueue ?? []).filter((item) => String(item?.status ?? "pending") === "pending");
  const selectedReviewQueueIds = currentBrowserCaptureReviewBatchSelection(selectedCaptureRunDetail?.reviewQueue ?? []);
  const reviewHistoryItems = (selectedCaptureRunDetail?.reviewQueue ?? []).filter((item) => String(item?.status ?? "pending") !== "pending");
  const taskCaptureRuns = selectedSamplingTask
    ? getBrowserCaptureRunItems(4, {
        taskId: selectedSamplingTask.taskId,
        districtId: state.districtFilter
      })
    : [];
  const recentCaptureRuns = getBrowserCaptureRunItems(6, {
    districtId: state.districtFilter
  });
  const browserSamplingCoverage = browserSamplingCoveragePayload();
  const workbenchQueue = getBrowserSamplingWorkbenchQueue(selectedSamplingTask);
  const reviewInboxQueue = getBrowserReviewInboxQueue(selectedSamplingTask);
  const reviewInboxSummary = state.browserReviewInboxSummary ?? browserReviewInboxSummaryFallback();
  const currentReviewInboxItemId = currentBrowserReviewInboxItemId();
  const reviewBatchBusy = state.busyBrowserCaptureReviewBatch || Boolean(state.busyBrowserCaptureReviewQueueId);

  browserSamplingWorkbench.innerHTML = selectedSamplingTask
    ? `
      ${
        state.opsMessage && state.opsMessageContext === "sampling"
          ? `<div class="ops-feedback ${state.opsMessageTone}">${state.opsMessage}</div>`
          : ""
      }
      <article
        class="import-run-section browser-capture-panel"
        data-browser-capture-panel="${selectedSamplingTask.taskId}"
        data-browser-capture-task-id="${selectedSamplingTask.taskId}"
        data-browser-capture-community-name="${escapeHtml(selectedSamplingTask.communityName ?? "")}"
        data-browser-capture-building-name="${escapeHtml(selectedSamplingTask.buildingName ?? "")}"
        data-browser-capture-floor-no="${selectedSamplingTask.floorNo ?? ""}"
        data-browser-capture-district-name="${escapeHtml(selectedSamplingTask.districtName ?? "")}"
      >
        <div class="capture-workbench-hero">
          <div class="capture-workbench-copy">
            <div class="breakdown-top">
              <strong>公开页面采样执行台</strong>
              <span class="badge">${selectedSamplingTask.taskTypeLabel}</span>
            </div>
            <p class="capture-task-label" data-browser-capture-task-label="true">${selectedSamplingTask.communityName}${selectedSamplingTask.buildingName ? ` · ${selectedSamplingTask.buildingName}` : ""}${selectedSamplingTask.floorNo != null ? ` · ${selectedSamplingTask.floorNo}层` : ""} · ${selectedSamplingTask.districtName}</p>
            <small class="capture-task-brief">${selectedSamplingTask.reason} ${selectedSamplingTask.captureGoal}</small>
          </div>
          <div class="capture-workbench-kpis">
            <article class="capture-kpi">
              <span>优先级</span>
              <strong>${selectedSamplingTask.priorityLabel}</strong>
              <small>${selectedSamplingTask.focusScope === "priority" ? "重点区任务" : "全市任务"}</small>
            </article>
            <article class="capture-kpi">
              <span>当前样本</span>
              <strong>${
                selectedSamplingTask.targetGranularity === "floor"
                  ? `${selectedSamplingTask.currentPairCount ?? 0}/${selectedSamplingTask.targetPairCount ?? 0}`
                  : `${selectedSamplingTask.currentSampleSize ?? 0}/${selectedSamplingTask.targetSampleSize ?? 0}`
              }</strong>
              <small>${selectedSamplingTask.targetGranularity === "floor" ? "样本对" : "聚合样本"}</small>
            </article>
            <article class="capture-kpi">
              <span>当前收益</span>
              <strong>${
                selectedSamplingTask.currentYieldPct != null
                  ? `${Number(selectedSamplingTask.currentYieldPct).toFixed(2)}%`
                  : "待补"
              }</strong>
              <small>${selectedSamplingTask.sampleStatusLabel ?? "状态待补"}</small>
            </article>
          </div>
        </div>
        <div class="comparison-strip capture-meta-strip">
          <span class="source-pill">${selectedSamplingTask.priorityLabel}</span>
          <span class="source-pill">${selectedSamplingTask.focusScope === "priority" ? "重点区任务" : "全市任务"}</span>
          <span class="source-pill">${selectedSamplingTask.sampleStatusLabel ?? "状态待补"}</span>
          ${
            selectedSamplingTask.currentYieldPct != null
              ? `<span class="source-pill">当前 ${Number(selectedSamplingTask.currentYieldPct).toFixed(2)}%</span>`
              : ""
          }
          ${
            selectedSamplingTask.targetGranularity === "floor"
              ? `<span class="source-pill">样本对 ${selectedSamplingTask.currentPairCount ?? 0}/${selectedSamplingTask.targetPairCount ?? 0}</span>`
              : `<span class="source-pill">样本 ${selectedSamplingTask.currentSampleSize ?? 0}/${selectedSamplingTask.targetSampleSize ?? 0}</span>`
          }
        </div>
        ${
          currentCaptureSubmission
            ? `
              <article
                class="ops-feedback success browser-capture-result browser-post-submit-relay"
                data-browser-capture-result="success"
                data-browser-capture-result-task-id="${currentCaptureSubmission.taskId}"
                data-browser-capture-result-import-run-id="${currentCaptureSubmission.importRunId ?? ""}"
                data-browser-capture-result-capture-run-id="${currentCaptureSubmission.captureRunId ?? ""}"
                data-browser-capture-result-metrics-run-id="${currentCaptureSubmission.metricsRunId ?? ""}"
                data-browser-capture-result-created-at="${currentCaptureSubmission.createdAt ?? ""}"
                data-browser-capture-result-attention-count="${currentCaptureSubmission.attentionCount ?? 0}"
                data-browser-post-submit-action="${currentCaptureSubmission.workflowAction ?? "stay_current"}"
                data-browser-post-submit-task-id="${currentCaptureSubmission.postSubmitTaskId ?? currentCaptureSubmission.taskId ?? ""}"
                data-browser-post-submit-workflow-task-id="${currentCaptureSubmission.workflowTaskId ?? ""}"
                data-browser-post-submit-workflow-task-provided="${currentCaptureSubmission.workflowTaskProvided ? "true" : "false"}"
                data-browser-post-submit-resolution="${currentCaptureSubmission.postSubmitTaskResolution ?? ""}"
                data-browser-post-submit-attention-count="${currentCaptureSubmission.attentionCount ?? 0}"
                data-browser-post-submit-source-task-id="${currentCaptureSubmission.taskId ?? ""}"
                data-browser-post-submit-reason="${currentCaptureSubmission.workflowReason ?? ""}"
                data-browser-post-submit-status="${currentCaptureSubmission.taskProgress?.status ?? ""}"
              >
                <div class="breakdown-top">
                  <strong>采样接力条</strong>
                  <span class="badge">${browserSamplingWorkflowActionLabel(currentCaptureSubmission.workflowAction)}</span>
                </div>
                <p>
                  已写入 ${currentCaptureSubmission.taskLabel ?? "当前任务"} ·
                  ${currentCaptureSubmission.importRunId ?? currentCaptureSubmission.captureRunId ?? "已提交"}
                  ${currentCaptureSubmission.metricsRunId ? ` · metrics ${currentCaptureSubmission.metricsRunId}` : ""}
                  ${currentCaptureSubmission.attentionCount ? ` · raw attention ${currentCaptureSubmission.attentionCount}` : " · raw attention 0"}
                </p>
                <div class="comparison-strip">
                  <span class="source-pill">${browserSamplingProgressLabel(currentCaptureSubmission.taskProgress)}</span>
                  <span class="source-pill">${browserSamplingTaskStatusLabel(currentCaptureSubmission.taskProgress?.status)}</span>
                  <span class="source-pill">待复核 ${currentCaptureSubmission.reviewPendingCount ?? 0}</span>
                  <span class="source-pill">收件箱 ${currentCaptureSubmission.reviewInboxPendingCount ?? reviewInboxSummary.pendingQueueCount ?? 0}</span>
                  <span class="source-pill">当前接力 ${currentCaptureSubmission.postSubmitTaskLabel ?? currentCaptureSubmission.taskLabel ?? "当前任务"}</span>
                  <span class="source-pill">${browserSamplingPostSubmitResolutionLabel(currentCaptureSubmission.postSubmitTaskResolution)}</span>
                  ${
                    (currentCaptureSubmission.autoFilledChannels ?? []).length
                      ? `<span class="source-pill">已预填 ${(currentCaptureSubmission.autoFilledChannels ?? [])
                          .map((channel) => (channel === "rent" ? "Rent" : "Sale"))
                          .join(" / ")}</span>`
                      : ""
                  }
                </div>
                <small>${browserSamplingWorkflowReasonLabel(currentCaptureSubmission.workflowReason)}</small>
              </article>
            `
            : ""
        }
        ${
          currentReviewAction
            ? `
              <article
                class="ops-feedback success browser-capture-result browser-post-submit-relay browser-review-relay"
                data-browser-review-action="${currentReviewAction.action ?? "stay_current"}"
                data-browser-review-run-id="${currentReviewAction.runId ?? ""}"
                data-browser-review-queue-id="${currentReviewAction.queueId ?? ""}"
                data-browser-review-workflow-run-id="${currentReviewAction.workflowRunId ?? ""}"
                data-browser-review-workflow-queue-id="${currentReviewAction.workflowQueueId ?? ""}"
                data-browser-review-workflow-task-id="${currentReviewAction.workflowTaskId ?? ""}"
                data-browser-review-workflow-item-provided="${currentReviewAction.workflowItemProvided ? "true" : "false"}"
                data-browser-review-resolution="${currentReviewAction.reviewResolution ?? ""}"
                data-browser-review-reason="${currentReviewAction.reason ?? ""}"
                data-browser-review-target-task-id="${currentReviewAction.postReviewTaskId ?? ""}"
                data-browser-review-target-run-id="${currentReviewAction.postReviewRunId ?? ""}"
                data-browser-review-target-queue-id="${currentReviewAction.postReviewQueueId ?? ""}"
                data-browser-review-pending-count="${currentReviewAction.pendingCount ?? 0}"
                data-browser-review-batch-affected-count="${currentReviewAction.reviewMode === "batch" ? currentReviewAction.affectedCount ?? 0 : 0}"
                data-browser-review-batch-skipped-count="${currentReviewAction.reviewMode === "batch" ? currentReviewAction.skippedCount ?? 0 : 0}"
                data-browser-review-batch-status="${currentReviewAction.reviewMode === "batch" ? currentReviewAction.reviewStatus ?? "" : ""}"
              >
                <div class="breakdown-top">
                  <strong>复核接力条</strong>
                  <span class="badge">${browserCaptureReviewActionLabel(currentReviewAction.action)}</span>
                </div>
                <p>
                  ${currentReviewAction.reviewMode === "batch" ? "已批量处理" : "已处理"} ${currentReviewAction.taskLabel ?? "当前任务"} ·
                  ${browserCaptureReviewStatusLabel(currentReviewAction.reviewStatus)} ·
                  run ${currentReviewAction.runId}
                </p>
                <div class="comparison-strip">
                  ${
                    currentReviewAction.reviewMode === "batch"
                      ? `<span class="source-pill">选中 ${currentReviewAction.selectedCount ?? 0}</span>
                         <span class="source-pill">成功 ${currentReviewAction.affectedCount ?? 0}</span>
                         <span class="source-pill">跳过 ${currentReviewAction.skippedCount ?? 0}</span>`
                      : `<span class="source-pill">队列 ${currentReviewAction.queueId ?? "待补"}</span>`
                  }
                  <span class="source-pill">剩余待复核 ${currentReviewAction.pendingCount ?? 0}</span>
                  <span class="source-pill">收件箱 ${currentReviewAction.reviewInboxPendingCount ?? reviewInboxSummary.pendingQueueCount ?? 0}</span>
                  <span class="source-pill">当前接力 ${currentReviewAction.postReviewTaskLabel ?? currentReviewAction.taskLabel ?? "当前任务"}</span>
                  <span class="source-pill">${browserCaptureReviewResolutionLabel(currentReviewAction.reviewResolution)}</span>
                </div>
                <small>${browserCaptureReviewReasonLabel(currentReviewAction.reason)}</small>
              </article>
            `
            : ""
        }
        <div class="comparison-strip">
          ${(selectedSamplingTask.requiredFields ?? []).map((field) => `<span class="source-pill">${field}</span>`).join("")}
        </div>
        <div class="comparison-strip">
          <span class="trace-status ${selectedSamplingTask.taskLifecycleStatus ?? "needs_capture"}">${selectedSamplingTask.taskLifecycleLabel ?? "待采样"}</span>
          <span class="source-pill">历史采样 ${selectedSamplingTask.captureHistoryCount ?? 0} 次</span>
          ${
            selectedSamplingTask.latestCaptureAt
              ? `<span class="source-pill">最近 ${formatTimestamp(selectedSamplingTask.latestCaptureAt)}</span>`
              : `<span class="source-pill">还没有公开页原文</span>`
          }
          ${
            browserCapturePendingAttentionCount(selectedSamplingTask)
              ? `<span class="source-pill">待复核 ${browserCapturePendingAttentionCount(selectedSamplingTask)}</span>`
              : selectedSamplingTask.latestCaptureAttentionCount
                ? `<span class="source-pill">raw attention ${selectedSamplingTask.latestCaptureAttentionCount}</span>`
              : ""
          }
        </div>
        <div class="capture-workbench-layout">
          <div class="capture-form-column">
            <article
              class="import-run-section browser-task-queue-panel browser-review-inbox-panel"
              data-browser-review-inbox-count="${reviewInboxSummary.pendingQueueCount ?? 0}"
            >
              <div class="breakdown-top">
                <strong>全局待复核收件箱</strong>
                <span class="badge">${reviewInboxQueue.previewItems.length}</span>
              </div>
              <div class="comparison-strip">
                <span class="source-pill">当前区 ${reviewInboxQueue.districtItems.length}</span>
                <span class="source-pill">全局 ${reviewInboxSummary.pendingQueueCount ?? 0}</span>
                <span class="source-pill">任务 ${reviewInboxSummary.pendingTaskCount ?? 0}</span>
              </div>
              ${
                reviewInboxQueue.previewItems.length
                  ? `
                    <div class="browser-task-queue">
                      ${reviewInboxQueue.previewItems
                        .map(
                          (item) => `
                            <article
                              class="browser-task-queue-item browser-review-inbox-item ${item.inboxItemId === currentReviewInboxItemId ? "is-active" : ""}"
                              data-browser-review-inbox-item-id="${item.inboxItemId}"
                              data-browser-review-inbox-run-id="${item.runId}"
                              data-browser-review-inbox-queue-id="${item.queueId}"
                              data-browser-review-inbox-task-id="${item.taskId ?? ""}"
                            >
                              <div class="breakdown-top">
                                <strong>${item.taskLabel ?? browserSamplingTaskLabel(item)}</strong>
                                <span class="trace-status needs_review">${item.businessTypeLabel ?? item.businessType ?? "原文"} · ${(item.attention ?? []).length} 项</span>
                              </div>
                              <p>${item.districtName ?? "未知行政区"} · run ${item.runId} · ${item.sourceListingId ?? "待补"}</p>
                              <small>${(item.attention ?? []).join(" / ") || "待复核 attention"}${item.publishedAt ? ` · ${item.publishedAt}` : ""}</small>
                            </article>
                          `
                        )
                        .join("")}
                    </div>
                  `
                  : `<p class="helper-text">${
                      reviewInboxSummary.pendingQueueCount
                        ? "当前区没有待复核条目，系统会在需要时自动退到全局收件箱。"
                        : "当前没有待复核条目，可以继续补样。"
                    }</p>`
              }
            </article>
            <article class="import-run-section browser-task-queue-panel">
              <div class="breakdown-top">
                <strong>连续补样快捷台</strong>
                <span class="badge">${workbenchQueue.previewTasks.length}</span>
              </div>
              <div class="comparison-strip">
                <span class="source-pill">同区待办 ${workbenchQueue.districtTasks.length}</span>
                <span class="source-pill">待复核 ${workbenchQueue.reviewDistrictCount}</span>
                <span class="source-pill">待采样/补采 ${workbenchQueue.districtTasks.filter((task) => ["needs_capture", "in_progress"].includes(browserSamplingCoverageState(task))).length}</span>
              </div>
              <div class="action-row compact browser-task-actions">
                <button class="action compact" data-browser-workbench-copy-brief="${selectedSamplingTask.taskId}">复制整包采样指令</button>
                <button class="action compact" data-browser-workbench-next-district="${workbenchQueue.nextDistrictTask?.taskId ?? ""}" ${workbenchQueue.nextDistrictTask ? "" : "disabled"}>下一个同区任务</button>
                <button class="action compact" data-browser-workbench-next-review="${workbenchQueue.nextReviewTask?.taskId ?? ""}" data-browser-workbench-next-review-run-id="${workbenchQueue.nextReviewItem?.runId ?? ""}" data-browser-workbench-next-review-queue-id="${workbenchQueue.nextReviewItem?.queueId ?? ""}" ${workbenchQueue.nextReviewTask ? "" : "disabled"}>下一个待复核</button>
                <button class="action compact" data-browser-workbench-next-capture="${workbenchQueue.nextCaptureTask?.taskId ?? ""}" ${workbenchQueue.nextCaptureTask ? "" : "disabled"}>下一个待采样</button>
              </div>
              ${
                workbenchQueue.previewTasks.length
                  ? `
                    <div class="browser-task-queue">
                      ${workbenchQueue.previewTasks
                        .map(
                          (task) => `
                            <article class="browser-task-queue-item ${task.taskId === state.selectedBrowserSamplingTaskId ? "is-active" : ""}" data-browser-workbench-task-id="${task.taskId}">
                              <div class="breakdown-top">
                                <strong>${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}${task.floorNo != null ? ` · ${task.floorNo}层` : ""}</strong>
                                <span class="trace-status ${browserSamplingCoverageState(task)}">${browserSamplingCoverageLabel(task)}</span>
                              </div>
                              <p>${task.districtName ?? "未知行政区"} · ${task.taskTypeLabel ?? task.taskType ?? "公开页采样"} · ${task.captureGoal ?? task.reason ?? "等待补齐公开页原文。"}</p>
                              <small>${browserSamplingCountSummary(task)} · 优先分 ${task.priorityScore ?? 0}</small>
                            </article>
                          `
                        )
                        .join("")}
                    </div>
                  `
                  : `<p class="helper-text">当前区内没有其他待办采样任务，继续补当前对象就好。</p>`
              }
            </article>
            <div class="action-row compact browser-task-actions capture-query-row">
              <button class="action compact" data-browser-workbench-copy-sale="${selectedSamplingTask.taskId}">复制 Sale 检索词</button>
              <button class="action compact" data-browser-workbench-copy-rent="${selectedSamplingTask.taskId}">复制 Rent 检索词</button>
              <button class="action compact" data-browser-workbench-copy-target="${selectedSamplingTask.taskId}">复制目标检索词</button>
            </div>
            <div class="browser-capture-grid">
          <article class="browser-capture-card">
            <div class="breakdown-top">
              <strong>Sale 原文</strong>
              <span class="trace-status resolved">出售</span>
            </div>
            <label class="field compact">
              <div class="field-header">
                <span>source_listing_id</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.sale.sourceListingId)}" data-browser-capture-field="sourceListingId" data-browser-capture-channel="sale" data-browser-capture-input="sale-sourceListingId" placeholder="例如 sale-20260414-001" />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>页面 URL</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.sale.url)}" data-browser-capture-field="url" data-browser-capture-channel="sale" data-browser-capture-input="sale-url" placeholder="https://..." />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>发布时间</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.sale.publishedAt)}" data-browser-capture-field="publishedAt" data-browser-capture-channel="sale" data-browser-capture-input="sale-publishedAt" placeholder="2026-04-14 12:30:00" />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>原文摘录</span>
                <strong>必填</strong>
              </div>
              <textarea data-browser-capture-field="rawText" data-browser-capture-channel="sale" data-browser-capture-input="sale-rawText" placeholder="把公开 sale 页面里包含楼栋、楼层、面积、户型、总价等文字直接贴进来。">${escapeHtml(state.browserCaptureDraft.sale.rawText)}</textarea>
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>备注</span>
                <strong>可选</strong>
              </div>
              <textarea data-browser-capture-field="note" data-browser-capture-channel="sale" data-browser-capture-input="sale-note" placeholder="例如：页面里写的是低楼层，楼栋文本来自标题。">${escapeHtml(state.browserCaptureDraft.sale.note)}</textarea>
            </label>
          </article>
          <article class="browser-capture-card">
            <div class="breakdown-top">
              <strong>Rent 原文</strong>
              <span class="trace-status high">出租</span>
            </div>
            <label class="field compact">
              <div class="field-header">
                <span>source_listing_id</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.rent.sourceListingId)}" data-browser-capture-field="sourceListingId" data-browser-capture-channel="rent" data-browser-capture-input="rent-sourceListingId" placeholder="例如 rent-20260414-001" />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>页面 URL</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.rent.url)}" data-browser-capture-field="url" data-browser-capture-channel="rent" data-browser-capture-input="rent-url" placeholder="https://..." />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>发布时间</span>
                <strong>必填</strong>
              </div>
              <input type="text" value="${escapeHtml(state.browserCaptureDraft.rent.publishedAt)}" data-browser-capture-field="publishedAt" data-browser-capture-channel="rent" data-browser-capture-input="rent-publishedAt" placeholder="2026-04-14 12:30:00" />
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>原文摘录</span>
                <strong>必填</strong>
              </div>
              <textarea data-browser-capture-field="rawText" data-browser-capture-channel="rent" data-browser-capture-input="rent-rawText" placeholder="把公开 rent 页面里包含楼栋、楼层、面积、户型、月租等文字直接贴进来。">${escapeHtml(state.browserCaptureDraft.rent.rawText)}</textarea>
            </label>
            <label class="field compact">
              <div class="field-header">
                <span>备注</span>
                <strong>可选</strong>
              </div>
              <textarea data-browser-capture-field="note" data-browser-capture-channel="rent" data-browser-capture-input="rent-note" placeholder="例如：月租来自详情页，朝向在副标题里。">${escapeHtml(state.browserCaptureDraft.rent.note)}</textarea>
            </label>
          </article>
            </div>
            <div class="queue-item-footer browser-capture-footer">
              <button class="action compact" data-browser-capture-reset="${selectedSamplingTask.taskId}" data-browser-capture-reset-button="${selectedSamplingTask.taskId}" ${state.busyBrowserSamplingSubmit ? "disabled" : ""}>清空草稿</button>
              <button class="action compact primary" data-browser-capture-submit="${selectedSamplingTask.taskId}" data-browser-capture-submit-button="${selectedSamplingTask.taskId}" ${state.busyBrowserSamplingSubmit ? "disabled" : ""}>
                ${state.busyBrowserSamplingSubmit ? "导入中..." : "生成采样批次并刷新"}
              </button>
            </div>
          </div>
          <div class="capture-side-column">
            <article class="import-run-section" data-browser-capture-current-task-runs="true">
          <div class="breakdown-top">
            <strong>当前任务最近采样</strong>
            <span class="badge">${taskCaptureRuns.length}</span>
          </div>
          <div class="import-run-grid">
            ${
              taskCaptureRuns.length
                ? taskCaptureRuns
                    .map(
                      (run) => `
                        <article class="import-run-evidence ${selectedCaptureRunDetail?.runId === run.runId ? "is-related" : ""}" data-browser-capture-run-id="${run.runId}" data-browser-capture-import-run-id="${run.importRunId ?? ""}" data-browser-capture-metrics-run-id="${run.metricsRunId ?? ""}" data-community-id="${run.communityId ?? ""}" data-building-id="${run.buildingId ?? ""}" data-floor-no="${run.floorNo ?? ""}">
                          <div class="breakdown-top">
                            <strong>${run.communityName}${run.buildingName ? ` · ${run.buildingName}` : ""}${run.floorNo != null ? ` · ${run.floorNo}层` : ""}</strong>
                            <span class="trace-status ${browserCapturePendingAttentionCount(run) ? "needs_review" : "captured"}">${browserCapturePendingAttentionCount(run) ? "待复核" : "已导入"}</span>
                          </div>
                          <p>${formatTimestamp(run.createdAt)} · 原文 ${run.captureCount} 条 · Sale ${run.saleCaptureCount} / Rent ${run.rentCaptureCount}</p>
                          <small>${
                            browserCapturePendingAttentionCount(run)
                              ? `待复核 ${browserCapturePendingAttentionCount(run)} 条 · 已修正 ${browserCaptureResolvedCount(run)} · 已豁免 ${browserCaptureWaivedCount(run)}`
                              : run.attentionCount
                                ? `raw attention ${run.attentionCount} 条已闭环`
                              : `已并入 ${run.importRunId ?? "最新 import run"} · metrics ${run.metricsRunId ?? "待刷新"}`
                          }</small>
                        </article>
                      `
                    )
                    .join("")
                : "<p class=\"helper-text\">当前任务还没有浏览器采样历史，第一次提交后这里会出现最近几次采样记录。</p>"
            }
          </div>
            </article>
            <article class="import-run-section" data-browser-capture-recent-runs="true">
          <div class="breakdown-top">
            <strong>最近公开页采样批次</strong>
            <span class="badge">${recentCaptureRuns.length}</span>
          </div>
          <div class="import-run-grid">
            ${
              recentCaptureRuns.length
                ? recentCaptureRuns
                    .map(
                      (run) => `
                        <article class="import-run-evidence ${selectedCaptureRunDetail?.runId === run.runId ? "is-related" : ""}" data-browser-capture-run-id="${run.runId}" data-browser-capture-import-run-id="${run.importRunId ?? ""}" data-browser-capture-metrics-run-id="${run.metricsRunId ?? ""}" data-browser-task-id="${run.taskId ?? ""}" data-community-id="${run.communityId ?? ""}" data-building-id="${run.buildingId ?? ""}" data-floor-no="${run.floorNo ?? ""}">
                          <div class="breakdown-top">
                            <strong>${run.communityName}${run.buildingName ? ` · ${run.buildingName}` : ""}${run.floorNo != null ? ` · ${run.floorNo}层` : ""}</strong>
                            <span class="trace-status ${browserCapturePendingAttentionCount(run) ? "needs_review" : "captured"}">${browserCapturePendingAttentionCount(run) ? "待复核" : "已采完成"}</span>
                          </div>
                          <p>${formatTimestamp(run.createdAt)} · ${run.taskTypeLabel ?? "公开页采样"} · ${run.captureCount} 条原文</p>
                          <small>${
                            browserCapturePendingAttentionCount(run)
                              ? `待复核 ${browserCapturePendingAttentionCount(run)} 条`
                              : run.attentionCount
                                ? `raw attention ${run.attentionCount} 条已闭环`
                              : `导入 ${run.importRunId ?? "latest"} · metrics ${run.metricsRunId ?? "latest"}`
                          }</small>
                        </article>
                      `
                    )
                    .join("")
                : "<p class=\"helper-text\">当前还没有公开页采样批次历史。</p>"
            }
          </div>
            </article>
            <article
              class="import-run-section"
              data-browser-capture-attention-panel="true"
              data-browser-capture-attention-run-id="${selectedCaptureRunDetail?.runId ?? ""}"
              data-browser-capture-attention-count="${browserCapturePendingAttentionCount(selectedCaptureRunDetail)}"
              data-browser-review-current-run-id="${selectedCaptureRunDetail?.runId ?? ""}"
              data-browser-review-current-pending-count="${browserCapturePendingAttentionCount(selectedCaptureRunDetail)}"
            >
          <div class="breakdown-top">
            <strong>review queue 回看面板</strong>
            <span class="badge">${
              state.busyBrowserCaptureRunId
                ? "加载中"
                : selectedCaptureRunDetail?.runId
                  ? `${browserCapturePendingAttentionCount(selectedCaptureRunDetail)} 条待处理`
                  : "未选中"
            }</span>
          </div>
          ${
            state.busyBrowserCaptureRunId
              ? `<p class="helper-text">正在加载采样批次详情…</p>`
              : selectedCaptureRunDetail?.runId
                ? `
                  <p>${selectedCaptureRunDetail.communityName}${selectedCaptureRunDetail.buildingName ? ` · ${selectedCaptureRunDetail.buildingName}` : ""}${selectedCaptureRunDetail.floorNo != null ? ` · ${selectedCaptureRunDetail.floorNo}层` : ""} · ${formatTimestamp(selectedCaptureRunDetail.createdAt)}</p>
                  <small>原文 ${selectedCaptureRunDetail.captureCount ?? 0} 条 · raw attention ${selectedCaptureRunDetail.attentionCount ?? 0} 条 · 待处理 ${browserCapturePendingAttentionCount(selectedCaptureRunDetail)} 条 · 已修正 ${browserCaptureResolvedCount(selectedCaptureRunDetail)} 条 · 已豁免 ${browserCaptureWaivedCount(selectedCaptureRunDetail)} 条${browserCaptureSupersededCount(selectedCaptureRunDetail) ? ` · 已接力 ${browserCaptureSupersededCount(selectedCaptureRunDetail)} 条` : ""}${selectedCaptureRunDetail.importRunId ? ` · import ${selectedCaptureRunDetail.importRunId}` : ""}${selectedCaptureRunDetail.metricsRunId ? ` · metrics ${selectedCaptureRunDetail.metricsRunId}` : ""}</small>
                  <div
                    class="action-row compact browser-task-actions browser-review-batch-toolbar"
                    data-browser-review-batch-selected-count="${selectedReviewQueueIds.length}"
                  >
                    <span class="source-pill">已选 ${selectedReviewQueueIds.length}</span>
                    <span class="source-pill">pending ${pendingReviewItems.length}</span>
                    <button class="action compact" data-browser-capture-review-select-all="${selectedCaptureRunDetail.runId}" ${pendingReviewItems.length && !reviewBatchBusy ? "" : "disabled"}>全选当前 pending</button>
                    <button class="action compact" data-browser-capture-review-clear-selection="${selectedCaptureRunDetail.runId}" ${selectedReviewQueueIds.length && !reviewBatchBusy ? "" : "disabled"}>清空选择</button>
                    <button class="action compact" data-browser-capture-review-batch-resolve="${selectedCaptureRunDetail.runId}" ${selectedReviewQueueIds.length && !reviewBatchBusy ? "" : "disabled"}>批量标记已修正</button>
                    <button class="action compact" data-browser-capture-review-batch-waive="${selectedCaptureRunDetail.runId}" ${selectedReviewQueueIds.length && !reviewBatchBusy ? "" : "disabled"}>批量豁免并留痕</button>
                  </div>
                  <div class="import-run-grid">
                    ${
                      pendingReviewItems.length
                        ? pendingReviewItems
                            .map(
                              (item) => `
                                <article class="import-run-evidence ${item.queueId === state.selectedBrowserCaptureReviewQueueId ? "is-related" : ""}" data-browser-capture-review-queue-item="${item.queueId}">
                                  <div class="breakdown-top">
                                    <div class="browser-review-item-heading">
                                      <label class="browser-review-select">
                                        <input type="checkbox" data-browser-capture-review-select="${item.queueId}" ${selectedReviewQueueIds.includes(item.queueId) ? "checked" : ""} ${reviewBatchBusy ? "disabled" : ""} />
                                        <span>${item.businessTypeLabel} · ${item.sourceListingId}</span>
                                      </label>
                                    </div>
                                    <span class="trace-status needs_review">${(item.attention ?? []).length} 项缺失</span>
                                  </div>
                                  <p>${(item.attention ?? []).join(" / ")}</p>
                                  <small>
                                    ${item.buildingText ? `楼栋 ${item.buildingText}` : "楼栋待补"} ·
                                    ${item.floorText ? `楼层 ${item.floorText}` : "楼层待补"} ·
                                    ${item.totalFloors ? `总层数 ${item.totalFloors}` : "总层数待补"} ·
                                    ${item.areaSqm ? `面积 ${item.areaSqm}` : "面积可选"}
                                  </small>
                                  <div class="comparison-strip">
                                    ${item.url ? `<span class="source-pill">${truncate(item.url, 52)}</span>` : ""}
                                    ${item.publishedAt ? `<span class="source-pill">${item.publishedAt}</span>` : ""}
                                    <span class="source-pill">${browserCaptureReviewStatusLabel(item.status)}</span>
                                  </div>
                                  <div class="action-row compact">
                                    <button class="action compact" data-browser-capture-fill-from-attention="${item.queueId}">回填到${item.businessTypeLabel}草稿</button>
                                    <button class="action compact" data-browser-capture-review-resolve="${item.queueId}" ${reviewBatchBusy || state.busyBrowserCaptureReviewQueueId === item.queueId ? "disabled" : ""}>${state.busyBrowserCaptureReviewQueueId === item.queueId ? "处理中..." : "标记已修正"}</button>
                                    <button class="action compact" data-browser-capture-review-waive="${item.queueId}" ${reviewBatchBusy || state.busyBrowserCaptureReviewQueueId === item.queueId ? "disabled" : ""}>豁免并留痕</button>
                                    ${item.rawText ? `<button class="action compact" data-browser-capture-copy-raw="${item.queueId}">复制原文</button>` : ""}
                                  </div>
                                </article>
                              `
                            )
                            .join("")
                        : "<p class=\"helper-text\">当前批次没有待处理 review queue，可继续接力到下一条待复核任务。</p>"
                    }
                  </div>
                  ${
                    reviewHistoryItems.length
                      ? `
                        <details class="browser-review-history">
                          <summary>已处理历史 ${reviewHistoryItems.length} 条</summary>
                          <div class="import-run-grid browser-review-history-grid">
                            ${reviewHistoryItems
                              .map(
                                (item) => `
                                  <article class="import-run-evidence">
                                    <div class="breakdown-top">
                                      <strong>${item.businessTypeLabel} · ${item.sourceListingId}</strong>
                                      <span class="trace-status ${item.status === "resolved" ? "resolved" : item.status === "waived" ? "medium" : "captured"}">${browserCaptureReviewStatusLabel(item.status)}</span>
                                    </div>
                                    <p>${(item.attention ?? []).join(" / ")}</p>
                                    <small>${item.resolutionNotes ?? "已记录处理结果。"}${item.reviewedAt ? ` · ${formatTimestamp(item.reviewedAt)}` : ""}${item.replacementRunId ? ` · 接力到 ${item.replacementRunId}` : ""}</small>
                                  </article>
                                `
                              )
                              .join("")}
                          </div>
                        </details>
                      `
                      : ""
                  }
                `
                : `<p class="helper-text">点击上面的最近采样批次后，这里会展开 run 级 review queue，并支持一键回填、标记已修正、或豁免留痕。</p>`
          }
            </article>
          </div>
        </div>
      </article>
    `
    : `<p class="helper-text">${
        (state.browserSamplingPackItems ?? []).length
          ? "选择一条公开页面采样任务后，这里会出现可直接粘贴公开页原文的执行工作台。"
          : "当前没有待执行的公开页面采样任务。"
      }</p>`;

  browserSamplingCoverageBoard.innerHTML = browserSamplingCoverage.communities.length
    ? `
        <article class="import-run-section">
          <div class="breakdown-top">
            <strong>采样覆盖看板</strong>
            <span class="badge">${browserSamplingCoverage.summary.communityCount}</span>
          </div>
          <div class="comparison-strip">
            <span class="source-pill">任务 ${browserSamplingCoverage.summary.taskCount}</span>
            <span class="source-pill">已采够 ${browserSamplingCoverage.summary.resolvedTaskCount}</span>
            <span class="source-pill">补采中 ${browserSamplingCoverage.summary.inProgressTaskCount}</span>
            <span class="source-pill">待复核 ${browserSamplingCoverage.summary.reviewTaskCount}</span>
            <span class="source-pill">待采样 ${browserSamplingCoverage.summary.pendingTaskCount}</span>
          </div>
          <div class="import-run-grid">
            <article class="import-run-section coverage-subsection">
              <div class="breakdown-top">
                <strong>行政区进度</strong>
                <span class="badge">${browserSamplingCoverage.districts.length}</span>
              </div>
              <div class="coverage-grid coverage-grid--district">
                ${browserSamplingCoverage.districts
                  .slice(0, 8)
                  .map(
                    (districtItem) => `
                      <article
                        class="import-run-evidence coverage-card ${districtItem.districtId === state.districtFilter ? "is-related" : ""}"
                        data-browser-coverage-district="${districtItem.districtId ?? ""}"
                        data-browser-coverage-task-id="${districtItem.outstandingTask?.taskId ?? districtItem.highestPriorityTask?.taskId ?? ""}"
                        data-community-id="${districtItem.outstandingTask?.communityId ?? districtItem.highestPriorityTask?.communityId ?? ""}"
                        data-building-id="${districtItem.outstandingTask?.buildingId ?? districtItem.highestPriorityTask?.buildingId ?? ""}"
                        data-floor-no="${districtItem.outstandingTask?.floorNo ?? districtItem.highestPriorityTask?.floorNo ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${districtItem.districtName}</strong>
                          <span class="trace-status ${districtItem.reviewTaskCount ? "needs_review" : districtItem.completionPct >= 100 ? "resolved" : districtItem.inProgressTaskCount ? "in_progress" : "needs_capture"}">
                            ${districtItem.reviewTaskCount ? "待复核" : districtItem.completionPct >= 100 ? "已采够" : districtItem.inProgressTaskCount ? "补采中" : "待采样"}
                          </span>
                        </div>
                        <p>${districtItem.taskCount} 个任务 · 已补 ${districtItem.currentCount}/${districtItem.targetCount || districtItem.currentCount || 0}</p>
                        <div class="coverage-progress"><div class="coverage-progress-fill" style="width: ${districtItem.completionPct}%;"></div></div>
                        <div class="comparison-strip">
                          <span class="source-pill">完成 ${districtItem.completionPct}%</span>
                          <span class="source-pill">高优 ${districtItem.priorityScore}</span>
                          ${
                            districtItem.latestCaptureAt
                              ? `<span class="source-pill">最近 ${formatTimestamp(districtItem.latestCaptureAt)}</span>`
                              : `<span class="source-pill">还没采样</span>`
                          }
                        </div>
                        <small class="ranking-note">${
                          districtItem.outstandingTask
                            ? `${districtItem.outstandingTask.communityName ?? "待识别小区"}${districtItem.outstandingTask.buildingName ? ` · ${districtItem.outstandingTask.buildingName}` : ""}${districtItem.outstandingTask.floorNo != null ? ` · ${districtItem.outstandingTask.floorNo}层` : ""} · ${districtItem.outstandingTask.captureGoal}`
                            : "当前没有可继续补采的任务。"
                        }</small>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            </article>
            <article class="import-run-section coverage-subsection">
              <div class="breakdown-top">
                <strong>小区采样进度</strong>
                <span class="badge">${browserSamplingCoverage.communities.length}</span>
              </div>
              <div class="coverage-grid">
                ${browserSamplingCoverage.communities
                  .slice(0, 12)
                  .map((communityItem, index) => {
                    const primaryTask = communityItem.outstandingTask ?? communityItem.highestPriorityTask;
                    const coverageState = communityItem.reviewTaskCount
                      ? "needs_review"
                      : communityItem.missingCount <= 0
                        ? "resolved"
                        : communityItem.inProgressTaskCount
                          ? "in_progress"
                          : "needs_capture";
                    return `
                      <article
                        class="import-run-evidence coverage-card ${primaryTask?.taskId === state.selectedBrowserSamplingTaskId ? "is-related" : ""}"
                        data-browser-coverage-community-id="${communityItem.communityId ?? ""}"
                        data-browser-coverage-task-id="${primaryTask?.taskId ?? ""}"
                        data-community-id="${primaryTask?.communityId ?? communityItem.communityId ?? ""}"
                        data-building-id="${primaryTask?.buildingId ?? ""}"
                        data-floor-no="${primaryTask?.floorNo ?? ""}"
                      >
                        <div class="breakdown-top">
                          <strong>${index + 1}. ${communityItem.communityName}</strong>
                          <span class="trace-status ${coverageState}">
                            ${communityItem.reviewTaskCount ? "待复核" : communityItem.missingCount <= 0 ? "已采够" : communityItem.inProgressTaskCount ? "补采中" : "待采样"}
                          </span>
                        </div>
                        <p>${communityItem.districtName} · ${communityItem.taskCount} 个任务 · 已补 ${communityItem.currentCount}/${communityItem.targetCount || communityItem.currentCount || 0}</p>
                        <div class="coverage-progress"><div class="coverage-progress-fill" style="width: ${communityItem.completionPct}%;"></div></div>
                        <div class="comparison-strip">
                          <span class="source-pill">完成 ${communityItem.completionPct}%</span>
                          <span class="source-pill">${communityItem.focusScope === "priority" ? "重点区" : "全市"}</span>
                          ${
                            communityItem.missingCount > 0
                              ? `<span class="source-pill">还差 ${communityItem.missingCount}</span>`
                              : `<span class="source-pill">样本已达标</span>`
                          }
                          ${
                            communityItem.pendingAttentionCount
                              ? `<span class="source-pill">待复核 ${communityItem.pendingAttentionCount}</span>`
                              : ""
                          }
                        </div>
                        <small class="ranking-note">${
                          primaryTask
                            ? `${primaryTask.taskTypeLabel} · ${browserSamplingCoverageLabel(primaryTask)} · ${primaryTask.captureGoal}`
                            : "当前没有可继续补采的任务。"
                        }</small>
                      </article>
                    `;
                  })
                  .join("")}
              </div>
            </article>
          </div>
        </article>
      `
    : `<p class="helper-text">${
        (state.browserSamplingPackItems ?? []).length
          ? "当前筛选窗口里没有可汇总的公开页采样任务。"
          : "公开页面采样任务会在 staged 样本和任务包就绪后出现在这里。"
      }</p>`;

  const anchorWatchItems = operationsOverview?.anchorWatchlist ?? [];
  addressQueueList.innerHTML = displayQueueItems
    .slice(0, 5)
    .map(
      (item) => `
        <article
          class="queue-item ${item.communityId === selectedCommunityId ? "is-related" : ""} ${item.runId ? "is-imported" : ""}"
          data-community-id="${item.communityId ?? ""}"
          data-building-id="${item.buildingId ?? ""}"
          data-floor-no="${item.floorNo ?? ""}"
        >
          <div class="breakdown-top">
            <strong>${item.buildingNo} · ${item.floorNo ?? "待识别"} 层</strong>
            <span class="trace-status ${item.status}">${queueStatusLabel(item.status)}</span>
          </div>
          <p>${item.normalizedPath}</p>
          <small>${sourceLabelById(item.sourceId)} · 置信度 ${Math.round(item.confidence * 100)}% · ${item.lastActionAt}${item.batchName ? ` · ${item.batchName}` : ""}</small>
          ${
            item.runId && item.status !== "resolved"
              ? `
                <div class="queue-item-footer">
                  <button class="action compact" data-review-run-id="${item.runId}" data-review-queue-id="${item.queueId}">
                    ${state.busyReviewQueueId === item.queueId ? "回写中..." : "标记已复核"}
                  </button>
                </div>
              `
              : ""
          }
        </article>
      `
    )
    .join("");

  anchorWatchlist.innerHTML = `
    <article class="import-run-section">
      <div class="breakdown-top">
        <strong>小区锚点待补榜</strong>
        <span class="badge">${anchorWatchItems.length}</span>
      </div>
      <div class="comparison-strip">
        <span class="source-pill">重点区 ${anchorWatchItems.filter((item) => item.focusScope === "priority").length}</span>
        <span class="source-pill">有候选建议 ${anchorWatchItems.filter((item) => (item.candidateSuggestions ?? []).length > 0).length}</span>
        <span class="source-pill">筛选 ${state.districtFilter === "all" ? "全上海" : districtLabelById(state.districtFilter)}</span>
      </div>
      <div class="import-run-grid">
        ${
          anchorWatchItems.length
            ? anchorWatchItems
                .map((item) => {
                  const topCandidate = item.topCandidate ?? item.candidateSuggestions?.[0] ?? null;
                  const scoreLabel = topCandidate?.score != null ? `${Math.round(Number(topCandidate.score) * 100)}%` : "待确认";
                  const suggestionName = topCandidate?.name ?? "等待人工补点";
                  const suggestionText = topCandidate?.address ?? topCandidate?.query ?? item.sourceRefs?.[0] ?? "暂未命中可靠候选。";
                  const suggestionSource = topCandidate?.matchSource ?? topCandidate?.match_source ?? item.previewAnchorSource ?? "candidate";
                  return `
                    <article class="queue-item ${item.communityId === state.selectedCommunityId ? "is-related" : ""}" data-community-id="${item.communityId}">
                      <div class="breakdown-top">
                        <strong>${item.communityName}</strong>
                        <span class="trace-status ${item.focusScope === "priority" ? "high" : "medium"}">${item.priorityLabel}</span>
                      </div>
                      <p>${item.districtName} · ${item.sampleStatusLabel}</p>
                      <div class="comparison-strip">
                        <span class="source-pill">${suggestionName}</span>
                        <span class="source-pill">${suggestionSource}</span>
                        <span class="source-pill">${scoreLabel}</span>
                      </div>
                      <small>${suggestionText}</small>
                      ${
                        item.latestAnchorReview?.reviewedAt
                          ? `<small>最近确认 ${formatTimestamp(item.latestAnchorReview.reviewedAt)} · ${anchorDecisionLabel(item.latestAnchorReview.decisionState ?? item.anchorDecisionState)}</small>`
                          : ""
                      }
                      <div class="queue-item-footer anchor-action-row">
                        <button class="action compact primary" data-anchor-confirm-community-id="${item.communityId}" data-anchor-reference-run-id="${item.referenceRunId ?? ""}">
                          ${state.busyAnchorCommunityId === item.communityId ? "写回中..." : "确认当前候选"}
                        </button>
                        <button class="action compact" data-anchor-open-editor-community-id="${item.communityId}">手工覆盖坐标</button>
                      </div>
                    </article>
                  `;
                })
                .join("")
            : "<p class=\"helper-text\">当前没有待补小区锚点。</p>"
        }
      </div>
    </article>
  `;

  importRunList.querySelectorAll("[data-run-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      state.operationsHistoryTab = "import";
      state.operationsDetailTab = "import";
      state.selectedImportRunId = item.dataset.runId;
      state.selectedBaselineRunId = null;
      syncOperationsBackstageLocationIfNeeded();
      await loadSelectedImportRunDetail();
      render();
    });
  });

  referenceRunList.querySelectorAll("[data-reference-persist-run-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await persistReferenceRun(button.dataset.referencePersistRunId);
    });
  });

  opsSummary.querySelectorAll("[data-database-bootstrap]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await bootstrapLocalDatabaseRequest({
        referenceRunId: referenceRuns[0]?.runId ?? null,
        importRunId: state.selectedImportRunId ?? importRuns[0]?.runId ?? null,
        geoRunId: state.selectedGeoAssetRunId ?? geoAssetRuns[0]?.runId ?? null,
        applySchema: true,
        refreshMetrics: true
      });
    });
  });

  opsSummary.querySelectorAll("[data-refresh-metrics]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await refreshMetricsSnapshotRequest();
    });
  });

  opsSummary.querySelectorAll("[data-refresh-metrics-postgres]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await refreshMetricsSnapshotRequest({ writePostgres: true });
    });
  });

  geoAssetRunList.querySelectorAll("[data-geo-run-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      state.operationsHistoryTab = "geo";
      state.operationsDetailTab = "geo";
      state.selectedGeoAssetRunId = item.dataset.geoRunId;
      state.selectedGeoBaselineRunId = null;
      state.selectedGeoTaskId = null;
      syncOperationsBackstageLocationIfNeeded();
      await loadSelectedGeoAssetRunDetail();
      await loadGeoAssets();
      render();
    });
  });

  document.querySelectorAll("[data-ops-history-tab]").forEach((button) => {
    const isActive = button.dataset.opsHistoryTab === state.operationsHistoryTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      const nextTab = button.dataset.opsHistoryTab;
      if (!operationsHistoryTabs.includes(nextTab) || nextTab === state.operationsHistoryTab) {
        return;
      }
      state.operationsHistoryTab = nextTab;
      syncOperationsBackstageLocationIfNeeded();
      renderOperations();
    };
  });

  document.querySelectorAll("[data-ops-history-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.opsHistoryPanel !== state.operationsHistoryTab;
  });

  document.querySelectorAll("[data-ops-detail-tab]").forEach((button) => {
    const isActive = button.dataset.opsDetailTab === state.operationsDetailTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      const nextTab = button.dataset.opsDetailTab;
      if (!operationsDetailTabs.includes(nextTab) || nextTab === state.operationsDetailTab) {
        return;
      }
      state.operationsDetailTab = nextTab;
      syncOperationsBackstageLocationIfNeeded();
      renderOperations();
    };
  });

  document.querySelectorAll("[data-ops-detail-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.opsDetailPanel !== state.operationsDetailTab;
  });

  document.querySelectorAll("[data-ops-quality-tab]").forEach((button) => {
    const isActive = button.dataset.opsQualityTab === state.operationsQualityTab;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.onclick = () => {
      const nextTab = button.dataset.opsQualityTab;
      if (!operationsQualityTabs.includes(nextTab) || nextTab === state.operationsQualityTab) {
        return;
      }
      state.operationsQualityTab = nextTab;
      syncOperationsBackstageLocationIfNeeded();
      renderOperations();
    };
  });

  document.querySelectorAll("[data-ops-quality-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.opsQualityPanel !== state.operationsQualityTab;
  });

  [
    ...importRunDetail.querySelectorAll("[data-building-id]"),
    ...geoAssetRunDetail.querySelectorAll("[data-building-id]"),
    ...addressQueueList.querySelectorAll("[data-building-id]"),
    ...anchorWatchlist.querySelectorAll("[data-community-id]")
  ]
    .forEach((item) => {
      item.addEventListener("click", async () => {
        const geoTaskId = item.dataset.geoTaskId;
        if (geoTaskId) {
          const task = (state.selectedGeoAssetRunDetail?.coverageTasks ?? []).find((taskItem) => taskItem.taskId === geoTaskId);
          if (task) {
            await navigateToGeoTask(task, {
              waypoint: {
                source: "geo_task",
                label: `${task.communityName ?? "待识别小区"}${task.buildingName ? ` · ${task.buildingName}` : ""}`,
                detail: task.watchlistFloors?.[0]?.floorNo != null ? `${task.watchlistFloors[0].floorNo}层证据与几何补采任务` : "楼栋证据与几何补采任务"
              }
            });
            return;
          }
        }
        const source = item.classList.contains("coverage-card")
          ? "coverage"
          : item.closest("#anchorWatchlist")
            ? "coverage"
            : "queue";
        const label = item.querySelector("strong")?.textContent?.trim() || "研究对象";
        await navigateToEvidenceTarget(item.dataset.communityId, item.dataset.buildingId, item.dataset.floorNo, {
          waypoint: {
            source,
            label,
            detail:
              source === "coverage"
                ? "采样覆盖卡与对应证据"
                : "运行队列与对应证据"
          }
        });
      });
    });

  [...anchorWatchlist.querySelectorAll("[data-anchor-confirm-community-id]"), ...detailCard.querySelectorAll("[data-anchor-confirm-community-id]")]
    .forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.stopPropagation();
        const communityId = button.dataset.anchorConfirmCommunityId;
        const community = communityId === state.selectedCommunityId
          ? state.selectedCommunityDetail ?? getSelectedCommunity()
          : mapCommunities.find((item) => item.id === communityId) ?? state.opportunityItems.find((item) => item.id === communityId);
        if (community && community.id !== state.selectedCommunityId) {
          await selectCommunity(community.id, community.districtId);
        }
        await confirmCurrentAnchorCandidate(
          state.selectedCommunityDetail ?? community,
          button.dataset.anchorReferenceRunId || null
        );
      });
    });

  [...anchorWatchlist.querySelectorAll("[data-anchor-open-editor-community-id]"), ...detailCard.querySelectorAll("[data-anchor-open-editor-community-id]")]
    .forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.stopPropagation();
        const communityId = button.dataset.anchorOpenEditorCommunityId;
        const community = communityId === state.selectedCommunityId
          ? state.selectedCommunityDetail ?? getSelectedCommunity()
          : mapCommunities.find((item) => item.id === communityId) ?? state.opportunityItems.find((item) => item.id === communityId);
        if (community && community.id !== state.selectedCommunityId) {
          await selectCommunity(community.id, community.districtId);
        }
        if (state.anchorEditorCommunityId === communityId) {
          closeAnchorManualEditor();
        } else {
          openAnchorManualEditor(state.selectedCommunityDetail ?? community);
        }
        render();
      });
    });

  browserSamplingWorkbench.querySelectorAll("[data-browser-workbench-copy-sale]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = currentBrowserSamplingTask();
      await copyTextToClipboard(task?.saleQuery, "Sale 检索词已复制。");
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-workbench-copy-rent]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = currentBrowserSamplingTask();
      await copyTextToClipboard(task?.rentQuery, "Rent 检索词已复制。");
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-workbench-copy-target]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = currentBrowserSamplingTask();
      await copyTextToClipboard(task?.targetQuery, "目标检索词已复制。");
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-workbench-copy-brief]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await copyTextToClipboard(browserSamplingInstructionText(currentBrowserSamplingTask()), "整包采样指令已复制。");
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-workbench-next-district], [data-browser-workbench-next-review], [data-browser-workbench-next-capture], [data-browser-workbench-task-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.dataset.browserWorkbenchNextReview) {
        const reviewItem =
          (state.browserReviewInboxItems ?? []).find(
            (item) =>
              item?.runId === (button.dataset.browserWorkbenchNextReviewRunId || null) &&
              item?.queueId === (button.dataset.browserWorkbenchNextReviewQueueId || null)
          ) ??
          null;
        if (reviewItem?.taskId && reviewItem?.runId && reviewItem?.queueId) {
          await navigateToBrowserReviewInboxItem(reviewItem, { resetDraft: false });
          render();
          return;
        }
      }
      const taskId =
        button.dataset.browserWorkbenchTaskId ||
        button.dataset.browserWorkbenchNextDistrict ||
        button.dataset.browserWorkbenchNextReview ||
        button.dataset.browserWorkbenchNextCapture;
      const task = (state.browserSamplingPackItems ?? []).find((item) => item.taskId === taskId);
      if (!task) {
        return;
      }
      await navigateToBrowserSamplingTask(task, {
        resetDraft: false,
        revealLatestCaptureRun: button.dataset.browserWorkbenchNextReview ? true : "auto"
      });
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-review-inbox-item-id]").forEach((card) => {
    card.addEventListener("click", async () => {
      const item =
        (state.browserReviewInboxItems ?? []).find(
          (entry) =>
            entry?.inboxItemId === (card.dataset.browserReviewInboxItemId || null) ||
            (entry?.runId === (card.dataset.browserReviewInboxRunId || null) &&
              entry?.queueId === (card.dataset.browserReviewInboxQueueId || null))
        ) ?? null;
      await navigateToBrowserReviewInboxItem(item, { resetDraft: false });
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-field]").forEach((input) => {
    const syncDraft = (event) => {
      const channel = input.dataset.browserCaptureChannel;
      const field = input.dataset.browserCaptureField;
      if (!channel || !field) {
        return;
      }
      updateBrowserCaptureDraft(channel, field, event.target.value);
    };
    input.addEventListener("input", syncDraft);
    input.addEventListener("change", syncDraft);
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-reset]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      resetBrowserCaptureDraft();
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-submit]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const task = currentBrowserSamplingTask();
      await submitBrowserSamplingCapture(task);
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-run-id]").forEach((card) => {
    card.addEventListener("click", async () => {
      const taskId = card.dataset.browserTaskId;
      if (taskId) {
        selectBrowserSamplingTask(taskId, { resetDraft: false });
      }
      await loadSelectedBrowserCaptureRunDetail(card.dataset.browserCaptureRunId);
      await navigateToEvidenceTarget(card.dataset.communityId, card.dataset.buildingId || null, card.dataset.floorNo || null);
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-fill-from-attention]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const queueId = button.dataset.browserCaptureFillFromAttention || "";
      const item = currentBrowserCaptureReviewQueue().find((entry) => entry.queueId === queueId) ?? null;
      if (!item) {
        return;
      }
      fillBrowserCaptureDraftFromAttention(item);
      state.selectedBrowserCaptureReviewQueueId = item.queueId ?? null;
      state.opsMessage = `已把 ${item.businessTypeLabel} attention 原文回填到草稿。`;
      state.opsMessageTone = "success";
      state.opsMessageContext = "sampling";
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-copy-raw]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const queueId = button.dataset.browserCaptureCopyRaw || "";
      const item = currentBrowserCaptureReviewQueue().find((entry) => entry.queueId === queueId) ?? null;
      await copyTextToClipboard(item?.rawText ?? "", "attention 原文已复制。");
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-select]").forEach((input) => {
    const syncSelection = (event) => {
      event.stopPropagation();
      toggleBrowserCaptureReviewBatchSelection(
        input.dataset.browserCaptureReviewSelect || "",
        input.checked,
        currentBrowserCaptureReviewQueue()
      );
      render();
    };
    input.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    input.addEventListener("change", syncSelection);
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-select-all]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      selectAllBrowserCaptureReviewBatchItems(currentBrowserCaptureReviewQueue());
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-clear-selection]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      clearBrowserCaptureReviewBatchSelection();
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-queue-item]").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedBrowserCaptureReviewQueueId = card.dataset.browserCaptureReviewQueueItem || null;
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-resolve]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const runId = currentBrowserCaptureRun()?.runId;
      const queueId = button.dataset.browserCaptureReviewResolve || "";
      await reviewBrowserCaptureQueueItem(runId, queueId, {
        status: "resolved",
        resolutionNotes: "已修正后由工作台人工确认。",
      });
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-waive]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const runId = currentBrowserCaptureRun()?.runId;
      const queueId = button.dataset.browserCaptureReviewWaive || "";
      const reason = window.prompt("请输入豁免原因：", "已人工确认当前缺失可接受。");
      if (!reason || !reason.trim()) {
        return;
      }
      await reviewBrowserCaptureQueueItem(runId, queueId, {
        status: "waived",
        resolutionNotes: reason.trim(),
      });
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-batch-resolve]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const runId = button.dataset.browserCaptureReviewBatchResolve || currentBrowserCaptureRun()?.runId;
      const queueIds = currentBrowserCaptureReviewBatchSelection(currentBrowserCaptureReviewQueue());
      await reviewBrowserCaptureQueueBatch(runId, queueIds, {
        status: "resolved",
        resolutionNotes: "已由工作台批量确认并完成修正。",
      });
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-review-batch-waive]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const runId = button.dataset.browserCaptureReviewBatchWaive || currentBrowserCaptureRun()?.runId;
      const queueIds = currentBrowserCaptureReviewBatchSelection(currentBrowserCaptureReviewQueue());
      if (!queueIds.length) {
        return;
      }
      const reason = window.prompt("请输入本次批量豁免原因：", "已人工确认当前缺失可接受。");
      if (!reason || !reason.trim()) {
        return;
      }
      await reviewBrowserCaptureQueueBatch(runId, queueIds, {
        status: "waived",
        resolutionNotes: reason.trim(),
      });
    });
  });

  browserSamplingCoverageBoard.querySelectorAll("[data-browser-coverage-district]").forEach((card) => {
    card.addEventListener("click", async () => {
      const districtId = card.dataset.browserCoverageDistrict;
      await applyDistrictScope(districtId || "all");
      const taskId = card.dataset.browserCoverageTaskId;
      const task = taskId ? (state.browserSamplingPackItems ?? []).find((item) => item.taskId === taskId) : null;
      if (task) {
        await navigateToBrowserSamplingTask(task, { resetDraft: false });
        render();
        return;
      }
      if (taskId) {
        selectBrowserSamplingTask(taskId, { resetDraft: false });
      }
      render();
      if (card.dataset.communityId) {
        await navigateToEvidenceTarget(card.dataset.communityId, card.dataset.buildingId || null, card.dataset.floorNo || null);
      }
      render();
    });
  });

  browserSamplingCoverageBoard.querySelectorAll("[data-browser-coverage-community-id]").forEach((card) => {
    card.addEventListener("click", async () => {
      const taskId = card.dataset.browserCoverageTaskId;
      const community = findCommunityById(card.dataset.communityId);
      await applyDistrictScope(community?.districtId ?? state.districtFilter);
      const task = taskId ? (state.browserSamplingPackItems ?? []).find((item) => item.taskId === taskId) : null;
      if (task) {
        await navigateToBrowserSamplingTask(task, { resetDraft: false });
        render();
        return;
      }
      if (taskId) {
        selectBrowserSamplingTask(taskId, { resetDraft: false });
      }
      await navigateToEvidenceTarget(card.dataset.communityId, card.dataset.buildingId || null, card.dataset.floorNo || null);
      render();
    });
  });

  detailCard.querySelectorAll("[data-anchor-close-editor-community-id]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      closeAnchorManualEditor();
      render();
    });
  });

  detailCard.querySelectorAll("[data-anchor-draft-field]").forEach((input) => {
    const handler = input.tagName === "TEXTAREA" || input.type === "text" ? "input" : "change";
    input.addEventListener(handler, (event) => {
      const field = input.dataset.anchorDraftField;
      if (!field) {
        return;
      }
      state.anchorDraft = {
        ...state.anchorDraft,
        [field]: event.target.value
      };
    });
  });

  detailCard.querySelectorAll("[data-anchor-save-manual-community-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const community = state.selectedCommunityDetail ?? getSelectedCommunity();
      await saveManualAnchorOverride(community);
    });
  });

  importRunDetail.querySelectorAll("[data-persist-run-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await persistImportRun(button.dataset.persistRunId);
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-persist-run-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (button.disabled) {
        return;
      }
      await persistGeoAssetRun(button.dataset.geoPersistRunId);
    });
  });

  [...importRunDetail.querySelectorAll("[data-review-queue-id]"), ...addressQueueList.querySelectorAll("[data-review-queue-id]")]
    .forEach((button) => {
      button.addEventListener("click", async (event) => {
        event.stopPropagation();
        await reviewQueueItem(button.dataset.reviewRunId, button.dataset.reviewQueueId);
      });
    });

  geoAssetRunDetail.querySelectorAll("[data-geo-review-task-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await reviewGeoAssetTask(button.dataset.geoReviewRunId, button.dataset.geoReviewTaskId, {
        status: button.dataset.geoNextStatus,
        resolutionNotes:
          button.dataset.geoNextStatus === "scheduled"
            ? "已在工作台标记为待补采并派给 GIS。"
            : button.dataset.geoNextStatus === "captured"
              ? "已确认下一版 footprint 会补齐该楼栋。"
              : "已由工作台人工复核确认。"
      });
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-create-work-order-task-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await createGeoWorkOrder(button.dataset.geoCreateWorkOrderRunId, button.dataset.geoCreateWorkOrderTaskId);
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-update-work-order-id]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await updateGeoWorkOrder(button.dataset.geoUpdateWorkOrderRunId, button.dataset.geoUpdateWorkOrderId, {
        status: button.dataset.geoUpdateWorkOrderStatus
      });
    });
  });

  importRunDetail.querySelectorAll("[data-baseline-run-select]").forEach((select) => {
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      state.selectedBaselineRunId = select.value || null;
      syncOperationsBackstageLocationIfNeeded();
      await loadSelectedImportRunDetail();
      render();
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-baseline-run-select]").forEach((select) => {
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      state.selectedGeoBaselineRunId = select.value || null;
      state.selectedGeoTaskId = null;
      syncOperationsBackstageLocationIfNeeded();
      await loadSelectedGeoAssetRunDetail();
      render();
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-work-order-status-filter]").forEach((select) => {
    select.addEventListener("change", (event) => {
      event.stopPropagation();
      state.geoWorkOrderStatusFilter = select.value || "all";
      render();
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-work-order-assignee-filter]").forEach((select) => {
    select.addEventListener("change", (event) => {
      event.stopPropagation();
      state.geoWorkOrderAssigneeFilter = select.value || "all";
      render();
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-export-work-orders-geojson]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await runExportAction(
        button,
        "导出中…",
        "工单 GeoJSON 已导出",
        "/api/export/geo-work-orders.geojson",
        buildGeoWorkOrderExportFilename("geojson"),
        buildGeoWorkOrderGeoJson,
        "application/geo+json",
        buildGeoWorkOrderExportQuery()
      );
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-export-work-orders-csv]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await runExportAction(
        button,
        "导出中…",
        "工单 CSV 已导出",
        "/api/export/geo-work-orders.csv",
        buildGeoWorkOrderExportFilename("csv"),
        buildGeoWorkOrderCsv,
        "text/csv;charset=utf-8",
        buildGeoWorkOrderExportQuery()
      );
    });
  });
}

function getYieldColor(value) {
  if (value >= 2.8) {
    return "#ff9966";
  }
  if (value >= 2.45) {
    return "#5bd5c1";
  }
  return "#6f8fff";
}




function sourceLabelById(sourceId) {
  if (sourceId === "authorized-manual") {
    return "授权手工样本";
  }
  return (
    operationsOverview?.sourceHealth?.find((item) => item.sourceId === sourceId || item.id === sourceId)?.name ??
    dataSources.find((item) => item.id === sourceId)?.name ??
    sourceId
  );
}


function renderProviderActions(source, options = {}) {
  const compact = options.compact ?? false;
  const actions = [
    source.applyUrl ? `<a class="source-link" href="${source.applyUrl}" target="_blank" rel="noreferrer">申请入口</a>` : "",
    source.docsUrl ? `<a class="source-link" href="${source.docsUrl}" target="_blank" rel="noreferrer">文档</a>` : "",
    source.platformUrl ? `<a class="source-link" href="${source.platformUrl}" target="_blank" rel="noreferrer">平台</a>` : "",
    source.guideUrl ? `<a class="source-link" href="${source.guideUrl}" target="_blank" rel="noreferrer">接入说明</a>` : ""
  ].filter(Boolean);
  if (!actions.length) {
    return "";
  }
  return `<div class="source-actions ${compact ? "compact" : ""}">${actions.join("")}</div>`;
}

function districtLabelById(districtId) {
  return districts.find((item) => item.id === districtId)?.name ?? districtId ?? "全上海";
}




function nextGeoTaskStatus(task) {
  if (!task) {
    return null;
  }
  if (task.status === "needs_review") {
    return "resolved";
  }
  if (task.status === "needs_capture") {
    return "scheduled";
  }
  if (task.status === "scheduled") {
    return "captured";
  }
  return null;
}

function geoTaskActionLabel(task) {
  const nextStatus = nextGeoTaskStatus(task);
  return {
    resolved: "标记已复核",
    scheduled: "标记已派工",
    captured: "标记已补齐"
  }[nextStatus] ?? "更新任务";
}



function nextGeoWorkOrderStatus(workOrder) {
  if (!workOrder) {
    return null;
  }
  if (workOrder.status === "assigned") {
    return "in_progress";
  }
  if (workOrder.status === "in_progress") {
    return "delivered";
  }
  if (workOrder.status === "delivered") {
    return "closed";
  }
  return null;
}

function geoWorkOrderActionLabel(workOrder) {
  const nextStatus = nextGeoWorkOrderStatus(workOrder);
  return {
    in_progress: "标记执行中",
    delivered: "标记待验收",
    closed: "标记已关闭"
  }[nextStatus] ?? "更新工单";
}


function canCreateGeoWorkOrder(task) {
  return ["needs_capture", "scheduled"].includes(task?.status) && !task?.workOrderId;
}

function getGeoWorkOrderAssignees() {
  return Array.from(
    new Set(
      (state.selectedGeoAssetRunDetail?.workOrders ?? [])
        .map((item) => (item.assignee ?? "").trim())
        .filter((value) => value)
    )
  ).sort((left, right) => left.localeCompare(right, "zh-CN"));
}

function getGeoWorkOrderItems(limit = null) {
  const districtFilter = state.districtFilter;
  const statusFilter = state.geoWorkOrderStatusFilter ?? "all";
  const assigneeFilter = state.geoWorkOrderAssigneeFilter ?? "all";
  const items = (state.selectedGeoAssetRunDetail?.workOrders ?? [])
    .filter((item) => districtFilter === "all" || item.districtId === districtFilter)
    .filter((item) => {
      if (statusFilter === "all") {
        return true;
      }
      if (statusFilter === "open") {
        return item.status !== "closed";
      }
      return item.status === statusFilter;
    })
    .filter((item) => assigneeFilter === "all" || (item.assignee ?? "").trim() === assigneeFilter)
    .slice()
    .sort((left, right) => {
      const rank = (value) =>
        ({
          assigned: 0,
          in_progress: 1,
          delivered: 2,
          closed: 3
        }[value] ?? 9);
      return (
        rank(left.status) - rank(right.status) ||
        Number(right.impactScore ?? 0) - Number(left.impactScore ?? 0) ||
        Number(right.watchlistHits ?? 0) - Number(left.watchlistHits ?? 0) ||
        `${left.communityName ?? ""}`.localeCompare(`${right.communityName ?? ""}`, "zh-CN")
      );
    });

  return typeof limit === "number" ? items.slice(0, limit) : items;
}


function buildGeoJson() {
  const features = getFilteredCommunities().map((community) => ({
    type: "Feature",
    properties: {
      name: community.name,
      district: districts.find((district) => district.id === community.districtId)?.name,
      avg_price_wan: community.avgPriceWan,
      monthly_rent: community.monthlyRent,
      yield_pct: community.yield,
      opportunity_score: community.score,
      sample_size: community.sample,
      granularity: state.granularity
    },
    geometry: {
      type: "Point",
      coordinates: normalizeSvgToLonLat(community.x, community.y)
    }
  }));

  return JSON.stringify(
    {
      type: "FeatureCollection",
      name: "ShanghaiYieldAtlas",
      features
    },
    null,
    2
  );
}

function floorWatchlistPoint(item) {
  return resolveFloorGeometry(item)?.position ?? [121.4737, 31.2304];
}

function floorWatchlistFeatureName(item) {
  return `${item.communityName} · ${item.buildingName} · ${item.floorNo}层`;
}

function geoTaskWatchlistFeatureName(item) {
  return `${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"}`;
}

function geoTaskWatchlistPoint(item) {
  const lookup = item.buildingId ? findBuildingById(item.buildingId) : null;
  if (lookup) {
    return resolveBuildingGeometry(lookup.community, lookup.building)?.position ?? [121.4737, 31.2304];
  }
  const community = item.communityId ? findCommunityById(item.communityId) : null;
  if (community) {
    return normalizeSvgToLonLat(community.x, community.y);
  }
  return [121.4737, 31.2304];
}

function geoWorkOrderFeatureName(item) {
  return item.title || `${item.communityName ?? "待识别小区"} · ${item.buildingName ?? "待识别楼栋"} 几何补采`;
}

function geoWorkOrderPoint(item) {
  const lookup = item.buildingId ? findBuildingById(item.buildingId) : null;
  if (lookup) {
    return resolveBuildingGeometry(lookup.community, lookup.building)?.position ?? [121.4737, 31.2304];
  }
  const community = item.communityId ? findCommunityById(item.communityId) : null;
  if (community) {
    return normalizeSvgToLonLat(community.x, community.y);
  }
  return [121.4737, 31.2304];
}

function buildGeoWorkOrderGeoJson() {
  const features = getGeoWorkOrderItems().map((item) => {
    const lookup = item.buildingId ? findBuildingById(item.buildingId) : null;
    const geometry = lookup ? resolveBuildingGeometry(lookup.community, lookup.building) : null;
    return {
      type: "Feature",
      properties: {
        name: geoWorkOrderFeatureName(item),
        title: item.title,
        district: item.districtName,
        district_id: item.districtId,
        community_id: item.communityId,
        community_name: item.communityName,
        building_id: item.buildingId,
        building_name: item.buildingName,
        work_order_id: item.workOrderId,
        status: item.status,
        status_label: geoWorkOrderStatusLabel(item.status),
        assignee: item.assignee ?? "",
        task_count: item.taskCount ?? 0,
        task_ids: item.taskIds ?? [],
        primary_task_id: item.primaryTaskId ?? null,
        focus_floor_no: item.focusFloorNo ?? null,
        focus_yield_pct: item.focusYieldPct ?? null,
        impact_score: item.impactScore ?? null,
        impact_band: item.impactBand ?? null,
        watchlist_hits: item.watchlistHits ?? 0,
        due_at: item.dueAt ?? null,
        created_at: item.createdAt ?? null,
        updated_at: item.updatedAt ?? null,
        created_by: item.createdBy ?? null,
        notes: item.notes ?? null,
        geo_asset_run_id: state.selectedGeoAssetRunId ?? null,
        geo_asset_batch_name: state.selectedGeoAssetRunDetail?.batchName ?? null,
        export_scope: "geo_work_orders"
      },
      geometry:
        geometry && geometry.lonLatPath?.length
          ? {
              type: "Polygon",
              coordinates: [geometry.lonLatPath]
            }
          : {
              type: "Point",
              coordinates: geoWorkOrderPoint(item)
            }
    };
  });

  return JSON.stringify(
    {
      type: "FeatureCollection",
      name: "ShanghaiGeoWorkOrders",
      features
    },
    null,
    2
  );
}

function buildGeoWorkOrderCsv() {
  const rows = getGeoWorkOrderItems().map((item) => ({
    geo_asset_run_id: state.selectedGeoAssetRunId ?? "",
    geo_asset_batch_name: state.selectedGeoAssetRunDetail?.batchName ?? "",
    district_name: item.districtName ?? "",
    community_name: item.communityName ?? "",
    building_name: item.buildingName ?? "",
    work_order_id: item.workOrderId ?? "",
    title: item.title ?? "",
    status: item.status ?? "",
    status_label: geoWorkOrderStatusLabel(item.status),
    assignee: item.assignee ?? "",
    task_count: item.taskCount ?? "",
    task_ids: (item.taskIds ?? []).join("|"),
    primary_task_id: item.primaryTaskId ?? "",
    focus_floor_no: item.focusFloorNo ?? "",
    focus_yield_pct: item.focusYieldPct ?? "",
    impact_score: item.impactScore ?? "",
    impact_band: item.impactBand ?? "",
    watchlist_hits: item.watchlistHits ?? "",
    due_at: item.dueAt ?? "",
    created_at: item.createdAt ?? "",
    updated_at: item.updatedAt ?? "",
    created_by: item.createdBy ?? "",
    notes: item.notes ?? ""
  }));
  const headers = Object.keys(
    rows[0] ?? {
      geo_asset_run_id: "",
      geo_asset_batch_name: "",
      district_name: "",
      community_name: "",
      building_name: "",
      work_order_id: "",
      title: "",
      status: "",
      status_label: "",
      assignee: "",
      task_count: "",
      task_ids: "",
      primary_task_id: "",
      focus_floor_no: "",
      focus_yield_pct: "",
      impact_score: "",
      impact_band: "",
      watchlist_hits: "",
      due_at: "",
      created_at: "",
      updated_at: "",
      created_by: "",
      notes: ""
    }
  );
  const escapeCsv = (value) => {
    const text = `${value ?? ""}`;
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(","))].join("\n");
}

function buildFloorWatchlistGeoJson() {
  const features = (state.floorWatchlistItems?.length ? state.floorWatchlistItems : canUseDemoFallback() ? getFallbackFloorWatchlistItems() : []).map((item) => ({
    type: "Feature",
    properties: {
      name: floorWatchlistFeatureName(item),
      district: item.districtName,
      community_id: item.communityId,
      building_id: item.buildingId,
      building_name: item.buildingName,
      floor_no: item.floorNo,
      latest_yield_pct: item.latestYieldPct,
      window_yield_delta_pct: item.windowYieldDeltaPct ?? null,
      yield_delta_since_first: item.yieldDeltaSinceFirst ?? null,
      latest_pair_count: item.latestPairCount,
      window_pair_count_delta: item.windowPairCountDelta ?? null,
      observed_runs: item.observedRuns,
      total_pair_count: item.totalPairCount,
      persistence_score: item.persistenceScore,
      trend_label: item.trendLabel,
      latest_status: item.latestStatus,
      latest_batch_name: item.latestBatchName,
      baseline_batch_name: item.baselineBatchName ?? null,
      export_scope: "floor_watchlist"
    },
    geometry: (() => {
      const geometry = resolveFloorGeometry(item);
      if (!geometry) {
        return {
          type: "Point",
          coordinates: floorWatchlistPoint(item)
        };
      }
      return {
        type: "Polygon",
        coordinates: [geometry.lonLatPath]
      };
    })()
  }));

  return JSON.stringify(
    {
      type: "FeatureCollection",
      name: "ShanghaiYieldFloorWatchlist",
      features
    },
    null,
    2
  );
}

function buildGeoTaskWatchlistGeoJson() {
  const features = getGeoTaskWatchlistItems(Math.max(getGeoTaskWatchlistItems().length, 12)).map((item) => {
    const lookup = item.buildingId ? findBuildingById(item.buildingId) : null;
    const geometry = lookup ? resolveBuildingGeometry(lookup.community, lookup.building) : null;
    return {
      type: "Feature",
      properties: {
        name: geoTaskWatchlistFeatureName(item),
        district: item.districtName,
        district_id: item.districtId,
        community_id: item.communityId,
        community_name: item.communityName,
        building_id: item.buildingId,
        building_name: item.buildingName,
        task_id: item.taskId,
        task_scope: item.taskScope,
        task_scope_label: item.taskScopeLabel,
        status: item.status,
        status_label: geoTaskStatusLabel(item.status),
        impact_score: item.impactScore,
        impact_band: item.impactBand,
        impact_label: item.impactLabel,
        watchlist_hits: item.watchlistHits,
        focus_floor_no: item.focusFloorNo ?? item.watchlistFloors?.[0]?.floorNo ?? null,
        focus_yield_pct: item.focusYieldPct ?? item.watchlistFloors?.[0]?.latestYieldPct ?? null,
        focus_trend_label: item.focusTrendLabel ?? item.watchlistFloors?.[0]?.trendLabel ?? null,
        target_granularity: item.focusFloorNo != null || item.watchlistFloors?.[0]?.floorNo != null ? "floor" : "building",
        community_score: item.communityScore ?? null,
        building_opportunity_score: item.buildingOpportunityScore ?? null,
        coverage_gap_count: item.coverageGapCount ?? null,
        work_order_id: item.workOrderId ?? null,
        work_order_status: item.workOrderStatus ?? null,
        work_order_status_label: item.workOrderStatusLabel ?? null,
        work_order_assignee: item.workOrderAssignee ?? null,
        source_ref: item.sourceRef ?? null,
        recommended_action: item.recommendedAction ?? null,
        geo_asset_run_id: item.geoAssetRunId ?? state.selectedGeoAssetRunId ?? null,
        geo_asset_batch_name: item.geoAssetBatchName ?? state.selectedGeoAssetRunDetail?.batchName ?? null,
        export_scope: "geo_task_watchlist"
      },
      geometry:
        geometry && geometry.lonLatPath?.length
          ? {
              type: "Polygon",
              coordinates: [geometry.lonLatPath]
            }
          : {
              type: "Point",
              coordinates: geoTaskWatchlistPoint(item)
            }
    };
  });

  return JSON.stringify(
    {
      type: "FeatureCollection",
      name: "ShanghaiGeoTaskWatchlist",
      features
    },
    null,
    2
  );
}

function buildGeoTaskWatchlistCsv() {
  const rows = getGeoTaskWatchlistItems(Math.max(getGeoTaskWatchlistItems().length, 12)).map((item) => ({
    geo_asset_run_id: item.geoAssetRunId ?? state.selectedGeoAssetRunId ?? "",
    geo_asset_batch_name: item.geoAssetBatchName ?? state.selectedGeoAssetRunDetail?.batchName ?? "",
    district_name: item.districtName ?? "",
    community_name: item.communityName ?? "",
    building_name: item.buildingName ?? "",
    task_id: item.taskId ?? "",
    task_scope: item.taskScope ?? "",
    task_scope_label: item.taskScopeLabel ?? "",
    status: item.status ?? "",
    status_label: geoTaskStatusLabel(item.status),
    impact_score: item.impactScore ?? "",
    impact_band: item.impactBand ?? "",
    impact_label: item.impactLabel ?? "",
    watchlist_hits: item.watchlistHits ?? "",
    focus_floor_no: item.focusFloorNo ?? item.watchlistFloors?.[0]?.floorNo ?? "",
    focus_yield_pct: item.focusYieldPct ?? item.watchlistFloors?.[0]?.latestYieldPct ?? "",
    focus_trend_label: item.focusTrendLabel ?? item.watchlistFloors?.[0]?.trendLabel ?? "",
    target_granularity: item.focusFloorNo != null || item.watchlistFloors?.[0]?.floorNo != null ? "floor" : "building",
    community_score: item.communityScore ?? "",
    building_opportunity_score: item.buildingOpportunityScore ?? "",
    coverage_gap_count: item.coverageGapCount ?? "",
    work_order_id: item.workOrderId ?? "",
    work_order_status: item.workOrderStatus ?? "",
    work_order_status_label: item.workOrderStatusLabel ?? "",
    work_order_assignee: item.workOrderAssignee ?? "",
    source_ref: item.sourceRef ?? "",
    recommended_action: item.recommendedAction ?? "",
    review_owner: item.reviewOwner ?? "",
    reviewed_at: item.reviewedAt ?? "",
    updated_at: item.updatedAt ?? ""
  }));
  const headers = Object.keys(rows[0] ?? {
    geo_asset_run_id: "",
    geo_asset_batch_name: "",
    district_name: "",
    community_name: "",
    building_name: "",
    task_id: "",
    task_scope: "",
    task_scope_label: "",
    status: "",
    status_label: "",
    impact_score: "",
    impact_band: "",
    impact_label: "",
    watchlist_hits: "",
    focus_floor_no: "",
    focus_yield_pct: "",
    focus_trend_label: "",
    target_granularity: "",
    community_score: "",
    building_opportunity_score: "",
    coverage_gap_count: "",
    work_order_id: "",
    work_order_status: "",
    work_order_status_label: "",
    work_order_assignee: "",
    source_ref: "",
    recommended_action: "",
    review_owner: "",
    reviewed_at: "",
    updated_at: ""
  });
  const escapeCsv = (value) => {
    const text = `${value ?? ""}`;
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(","))].join("\n");
}

function buildBrowserSamplingPackCsv() {
  const rows = getBrowserSamplingPackItems(Math.max(getBrowserSamplingPackItems().length, 12)).map((item) => ({
    task_id: item.taskId ?? "",
    provider_id: item.providerId ?? "",
    task_type: item.taskType ?? "",
    task_type_label: item.taskTypeLabel ?? "",
    target_granularity: item.targetGranularity ?? "",
    focus_scope: item.focusScope ?? "",
    priority_score: item.priorityScore ?? "",
    priority_label: item.priorityLabel ?? "",
    district_name: item.districtName ?? "",
    community_name: item.communityName ?? "",
    building_name: item.buildingName ?? "",
    floor_no: item.floorNo ?? "",
    sample_status: item.sampleStatus ?? "",
    sample_status_label: item.sampleStatusLabel ?? "",
    current_yield_pct: item.currentYieldPct ?? "",
    current_pair_count: item.currentPairCount ?? "",
    target_pair_count: item.targetPairCount ?? "",
    missing_pair_count: item.missingPairCount ?? "",
    current_sample_size: item.currentSampleSize ?? "",
    target_sample_size: item.targetSampleSize ?? "",
    missing_sample_count: item.missingSampleCount ?? "",
    data_freshness: item.dataFreshness ?? "",
    reason: item.reason ?? "",
    capture_goal: item.captureGoal ?? "",
    target_query: item.targetQuery ?? "",
    sale_query: item.saleQuery ?? "",
    rent_query: item.rentQuery ?? "",
    required_fields: (item.requiredFields ?? []).join(" / "),
    recommended_action: item.recommendedAction ?? ""
  }));
  const headers = Object.keys(rows[0] ?? {
    task_id: "",
    provider_id: "",
    task_type: "",
    task_type_label: "",
    target_granularity: "",
    focus_scope: "",
    priority_score: "",
    priority_label: "",
    district_name: "",
    community_name: "",
    building_name: "",
    floor_no: "",
    sample_status: "",
    sample_status_label: "",
    current_yield_pct: "",
    current_pair_count: "",
    target_pair_count: "",
    missing_pair_count: "",
    current_sample_size: "",
    target_sample_size: "",
    missing_sample_count: "",
    data_freshness: "",
    reason: "",
    capture_goal: "",
    target_query: "",
    sale_query: "",
    rent_query: "",
    required_fields: "",
    recommended_action: ""
  });
  const escapeCsv = (value) => {
    const text = `${value ?? ""}`;
    return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
  };
  return [headers.join(","), ...rows.map((row) => headers.map((header) => escapeCsv(row[header])).join(","))].join("\n");
}

function buildFloorWatchlistKml() {
  const placemarks = (state.floorWatchlistItems?.length ? state.floorWatchlistItems : canUseDemoFallback() ? getFallbackFloorWatchlistItems() : [])
    .map((item) => {
      const geometry = resolveFloorGeometry(item);
      const ring = geometry?.lonLatPath ?? [];
      const deltaText =
        item.windowYieldDeltaPct != null
          ? formatSignedDelta(item.windowYieldDeltaPct, { suffix: "%", digits: 2 })
          : item.yieldDeltaSinceFirst != null
          ? formatSignedDelta(item.yieldDeltaSinceFirst, { suffix: "%", digits: 2 })
          : "首批样本";
      const pairDeltaText = item.windowPairCountDelta != null ? formatSignedDelta(item.windowPairCountDelta, { digits: 0 }) : "n/a";
      const coordinateString = ring.map(([lon, lat]) => `${lon},${lat},0`).join(" ");
      const pointFallback = floorWatchlistPoint(item).join(",") + ",0";
      return `
  <Placemark>
    <name>${escapeXml(floorWatchlistFeatureName(item))}</name>
    <description><![CDATA[
      行政区: ${item.districtName}<br/>
      当前回报率: ${Number(item.latestYieldPct).toFixed(2)}%<br/>
      趋势标签: ${item.trendLabel}<br/>
      持续分: ${item.persistenceScore}<br/>
      当前批次: ${item.latestBatchName}<br/>
      基线批次: ${item.baselineBatchName ?? "自动首批"}<br/>
      回报变化: ${deltaText}<br/>
      配对变化: ${pairDeltaText}<br/>
      当前样本对: ${item.latestPairCount}<br/>
      累计样本对: ${item.totalPairCount}<br/>
      观测批次: ${item.observedRuns}
    ]]></description>
    ${
      ring.length
        ? `<Polygon>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>${coordinateString}</coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>`
        : `<Point>
      <coordinates>${pointFallback}</coordinates>
    </Point>`
    }
  </Placemark>`;
    })
    .join("");

  return `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Shanghai Yield Floor Watchlist</name>
    ${placemarks}
  </Document>
</kml>`;
}

function buildKml() {
  const placemarks = getFilteredCommunities()
    .map((community) => {
      const [lon, lat] = normalizeSvgToLonLat(community.x, community.y);
      return `
  <Placemark>
    <name>${escapeXml(community.name)}</name>
    <description><![CDATA[
      行政区: ${districts.find((district) => district.id === community.districtId)?.name}<br/>
      年化回报率: ${community.yield.toFixed(2)}%<br/>
      挂牌总价: ${community.avgPriceWan} 万<br/>
      月租中位数: ${community.monthlyRent} 元<br/>
      机会评分: ${community.score}<br/>
      样本量: ${community.sample}
    ]]></description>
    <Point>
      <coordinates>${lon},${lat},0</coordinates>
    </Point>
  </Placemark>`;
    })
    .join("");

  return `<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Shanghai Yield Atlas</name>
    ${placemarks}
  </Document>
</kml>`;
}

function buildExportQuery() {
  const params = new URLSearchParams({
    district: state.districtFilter,
    min_yield: String(state.minYield),
    max_budget: String(state.maxBudget),
    min_samples: String(state.minSamples)
  });
  if (state.selectedGeoAssetRunId) {
    params.set("geo_run_id", state.selectedGeoAssetRunId);
  }
  return params.toString();
}

function buildFloorWatchlistExportQuery() {
  const params = new URLSearchParams({
    district: state.districtFilter,
    min_yield: String(state.minYield),
    max_budget: String(state.maxBudget),
    min_samples: String(state.minSamples),
    limit: String(Math.max(state.floorWatchlistItems?.length ?? 0, 12))
  });
  if (state.selectedImportRunId) {
    params.set("run_id", state.selectedImportRunId);
  }
  if (state.selectedBaselineRunId) {
    params.set("baseline_run_id", state.selectedBaselineRunId);
  }
  if (state.selectedGeoAssetRunId) {
    params.set("geo_run_id", state.selectedGeoAssetRunId);
  }
  return params.toString();
}

function buildGeoTaskWatchlistExportQuery() {
  const params = new URLSearchParams({
    district: state.districtFilter,
    limit: String(Math.max(getGeoTaskWatchlistItems().length, 12))
  });
  if (state.selectedGeoAssetRunId) {
    params.set("geo_run_id", state.selectedGeoAssetRunId);
  }
  return params.toString();
}

function buildBrowserSamplingPackExportQuery() {
  const params = new URLSearchParams({
    district: state.districtFilter,
    min_yield: String(state.minYield),
    max_budget: String(state.maxBudget),
    min_samples: String(state.minSamples),
    limit: String(Math.max(getBrowserSamplingPackItems().length, 12))
  });
  return params.toString();
}

function buildGeoWorkOrderExportQuery() {
  const params = new URLSearchParams({
    district: state.districtFilter,
    limit: String(Math.max(getGeoWorkOrderItems().length, 12))
  });
  if (state.selectedGeoAssetRunId) {
    params.set("geo_run_id", state.selectedGeoAssetRunId);
  }
  if (state.geoWorkOrderStatusFilter && state.geoWorkOrderStatusFilter !== "all") {
    params.set("status", state.geoWorkOrderStatusFilter);
  }
  if (state.geoWorkOrderAssigneeFilter && state.geoWorkOrderAssigneeFilter !== "all") {
    params.set("assignee", state.geoWorkOrderAssigneeFilter);
  }
  return params.toString();
}


function buildFloorWatchlistExportFilename(extension) {
  const currentBatchName = state.selectedImportRunDetail?.batchName ?? state.selectedImportRunId ?? "latest";
  const baselineBatchName = state.selectedImportRunDetail?.comparison?.baselineBatchName ?? state.selectedBaselineRunId ?? null;
  const currentSlug = slugifyExportName(currentBatchName, "latest");
  const baselineSlug = baselineBatchName ? `-vs-${slugifyExportName(baselineBatchName, "baseline")}` : "";
  return `shanghai-floor-watchlist-${currentSlug}${baselineSlug}.${extension}`;
}

function buildGeoTaskWatchlistExportFilename(extension) {
  const currentBatchName = state.selectedGeoAssetRunDetail?.batchName ?? state.selectedGeoAssetRunId ?? "latest-geo";
  const currentSlug = slugifyExportName(currentBatchName, "latest-geo");
  return `shanghai-geo-task-watchlist-${currentSlug}.${extension}`;
}

function buildBrowserSamplingPackExportFilename(extension) {
  const importBatchName = state.selectedImportRunDetail?.batchName ?? state.selectedImportRunId ?? "latest-browser-pack";
  const currentSlug = slugifyExportName(importBatchName, "latest-browser-pack");
  const districtSlug = state.districtFilter && state.districtFilter !== "all" ? `-${slugifyExportName(state.districtFilter, "district")}` : "";
  return `shanghai-browser-sampling-pack-${currentSlug}${districtSlug}.${extension}`;
}

function buildGeoWorkOrderExportFilename(extension) {
  const currentBatchName = state.selectedGeoAssetRunDetail?.batchName ?? state.selectedGeoAssetRunId ?? "latest-geo";
  const currentSlug = slugifyExportName(currentBatchName, "latest-geo");
  const statusSlug =
    state.geoWorkOrderStatusFilter && state.geoWorkOrderStatusFilter !== "all"
      ? `-${slugifyExportName(state.geoWorkOrderStatusFilter, "status")}`
      : "";
  const assigneeSlug =
    state.geoWorkOrderAssigneeFilter && state.geoWorkOrderAssigneeFilter !== "all"
      ? `-${slugifyExportName(state.geoWorkOrderAssigneeFilter, "assignee")}`
      : "";
  return `shanghai-geo-work-orders-${currentSlug}${statusSlug}${assigneeSlug}.${extension}`;
}

async function exportWithFallback(endpoint, filename, fallbackBuilder, mimeType, queryString = buildExportQuery()) {
  try {
    const response = await fetch(`${endpoint}?${queryString}`);
    if (!response.ok) {
      throw new Error(`Export failed with ${response.status}`);
    }
    const blob = await response.blob();
    downloadBlob(filename, blob);
    return "server";
  } catch (error) {
    downloadFile(filename, fallbackBuilder(), mimeType);
    return "fallback";
  }
}



function escapeXml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function downloadFile(filename, content, mimeType = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type: mimeType });
  downloadBlob(filename, blob);
}

function downloadBlob(filename, blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function reportBootError(error) {
  const message = error?.message || String(error || "Unknown init error");
  window.__atlasBootError = {
    message,
    stack: error?.stack || null,
    at: new Date().toISOString()
  };
  console.error("Atlas init failed:", error);
  if (mapModeBadge) {
    mapModeBadge.textContent = "Init Error";
  }
  if (mapNote) {
    mapNote.textContent = `前端初始化失败：${message}`;
  }
}

Promise.resolve(init()).catch(reportBootError);
