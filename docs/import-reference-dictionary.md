# Reference Dictionary Import Flow

这条链专门承接“行政区 / 小区 / 楼栋主档与别名”的离线批次导入，用来把 `district -> resblock -> building -> unit -> floor` 的前三级锚点先稳定下来。

## 适用场景

- 上海开放数据导出的行政区 / 小区主档
- 自己整理或公开开放渠道下载后整理出的 `standResblock / standBuilding` 映射
- GIS / 研究团队人工维护的小区 / 楼栋别名表

## 输入文件

当前脚手架需要 3 份 `CSV`：

- [data/templates/district_dictionary_template.csv](/Users/leonardodon/project house/data/templates/district_dictionary_template.csv)
- [data/templates/community_dictionary_template.csv](/Users/leonardodon/project house/data/templates/community_dictionary_template.csv)
- [data/templates/building_dictionary_template.csv](/Users/leonardodon/project house/data/templates/building_dictionary_template.csv)

## 字段要求

### 行政区字典

必填列：

- `district_id`
- `district_name`
- `short_name`

### 小区字典

必填列：

- `district_id`
- `community_id`
- `community_name`
- `aliases`
- `source_confidence`

其中 `aliases` 用 `|`、`,`、`；` 都可以分隔。

### 楼栋字典

必填列：

- `community_id`
- `building_id`
- `building_name`
- `total_floors`
- `unit_count`
- `aliases`
- `source_ref`

`source_ref` 适合写官方平台里的 `standBuilding` 或外部楼栋编码。

## 运行方式

```bash
python3 jobs/import_reference_dictionary.py \
  --provider-id shanghai-open-data \
  --batch-name "shanghai-reference-seed" \
  --district-file data/templates/district_dictionary_template.csv \
  --community-file data/templates/community_dictionary_template.csv \
  --building-file data/templates/building_dictionary_template.csv \
  --output-dir tmp/reference-runs/shanghai-reference-seed
```

## 输出产物

脚本会生成：

- `district_dictionary.json`
- `community_dictionary.json`
- `building_dictionary.json`
- `reference_catalog.json`
- `summary.json`
- `manifest.json`

这些产物会被后续的 listing / geometry 导入当成 reference catalog 使用；如果数据库里已经有正式主档，优先级仍然是数据库第一。

如果后续在工作台里做了锚点人工确认，还会继续在同一个 reference run 目录下补充：

- `community_dictionary_enriched.csv`
- `anchor_report.json`
- `anchor_review_history.json`

如果数据库主档还没落好，也可以临时把：

```bash
ATLAS_REFERENCE_CATALOG_FILE=tmp/reference-runs/shanghai-reference-seed/reference_catalog.json
```

指向这次导出的 `reference_catalog.json`，让后续 listing / geometry 批次先吃这份离线主档。

## 落库方式

配置好 `POSTGRES_DSN` 后，可以把这批主档直接写进 PostgreSQL：

```bash
python3 jobs/load_reference_dictionary_to_postgres.py \
  --manifest tmp/reference-runs/shanghai-reference-seed/manifest.json
```

首次初始化时也可以一起执行 schema：

```bash
python3 jobs/load_reference_dictionary_to_postgres.py \
  --manifest tmp/reference-runs/shanghai-reference-seed/manifest.json \
  --apply-schema
```

## 现在这条链解决什么

- 让小区别名、楼栋别名和 `source_ref` 正式进入数据库主档
- 让授权 listing / 几何导入优先吃数据库 reference catalog，而不是只认 demo 名称
- 让“同一楼栋不同写法”的解析结果能真正反哺下一批导入
