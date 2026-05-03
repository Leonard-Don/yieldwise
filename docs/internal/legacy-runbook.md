# Yieldwise · 租知

[![Validate](https://github.com/Leonard-Don/shanghai-yield-atlas/actions/workflows/validate.yml/badge.svg)](https://github.com/Leonard-Don/shanghai-yield-atlas/actions/workflows/validate.yml)

**租赁资产投研工作台 · 拿房选址 / 估值 / 投后一张地图**

<p align="center">
  <img src="docs/screenshots/atlas-workbench-overview.png" alt="Yieldwise workbench overview" width="100%" />
</p>

<p align="center">
  <img src="docs/screenshots/atlas-ops-workbench.png" alt="Yieldwise ops workbench" width="100%" />
</p>

面向个人本地研究的租赁资产工作台。把公开资料、手工采样、历史快照和地图几何数据收进同一张地图，做选址观察、租售比估算和样本复核三个核心工作流。

## 这个仓库现在是什么

- 一个面向单用户研究的本地工具 `/`（Phase 6 完工）：三模式（收益猎手 / 自住找房 / 全市观察）+ 关注夹 + 笔记 + 变化提醒 + ⌘K 全局搜索 + 区抽屉
- 一个 FastAPI 本地工作台：页面、接口和 staged/database 运行态保持一致
- 一条 staged 优先的数据流水线：reference / import / geo / metrics 可逐批落盘
- 一条公开页补样闭环：任务包、原文录入、attention review queue、relay contract、browser smoke 都已接通
- 一套几何补采与质量控制面板：覆盖缺口、工单、基线对比、导出接口都在同一页

### 当前能力 / 已知限制

**能力**
- 用户平台 `/`：三模式（Yield / Home / City）+ 抽屉 KPI + 关注夹（★）+ 笔记 + 变化横幅 + ⌘K 搜索 + 区下钻
- 研究台 `/backstage`：原研究台整体保留，运营/复核/几何 QA 都在此
- 三态运行（staged / database / mock），`ATLAS_ENABLE_DEMO_MOCK=1` 控制 mock fallback
- 浏览器回归 25/25 步全绿，pytest 123 项 + smoke 21 路由 + `node --check` 全套 JS 文件全绿

**已知限制（spec 之后的增量，不在当前交付范围）**
- **`frontend/backstage/app.js` 还有 10077 行未拆分**：Phase 8 已抽出 9 个独立模块（`data/` × 3 + `lib/` × 8），但 `app.js` 主体仍然是经典脚本而非 ES module。**当前路线决定：继续 Phase 8 增量切片（A 路线），不做一次性 ES module 重写**。理由：spec 未强制；增量切片每步可独立验证（pwcli + node --check）；一次性重写需要重排全局 `state` 生命周期、风险中等。下次有功能改动时优先把动到的逻辑抽到 `lib/*.js` 或 `data/*.js`，而不是在 `app.js` 主体内追加。`/` 用户平台则继续保持 ES module 纯度，与 backstage 互不干涉。
- **`tmp/browser-capture-runs/` 状态不可逆**：`reviewBrowserCaptureQueueItem` 会修改 `review_queue.json` 把 attention 标记为 resolved；`browser-review-fixtures/` 里的 fixture 删除会回滚原状，但不要批量手动删除 capture run 目录
- **pwcli 默认 30s 单次 eval 上限**：在更慢的机器上请用 `ATLAS_PWCLI_EVAL_TIMEOUT=60` 等覆盖

## 路由布局（Phase 8i 起）

| 路径 | 绑定 | 说明 |
| --- | --- | --- |
| `/` | `frontend/user/` | 用户平台。收益模式 + 详情抽屉（含区级 KPI + 区内小区下钻）+ 筛选条 + 自住模式 + 全市模式 + 关注夹（★）+ 笔记 + 变化横幅（含目标名解析）+ 键盘快捷键（⌘K 搜索、⌘1/2/3 切模式、F 关注、N 笔记、? 帮助）。 |
| `/backstage` | `frontend/backstage/` | 原研究台，所有运营/复核/几何 QA 在此 |
| `/api/*` | `api/service.py` + `api/backstage/{runs,review,geo_qa,anchors}.py`（Phase 7 完工） | 传统接口，backstage 前端使用 |
| `/api/v2/*` | `api/domains/` | 用户平台专属接口。已开放：`/health`、`/opportunities`、`/map/{districts,communities,buildings}`、`/buildings/{id}`、`/communities/{id}`、`/districts/{id}`、`/user/prefs` (GET + PATCH)、`/watchlist` (GET + POST + DELETE)、`/annotations` (GET-by-target + POST + PATCH + DELETE)、`/alerts/{rules,since-last-open,mark-seen}` (GET + PATCH + POST)、`/search` (GET) |

要直接打开研究台请访问 `http://127.0.0.1:8000/backstage/`。`/` 在 Phase 1 结束时是一个空的 D1 shell。

## GitHub 首页速看

| 模块 | 现在能做什么 |
| --- | --- |
| Map Surface | 行政区、小区、楼栋、楼层四级研究入口，支持高德真地图和 footprint drill-down |
| Ops Workbench | 运行总览、批次与快照、运行细节、采样与质量都收成 panel/workbench 结构 |
| Public Browser Sampling | 生成采样任务、录入公开页原文、提交 capture、处理 attention review queue |
| Geo Asset QA | 看几何覆盖缺口、生成工单、追踪状态、导出 GeoJSON / CSV |
| Runtime Modes | `staged` / `database` / `mock` 三种模式明确可见，不再偷偷 fallback |

## 30 秒启动

```bash
uvicorn api.main:app --reload --port 8000
```

- 用户平台：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- 研究台（原主页）：[http://127.0.0.1:8000/backstage/](http://127.0.0.1:8000/backstage/)

如果你只想先做一轮静态和浏览器侧校验，最短路径是：

```bash
python3 -m compileall api jobs scripts
for f in frontend/backstage/{data,lib}/*.js frontend/backstage/app.js frontend/user/modules/*.js; do node --check "$f" || break; done
python3 scripts/phase1_smoke.py
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/backstage/
```

## 仓库导览

| 路径 | 用途 |
| --- | --- |
| `frontend/user/` | 用户平台（Phase 6）：D1 终端风格 shell + 三模式 + 抽屉 + 关注夹 + 笔记 + alerts + ⌘K 搜索 |
| `frontend/backstage/` | 研究台（迁自原主页），`app.js` 已抽出 `data/`（3 文件，常量 + DOM handle）和 `lib/`（8 模块，纯辅助）；`app.js` 仍含运行时与渲染主体 |
| `api/` | FastAPI 接口、领域查询、runtime 状态、review / relay contract |
| `api/domains/` | 用户平台 v2 接口（opportunities / map / buildings / communities / districts / user_prefs / watchlist / annotations / alerts / search） |
| `api/backstage/` | spec §4 Phase 7 拆分产物：`runs.py`（411）+ `review.py`（2235）+ `geo_qa.py`（1970）+ `anchors.py`（525）；service.py 仅保留共享业务逻辑 |
| `api/service.py` | 后台共享业务逻辑（5927 行，从 10674 减下来），顶部 import 把 backstage 模块拉回供自身内部使用 |
| `jobs/` | reference / import / geo / metrics / materialize 等离线任务 |
| `scripts/` | browser smoke、full regression、本地联调辅助脚本 |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Phase 6 起的迭代节奏，按时间倒序 |
| [`docs/api-contract.md`](docs/api-contract.md) | 页面与后端 contract、workflow / relay 字段说明 |
| [`docs/import-public-browser-capture.md`](docs/import-public-browser-capture.md) | 公开页补样导入、review queue、回归脚本说明 |
| [`docs/strategy.md`](docs/strategy.md) | 研究台定位、阶段路线与数据策略 |
| [`docs/superpowers/`](docs/superpowers/) | 当前迭代周期的 spec / plan / 子阶段任务底稿 |

## 当前运行原则

这轮开始，系统运行约定已经明确成：

- 地图和详情接口优先读 PostgreSQL + PostGIS
- 默认不再偷偷回退 demo 数据
- 没有真实数据时，页面显示明确空态、source readiness 和 staging 状态
- 只有显式设置 `ATLAS_ENABLE_DEMO_MOCK=true` 时，才允许 mock fallback
- 本地数据源批次统一拆成 `sale_rent_batch`、`dictionary_batch`、`geometry_batch` 三类

## 当前能力概览

- 地图前台：上海区级、小区级、楼栋级、楼层级联动研究面
- 数据后场：reference、import、metrics、geo 四类 run 的查看、切换、写库和基线对比
- 小区锚点：预锚点候选、人工确认、审计历史、主档写回
- 公开页补样：任务包、capture submit、attention review queue、review relay、定向 smoke
- 几何补采：缺口发现、影响分、工单流转、责任人筛选、GeoJSON / CSV 导出
- 指标与榜单：机会榜、逐层机会带、研究窗口感知楼层榜、跨批次收益历史
- 导出与复用：KML、GeoJSON、CSV 和 staged manifest / summary 输出

## 如何运行

这轮默认先用 `staged` 研究模式，不要求先起 Docker 或数据库。

如果你后面想切到 PostgreSQL 主读，再使用下面这条本地开发 DSN：

```bash
postgresql://atlas:atlas_local_dev@127.0.0.1:5432/shanghai_yield_atlas
```

推荐直接跑 FastAPI，这样页面、接口和运行时数据模式会一起生效：

1. 在当前目录启动一个静态服务，比如：

```bash
uvicorn api.main:app --reload --port 8000
```

2. 浏览器打开 `http://127.0.0.1:8000`

如果在启动前设置了 `AMAP_API_KEY`，页面会自动启用高德真地图；否则页面会保留真地图容器并提示你补齐高德配置。

如果你的高德 Web 端应用启用了安全密钥，建议同时配置 `AMAP_SECURITY_JSCODE`，前端会在加载 JSAPI 前自动注入 `window._AMapSecurityConfig`。

如果已经配置 `POSTGRES_DSN` 且数据库里有真实批次，页面会进入 `database` 模式；如果数据库已连接但还没 seed 完成，页面会继续显示 staged 数据，但会明确提示“本地库未完成首轮 bootstrap”。

只有在显式开启：

```bash
ATLAS_ENABLE_DEMO_MOCK=true uvicorn api.main:app --reload --port 8000
```

时，前端和导入脚手架才会允许使用 demo 数据联调。

如果你只是想快速看纯前端原型，也可以继续用静态服务：

```bash
npx serve .
```

这个模式下 `/api/*` 接口不会存在，页面会进入空态壳，而不是自动注入模拟值。

## 锚点确认闭环

现在工作台已经支持在 `小区锚点待补榜` 中直接做两件事：

- `确认当前候选`：把当前预锚点写回最新 reference run
- `手工覆盖坐标`：直接录入 `GCJ-02` 坐标并写回主档

写回会同步更新：

- `community_dictionary.json`
- `community_dictionary_enriched.csv`
- `reference_catalog.json`
- `anchor_report.json`
- `anchor_review_history.json`
- `manifest.json / summary.json`

如果已经配置 `POSTGRES_DSN`，后端还会尽力把这次确认同步到数据库里的 `communities / community_aliases / anchor_review_events`；即使数据库同步失败，本地 staged 主档也不会丢。

## 本地环境变量

项目现在会自动读取根目录下的 `.env.local` 和 `.env`。推荐把你自己的真实 key 放进 `.env.local`，不要直接改 `.env.example`。

最小示例：

```bash
AMAP_API_KEY=your_amap_key
AMAP_SECURITY_JSCODE=your_amap_security_js_code
POSTGRES_DSN=postgresql://atlas:atlas_local_dev@127.0.0.1:5432/shanghai_yield_atlas
```

## 如何跑授权导入演示

如果你已经拿到一批授权导出的出售 / 出租 `CSV`，或者只是先用模板试跑，可以直接执行：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id authorized-import \
  --batch-name "pudong-demo-2026-04-11" \
  --sale-file data/templates/authorized_sale_template.csv \
  --rent-file data/templates/authorized_rent_template.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-11
```

字段模板和输出说明见 `docs/import-authorized-data.md`。

## 如何跑 reference dictionary 导入

这条链用来把“行政区 / 小区 / 楼栋主档与别名”正式写成 reference catalog，供后续 listing / geometry 导入复用：

```bash
python3 jobs/import_reference_dictionary.py \
  --provider-id shanghai-open-data \
  --batch-name "shanghai-reference-seed" \
  --district-file data/templates/district_dictionary_template.csv \
  --community-file data/templates/community_dictionary_template.csv \
  --building-file data/templates/building_dictionary_template.csv \
  --output-dir tmp/reference-runs/shanghai-reference-seed
```

配置 `POSTGRES_DSN` 后，还可以直接落库：

```bash
python3 jobs/load_reference_dictionary_to_postgres.py \
  --manifest tmp/reference-runs/shanghai-reference-seed/manifest.json
```

如果你后面想直接完成本地首轮引导，而不是分别手动点三次 persist，可以执行：

```bash
python3 jobs/bootstrap_local_postgres.py
```

这条命令会按固定顺序执行：

1. 应用 `db/schema.sql`
2. 落最新 reference run
3. 落最新 import run
4. 落最新 geo run
5. 刷新并写入 metrics snapshot

说明见 `docs/import-reference-dictionary.md`。

如果数据库主档还没落好，也可以把这批导出的 `reference_catalog.json` 挂到 `ATLAS_REFERENCE_CATALOG_FILE`，先给 listing / geometry 导入当离线主档用。

## 如何跑 staged metrics run

如果你暂时不切数据库主读，但想让小区榜单、楼栋详情和楼层证据统一读同一批日更指标，可以直接生成一批 staged metrics run：

```bash
python3 jobs/refresh_metrics.py \
  --date 2026-04-14 \
  --batch-name "staged-metrics-2026-04-14"
```

运行后会在 `tmp/metrics-runs/` 下生成：

- `snapshot.json`
- `summary.json`
- `manifest.json`

前端在 `staged` 模式下会自动读取最新一批 metrics run，并把它当成当前研究口径；所以即使还没配 PostgreSQL，机会榜、小区详情和楼栋分桶也会统一到同一批快照时间。

## 如何跑全市小区锚点 enrichment

如果你已经整理了一份上海全市小区主档，可以先用高德 Web 服务把小区中心点补出来，再导成新的 reference batch：

```bash
python3 jobs/enrich_community_anchors.py \
  --district-file data/public-snapshot/2026-04-12/district_dictionary_seed.csv \
  --community-file data/public-snapshot/2026-04-12/community_dictionary_seed.csv \
  --output-file tmp/reference-runs/shanghai-citywide-reference-2026-04-12/community_dictionary_enriched.csv \
  --report-file tmp/reference-runs/shanghai-citywide-reference-2026-04-12/anchor_report.json \
  --web-service-key $AMAP_WEB_SERVICE_KEY
```

接着再导入成 reference batch：

```bash
python3 jobs/import_reference_dictionary.py \
  --provider-id shanghai-open-data \
  --batch-name "shanghai-citywide-reference-2026-04-12" \
  --district-file data/public-snapshot/2026-04-12/district_dictionary_seed.csv \
  --community-file tmp/reference-runs/shanghai-citywide-reference-2026-04-12/community_dictionary_enriched.csv \
  --building-file data/public-snapshot/2026-04-12/building_dictionary_seed.csv \
  --output-dir tmp/reference-runs/shanghai-citywide-reference-2026-04-12
```

## GitHub 协作与持续更新

仓库现在已经带了最小的 GitHub 协作骨架：

- `.github/workflows/validate.yml`
  - 每次 `push / pull_request` 会跑：
    - `python3 -m compileall api jobs scripts`
    - `node --check frontend/backstage/app.js`
- `.github/ISSUE_TEMPLATE/public-sampling-task.yml`
  - 用来派发公开页人工采样任务
- `.github/ISSUE_TEMPLATE/bug-report.yml`
  - 用来记录页面、导入链和地图联动问题

如果你要继续加公开页样本，建议先看：

- `CONTRIBUTING.md`
- `docs/public-sampling-backlog.md`

这样后面不管是自己补样本，还是把采样任务分给别人，口径都会更统一。

这条链跑完后，`/api/map/communities` 会直接返回全市真实小区点位；当前仓库已经自带一版全市小区主档与 staged 锚点 snapshot。

如果你不想手动拆这几步，现在也可以直接一键物化整套 staged public snapshot：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14
```

这条命令会固定按：

1. reference dictionary
2. community anchor enrichment
3. public-browser-sampling listing import
4. manual geometry staging import
5. metrics run refresh

的顺序把 staging 研究面全部更新一遍。

如果你这次拿到的是浏览器人工采样的 capture CSV，也可以直接并进这条链：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14 \
  --browser-capture-file path/to/capture.csv
```

## 如何跑公开页面辅助采样

如果手头还没有正式 API，只想先用公开页面做 staging 补洞，可以走 `public-browser-sampling`：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id public-browser-sampling \
  --batch-name "public-browser-sampling-2026-04-12" \
  --sale-file data/public-snapshot/2026-04-12/public_browser_sampling_sale.csv \
  --rent-file data/public-snapshot/2026-04-12/public_browser_sampling_rent.csv \
  --output-dir tmp/import-runs/public-browser-sampling-2026-04-12
```

这批样本会继续走统一的地址标准化、配对和楼层证据链，并明确标成 staging-only，不会伪装成官方实时接口。

如果你手里只有浏览器里人工复制下来的公开页面文本，不想自己先拆成 `sale / rent CSV`，现在也可以直接跑：

```bash
python3 jobs/import_public_browser_capture.py \
  --batch-name "public-browser-capture-2026-04-14" \
  --capture-file data/templates/public_browser_capture_template.csv \
  --output-dir tmp/browser-capture-runs/public-browser-capture-2026-04-14
```

它会先把 `raw_text` 自动拆成 `captured_sale.csv / captured_rent.csv`，再继续调用标准 `public-browser-sampling` 导入链。说明见 `docs/import-public-browser-capture.md`。

工作台里现在还新增了一块“公开页面采样任务包”：

- 会优先把高回报但样本偏薄的楼层排成 `楼层补样`
- 其次把高分楼栋排成 `楼栋加深`
- 再把全市研究盘里样本不足的小区排成 `小区补面`

每条任务都会给出：

- 推荐补样原因
- 当前样本量与目标样本量
- `sale / rent` 公开页检索词
- 建议复制的字段清单

如果你想直接在 Atlas 页面里执行，不用手工拼 CSV：

- 右侧点任一采样任务的“录入原文”
- 在 `Ops` 区的“公开页面采样执行台”里粘贴 `sale / rent` 原文、URL、发布时间
- 点击“生成采样批次并刷新”

这条链会：

- 把最新 `public-browser-sampling` 批次当成基线
- 只把你新粘贴的公开页样本合并进去，不会把全市 staged 盘面冲掉
- 自动生成新的 import run 和 staged metrics run
- 让地图、机会榜、楼栋详情和楼层证据立即吃到新口径

工作台里的采样任务现在还会带上进度语义：

- `待采样`：这个任务还没有公开页面原文历史
- `已采仍需补采`：已经采过，但当前样本仍没达到目标阈值
- `已采待复核`：最近一次采样里有 `attention`，建议先回看原文或补齐字段

“公开页面采样执行台”下方也会展示：

- 当前任务最近几次采样
- 最近公开页采样批次
- 每次采样是否含 `attention`
- 最近一次并入的 import run / metrics run

如果某次采样里出现了 `attention`：

- 工作台顶部的“全局待复核收件箱”会先把当前区最该处理的 pending 条目排出来
- 点击那次采样批次
- 或者直接点连续补样快捷台里的 `下一个待复核`
- 执行台会展开对应批次的 `review queue 回看面板`
- 直接看到哪一条 sale / rent 原文缺少楼栋、楼层、总层数、总价或月租
- 可以一键把那条原文回填到对应草稿，再补字段后重新提交

如果你想把这条“公开页采样写路径”做成可重复回归，不用再手点一遍：

```bash
python3 scripts/browser_capture_smoke.py --url http://127.0.0.1:8013/
```

这个脚本会：

- 用真实浏览器读取当前“公开页面采样执行台”
- 自动填写当前选中任务的 `sale / rent` 原文
- 点击“生成采样批次并刷新”
- 校验按钮能退出 `导入中...`
- 校验新的 import run / staged metrics run 已经落盘
- 把浏览器快照写到 `output/playwright/`

默认会复用 `atlas-smoke` 会话并以 headless 模式运行，不会再额外弹出一串浏览器图标；如果你想肉眼观察执行过程，可以加 `--headed`。如果你想复用已经打开的 Atlas 页面，可以显式传 `--session default`；如果你希望强制新开一个独立会话，可以再加 `--fresh-session`。

如果你想顺手把整张 Atlas 研究台也做一次真实浏览器回归，而不只是验证采样提交流程，可以再跑：

```bash
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/backstage/
```

它会覆盖全局观测、行政区覆盖卡片、行政区筛选、采样覆盖看板联动、连续补样快捷台跳转、机会榜点击、楼栋/楼层粒度切换，以及所有导出接口是否还能正常返回。

如果你想把今天要采的任务直接导出来，可以在页面右侧点“导出采样 CSV”，或者调用：

```bash
curl "http://127.0.0.1:8000/api/export/browser-sampling-pack.csv"
```

如果你想直接看“昨天 vs 今天”的批次变化，还可以再跑一组第二天样本：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id authorized-import \
  --batch-name "pudong-demo-2026-04-12" \
  --sale-file data/demo/authorized_sale_demo_2026-04-12.csv \
  --rent-file data/demo/authorized_rent_demo_2026-04-12.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-12
```

跑完后，工作台里的导入批次详情会自动出现“相对基线批次的变化”区块，你也可以手动切到更老的批次做窗口比较。

如果你已经拿到一批授权导出的楼栋 footprint `GeoJSON`，还可以把空间几何单独导入：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints" \
  --geojson-file data/demo/building_footprints_demo.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints
```

导入后，楼栋 / 楼层地图会优先读取这批 footprint；如果某些楼栋还没有几何资产，前端会自动回退到本地推导几何。

如果是研究阶段自己手工勾绘的一批重点区楼栋 footprint，则建议走 `manual-geometry-staging`：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id manual-geometry-staging \
  --batch-name "manual-priority-geometry-2026-04-14" \
  --geojson-file data/public-snapshot/2026-04-12/manual_priority_building_footprints.geojson \
  --output-dir tmp/geo-assets/manual-priority-geometry-2026-04-14
```

这样工作台里会明确把它标成 staging 几何，而不是伪装成官方 AOI。
现在工作台里还能直接切换不同几何批次，查看该批次的目录覆盖率、缺口楼栋和未命中 feature；导出的楼层榜 `GeoJSON / KML` 也会跟着携带当前 `geo_run_id`。
这轮还新增了几何补采工单流，所以高影响缺口楼栋可以直接在工作台里生成工单、推进到“执行中 / 待验收 / 已关闭”，并在下一版 footprint 回灌前持续追踪；现在还可以按状态和责任人在工作台里筛选，并直接导出 `GeoJSON / CSV` 给 GIS 团队接单。

如果你想直接看“上一版 footprint vs 当前版 footprint”的变化，我还补了一组历史基线样本：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints-baseline" \
  --geojson-file data/demo/building_footprints_demo_previous.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints-baseline
```

跑完后，在工作台里点当前几何批次，就可以用“对比基线”下拉切到这版历史样本，直接看新增覆盖楼栋、几何修正和打开任务变化。

如果已经配置 `POSTGRES_DSN`，几何批次也能单独落库：

```bash
python3 jobs/load_geo_asset_run_to_postgres.py \
  --manifest tmp/geo-assets/demo-building-footprints/manifest.json
```

## 本地数据库主读如何切换

工作台现在会明确区分三种本地数据库状态：

- `未配置`：没有 `POSTGRES_DSN`
- `待引导`：DSN 已配置、数据库可连通，但还没完成首轮 bootstrap
- `已引导`：reference / import / geo / metrics 都已落库，前端进入 `database` 主读

前端 `Ops` 面板里现在有：

- `Reference 主档批次 -> 写入 PostgreSQL`
- `Import 批次 -> 写入 PostgreSQL`
- `Geo 批次 -> 写入 PostgreSQL`
- `本地 Bootstrap` 一键引导按钮

如果已经跑出了一个批次 manifest，还可以继续把它写进 PostgreSQL：

```bash
python3 jobs/load_import_run_to_postgres.py \
  --manifest tmp/import-runs/pudong-demo-2026-04-11/manifest.json
```

如果你希望首次落库时顺手执行 `db/schema.sql`，可以加上 `--apply-schema`。

## 现在多了什么

- `api/main.py`：FastAPI 服务，提供 bootstrap、机会榜、geo-assets、楼层明细、运维总览和导出接口
- `api/provider_adapters.py`：本地数据源清单、批次契约和就绪规则
- `api/reference_catalog.py`：数据库 / 文件 / mock 三层 reference catalog 读取
- `api/service.py`：数据库优先的领域查询、小区 / 楼栋 / 楼层证据明细、批次复核回写、几何任务回写、几何基线对比和 GeoJSON / KML 生成逻辑
- `api/persistence.py`：授权批次、几何批次和 reference dictionary 写入 PostgreSQL 的持久化层
- `db/schema.sql`：PostgreSQL + PostGIS 建表稿
- `docs/api-contract.md`：接口说明
- `docs/import-authorized-data.md`：授权导入字段模板与批次说明
- `docs/import-reference-dictionary.md`：reference dictionary 导入说明
- `docs/strategy.md`：地图 / 数据 / 坐标 / 地址标准化策略
- `data/templates/`：授权出售 / 出租 CSV 模板
- `data/templates/*dictionary_template.csv`：district / community / building 主档模板
- `data/demo/`：用于跨批次对比演示的第二批样本
- `data/demo/building_footprints_demo_previous.geojson`：几何批次基线对比样本
- `jobs/import_authorized_listings.py`：授权导入、地址标准化和楼层配对脚手架
- `jobs/import_reference_dictionary.py`：district / community / building 主档导入脚手架
- `jobs/enrich_community_anchors.py`：用高德 Web 服务给小区主档补真实锚点
- `jobs/import_geo_assets.py`：授权 `GeoJSON` 几何批次导入脚手架
- `jobs/load_geo_asset_run_to_postgres.py`：把几何批次、缺口任务和任务历史写入 PostgreSQL
- `jobs/load_import_run_to_postgres.py`：把授权批次和逐层证据写入 PostgreSQL
- `jobs/load_reference_dictionary_to_postgres.py`：把 reference dictionary 批次写入 PostgreSQL
- `jobs/refresh_metrics.py`：指标快照任务脚手架
- `.env.example`：高德地图与本地辅助任务的环境变量模板

## 原型定位

这个版本仍然是“内部研究系统 Beta”，不是对外交付物。当前地图已经会按小区 / 楼栋 / 楼层三种粒度切换，并在楼栋 / 楼层视图里优先读取后端 `geo-assets` 返回的 footprint 面图；当数据库或几何主档为空时，页面会明确显示空态、覆盖缺口和 staging 状态，而不是伪造结果。现阶段 demo 坐标仍然是示意级，不是最终精确上海楼栋底图；楼层结果仍然更偏证据层，不把“全市楼层精确覆盖”当作当前阶段交付标准。

## 下一步怎么接真实项目

1. 先用 `jobs/import_reference_dictionary.py` 把上海行政区 / 小区 / 楼栋主档落进 PostgreSQL。
2. 再用 `docs/import-authorized-data.md` 的模板接一批真实授权 listing 数据，跑通地址标准化和楼层证据。
3. 用 `jobs/load_import_run_to_postgres.py` 把 listing 批次落进 PostgreSQL。
4. 用 `jobs/import_geo_assets.py` 和 `jobs/load_geo_asset_run_to_postgres.py` 逐步补齐楼栋 footprint。
5. 继续提升真实底图质量，把重点区楼栋 footprint 与公开页采样证据做得更厚。
6. 用楼层榜导出按钮把当前批次 / 基线窗口导出成 `KML` 或 `GeoJSON`，给内部分析或 Google Earth 巡检使用。
7. 把 `jobs/refresh_metrics.py` 改成真实定时任务，并接上数据库写入。
8. 保持离线导入和手工公开样本路线；不把本地工作台升级成外部平台自动拉取器。

## 建议的后续拆分

- `frontend/`：后续可迁移到 Next.js + React 页面
- `api/`：FastAPI 指标与导出接口
- `db/`：建表 SQL 与空间索引
- `jobs/`：采集、清洗、去重、指标快照任务
