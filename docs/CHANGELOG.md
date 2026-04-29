# Changelog

记录 Phase 6 起的迭代节奏。每条目对应一个或多个 PR/合并 commit。

按 spec `docs/internal/superpowers/specs/2026-04-23-user-facing-platform-design.md` 推进；spec 第 3 节路由布局已 100% 兑现，第 4 节后端拆分已 100% 兑现，前端 `app.js` 拆分按机械切片渐进推进至 ~19%。

---

## 2026-04-28 — Phase 8i: 数据模式 + 运行选择辅助

`refactor(backstage): extract data-mode + run-selection helpers (4e9293a)`

- 抽 5 个数据模式辅助到 `lib/data-mode.js`：`canUseDemoFallback`、`currentDataMode`、`applyDataModeDefaults`、`effectiveOperationsOverview`、`districtDirectory`
- 抽 5 个运行选择辅助到 `lib/run-selection.js`：`ensureImportRunSelection`、`ensureGeoAssetRunSelection`、`normalizeGeoWorkOrderFilters`、`availableGeoBaselineRunsFor`、`availableBaselineRunsFor`
- 把 `mapWaypointTone` 并到 `lib/format.js`
- `app.js`: 10215 → 10077（-138 行）

## 2026-04-28 — Fix: pwcli 单次 eval 上限从 8s 抬到 30s

`fix(scripts): bump pwcli per-eval timeout from 8s to 30s (f4d5c79)`

- `npx --yes --package @playwright/cli` 自身启动开销 ~5s/次，原来 8s cap 实际只剩 ~3s 给 `page.evaluate`，cold-session 调用必超时
- 新增 `browser_capture_smoke.PWCLI_EVAL_TIMEOUT_SECONDS = 30`，可用 `ATLAS_PWCLI_EVAL_TIMEOUT` env 覆盖
- 三个脚本（`browser_capture_smoke.py` / `browser_review_smoke.py` / `full_browser_regression.py`）共用同一常量
- 修复后 `python3 scripts/full_browser_regression.py` 25 步全绿

## 2026-04-28 — Phase 8h: 路由 + hydrate 辅助

`refactor(backstage): extract routing + hydrate helpers (98799d3)`

- 11 个 URL/tab 路由辅助 → `lib/routing.js`：`normalize{Workspace,Backstage,OperationsHistory,OperationsDetail,OperationsQuality}{View,Tab}` + `initial*FromLocation` 系列 + `initialOperationsSelectionParamFromLocation`
- 2 个数据 hydrate 辅助 → `lib/hydrate.js`：`hydrateDistrictsPayload`、`hydrateCommunity`
- `app.js`: 10314 → 10215（-99 行）

## 2026-04-28 — Phase 8g: fallback / mock 数据构造器

`refactor(backstage): extract fallback/mock builders (9034e9b)`

- 8 个 fallback 数据构造器 → `lib/fallback-builders.js`：`buildFallbackBuildingDetail`、`buildFallbackImportRunDetail`、`buildFallbackGeoAssetRunComparison`、`buildFallbackGeoAssetRunDetail`、`buildFallbackFloorDetail`、`buildFallbackSamplePairs`、`buildFallbackResolutionTrace`、`buildScoreBreakdown`
- 这些函数读 `state.*` / `districts` / `mapCommunities` 全局，靠 classic-script 共享作用域在调用时解析
- `app.js`: 10920 → 10314（-606 行）

## 2026-04-28 — Phase 8f: geometry / 查找辅助

`refactor(backstage): extract pure geometry/lookup helpers (d51c097)`

- 24 个纯函数 → `lib/geometry.js`：`clamp`、`bucketForFloor`、`hydrateBuilding`、`communityCenter`、`communityAnchorPreview`、`interpolateFloorYield`、`buildFloorCurve`、`buildingSvgPoint`、`floorSvgPoint`、`footprint{Dimensions,Polygon,Centroid,PathToLonLat}`、`buildingFootprintPoints`、`floorFootprintPoints`、`polygonPointsAttribute`、`fallbackDistrictPolygonPath`、`polygonCenterLonLat`、`featureSvg{Points,Center}`、`featureLonLat{Path,Center}`、`normalizeSvgToLonLat`、`normalizeLonLatToSvg`
- `app.js`: 11204 → 10920（-284 行，首次跌破 11000）

## 2026-04-28 — Phase 8d: util 函数

`refactor(backstage): extract pure utility helpers (dcde93e)`

- 28 个纯函数 → `lib/util.js`：时间比较器、tone/color 类、几何运算、任务谓词/比较器、capture 计数器、采样计数器、`browserSamplingCoverageState/Label/Progress`
- `app.js`: 11384 → 11204（-180 行）

## 2026-04-28 — Phase 8c: format / label 函数

`refactor(backstage): extract pure format/label helpers (41b61ca)`

- 32 个纯函数 → `lib/format.js`：`truncate`、`slugifyExportName`、`formatSignedNumber/Delta`、`searchScore`、`searchTypeLabel`、`yieldClass`、`granularityLabel`、`anchorDecisionLabel`、`mapWaypointSourceLabel` + 4 个 `metricsRefresh*Label` + 6 个 `browserSampling*Label` + 4 个 `browserCaptureReview*Label` + `providerModeLabel` / `sourceStatusLabel` / `queueStatusLabel` / `geoTaskStatusLabel` / `geoWorkOrderStatusLabel` / `geoWorkOrderFilterLabel` / `resolutionStatusLabel` 等
- `app.js`: 11646 → 11384（-262 行）

## 2026-04-28 — Phase 8b: DOM selectors + UI 常量

`refactor(backstage): extract DOM selectors + UI constants (e6a43b3)`

- 58 个 `document.querySelector` 句柄 → `data/dom.js`
- 5 个 UI tab 数组（`workspaceViews`、`backstageTabs`、`operationsHistoryTabs`、`operationsDetailTabs`、`operationsQualityTabs`）→ `data/constants.js`
- `app.js`: 11709 → 11646（-63 行）

## 2026-04-28 — Phase 8a: fallback 数据常量

`refactor(backstage): extract fallback data constants (2ec4eac)`

- 5 个 fallback 数据常量 → `data/fallbacks.js`：`fallbackDistricts`、`fallbackPipelineSteps`、`fallbackSchemas`、`fallbackOperationsOverview`、`emptyOperationsOverview`
- `app.js`: 12392 → 11709（-683 行，首次结构化拆分）

**Phase 8 累计：app.js 12392 → 10077 行，-2315 行（-18.7%）；新增 `frontend/backstage/lib/`（8 模块）+ `data/`（3 文件）。**

---

## 2026-04-27 — Phase 7g: 导入指向 backstage 模块

`refactor(api): rewire importers to backstage modules direct (8826f98)`

- `api/main.py` / `persistence.py` / `domains/*` / `tests/conftest.py` / `jobs/*` 中的 `from .service import` 改为直接 `from .backstage.{runs,review,geo_qa,anchors} import`
- `clear_runtime_caches` 用 lazy import 避开 service.py 顶部 shim 依赖
- backstage/* 内部跨模块 lazy import 改为指向兄弟模块（runs/review/geo_qa/anchors 之间）
- service.py 顶部仍保留 4 块 backstage import 作为 service.py 自身内部依赖（不再是外部 shim）

## 2026-04-26 / 2026-04-27 — Phase 7a-7f: api/service.py 拆分（spec §4 完工）

按 spec 第 4 节 backstage 拆分指引推进，service.py 10674 → 5927 行（-44.5%）。

| Phase | 子模块 | 函数数 | 移出行数 | commit |
|---|---|---|---|---|
| 7a | `api/backstage/runs.py` | 23 | 347 | `4eb8ef2` |
| 7b | `api/backstage/review.py`（capture run） | 19 | 335 | `b361d93` |
| 7c | `api/backstage/review.py`（inbox/fixture） | 13 | 500 | `bcdfe99` |
| 7d | `api/backstage/review.py`（sampling pack/submit） | 17 | 1256 | `6791886` |
| 7e1 | `api/backstage/geo_qa.py`（helpers） | 25 | 620 | `9d3ef3a` |
| 7e2 | `api/backstage/geo_qa.py`（detail/compare） | 14 | 745 | `e77f269` |
| 7e3 | `api/backstage/geo_qa.py`（work-order CRUD） | 5 | 490 | `d8dde0b` |
| 7f | `api/backstage/anchors.py` | 12 | 454 | `162f240` |

**累计 128 函数迁出，零行为变化。`api/backstage/`：runs(411) + review(2235) + geo_qa(1970) + anchors(525) = 5141 行 / 128 函数。**

---

## 2026-04-26 — Phase 6g: hover 微动画

`feat(user): hover transitions for chips + board row left-bar slide-in (c8d4a7d)`
`feat(user): drawer/search/banner button transitions + lift effects (177ae68)`

- mode chip / filter chip clear / prefs button / help chip 加 120ms transition
- board row 永久 2px transparent 左边框，hover 时颜色淡入到 `var(--up)`，避免 reflow
- drawer × close 旋 90° + 红底；★ star hover scale(1.12) / active scale(0.94)
- search row / search close / banner 切换按钮全部统一 120ms ease-out

## 2026-04-26 — Phase 6f: 区级变化提醒

- 扩展 `Alert` schema 支持 district 类型 + `district_delta_up/down` kind
- `compute_alerts` 在区均租售比跨阈值时 emit district 级 alert
- `/alerts` 端点 since-last-open + mark-seen 同时遍历 districts
- 用户前台 banner formatter 处理 district_delta：「区均租售比 N% → M% (±D)」

## 2026-04-26 — Phase 6e: 区抽屉 + 区下钻

- `/api/v2/districts/{id}` 返回区级聚合（KPI bar + topN 小区列表）
- 用户抽屉 `renderBody` 按 `sel.type` 分支：district 跳过 floor chart，渲染区级 KPI + 小区列表
- 小区行点击 → 切换 `selectedTarget` 触发抽屉重新加载

## 2026-04-26 — Phase 6d: ⌘K 全局搜索

- `/api/v2/search` 端点遍历 districts→communities→buildings，纯函数 search-scoring
- 前端 search overlay：输入框 + 结果列表 + 上下键导航 + Enter 选中
- ⌘K 在 frontend 模式三键里加快捷键

## 2026-04-26 — Phase 6c: 视觉细节

- board / drawer body / notes / help / onboarding form 加滚动阴影
- drawer 加 shimmer skeleton 替代 loading 文字

## 2026-04-26 — Phase 6b: 变化提醒解析目标名

- alerts diff 链路把 `target_name` 从规则反解到 banner row
- 「关注 zhangjiang-park 跌破阈值」→「张江汤臣豪园 跌破阈值」

## 2026-04-26 — Phase 6a: 键盘快捷键

- `parseShortcut` 解析 `⌘K` / `⌘1` / `⌘2` / `⌘3` / `F` / `N` / `?`
- shortcuts 模块根据 dispatched key 派发到模式切换、关注、笔记、帮助
- 帮助浮层 + topbar `?` chip

---

## 验证基线

每轮 phase 结束都跑：
```bash
pytest -q                                                              # 123 passed
ATLAS_ENABLE_DEMO_MOCK=1 python3 scripts/phase1_smoke.py               # 21 routes OK
node --check frontend/backstage/{data,lib}/*.js frontend/backstage/app.js
node --check frontend/user/modules/*.js
python3 -m compileall api jobs scripts                                 # exit 0
```

定期跑：
```bash
ATLAS_ENABLE_DEMO_MOCK=1 uvicorn api.main:app --port 8013 &
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/backstage/  # 25 steps
```

最近一次完整浏览器回归：`output/playwright/atlas-rerun-fixed.json`，25/25 通过。
