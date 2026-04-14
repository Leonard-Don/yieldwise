# Geo Assets Import Flow

这份说明固定了“授权导出的楼栋 footprint / AOI `GeoJSON`”接入当前 MVP 的最短路径。

## 适用场景

- 高德 AOI / POI 批量导出后的再整理结果
- 第三方授权提供的楼栋 footprint `GeoJSON`
- 内部人工勾绘或 GIS 同事导出的楼栋多边形

## 输入格式

当前脚手架要求输入是 `FeatureCollection`，每个 feature 至少要能让系统定位到一个楼栋：

- 优先：`properties.building_id`
- 其次：`properties.community_id + properties.building_name`
- 再其次：`properties.community_name + properties.building_name`

推荐属性：

- `source_ref`
- `community_id`
- `community_name`
- `building_id`
- `building_name`

几何类型当前支持：

- `Polygon`
- `MultiPolygon`

## 运行方式

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints" \
  --geojson-file data/demo/building_footprints_demo.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints
```

## 输出产物

- `building_footprints.geojson`
- `unresolved_features.json`
- `coverage_tasks.json`
- `review_history.json`
- `work_orders.json`
- `work_order_events.json`
- `summary.json`
- `manifest.json`

其中：

- `building_footprints.geojson` 只保留已成功归一到楼栋实体的 feature
- `unresolved_features.json` 记录未命中楼栋词典的几何对象，适合人工复核
- `coverage_tasks.json` 把目录缺口楼栋和未命中 feature 统一成可派工任务
- `review_history.json` 记录几何任务的状态流转
- `work_orders.json` 记录已经生成的补采工单和负责人 / 截止时间
- `work_order_events.json` 记录补采工单从派单到关闭的流转历史
- `summary.json` 汇总本批次覆盖率
- `manifest.json` 记录输入输出、批次号和注意事项

## 当前消费方式

导入完成后：

1. `/api/geo-assets/buildings` 会优先读取选中或最新几何批次里的楼栋 footprint
2. `/api/geo-assets/floor-watchlist` 会基于楼栋 footprint 派生楼层 footprint
3. `/api/geo-assets/runs/{run_id}` 会返回该批次的目录覆盖率、覆盖缺口、未命中 feature 和几何任务
4. `/api/geo-assets/runs/{run_id}` 里现在还会直接带 `workOrders`、`workOrderSummary` 和 `recentWorkOrderEvents`
5. `/api/geo-assets/runs/{run_id}/work-orders` / `POST .../work-orders/{work_order_id}` 可以直接把高影响缺口推进成补采工单
6. 如果带上 `baseline_run_id`，`/api/geo-assets/runs/{run_id}` 和 `/api/geo-assets/runs/{run_id}/compare` 还会返回相对上一版几何的变化摘要
7. 前端楼栋 / 楼层地图会优先使用这批几何资产，缺失楼栋才回退到本地推导

几何任务详情现在还会动态补一层“影响分”：

- 是否已经命中持续套利楼层榜
- 楼栋机会分和小区机会分
- 当前是“未命中归一”还是“楼栋缺口”
- 当前任务状态是否已派工 / 已关闭

这样工作台能直接把“最影响套利判断的缺口楼栋”排到前面。

如果前端或导出需要固定某一版几何批次，可以在请求里显式带上：

- `geo_run_id=<run_id>`

如果要把这批 footprint 和几何任务写进 PostgreSQL，可以运行：

```bash
python3 jobs/load_geo_asset_run_to_postgres.py \
  --manifest tmp/geo-assets/demo-building-footprints/manifest.json
```

如果你想直接演示“上一版几何 vs 当前版几何”，可以再跑一版历史样本：

```bash
python3 jobs/import_geo_assets.py \
  --provider-id amap-aoi-poi \
  --batch-name "demo-building-footprints-baseline" \
  --geojson-file data/demo/building_footprints_demo_previous.geojson \
  --output-dir tmp/geo-assets/demo-building-footprints-baseline
```

然后在工作台里的“对比基线”下拉切到这版历史样本，就能直接看新增覆盖楼栋、几何修正和打开任务变化。

## 现在还没做的部分

- 真实 `GCJ-02 / WGS-84` 坐标转换链
- `geo_assets` 表正式落库
- AOI 与楼栋 footprint 的自动质量评分
- 与地址标准化 / 导入批次联动的几何质量工单流
