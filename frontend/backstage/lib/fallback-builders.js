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

