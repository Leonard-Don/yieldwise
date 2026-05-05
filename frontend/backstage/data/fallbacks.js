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
        note: "低总价高出租活跃度，适合本地样本演示。",
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
    description: "公开页浏览器抓取样本，保留原始文本、原始坐标、抓取时间与页面快照。",
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
    sourceCount: 3,
    readySourceCount: 3,
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
      sourceId: "shanghai-open-data-community",
      name: "上海开放数据 · 物业小区信息",
      status: "local_ready",
      freshness: "weekly",
      coveragePct: 92,
      listingCount: 128,
      normalizationPct: 96,
      note: "适合做小区字典底座和别名归一。"
    },
    {
      sourceId: "public-browser-sampling",
      name: "浏览器公开页抓取",
      status: "local_ready",
      freshness: "on_demand",
      coveragePct: 58,
      listingCount: 48,
      normalizationPct: 84,
      note: "listing 补样只通过浏览器抓取批次进入。"
    },
    {
      sourceId: "amap-aoi-poi",
      name: "高德 AOI / POI / District",
      status: "local_ready",
      freshness: "on_demand",
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
      sourceId: "public-browser-sampling",
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
      sourceId: "public-browser-sampling",
      rawAddress: "张江汤臣豪园5号楼顶层复式",
      normalizedPath: "浦东新区 / 张江汤臣豪园 / 5号楼 / 待识别单元 / 24层",
      status: "needs_review",
      confidence: 0.79,
      lastActionAt: "2026-04-11 08:42",
      reviewHint: "缺少单元号，建议结合 AOI 和下一轮浏览器抓取补齐。"
    },
    {
      queueId: "addr-003",
      communityId: "qibao-yunting",
      buildingNo: "9幢",
      buildingId: "qibao-yunting-b2",
      floorNo: 12,
      sourceId: "public-browser-sampling",
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
      sourceId: "public-browser-sampling",
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
      sourceId: "public-browser-sampling",
      rawAddress: "闵行区七宝云庭9幢高楼层样本",
      normalizedPath: "闵行区 / 七宝云庭 / 9幢 / 1单元 / 15层",
      status: "needs_review",
      confidence: 0.81,
      lastActionAt: "2026-04-11 20:38",
      reviewHint: "来自浏览器抓取样本，高楼层被折算为 15 层，建议复核。",
      runId: "pudong-demo-2026-04-11-20260411222040",
      batchName: "pudong-demo-2026-04-11"
    }
  ],
  anchorWatchlist: [],
  importRuns: [
    {
      runId: "pudong-demo-2026-04-11-20260411222040",
      providerId: "public-browser-sampling",
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
