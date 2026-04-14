# Public Sampling Backlog

这份 backlog 记录当前最值得继续补的公开页面人工采样任务，目标是把重点区楼栋和楼层证据继续做厚。

## 第一优先级

- 中兴新村 `1号楼 4层`
  - 目标：把当前 floor task 从单对样本推进到双对样本。
- 中兴新村 `5号楼 6层`
  - 目标：补第二组 sale / rent pair，增强崇明低总价样本稳定性。
- 松江大学城嘉和休闲广场 `B座 8层`
  - 目标：把当前单对样本推进到双对样本，平衡 A / B 两栋。
- 七宝云庭 `3幢 8层`
  - 目标：补足七宝云庭第三栋的楼层证据，减少楼栋间不均衡。

## 第二优先级

- 张江汤臣豪园三期 `2号楼 9层`
  - 目标：把张江第二栋从单层证据扩到双对样本。
- 张江汤臣豪园三期 `7号楼 14层`
  - 目标：继续加第二组 pair，增强新增楼栋证据。
- 海湾艺墅 `2号楼 3层`
  - 目标：补第二组 pair，提升远郊盘稳健度。
- 海湾艺墅 `9号楼 5层`
  - 目标：平衡同小区不同楼栋样本。

## 采样要求

- 每个目标优先补 `1 sale + 1 rent` 成对样本。
- 尽量保持：
  - 同一楼栋
  - 楼层差不超过 `1`
  - 面积差尽量小于 `2 sqm`
- 必填字段：
  - 小区
  - 楼栋
  - 单元
  - 楼层 / 总层数
  - 面积
  - 户型
  - 总价或月租
  - 发布时间

## 操作建议

1. 先在工作台看 `公开页面采样执行台` 和 `attention 回看面板`。
2. 再把样本补到：
   - `data/public-snapshot/2026-04-12/public_browser_sampling_sale.csv`
   - `data/public-snapshot/2026-04-12/public_browser_sampling_rent.csv`
3. 补完后跑：

```bash
python3 jobs/materialize_public_snapshot.py \
  --snapshot-dir data/public-snapshot/2026-04-12 \
  --snapshot-date 2026-04-14
```
