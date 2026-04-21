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
3. 先在 Atlas 工作台顶部看 `全局待复核收件箱`，它会优先按当前区展示待复核条目。
4. 进入目标任务后，在 `review queue 回看面板` 里看当前 batch 的 `pending` 条目。
5. 对每条缺口选择：
   - 回填到 `sale / rent` 草稿后重新提交修正
   - 或者直接 `豁免并留痕`
   - 如果当前 run 有多条同类缺口，也可以先勾选子集，再批量 `标记已修正` 或 `批量豁免并留痕`
6. 确认当前 run 的 `pendingCount` 清零后，工作台会自动接力到同任务 / 同区 / 全局的下一条待复核；都清空后再并进 staged 日更。

如果你想顺手验证 Atlas 工作台里的“公开页面采样执行台”写路径也没坏，可以直接运行：

```bash
python3 scripts/browser_capture_smoke.py --url http://127.0.0.1:8013/
```

它会自动填当前任务、提交、等待刷新，并检查新的 import / metrics run 是否真的生成。
默认会复用 `atlas-smoke` 会话并以 headless 模式运行；如果你希望看到真实浏览器窗口，可以显式传 `--headed`。如果你希望复用当前已经打开的 Atlas 页面，可以显式传 `--session default`；如果你想强制新开一个干净会话，可以再加 `--fresh-session`。

如果你想稳定验证某一条 workflow 分支，也可以直接断言提交后的接力动作：

```bash
python3 scripts/browser_capture_smoke.py \
  --url http://127.0.0.1:8013/ \
  --expected-workflow-action review_current_capture
```

```bash
python3 scripts/browser_capture_smoke.py \
  --url http://127.0.0.1:8013/ \
  --expected-workflow-action advance_next_capture
```

不传 `--task-id` 时，脚本会先读取 live `browser_sampling_pack`，再自动挑一条最适合该 workflow 的任务；
如果你就是想复核某个固定任务，也仍然可以额外传入 `--task-id ...` 覆盖自动选择。

如果你想把 review queue 的接力 contract 单独跑成定向 smoke，也可以直接验证三条核心分支：

```bash
python3 scripts/browser_review_smoke.py \
  --url http://127.0.0.1:8013/ \
  --expected-workflow-action review_current_run
```

```bash
python3 scripts/browser_review_smoke.py \
  --url http://127.0.0.1:8013/ \
  --expected-workflow-action review_current_task
```

```bash
python3 scripts/browser_review_smoke.py \
  --url http://127.0.0.1:8013/ \
  --expected-workflow-action advance_next_review
```

不传 `--run-id / --queue-id / --task-id` 时，脚本会先读取 live `browser-review-inbox`，再自动挑一条最适合该 workflow 的 pending item；
如果你要复核某个固定 queue，也可以显式覆盖这些参数。脚本会直接断言复核接力条是否真的使用了后端返回的 `workflow.item / runId / queueId / taskId / reason`。

其中 `review_current_task` 这条分支默认会优先走一个 server-managed 的临时 fixture：
脚本会先把某条同 task 多 run 的 review queue 临时收成“source run 只剩 1 条 pending、其他 run 仍有 pending”，跑完 smoke 之后再自动恢复原始 `review_queue.json`，这样就不用依赖 live inbox 是否刚好存在天然候选。

如果你想把 Atlas 研究台的地图、榜单、楼栋/楼层切换、采样覆盖看板和导出链路也一起回归一遍，可以再运行：

```bash
python3 scripts/full_browser_regression.py --url http://127.0.0.1:8013/
```

这条完整回归现在还会额外检查：

- 行政区覆盖卡片是否真的切换了筛选范围和执行台任务
- 连续补样快捷台里的“下一个待采样 / 下一个同区任务”是否还能推进到下一条任务
- `下一个待复核` 是否会命中全局收件箱首条 pending item，并自动展开精确的 review queue 条目
- 当前 run 的勾选子集批量复核是否会写回并正确更新接力条里的成功数 / 跳过数
- review queue 的 `豁免并留痕` 动作是否会写回并触发复核接力条
- 复核接力条是否明确使用后端 `workflow.item` 指定的下一条 review 目标，而不是退回前端本地收件箱推导
- `review_current_task` 分支是否会在临时 fixture 场景下稳定命中，并把工作台继续 pin 在当前 task 上
- 公开页采样提交流程里的 `review_current_capture` / `advance_next_capture` 两条 workflow 分支是否都还能走通
- 采样接力条是否明确使用后端 `workflow.task` 指定的目标，而不是退回前端本地兜底推导
- 提交成功后，`当前任务最近采样` / `最近公开页采样批次` 是否都会指向本次新生成的 capture run
