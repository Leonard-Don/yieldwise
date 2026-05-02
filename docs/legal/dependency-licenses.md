# Yieldwise — Dependency License Matrix

- **Generated:** 2026-05-01
- **Tool:** `pip-licenses` against `api/requirements.txt`, supplemented by `pip show` for PEP 639 `License-Expression` fields that pip-licenses 4.x does not parse
- **Audit policy:**
  - ✅ Acceptable: MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause, ISC, MPL-2.0, LGPL-3.0-only / LGPL-3.0-or-later when consumed via dynamic import only (no static linking, no modification, no derivative distribution)
  - ❌ Forbidden in `main`: GPL-*, AGPL-*, statically-linked LGPL
  - 🟡 Per-case review: SSPL, BSL — confirm scope at next refresh
- **Frontend deps:** loaded via CDN script tags from `frontend/*/index.html` —
  - 高德 SDK：本地运行时由使用者自行配置个人/开发 Key，并遵守高德平台条款

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

The following dependencies are LGPL-3.0-only. They are consumed via Python `import` only: no static linking, no modification, no redistribution of modified versions. Per the local open-source audit policy this is acceptable.

| Package | Version | License | Usage | Justification |
|---|---|---|---|---|
| psycopg | 3.x | LGPL-3.0-only | PostgreSQL driver, dynamic `import psycopg` | mature Python Postgres driver for local PostGIS workflows |
| psycopg-pool | 3.x | LGPL-3.0-only | Connection pool wrapper | companion to psycopg; same legal posture |

If this project ever needs a stricter dependency posture for public packaging, evaluate `pg8000` (BSD-3-Clause) in a separate technical migration.

## Frontend / Vendored Assets

| 资产 | 来源 | 许可 | 备注 |
| --- | --- | --- | --- |
| AMap JS API | api.amap.com | 按高德平台条款 | 本地使用者自行配置个人/开发 Key |

## Refresh policy

每次 `api/requirements.txt` 修改后：

1. 重跑生成命令 + `pip show` 校验 UNKNOWN 行
2. 把表更新进本文件
3. 在 PR 描述里贴 diff
