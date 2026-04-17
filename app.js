const fallbackDistricts = [
  {
    id: "pudong",
    name: "浦东新区",
    short: "浦东",
    yield: 2.82,
    budget: 1180,
    rent: 16250,
    saleSample: 82,
    rentSample: 67,
    score: 91,
    trend: "+0.21%",
    labelX: 555,
    labelY: 224,
    polygon: "430,85 620,60 710,120 705,235 642,298 640,412 532,470 470,380 470,290 420,220",
    communities: [
      {
        id: "zhangjiang-park",
        name: "张江汤臣豪园",
        districtId: "pudong",
        x: 548,
        y: 188,
        avgPriceWan: 980,
        monthlyRent: 16500,
        yield: 2.86,
        score: 94,
        sample: 28,
        buildingCount: 7,
        buildingFocus: "5号楼",
        note: "地铁与产业园双重支撑，租金黏性强，楼层价差相对温和。",
        buildings: [
          { name: "2号楼", totalFloors: 18, low: 2.61, mid: 2.74, high: 2.58, score: 80 },
          { name: "5号楼", totalFloors: 24, low: 2.78, mid: 2.92, high: 3.08, score: 94 },
          { name: "7号楼", totalFloors: 22, low: 2.73, mid: 2.81, high: 2.77, score: 86 }
        ]
      },
      {
        id: "lianyang-city",
        name: "联洋年华",
        districtId: "pudong",
        x: 598,
        y: 232,
        avgPriceWan: 1260,
        monthlyRent: 17800,
        yield: 2.41,
        score: 73,
        sample: 24,
        buildingCount: 5,
        buildingFocus: "3栋",
        note: "总价抬升明显，适合作为高净值长持标的，不是当前套利主战场。",
        buildings: [
          { name: "1栋", totalFloors: 16, low: 2.22, mid: 2.35, high: 2.27, score: 66 },
          { name: "3栋", totalFloors: 18, low: 2.34, mid: 2.44, high: 2.49, score: 73 },
          { name: "5栋", totalFloors: 18, low: 2.29, mid: 2.41, high: 2.36, score: 70 }
        ]
      },
      {
        id: "biyun-mansion",
        name: "碧云天第",
        districtId: "pudong",
        x: 522,
        y: 275,
        avgPriceWan: 890,
        monthlyRent: 14900,
        yield: 2.67,
        score: 88,
        sample: 21,
        buildingCount: 4,
        buildingFocus: "B座",
        note: "外籍租客占比较高，空置波动要单独折现。",
        buildings: [
          { name: "A座", totalFloors: 14, low: 2.46, mid: 2.61, high: 2.57, score: 79 },
          { name: "B座", totalFloors: 20, low: 2.58, mid: 2.76, high: 2.83, score: 88 },
          { name: "C座", totalFloors: 16, low: 2.44, mid: 2.51, high: 2.47, score: 74 }
        ]
      }
    ]
  },
  {
    id: "minhang",
    name: "闵行区",
    short: "闵行",
    yield: 2.66,
    budget: 760,
    rent: 10450,
    saleSample: 69,
    rentSample: 55,
    score: 87,
    trend: "+0.17%",
    labelX: 320,
    labelY: 360,
    polygon: "120,278 240,248 360,255 448,325 418,442 310,482 205,468 118,398",
    communities: [
      {
        id: "qibao-yunting",
        name: "七宝云庭",
        districtId: "minhang",
        x: 266,
        y: 335,
        avgPriceWan: 650,
        monthlyRent: 11800,
        yield: 2.91,
        score: 92,
        sample: 30,
        buildingCount: 6,
        buildingFocus: "9幢",
        note: "低总价高出租活跃度，适合 MVP 试点。",
        buildings: [
          { name: "3幢", totalFloors: 12, low: 2.63, mid: 2.75, high: 2.71, score: 83 },
          { name: "9幢", totalFloors: 18, low: 2.84, mid: 2.96, high: 3.04, score: 92 },
          { name: "11幢", totalFloors: 18, low: 2.67, mid: 2.79, high: 2.83, score: 86 }
        ]
      },
      {
        id: "xinzhuang-hub",
        name: "莘庄都会里",
        districtId: "minhang",
        x: 340,
        y: 385,
        avgPriceWan: 580,
        monthlyRent: 9800,
        yield: 2.69,
        score: 85,
        sample: 26,
        buildingCount: 5,
        buildingFocus: "2号楼",
        note: "交通枢纽优势明显，但房龄带来部分维护折价。",
        buildings: [
          { name: "2号楼", totalFloors: 14, low: 2.62, mid: 2.75, high: 2.81, score: 85 },
          { name: "4号楼", totalFloors: 12, low: 2.51, mid: 2.59, high: 2.56, score: 78 },
          { name: "8号楼", totalFloors: 16, low: 2.44, mid: 2.63, high: 2.66, score: 81 }
        ]
      }
    ]
  },
  {
    id: "xuhui",
    name: "徐汇区",
    short: "徐汇",
    yield: 2.18,
    budget: 1380,
    rent: 17100,
    saleSample: 58,
    rentSample: 48,
    score: 64,
    trend: "-0.06%",
    labelX: 238,
    labelY: 220,
    polygon: "164,118 274,98 346,126 350,248 246,250 162,206",
    communities: [
      {
        id: "xujiahui-view",
        name: "徐家汇公馆",
        districtId: "xuhui",
        x: 252,
        y: 176,
        avgPriceWan: 1580,
        monthlyRent: 18600,
        yield: 1.89,
        score: 58,
        sample: 18,
        buildingCount: 3,
        buildingFocus: "1栋",
        note: "自住属性更强，作为对照区很有价值。",
        buildings: [
          { name: "1栋", totalFloors: 20, low: 1.81, mid: 1.92, high: 1.98, score: 58 },
          { name: "2栋", totalFloors: 16, low: 1.78, mid: 1.84, high: 1.79, score: 53 }
        ]
      }
    ]
  },
  {
    id: "yangpu",
    name: "杨浦区",
    short: "杨浦",
    yield: 2.54,
    budget: 920,
    rent: 13300,
    saleSample: 51,
    rentSample: 42,
    score: 79,
    trend: "+0.09%",
    labelX: 392,
    labelY: 144,
    polygon: "348,84 452,90 514,140 478,230 386,214 350,154",
    communities: [
      {
        id: "wujiaochang-one",
        name: "五角场壹里",
        districtId: "yangpu",
        x: 410,
        y: 156,
        avgPriceWan: 880,
        monthlyRent: 13600,
        yield: 2.46,
        score: 76,
        sample: 22,
        buildingCount: 4,
        buildingFocus: "6幢",
        note: "学区与商圈双属性，挂牌会有情绪溢价。",
        buildings: [
          { name: "2幢", totalFloors: 18, low: 2.29, mid: 2.41, high: 2.35, score: 71 },
          { name: "6幢", totalFloors: 24, low: 2.38, mid: 2.54, high: 2.62, score: 76 }
        ]
      }
    ]
  },
  {
    id: "jingan",
    name: "静安区",
    short: "静安",
    yield: 2.04,
    budget: 1460,
    rent: 18200,
    saleSample: 44,
    rentSample: 39,
    score: 59,
    trend: "-0.04%",
    labelX: 300,
    labelY: 142,
    polygon: "240,82 344,82 346,152 264,168 226,126",
    communities: [
      {
        id: "jingan-park",
        name: "静安府",
        districtId: "jingan",
        x: 292,
        y: 122,
        avgPriceWan: 1720,
        monthlyRent: 19500,
        yield: 1.81,
        score: 51,
        sample: 12,
        buildingCount: 2,
        buildingFocus: "A座",
        note: "绝对值贵，更多作为市场锚点，而非收益套利样本。",
        buildings: [
          { name: "A座", totalFloors: 20, low: 1.75, mid: 1.84, high: 1.88, score: 51 }
        ]
      }
    ]
  },
  {
    id: "putuo",
    name: "普陀区",
    short: "普陀",
    yield: 2.38,
    budget: 790,
    rent: 10800,
    saleSample: 49,
    rentSample: 43,
    score: 74,
    trend: "+0.05%",
    labelX: 176,
    labelY: 156,
    polygon: "92,116 218,88 246,148 216,238 118,252 84,182",
    communities: [
      {
        id: "zhenru-harbor",
        name: "真如港湾",
        districtId: "putuo",
        x: 164,
        y: 176,
        avgPriceWan: 710,
        monthlyRent: 11100,
        yield: 2.53,
        score: 77,
        sample: 19,
        buildingCount: 3,
        buildingFocus: "7号楼",
        note: "适合做中等预算样本池，租金相对稳定。",
        buildings: [
          { name: "1号楼", totalFloors: 14, low: 2.39, mid: 2.47, high: 2.44, score: 70 },
          { name: "7号楼", totalFloors: 18, low: 2.45, mid: 2.58, high: 2.63, score: 77 }
        ]
      }
    ]
  },
  {
    id: "changning",
    name: "长宁区",
    short: "长宁",
    yield: 2.21,
    budget: 1050,
    rent: 15200,
    saleSample: 42,
    rentSample: 35,
    score: 68,
    trend: "+0.02%",
    labelX: 132,
    labelY: 238,
    polygon: "70,216 162,202 198,246 174,326 88,334 52,274",
    communities: [
      {
        id: "gubei-center",
        name: "古北中心",
        districtId: "changning",
        x: 132,
        y: 264,
        avgPriceWan: 1020,
        monthlyRent: 14800,
        yield: 2.05,
        score: 61,
        sample: 16,
        buildingCount: 2,
        buildingFocus: "4幢",
        note: "国际社区租客结构好，但总价高导致回报率偏保守。",
        buildings: [
          { name: "4幢", totalFloors: 18, low: 1.96, mid: 2.08, high: 2.11, score: 61 }
        ]
      }
    ]
  },
  {
    id: "baoshan",
    name: "宝山区",
    short: "宝山",
    yield: 2.72,
    budget: 530,
    rent: 7900,
    saleSample: 47,
    rentSample: 37,
    score: 83,
    trend: "+0.14%",
    labelX: 526,
    labelY: 100,
    polygon: "456,20 612,16 676,78 620,126 522,138 452,94",
    communities: [
      {
        id: "gongkang-hill",
        name: "共康新城",
        districtId: "baoshan",
        x: 542,
        y: 90,
        avgPriceWan: 460,
        monthlyRent: 8600,
        yield: 2.98,
        score: 90,
        sample: 25,
        buildingCount: 5,
        buildingFocus: "12幢",
        note: "低总价 + 交通改善预期，适合打榜。",
        buildings: [
          { name: "6幢", totalFloors: 11, low: 2.77, mid: 2.85, high: 2.81, score: 82 },
          { name: "12幢", totalFloors: 18, low: 2.86, mid: 3.01, high: 3.12, score: 90 }
        ]
      }
    ]
  }
];

const fallbackPipelineSteps = [
  {
    title: "采集层",
    description: "安居客 / 贝壳出售与出租房源，保留原始文本、原始坐标、抓取时间与页面快照。",
    meta: "raw_listings_sale / raw_listings_rent"
  },
  {
    title: "标准化层",
    description: "做小区别名归一、楼栋文本抽取、楼层解析与价格单位统一，生成标准实体。",
    meta: "community_aliases / listing_normalized"
  },
  {
    title: "去重层",
    description: "按面积、楼层、朝向、价格接近度进行跨平台聚类，产出去重组与置信度。",
    meta: "listing_dedup_groups"
  },
  {
    title: "空间层",
    description: "内部保留 GCJ-02 与 WGS-84 双字段，前端与 Google Earth 各取所需。",
    meta: "communities / buildings / geom"
  },
  {
    title: "指标层",
    description: "按小区、楼栋、楼层桶计算租售比、年化回报率、样本量与机会评分。",
    meta: "metrics_community / metrics_building_floor"
  }
];

const fallbackSchemas = [
  {
    name: "communities",
    description: "小区维表，存小区名、别名、板块、中心点和 polygon。",
    fields: "community_id, district_id, aliases_json, centroid, polygon_geojson"
  },
  {
    name: "buildings",
    description: "楼栋实体，关联小区、楼栋号、总层数和空间几何。",
    fields: "building_id, community_id, building_no, total_floors, geom"
  },
  {
    name: "listings_sale",
    description: "在售房源事实表，保留源字段与标准化字段并行。",
    fields: "source_listing_id, raw_address, floor_no, area_sqm, price_total_wan"
  },
  {
    name: "listings_rent",
    description: "出租房源事实表，用于年租金回报率和空置波动分析。",
    fields: "source_listing_id, monthly_rent, floor_no, orientation, published_at"
  },
  {
    name: "metrics_building_floor",
    description: "楼栋 + 楼层桶指标快照，用于地图弹窗和机会榜排序。",
    fields: "building_id, floor_bucket, yield_pct, rent_sale_ratio, sample_size, score"
  }
];

const fallbackOperationsOverview = {
  summary: {
    sourceCount: 5,
    readySourceCount: 4,
    resolvedQueueCount: 3,
    reviewQueueCount: 2,
    matchingQueueCount: 1,
    avgNormalizationPct: 84.6,
    importRunCount: 1,
    geoAssetRunCount: 1,
    geoAssetCoveragePct: 100,
    geoAssetOpenTaskCount: 15
  },
  sourceHealth: [
    {
      sourceId: "beike-open-platform",
      name: "贝壳开放平台",
      status: "ready_for_integration",
      freshness: "T-1",
      coveragePct: 78,
      listingCount: 326,
      normalizationPct: 88,
      note: "OAuth 与字段映射位已预留，适合做主商业源。"
    },
    {
      sourceId: "58-anjuke-platform",
      name: "58 / 安居客开放体系",
      status: "partner_negotiation",
      freshness: "T-2",
      coveragePct: 64,
      listingCount: 214,
      normalizationPct: 72,
      note: "字段一致性需要更强的地址归一与去重。"
    },
    {
      sourceId: "shanghai-open-data-community",
      name: "上海开放数据 · 物业小区信息",
      status: "online",
      freshness: "weekly",
      coveragePct: 92,
      listingCount: 128,
      normalizationPct: 96,
      note: "适合做小区字典底座和别名归一。"
    },
    {
      sourceId: "authorized-batch-import",
      name: "授权批次导入",
      status: "online",
      freshness: "on_demand",
      coveragePct: 58,
      listingCount: 48,
      normalizationPct: 84,
      note: "适合先跑小批量授权数据、地址复核和逐层证据验证。"
    },
    {
      sourceId: "amap-aoi-poi",
      name: "高德 AOI / POI / District",
      status: "online",
      freshness: "realtime",
      coveragePct: 81,
      listingCount: 96,
      normalizationPct: 83,
      note: "适合补全 AOI、行政区边界与地图增强。"
    }
  ],
  addressQueue: [
    {
      queueId: "addr-001",
      communityId: "zhangjiang-park",
      buildingNo: "5号楼",
      buildingId: "zhangjiang-park-b2",
      floorNo: 17,
      sourceId: "beike-open-platform",
      rawAddress: "浦东新区张江路xx弄5号楼17层1702",
      normalizedPath: "浦东新区 / 张江汤臣豪园 / 5号楼 / 2单元 / 17层 / 1702",
      status: "resolved",
      confidence: 0.96,
      lastActionAt: "2026-04-11 09:18",
      reviewHint: "已匹配楼栋号与楼层，自动进入指标层。"
    },
    {
      queueId: "addr-002",
      communityId: "zhangjiang-park",
      buildingNo: "5号楼",
      buildingId: "zhangjiang-park-b2",
      floorNo: 24,
      sourceId: "58-anjuke-platform",
      rawAddress: "张江汤臣豪园5号楼顶层复式",
      normalizedPath: "浦东新区 / 张江汤臣豪园 / 5号楼 / 待识别单元 / 24层",
      status: "needs_review",
      confidence: 0.79,
      lastActionAt: "2026-04-11 08:42",
      reviewHint: "缺少单元号，建议结合 AOI 和人工校正补齐。"
    },
    {
      queueId: "addr-003",
      communityId: "qibao-yunting",
      buildingNo: "9幢",
      buildingId: "qibao-yunting-b2",
      floorNo: 12,
      sourceId: "beike-open-platform",
      rawAddress: "七宝云庭9幢12楼1201",
      normalizedPath: "闵行区 / 七宝云庭 / 9幢 / 1单元 / 12层 / 1201",
      status: "resolved",
      confidence: 0.94,
      lastActionAt: "2026-04-11 07:55",
      reviewHint: "命中楼栋别名表，已完成标准化。"
    },
    {
      queueId: "addr-004",
      communityId: "gongkang-hill",
      buildingNo: "12幢",
      buildingId: "gongkang-hill-b2",
      floorNo: 18,
      sourceId: "58-anjuke-platform",
      rawAddress: "共康新城十二幢18F",
      normalizedPath: "宝山区 / 共康新城 / 12幢 / 待识别单元 / 18层",
      status: "matching",
      confidence: 0.84,
      lastActionAt: "2026-04-11 10:06",
      reviewHint: "楼栋已识别，正在等待单元侧补全。"
    },
    {
      queueId: "addr-006",
      communityId: "qibao-yunting",
      buildingNo: "9幢",
      buildingId: "qibao-yunting-b2",
      floorNo: 15,
      sourceId: "authorized-batch-import",
      rawAddress: "闵行区七宝云庭9幢高楼层样本",
      normalizedPath: "闵行区 / 七宝云庭 / 9幢 / 1单元 / 15层",
      status: "needs_review",
      confidence: 0.81,
      lastActionAt: "2026-04-11 20:38",
      reviewHint: "来自授权 CSV，高楼层被折算为 15 层，建议人工复核。",
      runId: "pudong-demo-2026-04-11-20260411222040",
      batchName: "pudong-demo-2026-04-11"
    }
  ],
  anchorWatchlist: [],
  importRuns: [
    {
      runId: "pudong-demo-2026-04-11-20260411222040",
      providerId: "beike-open-platform",
      batchName: "pudong-demo-2026-04-11",
      createdAt: "2026-04-11T22:20:40+08:00",
      resolvedRate: 0.75,
      resolvedCount: 6,
      reviewCount: 2,
      matchingCount: 0,
      pairCount: 4,
      evidenceCount: 4
    }
  ],
  geoAssetRuns: [
    {
      runId: "demo-building-footprints-baseline-20260411183000",
      providerId: "amap-aoi-poi",
      batchName: "demo-building-footprints-baseline",
      assetType: "building_footprint",
      createdAt: "2026-04-11T18:30:00+08:00",
      featureCount: 5,
      resolvedBuildingCount: 4,
      unresolvedFeatureCount: 1,
      communityCount: 2,
      coveragePct: 80,
      taskCount: 18,
      openTaskCount: 18,
      reviewTaskCount: 1,
      captureTaskCount: 17
    },
    {
      runId: "demo-building-footprints-20260412110000",
      providerId: "amap-aoi-poi",
      batchName: "demo-building-footprints",
      assetType: "building_footprint",
      createdAt: "2026-04-12T11:00:00+08:00",
      featureCount: 6,
      resolvedBuildingCount: 6,
      unresolvedFeatureCount: 0,
      communityCount: 2,
      coveragePct: 100,
      taskCount: 15,
      openTaskCount: 15,
      reviewTaskCount: 0,
      captureTaskCount: 15
    }
  ]
};

const emptyOperationsOverview = {
  summary: {
    sourceCount: 0,
    readySourceCount: 0,
    resolvedQueueCount: 0,
    reviewQueueCount: 0,
    matchingQueueCount: 0,
    avgNormalizationPct: 0,
    referenceRunCount: 0,
    importRunCount: 0,
    geoAssetRunCount: 0,
    metricsRunCount: 0,
    activeDataMode: "empty",
    mockEnabled: false,
    hasRealData: false,
    databaseConnected: false,
    databaseReadable: false,
    databaseSeeded: false,
    latestBootstrapAt: null,
    databaseCommunityCount: 0,
    databaseBuildingCount: 0,
    databaseSaleListingCount: 0,
    databaseRentListingCount: 0,
    databaseGeoAssetCount: 0,
    cityCoveragePct: 0,
    buildingCoveragePct: 0,
    sampleFreshness: null,
    latestSuccessfulRunAt: null,
    latestReferencePersistAt: null,
    latestImportPersistAt: null,
    latestGeoPersistAt: null,
    latestMetricsRefreshAt: null,
    latestMetricsRunAt: null,
    geoAssetCoveragePct: 0,
    geoAssetOpenTaskCount: 0,
    geoAssetCriticalTaskCount: 0,
    geoAssetWatchlistLinkedTaskCount: 0,
    browserSamplingTaskCount: 0,
    priorityBrowserSamplingTaskCount: 0,
    browserCaptureRunCount: 0,
    latestBrowserCaptureAt: null,
    browserCaptureAttentionCount: 0,
    pendingAnchorCount: 0,
    candidateBackedAnchorCount: 0,
    latestAnchorReviewAt: null
  },
  runtime: null,
  sourceHealth: [],
  addressQueue: [],
  anchorWatchlist: [],
  browserSamplingPack: [],
  browserCaptureRuns: [],
  referenceRuns: [],
  importRuns: [],
  metricsRuns: [],
  geoAssetRuns: []
};

let districts = [];
let mapCommunities = [];
let pipelineSteps = [];
let schemas = [];
let systemStrategy = null;
let dataSources = [];
let operationsOverview = emptyOperationsOverview;
let runtimeConfig = {
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

const state = {
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
  selectedImportRunId: null,
  selectedBaselineRunId: null,
  selectedGeoAssetRunId: null,
  selectedGeoBaselineRunId: null,
  selectedGeoTaskId: null,
  geoWorkOrderStatusFilter: "all",
  geoWorkOrderAssigneeFilter: "all",
  summary: null,
  opportunityItems: [],
  floorWatchlistItems: [],
  floorWatchlistLoading: false,
  browserSamplingPackItems: [],
  mobileInspectorPanel: "detail",
  selectedBrowserSamplingTaskId: null,
  selectedCommunityDetail: null,
  selectedBuildingDetail: null,
  selectedFloorDetail: null,
  selectedImportRunDetail: null,
  selectedGeoAssetRunDetail: null,
  selectedBrowserCaptureRunId: null,
  selectedBrowserCaptureRunDetail: null,
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
  busyAnchorCommunityId: null,
  busyGeoPersistRunId: null,
  busyGeoTaskId: null,
  busyGeoWorkOrderTaskId: null,
  busyGeoWorkOrderId: null,
  busyBrowserSamplingSubmit: false,
  busyBrowserCaptureRunId: null,
  lastBrowserCaptureSubmission: null,
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

function canUseDemoFallback() {
  return Boolean(runtimeConfig?.mockEnabled);
}

function currentDataMode() {
  return runtimeConfig?.activeDataMode ?? operationsOverview?.summary?.activeDataMode ?? "empty";
}

function applyDataModeDefaults() {
  const usingLegacyDefaults = state.minYield === 2.4 && state.maxBudget === 1200 && state.minSamples === 20;
  if (!usingLegacyDefaults) {
    return;
  }
  if (currentDataMode() === "staged" || currentDataMode() === "empty") {
    state.minYield = 0;
    state.maxBudget = 10000;
    state.minSamples = 1;
  }
}

function effectiveOperationsOverview() {
  return operationsOverview ?? emptyOperationsOverview;
}

const districtFilter = document.querySelector("#districtFilter");
const minYieldFilter = document.querySelector("#minYieldFilter");
const maxBudgetFilter = document.querySelector("#maxBudgetFilter");
const minSamplesFilter = document.querySelector("#minSamplesFilter");
const minYieldValue = document.querySelector("#minYieldValue");
const maxBudgetValue = document.querySelector("#maxBudgetValue");
const minSamplesValue = document.querySelector("#minSamplesValue");
const researchSearchInput = document.querySelector("#researchSearchInput");
const researchSearchResults = document.querySelector("#researchSearchResults");
const searchClearButton = document.querySelector("#searchClearButton");
const globalFeedback = document.querySelector("#globalFeedback");
const summaryGrid = document.querySelector("#summaryGrid");
const amapContainer = document.querySelector("#amapContainer");
const mapWaypointBadge = document.querySelector("#mapWaypointBadge");
const mapModeBadge = document.querySelector("#mapModeBadge");
const mapNote = document.querySelector("#mapNote");
const detailCard = document.querySelector("#detailCard");
const rankingList = document.querySelector("#rankingList");
const rankingCount = document.querySelector("#rankingCount");
const floorWatchlist = document.querySelector("#floorWatchlist");
const floorWatchlistCount = document.querySelector("#floorWatchlistCount");
const geoTaskWatchlist = document.querySelector("#geoTaskWatchlist");
const geoTaskWatchlistCount = document.querySelector("#geoTaskWatchlistCount");
const browserSamplingPack = document.querySelector("#browserSamplingPack");
const browserSamplingPackCount = document.querySelector("#browserSamplingPackCount");
const exportFloorWatchlistKmlButton = document.querySelector("#exportFloorWatchlistKmlButton");
const exportFloorWatchlistGeoJsonButton = document.querySelector("#exportFloorWatchlistGeoJsonButton");
const exportGeoTaskWatchlistGeoJsonButton = document.querySelector("#exportGeoTaskWatchlistGeoJsonButton");
const exportGeoTaskWatchlistCsvButton = document.querySelector("#exportGeoTaskWatchlistCsvButton");
const exportBrowserSamplingPackCsvButton = document.querySelector("#exportBrowserSamplingPackCsvButton");
const matrixTable = document.querySelector("#matrixTable");
const matrixTitle = document.querySelector("#matrixTitle");
const mapFrame = document.querySelector(".map-frame");
const pipeline = document.querySelector("#pipeline");
const schemaList = document.querySelector("#schemaList");
const strategyPanel = document.querySelector("#strategyPanel");
const dataSourceList = document.querySelector("#dataSourceList");
const opsSummary = document.querySelector("#opsSummary");
const referenceRunList = document.querySelector("#referenceRunList");
const importRunList = document.querySelector("#importRunList");
const metricsRunList = document.querySelector("#metricsRunList");
const geoAssetRunList = document.querySelector("#geoAssetRunList");
const geoAssetRunDetail = document.querySelector("#geoAssetRunDetail");
const importRunDetail = document.querySelector("#importRunDetail");
const sourceHealthList = document.querySelector("#sourceHealthList");
const browserSamplingWorkbench = document.querySelector("#browserSamplingWorkbench");
const browserSamplingCoverageBoard = document.querySelector("#browserSamplingCoverageBoard");
const addressQueueList = document.querySelector("#addressQueueList");
const anchorWatchlist = document.querySelector("#anchorWatchlist");
const floorEvidence = document.querySelector("#floorEvidence");
const exportKmlButton = document.querySelector("#exportKmlButton");
const exportGeoJsonButton = document.querySelector("#exportGeoJsonButton");
const granularityGroup = document.querySelector("#granularityGroup");
const inspectorToggleButtons = document.querySelectorAll("[data-inspector-toggle]");

function hydrateDistrictsPayload(rawDistricts) {
  return (rawDistricts ?? []).map((district) => ({
    ...district,
    communities: (district.communities ?? []).map(hydrateCommunity)
  }));
}

function hydrateCommunity(community) {
  const buildings = (community.buildings ?? []).map((building, index) => hydrateBuilding(community, building, index));
  const focusMatch = buildings.find((building) => building.name === community.buildingFocus);
  return {
    ...community,
    centerLng: community.centerLng ?? community.center_lng ?? null,
    centerLat: community.centerLat ?? community.center_lat ?? null,
    anchorSource: community.anchorSource ?? community.anchor_source ?? null,
    anchorQuality: community.anchorQuality ?? community.anchor_quality ?? null,
    previewCenterLng: community.previewCenterLng ?? community.preview_center_lng ?? null,
    previewCenterLat: community.previewCenterLat ?? community.preview_center_lat ?? null,
    previewAnchorSource: community.previewAnchorSource ?? community.preview_anchor_source ?? null,
    previewAnchorQuality: community.previewAnchorQuality ?? community.preview_anchor_quality ?? null,
    previewAnchorName: community.previewAnchorName ?? community.preview_anchor_name ?? null,
    previewAnchorAddress: community.previewAnchorAddress ?? community.preview_anchor_address ?? null,
    anchorDecisionState: community.anchorDecisionState ?? community.anchor_decision_state ?? null,
    latestAnchorReview: community.latestAnchorReview ?? community.latest_anchor_review ?? null,
    sampleStatus: community.sampleStatus ?? community.sample_status ?? (community.sample > 0 ? "active_metrics" : "dictionary_only"),
    sampleStatusLabel: community.sampleStatusLabel ?? community.sample_status_label ?? "状态待补",
    buildings,
    primaryBuildingId: community.primaryBuildingId ?? focusMatch?.id ?? buildings[0]?.id ?? null
  };
}

function hydrateBuilding(community, building, index = 0) {
  const buildingId = building.id ?? `${community.id}-b${index + 1}`;
  const yieldAvg = Number((((building.low ?? 0) + (building.mid ?? 0) + (building.high ?? 0)) / 3).toFixed(2));
  const floorPairs = [
    ["low", building.low ?? 0],
    ["mid", building.mid ?? 0],
    ["high", building.high ?? 0]
  ];
  floorPairs.sort((left, right) => right[1] - left[1]);
  return {
    ...building,
    id: buildingId,
    sequenceNo: building.sequenceNo ?? index + 1,
    communityId: building.communityId ?? community.id,
    communityName: building.communityName ?? community.name,
    districtId: building.districtId ?? community.districtId,
    districtName: building.districtName ?? community.districtName,
    yieldAvg: building.yieldAvg ?? yieldAvg,
    bestBucket: building.bestBucket ?? floorPairs[0][0]
  };
}

function districtDirectory() {
  const directory = new Map();
  districts.forEach((district) => {
    directory.set(district.id, { id: district.id, name: district.name, short: district.short });
  });
  mapCommunities.forEach((community) => {
    if (!directory.has(community.districtId)) {
      directory.set(community.districtId, {
        id: community.districtId,
        name: community.districtName ?? community.districtId,
        short: community.districtShort ?? community.districtName ?? community.districtId
      });
    }
  });
  return Array.from(directory.values()).sort((left, right) => left.id.localeCompare(right.id, "zh-Hans-CN"));
}

function communityCenter(community) {
  if (community?.centerLng != null && community?.centerLat != null) {
    return [Number(community.centerLng), Number(community.centerLat)];
  }
  return normalizeSvgToLonLat(community?.x ?? 380, community?.y ?? 260);
}

function communityAnchorPreview(community) {
  if (!community || community.centerLng != null || community.centerLat != null) {
    return null;
  }
  if (community.previewCenterLng != null && community.previewCenterLat != null) {
    return {
      centerLng: Number(community.previewCenterLng),
      centerLat: Number(community.previewCenterLat),
      anchorSource: community.previewAnchorSource ?? "candidate_preview",
      anchorQuality: community.previewAnchorQuality ?? null,
      anchorName: community.previewAnchorName ?? community.candidateSuggestions?.[0]?.name ?? null,
      anchorAddress: community.previewAnchorAddress ?? community.candidateSuggestions?.[0]?.address ?? null
    };
  }
  return null;
}

function anchorDecisionLabel(value) {
  return {
    pending: "待确认",
    confirmed: "已确认",
    manual_override: "手工覆盖"
  }[value] ?? "待确认";
}

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
  void initializeMapExperience()
    .then(() => {
      render();
      scheduleUiHydrationRetry();
    })
    .catch(() => {
      render();
      scheduleUiHydrationRetry();
    });
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
  } catch (error) {
    operationsOverview = canUseDemoFallback() ? fallbackOperationsOverview : emptyOperationsOverview;
  }
}

async function refreshOperationsWorkbench({ reloadFloor = false } = {}) {
  await loadOperationsOverview();
  ensureImportRunSelection();
  ensureGeoAssetRunSelection();
  if (
    state.selectedBrowserCaptureRunId &&
    !(effectiveOperationsOverview().browserCaptureRuns ?? []).some((item) => item.runId === state.selectedBrowserCaptureRunId)
  ) {
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
  }
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

function ensureImportRunSelection() {
  const importRuns = effectiveOperationsOverview().importRuns ?? [];
  if (!importRuns.length) {
    state.selectedImportRunId = null;
    state.selectedBaselineRunId = null;
    state.selectedImportRunDetail = null;
    return;
  }
  if (!importRuns.some((item) => item.runId === state.selectedImportRunId)) {
    state.selectedImportRunId = importRuns[0].runId;
    state.selectedBaselineRunId = null;
  }
  if (state.selectedBaselineRunId) {
    const selectedRun = importRuns.find((item) => item.runId === state.selectedImportRunId);
    const baselineRun = importRuns.find((item) => item.runId === state.selectedBaselineRunId);
    if (
      !selectedRun ||
      !baselineRun ||
      baselineRun.runId === selectedRun.runId ||
      (baselineRun.createdAt || "") >= (selectedRun.createdAt || "")
    ) {
      state.selectedBaselineRunId = null;
    }
  }
}

function ensureGeoAssetRunSelection() {
  const geoAssetRuns = effectiveOperationsOverview().geoAssetRuns ?? [];
  if (!geoAssetRuns.length) {
    state.selectedGeoAssetRunId = null;
    state.selectedGeoBaselineRunId = null;
    state.selectedGeoAssetRunDetail = null;
    return;
  }
  if (!geoAssetRuns.some((item) => item.runId === state.selectedGeoAssetRunId)) {
    state.selectedGeoAssetRunId = geoAssetRuns[0].runId;
  }
  if (state.selectedGeoBaselineRunId) {
    const selectedRun = geoAssetRuns.find((item) => item.runId === state.selectedGeoAssetRunId);
    const baselineRun = geoAssetRuns.find((item) => item.runId === state.selectedGeoBaselineRunId);
    if (
      !selectedRun ||
      !baselineRun ||
      baselineRun.runId === selectedRun.runId ||
      baselineRun.providerId !== selectedRun.providerId ||
      baselineRun.assetType !== selectedRun.assetType ||
      (baselineRun.createdAt || "") >= (selectedRun.createdAt || "")
    ) {
      state.selectedGeoBaselineRunId = null;
    }
  }
}

function normalizeGeoWorkOrderFilters() {
  const items = state.selectedGeoAssetRunDetail?.workOrders ?? [];
  const assignees = new Set(
    items
      .map((item) => (item.assignee ?? "").trim())
      .filter((value) => value)
  );
  const validStatuses = new Set(["all", "open", "assigned", "in_progress", "delivered", "closed"]);
  if (!validStatuses.has(state.geoWorkOrderStatusFilter)) {
    state.geoWorkOrderStatusFilter = "all";
  }
  if (state.geoWorkOrderAssigneeFilter !== "all" && !assignees.has(state.geoWorkOrderAssigneeFilter)) {
    state.geoWorkOrderAssigneeFilter = "all";
  }
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

function availableGeoBaselineRunsFor(runId) {
  const geoAssetRuns = effectiveOperationsOverview().geoAssetRuns ?? [];
  const selectedRun = geoAssetRuns.find((item) => item.runId === runId);
  if (!selectedRun) {
    return [];
  }
  return geoAssetRuns.filter(
    (item) =>
      item.runId !== runId &&
      item.providerId === selectedRun.providerId &&
      item.assetType === selectedRun.assetType &&
      (item.createdAt || "") < (selectedRun.createdAt || "")
  );
}

function availableBaselineRunsFor(runId) {
  const importRuns = effectiveOperationsOverview().importRuns ?? [];
  const selectedRun = importRuns.find((item) => item.runId === runId);
  if (!selectedRun) {
    return [];
  }
  return importRuns.filter(
    (item) => item.runId !== runId && (item.createdAt || "") < (selectedRun.createdAt || "")
  );
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
  if (amapState.map || amapState.scriptPromise || amapState.status === "loading" || amapState.status === "ready") {
    return;
  }
  requestAnimationFrame(() => {
    if (!runtimeConfig?.hasAmapKey || !runtimeConfig?.amapApiKey) {
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

async function refreshData() {
  const requestId = ++mapRequestId;
  const query = buildExportQuery();
  const communityQuery = new URLSearchParams();
  communityQuery.set("district", state.districtFilter);
  communityQuery.set("sample_status", "all");
  communityQuery.set("focus_scope", "all");

  try {
    const [mapResponse, communityResponse, opportunitiesResponse, browserPackResponse] = await Promise.all([
      fetch(`/api/map/districts?${query}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/map/communities?${communityQuery.toString()}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/opportunities?${query}`, { headers: { Accept: "application/json" } }),
      fetch(`/api/browser-sampling-pack?${query}`, { headers: { Accept: "application/json" } })
    ]);

    if (!mapResponse.ok || !communityResponse.ok || !opportunitiesResponse.ok || !browserPackResponse.ok) {
      throw new Error("API data refresh failed");
    }

    const [mapPayload, communityPayload, opportunitiesPayload, browserPackPayload] = await Promise.all([
      mapResponse.json(),
      communityResponse.json(),
      opportunitiesResponse.json(),
      browserPackResponse.json()
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
    ensureBrowserSamplingTaskSelection();
    render();
    scheduleUiHydrationRetry();
    scheduleMapInitializationRetry();
  }

  buildFilters();
  ensureValidSelection();
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

function buildFallbackBuildingDetail(buildingId) {
  const community = state.selectedCommunityDetail ?? getSelectedCommunity();
  if (!community) {
    return null;
  }
  const building = (community.buildings ?? []).find((item) => item.id === buildingId);
  if (!building) {
    return null;
  }
  const averageYield = Number((((building.low ?? 0) + (building.mid ?? 0) + (building.high ?? 0)) / 3).toFixed(2));
  const avgPriceWanEstimate = Math.round(community.avgPriceWan * (0.91 + (building.sequenceNo ?? 1) * 0.035));
  const sampleSizeEstimate = Math.max(6, Math.round(community.sample / Math.max(1, community.buildingCount ?? community.buildings.length ?? 1)));
  const floorCurve = buildFloorCurve(building, avgPriceWanEstimate);
  const focusFloor = floorCurve.reduce((best, floor) => {
    if (!best) {
      return floor;
    }
    if (floor.opportunityScore !== best.opportunityScore) {
      return floor.opportunityScore > best.opportunityScore ? floor : best;
    }
    return floor.yieldPct > best.yieldPct ? floor : best;
  }, null);
  return {
    ...building,
    communityId: community.id,
    communityName: community.name,
    districtId: community.districtId,
    districtName: community.districtName,
    communityYield: community.yield,
    communityScore: community.score,
    communitySample: community.sample,
    avgPriceWanEstimate,
    monthlyRentEstimate: Math.round(community.monthlyRent * (averageYield / Math.max(community.yield, 0.1))),
    sampleSizeEstimate,
    yieldSpreadVsCommunity: Number((averageYield - community.yield).toFixed(2)),
    bestBucketLabel: { low: "低楼层", mid: "中楼层", high: "高楼层" }[building.bestBucket ?? "mid"],
    floorMetrics: [
      { bucket: "low", label: "低楼层", yieldPct: building.low },
      { bucket: "mid", label: "中楼层", yieldPct: building.mid },
      { bucket: "high", label: "高楼层", yieldPct: building.high }
    ],
    scoreBreakdown: buildScoreBreakdown(building, community, sampleSizeEstimate, avgPriceWanEstimate),
    floorCurve,
    focusFloorNo: focusFloor?.floorNo ?? floorCurve[0]?.floorNo ?? null,
    topFloors: floorCurve
      .slice()
      .sort((left, right) => right.opportunityScore - left.opportunityScore || right.yieldPct - left.yieldPct)
      .slice(0, 5)
  };
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

function buildFallbackImportRunDetail(runId) {
  const run = (effectiveOperationsOverview().importRuns ?? []).find((item) => item.runId === runId);
  if (!run) {
    return null;
  }
  const reviewQueue = (effectiveOperationsOverview().addressQueue ?? []).filter(
    (item) => item.runId === runId || item.sourceId === "authorized-batch-import"
  );
  const topEvidence = [
    {
      buildingId: "zhangjiang-park-b2",
      buildingName: "5号楼",
      communityId: "zhangjiang-park",
      communityName: "张江汤臣豪园",
      floorNo: 17,
      yieldPct: 2.85,
      pairCount: 1,
      bestPairConfidence: 0.9798
    },
    {
      buildingId: "zhangjiang-park-b2",
      buildingName: "5号楼",
      communityId: "zhangjiang-park",
      communityName: "张江汤臣豪园",
      floorNo: 9,
      yieldPct: 2.82,
      pairCount: 1,
      bestPairConfidence: 0.911
    },
    {
      buildingId: "qibao-yunting-b2",
      buildingName: "9幢",
      communityId: "qibao-yunting",
      communityName: "七宝云庭",
      floorNo: 15,
      yieldPct: 2.79,
      pairCount: 1,
      bestPairConfidence: 0.8827
    }
  ];
  const recentReviews = [
    {
      eventId: `${runId}::authorized-manual::SALE-003::20260411225038`,
      queueId: `${runId}::authorized-manual::SALE-003`,
      sourceId: "authorized-manual",
      communityId: "qibao-yunting",
      communityName: "七宝云庭",
      buildingId: "qibao-yunting-b2",
      buildingName: "9幢",
      floorNo: 15,
      previousStatus: "needs_review",
      newStatus: "resolved",
      reviewOwner: "atlas-ui",
      reviewedAt: "2026-04-11T22:50:38+08:00",
      resolutionNotes: "工作台烟测：人工复核确认。"
    }
  ];
  return {
    ...run,
    attention: {
      unresolved_examples: reviewQueue.slice(0, 2).map((item) => ({
        source: item.sourceId,
        source_listing_id: item.queueId,
        parse_status: item.status,
        raw_text: item.rawAddress,
        resolution_notes: item.reviewHint
      })),
      low_confidence_pairs: []
    },
    reviewQueue,
    reviewHistoryCount: recentReviews.length,
    recentReviews,
    topEvidence,
    comparison: null
  };
}

function buildFallbackGeoAssetRunComparison(selectedRun, baselineRun) {
  if (!selectedRun || !baselineRun) {
    return null;
  }
  return {
    baselineRunId: baselineRun.runId,
    baselineBatchName: baselineRun.batchName,
    baselineCreatedAt: baselineRun.createdAt,
    coveragePctDelta: Number(((selectedRun.coveragePct ?? 0) - (baselineRun.coveragePct ?? 0)).toFixed(1)),
    resolvedBuildingDelta: (selectedRun.resolvedBuildingCount ?? 0) - (baselineRun.resolvedBuildingCount ?? 0),
    missingBuildingDelta: 2,
    openTaskDelta: (selectedRun.openTaskCount ?? 0) - (baselineRun.openTaskCount ?? 0),
    reviewTaskDelta: (selectedRun.reviewTaskCount ?? 0) - (baselineRun.reviewTaskCount ?? 0),
    captureTaskDelta: (selectedRun.captureTaskCount ?? 0) - (baselineRun.captureTaskCount ?? 0),
    scheduledTaskDelta: 1,
    resolvedTaskDelta: 1,
    criticalOpenTaskDelta: -1,
    watchlistLinkedTaskDelta: 2,
    newBuildingCount: 2,
    removedBuildingCount: 0,
    changedGeometryCount: 1,
    sharedBuildingCount: 4,
    topBuildingChanges: [
      {
        communityId: "zhangjiang-park",
        communityName: "张江汤臣豪园",
        districtId: "pudong",
        districtName: "浦东新区",
        buildingId: "zhangjiang-park-b3",
        buildingName: "7号楼",
        sourceRef: "geo-demo-003",
        resolutionNotes: "新增补采楼栋 footprint。",
        geometryType: "Polygon",
        status: "new",
        statusLabel: "新增覆盖",
        centroidShiftMeters: null,
        areaDeltaPct: null,
        vertexDelta: null
      },
      {
        communityId: "qibao-yunting",
        communityName: "七宝云庭",
        districtId: "minhang",
        districtName: "闵行区",
        buildingId: "qibao-yunting-b3",
        buildingName: "11幢",
        sourceRef: "geo-demo-006",
        resolutionNotes: "新增补采楼栋 footprint。",
        geometryType: "Polygon",
        status: "new",
        statusLabel: "新增覆盖",
        centroidShiftMeters: null,
        areaDeltaPct: null,
        vertexDelta: null
      },
      {
        communityId: "zhangjiang-park",
        communityName: "张江汤臣豪园",
        districtId: "pudong",
        districtName: "浦东新区",
        buildingId: "zhangjiang-park-b2",
        buildingName: "5号楼",
        sourceRef: "geo-demo-002",
        resolutionNotes: "对齐楼栋 footprint 后做了一轮几何修正。",
        geometryType: "Polygon",
        status: "changed",
        statusLabel: "几何修正",
        centroidShiftMeters: 12.4,
        areaDeltaPct: 8.7,
        vertexDelta: 0
      }
    ]
  };
}

function buildFallbackGeoAssetRunDetail(runId, baselineRunId = null) {
  const run = (effectiveOperationsOverview().geoAssetRuns ?? []).find((item) => item.runId === runId);
  if (!run) {
    return null;
  }
  const baselineRun = baselineRunId
    ? (effectiveOperationsOverview().geoAssetRuns ?? []).find((item) => item.runId === baselineRunId)
    : availableGeoBaselineRunsFor(runId)[0];
  const coverageTasks = [
    {
      taskId: `${runId}::missing::qibao-yunting-b1`,
      taskScope: "missing_building",
      taskScopeLabel: "楼栋缺口",
      status: "needs_capture",
      priority: "medium",
      providerId: run.providerId,
      districtId: "minhang",
      districtName: "闵行区",
      communityId: "qibao-yunting",
      communityName: "七宝云庭",
      buildingId: "qibao-yunting-b1",
      buildingName: "8幢",
      sourceRef: "qibao-yunting-b1",
      resolutionNotes: "当前批次未提供该楼栋 footprint，建议补采或人工勾绘。",
      reviewOwner: null,
      reviewedAt: null,
      updatedAt: run.createdAt,
      runId,
      batchName: run.batchName,
      impactScore: 84,
      impactBand: "critical",
      impactLabel: "立即补齐",
      watchlistHits: 2,
      watchlistFloors: [
        { floorNo: 15, latestYieldPct: 2.89, persistenceScore: 92, trendLabel: "持续走强" },
        { floorNo: 11, latestYieldPct: 2.78, persistenceScore: 81, trendLabel: "新增样本" }
      ],
      recommendedAction: "优先补采 footprint，这栋楼已影响套利楼层定位和导出。",
      communityScore: 84,
      buildingOpportunityScore: 79,
      coverageGapCount: 1,
      workOrderId: null,
      workOrderStatus: null,
      workOrderStatusLabel: null,
      workOrderAssignee: null
    },
    {
      taskId: `${runId}::missing::gongkang-hill-b2`,
      taskScope: "missing_building",
      taskScopeLabel: "楼栋缺口",
      status: "scheduled",
      priority: "medium",
      providerId: run.providerId,
      districtId: "baoshan",
      districtName: "宝山区",
      communityId: "gongkang-hill",
      communityName: "共康新城",
      buildingId: "gongkang-hill-b2",
      buildingName: "12幢",
      sourceRef: "gongkang-hill-b2",
      resolutionNotes: "已派工给 GIS，同步等待下一版 AOI 导出。",
      reviewOwner: "atlas-ui",
      reviewedAt: "2026-04-12T12:08:00+08:00",
      updatedAt: "2026-04-12T12:08:00+08:00",
      runId,
      batchName: run.batchName,
      impactScore: 58,
      impactBand: "medium",
      impactLabel: "排入本轮",
      watchlistHits: 0,
      watchlistFloors: [],
      recommendedAction: "跟进 GIS 派工结果，优先确认下一版 footprint 已包含该楼栋。",
      communityScore: 72,
      buildingOpportunityScore: 61,
      coverageGapCount: 2,
      workOrderId: `${runId}::wo::20260412120800`,
      workOrderStatus: "assigned",
      workOrderStatusLabel: "已派单",
      workOrderAssignee: "gis-team"
    }
  ];
  const recentReviews = [
    {
      eventId: `${runId}::missing::gongkang-hill-b2::20260412120800`,
      taskId: `${runId}::missing::gongkang-hill-b2`,
      taskScope: "missing_building",
      communityId: "gongkang-hill",
      communityName: "共康新城",
      buildingId: "gongkang-hill-b2",
      buildingName: "12幢",
      sourceRef: "gongkang-hill-b2",
      previousStatus: "needs_capture",
      newStatus: "scheduled",
      reviewOwner: "atlas-ui",
      reviewedAt: "2026-04-12T12:08:00+08:00",
      resolutionNotes: "已派工给 GIS，同步等待下一版 AOI 导出。",
      runId,
      batchName: run.batchName
    }
  ];
  const workOrders = [
    {
      workOrderId: `${runId}::wo::20260412120800`,
      status: "assigned",
      statusLabel: "已派单",
      assignee: "gis-team",
      title: "共康新城 · 12幢 几何补采",
      taskIds: [`${runId}::missing::gongkang-hill-b2`],
      taskCount: 1,
      districtId: "baoshan",
      districtName: "宝山区",
      communityId: "gongkang-hill",
      communityName: "共康新城",
      buildingId: "gongkang-hill-b2",
      buildingName: "12幢",
      primaryTaskId: `${runId}::missing::gongkang-hill-b2`,
      focusFloorNo: null,
      focusYieldPct: null,
      impactScore: 58,
      impactBand: "medium",
      watchlistHits: 0,
      notes: "已派工给 GIS，同步等待下一版 AOI 导出。",
      createdBy: "atlas-ui",
      createdAt: "2026-04-12T12:08:00+08:00",
      updatedAt: "2026-04-12T12:08:00+08:00",
      dueAt: "2026-04-13T18:00:00+08:00",
      linkedTasks: [coverageTasks[1]],
      runId,
      batchName: run.batchName
    }
  ];
  const recentWorkOrderEvents = [
    {
      eventId: `${runId}::wo::20260412120800::assigned`,
      workOrderId: `${runId}::wo::20260412120800`,
      previousStatus: null,
      newStatus: "assigned",
      changedBy: "atlas-ui",
      changedAt: "2026-04-12T12:08:00+08:00",
      notes: "已从 Geo Ops 工作台生成补采工单。",
      runId,
      batchName: run.batchName
    }
  ];
  return {
    ...run,
    coverage: {
      catalogBuildingCount: 21,
      resolvedBuildingCount: run.resolvedBuildingCount ?? 0,
      missingBuildingCount: Math.max(21 - (run.resolvedBuildingCount ?? 0), 0),
      catalogCoveragePct: Number((((run.resolvedBuildingCount ?? 0) / 21) * 100).toFixed(1))
    },
    coverageGaps: [
      {
        communityId: "zhangjiang-park",
        communityName: "张江汤臣豪园",
        districtId: "pudong",
        districtName: "浦东新区",
        resolvedBuildingCount: 3,
        missingBuildingCount: 0,
        totalBuildingCount: 3,
        coveragePct: 100,
        missingBuildings: []
      },
      {
        communityId: "qibao-yunting",
        communityName: "七宝云庭",
        districtId: "minhang",
        districtName: "闵行区",
        resolvedBuildingCount: 3,
        missingBuildingCount: 0,
        totalBuildingCount: 3,
        coveragePct: 100,
        missingBuildings: []
      }
    ],
    featurePreview: [
      {
        communityId: "zhangjiang-park",
        communityName: "张江汤臣豪园",
        buildingId: "zhangjiang-park-b2",
        buildingName: "5号楼",
        sourceRef: "zhangjiang-park-b2",
        resolutionNotes: "命中 building_id",
        geometryType: "Polygon"
      },
      {
        communityId: "qibao-yunting",
        communityName: "七宝云庭",
        buildingId: "qibao-yunting-b2",
        buildingName: "9幢",
        sourceRef: "qibao-yunting-b2",
        resolutionNotes: "命中 building_id",
        geometryType: "Polygon"
      }
    ],
    unresolvedFeatures: [],
    coverageTasks,
    taskSummary: {
      taskCount: coverageTasks.length,
      openTaskCount: 2,
      reviewTaskCount: 0,
      captureTaskCount: 1,
      scheduledTaskCount: 1,
      resolvedTaskCount: 0,
      criticalOpenTaskCount: 1,
      highPriorityOpenTaskCount: 1,
      watchlistLinkedTaskCount: 1,
      avgImpactScore: 71,
      workOrderCount: workOrders.length,
      activeWorkOrderCount: 1,
      assignedWorkOrderCount: 1,
      inProgressWorkOrderCount: 0,
      deliveredWorkOrderCount: 0,
      closedWorkOrderCount: 0,
      linkedTaskCount: 1,
      unassignedOpenTaskCount: 1
    },
    reviewHistoryCount: recentReviews.length,
    recentReviews,
    workOrders,
    workOrderSummary: {
      workOrderCount: workOrders.length,
      activeWorkOrderCount: 1,
      assignedWorkOrderCount: 1,
      inProgressWorkOrderCount: 0,
      deliveredWorkOrderCount: 0,
      closedWorkOrderCount: 0,
      linkedTaskCount: 1,
      unassignedOpenTaskCount: 1
    },
    workOrderEventCount: recentWorkOrderEvents.length,
    recentWorkOrderEvents,
    comparison: buildFallbackGeoAssetRunComparison(run, baselineRun)
  };
}

function buildFallbackFloorDetail(floorNo) {
  const building = state.selectedBuildingDetail ?? buildFallbackBuildingDetail(state.selectedBuildingId);
  if (!building) {
    return null;
  }
  const floorItem = building.floorCurve?.find((item) => item.floorNo === floorNo) ?? building.floorCurve?.[0];
  if (!floorItem) {
    return null;
  }

  const queueItems = (operationsOverview?.addressQueue ?? [])
    .filter((item) => item.communityId === building.communityId && item.buildingNo === building.name && Math.abs(item.floorNo - floorItem.floorNo) <= 8)
    .slice(0, 3);
  const samplePairs = buildFallbackSamplePairs(building, floorItem);
  const sourceMix = {};
  samplePairs.forEach((pair) => {
    [pair.saleSourceName, pair.rentSourceName].forEach((name) => {
      sourceMix[name] = (sourceMix[name] ?? 0) + 1;
    });
  });

  return {
    buildingId: building.id,
    buildingName: building.name,
    communityId: building.communityId,
    communityName: building.communityName,
    districtId: building.districtId,
    districtName: building.districtName,
    floorNo: floorItem.floorNo,
    bucket: floorItem.bucket,
    bucketLabel: floorItem.bucketLabel,
    yieldPct: floorItem.yieldPct,
    yieldSpreadVsBuilding: floorItem.yieldSpreadVsBuilding,
    estPriceWan: floorItem.estPriceWan,
    estMonthlyRent: floorItem.estMonthlyRent,
    pricePremiumPct: floorItem.pricePremiumPct,
    opportunityScore: floorItem.opportunityScore,
    arbitrageTag: floorItem.arbitrageTag,
    samplePairs,
    sourceMix: Object.entries(sourceMix)
      .sort((left, right) => right[1] - left[1])
      .map(([name, count]) => ({ name, count })),
    resolutionTrace: buildFallbackResolutionTrace(building, floorItem, queueItems),
    queueItems,
    evidenceSource: "simulated",
    importRun: null,
    historyTimeline: [],
    historySummary: null,
    measuredMetrics: null
  };
}

function buildFallbackSamplePairs(building, floorItem) {
  const sampleCount = Math.max(3, Math.min(5, Math.round((building.sampleSizeEstimate ?? 6) / 2)));
  const layouts = ["2室1厅1卫", "2室2厅1卫", "3室2厅2卫", "3室1厅2卫", "4室2厅2卫"];
  const orientations = ["南", "南北", "东南", "西南", "东"];
  const sourceNames = (operationsOverview?.sourceHealth ?? []).map((item) => item.name);
  const sourcePool = sourceNames.length
    ? sourceNames
    : ["贝壳开放平台", "58 / 安居客开放体系", "上海开放数据 · 物业小区信息", "高德 AOI / POI / District"];

  return Array.from({ length: sampleCount }, (_, index) => {
    const saleSourceName = sourcePool[index % sourcePool.length];
    const rentSourceName = sourcePool[(index + 1) % sourcePool.length];
    const unitNo = `${String(floorItem.floorNo).padStart(2, "0")}${String(index + 1).padStart(2, "0")}`;
    const areaSqm = Number((78 + (building.sequenceNo ?? 1) * 6.4 + index * 5.8 + (floorItem.floorNo % 3) * 3.6).toFixed(1));
    const salePriceWan = Number((floorItem.estPriceWan * (0.94 + index * 0.028)).toFixed(1));
    const monthlyRent = Math.round(floorItem.estMonthlyRent * (0.93 + index * 0.036));
    const resolutionConfidence = Number(clamp(0.95 - index * 0.045 + floorItem.yieldSpreadVsBuilding * 0.02, 0.68, 0.99).toFixed(2));
    const dedupConfidence = Number(clamp(0.91 - index * 0.04 + (index === 0 ? 0.02 : 0), 0.58, 0.98).toFixed(2));
    return {
      pairId: `${building.id}-f${floorItem.floorNo}-${index + 1}`,
      unitNo,
      layout: layouts[((building.sequenceNo ?? 1) + index) % layouts.length],
      orientation: orientations[(floorItem.floorNo + index) % orientations.length],
      areaSqm,
      saleSourceName,
      rentSourceName,
      salePriceWan,
      monthlyRent,
      yieldPct: Number(((monthlyRent * 12) / (salePriceWan * 10000) * 100).toFixed(2)),
      resolutionConfidence,
      dedupConfidence,
      reviewState: resolutionConfidence >= 0.9 ? "已归一" : resolutionConfidence >= 0.8 ? "待复核" : "需人工确认",
      normalizedAddress: `${building.districtName} / ${building.communityName} / ${building.name} / ${index + 1}单元 / ${floorItem.floorNo}层 / ${unitNo}`,
      rawSaleAddress: `${building.communityName}${building.name}${floorItem.floorNo}层${unitNo}`,
      rawRentAddress: `${building.districtName}${building.communityName}${building.name}${floorItem.floorNo}F-${unitNo}`,
      updatedAt: `2026-04-11 ${String(8 + index).padStart(2, "0")}:3${index}`
    };
  });
}

function buildFallbackResolutionTrace(building, floorItem, queueItems) {
  const gateDetail =
    queueItems[0]?.reviewHint ??
    `${building.name} ${floorItem.floorNo} 层当前没有现成地址队列记录，按规则生成了待匹配占位。`;
  const gateStatus = queueItems[0]?.status === "resolved" ? "done" : "review";
  return [
    {
      step: "原始抓取",
      status: "done",
      detail: `出售与出租样本已在 ${building.communityName} / ${building.name} / ${floorItem.floorNo} 层收敛到同一候选层。`
    },
    {
      step: "小区别名归一",
      status: "done",
      detail: `已和物业小区字典对齐到 ${building.communityName}。`
    },
    {
      step: "楼栋 / 单元解析",
      status: gateStatus === "done" ? "done" : "review",
      detail: `楼栋号 ${building.name} 已识别，单元与门牌通过规则和历史别名表做二次补齐。`
    },
    {
      step: "空间挂载",
      status: "done",
      detail: "已挂到 AOI / 楼栋 footprint，可用于地图定位和 Google Earth 导出。"
    },
    {
      step: "人工复核闸门",
      status: gateStatus,
      detail: gateDetail
    }
  ];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function bucketForFloor(totalFloors, floorNo) {
  const lowTop = Math.max(1, Math.round(totalFloors * 0.33));
  const highStart = Math.max(lowTop + 1, Math.round(totalFloors * 0.67));
  if (floorNo <= lowTop) {
    return "low";
  }
  if (floorNo >= highStart) {
    return "high";
  }
  return "mid";
}

function interpolateFloorYield(building, floorNo) {
  const totalFloors = Math.max(Number(building.totalFloors ?? 1), 1);
  if (totalFloors === 1) {
    return Number((building.mid ?? building.low ?? building.high ?? 0).toFixed(2));
  }
  const midFloor = Math.max(2, Math.round(totalFloors / 2));
  let yieldPct = 0;
  if (floorNo <= midFloor) {
    const ratio = (floorNo - 1) / Math.max(1, midFloor - 1);
    yieldPct = (building.low ?? 0) + ((building.mid ?? 0) - (building.low ?? 0)) * ratio;
  } else {
    const ratio = (floorNo - midFloor) / Math.max(1, totalFloors - midFloor);
    yieldPct = (building.mid ?? 0) + ((building.high ?? 0) - (building.mid ?? 0)) * ratio;
  }
  return Number(yieldPct.toFixed(2));
}

function buildFloorCurve(building, avgPriceWanEstimate) {
  const totalFloors = Math.max(Number(building.totalFloors ?? 1), 1);
  const averageYield = building.yieldAvg ?? Number((((building.low ?? 0) + (building.mid ?? 0) + (building.high ?? 0)) / 3).toFixed(2));

  return Array.from({ length: totalFloors }, (_, index) => {
    const floorNo = index + 1;
    const bucket = bucketForFloor(totalFloors, floorNo);
    const floorRatio = totalFloors === 1 ? 0 : index / Math.max(1, totalFloors - 1);
    const pricePremiumPct = -2 + floorRatio * 8;
    const shapeBonus = 10 - Math.abs(floorRatio - 0.68) * 18;
    const estPriceWan = Number((avgPriceWanEstimate * (1 + pricePremiumPct / 100)).toFixed(1));
    const yieldPct = interpolateFloorYield(building, floorNo);
    const estMonthlyRent = Math.round(estPriceWan * 10000 * (yieldPct / 100) / 12);
    const yieldSpreadVsBuilding = Number((yieldPct - averageYield).toFixed(2));
    const opportunityScore = Math.round(
      clamp(
        (building.score ?? 0) -
          10 +
          yieldSpreadVsBuilding * 40 +
          shapeBonus -
          Math.max(pricePremiumPct, 0) * 0.35 +
          Math.max(-pricePremiumPct, 0) * 0.12,
        0,
        99
      )
    );

    return {
      floorNo,
      bucket,
      bucketLabel: { low: "低楼层", mid: "中楼层", high: "高楼层" }[bucket],
      yieldPct,
      yieldSpreadVsBuilding,
      estPriceWan,
      estMonthlyRent,
      pricePremiumPct: Number(pricePremiumPct.toFixed(2)),
      opportunityScore,
      arbitrageTag:
        opportunityScore >= 90
          ? "重点关注"
          : opportunityScore >= 82
            ? "可跟进"
            : opportunityScore >= 74
              ? "观察"
              : "对照"
    };
  });
}

function buildScoreBreakdown(building, community, sampleSizeEstimate, avgPriceWanEstimate) {
  const district = districts.find((item) => item.id === community.districtId) ?? { yield: community.yield };
  const rawFactors = [
    {
      key: "district_spread",
      label: "板块偏离",
      weight: 0.32,
      score: clamp(50 + (community.yield - district.yield) * 40, 0, 100),
      summary: `小区回报率相对所在行政区${community.yield >= district.yield ? "领先" : "落后"} ${Math.abs(community.yield - district.yield).toFixed(2)}%。`
    },
    {
      key: "building_spread",
      label: "楼栋偏离",
      weight: 0.24,
      score: clamp(50 + ((building.yieldAvg ?? community.yield) - community.yield) * 55, 0, 100),
      summary: `楼栋均值相对小区${(building.yieldAvg ?? community.yield) >= community.yield ? "领先" : "落后"} ${Math.abs((building.yieldAvg ?? community.yield) - community.yield).toFixed(2)}%。`
    },
    {
      key: "sample_confidence",
      label: "样本可信度",
      weight: 0.18,
      score: clamp(sampleSizeEstimate * 5.4, 0, 100),
      summary: `当前估算到 ${sampleSizeEstimate} 套有效样本，可支撑楼栋层面的初步判断。`
    },
    {
      key: "liquidity",
      label: "流动性",
      weight: 0.14,
      score: clamp(78 - Math.max(avgPriceWanEstimate - 900, 0) / 24 + community.sample * 0.45, 0, 100),
      summary: `总价 ${avgPriceWanEstimate} 万，对比样本活跃度 ${community.sample} 套做了流动性折现。`
    },
    {
      key: "data_quality",
      label: "数据质量",
      weight: 0.12,
      score: clamp(60 + (community.buildings?.length ?? 1) * 4 + Math.max((building.totalFloors ?? 12) - 12, 0) * 1.1, 0, 100),
      summary: "楼栋结构完整、楼层跨度足够，适合继续往逐层价差建模。"
    }
  ];
  const rawTotal = rawFactors.reduce((sum, item) => sum + item.score * item.weight, 0) || 1;
  const scale = (building.score ?? community.score ?? 0) / rawTotal;
  return rawFactors.map((item) => ({
    ...item,
    score: Number(item.score.toFixed(1)),
    contribution: Number((item.score * item.weight * scale).toFixed(1))
  }));
}

function render() {
  renderGlobalFeedback();
  renderInspectorPanels();
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

function mapWaypointSourceLabel(source) {
  return (
    {
      opportunity: "机会榜",
      floor_watchlist: "持续套利楼层榜",
      matrix: "楼栋矩阵",
      search: "全局搜索",
      browser_sampling: "公开页采样台",
      geo_task: "几何补采榜",
      coverage: "采样覆盖看板",
      capture_run: "采样批次回看",
      queue: "运行队列"
    }[source] ?? "研究台"
  );
}

function mapWaypointTone(source) {
  if (["browser_sampling", "coverage", "capture_run"].includes(source)) {
    return "sampling";
  }
  if (source === "geo_task") {
    return "geo";
  }
  if (source === "search") {
    return "district-active";
  }
  return "yield";
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

function searchScore(text, query) {
  if (!text || !query) {
    return 0;
  }
  if (text === query) {
    return 120;
  }
  if (text.startsWith(query)) {
    return 96;
  }
  if (text.includes(query)) {
    return 72;
  }
  return 0;
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

function searchTypeLabel(type) {
  return {
    community: "小区",
    building: "楼栋",
    floor: "楼层",
    sampling: "采样"
  }[type] ?? "对象";
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

async function applyDistrictScope(districtId, { refresh = true } = {}) {
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
    await refreshData();
  }
  return changed;
}

function updateMapNote() {
  if (!getVisibleMapCommunities().length && currentDataMode() === "empty") {
    mapNote.innerHTML = `
      <strong>说明</strong>
      <p>${amapState.modeNote ?? "当前地图用于展示上海租售比机会分布。"}</p>
      <p>当前没有数据库主读数据，所以这里仅保留真地图容器与加载说明，并等待高德底图与 staged 数据同步完成。</p>
      <p>${runtimeConfig.hasPostgresDsn ? "本地库已经配置，但还没完成首轮 bootstrap。先跑 reference → import → geo → metrics。" : "下一步请先导入授权 / 官方批次，完成地址标准化与 PostgreSQL 落库；需要联调时也可以显式开启 demo mock。"}</p>
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
  const scopeText =
    isFloorWatchlistLoading
      ? `持续套利楼层带仍在计算中，当前先保留 ${getVisibleBuildingItems().length} 个楼栋面的上下文，并挂着 ${geoTaskItems.length} 个高影响几何缺口与 ${browserSamplingVisibleCount} 个采样任务标记。`
      : state.granularity === "community"
      ? `当前显示 ${visibleCount} 个小区点，适合做全市级热力筛选；同时挂着 ${geoTaskItems.length} 个高影响几何缺口和 ${browserSamplingVisibleCount} 个公开页采样缺口。`
      : state.granularity === "building"
      ? `当前显示 ${visibleCount} 个楼栋面，并叠加 ${geoTaskItems.length} 个高影响几何补采点与 ${browserSamplingVisibleCount} 个采样任务标记。`
      : `当前显示 ${visibleCount} 个持续套利楼层面，并叠加 ${geoTaskItems.length} 个会影响楼层定位的几何缺口与 ${browserSamplingVisibleCount} 个采样任务标记。`;
  const windowText =
    isFloorWatchlistLoading
      ? `研究窗口：${currentBatch}${baselineBatch ? ` vs ${baselineBatch}` : "（自动首批基线）"}，楼层榜正在异步刷新。`
      : state.granularity === "floor"
      ? `研究窗口：${currentBatch}${baselineBatch ? ` vs ${baselineBatch}` : "（自动首批基线）"}。`
      : `当前粒度：${granularityLabel(state.granularity)}。`;
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
      ? `小区层当前优先使用真实经纬度挂图：${activeMetricCount} 个有指标样本，${dictionaryOnlyCount} 个仅主档待补样本；全市主档里还有 ${unanchoredCommunityCount} 个小区待补坐标。`
      : geometrySource === "api"
      ? `楼栋与楼层 footprint 当前优先来自后端 geo-assets 接口${geometryBatchName ? `（${geometryBatchName}）` : ""}，可继续替换成 AOI / 楼栋实测几何。`
      : "楼栋与楼层 footprint 当前由前端本地推导，接入真实 geo-assets 后会自动切换。";
  const taskText = topGeoTask
    ? `当前最该补的几何缺口是 ${topGeoTask.communityName ?? "待识别小区"} · ${topGeoTask.buildingName ?? "待识别楼栋"}，${topGeoTask.impactLabel}。`
    : "当前筛选窗口下没有高影响几何缺口。";
  const samplingText = topBrowserSamplingTask
    ? `当前还有 ${browserSamplingOpenTasks.length} 个公开页采样缺口${browserSamplingReviewCount ? `，其中 ${browserSamplingReviewCount} 个待复核` : ""}；最紧急的是 ${topBrowserSamplingTask.communityName ?? "待识别小区"}${topBrowserSamplingTask.buildingName ? ` · ${topBrowserSamplingTask.buildingName}` : ""}${topBrowserSamplingTask.floorNo != null ? ` · ${topBrowserSamplingTask.floorNo}层` : ""}，${browserSamplingCoverageLabel(topBrowserSamplingTask)}。`
    : "当前筛选窗口下没有公开页采样缺口。";
  const waypointText = waypoint
    ? `刚刚从${waypoint.sourceLabel ?? "研究台"}跳转到了 ${waypoint.label}${waypoint.detail ? `，当前正在联动 ${waypoint.detail}` : ""}。`
    : null;
  const previewText = selectedPreview
    ? `当前选中的 ${selectedCommunity?.name ?? "小区"} 还没正式写回主档坐标，地图正在用候选预锚点 ${selectedPreview.anchorName ?? "待确认候选"} 做人工判断参考。`
    : `当前没有处于预锚点评估中的小区；当前批次仍有 ${Number(opsSummaryData.pendingAnchorCount ?? unanchoredCommunityCount)} 个小区待确认锚点${latestAnchorReviewAt ? `，最近一次确认在 ${formatTimestamp(latestAnchorReviewAt)}` : ""}。`;

  mapNote.innerHTML = `
    <strong>说明</strong>
    <p>${baseNote}</p>
    <p>${scopeText}</p>
    <p>${windowText}</p>
    <p>${geometryText}</p>
    <p>${samplingText}</p>
    ${waypointText ? `<p>${waypointText}</p>` : ""}
    <p>${previewText}</p>
    <p>${taskText}</p>
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

function buildingSvgPoint(community, building) {
  const buildingCount = Math.max(community.buildings?.length ?? 1, 1);
  const sequenceNo = building?.sequenceNo ?? 1;
  const sequenceOffset = sequenceNo - (buildingCount + 1) / 2;
  return {
    x: community.x + sequenceOffset * 18,
    y: community.y + (sequenceNo % 2 === 0 ? 10 : -10)
  };
}

function floorSvgPoint(community, building, floorNo) {
  const anchor = buildingSvgPoint(community, building);
  const safeFloor = Math.max(Number(floorNo) || 1, 1);
  const totalFloors = Math.max(Number(building?.totalFloors) || safeFloor, 1);
  const floorOffset = Math.min(safeFloor, totalFloors) / totalFloors;
  return {
    x: anchor.x + ((safeFloor % 4) - 1.5) * 2.2,
    y: anchor.y - floorOffset * 22
  };
}

function footprintDimensions(building, scale = 1) {
  const totalFloors = Math.max(Number(building?.totalFloors) || 12, 1);
  return {
    halfWidth: (8 + Math.min(totalFloors, 30) * 0.22) * scale,
    halfHeight: (6 + Math.min(totalFloors, 30) * 0.14) * scale
  };
}

function footprintPolygon(center, dimensions) {
  return [
    { x: Number((center.x - dimensions.halfWidth).toFixed(2)), y: Number((center.y + dimensions.halfHeight * 0.45).toFixed(2)) },
    { x: Number((center.x + dimensions.halfWidth * 0.35).toFixed(2)), y: Number((center.y + dimensions.halfHeight).toFixed(2)) },
    { x: Number((center.x + dimensions.halfWidth).toFixed(2)), y: Number((center.y - dimensions.halfHeight * 0.35).toFixed(2)) },
    { x: Number((center.x - dimensions.halfWidth * 0.25).toFixed(2)), y: Number((center.y - dimensions.halfHeight).toFixed(2)) }
  ];
}

function buildingFootprintPoints(community, building) {
  return footprintPolygon(buildingSvgPoint(community, building), footprintDimensions(building, 1));
}

function floorFootprintPoints(community, building, floorNo) {
  return footprintPolygon(floorSvgPoint(community, building, floorNo), footprintDimensions(building, 0.82));
}

function polygonPointsAttribute(points) {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

function footprintCentroid(points) {
  if (!points.length) {
    return { x: 0, y: 0 };
  }
  const total = points.reduce(
    (sum, point) => ({ x: sum.x + point.x, y: sum.y + point.y }),
    { x: 0, y: 0 }
  );
  return {
    x: Number((total.x / points.length).toFixed(2)),
    y: Number((total.y / points.length).toFixed(2))
  };
}

function footprintPathToLonLat(points) {
  const ring = points.map((point) => normalizeSvgToLonLat(point.x, point.y));
  if (ring.length) {
    const [firstLon, firstLat] = ring[0];
    const [lastLon, lastLat] = ring[ring.length - 1];
    if (firstLon !== lastLon || firstLat !== lastLat) {
      ring.push([firstLon, firstLat]);
    }
  }
  return ring;
}

function fallbackDistrictPolygonPath(district) {
  const rawPolygon = district?.polygon;
  if (!rawPolygon) {
    return [];
  }
  const points = String(rawPolygon)
    .trim()
    .split(/\s+/)
    .map((segment) => segment.split(",").map(Number))
    .filter((pair) => pair.length === 2 && Number.isFinite(pair[0]) && Number.isFinite(pair[1]))
    .map(([x, y]) => normalizeSvgToLonLat(x, y));
  if (!points.length) {
    return [];
  }
  const [firstLon, firstLat] = points[0];
  const [lastLon, lastLat] = points[points.length - 1];
  if (firstLon !== lastLon || firstLat !== lastLat) {
    points.push([firstLon, firstLat]);
  }
  return points;
}

function polygonCenterLonLat(ring) {
  if (!Array.isArray(ring) || !ring.length) {
    return null;
  }
  const rawPoints = ring.slice(0, ring.length > 1 ? -1 : ring.length);
  const points = rawPoints
    .map((point) => {
      if (Array.isArray(point) && point.length >= 2) {
        return [Number(point[0]), Number(point[1])];
      }
      const lng = typeof point?.getLng === "function" ? point.getLng() : point?.lng;
      const lat = typeof point?.getLat === "function" ? point.getLat() : point?.lat;
      if (Number.isFinite(Number(lng)) && Number.isFinite(Number(lat))) {
        return [Number(lng), Number(lat)];
      }
      return null;
    })
    .filter((point) => Array.isArray(point) && Number.isFinite(point[0]) && Number.isFinite(point[1]));
  if (!points.length) {
    return null;
  }
  const total = points.reduce(
    (sum, [lon, lat]) => ({ lon: sum.lon + Number(lon), lat: sum.lat + Number(lat) }),
    { lon: 0, lat: 0 }
  );
  return [Number((total.lon / points.length).toFixed(6)), Number((total.lat / points.length).toFixed(6))];
}

function featureSvgPoints(feature) {
  const points = feature?.properties?.svg_points;
  if (!Array.isArray(points)) {
    return [];
  }
  return points
    .filter((point) => Array.isArray(point) && point.length >= 2)
    .map(([x, y]) => ({ x: Number(x), y: Number(y) }));
}

function featureSvgCenter(feature) {
  const svgCenter = feature?.properties?.svg_center;
  if (Array.isArray(svgCenter) && svgCenter.length >= 2) {
    return { x: Number(svgCenter[0]), y: Number(svgCenter[1]) };
  }
  const svgPoints = featureSvgPoints(feature);
  return svgPoints.length ? footprintCentroid(svgPoints) : null;
}

function featureLonLatPath(feature) {
  const geometry = feature?.geometry;
  if (geometry?.type === "Polygon" && Array.isArray(geometry.coordinates?.[0])) {
    return geometry.coordinates[0].map(([lon, lat]) => [Number(lon), Number(lat)]);
  }
  return [];
}

function featureLonLatCenter(feature) {
  const properties = feature?.properties ?? {};
  if (properties.center_lng != null && properties.center_lat != null) {
    return [Number(properties.center_lng), Number(properties.center_lat)];
  }
  const geometry = feature?.geometry;
  if (geometry?.type === "Point" && Array.isArray(geometry.coordinates)) {
    return geometry.coordinates.map((value) => Number(value));
  }
  return polygonCenterLonLat(featureLonLatPath(feature));
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

function formatTimestamp(value) {
  if (!value) {
    return "时间待补";
  }
  return value.replace("T", " ").slice(0, 16);
}

function metricsRefreshStatusTone(status) {
  return {
    completed: "resolved",
    partial: "matching",
    error: "needs_review"
  }[String(status ?? "").trim().toLowerCase()] ?? "captured";
}

function metricsRefreshStatusLabel(status) {
  return {
    completed: "已完成",
    partial: "部分完成",
    error: "失败"
  }[String(status ?? "").trim().toLowerCase()] ?? "状态待补";
}

function metricsRefreshModeLabel(mode) {
  return {
    staged: "仅 staged",
    "staged+postgres": "staged + PostgreSQL",
    "postgres-only": "仅 PostgreSQL"
  }[String(mode ?? "").trim().toLowerCase()] ?? "模式待补";
}

function metricsRefreshTriggerLabel(source) {
  return {
    "atlas-ui": "工作台手动",
    "browser-sampling": "公开页采样",
    bootstrap: "本地 Bootstrap"
  }[String(source ?? "").trim().toLowerCase()] ?? "系统触发";
}

function metricsRefreshPostgresLabel(status) {
  return {
    completed: "DB 已同步",
    skipped: "DB 未写入",
    error: "DB 同步失败",
    pending: "DB 等待中"
  }[String(status ?? "").trim().toLowerCase()] ?? "DB 状态待补";
}

function truncate(value, maxLength = 48) {
  const text = String(value ?? "");
  if (!text || text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxLength - 1))}…`;
}

function formatSignedNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "待补";
  }
  const numeric = Number(value);
  const prefix = numeric > 0 ? "+" : "";
  return `${prefix}${numeric.toFixed(digits)}`;
}

function formatSignedDelta(value, { suffix = "", digits = 0, emptyLabel = "上批无样本" } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return emptyLabel;
  }
  return `${formatSignedNumber(value, digits)}${suffix}`;
}

function comparisonToneClass(status) {
  return {
    improved: "improved",
    deteriorated: "deteriorated",
    stable: "stable",
    new: "new"
  }[status] ?? "stable";
}

function geoComparisonToneClass(status) {
  return {
    new: "new",
    changed: "changed",
    removed: "removed"
  }[status] ?? "stable";
}

function geoImpactBandClass(band) {
  return {
    critical: "critical",
    high: "high",
    medium: "medium",
    low: "low"
  }[band] ?? "stable";
}

function geoTaskColor(band) {
  return {
    critical: "#ff8c6b",
    high: "#ffb347",
    medium: "#75f0cf",
    low: "#97bfe2"
  }[band] ?? "#97bfe2";
}

function geoTaskBadgeText(task) {
  if ((task.watchlistHits ?? 0) > 0) {
    return String(task.watchlistHits);
  }
  return task.impactBand === "critical" ? "!" : String(Math.max(1, Math.round((task.impactScore ?? 0) / 10)));
}

function scaleRelativePolygon(points, scale = 1) {
  return points.map((point) => ({
    x: Number((point.x * scale).toFixed(2)),
    y: Number((point.y * scale).toFixed(2))
  }));
}

function polygonBounds(points) {
  if (!points.length) {
    return { minX: 0, maxX: 0, minY: 0, maxY: 0 };
  }
  return points.reduce(
    (bounds, point) => ({
      minX: Math.min(bounds.minX, point.x),
      maxX: Math.max(bounds.maxX, point.x),
      minY: Math.min(bounds.minY, point.y),
      maxY: Math.max(bounds.maxY, point.y)
    }),
    { minX: points[0].x, maxX: points[0].x, minY: points[0].y, maxY: points[0].y }
  );
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

function geoTaskIsOpen(task) {
  return ["needs_review", "needs_capture", "scheduled"].includes(task?.status);
}

function compareGeoTaskPriority(left, right) {
  const statusRank = { needs_review: 0, needs_capture: 1, scheduled: 2, resolved: 3, captured: 4 };
  return (
    (statusRank[left?.status] ?? 9) - (statusRank[right?.status] ?? 9) ||
    Number(right?.impactScore ?? 0) - Number(left?.impactScore ?? 0) ||
    Number(right?.watchlistHits ?? 0) - Number(left?.watchlistHits ?? 0) ||
    String(left?.communityName ?? "").localeCompare(String(right?.communityName ?? "")) ||
    String(left?.buildingName ?? "").localeCompare(String(right?.buildingName ?? ""))
  );
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

function compareBrowserSamplingTask(left, right) {
  const lifecycleRank = { needs_capture: 0, needs_review: 1, captured: 2 };
  return (
    (lifecycleRank[left?.taskLifecycleStatus] ?? 9) - (lifecycleRank[right?.taskLifecycleStatus] ?? 9) ||
    Number(right?.priorityScore ?? 0) - Number(left?.priorityScore ?? 0) ||
    String(left?.taskType ?? "").localeCompare(String(right?.taskType ?? "")) ||
    String(left?.communityName ?? "").localeCompare(String(right?.communityName ?? "")) ||
    String(left?.buildingName ?? "").localeCompare(String(right?.buildingName ?? ""))
  );
}

function compareBrowserSamplingMapTask(left, right) {
  const statusRank = { needs_review: 0, needs_capture: 1, in_progress: 2, resolved: 3 };
  return (
    (statusRank[browserSamplingCoverageState(left)] ?? 9) - (statusRank[browserSamplingCoverageState(right)] ?? 9) ||
    compareBrowserSamplingTask(left, right)
  );
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

function setBestBrowserSamplingTask(map, key, task) {
  if (!key) {
    return;
  }
  const current = map.get(key);
  if (!current || compareBrowserSamplingMapTask(task, current) < 0) {
    map.set(key, task);
  }
}

function browserSamplingTaskKey(task) {
  return task?.buildingId && task?.floorNo != null ? `${task.buildingId}:${task.floorNo}` : null;
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
  const reviewCount = Number(task?.latestCaptureAttentionCount ?? 0);
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

async function navigateToBrowserSamplingTask(task, { resetDraft = false, waypoint = null, revealLatestCaptureRun = "auto" } = {}) {
  if (!task?.taskId) {
    return;
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
  const shouldRevealAttentionRun =
    Boolean(task.latestCaptureRunId) &&
    (revealLatestCaptureRun === true || (revealLatestCaptureRun === "auto" && Number(task.latestCaptureAttentionCount ?? 0) > 0));
  if (shouldRevealAttentionRun) {
    await loadSelectedBrowserCaptureRunDetail(task.latestCaptureRunId);
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
    .sort((left, right) => String(right?.createdAt ?? "").localeCompare(String(left?.createdAt ?? "")));
  return runs.slice(0, limit);
}

function currentBrowserCaptureRun() {
  const selectedRunId = state.selectedBrowserCaptureRunId;
  if (!selectedRunId) {
    return null;
  }
  return state.selectedBrowserCaptureRunDetail?.runId === selectedRunId ? state.selectedBrowserCaptureRunDetail : null;
}

function currentBrowserCaptureSubmission() {
  const submission = state.lastBrowserCaptureSubmission;
  if (!submission?.taskId) {
    return null;
  }
  return submission.taskId === state.selectedBrowserSamplingTaskId ? submission : null;
}

function getBrowserSamplingWorkbenchQueue(task = currentBrowserSamplingTask()) {
  const openTasks = (state.browserSamplingPackItems ?? [])
    .filter((item) => item.taskId !== task?.taskId)
    .filter((item) => browserSamplingCoverageState(item) !== "resolved")
    .slice()
    .sort(compareBrowserSamplingMapTask);
  const districtTasks = task?.districtId
    ? openTasks.filter((item) => item.districtId === task.districtId)
    : openTasks;
  const taskPool = districtTasks.length ? districtTasks : openTasks;
  return {
    districtTasks: taskPool,
    nextDistrictTask: taskPool[0] ?? null,
    nextReviewTask: taskPool.find((item) => browserSamplingCoverageState(item) === "needs_review") ?? null,
    nextCaptureTask:
      taskPool.find((item) => ["needs_capture", "in_progress"].includes(browserSamplingCoverageState(item))) ?? null,
    previewTasks: taskPool.slice(0, 4)
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

function browserCaptureLifecycleStatus(attentionCount) {
  return Number(attentionCount || 0) > 0 ? "needs_review" : "captured";
}

function browserCaptureLifecycleLabel(attentionCount) {
  return Number(attentionCount || 0) > 0 ? "已采待复核" : "已采仍需补采";
}

function browserSamplingTargetCount(task) {
  if (!task) {
    return 0;
  }
  return Number(
    task.targetGranularity === "floor"
      ? task.targetPairCount ?? 0
      : task.targetSampleSize ?? 0
  );
}

function browserSamplingCurrentCount(task) {
  if (!task) {
    return 0;
  }
  return Number(
    task.targetGranularity === "floor"
      ? task.currentPairCount ?? 0
      : task.currentSampleSize ?? 0
  );
}

function browserSamplingMissingCount(task) {
  return Math.max(browserSamplingTargetCount(task) - browserSamplingCurrentCount(task), 0);
}

function browserSamplingCoverageState(task) {
  const attentionCount = Number(task?.latestCaptureAttentionCount ?? 0);
  if (attentionCount > 0) {
    return "needs_review";
  }
  if (browserSamplingMissingCount(task) <= 0 && browserSamplingTargetCount(task) > 0) {
    return "resolved";
  }
  if (browserSamplingCurrentCount(task) > 0 || Number(task?.captureHistoryCount ?? 0) > 0) {
    return "in_progress";
  }
  return "needs_capture";
}

function browserSamplingCoverageLabel(task) {
  return {
    resolved: "已采够",
    in_progress: "补采中",
    needs_review: "待复核",
    needs_capture: "待采样"
  }[browserSamplingCoverageState(task)];
}

function browserSamplingCoverageProgress(task) {
  const target = browserSamplingTargetCount(task);
  if (target <= 0) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((browserSamplingCurrentCount(task) / target) * 100)));
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
    if (!districtEntry.latestCaptureAt || String(task.latestCaptureAt ?? "") > String(districtEntry.latestCaptureAt ?? "")) {
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
        latestCaptureAttentionCount: 0,
        highestPriorityTask: task,
        outstandingTask: task,
        taskItems: []
      };

    communityEntry.taskCount += 1;
    communityEntry.targetCount += browserSamplingTargetCount(task);
    communityEntry.currentCount += Math.min(browserSamplingCurrentCount(task), browserSamplingTargetCount(task) || browserSamplingCurrentCount(task));
    communityEntry.missingCount += browserSamplingMissingCount(task);
    communityEntry.taskItems.push(task);
    communityEntry.latestCaptureAttentionCount += Number(task.latestCaptureAttentionCount ?? 0);
    if (!communityEntry.latestCaptureAt || String(task.latestCaptureAt ?? "") > String(communityEntry.latestCaptureAt ?? "")) {
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
  const createdAt = new Date().toISOString();
  const attentionCount = Number(summary.attention_count ?? (body?.attention ?? []).length ?? 0);
  const taskSnapshot = body?.task ?? task ?? {};
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
    importRunId: body?.importRunId ?? null,
    metricsRunId: body?.metricsRun?.runId ?? null,
    metricsBatchName: body?.metricsRun?.batchName ?? null,
    taskLifecycleStatus: browserCaptureLifecycleStatus(attentionCount),
    taskLifecycleLabel: browserCaptureLifecycleLabel(attentionCount),
  };
}

function upsertBrowserCaptureRunSummary(runSummary) {
  if (!runSummary?.runId) {
    return;
  }
  const nextRuns = [runSummary, ...(effectiveOperationsOverview().browserCaptureRuns ?? []).filter((item) => item.runId !== runSummary.runId)];
  const summary = effectiveOperationsOverview().summary ?? emptyOperationsOverview.summary;
  const existing = (effectiveOperationsOverview().browserCaptureRuns ?? []).some((item) => item.runId === runSummary.runId);
  operationsOverview = {
    ...effectiveOperationsOverview(),
    browserCaptureRuns: nextRuns,
    summary: {
      ...summary,
      browserCaptureRunCount: existing ? Number(summary.browserCaptureRunCount ?? nextRuns.length) : Number(summary.browserCaptureRunCount ?? 0) + 1,
      latestBrowserCaptureAt: runSummary.createdAt ?? summary.latestBrowserCaptureAt ?? null,
      browserCaptureAttentionCount: Number(summary.browserCaptureAttentionCount ?? 0) + Number(runSummary.attentionCount ?? 0),
    }
  };
}

function buildOptimisticBrowserSamplingTask(task, runSummary) {
  if (!task?.taskId) {
    return null;
  }
  const attentionCount = Number(runSummary?.attentionCount ?? 0);
  const previousHistoryCount = Number(task.captureHistoryCount ?? 0);
  return {
    ...task,
    captureHistoryCount: previousHistoryCount + (runSummary?.runId ? 1 : 0),
    latestCaptureAt: runSummary?.createdAt ?? task.latestCaptureAt ?? null,
    latestCaptureRunId: runSummary?.runId ?? task.latestCaptureRunId ?? null,
    latestCaptureImportRunId: runSummary?.importRunId ?? task.latestCaptureImportRunId ?? null,
    latestCaptureMetricsRunId: runSummary?.metricsRunId ?? task.latestCaptureMetricsRunId ?? null,
    latestCaptureAttentionCount: attentionCount,
    latestCaptureAttentionPreview: runSummary?.attentionPreview ?? [],
    taskLifecycleStatus: browserCaptureLifecycleStatus(attentionCount),
    taskLifecycleLabel: browserCaptureLifecycleLabel(attentionCount),
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

async function finalizeBrowserSamplingCaptureRefresh(task, body, optimisticTask) {
  const refreshResults = await Promise.allSettled([refreshData(), refreshOperationsWorkbench({ reloadFloor: true })]);
  if (optimisticTask?.taskId && !(state.browserSamplingPackItems ?? []).some((item) => item.taskId === optimisticTask.taskId)) {
    upsertBrowserSamplingTask(optimisticTask, { pinSelection: true });
  }
  if (body?.captureRunId) {
    await loadSelectedBrowserCaptureRunDetail(body.captureRunId);
  }
  if (task?.communityId) {
    await navigateToEvidenceTarget(task.communityId, task.buildingId, task.floorNo);
  }
  const rejected = refreshResults.find((item) => item.status === "rejected");
  if (rejected) {
    throw rejected.reason instanceof Error ? rejected.reason : new Error("公开页面采样刷新失败。");
  }
}

async function loadSelectedBrowserCaptureRunDetail(runId) {
  if (!runId) {
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
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
    return body;
  } catch (error) {
    state.selectedBrowserCaptureRunDetail = null;
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
    resetBrowserCaptureDraft();
    return;
  }
  const selectedTask = tasks.find((task) => task.taskId === state.selectedBrowserSamplingTaskId);
  if (!selectedTask) {
    state.selectedBrowserSamplingTaskId = tasks[0].taskId;
    state.selectedBrowserCaptureRunId = null;
    state.selectedBrowserCaptureRunDetail = null;
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
    }
    const optimisticRun = buildOptimisticBrowserCaptureRun(task, body);
    const optimisticTask = buildOptimisticBrowserSamplingTask(task, optimisticRun);
    state.lastBrowserCaptureSubmission = {
      status: "success",
      taskId: task.taskId,
      captureRunId: body.captureRunId ?? null,
      importRunId: body.importRunId ?? null,
      metricsRunId: body.metricsRun?.runId ?? null,
      createdAt: optimisticRun.createdAt ?? new Date().toISOString(),
      attentionCount: Number(optimisticRun.attentionCount ?? 0)
    };
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
                        item.latestCaptureAttentionCount
                          ? `<span class="source-pill">attention ${item.latestCaptureAttentionCount}</span>`
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

  opsSummary.innerHTML = `
    ${
      state.opsMessage && state.opsMessageContext === "database"
        ? `<div class="ops-feedback ${state.opsMessageTone}">${state.opsMessage}</div>`
        : ""
    }
    <article class="metric mini">
      <span class="metric-label">数据模式</span>
      <strong>${dataModeLabel}</strong>
      <small>${dataModeHint}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">本地数据库</span>
      <strong>${databaseStatusLabel}</strong>
      <small>${databaseStatusHint}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">最近引导</span>
      <strong>${summary.latestBootstrapAt ? formatTimestamp(summary.latestBootstrapAt) : "暂无"}</strong>
      <small>${postgresLabel}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">Provider</span>
      <strong>${summary.readySourceCount}/${summary.sourceCount}</strong>
      <small>离线接入 / 凭证位 readiness</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">小区挂图</span>
      <strong>${summary.anchoredCommunityCount ?? 0}/${summary.cityCommunityCount ?? 0}</strong>
      <small>${Number(summary.anchoredCommunityPct ?? 0).toFixed(1)}% 已锚定</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">待补锚点</span>
      <strong>${Math.max((summary.cityCommunityCount ?? 0) - (summary.anchoredCommunityCount ?? 0), 0)}</strong>
      <small>优先补重点区与高价值小区</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">最近确认</span>
      <strong>${summary.latestAnchorReviewAt ? formatTimestamp(summary.latestAnchorReviewAt) : "暂无"}</strong>
      <small>${summary.pendingAnchorCount ?? 0} 个仍在预锚点评估中</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">采样任务</span>
      <strong>${state.browserSamplingPackItems?.length ?? 0}</strong>
      <small>${summary.browserCaptureRunCount ?? 0} 次公开页采样 · ${(state.browserSamplingPackItems ?? []).filter((item) => item.focusScope === "priority").length} 个重点区任务</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">归一均值</span>
      <strong>${summary.avgNormalizationPct}%</strong>
      <small>当前 staging 队列的归一完成率</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">待复核</span>
      <strong>${summary.reviewQueueCount}</strong>
      <small>重点盯单元和门牌</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">导入批次</span>
      <strong>${summary.importRunCount ?? 0}</strong>
      <small>staging 离线批次</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">主档批次</span>
      <strong>${summary.referenceRunCount ?? referenceRuns.length}</strong>
      <small>${summary.latestReferencePersistAt ? `最近写库 ${formatTimestamp(summary.latestReferencePersistAt)}` : "等待首轮 reference 落库"}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">全市覆盖</span>
      <strong>${Number(summary.cityCoveragePct ?? 0).toFixed(1)}%</strong>
      <small>${summary.sampleFreshness ? `样本更新 ${formatTimestamp(summary.sampleFreshness)}` : "等待真实 listing 落库"}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">几何批次</span>
      <strong>${summary.geoAssetRunCount ?? geoAssetRuns.length}</strong>
      <small>${summary.latestGeoPersistAt ? `最近写库 ${formatTimestamp(summary.latestGeoPersistAt)}` : `staging 覆盖 ${summary.geoAssetCoveragePct ?? 0}% / DB ${Number(summary.buildingCoveragePct ?? 0).toFixed(1)}%`}</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">几何待处理</span>
      <strong>${summary.geoAssetOpenTaskCount ?? geoAssetRuns.reduce((sum, item) => sum + (item.openTaskCount ?? 0), 0)}</strong>
      <small>缺口补采与未命中复核</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">几何紧急</span>
      <strong>${summary.geoAssetCriticalTaskCount ?? selectedGeoRunDetail?.taskSummary?.criticalOpenTaskCount ?? 0}</strong>
      <small>优先处理会影响楼层榜定位的任务</small>
    </article>
    <article class="metric mini">
      <span class="metric-label">榜单关联</span>
      <strong>${summary.geoAssetWatchlistLinkedTaskCount ?? selectedGeoRunDetail?.taskSummary?.watchlistLinkedTaskCount ?? 0}</strong>
      <small>已挂到持续套利楼层榜的几何缺口</small>
    </article>
    <article class="metric mini metric-action">
      <span class="metric-label">指标快照</span>
      <strong>${summary.latestMetricsRefreshAt ? formatTimestamp(summary.latestMetricsRefreshAt) : "待刷新"}</strong>
      <small>${
        summary.activeDataMode === "database"
          ? `${summary.databaseSaleListingCount ?? 0} sale / ${summary.databaseRentListingCount ?? 0} rent`
          : `${summary.metricsRunCount ?? metricsRuns.length} 个 staged metrics run`
      }</small>
      <div class="comparison-strip">
        <span class="source-pill">staged ${stagedMetricsLabel}</span>
        <span class="source-pill">${postgresReady ? `db ${databaseMetricsLabel}` : "db 未配置"}</span>
      </div>
      <small>${metricsStatusHint}</small>
      <div class="metric-action-buttons">
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
    </article>
    <article class="metric mini metric-action">
      <span class="metric-label">一键引导</span>
      <strong>${postgresReady ? "reference → import → geo → metrics" : "等待 DSN"}</strong>
      <small>${postgresReady ? "建议首次直接跑本地 bootstrap。" : "先配置 POSTGRES_DSN；当前也可以先用 staged metrics run 保持研究口径统一。"}</small>
      <button class="action compact primary" data-database-bootstrap ${postgresReady ? "" : "disabled"}>
        ${state.busyBootstrapDatabase ? "引导中..." : "本地 Bootstrap"}
      </button>
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
            <article class="import-run-section">
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
            <article class="import-run-section">
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
                class="ops-feedback success browser-capture-result"
                data-browser-capture-result="success"
                data-browser-capture-result-task-id="${currentCaptureSubmission.taskId}"
                data-browser-capture-result-import-run-id="${currentCaptureSubmission.importRunId ?? ""}"
                data-browser-capture-result-capture-run-id="${currentCaptureSubmission.captureRunId ?? ""}"
                data-browser-capture-result-metrics-run-id="${currentCaptureSubmission.metricsRunId ?? ""}"
                data-browser-capture-result-created-at="${currentCaptureSubmission.createdAt ?? ""}"
                data-browser-capture-result-attention-count="${currentCaptureSubmission.attentionCount ?? 0}"
              >
                最近一次写入：${currentCaptureSubmission.importRunId ?? currentCaptureSubmission.captureRunId ?? "已提交"}${currentCaptureSubmission.metricsRunId ? ` · metrics ${currentCaptureSubmission.metricsRunId}` : ""}${currentCaptureSubmission.attentionCount ? ` · attention ${currentCaptureSubmission.attentionCount}` : " · attention 0"}
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
            selectedSamplingTask.latestCaptureAttentionCount
              ? `<span class="source-pill">attention ${selectedSamplingTask.latestCaptureAttentionCount}</span>`
              : ""
          }
        </div>
        <div class="capture-workbench-layout">
          <div class="capture-form-column">
            <article class="import-run-section browser-task-queue-panel">
              <div class="breakdown-top">
                <strong>连续补样快捷台</strong>
                <span class="badge">${workbenchQueue.previewTasks.length}</span>
              </div>
              <div class="comparison-strip">
                <span class="source-pill">同区待办 ${workbenchQueue.districtTasks.length}</span>
                <span class="source-pill">待复核 ${workbenchQueue.districtTasks.filter((task) => browserSamplingCoverageState(task) === "needs_review").length}</span>
                <span class="source-pill">待采样/补采 ${workbenchQueue.districtTasks.filter((task) => ["needs_capture", "in_progress"].includes(browserSamplingCoverageState(task))).length}</span>
              </div>
              <div class="action-row compact browser-task-actions">
                <button class="action compact" data-browser-workbench-copy-brief="${selectedSamplingTask.taskId}">复制整包采样指令</button>
                <button class="action compact" data-browser-workbench-next-district="${workbenchQueue.nextDistrictTask?.taskId ?? ""}" ${workbenchQueue.nextDistrictTask ? "" : "disabled"}>下一个同区任务</button>
                <button class="action compact" data-browser-workbench-next-review="${workbenchQueue.nextReviewTask?.taskId ?? ""}" ${workbenchQueue.nextReviewTask ? "" : "disabled"}>下一个待复核</button>
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
            <article class="import-run-section">
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
                            <span class="trace-status ${run.attentionCount ? "needs_review" : "captured"}">${run.attentionCount ? "含 attention" : "已导入"}</span>
                          </div>
                          <p>${formatTimestamp(run.createdAt)} · 原文 ${run.captureCount} 条 · Sale ${run.saleCaptureCount} / Rent ${run.rentCaptureCount}</p>
                          <small>${
                            run.attentionCount
                              ? `${run.attentionCount} 条需要回看原文`
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
            <article class="import-run-section">
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
                            <span class="trace-status ${run.attentionCount ? "needs_review" : "captured"}">${run.attentionCount ? "待回看" : "已采完成"}</span>
                          </div>
                          <p>${formatTimestamp(run.createdAt)} · ${run.taskTypeLabel ?? "公开页采样"} · ${run.captureCount} 条原文</p>
                          <small>${
                            run.attentionCount
                              ? `${run.attentionCount} 条 attention`
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
              data-browser-capture-attention-count="${selectedCaptureRunDetail?.attentionCount ?? 0}"
            >
          <div class="breakdown-top">
            <strong>attention 回看面板</strong>
            <span class="badge">${
              state.busyBrowserCaptureRunId
                ? "加载中"
                : selectedCaptureRunDetail?.runId
                  ? `${selectedCaptureRunDetail.attentionCount ?? 0} 条`
                  : "未选中"
            }</span>
          </div>
          ${
            state.busyBrowserCaptureRunId
              ? `<p class="helper-text">正在加载采样批次详情…</p>`
              : selectedCaptureRunDetail?.runId
                ? `
                  <p>${selectedCaptureRunDetail.communityName}${selectedCaptureRunDetail.buildingName ? ` · ${selectedCaptureRunDetail.buildingName}` : ""}${selectedCaptureRunDetail.floorNo != null ? ` · ${selectedCaptureRunDetail.floorNo}层` : ""} · ${formatTimestamp(selectedCaptureRunDetail.createdAt)}</p>
                  <small>原文 ${selectedCaptureRunDetail.captureCount ?? 0} 条 · attention ${selectedCaptureRunDetail.attentionCount ?? 0} 条${selectedCaptureRunDetail.importRunId ? ` · import ${selectedCaptureRunDetail.importRunId}` : ""}${selectedCaptureRunDetail.metricsRunId ? ` · metrics ${selectedCaptureRunDetail.metricsRunId}` : ""}</small>
                  <div class="import-run-grid">
                    ${
                      (selectedCaptureRunDetail.attention ?? []).length
                        ? (selectedCaptureRunDetail.attention ?? [])
                            .map(
                              (item, index) => `
                                <article class="import-run-evidence">
                                  <div class="breakdown-top">
                                    <strong>${item.businessTypeLabel} · ${item.sourceListingId}</strong>
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
                                  </div>
                                  <div class="action-row compact">
                                    <button class="action compact" data-browser-capture-fill-from-attention="${index}">回填到${item.businessTypeLabel}草稿</button>
                                    ${item.rawText ? `<button class="action compact" data-browser-capture-copy-raw="${index}">复制原文</button>` : ""}
                                  </div>
                                </article>
                              `
                            )
                            .join("")
                        : "<p class=\"helper-text\">这次采样没有 attention，当前批次可直接视为已采完成。</p>"
                    }
                  </div>
                `
                : `<p class="helper-text">点击上面的最近采样批次后，这里会展开 attention 明细，并支持一键回填到 sale / rent 草稿。</p>`
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
                            communityItem.latestCaptureAttentionCount
                              ? `<span class="source-pill">attention ${communityItem.latestCaptureAttentionCount}</span>`
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
      state.selectedImportRunId = item.dataset.runId;
      state.selectedBaselineRunId = null;
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
      state.selectedGeoAssetRunId = item.dataset.geoRunId;
      state.selectedGeoBaselineRunId = null;
      state.selectedGeoTaskId = null;
      await loadSelectedGeoAssetRunDetail();
      await loadGeoAssets();
      render();
    });
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
      const index = Number(button.dataset.browserCaptureFillFromAttention ?? -1);
      const attentionItems = currentBrowserCaptureRun()?.attention ?? [];
      const item = Number.isInteger(index) ? attentionItems[index] : null;
      if (!item) {
        return;
      }
      fillBrowserCaptureDraftFromAttention(item);
      state.opsMessage = `已把 ${item.businessTypeLabel} attention 原文回填到草稿。`;
      state.opsMessageTone = "success";
      state.opsMessageContext = "sampling";
      render();
    });
  });

  browserSamplingWorkbench.querySelectorAll("[data-browser-capture-copy-raw]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const index = Number(button.dataset.browserCaptureCopyRaw ?? -1);
      const attentionItems = currentBrowserCaptureRun()?.attention ?? [];
      const item = Number.isInteger(index) ? attentionItems[index] : null;
      await copyTextToClipboard(item?.rawText ?? "", "attention 原文已复制。");
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
      await loadSelectedImportRunDetail();
      render();
    });
  });

  geoAssetRunDetail.querySelectorAll("[data-geo-baseline-run-select]").forEach((select) => {
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      state.selectedGeoBaselineRunId = select.value || null;
      state.selectedGeoTaskId = null;
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

function yieldClass(value) {
  if (value >= 2.8) {
    return "high";
  }
  if (value >= 2.45) {
    return "mid";
  }
  return "low";
}

function sizeByScore(score) {
  return Math.max(8, Math.min(18, Math.round(score / 7)));
}

function granularityLabel(value) {
  return {
    community: "小区",
    building: "楼栋",
    floor: "楼层"
  }[value];
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

function providerModeLabel(mode) {
  return {
    self_serve_trial: "自助试用",
    business_contact: "商务合作",
    catalog_apply_or_download: "目录申请 / 下载",
    console_key: "控制台申请 Key",
    internal_staging: "内部 staging",
    manual_sketch: "手工勾绘 staging"
  }[mode] ?? mode;
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

function sourceStatusLabel(status) {
  return {
    credentials_ready: "凭证位已就绪",
    credentials_partial: "部分凭证已就绪",
    offline_ready: "离线可接入",
    connected_live: "在线接通",
    ready_for_integration: "待接入",
    online: "在线",
    partner_negotiation: "洽谈中",
    not_connected: "待接入"
  }[status] ?? status;
}

function queueStatusLabel(status) {
  return {
    resolved: "已归一",
    needs_review: "待复核",
    matching: "匹配中"
  }[status] ?? status;
}

function geoTaskStatusLabel(status) {
  return {
    needs_review: "待复核",
    needs_capture: "待补采",
    scheduled: "已派工",
    resolved: "已复核",
    captured: "已补齐"
  }[status] ?? status;
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


function geoWorkOrderStatusLabel(status) {
  return {
    assigned: "已派单",
    in_progress: "执行中",
    delivered: "待验收",
    closed: "已关闭"
  }[status] ?? status;
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

function geoWorkOrderFilterLabel(status) {
  return {
    all: "全部工单",
    open: "打开工单",
    assigned: "已派单",
    in_progress: "执行中",
    delivered: "待验收",
    closed: "已关闭"
  }[status] ?? status ?? "全部工单";
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

function resolutionStatusLabel(status) {
  return {
    done: "完成",
    review: "复核"
  }[status] ?? status;
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

function slugifyExportName(value, fallback = "latest") {
  return (value ?? fallback)
    .toString()
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/gi, "-")
    .replace(/^-+|-+$/g, "") || fallback;
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

function normalizeSvgToLonLat(x, y) {
  const lon = 121.05 + (x / 760) * 0.8;
  const lat = 31.0 + ((520 - y) / 520) * 0.55;
  return [Number(lon.toFixed(6)), Number(lat.toFixed(6))];
}

function normalizeLonLatToSvg(lon, lat) {
  const x = ((Number(lon) - 121.05) / 0.8) * 760;
  const y = 520 - ((Number(lat) - 31.0) / 0.55) * 520;
  return {
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2))
  };
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
