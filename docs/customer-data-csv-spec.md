# Yieldwise Customer Data CSV Spec

Three CSV templates available at `/api/v2/customer-data/templates/{type}.csv`.
All require UTF-8 with BOM (Excel CN default), comma-delimited, first row is header.

## portfolio.csv (在管房源)

| 列 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| project_name | text | ✓ | 项目名（client + project_name 唯一） |
| address | text |  | 详细地址 |
| building_no | text |  | 楼栋号 |
| unit_type | text |  | 户型，如 `2室1厅` |
| monthly_rent_cny | decimal |  | 月租金（元） |
| occupancy_rate_pct | decimal |  | 出租率百分比（0-100） |
| move_in_date | YYYY-MM-DD |  | 入住日期 |
| longitude | float | ✓ | GCJ-02 经度 |
| latitude | float | ✓ | GCJ-02 纬度 |

## pipeline.csv (候选标的)

| 列 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| project_name | text | ✓ |  |
| address | text |  |  |
| stage | enum | ✓ | `lead` / `qualified` / `negotiating` / `won` / `lost` |
| est_price_cny | decimal |  | 预估总价 |
| notes | text |  |  |
| longitude | float | ✓ |  |
| latitude | float | ✓ |  |
| updated_at | YYYY-MM-DD |  | 阶段最近更新日期 |

## comp_set.csv (比准数据)

| 列 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| source | text | ✓ | 报告来源（如 `戴德梁行 2026Q1`） |
| report_date | YYYY-MM-DD |  |  |
| address | text |  |  |
| transaction_price_cny | decimal |  | 成交总价 |
| rent_per_sqm_cny | decimal |  | 单平租金 |
| area_sqm | decimal |  | 面积 |
| longitude | float | ✓ |  |
| latitude | float | ✓ |  |

## 行级错误

任何字段类型不符 / 必填缺失 / longitude/latitude 越界（绝对值超过 180/90）→ 该行进 `errors.json`，不阻塞其它行。前端 UI 会展示前 20 条错误并允许 admin/analyst 在确认后 `?force=true` 持久化。
