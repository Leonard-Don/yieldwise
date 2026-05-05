# API Contract

这份文档描述当前内部研究 Beta 已具备的后端接口。当前约定已经切到“数据库优先、默认空态、显式 mock 开关”。

## Base URL

- 本地开发默认：`http://127.0.0.1:8000`

## Endpoints

### `GET /api/health`

健康检查。

响应示例：

```json
{
  "status": "ok"
}
```

### `GET /api/bootstrap`

返回页面初始化所需的数据，包括：

- `districts`
- `pipeline_steps`
- `schemas`
- `runtime`
- `operations_overview`

行为约定：

- `database` 模式下优先返回 PostgreSQL 聚合结果
- `mock` 模式下才允许返回 demo 数据
- `empty` 模式下返回空数组和 readiness 信息，不伪造研究值

### `GET /api/system/strategy`

返回当前系统采用的：

- 地图主副栈策略
- 坐标策略
- 数据优先级策略
- 数据源清单

当前还会附带：

- `runtime`
- `data_sources`

其中 `data_sources` 是本地数据源清单的就绪视图。

每个数据源条目当前除了基础字段，还会带：

- `platformUrl`
- `applyUrl`
- `docsUrl`
- `guideUrl`
- `applicationMode`
- `recommendedNextStep`
- `contactLabel`
- `contactValue`
- `configuredLocalEnv`
- `missingLocalEnv`
- `matchedLocalConfigSetLabel`

### `GET /api/runtime-config`

返回前端运行时可直接使用的公开配置。

当前包括：

- `amapApiKey`
- `hasAmapKey`
- `amapSecurityJsCode`
- `hasAmapSecurityJsCode`
- `hasPostgresDsn`
- `postgresDsnMasked`
- `mockEnabled`
- `activeDataMode`
- `hasRealData`
- `stagedArtifactsPresent`
- `stagedReferenceRunCount`
- `stagedImportRunCount`
- `stagedGeoRunCount`
- `stagedMetricsRunCount`
- `databaseConnected`
- `databaseReadable`
- `databaseSeeded`
- `latestBootstrapAt`

### `GET /api/map/districts`

查询过滤后的区级地图层和概览统计。

查询参数：

- `district`: `all` 或行政区 id
- `min_yield`: 最低年化回报率
- `max_budget`: 最高总价预算，单位万
- `min_samples`: 最低有效样本量

### `GET /api/map/communities`

返回全市小区真实点位主载荷。

查询参数：

- `district`: `all` 或行政区 id
- `sample_status`: `all / active_metrics / sparse_sample / dictionary_only`
- `focus_scope`: `all / priority`
- `zoom`: 当前前端缩放层级，可选
- `viewport`: 当前地图视窗，可选

每个要素当前至少包含：

- `community_id`
- `district_id`
- `district_name`
- `name`
- `center_lng`
- `center_lat`
- `anchor_source`
- `anchor_quality`
- `anchor_decision_state`
- `sample_status`
- `sample_status_label`
- `yield_pct`
- `sample_size`
- `data_freshness`
- `opportunity_score`

### `GET /api/map/buildings`

返回楼栋级要素集合，重点区默认可直接用于高缩放地图层。

查询参数：

- `district`: `all` 或行政区 id
- `focus_scope`: `all / priority`
- `geometry_quality`: `all / real / fallback`
- `geo_run_id`: 可选几何批次
- `viewport`: 当前地图视窗，可选

### `GET /api/communities/{community_id}`

查询单个小区的详情，包括：

- 小区基础信息
- `centerLng / centerLat`
- `anchorSource / anchorQuality`
- `previewCenterLng / previewCenterLat`
- `previewAnchorSource / previewAnchorQuality`
- `previewAnchorName / previewAnchorAddress`
- `candidateSuggestions`
- `anchorDecisionState`
- `latestAnchorReview`
- `sampleStatus / sampleStatusLabel`
- 楼栋列表
- 所属行政区指标

### `POST /api/communities/{community_id}/anchor-confirmation`

把锚点确认结果写回最新 reference run，默认只支持逐小区人工确认。

请求体支持两种模式：

1. 候选确认

```json
{
  "action": "confirm_candidate",
  "candidate_index": 0,
  "reference_run_id": "optional-run-id",
  "review_note": "已在工作台确认当前候选。"
}
```

手工覆盖入口已移除；如果没有可靠候选，需要补充开放数据或浏览器抓取批次后再确认。

响应会带：

- `community`
- `detail`
- `watchlist`
- `latestAnchorReview`
- `databaseSync`

### `GET /api/buildings/{building_id}`

查询单个楼栋详情，包括：

- 楼栋基础信息
- 低 / 中 / 高楼层收益快照
- 逐层收益曲线 `floorCurve`
- 默认关注楼层 `focusFloorNo`
- 机会评分拆解 `scoreBreakdown`
- 相对小区收益偏离
- 楼栋估算总价与月租
- `quality / decisionBrief` 数据可信度与下一步动作

### `POST /api/v2/decision-memo`

根据前台候选对比列表生成本地 Markdown 研究备忘录。

请求体：

```json
{
  "targets": [
    { "target_id": "zhangjiang-park", "target_type": "community" },
    { "target_id": "zhangjiang-park-b2", "target_type": "building" }
  ]
}
```

约定：

- `target_type` 支持 `community / building / district`
- 单次最多 5 个候选
- 未找到的候选会进入 `missingTargets`，已找到的候选仍会生成备忘录

响应至少包含：

- `generatedAt`
- `targetCount`
- `missingTargets`
- `items[]`
  - `targetId / targetType / name / districtName`
  - `yieldPct / paybackYears / score`
  - `quality`
  - `decisionBrief`
  - `nextSteps / risks`
- `memo`: Markdown 文本

### `GET /api/buildings/{building_id}/floors/{floor_no}`

查询单个楼层的证据明细，包括：

- 楼层收益与估算价格
- `samplePairs` 楼层样本对
- `resolutionTrace` 地址标准化路径
- `queueItems` 相关地址解析队列
- `sourceMix` 当前楼层的数据源混合情况
- `historyTimeline` 当前楼层的跨批次快照时间线
- `historySummary` 当前楼层的跨批次摘要

### `GET /api/ops/overview`

查询当前数据接入与地址标准化总览，包括：

- `summary`
- `runtime`
- `sourceHealth`
- `addressQueue`
- `importRuns`
- `geoAssetRuns`

其中 `summary` 现在还会明确返回：

- `activeDataMode`
- `mockEnabled`
- `hasRealData`
- `cityCoveragePct`
- `buildingCoveragePct`
- `sampleFreshness`
- `latestSuccessfulRunAt`
- `cityCommunityCount`
- `anchoredCommunityCount`
- `anchoredCommunityPct`
- `priorityDistrictBuildingCount`
- `priorityDistrictGeoCoveragePct`
- `pendingAnchorCount`
- `candidateBackedAnchorCount`
- `latestAnchorReviewAt`
- `latestReferenceRunAt`
- `latestListingRunAt`
- `latestGeoRunAt`
- `metricsRunCount`
- `latestMetricsRunAt`
- `latestStagedMetricsRunAt`
- `databaseConnected`
- `databaseReadable`
- `databaseSeeded`
- `latestBootstrapAt`
- `databaseCommunityCount`
- `databaseBuildingCount`
- `databaseSaleListingCount`
- `databaseRentListingCount`
- `databaseGeoAssetCount`
- `latestReferencePersistAt`
- `latestImportPersistAt`
- `latestGeoPersistAt`
- `latestMetricsRefreshAt`
- `latestDatabaseMetricsRefreshAt`
- `metricsRefreshHistory[]`

`metricsRefreshHistory[]` 每条事件当前至少包含：

- `createdAt`
- `batchName`
- `snapshotDate`
- `status / statusLabel`
- `mode / modeLabel`
- `triggerSource / triggerLabel`
- `postgresStatus`
- `summary.communityMetricCount`
- `summary.buildingFloorMetricCount`
- `summary.communityCoverageCount`
- `summary.buildingCoverageCount`
- `error`

### `GET /api/import-runs`

返回当前工作区 `tmp/` 下可发现的浏览器抓取导入批次列表。

说明：

- 当前仍以 listing 类 staging 批次为主
- reference dictionary 批次暂时走独立 jobs 链，不进入这个 API 列表

每个条目包含：

- `runId`
- `providerId`
- `batchName`
- `createdAt`
- `resolvedRate`
- `reviewCount`
- `pairCount`
- `evidenceCount`

### `GET /api/reference-runs`

返回当前工作区 `tmp/reference-runs/` 与 PostgreSQL 中可发现的 reference dictionary 批次列表。

每个条目当前至少包含：

- `runId`
- `providerId`
- `batchName`
- `startedAt`
- `manifestPath`
- `communityCount`
- `anchoredCommunityCount`
- `pendingAnchorCount`
- `source`

### `GET /api/metrics-runs`

返回当前工作区 `tmp/metrics-runs/` 下可发现的 staged metrics 批次列表。

每个条目当前至少包含：

- `runId`
- `batchName`
- `createdAt`
- `snapshotDate`
- `communityMetricCount`
- `buildingFloorMetricCount`
- `communityCoverageCount`
- `buildingCoverageCount`
- `manifestPath`

### `POST /api/jobs/refresh-metrics`

立即触发一轮 staged metrics 快照计算，并在完成后刷新工作台读到的 metrics run 列表。

默认行为：

- 若未传 `snapshot_date`，后端会使用服务端当天日期
- 若未传 `batch_name`，后端会生成 `staged-metrics-YYYY-MM-DD`
- 若前端处于数据库主读且当前已连通 PostgreSQL，可额外传 `write_postgres=true`

请求体示例：

```json
{
  "snapshot_date": "2026-04-17",
  "batch_name": "staged-metrics-2026-04-17",
  "write_postgres": false,
  "apply_schema": false
}
```

响应至少包含：

- `metricsRun`
- `postgres`
- `steps`
- `summary.communityMetricCount`
- `summary.buildingFloorMetricCount`
- `requested.snapshotDate`
- `requested.batchName`
- `requested.writePostgres`
- `requested.triggerSource`

### `GET /api/browser-sampling-pack`

返回当前筛选窗口下最值得继续补的公开页面浏览器抓取任务包。

查询参数：

- `district`: `all` 或行政区 id
- `min_yield`
- `max_budget`
- `min_samples`
- `focus_scope`: `all / priority`
- `limit`

每个任务条目至少包含：

- `taskId`
- `providerId`
- `taskType / taskTypeLabel`
- `targetGranularity`
- `focusScope`
- `priorityScore / priorityLabel`
- `districtId / districtName`
- `communityId / communityName`
- `buildingId / buildingName`
- `floorNo`
- `sampleStatus / sampleStatusLabel`
- `currentYieldPct`
- `currentPairCount / targetPairCount / missingPairCount`
- `currentSampleSize / targetSampleSize / missingSampleCount`
- `reason`
- `captureGoal`
- `targetQuery / saleQuery / rentQuery`
- `requiredFields`
- `recommendedAction`
- `captureHistoryCount`
- `latestCaptureAt / latestCaptureRunId`
- `latestCaptureImportRunId / latestCaptureMetricsRunId`
- `latestCaptureAttentionCount / latestCaptureAttentionPreview`
- `taskLifecycleStatus / taskLifecycleLabel`

返回体还会附带：

- `recentCaptures`: 最近几次公开页浏览器抓取 run
- `summary.capturedTaskCount`
- `summary.attentionTaskCount`
- `summary.latestCaptureAt`

### `GET /api/browser-capture-runs`

返回最近的公开页面浏览器抓取 run 历史。

查询参数：

- `limit`

每条 run 至少包含：

- `runId`
- `createdAt`
- `taskId`
- `taskType / taskTypeLabel`
- `districtId / districtName`
- `communityId / communityName`
- `buildingId / buildingName`
- `floorNo`
- `captureCount / saleCaptureCount / rentCaptureCount`
- `attentionCount / attentionPreview`
- `importRunId`
- `metricsRunId`

### `GET /api/browser-capture-runs/{run_id}`

返回单个公开页面浏览器抓取 run 的完整详情。

至少包含：

- 顶层 run 摘要字段
- `task`
- `baseImportRunId`
- `captures`
- `attention`

其中 `attention` 每条至少包含：

- `businessType / businessTypeLabel`
- `sourceListingId`
- `url`
- `publishedAt`
- `communityName / addressText`
- `buildingText / unitText / floorText / totalFloors`
- `areaSqm / orientation / decoration`
- `priceTotalWan / unitPriceYuan / monthlyRent`
- `rawText`
- `captureNotes`
- `attention`

### `POST /api/browser-sampling-captures`

把浏览器抓取器产出的 `sale / rent raw_text` 写成一批新的 staged 抓取输入，并自动：

- 合并到最新 `public-browser-sampling` 基线批次
- 生成新的 import run
- 刷新一批新的 staged metrics run

请求体示例：

```json
{
  "task_id": "browser-floor::qibao-yunting-b1::8",
  "task": {
    "communityId": "qibao-yunting",
    "communityName": "七宝云庭",
    "districtId": "minhang",
    "districtName": "闵行区",
    "buildingId": "qibao-yunting-b1",
    "buildingName": "3幢",
    "floorNo": 8
  },
  "captures": [
    {
      "business_type": "sale",
      "source_listing_id": "PB-UI-SALE-001",
      "url": "https://example.com/public-sale",
      "published_at": "2026-04-14T13:20:00+08:00",
      "raw_text": "七宝云庭 3幢 8/12层 75.6平 2室1厅1卫 南 精装 总价628万"
    },
    {
      "business_type": "rent",
      "source_listing_id": "PB-UI-RENT-001",
      "url": "https://example.com/public-rent",
      "published_at": "2026-04-14T13:28:00+08:00",
      "raw_text": "七宝云庭 3幢 8/12层 75.1平 2室1厅1卫 南 精装 月租14900元"
    }
  ],
  "refresh_metrics": true
}
```

响应会返回：

- `captureRunId`
- `baseImportRunId`
- `importRunId`
- `metricsRun`
- `summary`
- `attention`
- `reviewSummary`
- `workflow`
- `taskProgress`
- `task`
- `reviewInboxSummary`

其中：

- `reviewSummary`
  - `pendingCount`
  - `resolvedCount`
  - `waivedCount`
  - `supersededCount`
- `workflow`
  - `action`: `review_current_capture | advance_next_capture | stay_current`
  - `reason`: `attention_detected | same_district_queue_available | global_queue_available | no_pending_task`
  - `taskId`: 提交后工作台应聚焦的任务 id
  - `task`: 提交后工作台应聚焦的任务快照；`advance_next_capture` 时由后端直接指定接力目标，避免前端再自行推导
- `taskProgress`
  - `beforeCount`
  - `afterCount`
  - `targetCount`
  - `missingCount`
  - `status`
- `task`
  - 保留当前任务快照，并额外带回 `pendingReviewRunId`、`pendingReviewQueueId`、`pendingAttentionCount`、`pendingAttentionPreview`
- `reviewInboxSummary`
  - `pendingQueueCount`
  - `pendingTaskCount`
  - `pendingDistrictCount`
  - `oldestPendingAt`
  - `latestPendingAt`

### `GET /api/browser-review-inbox`

返回当前公开页采样 review queue 的全局收件箱。

查询参数：

- `district`: `all` 或行政区 id
- `limit`

响应包括：

- `summary`
  - `pendingQueueCount`
  - `pendingTaskCount`
  - `pendingDistrictCount`
  - `oldestPendingAt`
  - `latestPendingAt`
- `items`
  - `inboxItemId`
  - `runId`
  - `queueId`
  - `taskId`
  - `taskLabel`
  - `districtId / districtName`
  - `communityName / buildingName`
  - `businessType / sourceListingId`
  - `attention`
  - `runCreatedAt`
  - `taskPendingAttentionCount`
  - `runPendingCount`

### `GET /api/browser-capture-runs`

返回最近公开页采样批次列表。

每个 run summary 除已有字段外，还会带：

- `attentionCount`: 原始 attention 命中数
- `reviewSummary`
  - `pendingCount`
  - `resolvedCount`
  - `waivedCount`
  - `supersededCount`
- `pendingAttentionPreview`

### `GET /api/browser-capture-runs/{run_id}`

返回单个公开页采样批次详情。

除已有 `captures` / `attention` 外，还会返回：

- `reviewQueue`
  - `queueId`
  - `businessType`
  - `sourceListingId`
  - `attention`
  - `status`: `pending | resolved | waived | superseded`
  - `resolutionNotes`
  - `reviewOwner`
  - `reviewedAt`
  - `replacementRunId`
- `reviewSummary`

### `POST /api/browser-capture-runs/{run_id}/review-queue/{queue_id}`

更新公开页采样批次里的 review queue 条目。

请求体示例：

```json
{
  "status": "waived",
  "resolutionNotes": "已人工核对，当前公开页缺少总层数但可接受。",
  "reviewOwner": "atlas-ui"
}
```

行为约定：

- `status` 仅允许 `resolved` 或 `waived`
- `waived` 必须填写 `resolutionNotes`
- 成功后会返回更新后的 queue item、run 级 `reviewSummary`、任务最新复核态、`workflow`，以及 `reviewInboxSummary`

其中 `workflow` 现在还会带：

- `action`: `review_current_run | review_current_task | advance_next_review | stay_current`
- `reason`: `current_run_pending_remaining | current_task_pending_remaining | same_district_review_available | global_review_available | review_queue_cleared`
- `runId`: 接力目标 run id
- `queueId`: 接力目标 queue id
- `taskId`: 接力目标 task id
- `task`: 接力目标任务快照
- `item`: 接力目标 inbox item 快照；命中下一条 review 目标时由后端直接指定，避免前端再本地推导

### `POST /api/browser-capture-runs/{run_id}/review-queue/batch`

批量更新当前公开页采样批次里的 review queue 条目。

请求体示例：

```json
{
  "queueIds": ["sale::listing-001", "rent::listing-002"],
  "status": "waived",
  "resolutionNotes": "已人工核对，本批次这两条缺失都可接受。",
  "reviewOwner": "atlas-ui"
}
```

行为约定：

- `queueIds` 必填且不能为空
- `status` 仅允许 `resolved` 或 `waived`
- `waived` 必须填写 `resolutionNotes`
- 只会真正更新当前 run 里仍是 `pending` 的条目
- 成功后返回：
  - `updatedQueueItems`
  - `skippedQueueItems`
    - `reason`: `not_found | not_pending | superseded`
  - `reviewSummary`
  - `workflow`
  - `task`
  - `detail`
  - `reviewInboxSummary`

其中 `workflow` 字段约定与单条 review 接口一致，也会直接带回后端选定的接力目标 `item / task / runId / queueId`。

### `POST /api/reference-runs/{run_id}/persist`

把指定 reference batch 写入 PostgreSQL。

请求体示例：

```json
{
  "applySchema": true
}
```

行为约定：

- 若未配置 `POSTGRES_DSN`，返回 `400`
- 若 `run_id` 不存在或缺少 `manifestPath`，返回 `404`
- 成功时返回当前批次写库结果与最新数据库状态

### `POST /api/database/bootstrap-local`

执行本地 PostGIS 首轮引导，固定顺序为：

1. reference
2. import
3. geometry
4. metrics

请求体示例：

```json
{
  "reference_run_id": "optional-reference-run-id",
  "import_run_id": "optional-import-run-id",
  "geo_run_id": "optional-geo-run-id",
  "applySchema": true,
  "refreshMetrics": true
}
```

行为约定：

- 若未配置 `POSTGRES_DSN`，返回 `400`
- 未显式传 run id 时，默认取各自最新批次
- `reference` 是首轮引导的必需步骤
- `import` / `geometry` 缺失时会返回 `skipped`，不会阻塞整条引导链
- 成功时返回每一步的 `status / runId / persistedAt` 和最新数据库快照

### `GET /api/geo-assets/runs`

返回当前工作区 `tmp/geo-assets/` 下可发现的几何批次列表。

每个条目包含：

- `runId`
- `providerId`
- `batchName`
- `assetType`
- `createdAt`
- `featureCount`
- `resolvedBuildingCount`
- `unresolvedFeatureCount`
- `communityCount`
- `coveragePct`
- `taskCount`
- `openTaskCount`
- `reviewTaskCount`
- `captureTaskCount`

### `GET /api/geo-assets/runs/{run_id}`

返回单个几何批次的详情，包括：

- `coverage`
- `coverageGaps`
- `taskSummary`
- `coverageTasks`
- `reviewHistoryCount`
- `recentReviews`
- `workOrders`
- `workOrderSummary`
- `workOrderEventCount`
- `recentWorkOrderEvents`
- `comparison`
- `featurePreview`
- `unresolvedFeatures`
- `outputPaths`

可选查询参数：

- `baseline_run_id`

其中 `comparison` 会在存在上一批几何基线时返回：

- `baselineRunId`
- `baselineBatchName`
- `coveragePctDelta`
- `resolvedBuildingDelta`
- `missingBuildingDelta`
- `openTaskDelta`
- `captureTaskDelta`
- `resolvedTaskDelta`
- `newBuildingCount`
- `removedBuildingCount`
- `changedGeometryCount`
- `topBuildingChanges`

其中 `taskSummary` 现在还会额外提供：

- `criticalOpenTaskCount`
- `highPriorityOpenTaskCount`
- `watchlistLinkedTaskCount`
- `avgImpactScore`

其中 `coverageTasks` 每条还会额外提供：

- `taskScopeLabel`
- `impactScore`
- `impactBand`
- `impactLabel`
- `watchlistHits`
- `watchlistFloors`
- `recommendedAction`
- `communityScore`
- `buildingOpportunityScore`
- `workOrderId`
- `workOrderStatus`
- `workOrderStatusLabel`
- `workOrderAssignee`

其中 `workOrderSummary` 额外提供：

- `workOrderCount`
- `activeWorkOrderCount`
- `assignedWorkOrderCount`
- `inProgressWorkOrderCount`
- `deliveredWorkOrderCount`
- `closedWorkOrderCount`
- `linkedTaskCount`
- `unassignedOpenTaskCount`

### `GET /api/geo-assets/runs/{run_id}/compare`

单独返回某个几何批次相对上一批几何基线的差异摘要。

可选查询参数：

- `baseline_run_id`

### `GET /api/geo-assets/runs/{run_id}/work-orders`

返回某个几何批次当前已经生成的补采工单列表。

可选查询参数：

- `district`
- `status`
- `assignee`
- `limit`

每个条目包含：

- `workOrderId`
- `status`
- `statusLabel`
- `assignee`
- `title`
- `taskIds`
- `taskCount`
- `primaryTaskId`
- `focusFloorNo`
- `focusYieldPct`
- `impactScore`
- `watchlistHits`
- `linkedTasks`
- `createdAt`
- `updatedAt`

其中 `status` 支持：

- `all`
- `open`
- `assigned`
- `in_progress`
- `delivered`
- `closed`

### `POST /api/geo-assets/runs/{run_id}/work-orders`

从一个或多个几何任务生成补采工单。

请求体：

- `taskIds`
- `assignee`
- `dueAt`
- `notes`
- `createdBy`

返回：

- `workOrderId`
- `workOrder`
- `detail`
- `databaseSync`

### `POST /api/geo-assets/runs/{run_id}/work-orders/{work_order_id}`

推进补采工单状态。

请求体：

- `status`
- `assignee`
- `notes`
- `changedBy`

当前支持的工单状态：

- `assigned`
- `in_progress`
- `delivered`
- `closed`

### `GET /api/import-runs/{run_id}`

返回单个浏览器抓取导入批次的详情，包括：

- `reviewQueue`
- `reviewHistoryCount`
- `recentReviews`
- `topEvidence`
- `comparison`
- `attention`
- 以及用于前端楼层证据绑定的批次元数据

可选查询参数：

- `baseline_run_id`

其中 `comparison` 会在存在上一批基线时返回：

- `baselineRunId`
- `baselineBatchName`
- `resolvedRateDeltaPct`
- `reviewCountDelta`
- `pairCountDelta`
- `evidenceCountDelta`
- `newFloorCount`
- `removedFloorCount`
- `avgYieldDeltaPct`
- `topFloorChanges`

### `GET /api/import-runs/{run_id}/compare`

单独返回某个批次相对上一批基线的差异摘要。

可选查询参数：

- `baseline_run_id`

适合后续做：

- 独立的批次对比页面
- 跨批次榜单
- 指标日报 / 飞书推送

### `POST /api/import-runs/{run_id}/persist`

把某个浏览器抓取导入批次整体写入 PostgreSQL。

请求体：

```json
{
  "applySchema": false
}
```

### `POST /api/import-runs/{run_id}/review-queue/{queue_id}`

回写单条地址标准化复核结果，并同步更新：

- `address_resolution_queue.json`
- `normalized_sale.json`
- `normalized_rent.json`
- `review_history.json`
- `summary.json`
- `manifest.json`

请求体：

```json
{
  "status": "resolved",
  "resolutionNotes": "已由工作台人工复核确认。",
  "reviewOwner": "atlas-ui"
}
```

### `POST /api/geo-assets/runs/{run_id}/persist`

把某个几何批次整体写入 PostgreSQL，包括：

- `geo_assets`
- `geo_asset_capture_tasks`
- `geo_asset_review_events`

请求体：

```json
{
  "applySchema": false
}
```

### `POST /api/geo-assets/runs/{run_id}/tasks/{task_id}`

回写单条几何任务状态，并同步更新：

- `coverage_tasks.json`
- `review_history.json`
- `summary.json`
- `manifest.json`

请求体：

```json
{
  "status": "scheduled",
  "resolutionNotes": "已派工给 GIS。",
  "reviewOwner": "atlas-ui"
}
```

### `GET /api/opportunities`

查询机会榜条目。

查询参数：

- `district`
- `min_yield`
- `max_budget`
- `min_samples`
- `geo_run_id`
- `geo_run_id`
- `min_score`

### `GET /api/floor-watchlist`

查询跨批次“持续套利楼层榜”。

可选查询参数：

- `run_id`
- `baseline_run_id`

只有满足样本阈值的楼层才会进入这份榜单。

返回条目包括：

- `communityId`
- `buildingId`
- `floorNo`
- `latestYieldPct`
- `windowYieldDeltaPct`
- `yieldDeltaSinceFirst`
- `observedRuns`
- `totalPairCount`
- `persistenceScore`
- `trendLabel`

### `GET /api/geo-task-watchlist`

查询当前几何批次下、会直接影响地图定位和套利判断的“补采工单榜”。

可选查询参数：

- `district`
- `geo_run_id`
- `limit`
- `include_resolved`

返回条目包括：

- `taskId`
- `communityId`
- `buildingId`
- `taskScope`
- `taskScopeLabel`
- `status`
- `statusLabel`
- `impactScore`
- `impactBand`
- `impactLabel`
- `watchlistHits`
- `focusFloorNo`
- `focusYieldPct`
- `focusTrendLabel`
- `targetGranularity`
- `recommendedAction`
- `workOrderId`
- `workOrderStatus`
- `workOrderStatusLabel`
- `workOrderAssignee`
- `geoAssetRunId`
- `geoAssetBatchName`

### `GET /api/geo-assets/buildings`

返回当前筛选窗口内的楼栋 footprint GeoJSON。

查询参数：

- `district`
- `min_yield`
- `max_budget`
- `min_samples`
- `geo_run_id`

每个要素当前包含：

- `building_id`
- `building_name`
- `community_id`
- `community_name`
- `yield_avg_pct`
- `yield_spread_vs_community`
- `opportunity_score`
- `center_lng`
- `center_lat`
- `geometry_source`
- `geo_asset_run_id`
- `geo_asset_batch_name`
- `geo_asset_provider_id`
- `svg_points`
- `svg_center`

其中 `svg_points / svg_center` 目前主要保留给前端调试、导出和几何兜底计算使用，不再承担旧的 SVG 地图渲染职责。

行为约定：

- `database` 模式下优先读取 `geo_assets`
- 数据库缺几何时允许标记为 `fallback / gap`
- `empty` 模式下返回空 features

### `GET /api/geo-assets/floor-watchlist`

返回当前筛选窗口和研究批次对应的楼层 footprint GeoJSON，供前端楼层粒度直接绘制。

可选查询参数：

- `district`
- `min_yield`
- `max_budget`
- `min_samples`
- `run_id`
- `baseline_run_id`
- `geo_run_id`
- `limit`

每个要素当前包含：

- `building_id`
- `building_name`
- `floor_no`
- `latest_yield_pct`
- `window_yield_delta_pct`
- `yield_delta_since_first`
- `latest_pair_count`
- `persistence_score`
- `latest_batch_name`
- `baseline_batch_name`
- `center_lng`
- `center_lat`
- `geometry_source`
- `geo_asset_run_id`
- `geo_asset_batch_name`
- `geo_asset_provider_id`
- `svg_points`
- `svg_center`

行为约定同上，且导出与页面筛选窗口保持一致。

### `GET /api/export/geojson`

按筛选条件导出 GeoJSON。

### `GET /api/export/kml`

按筛选条件导出 KML，适合导入 Google Earth 做演示或巡检。

### `GET /api/export/floor-watchlist.geojson`

按当前筛选条件、当前批次和可选基线批次导出“持续套利楼层榜” GeoJSON。
当前默认导出为楼层 footprint `Polygon`，如果缺少 footprint 映射则回退到 `Point`。

可选查询参数：

- `district`
- `min_yield`
- `max_budget`
- `min_samples`
- `run_id`
- `baseline_run_id`
- `geo_run_id`
- `limit`

每个要素会附带：

- `latest_yield_pct`
- `window_yield_delta_pct`
- `yield_delta_since_first`
- `latest_pair_count`
- `window_pair_count_delta`
- `persistence_score`
- `latest_batch_name`
- `baseline_batch_name`

### `GET /api/export/floor-watchlist.kml`

按当前筛选条件、当前批次和可选基线批次导出“持续套利楼层榜” KML，适合直接导入 Google Earth 做楼层套利巡检。
当前默认导出为楼层 footprint 面对象。

### `GET /api/export/geo-task-watchlist.geojson`

按当前行政区和几何批次导出“几何补采优先级榜” GeoJSON。

可选查询参数：

- `district`
- `geo_run_id`
- `limit`
- `include_resolved`

每个要素会附带：

- `task_id`
- `task_scope`
- `task_scope_label`
- `status`
- `status_label`
- `impact_score`
- `impact_band`
- `impact_label`
- `watchlist_hits`
- `focus_floor_no`
- `focus_yield_pct`
- `focus_trend_label`
- `work_order_id`
- `work_order_status`
- `work_order_status_label`
- `work_order_assignee`
- `recommended_action`
- `geo_asset_run_id`
- `geo_asset_batch_name`
- `geometry_source`

如果楼栋在当前字典中存在，会优先导出楼栋 footprint `Polygon`；如果只有小区级锚点，则回退为 `Point`。

### `GET /api/export/geo-task-watchlist.csv`

按当前行政区和几何批次导出“几何补采优先级榜” CSV，适合直接作为 GIS / 数据团队的补采工单输入。

### `GET /api/export/browser-sampling-pack.csv`

按当前行政区和筛选窗口导出“公开页面浏览器抓取任务包” CSV，适合直接作为当天抓取清单。

字段包含：

- 任务类型与粒度
- 当前样本量 / 目标样本量
- 当前回报率
- `sale / rent` 检索词
- 建议复制字段
- 推荐动作与补样原因

包含字段：

- `geo_asset_run_id`
- `geo_asset_batch_name`
- `district_name`
- `community_name`
- `building_name`
- `task_id`
- `task_scope`
- `status`
- `impact_score`
- `impact_label`
- `watchlist_hits`
- `focus_floor_no`
- `focus_yield_pct`
- `work_order_id`
- `work_order_status`
- `work_order_assignee`
- `recommended_action`

### `GET /api/export/geo-work-orders.geojson`

按当前行政区、几何批次、工单状态和责任人导出“几何补采工单榜” GeoJSON。

可选查询参数：

- `district`
- `geo_run_id`
- `status`
- `assignee`
- `limit`

每个要素会附带：

- `work_order_id`
- `title`
- `status`
- `status_label`
- `assignee`
- `task_count`
- `task_ids`
- `primary_task_id`
- `focus_floor_no`
- `focus_yield_pct`
- `impact_score`
- `impact_band`
- `watchlist_hits`
- `due_at`
- `created_at`
- `updated_at`
- `geo_asset_run_id`
- `geo_asset_batch_name`
- `geometry_source`

如果楼栋在当前几何批次里已有 footprint，会优先导出为 `Polygon`；否则回退成小区 / 楼栋锚点 `Point`。

### `GET /api/export/geo-work-orders.csv`

按当前行政区、几何批次、工单状态和责任人导出“几何补采工单榜” CSV，适合直接发给 GIS / 数据处理团队排班。

包含字段：

- `geo_asset_run_id`
- `geo_asset_batch_name`
- `district_name`
- `community_name`
- `building_name`
- `work_order_id`
- `title`
- `status`
- `status_label`
- `assignee`
- `task_count`
- `task_ids`
- `primary_task_id`
- `focus_floor_no`
- `focus_yield_pct`
- `impact_score`
- `impact_band`
- `watchlist_hits`
- `due_at`
- `created_at`
- `updated_at`
- `created_by`
- `notes`

## 下一步扩展建议

1. 把 `samplePairs` 替换成真实出售 / 出租配对样本。
2. 为 `GET /api/buildings/{building_id}/floors/{floor_no}` 增加真实单元号与原始快照链接。
3. 增加鉴权与抓取任务状态接口。
