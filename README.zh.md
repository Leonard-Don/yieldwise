# Yieldwise · 租知

[![Validate](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml/badge.svg)](https://github.com/Leonard-Don/yieldwise/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**开源租赁资产分析工作台 —— 把你的房源、候选标的、市场比准数据放在同一张地图上。**

[English README](README.md) · [Demo 跑起来](#快速开始) · [背后的实现笔记](docs/internal/legacy-runbook.md)

<p align="center">
  <img src="docs/screenshots/atlas-workbench-overview.png" alt="Yieldwise 工作台" width="100%" />
</p>

## 这是什么

Yieldwise 是一个**个人级**的房地产分析工具。你导入自己的 CSV（在管房源 / 候选标的 / 第三方比准），Yieldwise 会：

- 把它们和开放数据小区 + OSM 楼栋画在一张地图上
- 按行政区 / 小区 / 楼栋粒度算租售比 / 回本年限 / 出租率 KPI
- 让你几秒内对比你的标的与本地市场

**本地跑，数据不出你的电脑。**

## 谁会用得上

- **个人投资者**：在出价之前想看一眼某个区的租售比分布
- **金融科技 / 城市经济学 / 房地产金融的学生 / 研究者**：写论文 / 做课题需要快速分析底稿，但不想付戴德梁行 / 仲量联行 / CoStar 的钱
- **独立房产顾问**：手上有几个小单子，不想自己搭 GIS
- **爱折腾的人**：想看看一个"中国租赁市场版的彭博终端"长啥样，零软件成本

## 为什么做这个

一个金融科技专业大四学生的毕业项目。中国公开房产数据散在政府开放数据门户、OSM、高德 POI、给机构看的 PDF 报告里。Yieldwise 把开源那部分拼起来，剩下的部分给你留了 CSV 导入通道。

**不爬数据，不碰合规灰区** —— 你带你授权的数据来，工具帮你分析。

## 快速开始

需要 Docker + Docker Compose。一条命令同时起 Postgres+PostGIS 和 app：

```bash
git clone https://github.com/Leonard-Don/yieldwise.git
cd yieldwise
cp .env.example .env             # 编辑 .env 填入 AMAP_API_KEY（免费，见下方）
docker compose up -d --build     # 首次 build ~2 分钟，后续 ~10 秒起
```

打开 `http://localhost:8000`，用 `.env` 里的账号登录（默认 `admin` / `changeme-after-first-login` —— 暴露端口到网络前请改）。

到 `/admin/customer-data` 试上传：
1. 点 **下载模板** → 存 `portfolio.csv`
2. 填 5–10 行你的样本数据
3. 上传
4. 地图自动出你的点

需要免费高德 key 才能渲染地图？去 [lbs.amap.com](https://lbs.amap.com/api/javascript-api-v2/prerequisites) 申请。商业部署请申请商用 key（个人 key 商用违 ToS）。

不想用 Docker？

<details>
<summary>原生 Python 启动</summary>

```bash
docker compose up -d postgis      # 只起 postgis
python3 -m venv .venv && source .venv/bin/activate
pip install -r api/requirements.txt
export $(grep -v '^#' .env | xargs)
export POSTGRES_DSN=postgresql://atlas:atlas_local_dev@127.0.0.1:5432/yieldwise
uvicorn api.main:app --reload --port 8000
```
</details>

CSV 模板：`/api/v2/customer-data/templates/{portfolio,pipeline,comp_set}.csv` —— 列规范见 [docs/customer-data-csv-spec.md](docs/customer-data-csv-spec.md)。

## 功能

- **一张地图三种工作流**：收益猎手 · 自住找房 · 全市观察
- **三类 CSV 导入**：
  - `portfolio` —— 在管房源
  - `pipeline` —— 候选标的（lead/qualified/negotiating/won/lost 阶段追踪）
  - `comp_set` —— 第三方比准
- **多用户 auth** 含 admin/analyst/viewer 角色（单租户私部署）
- **多城市参数化** —— 一个 YAML 配置增加一个城市
- **OSM + 高德楼栋融合** 含 per-community 配额匹配
- **行级错误捕获** —— 烂行进 `errors.json` 审计，整批不会因为一行炸掉
- **暂存优先**存储 —— 每次导入先落 `tmp/customer-data-runs/<run_id>/`，确认后再写入 Postgres

## 数据来源（公开透明）

| 层 | 来源 | 许可 |
|---|---|---|
| 楼栋形状 | OpenStreetMap | ODbL |
| 小区边界 | 高德 POI（生产用需要商用 key）| 按高德 ToS |
| 行政区边界 | 上海政府开放数据 | 开放政府数据 |
| 挂牌（demo）| 合成 / 手工策展数据 | 自生成 |
| 客户数据 | **用户自带（CSV）** | 用户所有 |

Yieldwise 不带任何爬虫、不主动获取任何需要授权的数据。要爬，你在你自己的环境自己决定。

## 项目状态

**v0.3**（2026 年 4 月）—— Beta。已稳定的能力：
- Auth + 客户数据导入 + 暂存优先持久化
- 多城市配置（上海开箱即用，北京/深圳模板就绪）
- 后端 253 测试通过，前端 ~110 个 node:test
- 一个学生每周 ~10 小时维护 —— 难免有粗糙之处

**还没做的** —— 见 [GitHub Issues](https://github.com/Leonard-Don/yieldwise/issues)：
- PDF / Excel 报表导出
- 公网 hosted demo
- 仅地址的 geocoding（当前 CSV 必须显式 lng/lat）

## 收费方式

工具本身按 MIT 免费。如果你想要"方法论 + demo 数据集 + Excel 模板"的完整知识包，关注 [Discussions](https://github.com/Leonard-Don/yieldwise/discussions) —— 计划首次公开后 6 周内发布。

## 贡献

欢迎 issue / 想法 / PR。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

MIT —— 见 [LICENSE](LICENSE)。MIT 仅覆盖 Yieldwise 自己的源码；数据来源各有各的许可（OSM ODbL、高德 ToS 等）。

## 联系

- GitHub: [@Leonard-Don](https://github.com/Leonard-Don)
- Email: leonarddon@oxxz.site

如果对你有用或者有想法，给个 star 我会很开心。
