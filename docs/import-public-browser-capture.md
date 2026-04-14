# 公开页面人工采样导入

这条链专门服务“暂时拿不到正式授权，但仍然要持续补洞”的阶段。

约束：

- 只处理**公开页面**人工采样
- 不依赖登录态
- 不做高频自动化抓取
- 最终仍然统一落成 `public-browser-sampling` 的标准 staging 批次

## 1. 准备 capture CSV

模板见：

`data/templates/public_browser_capture_template.csv`

最小必填字段：

- `source_listing_id`
- `business_type`
- `url`
- `community_name`
- `address_text`
- `raw_text`
- `published_at`

建议做法：

1. 浏览器打开公开房源页或小区详情页。
2. 人工复制核心文本到 `raw_text`。
3. 如果页面上的结构化字段很清楚，可以把 `building_text / floor_text / area_sqm / price_total_wan / monthly_rent` 这些覆盖字段也直接填上。

## 2. 把 capture CSV 转成标准 sale / rent staging 样本

```bash
python3 jobs/import_public_browser_capture.py \
  --batch-name "public-browser-capture-2026-04-14" \
  --capture-file data/templates/public_browser_capture_template.csv \
  --output-dir tmp/browser-capture-runs/public-browser-capture-2026-04-14
```

这条命令会产出：

- `captured_sale.csv`
- `captured_rent.csv`
- `parsed_captures.json`
- `manifest.json`

默认还会自动继续调用：

`jobs/import_authorized_listings.py --provider-id public-browser-sampling`

所以最后也会生成标准 import run。

## 3. 只想先看解析结果，不想立刻导入

```bash
python3 jobs/import_public_browser_capture.py \
  --batch-name "public-browser-capture-2026-04-14" \
  --capture-file path/to/capture.csv \
  --output-dir tmp/browser-capture-runs/public-browser-capture-2026-04-14 \
  --skip-import
```

## 4. 接进整套 staged 日更

如果你已经有一份新的 capture CSV，也可以直接交给：

`jobs/materialize_public_snapshot.py`

示例：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14 \
  --browser-capture-file path/to/capture.csv
```

这样它会先把 capture CSV 转成标准 sale/rent CSV，再继续跑：

1. reference dictionary
2. community anchor enrichment
3. public-browser-sampling listing import
4. manual geometry staging import
5. staged metrics refresh

## 5. 解析规则

当前脚本会从 `raw_text` 中尽量抽取：

- `building_text`
- `unit_text`
- `floor_text`
- `total_floors`
- `area_sqm`
- `bedrooms / living_rooms / bathrooms`
- `orientation`
- `decoration`
- `price_total_wan`
- `unit_price_yuan`
- `monthly_rent`

提取不到时不会伪造，只会在 `manifest.json -> attention` 里提示缺口。

## 6. 推荐使用方式

1. 先用浏览器人工采样少量高价值楼栋。
2. 跑 `import_public_browser_capture.py`。
3. 看 `manifest.json` 里的缺口。
4. 再把缺字段补回 capture CSV。
5. 确认无误后，并进 staged 日更。

如果你想顺手验证 Atlas 工作台里的“公开页面采样执行台”写路径也没坏，可以直接运行：

```bash
python3 scripts/browser_capture_smoke.py --url http://127.0.0.1:8013/
```

它会自动填当前任务、提交、等待刷新，并检查新的 import / metrics run 是否真的生成。
默认会使用隔离的 `atlas-smoke` 浏览器会话并跳到指定 Atlas 地址；如果你希望复用当前已经打开的 Atlas 页面，可以显式传 `--session default`。
