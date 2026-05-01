# Yieldwise — Dependency License Matrix

- **Generated:** 2026-05-01
- **Tool:** `pip-licenses` against `api/requirements.txt`, supplemented by `pip show` for PEP 639 `License-Expression` fields that pip-licenses 4.x does not parse
- **Audit policy:**
  - ✅ Acceptable: MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause, ISC, MPL-2.0, LGPL-3.0-only / LGPL-3.0-or-later when consumed via dynamic import only (no static linking, no modification, no derivative distribution)
  - ❌ Forbidden in `main`: GPL-*, AGPL-*, statically-linked LGPL
  - 🟡 Per-case review: SSPL, BSL — confirm scope at next refresh
- **Frontend deps:** loaded via CDN script tags from `frontend/*/index.html` —
  - 高德 SDK：客户使用商用 key，许可由客户与高德直接签署（参见部署 SOP）

## Backend Dependencies

(Auto-generated table from pip-licenses. Rows with UNKNOWN license cross-checked via `pip show` and reported in the LGPL section below.)

| Name             | Version | License                 | URL                                        |
|------------------|---------|-------------------------|--------------------------------------------|
| fastapi          | 0.116.1 | MIT License             | https://github.com/fastapi/fastapi         |
| psycopg          | 3.3.3   | UNKNOWN                 | https://psycopg.org/                       |
| psycopg-pool     | 3.3.0   | UNKNOWN                 | https://psycopg.org/                       |
| PyYAML           | 6.0.2   | MIT License             | https://pyyaml.org/                        |
| uvicorn          | 0.35.0  | BSD License             | https://www.uvicorn.org/                   |

`pip show` cross-check for UNKNOWN / underspecified rows:

| Package          | `License` / `License-Expression` (PEP 639) |
|------------------|--------------------------------------------|
| psycopg          | LGPL-3.0-only                              |
| psycopg-pool     | LGPL-3.0-only                              |
| uvicorn          | BSD-3-Clause                               |

## LGPL Components (Dynamic Import)

The following dependencies are LGPL-3.0-only. They are consumed via Python `import` only — no static linking, no modification, no redistribution of modified versions. Per the audit policy this is acceptable; client legal review should confirm against their own corporate policy.

| Package | Version | License | Usage | Justification |
|---|---|---|---|---|
| psycopg | 3.x | LGPL-3.0-only | PostgreSQL driver, dynamic `import psycopg` | de facto Python Postgres driver; no commercial drop-in replacement at parity |
| psycopg-pool | 3.x | LGPL-3.0-only | Connection pool wrapper | companion to psycopg; same legal posture |

If the client's policy disallows LGPL outright, swap for `pg8000` (BSD-3-Clause). This requires a code migration: pg8000 has different cursor/row API, no async, no built-in pool — re-evaluate before committing to the swap.

## Frontend / Vendored Assets

| 资产 | 来源 | 许可 | 备注 |
| --- | --- | --- | --- |
| AMap JS API | api.amap.com | 商业版需高德商用 key | 客户自备 |

## Refresh policy

每次 `api/requirements.txt` 修改后：

1. 重跑生成命令 + `pip show` 校验 UNKNOWN 行
2. 把表更新进本文件
3. 在 PR 描述里贴 diff
