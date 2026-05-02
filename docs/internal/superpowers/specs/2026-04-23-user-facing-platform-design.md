# User-Facing Platform Design

- **Status**: Draft (pending user review)
- **Date**: 2026-04-23
- **Scope**: 把现有 `/` 研究台（developer-facing workbench）改造成面向单用户的本地研究工具 `/`，原研究台整体迁到 `/backstage`。实施过程中顺带完成 `api/service.py` 和 `app.js` 两个单文件的领域拆分。

## 1. 背景与目标

项目 Shanghai Yield Atlas 目前是一个面向开发/运营的研究台：run 对比、review queue、几何工单、runtime mode 切换等 ops 面板占据主前台。实际主用户只有 1 人（localhost 部署），且该用户在三种场景间切换：

1. **收益猎手**（Yield Hunter）：找租售比高、值得持有的楼栋
2. **自住找房**（Home Finder）：在预算 / 区域 / 面积约束下挑自己住的房
3. **全市观察**（City Observer）：看区域分布、趋势、挂牌量变化

这次改造的目标是把主前台变成贴合这三种场景的本地研究工具，同时保留研究台的 ops 能力作为"后台入口"。

### 非目标

- 不做多用户账号系统、权限、审计日志
- 不上现代前端构建链（Vite / Webpack / TS）
- 不重写业务逻辑，只做领域拆分和界面重构
- 不迁移 `api/persistence.py` / `provider_adapters.py` / `reference_catalog.py` / `mock_data.py`

## 2. 约束与原则

- **部署**：localhost 单用户，`.env.local` 模式延续；不引入 auth、TLS、session
- **无构建工具**：使用浏览器原生 ES modules（`<script type="module">`）+ 必要时 import map
- **向后兼容**：现有 `/api/*` 端点全部保留，backstage 前端零改动
- **Runtime 模式不动**：`staged / database / mock` 三态感知保留；`ATLAS_ENABLE_DEMO_MOCK` 策略不变
- **渐进交付**：每个 phase 结束仓库都是可用产品，任何时候可停

## 3. 路由

| 路径 | 绑定 | 状态 |
| --- | --- | --- |
| `/` | 新用户平台（`frontend/user/index.html`） | 新建 |
| `/backstage` | 现有研究台（`frontend/backstage/index.html`） | 迁移 |
| `/api/v2/*` | 用户前台专属 API | 新建 |
| `/api/*` | 现有 API | 保留，backstage 继续用 |

`api/main.py` 保持瘦：聚合 domain routers + 静态文件挂载。

## 4. 整体架构

### 后端（Python / FastAPI）

`api/service.py`（10,674 行）按领域拆分到 `api/domains/`：

```
api/
├── main.py                    # router 聚合（保持瘦）
├── domains/                   # 新建：用户前台领域
│   ├── __init__.py
│   ├── opportunities.py       # 机会榜、机会分、排序
│   ├── buildings.py           # 楼栋详情、楼层、挂牌
│   ├── communities.py         # 小区详情、归属楼栋
│   ├── map_tiles.py           # 地图聚合 endpoint（按 zoom 给不同聚合）
│   ├── watchlist.py           # 关注夹 CRUD（新能力）
│   ├── annotations.py         # 笔记 CRUD（新能力）
│   ├── alerts.py              # 变化检测 + 未读标记（新能力）
│   └── user_prefs.py          # 视图状态持久化（可选）
├── backstage/                 # 新建：研究台保留模块
│   ├── __init__.py
│   ├── runs.py                # reference / import / geo / metrics 运行态
│   ├── review.py              # browser sampling + attention review queue
│   ├── geo_qa.py              # 几何缺口工单、责任人
│   └── anchors.py             # 锚点确认、审计历史
├── persistence.py             # 不动
├── provider_adapters.py       # 不动
├── reference_catalog.py       # 不动
└── mock_data.py               # 不动
```

**拆分策略**：按 `service.py` 里现有函数的前缀/关键词机械迁移，**不重写业务逻辑**。每个 domain 暴露一个 `APIRouter`。`api/main.py` 顺序挂载：

```python
from api.domains import opportunities, buildings, communities, map_tiles, watchlist, annotations, alerts, user_prefs
from api.backstage import runs, review, geo_qa, anchors

app.include_router(opportunities.router, prefix="/api/v2")
app.include_router(buildings.router, prefix="/api/v2")
# ... 共用 domain
app.include_router(runs.router, prefix="/api")         # legacy path for backstage
# ...
```

旧 `/api/*` 路径映射到 `backstage/` 模块下的同名函数，保证 backstage 前端不用改。

### 前端（Vanilla ES Modules）

现有 `index.html` / `styles.css` / `app.js` 整体搬到 `frontend/backstage/`。新用户前台：

```
frontend/
├── backstage/                 # 迁移：现有研究台整体搬进来
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── user/                      # 新建：用户平台
    ├── index.html
    ├── styles/
    │   ├── tokens.css         # D1 色板、字体、间距、阴影 CSS 变量
    │   ├── shell.css          # topbar / mode chips / layout grid
    │   ├── map.css            # 地图容器、浮层
    │   ├── board.css          # 机会榜
    │   └── detail.css         # 抽屉
    └── modules/
        ├── main.js            # 入口：组合各 module + 启动 state
        ├── shell.js           # topbar + mode chips + 状态栏
        ├── map.js             # 高德地图包装（继承 backstage 坐标转换逻辑）
        ├── opportunity-board.js
        ├── detail-drawer.js
        ├── watchlist.js
        ├── annotations.js
        ├── alerts.js          # 变化横幅
        ├── modes.js           # 三模式配置表（色/榜列/默认筛选/抽屉重点）
        ├── api.js             # fetch 封装 + response cache
        └── state.js           # 轻量 pub/sub store（mode / filters / viewport / selection）
```

**状态管理**：自写的 ~50 行 pub/sub store，不引 Redux/Zustand。
**模块通信**：仅通过 state store；禁止模块之间直接 import。

### 前端加载顺序（`frontend/user/index.html`）

```html
<link rel="stylesheet" href="/frontend/user/styles/tokens.css">
<link rel="stylesheet" href="/frontend/user/styles/shell.css">
<!-- ... -->
<script type="module" src="/frontend/user/modules/main.js"></script>
```

## 5. 页面骨架（D1 金融终端 + B 布局）

### 视觉基调

- 深色底：`--bg-0: #070a10` / `--bg-1: #0a0e14` / `--bg-2: #0f1823`
- 分隔：`--line: #1a2332`
- 文字：`--text-0: #cfd6e0` / `--text-dim: #7a8494` / `--text-xs: #5a6a80`
- 语义色：`--up: #00d68f` / `--down: #ff4d4d` / `--warn: #ffb020`
- 字体：UI `Inter`；数字 `ui-monospace, 'SF Mono', 'JetBrains Mono'`，`font-variant-numeric: tabular-nums`

### 区域（自上而下）

1. **变化横幅**（可收起）：自上次打开以来关注对象的变化摘要，展开成时间线
2. **顶栏**：Logo · 模式切换（`⌘1/2/3`）· ⌘K 搜索 · 关注计数 · 变化计数 · 笔记入口 · 后台入口
3. **筛选条**：模式专属默认筛选 chip，可增减，右端显示命中条数
4. **主体（flex: 1.6 / 1）**
   - **地图**（左）：高德地图；按模式着色；楼栋 / 小区 / 区 三级聚合切换；★ 标记关注；图例浮层；坐标浮层
   - **机会榜**（右）：按当前视野 + 筛选排序；列由模式配置；选中高亮；★ 标记；空态提示；虚拟滚动（列表大时）
5. **楼栋透视抽屉**：点击地图标记或榜单条目从右滑入，覆盖榜单列。包含 KPI 条、楼层分布柱、挂牌列表、笔记区、操作（★、✎、关）
6. **状态栏**：数据源（staged/database/mock）· 快照时间 · 批次号 · 样本量 · 后台跳转

### 三模式语义

| 维度 | 收益猎手 · Yield | 自住找房 · Home | 全市观察 · City |
| --- | --- | --- | --- |
| 地图色 | 租售比梯度：红 <3.5 / 琥珀 3.5-5 / 绿 ≥5 | 总价相对预算：绿=预算内/琥珀=轻超/红=远超 | 行政区聚合涂色：Δ 均值（涨绿跌红） |
| 默认聚合粒度 | 楼栋 | 楼栋 | 区（街道作为后续升级项，见 Phase 6） |
| 榜单排序 | 租售比 ↓ | 单价 ↑ | Δ 均租售比 ↓ |
| 榜单列 | 名称 · 租售比 · Δ30d | 名称 · 总价 · 单价 | 区 · 均租售比 · Δ30d |
| 默认筛选 | 租售比 ≥ 4% · 总价 500–1500 万 | **必填**预算 + 区域 + 面积 | 无筛选 |
| 抽屉 KPI 重点 | 租售比 / 均价 / 均租 / 机会分 + 楼层分布 | 总价 / 单价 / 户型 / 通勤分钟 + 近距配套 | 区均租售比 / 挂牌量 / 6-12-24 月趋势 / 分位数 |
| 变化提醒触发 | 租售比跨 ±0.5% · 新挂牌 · 机会分跳变 ≥5 | 预算内新挂 · 关注对象降价 ≥3% | 区级指标跨 ±1% · 挂牌量突变 |

### 跨模式共用行为

- 搜索 ⌘K、关注夹、笔记、抽屉里的`楼栋/楼层/挂牌`始终存在
- 模式切换不跳路由；URL 带 `?mode=yield|home|city` 可作书签
- 筛选和视野 **按模式分别记忆**（切回仍是上次状态）
- 地图聚合粒度可覆盖默认（顶栏 `楼栋 / 小区 / 区` 切换）

### 自住模式首次引导

首次进入 Home 模式，弹出一次性引导弹窗收集：预算（万元区间）、优先区域、面积区间、可选 office anchor（用于 Phase 6 通勤计算；未填则跳过通勤列）。写入 `data/personal/user_prefs.json`，下次不再弹；顶栏"偏好"入口可随时改。

## 6. 数据模型与个人化层

### 存储分层

| 数据 | 存储 | 跨浏览器 | 备注 |
| --- | --- | --- | --- |
| mode / filters / viewport / drawer state | `localStorage` | 否 | 刷新即恢复 |
| 关注夹 | `data/personal/watchlist.json` | 是 | API 中介 |
| 笔记 | `data/personal/annotations.json` | 是 | API 中介 |
| 变化提醒 baseline | `data/personal/alerts_state.json` | 是 | 用于 diff |
| 提醒阈值规则 | `data/personal/alert_rules.json` | 是 | 出厂默认 + 用户覆盖 |
| Home 模式 onboarding 结果 | `data/personal/user_prefs.json` | 是 | 预算/区域/面积 |

### `data/personal/` 目录

```
data/
└── personal/
    ├── watchlist.json
    ├── annotations.json
    ├── alerts_state.json
    ├── alert_rules.json
    ├── user_prefs.json
    └── .trash/                # 每次写入前自动备份，保留最近 20 份
```

- `.gitignore` 追加 `data/personal/`
- 每次写入前把当前版本复制到 `.trash/YYYY-MM-DDTHH-MM-SS-<file>.json`；超过 20 份删最旧
- 使用 `fcntl.flock` 在写入前加文件锁，冲突 retry 1 次后报错
- 所有写入前用 pydantic schema 校验；校验失败返回 422

### Schemas（简版）

```python
class WatchlistEntry(BaseModel):
    target_id: str
    target_type: Literal["building", "community"]
    added_at: datetime
    last_seen_snapshot: dict | None

class Annotation(BaseModel):
    note_id: str                  # uuid
    target_id: str
    target_type: Literal["building", "community", "floor", "listing"]
    body: str                     # markdown
    created_at: datetime
    updated_at: datetime

class AlertsState(BaseModel):
    baselines: dict[str, dict]    # target_id -> {yield, price, listing_count, ...}
    last_open_at: datetime

class AlertRules(BaseModel):
    yield_delta_abs: float = 0.005        # ±0.5%
    price_drop_pct: float = 0.03          # ≥3%
    listing_new: bool = True
    district_delta_abs: float = 0.01      # ±1%
```

### API（`/api/v2/*`）

```
# 地图 & 榜单
GET    /api/v2/opportunities?mode=&bbox=&filters=...
GET    /api/v2/map/buildings?bbox=&zoom=
GET    /api/v2/map/communities?bbox=&zoom=
GET    /api/v2/map/districts
GET    /api/v2/buildings/{id}
GET    /api/v2/communities/{id}

# 关注夹
GET    /api/v2/watchlist
POST   /api/v2/watchlist                    {target_id, target_type}
DELETE /api/v2/watchlist/{target_id}

# 笔记
GET    /api/v2/annotations/by-target/{target_id}
POST   /api/v2/annotations                  {target_id, target_type, body}
PATCH  /api/v2/annotations/{note_id}        {body}
DELETE /api/v2/annotations/{note_id}

# 变化提醒
GET    /api/v2/alerts/since-last-open
POST   /api/v2/alerts/mark-seen
GET    /api/v2/alerts/rules
PATCH  /api/v2/alerts/rules                 {...rules}

# 用户偏好
GET    /api/v2/user/prefs
PATCH  /api/v2/user/prefs                   {budget, districts, area_min, area_max, office_anchor?}

# 视图状态镜像（可选 Phase 6）
GET    /api/v2/user/view-state
PATCH  /api/v2/user/view-state
```

### 变化提醒计算时机

**客户端主动触发**，无后台 cron：

1. 页面加载 → `GET /api/v2/alerts/since-last-open`
2. 服务端读 `alerts_state.json`（上次快照）+ 当前 staged/database 值 + `alert_rules.json`
3. 计算 diff，返回结构化变化列表
4. 前端渲染为顶部横幅
5. 用户点"标记已读" → `POST /mark-seen` → 服务端把当前值写进 `alerts_state.json` 作为新 baseline

### 未来升级路径（不在本次实施范围）

"你 + 合伙人共用"场景只需把 `data/personal/` 替换为 PG 表（同 schema + `user_id` 列）。前端不变，API URL 不变，只改 persistence 层。

## 7. 实施分期

### Phase 1 · 脚手架（1–2 天）

- 迁移 `index.html` / `styles.css` / `app.js` → `frontend/backstage/`；路由指向 `/backstage`
- 创建 `frontend/user/` 壳（D1 tokens + 空 topbar + 空 map div + 空 board）
- 创建 `api/domains/` + `api/backstage/` 目录骨架
- 挂 `/api/v2/*` 前缀
- pytest 基线：`tests/api/test_v2_health.py`
- 扩 `scripts/full_browser_regression.py` 覆盖两路由

**验收**：backstage 功能零损失；`/` 空壳能开；`python -m compileall` + `node --check` + 浏览器回归全绿。

### Phase 2 · 地图 + 机会榜（3–4 天）

- 从 `service.py` 切出 `opportunities.py` / `buildings.py` / `communities.py` / `map_tiles.py`
- `map.js` 接管高德地图（搬用现成坐标转换、绘制）
- `opportunity-board.js` 订阅 state store，按视野+筛选查接口
- 收益模式端到端通；自住 / 全市 chip stub 但可切
- mode state store + URL `?mode=yield` 同步

**验收**：看到上海、租售比热力、点击标记高亮、榜单随视野变。

### Phase 3 · 详情抽屉 + 三模式全通（3–4 天）

- `detail-drawer.js`：KPI 条 / 楼层分布 SVG / 挂牌列表
- `modes.js`：把三套配置化
- 自住模式 budget onboarding 弹窗
- 全市模式区级聚合 endpoint
- mode-specific filter persistence

**验收**：三模式切换流畅；每模式的地图色 / 榜列 / 默认筛选正确；抽屉重点随模式切换。

### Phase 4 · 关注夹 + 笔记（2–3 天）

- `data/personal/` JSON 存储 + `fcntl.flock` + 自动 `.trash/` 备份
- `watchlist.py` / `annotations.py` domain（pydantic schema）
- `watchlist.js` + `annotations.js`
- 顶栏 ★ 计数；抽屉内 ★ 按钮、笔记编辑器

**验收**：加 / 删 / 改都生效；重启 uvicorn 后数据还在；手动改坏 JSON 重启有清晰报错。

### Phase 5 · 变化提醒（2 天）

- `alerts.py`：diff 逻辑 + 阈值规则
- `/since-last-open` + `/mark-seen`
- 顶部变化横幅组件

**验收**：改一条 staged 数据 → 刷新 → 横幅出现正确变化 → 标记已读 → 刷新横幅消失。

### Phase 6 · 打磨（2–3 天）

- 自住模式通勤分钟（高德 routing + daily batch cache；进入 Home 模式时按 `onboarding` 中的 office anchor 与当前视野内楼栋对调用，结果缓存到 `tmp/commute-cache/YYYY-MM-DD.json`，同一天复用）
- 全市模式街道聚合（若数据密度够）
- 键盘快捷键：`⌘K` 搜索、`⌘1/2/3` 切模式、`F` 加关注、`N` 写笔记
- 可选：`view-state` 服务端镜像
- 视觉细节（滚动阴影、骨架屏、hover 微动画）

**总工期**：13–18 天单人全职，可按 phase 拆分异步推进。

## 8. 验证策略

### 自动化

- **后端 pytest**：每个 domain 模块一份测试，mock `persistence` 层，覆盖关键路径
  - `tests/api/domains/test_opportunities.py`（排序、机会分）
  - `tests/api/domains/test_watchlist.py`（文件锁、备份、schema 校验）
  - `tests/api/domains/test_alerts.py`（diff 逻辑、阈值触发）
- **前端语法**：`node --check` 每个 `.js` 文件
- **浏览器回归**：`scripts/full_browser_regression.py` 扩两套场景
  - `/` 三模式核心流（切换、搜索、加关注、看详情）
  - `/backstage` 回归（确认没改坏）
- **CI**：`.github/workflows/validate.yml` 加 `pytest tests/` 步骤 + 轻量 smoke（不跑完整回归）

### 人工

每 phase 完成前按 checklist 过验收项，对齐 `verification-before-completion` 原则：先有证据再说"完成"。

## 9. 风险与退路

| 风险 | 退路 |
| --- | --- |
| `service.py` 拆分遇到隐蔽耦合 | 新旧接口并行一段，backstage 不动；每次迁一个 domain 就跑回归 |
| 高德 API 加载失败 | Phase 2 加离线 fallback 到 staged GeoJSON 覆盖物 |
| JSON 文件并发 corruption | `fcntl.flock` + 每次写前 `.trash/` 备份（最近 20 份）；真出问题改 SQLite 无难度 |
| D1 深色强光下刺眼 | Phase 6 加主题 token 切换（深/浅），仅 CSS 变量层切换 |
| 街道级数据密度不够（Phase 6） | 退回 Phase 3 的区级聚合，街道留作数据补齐后的升级 |

## 10. Out of Scope（本次不做）

- 账号、权限、审计
- 多设备同步（localStorage 镜像到服务端除外，Phase 6 可选）
- 移动端适配（桌面优先；手机端容忍"能看不能用顺"）
- 上构建链（Vite / TS）
- 推送通知（任何形式的 WebPush / IFTTT 集成）
- 重写 `persistence.py` / `provider_adapters.py` / `reference_catalog.py`
- 改动 staged / database / mock 三态切换逻辑

## 11. 交付物清单

- [ ] `frontend/backstage/` 迁移完成，`/backstage` 可访问
- [ ] `frontend/user/` 新建，`/` 显示用户平台
- [ ] `api/domains/` 8 个领域模块建立；`api/backstage/` 保留模块建立
- [ ] `api/service.py` 规模降到 < 2000 行（仅剩跨领域聚合函数或已完全迁走）
- [ ] `/api/v2/*` 全端点可用
- [ ] `data/personal/` JSON 文件机制 + 文件锁 + 备份
- [ ] 变化横幅端到端可用
- [ ] 三模式切换、筛选记忆、URL 同步正常
- [ ] 楼栋透视抽屉含笔记
- [ ] `scripts/full_browser_regression.py` 覆盖两路由
- [ ] `pytest tests/` 通过；CI 接入
- [ ] `README.md` 更新，指明 `/` 和 `/backstage` 的职责
