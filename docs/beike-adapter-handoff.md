# Beike Adapter Handoff

`jobs/import_beike_listings.py` 已搭好骨架 + I/O 管线 + 与现有 staging pipeline 完全兼容的输出格式。但**签名算法和 endpoint 协议在 [open.ke.com](https://open.ke.com/) 登录后才能看到**，所以四个 TODO 留给你按官方文档填。

`.env.local` 里 `BEIKE_APP_ID` 和 `BEIKE_APP_AK` 已配置；当前 [api/provider_adapters.py:300](../api/provider_adapters.py) 也确认凭证已就绪，只差在线 adapter。

## 四步把 adapter 接通

### Step 1 — 拿到正式技术文档

1. 打开 [open.ke.com](https://open.ke.com/) → 登录
2. 进 "控制台 → 应用管理"，确认你的 App 已经处于"试用通过"或正式状态
3. 在 "服务与支持 → 技术文档" 里找：
   - **TOKEN 获取接口** — 决定 [jobs/import_beike_listings.py:62 `acquire_token`](../jobs/import_beike_listings.py)
   - **房源搜索 / 楼盘字典 / 出租房源** 任意一个 listing 类 endpoint — 决定 [`fetch_listings_page`](../jobs/import_beike_listings.py) 和 [`extract_rows`](../jobs/import_beike_listings.py)
   - **响应字段说明** — 决定 [`normalize_listing`](../jobs/import_beike_listings.py) 的字段映射

### Step 2 — 填四个 TODO

四个函数在 [jobs/import_beike_listings.py](../jobs/import_beike_listings.py) 顶部 TODO 注释里，全有占位实现 + 常见 pattern：

| TODO # | 函数 | 现状 | 你要做的 |
|---|---|---|---|
| 1 | `acquire_token` | 抛 NotImplementedError | 按官方 token 协议（多半是 `app_id + app_ak + timestamp + signature`，HMAC-SHA256 / MD5）实现 |
| 2 | `fetch_listings_page` | 占位 endpoint = `https://api.ke.com/v1/listing/search` | 替换为真实 endpoint 路径 + 参数名（city / district / biz_type 等） |
| 3 | `normalize_listing` | 占位字段名 = `resblock_id` / `house_code` / `total_price_wan` 等 | 跟实际响应字段对齐 |
| 4 | `extract_rows` | 假设 `{code: 0, data: {list: [...], total: N}}` | 按真实包裹格式调整 |

每个 TODO 都有"常见 pattern"注释，多数情况下小改即可。

### Step 3 — 验证

```bash
# 干跑（不会调真 API），先确认骨架还编译：
python3 jobs/import_beike_listings.py --dry-run --district baoshan

# 真跑，单区单页测试（量小，避免试用配额烧光）：
python3 jobs/import_beike_listings.py --district baoshan --max-pages 1 --page-size 5
```

成功的标志：`tmp/import-runs/beike-import-<TS>/` 出现，里面 `normalized_sale.json` / `normalized_rent.json` 有真实数据。重启 uvicorn 后用户平台立刻能用。

### Step 4 — 拉量

`jobs/import_beike_listings.py` 默认拉 `bao​shan` / `jingan` / `jinshan` 三区（Option C 修宝山/静安/金山的 rent 缺口）：

```bash
# 修 Option C（三区 rent backfill）：
python3 jobs/import_beike_listings.py --max-pages 5

# 全量拉所有区：
for d in huangpu jingan xuhui changning putuo hongkou yangpu minhang \
         baoshan jiading pudong jinshan songjiang qingpu fengxian chongming; do
  python3 jobs/import_beike_listings.py --district $d --max-pages 10
done
```

## Quota / 速率注意

试用层一般是几千次/天上限，所以默认参数（`--page-size 20 --max-pages 10 --pause-ms 200`）单区限制在 ~200 条 listings。觉得限太狠就自己改。如果撞 429，把 `--pause-ms` 调到 500-1000。

## 如果卡住

最快路径：
1. 把 token 获取响应（去掉真值）贴给我
2. 把任意一条 listing 的真实 JSON 字段（去掉敏感 ID）贴给我

我下次能直接照着写 `acquire_token` + `normalize_listing` 的 final 版本。

## 别走的路

- **绕开签名直接 GET**：会被风控，IP 可能被封
- **用 `requests` 库**：项目刻意只用 stdlib，加 deps 是 policy change
- **把 secret 落 git**：`BEIKE_APP_AK` 永远只在 `.env.local`（gitignored）
