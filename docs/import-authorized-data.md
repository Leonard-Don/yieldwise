# Authorized Import Flow

这份说明把“自有或已授权 CSV”接进当前本地工作台的最短路径固定下来。

这轮开始，这条链默认不再偷吃 demo 词典。脚本会优先从 PostgreSQL 主档读取 reference catalog；如果数据库还没准备好，可以先跑一批 reference dictionary，或显式设置 `ATLAS_REFERENCE_CATALOG_FILE` 指向一份离线主档。只有在 `ATLAS_ENABLE_DEMO_MOCK=true` 时，才允许退回 demo catalog。

## 适用场景

- 自己整理、购买后合法持有、或从公开开放渠道下载后整理出的 `CSV`
- 研究员人工整理的小批量出售 / 出租样本
- 暂时不走在线 API，但希望先跑通地址标准化、楼层归一和逐层证据配对

## 输入文件

当前任务脚手架支持分别导入出售和出租两份 `CSV`：

- `authorized_sale_template.csv`
- `authorized_rent_template.csv`

模板放在 [data/templates/authorized_sale_template.csv](/Users/leonardodon/project house/data/templates/authorized_sale_template.csv) 和 [data/templates/authorized_rent_template.csv](/Users/leonardodon/project house/data/templates/authorized_rent_template.csv)。

## 出售 CSV 字段

必填列：

- `source`
- `source_listing_id`
- `url`
- `community_name`
- `address_text`
- `building_text`
- `unit_text`
- `floor_text`
- `total_floors`
- `area_sqm`
- `bedrooms`
- `living_rooms`
- `bathrooms`
- `orientation`
- `decoration`
- `price_total_wan`
- `unit_price_yuan`
- `published_at`

## 出租 CSV 字段

必填列：

- `source`
- `source_listing_id`
- `url`
- `community_name`
- `address_text`
- `building_text`
- `unit_text`
- `floor_text`
- `total_floors`
- `area_sqm`
- `bedrooms`
- `living_rooms`
- `bathrooms`
- `orientation`
- `decoration`
- `monthly_rent`
- `published_at`

## 运行方式

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id authorized-import \
  --batch-name "pudong-demo-2026-04-11" \
  --sale-file data/templates/authorized_sale_template.csv \
  --rent-file data/templates/authorized_rent_template.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-11
```

在正式接入前，建议先确保 reference catalog 已经就位：

1. PostgreSQL 里已经有 `districts / communities / buildings / *_aliases`
2. 或者先跑一批 `docs/import-reference-dictionary.md` 里的主档导入
3. 或者显式设置 `ATLAS_REFERENCE_CATALOG_FILE`

如果你想直接演示跨批次变化，可以再导入一组“第二天”样本：

```bash
python3 jobs/import_authorized_listings.py \
  --provider-id authorized-import \
  --batch-name "pudong-demo-2026-04-12" \
  --sale-file data/demo/authorized_sale_demo_2026-04-12.csv \
  --rent-file data/demo/authorized_rent_demo_2026-04-12.csv \
  --output-dir tmp/import-runs/pudong-demo-2026-04-12
```

## 输出产物

脚本会生成：

- `normalized_sale.json`
- `normalized_rent.json`
- `address_resolution_queue.json`
- `floor_pairs.json`
- `floor_evidence.json`
- `review_history.json`
- `summary.json`
- `manifest.json`

其中：

- `normalized_*` 是标准化后的房源事实层草稿
- `address_resolution_queue.json` 对应后续的人工复核队列
- `floor_pairs.json` 是出售 / 出租样本配对结果
- `floor_evidence.json` 是按楼栋楼层聚合后的逐层证据
- `review_history.json` 是人工复核审计时间线
- `manifest.json` 记录批次号、输入输出和待关注项

如果后续做了人工复核，`address_resolution_queue.json`、`normalized_sale.json`、`normalized_rent.json`、`review_history.json`、`summary.json` 和 `manifest.json` 会被原地回写。

## 批次落库

当 `POSTGRES_DSN` 已配置好后，可以把某个批次整体写入 PostgreSQL：

```bash
python3 jobs/load_import_run_to_postgres.py \
  --manifest tmp/import-runs/pudong-demo-2026-04-11/manifest.json
```

首次初始化数据库时可加：

```bash
python3 jobs/load_import_run_to_postgres.py \
  --manifest tmp/import-runs/pudong-demo-2026-04-11/manifest.json \
  --apply-schema
```

## 当前匹配规则

1. 小区名 / 地址优先命中数据库 reference catalog。
2. 楼栋文本优先命中主楼栋名、楼栋别名和 `source_ref`，命不中时再尝试从地址里兜底。
3. 楼层优先解析 `17/24`，其次解析 `17层`、`高楼层`、`中楼层`、`低楼层`。
4. 出售和出租配对时，会综合比较：
   - 同一小区 / 楼栋
   - 面积差
   - 楼层差
   - 房型差
   - 朝向一致性
   - 地址标准化置信度

## 推荐流程

1. 先用模板跑一遍，确认输出结构和批次 manifest。
2. 再把真实授权导出的字段映射到模板列名。
3. 看 `summary.json` 和 `manifest.json` 里的 `attention`，先处理未命中和低置信配对。
4. 通过工作台或 API 把 `needs_review` 队列逐条复核。
5. 等规则稳定后，再用 `jobs/load_import_run_to_postgres.py` 把输出写入 `db/schema.sql` 里的 `ingestion_runs`、`listings_*`、`floor_evidence_*` 表。

## 现在还没做的部分

- 真实在线 OAuth / API 拉取
- 楼栋 footprint / AOI 自动匹配
- 批次审计与权限控制
