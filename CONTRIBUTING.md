# Contributing

这个仓库当前按“内部研究台”来维护，默认走 `staged` 数据模式，不要求先接正式授权源。

## 推荐工作流

1. 先补主档或公开页样本，再刷新 staged 批次。
2. 优先复用现有 reference catalog、building dictionary 和 footprint。
3. 只提交源码、文档、静态资源和 seed 数据，不提交 `tmp/`、`.env.local`、浏览器缓存。

## 提交前最少检查

```bash
python3 -m compileall api jobs scripts
node --check app.js
```

## 公开页采样边界

- 只处理公开可见页面。
- 不依赖登录态。
- 不做高频自动化抓取。
- 统一落成 `public-browser-sampling` 的 staging 批次。

## 常用命令

刷新整套 staged 研究面：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14
```

只增量刷新 listing / metrics：

```bash
ATLAS_REFERENCE_CATALOG_FILE=tmp/reference-runs/shanghai-citywide-reference-2026-04-14/reference_catalog.json \
python3 jobs/import_authorized_listings.py \
  --provider-id public-browser-sampling \
  --batch-name "public-browser-sampling-2026-04-14" \
  --sale-file data/public-snapshot/2026-04-12/public_browser_sampling_sale.csv \
  --rent-file data/public-snapshot/2026-04-12/public_browser_sampling_rent.csv \
  --output-dir tmp/import-runs/public-browser-sampling-2026-04-14

python3 jobs/refresh_metrics.py \
  --date 2026-04-14 \
  --batch-name "staged-metrics-2026-04-14"
```

## Issue 类型

- `Public Sampling Task`: 继续补公开页人工采样
- `Bug Report`: 页面、导入链或地图联动问题

当前采样重点见 `docs/internal/public-sampling-backlog.md`。
