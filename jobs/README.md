# Jobs Scaffold

当前 `jobs/` 目录已经承接三类 provider adapter 批次：

- `sale_rent_batch`
- `dictionary_batch`
- `geometry_batch`

并附带三条落库脚手架和一条指标快照任务。

## 1. Reference Dictionary 导入任务

`jobs/import_reference_dictionary.py`

用途：

- 导入行政区 / 小区 / 楼栋主档
- 统一小区别名、楼栋别名和 `source_ref`
- 给后续 listing / geometry 批次提供数据库优先的 reference catalog

运行示例：

```bash
python3 jobs/import_reference_dictionary.py \
  --provider-id shanghai-open-data \
  --batch-name "shanghai-reference-seed" \
  --district-file data/templates/district_dictionary_template.csv \
  --community-file data/templates/community_dictionary_template.csv \
  --building-file data/templates/building_dictionary_template.csv \
  --output-dir tmp/reference-runs/shanghai-reference-seed
```

输出：

- `district_dictionary.json`
- `community_dictionary.json`
- `building_dictionary.json`
- `reference_catalog.json`
- `summary.json`
- `manifest.json`

## 2. 授权导入任务

`jobs/import_authorized_listings.py`

用途：

- 导入授权导出的出售 / 出租 `CSV`
- 统一到 `district -> resblock -> building -> unit -> floor`
- 产出地址标准化队列、楼层配对和逐层证据

运行示例：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id beike-open-platform \
  --batch-name "pudong-demo-2026-04-11" \
  --sale-file data/templates/authorized_sale_template.csv \
  --rent-file data/templates/authorized_rent_template.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-11
```

跨批次对比演示样本：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id beike-open-platform \
  --batch-name "pudong-demo-2026-04-12" \
  --sale-file data/demo/authorized_sale_demo_2026-04-12.csv \
  --rent-file data/demo/authorized_rent_demo_2026-04-12.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-12
```

输出：

- `normalized_sale.json`
- `normalized_rent.json`
- `address_resolution_queue.json`
- `floor_pairs.json`
- `floor_evidence.json`
- `review_history.json`
- `summary.json`
- `manifest.json`

## 3. 几何批次导入任务

`jobs/import_geo_assets.py`

用途：

- 导入一批授权导出的楼栋 footprint `GeoJSON`
- 把 feature 归一到 `district -> community -> building`
- 产出几何批次 manifest、标准化 footprint 和未命中清单

运行示例：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints" \
  --geojson-file data/demo/building_footprints_demo.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints
```

基线对比演示样本：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints-baseline" \
  --geojson-file data/demo/building_footprints_demo_previous.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints-baseline
```

输出：

- `building_footprints.geojson`
- `unresolved_features.json`
- `coverage_tasks.json`
- `review_history.json`
- `work_orders.json`
- `work_order_events.json`
- `summary.json`
- `manifest.json`

补充说明：

- 前端工作台会把每个几何批次展示成单独卡片
- 几何批次详情支持选择一个更早的 `baseline_run_id`，直接查看新增覆盖楼栋和 footprint 修正
- 选中某个批次后，地图、楼层榜导出和 footprint 接口都会带上对应 `geo_run_id`
- `unresolved_features.json` 会在工作台详情里直接展示，方便追踪未命中楼栋词典的 feature
- `coverage_tasks.json` 会把缺口楼栋和未命中 feature 统一变成可派工任务
- `work_orders.json / work_order_events.json` 会承接工作台里生成的补采工单与状态流转

## 4. Reference Dictionary 落库任务

`jobs/load_reference_dictionary_to_postgres.py`

用途：

- 读取某个 reference dictionary 批次的 `manifest.json`
- 把 `districts`、`communities`、`community_aliases`、`buildings`、`building_aliases` 写入 PostgreSQL
- 在需要时顺手执行 `db/schema.sql`

运行示例：

```bash
python3 jobs/load_reference_dictionary_to_postgres.py \
  --manifest tmp/reference-runs/shanghai-reference-seed/manifest.json
```

## 5. 几何批次落库任务

`jobs/load_geo_asset_run_to_postgres.py`

用途：

- 读取某个几何批次的 `manifest.json`
- 把 `geo_assets`、几何任务队列和几何任务历史写入 PostgreSQL
- 在需要时顺手执行 `db/schema.sql`

运行示例：

```bash
python3 jobs/load_geo_asset_run_to_postgres.py \
  --manifest tmp/geo-assets/demo-building-footprints/manifest.json
```

## 6. 批次落库任务

`jobs/load_import_run_to_postgres.py`

用途：

- 读取某个授权导入批次的 `manifest.json`
- 把 `listings_*`、`address_resolution_queue`、`floor_evidence_*` 写入 PostgreSQL
- 在需要时顺手执行 `db/schema.sql`

运行示例：

```bash
python3 jobs/load_import_run_to_postgres.py \
  --manifest tmp/import-runs/pudong-demo-2026-04-11/manifest.json
```

首次初始化数据库时：

```bash
python3 jobs/load_import_run_to_postgres.py \
  --manifest tmp/import-runs/pudong-demo-2026-04-11/manifest.json \
  --apply-schema
```

## 7. 指标快照任务

`jobs/refresh_metrics.py`

用途：

- 给 `metrics_community` 生成快照 payload
- 给 `metrics_building_floor` 生成快照 payload
- 帮你先跑通“数据任务 → 指标快照 → 导出/前端查询”这条链路

运行示例：

```bash
python3 jobs/refresh_metrics.py --date 2026-04-11 --output tmp/metrics-snapshot.json
```

生成 staged metrics run：

```bash
python3 jobs/refresh_metrics.py \
  --date 2026-04-14 \
  --batch-name "staged-metrics-2026-04-14"
```

这会在 `tmp/metrics-runs/<run-id>/` 下生成：

- `snapshot.json`
- `summary.json`
- `manifest.json`

前端 `staged` 模式会自动读取最新一批 metrics run，把榜单和详情统一到同一批指标快照。

写入 PostgreSQL：

```bash
python3 jobs/refresh_metrics.py \
  --date 2026-04-11 \
  --write-postgres
```

## 8. 本地数据库一键引导

## 8. staged public snapshot 一键物化

`jobs/materialize_public_snapshot.py`

用途：

- 把 `reference -> anchor enrichment -> listing import -> geometry import -> metrics refresh` 收口成一条本地 staging 管线
- 适合不接 Docker / PostgreSQL 时，先把研究面按天更新出来
- 默认读取 `data/public-snapshot/...` 目录里的主档、公开采样和手工几何文件

运行示例：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14
```

这条命令会输出：

- 一批最新 reference run
- 一批最新 public-browser-sampling import run
- 一批最新 manual-geometry-staging geo run
- 一批最新 staged metrics run

如果某次只想更新 listing / metrics，可以继续单独跑 `jobs/import_authorized_listings.py` 和 `jobs/refresh_metrics.py`。

如果你这次拿到的是浏览器人工采样的 capture CSV，也可以直接加：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14 \
  --browser-capture-file path/to/capture.csv
```

它会先调用 `jobs/import_public_browser_capture.py`，把 capture CSV 自动拆成标准 `sale/rent CSV`，再继续并进整套 staged 物化。

单独跑人工采样导入：

```bash
python3 jobs/import_public_browser_capture.py \
  --batch-name "public-browser-capture-2026-04-14" \
  --capture-file data/templates/public_browser_capture_template.csv \
  --output-dir tmp/browser-capture-runs/public-browser-capture-2026-04-14
```

## 9. 本地数据库一键引导

`jobs/bootstrap_local_postgres.py`

用途：

- 在你已经准备好 PostgreSQL / PostGIS 后，执行首轮 bootstrap
- 固定顺序执行 `reference -> import -> geo -> metrics`
- 让前端从 staged 切到 database 主读

运行示例：

```bash
python3 jobs/bootstrap_local_postgres.py
```

指定批次：

```bash
python3 jobs/bootstrap_local_postgres.py \
  --reference-run-id shanghai-citywide-reference-2026-04-12-20260412223000 \
  --import-run-id public-browser-sampling-2026-04-12-20260412230000 \
  --geo-run-id demo-building-footprints-20260412110000
```

## 下一步替换建议

1. 优先先跑 reference dictionary，让数据库主档替代 demo 词典。
2. 默认不再依赖 mock；只有显式设置 `ATLAS_ENABLE_DEMO_MOCK=true` 时，脚手架才允许吃 demo catalog。
3. 把 PostgreSQL 写入接成正式调度任务，而不是手工触发。
4. 给几何缺口任务补“坐标系校正 / 质量评分 / GIS 回传”字段。
5. 增加批次基线选择、人工复核闭环和异常值过滤。
