# Yieldwise Commercialization Design

- **Status**: Draft (pending user review)
- **Date**: 2026-04-29
- **Scope**: 把现有 Shanghai Yield Atlas（单用户内研工具）改造为可对外售卖的 B2B 产品 **Yieldwise**，目标客户为头部保租房 REITs / 长租公寓运营商的投资部 / 资管部。商业模式为单租户私部署 + 项目制实施费 + 年度订阅维护。
- **前置 spec**：`2026-04-23-user-facing-platform-design.md`（用户前台改造）已完成。本 spec 在其基础上做"商业化包装 + 数据合规剥离 + 私部署化"。

## 1. 背景与目标

### 现状（2026-04-29 verified）

- 项目代号 Shanghai Yield Atlas，mid-Beta；用户前台 `/` + 研究台 `/backstage` 双入口；FastAPI + 原生 JS（无打包器）；PostGIS 可选；三种运行态 `staged / database / mock`
- 数据流主链路依赖 `tmp/browser-capture-runs/` 公开页采样（贝壳等）—— `docs/strategy.md` §3 自身已写明"不稳定抓取不作为长期生产主链路"
- 上海一城写死（行政区字典、坐标参考、地图中心），多用户/多租户能力为零
- `api/service.py` 5947 行（已大幅瘦身但仍是 re-export hub），`frontend/backstage/app.js` 10077 行
- 测试基线：pytest 123 项 + browser regression 25/25 + phase1_smoke 21 路由

### 商业化目标

- **首年（v1，本 spec 范围）**：ship 商业版 v1，签下 1 个灯塔客户（成交价 ≥ ¥196k），再签 1–2 个正价客户
- **首年财务目标**：现金流 ¥1.2M–¥3.2M（含一次性 license + 年度维护）
- **市场定位**：租赁资产投研工作台，绕开数据合规风险（客户自带授权数据），定位投资 / 资管科室而非整个公司

### 非目标（首年不做）

- 多租户 SaaS / 公网托管 / 自营云
- 多语言（中文优先）
- 移动端响应式 / App
- 自动数据爬取 / 订阅服务
- 跨境部署（数据出境合规过重）
- 政府 / 银行 / 评估机构市场（这些赛道单独评估，不在 v1 ICP）

## 2. 产品定位与 ICP

### 2.1 改名

`Shanghai Yield Atlas` → **`Yieldwise`**（中文 **租知**）

副标题：**租赁资产投研工作台 · 拿房选址 / 估值 / 投后一张地图**

理由：
- "Shanghai" 锁死地域，第一印象就是"它只能干上海"
- "Yield Atlas" 太学术，不像投决工具
- "Yieldwise" 直指租售比 / 派息率，REITs 圈一听就懂；"wise" 暗示决策辅助
- 中文"租知"短、好记、域名易申请

### 2.2 ICP（理想客户画像）

主线 ICP：

> **头部保租房 / 长租公寓运营商的投资部 / 拿房部 / 资产管理部**
> 公司规模：管理房源 ≥ 5 万间 OR 已发行 / 准备发行 REIT
> 决策人：投资总监 / 资管总监（预算 ¥200k–¥1M 可拍板）

**不卖给**：
- 散户投资者 / 中介门店 / 自住购房者
- 政府规划院（B2G 销售吃力）
- 银行风控（中房信占住）
- 私募地产基金（已转向 AI 量化 + 股票）

### 2.3 核心价值主张

> **"把你团队散在 Excel、戴德梁行 PDF、内部 PMS 里的拿房线索、在管房源、市场比准数据，收进同一张地图，3 周做出原本 3 个月的投决报告。"**

3 个 anchor use case（按客户痛点排序）：

1. **拿房选址（最痛）**：候选项目 vs 周边在管 / 在售 / 已签约项目的租金差、地铁距离、商圈竞品、楼栋一致性
2. **REIT 扩募估值（最值钱）**：portfolio 视图的派息率 + 出租率 + 单平租金的快照对比与变化提醒
3. **投后管理（最高频）**：每月 IC paper 自动生成（沿用现有"笔记 + 关注夹 + 变化横幅"骨架）

### 2.4 灯塔客户清单（首批 30 家）

**已发行 REIT（最优先，投研流程最规范）**：
- 华夏北京保障房 REIT（北京住保）
- 中金厦门安居 REIT
- 华润有巢 REIT
- 华夏华润悠米 REIT

**头部运营商无 REIT 但规模够**：
- 万科泊寓、龙湖冠寓、招商伊敦、建信住房、保利公寓
- 上海地产城方、平安不动产长租、中海长租、越秀公寓、深业泊富

**二线区域龙头（决策快、单价低、用作首单试点）**：
- 各地国资背景的长租运营商（约 14 家，按城市排）

## 3. 约束与原则

- **部署**：单租户私部署 only（Docker on customer infra）；不做 SaaS / 公网托管 / 跨境
- **数据**：客户自带授权数据；商业版不预装、不交付任何抓取 / 采集 / 公开页采样代码
- **架构连续**：`api/domains/` 用户前台领域保留并扩展；`api/backstage/*` 公开页相关模块剥离
- **无构建工具**：延续浏览器原生 ES modules + import map（pyproject 依赖最小化原则不变）
- **三态运行模式**：保留 `staged / database`，**砍掉 `mock`**（私部署直连客户库）
- **渐进交付**：6 个 milestone（M1–M6）+ 3 个技术债（T1–T3），每项完结后仓库可独立 build / demo

## 4. 仓库分支策略

| 分支 | 用途 | 含 browser-capture? |
|---|---|---|
| `main` | 商业版 v1（Yieldwise）唯一发布分支 | ❌ 已剥离 |
| `research-private` | 长期分支，自研 / 公开页采集留用 | ✅ 保留 |
| `release/yieldwise-v1.x` | 客户私部署的 frozen 标签 | ❌ |

`research-private` 每半年从 `main` cherry-pick 商业版的非合规改进（性能、地图、报告模板等）；不反向合并。

## 5. 产品改造清单

### 5.1 必须做（v1 商业版）

#### M1 · 多城市参数化 · ~3–4 工程日

- 新增 `api/config/cities/<city>.yaml`（city manifest）：行政区字典、坐标参考点、地铁站 GeoJSON、城市边界、map center
- 当前模块对"上海"的硬编码全部抽到 city manifest：
  - `api/service.py` 内 anchors / districts 相关常量
  - `frontend/user/modules/` 地图初始化
  - `frontend/backstage/lib/` map layer init
- 启动时按 `ATLAS_CITY=shanghai` 环境变量加载对应 manifest
- v1 实交付的客户私部署内只放 1 份对应城市 manifest，但代码层支持 dropdown 切换

#### M2 · Auth + 多用户（单租户）· ~4–5 工程日

- 新增 `api/auth/`：
  - bcrypt 密码哈希（python-bcrypt）
  - HTTP-only session cookie（Starlette `SessionMiddleware`）
  - 不引入 JWT / OAuth2（私部署不需要）
- 三档角色：
  - `admin`：管理用户 + 全部数据读写
  - `analyst`：全部数据读写，不能管用户
  - `viewer`：只读 + 自己的笔记
- 新增 `/admin/users` 简单管理页（admin 加 / 禁用 / 改密）
- 所有 `/api/*` + `/api/v2/*` 套 session middleware；`/login` 例外
- 用户表：`auth_users(id, username, password_hash, role, disabled, created_at)` ；首次启动 seed 一个 admin（密码从环境变量读）
- **明确不做**：多租户隔离、SSO、SAML、LDAP、SCIM —— 等客户主动要再加

#### M3 · 数据导入 API + CSV 模板 · ~5–7 工程日

三类客户数据：

| 类型 | 字段 | 流向 |
|---|---|---|
| **portfolio**（在管房源） | 项目名 / 地址 / 楼栋 / 户型 / 租金 / 出租率 / 入住日 | `customer_data.portfolio` 表 |
| **pipeline**（候选标的） | 项目名 / 位置 / 谈判阶段 / 预估价 / 备注 | `customer_data.pipeline` 表 |
| **comp_set**（比准数据） | 来源 / 报告日期 / 地址 / 成交价 / 单平租金 | `customer_data.comp_set` 表 |

- CSV 模板从落地页下载
- 上传 → 地址解析（复用现有 address resolver）→ 入 `customer_data.*` 表
- 复用现有 `tmp/import-runs/` staged-first 流水线，加 `customer-data` namespace
- 失败行进 `customer_data.import_errors` + UI 显示
- 后续：v2 加 REST API 让客户内部 BI 系统直接 push

#### M4 · 投决报告导出（PDF + Excel）· ~4–5 工程日

两个标准模板：

- **拿房选址一页纸**（PDF）：项目位置图 + 周边比准 + 租金差表 + 决策建议占位
- **REIT portfolio 月报**（PDF）：portfolio map + 派息率趋势 + 出租率热力 + 变化提醒清单

技术：
- PDF：复用现有 `pwcli`（playwright headless）拍页面成 PDF（不引入 weasyprint，省一个依赖）
- Excel：openpyxl 导出 KPI 表（portfolio 主表 + comp_set 副表）
- 模板渲染：Jinja2 + `frontend/reports/` 下静态 HTML 模板
- 新增 `/api/v2/reports/{template_id}/render` endpoint（返回下载 URL）

#### M5 · 私部署 + 离线安装包 · ~3–4 工程日

- 完善现有 `docker-compose.yml` 为 offline-ready：
  - PostGIS 镜像
  - app 镜像（含所有 Python wheels 预下载到 `vendor/wheels/`）
  - 高德 SDK 离线 JS bundle
- 离线 tar.gz 安装包：包含上述镜像 + 一键启动脚本
- 部署 SOP（`docs/deployment/onprem-install.md`）：1 页纸
- 故障排查清单：常见症状 + 命令

#### M6 · 改 backstage 为运营商工作流 · ~7–10 工程日（最大块）

**砍掉**：
- 公开页补样 panel
- attention review queue（公开页部分 — 保留运营复核部分）
- relay contract 相关 UI
- 任何提到"贝壳 / 链家 / 抓取 / 公开页"的 UI 文案

**替换为**：
- **拿房 pipeline 看板**：候选项目卡片化展示，可拖拽改阶段（lead / qualified / negotiating / won / lost）
- **标的库**：在管房源 + 候选房源统一列表 + 地图叠加
- **决策记录**：每个项目的决策时间线（沿用现有"笔记 + 关注夹"骨架）

影响最大的文件：`frontend/backstage/app.js`。改造时按 Phase 8 增量切片原则（不做 ES module 大重写），把动到的逻辑抽到 `frontend/backstage/lib/` 或 `data/`。

### 5.2 砍掉（不进商业版）

| 项 | 原因 |
|---|---|
| `tmp/browser-capture-runs/` 流水线 | 合规雷区 |
| `mock` 运行模式 + `ATLAS_ENABLE_DEMO_MOCK` | 私部署直连客户库，不需要 |
| backstage "公开页采集 / 录入 / 复核" panel | 见 M6 |
| README 里贝壳 / 公开页相关章节 | 商业版品牌一致性 |
| `relay contract` 模块 | 同上 |

实施：M6 阶段在 `main` 分支删除；同步 cherry-pick 必要修复到 `research-private` 分支保留私用。

### 5.3 推迟（v2 / 客户主动要才做）

- 通勤分钟（高德路线 API）
- 街道粒度聚合
- 多租户 SaaS
- 自动数据爬取 / 订阅
- SSO / SAML / LDAP
- 国密 SM2/3/4

### 5.4 技术债（必修）

#### T1 · psycopg connection pool · ~2 工程日

- 现状：每查询新连接（README 已记录）
- 私部署多用户必撑不住
- 上 `psycopg_pool.ConnectionPool`，max 10–20
- 影响：`api/db_helpers.py` 全部连接获取路径
- 测试：所有现有 db 测试通过 + 新增 pool 压测（20 并发 30s）

#### T2 · service.py 切干净 · 与 M6 合并

- 把"公开页采集相关"的 import 从 `service.py` 全部砍掉
- 商业版 build 不应该包含这些代码
- 副产物：service.py 行数预计降到 ~3500 行

#### T3 · 依赖许可证审计 · ~1 工程日

- 跑一遍 `pyproject.toml`：MIT / Apache / BSD ✅；GPL ❌
- 高德 SDK：申请商用 key（个人 key 商业用违 ToS）
- 输出 `docs/legal/dependency-licenses.md` 给客户法务审

### 5.5 工作量汇总

| 项 | 工程日 |
|---|---|
| v1 必做（M1–M6） | 26–35 |
| 技术债（T1–T3） | 4–5 |
| Demo dataset 制作 | ~5 |
| Buffer（联调 + 文档 + 第一次 demo） | 7–10 |
| **合计** | **42–55 工程日** |

兼职（每周 20h）：**14–18 周 ship v1**

## 6. 数据 + 部署 + 合规

### 6.1 部署模型

```
客户 IT 机房 / 客户 VPC
├── PostGIS（客户管的数据库）
├── Yieldwise app（Docker container）
└── 客户运营 / Pipeline / Comp set 数据
        ↑
   你的代码，永远不接触客户实际数据
```

### 6.2 数据流

合同明确客户自带：
1. 运营数据（自有 PMS / 内部 Excel）
2. 比准数据（戴德梁行 / 仲量联行 / CBRE / 高力 已订阅报告）
3. 公开数据（政府开放数据 / 高德 POI 商用 / 国家统计局）

商业版**不预装、不交付任何抓取 / 采集脚本**。

### 6.3 Demo Dataset

- 来源：上海开放数据 + 国家统计局 + 高德商用 POI + 合成虚拟租金（标注"虚拟数据，不构成投资建议"）
- 范围：1 城市，~500 小区，~50 楼栋
- 形态：开源 GitHub repo，客户 `docker compose up` 5 分钟跑起来
- 作用：销售 funnel 转化关键资产；ship v1 之前必须完成

### 6.4 合同必含 4 条

1. **数据所有权与责任**：客户对其导入数据的合法性负全责，工具不主动获取数据
2. **工具不含抓取模块**：商业版构建产物经审计，不含任何 web scraping / browser automation / public crawling 代码
3. **数据驻留**：所有客户数据驻留客户基础设施，乙方不存储 / 不传输 / 不查询
4. **责任上限**：合同总额的 1 倍

### 6.5 不必触碰

- 等保（客户机房客户负责）
- 数据出境（工具不出境）
- 个保法（B2B 不涉 C 端 PII）
- 国密（推迟到客户主动要）

### 6.6 高德 SDK 商用 key

- 必须申请（个人 key 商业用违 ToS）
- **客户出钱**：调用量按客户业务规模算，他们自己控成本更合理；你只做集成
- 落地：合同附录列明客户需自备的第三方 API key 清单

## 7. 定价与商业模式

### 7.1 定价档位（v1）

| 档 | 首年价格 | 维护年费 | 含义 |
|---|---|---|---|
| **Starter** | ¥280k | ¥120k | 1 城 + 5 用户 + CSV 导入 + 标准 PDF 报告 |
| **Growth** | ¥480k | ¥200k | 3 城 + 15 用户 + 数据 API + 定制 1 套报告模板 |
| **Enterprise** | ¥800k+ | ¥320k+ | 多城无限 + 无限用户 + 内部 BI 对接 + 月度驻场 |

加项：扩城 ¥50k/城；定制报告模板 ¥30k/套；内网 BI 对接 ¥80k+

### 7.2 首单战略

- **首单给 Starter 7 折（¥196k）+ 联合发布客户头衔 + 6 个月联合月报权 + Steering Committee 席位**
- 换的是案例、Logo、推荐信、口碑
- 第 2 单恢复正价

### 7.3 LTV 假设

- 单客户 3 年 LTV：¥1.0M–¥3.2M（首年 + 2 年维护 + 加项）
- 首年目标 2–3 个客户 → ¥1.2M–¥3.2M 现金流

## 8. GTM 90 天计划

### W1–4（v1 改造期，与开发并行）

**物料（5 个）**：
1. 5 页商业 deck（PDF）
2. 3 分钟 demo 视频（讲拿房选址 anchor use case）
3. 落地页（静态站，托管 Cloudflare Pages 免费）
4. Demo dataset GitHub repo
5. 5–8 页白皮书 PDF + 同步公众号文章

**目标客户名单**：30 家（见 §2.4）

### W5–8（铺线索 + 跑 demo）

**3 路获客**：
1. 公众号 / 知乎专栏：5 篇深度文（租售比可视化 / REIT 拿房选址 / 长租资产估值 / 比准数据治理 / Excel 替代方案）
2. LinkedIn / 脉脉冷邮：30 个目标客户的投资 / 资管总监，1 天 2 封手写
3. 行业会议：ICCRA 中国不动产证券化论坛、长租公寓行业年会—参会、加微信、不卖、混脸熟

**目标**：W5–W8 累计跑 8–10 个 30 分钟 demo 会议，转化 3 个进 POC

### W9–12（POC + 首单成交）

- POC 形态：客户用自己 1 个项目脱敏数据跑 2 周，输出 1 份样板拿房选址报告
- POC 免费但合同前置：先签 LOI 锁定 30 天独家议价期 + POC 通过后 14 天内决定是否采购
- 首单目标：3 POC → 1 落地（成交率 33% 是 solo B2B 合理基线）

### KPI（90 天）

| 指标 | 目标 |
|---|---|
| 物料齐 | W4 末 |
| Demo 会议 | 8–10 |
| POC | 3 |
| 首单 | 1（≥¥196k 现金） |
| Pipeline value | ≥¥1.5M |

## 9. Roadmap（12 个月）

| Phase | 周期 | 交付 |
|---|---|---|
| **P0 · 改造** | W1–W18（兼职） | v1 商业版 ship + Demo dataset + 落地页 |
| **P1 · 首单** | W12–W26 | LOI → POC → 1 灯塔客户成交 |
| **P2 · 第二三单** | W26–W40 | 价格正常化 + 反馈循环 + 定制功能积累 |
| **P3 · 决策点** | W40–W52 | 决定 v2 方向：SaaS / 多租户 / 邻近赛道（银行 / 规划院） |

## 10. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 头部客户已有内部工具 | 中 | 高 | demo 强调"投决工作流 + 一张地图"差异，不正面拼 BI |
| solo 兼职节奏延期 | 高 | 中 | 14–18 周给了 buffer；M6 是最大变量，必要时砍 UI 美化保功能 |
| POC 全没落地 | 中 | 中 | W12 前要从客户拿 NPS 拒绝原因，调价格 / 功能 / ICP |
| 数据合规审计被客户法务卡 | 低 | 高 | §6.4 合同 4 条 + 商业版构建产物审计 |
| 高德商用 key 申请被拒 | 低 | 中 | 备选：百度 / 腾讯地图 SDK；保留地图层抽象 |

## 11. 测试与验证

### v1 ship 前必过

- 现有 pytest 123 项 + 新增 auth / 多城市 / 数据导入 / 报告导出测试 ≈ 总 180 项
- Browser regression 25/25 → 适配新 backstage 工作流后维持 100%
- Connection pool 压测：20 并发 × 30s 无错误
- Docker 离线安装：在干净 Linux VM 上 5 分钟内启动成功
- Demo dataset 完整跑通：上传 → 解析 → 入库 → 地图渲染 → 报告导出

### 灯塔客户验收

- POC 期内客户用其真实数据完整走通拿房选址流程一次
- 输出 1 份样板报告获客户投决会认可
- 客户 IT 在客户机房完成 docker 离线部署

## 12. 后续 spec / plan

- 本 spec 通过审阅后由 `superpowers:writing-plans` 转为实施计划
- 实施计划按 M1 → T1 → M2 → M3 → M4 → M5 → M6+T2 → T3 顺序排（M1/M2 可并行；M6 + T2 合并）
- Demo dataset 制作单独出 mini-spec（涉及法律 + 数据合成）
- GTM 物料（deck / video / 白皮书）单独出 mini-spec（不属代码工作）

## 13. 决策日志

| 日期 | 决策 | 理由 |
|---|---|---|
| 2026-04-29 | 选 B2B 项目制 + 单租户私部署而非 SaaS | 数据合规风险 + solo 运维成本 + 客户 IT 安全策略 |
| 2026-04-29 | ICP = 保租房 REITs / 长租头部运营商投资部 | 租售比是其 KPI 而非装饰；投决工作流匹配现有代码 |
| 2026-04-29 | 改名 Yieldwise / 租知 | 去 Shanghai 锁定；副标题"租赁资产投研工作台" |
| 2026-04-29 | 砍 browser-capture 整条流，移至 research-private 分支 | 合规雷区；商业版 build 必须干净 |
| 2026-04-29 | 砍 mock 运行模式 | 私部署直连客户库 |
| 2026-04-29 | 高德商用 key 由客户出 | 调用量按客户业务规模算 |
| 2026-04-29 | 首单 7 折换灯塔客户案例 | 第一案例的口碑价值 > 首单溢价 |
