# Yieldwise Plan 3 — M3 Customer Data Import

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship Yieldwise v0.3 — customer-supplied CSV import for three data types (portfolio / pipeline / comp_set). Customers download CSV templates, fill them with their authorized data, upload, review staged results, persist to PostgreSQL. Admins / analysts can upload; viewers read.

**Architecture:** New `api/customer_data/` package: pydantic row models per type, CSV parser with row-level error capture, staged-first storage helper that writes JSON + summary to `tmp/customer-data-runs/<run_id>/`, and a Postgres persistence helper that drains a staged run into `customer_data.{portfolio,pipeline,comp_set,import_errors}` tables. `api/domains/customer_data.py` exposes upload (multipart-form), staged-status, persist, and read endpoints under `/api/v2/customer-data/*` — gated by the existing `Depends(current_user)` from M2 plus per-route role checks. Frontend gets a new admin page `/admin/customer-data` (template downloads + upload form per type + staged-run status + errors table), reusing the admin `<title>` + `escapeHTML` patterns from P2-B5. CSV format is UTF-8-BOM (Excel CN compatibility), comma-delimited, ISO-8601 dates. Coordinates are explicit `longitude` / `latitude` columns (GCJ-02); address-only geocoding deferred to v0.4 to keep M3 scope tight.

**Tech Stack:** FastAPI · Pydantic 2.x · python's stdlib `csv` module (no extra deps) · existing `psycopg`+`psycopg-pool` connection pool from `api/persistence.py` · vanilla JS ES modules · pytest + `node:test`.

**Parent spec:** `docs/superpowers/specs/2026-04-29-yieldwise-commercialization-design.md` §5.1 M3.

**Predecessors:**
- `docs/superpowers/plans/2026-04-29-yieldwise-plan-1-foundation.md` — tag `yieldwise-v0.1-foundation` (commit `9191d24`)
- `docs/superpowers/plans/2026-04-29-yieldwise-plan-2-auth.md` — tag `yieldwise-v0.2-auth` (commit `4c7bcaa`)

---

## Scope

This plan covers ONLY M3 Customer Data Import.

**Out of scope (subsequent plans):**
- **Plan 4** — M4 Reports + M5 Deployment Package (~7–10 工程日)
- **Plan 5** — M6 Backstage Workflow Pivot + T2 service.py cleanup (~10–12 工程日)
- v0.4 — address-only geocoding when CSV lacks coordinates (M3 v0.3 requires explicit lng/lat)
- v0.4 — REST API for clients to push from internal BI (M3 v0.3 is upload-only via the admin UI)

**Total this plan:** ~5–7 工程日 ≈ 3 weeks part-time.

---

## Design Decisions

1. **Three data types, three tables** (per spec §5.1 M3 table):
   - `customer_data.portfolio` — properties under management. Fields: `project_name`, `address`, `building_no`, `unit_type`, `monthly_rent_cny`, `occupancy_rate_pct`, `move_in_date`, `longitude`, `latitude`.
   - `customer_data.pipeline` — acquisition candidates. Fields: `project_name`, `address`, `stage` (lead/qualified/negotiating/won/lost), `est_price_cny`, `notes`, `longitude`, `latitude`, `updated_at`.
   - `customer_data.comp_set` — third-party reference points. Fields: `source` (e.g. "戴德梁行 2026Q1"), `report_date`, `address`, `transaction_price_cny`, `rent_per_sqm_cny`, `area_sqm`, `longitude`, `latitude`.
2. **CSV format**: UTF-8 with BOM, comma-delimited, header row required, ISO-8601 dates (`YYYY-MM-DD`). UTF-8 BOM accommodates Excel CN's default opening behavior.
3. **Coordinates explicit**: `longitude` + `latitude` columns (GCJ-02). Reject rows without both. v0.4 will add address-only geocoding via the existing AMap pattern at `jobs/enrich_community_anchors.py`.
4. **Staged-first**: every upload writes to `tmp/customer-data-runs/<run_id>/{portfolio,pipeline,comp_set,errors}.json` + `summary.json` (matches existing `tmp/import-runs/` pattern). Persist is a separate explicit action.
5. **Row error policy**: parse errors don't fail the whole upload. Bad rows go into `errors.json` with `{row_index, raw_values, error_messages}`. Frontend shows error count + first 20 errors. Persist refuses to drain a run with errors unless `?force=true` (admin only).
6. **File limits**: 10 MB max upload, 50000 rows max per type. Configurable via env (`ATLAS_CUSTOMER_DATA_MAX_BYTES`, `ATLAS_CUSTOMER_DATA_MAX_ROWS`). Document defaults.
7. **Persist semantics**: Postgres write is upsert-by-`(client_id, project_name)` for portfolio/pipeline; comp_set is append-only (each report is a new row). `client_id` is the username of the uploading admin/analyst (single-tenant deploy → one client_id per deploy → effectively a partition key, not a tenant filter).
8. **Run rotation**: keep last 30 days of `tmp/customer-data-runs/`; older runs pruned by a `scripts/prune_customer_data_runs.py` cron candidate. Defer the cron itself to ops.
9. **Auth**:
   - `POST /api/v2/customer-data/imports` — admin OR analyst
   - `POST /api/v2/customer-data/imports/{id}/persist` — admin OR analyst
   - `GET /api/v2/customer-data/imports/{id}` — any authenticated user
   - `GET /api/v2/customer-data/{type}` — any authenticated user (read)
   - `GET /api/v2/customer-data/templates/{type}.csv` — any authenticated user (download blank)
10. **Persist runs in `database` mode only**. In `staged` mode the persist endpoint returns 503 "no database configured". This matches the existing 3-mode runtime contract.

---

## File Structure (Plan 3 outcome)

```
api/
├── main.py                          # MODIFIED: include customer_data router; serve /admin/customer-data HTML
├── customer_data/                   # NEW package
│   ├── __init__.py
│   ├── models.py                    # NEW — pydantic row models per type
│   ├── parser.py                    # NEW — CSV → rows + errors
│   ├── staging.py                   # NEW — write/read tmp/customer-data-runs/<run_id>/*
│   ├── persistence.py               # NEW — drain a staged run into Postgres
│   └── templates/                   # NEW — CSV blank templates (committed)
│       ├── portfolio.csv
│       ├── pipeline.csv
│       └── comp_set.csv
├── domains/
│   └── customer_data.py             # NEW — /api/v2/customer-data/* endpoints
├── schemas/
│   └── customer_data.py             # NEW — pydantic request/response models
├── persistence.py                   # MODIFIED: + customer_data table create-if-missing helper
└── requirements.txt                 # unchanged

frontend/
├── admin/
│   ├── customer-data.html           # NEW — admin/analyst upload page
│   ├── customer-data.css            # NEW
│   └── customer-data.js             # NEW

db/
└── customer_data.sql                # NEW — DDL for customer_data.* tables

docs/
├── deployment/
│   └── customer-data-import.md      # NEW — CSV format, runs lifecycle, persist semantics
└── customer-data-csv-spec.md        # NEW — column-by-column reference

tests/api/
├── test_customer_data_models.py     # NEW (~5 cases)
├── test_customer_data_parser.py     # NEW (~6 cases)
├── test_customer_data_staging.py    # NEW (~4 cases)
├── test_customer_data_endpoints.py  # NEW (~8 cases)
└── test_customer_data_read.py       # NEW (~3 cases)

tests/frontend/
└── test_customer_data_helpers.mjs   # NEW (~3 cases)

scripts/
├── phase1_smoke.py                  # MODIFIED: + /api/v2/customer-data/templates/portfolio.csv check
└── prune_customer_data_runs.py      # NEW — ops helper, cron-friendly

README.md                            # MODIFIED: + brief Customer Data section
```

---

## Phase A: Schema + CSV templates + template downloads (~1 工程日)

### Task A.1: Database DDL for `customer_data` schema

**Why:** Customer data lives in its own Postgres schema so it's clearly separated from research data + easy to back up / drop without touching the research surface.

**Files:**
- Create: `db/customer_data.sql`
- Modify: `api/persistence.py` (add `ensure_customer_data_schema()` helper)

**Steps:**

1. Create `db/customer_data.sql`:

```sql
-- Yieldwise customer data schema. Single-tenant: client_id is the
-- uploading user's username (effectively a partition key on each row).

CREATE SCHEMA IF NOT EXISTS customer_data;

CREATE TABLE IF NOT EXISTS customer_data.portfolio (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    address TEXT,
    building_no TEXT,
    unit_type TEXT,
    monthly_rent_cny NUMERIC(14, 2),
    occupancy_rate_pct NUMERIC(5, 2),
    move_in_date DATE,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (client_id, project_name)
);
CREATE INDEX IF NOT EXISTS portfolio_client_idx ON customer_data.portfolio (client_id);

CREATE TABLE IF NOT EXISTS customer_data.pipeline (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    address TEXT,
    stage TEXT NOT NULL CHECK (stage IN ('lead', 'qualified', 'negotiating', 'won', 'lost')),
    est_price_cny NUMERIC(16, 2),
    notes TEXT,
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    updated_at DATE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (client_id, project_name)
);
CREATE INDEX IF NOT EXISTS pipeline_client_idx ON customer_data.pipeline (client_id);
CREATE INDEX IF NOT EXISTS pipeline_stage_idx ON customer_data.pipeline (client_id, stage);

CREATE TABLE IF NOT EXISTS customer_data.comp_set (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    source TEXT NOT NULL,
    report_date DATE,
    address TEXT,
    transaction_price_cny NUMERIC(16, 2),
    rent_per_sqm_cny NUMERIC(10, 2),
    area_sqm NUMERIC(10, 2),
    longitude DOUBLE PRECISION NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS comp_set_client_idx ON customer_data.comp_set (client_id);
CREATE INDEX IF NOT EXISTS comp_set_source_idx ON customer_data.comp_set (client_id, source, report_date);

CREATE TABLE IF NOT EXISTS customer_data.import_errors (
    id BIGSERIAL PRIMARY KEY,
    client_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('portfolio', 'pipeline', 'comp_set')),
    row_index INT NOT NULL,
    raw_values JSONB NOT NULL,
    error_messages JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS import_errors_run_idx ON customer_data.import_errors (run_id);
```

2. Add a helper to `api/persistence.py`. Find a sensible spot near other DDL helpers:

```python
def ensure_customer_data_schema(*, dsn: str | None = None) -> None:
    """Apply db/customer_data.sql idempotently. Called by domains/customer_data
    before every persist; cheap because every statement is IF NOT EXISTS."""
    import pathlib
    sql_path = pathlib.Path(__file__).resolve().parents[1] / "db" / "customer_data.sql"
    sql_text = sql_path.read_text(encoding="utf-8")
    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.commit()
```

3. Run pytest to confirm no break:
```bash
pytest tests/api -x --timeout=30 2>&1 | tail -3
```
Expected: 228 passed, 1 skipped (unchanged from Plan 2 ship).

4. Commit:
```bash
git add db/customer_data.sql api/persistence.py
git commit -m "$(cat <<'EOF'
feat(customer-data): customer_data Postgres schema + apply helper (M3)

DDL for portfolio / pipeline / comp_set / import_errors. All four
tables key on client_id (the uploading user's username — effective
partition key in single-tenant deploy). Lng/lat are NOT NULL; v0.3
requires explicit coordinates (geocoding deferred to v0.4).

ensure_customer_data_schema() in api/persistence.py applies the SQL
idempotently; called by the customer_data domain before each
persist.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.2: CSV templates (committed)

**Why:** Customers download blank templates from the admin UI to know which columns + headers to fill.

**Files:**
- Create: `api/customer_data/templates/portfolio.csv`
- Create: `api/customer_data/templates/pipeline.csv`
- Create: `api/customer_data/templates/comp_set.csv`
- Create: `api/customer_data/__init__.py` (1-line docstring)

**Steps:**

1. Create `api/customer_data/__init__.py`:
```python
"""Yieldwise customer data import — CSV parsing, staging, persistence."""
```

2. Create `api/customer_data/templates/portfolio.csv` with UTF-8 BOM. The first byte must be `﻿`. The simplest way:

```bash
printf '\xef\xbb\xbf' > api/customer_data/templates/portfolio.csv
cat >> api/customer_data/templates/portfolio.csv <<'CSV'
project_name,address,building_no,unit_type,monthly_rent_cny,occupancy_rate_pct,move_in_date,longitude,latitude
示例项目,上海市浦东新区张江路123号,1号楼,2室1厅,7800.00,95.0,2024-09-01,121.5917,31.2120
CSV
```

3. Same for `pipeline.csv`:
```bash
printf '\xef\xbb\xbf' > api/customer_data/templates/pipeline.csv
cat >> api/customer_data/templates/pipeline.csv <<'CSV'
project_name,address,stage,est_price_cny,notes,longitude,latitude,updated_at
示例标的A,上海市徐汇区漕河泾,negotiating,180000000.00,首轮报价,121.4011,31.1735,2026-04-15
CSV
```

4. And `comp_set.csv`:
```bash
printf '\xef\xbb\xbf' > api/customer_data/templates/comp_set.csv
cat >> api/customer_data/templates/comp_set.csv <<'CSV'
source,report_date,address,transaction_price_cny,rent_per_sqm_cny,area_sqm,longitude,latitude
戴德梁行2026Q1,2026-03-31,上海市静安区南京西路,250000000.00,180.5,1500.0,121.4651,31.2304
CSV
```

5. Verify BOM is present:
```bash
head -c 3 api/customer_data/templates/portfolio.csv | xxd
```
Expected: `00000000: efbb bf` followed by header bytes.

6. Commit:
```bash
git add api/customer_data/__init__.py api/customer_data/templates/
git commit -m "$(cat <<'EOF'
feat(customer-data): CSV blank templates (M3)

UTF-8 BOM (Excel CN compatibility) + comma delimiter + header row.
One example row per template documents expected types (ISO date,
GCJ-02 lng/lat, 2-decimal CNY).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task A.3: Template-download endpoint

**Why:** Frontend admin page links to these. They're admin-only assets but reachable from any authenticated user.

**Files:**
- Create: `api/domains/customer_data.py` (initial — only template endpoint)
- Modify: `api/main.py` (include router)
- Create: `tests/api/test_customer_data_endpoints.py` (initial — 1 case)

**TDD first.**

**Steps:**

1. Write the failing test `tests/api/test_customer_data_endpoints.py`:

```python
"""Customer data endpoint tests — start with template download."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    yield


def _login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def _seed_and_login(role="analyst"):
    user_store.create_user(username="u", password="hunter22", role=role)
    client = TestClient(app)
    _login(client, "u", "hunter22")
    return client


def test_portfolio_template_downloads_with_bom():
    client = _seed_and_login()
    r = client.get("/api/v2/customer-data/templates/portfolio.csv")
    assert r.status_code == 200
    # First 3 bytes must be the UTF-8 BOM
    assert r.content.startswith(b"\xef\xbb\xbf")
    text = r.content.decode("utf-8-sig")
    assert "project_name" in text.split("\n", 1)[0]
    assert r.headers.get("content-type", "").startswith("text/csv")


def test_unknown_template_404():
    client = _seed_and_login()
    r = client.get("/api/v2/customer-data/templates/unknown.csv")
    assert r.status_code == 404
```

2. Run — must fail (404 because the endpoint doesn't exist yet).

3. Create `api/domains/customer_data.py`:

```python
"""Customer data import endpoints — templates, upload, persist, read."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status

router = APIRouter(tags=["customer-data"])

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "customer_data" / "templates"
_TEMPLATE_TYPES = ("portfolio", "pipeline", "comp_set")


@router.get("/customer-data/templates/{template_name}")
def download_template(template_name: str) -> Response:
    # template_name is "<type>.csv"
    if not template_name.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    type_ = template_name[: -len(".csv")]
    if type_ not in _TEMPLATE_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    path = _TEMPLATE_DIR / template_name
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="template missing")
    return Response(
        content=path.read_bytes(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="yieldwise-{template_name}"',
        },
    )
```

4. Wire in `api/main.py`. Add to the existing `from .domains import (...)` block (alphabetical):
```python
from .domains import (
    auth as v2_auth,
    alerts as v2_alerts,
    annotations as v2_annotations,
    buildings as v2_buildings,
    communities as v2_communities,
    config as v2_config,
    customer_data as v2_customer_data,  # NEW
    districts as v2_districts,
    ...
)
```

Then in the include_router block:
```python
app.include_router(
    v2_customer_data.router,
    prefix="/api/v2",
    dependencies=_AUTH_REQUIRED,
)
```

5. Run test — must pass:
```bash
pytest tests/api/test_customer_data_endpoints.py -v
```
Expected: 2 passed.

6. Commit:
```bash
git add api/domains/customer_data.py api/main.py tests/api/test_customer_data_endpoints.py
git commit -m "$(cat <<'EOF'
feat(customer-data): GET /api/v2/customer-data/templates/{name}.csv (M3)

Admin/analyst/viewer can download CSV blanks. Filename suggested
via Content-Disposition (yieldwise-portfolio.csv etc).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase B: Row models + parser + staging (~1.5 工程日)

### Task B.1: Pydantic row models

**Files:**
- Create: `api/customer_data/models.py`
- Create: `tests/api/test_customer_data_models.py`

**TDD.**

**Steps:**

1. Write `tests/api/test_customer_data_models.py`:

```python
"""Customer data row model tests."""
from __future__ import annotations

import pytest

from api.customer_data.models import (
    CompSetRow,
    PipelineRow,
    PortfolioRow,
    ROW_MODELS,
)


def test_portfolio_row_validates_lng_lat_required():
    with pytest.raises(ValueError):
        PortfolioRow(project_name="x", longitude=None, latitude=31.0)


def test_portfolio_row_accepts_iso_date_string():
    r = PortfolioRow(
        project_name="A",
        address="addr",
        building_no="1",
        unit_type="2室1厅",
        monthly_rent_cny=7800,
        occupancy_rate_pct=95,
        move_in_date="2024-09-01",
        longitude=121.59,
        latitude=31.21,
    )
    assert r.move_in_date.isoformat() == "2024-09-01"
    assert float(r.monthly_rent_cny) == 7800.0


def test_pipeline_row_rejects_invalid_stage():
    with pytest.raises(ValueError, match="stage"):
        PipelineRow(
            project_name="P", stage="not-a-stage",
            longitude=121.5, latitude=31.0,
        )


def test_pipeline_row_accepts_all_stages():
    for stage in ("lead", "qualified", "negotiating", "won", "lost"):
        r = PipelineRow(
            project_name="P", stage=stage,
            longitude=121.5, latitude=31.0,
        )
        assert r.stage == stage


def test_comp_set_row_iso_date_and_numeric_fields():
    r = CompSetRow(
        source="戴德梁行 2026Q1",
        report_date="2026-03-31",
        address="addr",
        transaction_price_cny="250000000.00",
        rent_per_sqm_cny="180.5",
        area_sqm=1500,
        longitude=121.46,
        latitude=31.23,
    )
    assert r.report_date.isoformat() == "2026-03-31"
    assert float(r.transaction_price_cny) == 250_000_000.0


def test_row_models_registry():
    assert ROW_MODELS["portfolio"] is PortfolioRow
    assert ROW_MODELS["pipeline"] is PipelineRow
    assert ROW_MODELS["comp_set"] is CompSetRow
```

2. Run — must fail (ImportError).

3. Create `api/customer_data/models.py`:

```python
"""Pydantic row models for customer_data uploads."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator

Stage = Literal["lead", "qualified", "negotiating", "won", "lost"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore", str_strip_whitespace=True)


class PortfolioRow(_Base):
    project_name: str
    address: str | None = None
    building_no: str | None = None
    unit_type: str | None = None
    monthly_rent_cny: Decimal | None = None
    occupancy_rate_pct: Decimal | None = None
    move_in_date: date | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)


class PipelineRow(_Base):
    project_name: str
    address: str | None = None
    stage: Stage
    est_price_cny: Decimal | None = None
    notes: str | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)
    updated_at: date | None = None


class CompSetRow(_Base):
    source: str
    report_date: date | None = None
    address: str | None = None
    transaction_price_cny: Decimal | None = None
    rent_per_sqm_cny: Decimal | None = None
    area_sqm: Decimal | None = None
    longitude: float = Field(..., gt=-180, lt=180)
    latitude: float = Field(..., gt=-90, lt=90)


ROW_MODELS: dict[str, Type[_Base]] = {
    "portfolio": PortfolioRow,
    "pipeline": PipelineRow,
    "comp_set": CompSetRow,
}
```

4. Run — must pass:
```bash
pytest tests/api/test_customer_data_models.py -v
```
Expected: 6 passed.

5. Commit:
```bash
git add api/customer_data/models.py tests/api/test_customer_data_models.py
git commit -m "$(cat <<'EOF'
feat(customer-data): pydantic row models (M3)

PortfolioRow / PipelineRow / CompSetRow with field validators.
str_strip_whitespace handles raw CSV cells. Lng/Lat required and
range-checked. ROW_MODELS registry keyed by type slug.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.2: CSV parser with row-level error capture

**Files:**
- Create: `api/customer_data/parser.py`
- Create: `tests/api/test_customer_data_parser.py`

**TDD.**

**Steps:**

1. Write `tests/api/test_customer_data_parser.py`:

```python
"""CSV parser tests."""
from __future__ import annotations

import io

import pytest

from api.customer_data.parser import ParseResult, parse_csv


_GOOD_PORTFOLIO_CSV = (
    "﻿project_name,address,building_no,unit_type,monthly_rent_cny,"
    "occupancy_rate_pct,move_in_date,longitude,latitude\n"
    "Alpha,addr1,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    "Beta,addr2,2,3-1,9000,88.5,2025-01-15,121.40,31.18\n"
)


def test_parse_good_csv_returns_rows_no_errors():
    res = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    assert isinstance(res, ParseResult)
    assert len(res.rows) == 2
    assert res.errors == []
    assert res.rows[0].project_name == "Alpha"


def test_parse_strips_utf8_bom():
    res = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    # BOM must not contaminate the first column header
    assert res.rows[0].project_name == "Alpha"


def test_parse_captures_invalid_row_in_errors():
    bad_csv = (
        "project_name,address,building_no,unit_type,monthly_rent_cny,"
        "occupancy_rate_pct,move_in_date,longitude,latitude\n"
        "Good,a,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
        "Bad,a,1,2-1,not-a-number,95,2024-09-01,121.59,31.21\n"
        ",a,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    )
    res = parse_csv(bad_csv.encode("utf-8"), type_="portfolio")
    assert len(res.rows) == 1
    assert len(res.errors) == 2
    assert res.errors[0]["row_index"] == 2  # 1-based, header is row 1
    assert "monthly_rent_cny" in str(res.errors[0]["error_messages"])


def test_parse_rejects_unknown_type():
    with pytest.raises(ValueError, match="type"):
        parse_csv(b"x,y\n", type_="not-a-type")


def test_parse_pipeline_validates_stage():
    pipeline_csv = (
        "project_name,address,stage,est_price_cny,notes,longitude,latitude,updated_at\n"
        "P1,a,negotiating,1000000,note,121.5,31.0,2026-04-15\n"
        "P2,a,bogus,500000,note,121.5,31.0,2026-04-15\n"
    )
    res = parse_csv(pipeline_csv.encode("utf-8"), type_="pipeline")
    assert len(res.rows) == 1
    assert len(res.errors) == 1


def test_parse_empty_file_returns_zero_rows_no_errors():
    res = parse_csv(b"", type_="portfolio")
    assert res.rows == []
    assert res.errors == []
```

2. Create `api/customer_data/parser.py`:

```python
"""CSV → typed rows + per-row error capture."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Any

from .models import ROW_MODELS, _Base


@dataclass
class ParseResult:
    rows: list[_Base] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)


def parse_csv(content: bytes, *, type_: str) -> ParseResult:
    if type_ not in ROW_MODELS:
        raise ValueError(f"unknown customer-data type: {type_}")
    model_cls = ROW_MODELS[type_]
    if not content:
        return ParseResult()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    result = ParseResult()
    for idx, raw in enumerate(reader, start=2):  # row 1 is the header
        # Normalize empty cells to None so pydantic Optional fields work
        normalized = {k: (v if v != "" else None) for k, v in raw.items()}
        try:
            row = model_cls.model_validate(normalized)
        except Exception as exc:  # pydantic ValidationError or anything else
            result.errors.append(
                {
                    "row_index": idx,
                    "raw_values": raw,
                    "error_messages": _format_validation_error(exc),
                }
            )
            continue
        result.rows.append(row)
    return result


def _format_validation_error(exc: Exception) -> list[str]:
    if hasattr(exc, "errors"):
        try:
            return [
                f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            ]
        except Exception:
            pass
    return [str(exc)]
```

3. Run — must pass:
```bash
pytest tests/api/test_customer_data_parser.py -v
```
Expected: 6 passed.

4. Commit:
```bash
git add api/customer_data/parser.py tests/api/test_customer_data_parser.py
git commit -m "$(cat <<'EOF'
feat(customer-data): CSV parser with row-level error capture (M3)

UTF-8-sig handles BOM. Empty cells normalize to None for pydantic
Optional fields. Per-row pydantic ValidationError → ParseResult.errors
with row_index, raw_values, error_messages. row_index is 1-based,
header counts as row 1 so first data row is row 2.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task B.3: Staged-run helper

**Why:** Each upload writes a self-contained `tmp/customer-data-runs/<run_id>/` folder so persist is independent and runs are inspectable.

**Files:**
- Create: `api/customer_data/staging.py`
- Create: `tests/api/test_customer_data_staging.py`

**Steps:**

1. Write `tests/api/test_customer_data_staging.py`:

```python
"""Staged-run storage tests."""
from __future__ import annotations

import json

import pytest

from api.customer_data.parser import parse_csv
from api.customer_data.staging import (
    StagedRun,
    list_runs,
    load_run,
    save_run,
)


_GOOD_PORTFOLIO_CSV = (
    "project_name,address,building_no,unit_type,monthly_rent_cny,"
    "occupancy_rate_pct,move_in_date,longitude,latitude\n"
    "Alpha,addr1,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
)


@pytest.fixture(autouse=True)
def runs_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "customer-data-runs"))
    yield tmp_path / "customer-data-runs"


def test_save_run_writes_json_files_and_summary(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    run = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    assert isinstance(run, StagedRun)
    assert run.run_id
    files = sorted(p.name for p in (runs_dir / run.run_id).iterdir())
    assert "portfolio.json" in files
    assert "summary.json" in files
    summary = json.loads((runs_dir / run.run_id / "summary.json").read_text())
    assert summary["row_count"] == 1
    assert summary["error_count"] == 0
    assert summary["client_id"] == "alice"


def test_load_run_round_trips(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    saved = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    loaded = load_run(saved.run_id)
    assert loaded is not None
    assert loaded.run_id == saved.run_id
    assert loaded.row_count == 1
    assert loaded.error_count == 0


def test_load_unknown_run_returns_none(runs_dir):
    assert load_run("does-not-exist") is None


def test_list_runs_returns_recent_first(runs_dir):
    parsed = parse_csv(_GOOD_PORTFOLIO_CSV.encode("utf-8"), type_="portfolio")
    a = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    b = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    c = save_run(client_id="alice", type_="portfolio", parsed=parsed)
    runs = list_runs(client_id="alice")
    ids = [r.run_id for r in runs]
    assert ids == [c.run_id, b.run_id, a.run_id]
```

2. Create `api/customer_data/staging.py`:

```python
"""Staged-run storage for customer data uploads.

Layout:
  <runs_dir>/<run_id>/
    portfolio.json        rows: [{...}, ...]
    pipeline.json         (only if a pipeline upload)
    comp_set.json
    errors.json
    summary.json          {run_id, client_id, type, row_count, error_count, created_at}
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .parser import ParseResult


@dataclass(frozen=True)
class StagedRun:
    run_id: str
    client_id: str
    type_: str
    row_count: int
    error_count: int
    created_at: str


def _runs_dir() -> Path:
    override = os.environ.get("ATLAS_CUSTOMER_DATA_RUNS_DIR")
    base = Path(override) if override else Path(__file__).resolve().parents[2] / "tmp" / "customer-data-runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _new_run_id() -> str:
    # Lexicographically sortable: ISO timestamp + short suffix.
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return f"{ts}-{suffix}"


def save_run(*, client_id: str, type_: str, parsed: ParseResult) -> StagedRun:
    run_id = _new_run_id()
    run_dir = _runs_dir() / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    rows_payload = [r.model_dump(mode="json") for r in parsed.rows]
    (run_dir / f"{type_}.json").write_text(
        json.dumps(rows_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "errors.json").write_text(
        json.dumps(parsed.errors, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "client_id": client_id,
        "type": type_,
        "row_count": len(parsed.rows),
        "error_count": len(parsed.errors),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return StagedRun(
        run_id=run_id,
        client_id=client_id,
        type_=type_,
        row_count=len(parsed.rows),
        error_count=len(parsed.errors),
        created_at=summary["created_at"],
    )


def load_run(run_id: str) -> StagedRun | None:
    summary_path = _runs_dir() / run_id / "summary.json"
    if not summary_path.is_file():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return StagedRun(
        run_id=summary["run_id"],
        client_id=summary["client_id"],
        type_=summary["type"],
        row_count=summary["row_count"],
        error_count=summary["error_count"],
        created_at=summary["created_at"],
    )


def load_run_rows(run_id: str) -> list[dict]:
    """Return raw row dicts from <run_id>/<type>.json."""
    run = load_run(run_id)
    if run is None:
        return []
    rows_path = _runs_dir() / run_id / f"{run.type_}.json"
    if not rows_path.is_file():
        return []
    return json.loads(rows_path.read_text(encoding="utf-8"))


def list_runs(*, client_id: str | None = None) -> list[StagedRun]:
    """Return all runs, newest first. Optionally filtered by client_id."""
    runs: list[StagedRun] = []
    base = _runs_dir()
    if not base.is_dir():
        return runs
    for entry in sorted(base.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        run = load_run(entry.name)
        if run is None:
            continue
        if client_id is not None and run.client_id != client_id:
            continue
        runs.append(run)
    return runs
```

3. Run — must pass:
```bash
pytest tests/api/test_customer_data_staging.py -v
```
Expected: 4 passed.

4. Commit:
```bash
git add api/customer_data/staging.py tests/api/test_customer_data_staging.py
git commit -m "$(cat <<'EOF'
feat(customer-data): staged-run storage helper (M3)

save_run / load_run / list_runs writing JSON+summary to
tmp/customer-data-runs/<run_id>/. ATLAS_CUSTOMER_DATA_RUNS_DIR
overrides the path for tests + alternative deployments.
run_id is sortable (ISO ts + short suffix); newest-first listing.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase C: Upload + persist + read endpoints (~2 工程日)

### Task C.1: Upload endpoint (multipart-form, admin/analyst only)

**Files:**
- Modify: `api/domains/customer_data.py` (extend with upload route)
- Create: `api/schemas/customer_data.py`
- Modify: `tests/api/test_customer_data_endpoints.py` (add upload cases)

**Steps:**

1. Create `api/schemas/customer_data.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CustomerDataType = Literal["portfolio", "pipeline", "comp_set"]


class StagedRunSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(serialization_alias="runId")
    client_id: str = Field(serialization_alias="clientId")
    type: CustomerDataType
    row_count: int = Field(serialization_alias="rowCount")
    error_count: int = Field(serialization_alias="errorCount")
    created_at: str = Field(serialization_alias="createdAt")


class ImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: StagedRunSummary
    errors_preview: list[dict] = Field(default_factory=list, serialization_alias="errorsPreview")
```

2. Append to `api/domains/customer_data.py`:

```python
import os

from fastapi import Depends, File, Form, UploadFile

from api.auth.deps import current_user, require_role
from api.customer_data import staging
from api.customer_data.parser import parse_csv
from api.schemas.auth import CurrentUser
from api.schemas.customer_data import (
    CustomerDataType,
    ImportResponse,
    StagedRunSummary,
)


def _max_bytes() -> int:
    raw = os.environ.get("ATLAS_CUSTOMER_DATA_MAX_BYTES", str(10 * 1024 * 1024))
    return int(raw)


def _max_rows() -> int:
    raw = os.environ.get("ATLAS_CUSTOMER_DATA_MAX_ROWS", "50000")
    return int(raw)


def _summary_to_schema(s: staging.StagedRun) -> StagedRunSummary:
    return StagedRunSummary(
        run_id=s.run_id,
        client_id=s.client_id,
        type=s.type_,
        row_count=s.row_count,
        error_count=s.error_count,
        created_at=s.created_at,
    )


@router.post(
    "/customer-data/imports",
    response_model=ImportResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def upload_csv(
    type: CustomerDataType = Form(...),
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_role("admin", "analyst")),
) -> ImportResponse:
    body = await file.read()
    if len(body) > _max_bytes():
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds limit of {_max_bytes()} bytes",
        )
    parsed = parse_csv(body, type_=type)
    if len(parsed.rows) > _max_rows():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"row count {len(parsed.rows)} exceeds limit {_max_rows()}",
        )
    run = staging.save_run(client_id=user.username, type_=type, parsed=parsed)
    return ImportResponse(
        run=_summary_to_schema(run),
        errors_preview=parsed.errors[:20],
    )


@router.get(
    "/customer-data/imports/{run_id}",
    response_model=StagedRunSummary,
    response_model_by_alias=True,
)
def get_import_status(run_id: str, _: CurrentUser = Depends(current_user)) -> StagedRunSummary:
    run = staging.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return _summary_to_schema(run)


@router.get(
    "/customer-data/imports",
    response_model=list[StagedRunSummary],
    response_model_by_alias=True,
)
def list_imports(_: CurrentUser = Depends(current_user)) -> list[StagedRunSummary]:
    return [_summary_to_schema(r) for r in staging.list_runs()]
```

3. Append upload tests to `tests/api/test_customer_data_endpoints.py`:

```python
def test_upload_portfolio_creates_staged_run(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="al", password="hunter22", role="analyst")
    client = TestClient(app)
    _login(client, "al", "hunter22")
    csv_body = (
        "project_name,address,building_no,unit_type,monthly_rent_cny,"
        "occupancy_rate_pct,move_in_date,longitude,latitude\n"
        "Alpha,addr,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    ).encode("utf-8")
    r = client.post(
        "/api/v2/customer-data/imports",
        data={"type": "portfolio"},
        files={"file": ("portfolio.csv", csv_body, "text/csv")},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["run"]["rowCount"] == 1
    assert body["run"]["errorCount"] == 0
    assert body["run"]["clientId"] == "al"
    assert body["errorsPreview"] == []


def test_viewer_cannot_upload(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="v", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "v", "hunter22")
    csv_body = b"project_name,longitude,latitude\nA,121,31\n"
    r = client.post(
        "/api/v2/customer-data/imports",
        data={"type": "portfolio"},
        files={"file": ("p.csv", csv_body, "text/csv")},
    )
    assert r.status_code == 403


def test_get_import_status_unknown_returns_404(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    user_store.create_user(username="u", password="hunter22", role="viewer")
    client = TestClient(app)
    _login(client, "u", "hunter22")
    r = client.get("/api/v2/customer-data/imports/does-not-exist")
    assert r.status_code == 404
```

4. Run:
```bash
pytest tests/api/test_customer_data_endpoints.py -v
```
Expected: 5 passed (2 prior + 3 new).

5. Commit:
```bash
git add api/schemas/customer_data.py api/domains/customer_data.py tests/api/test_customer_data_endpoints.py
git commit -m "$(cat <<'EOF'
feat(customer-data): upload + status + list endpoints (M3)

POST /api/v2/customer-data/imports — multipart form (type + file),
admin or analyst role required. File size limit (default 10 MB)
and row count limit (default 50000) configurable via env. Errors
preview (first 20) returned in response.

GET /api/v2/customer-data/imports/{run_id} — staged-run summary;
404 if missing.

GET /api/v2/customer-data/imports — list all runs.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.2: Persist endpoint (stage → Postgres)

**Files:**
- Create: `api/customer_data/persistence.py`
- Modify: `api/domains/customer_data.py` (add persist route)
- Modify: `tests/api/test_customer_data_endpoints.py` (add persist case)

**Steps:**

1. Create `api/customer_data/persistence.py`:

```python
"""Drain a staged customer-data run into Postgres."""
from __future__ import annotations

from typing import Any

from api import persistence as db
from . import staging


_TABLE_FOR = {
    "portfolio": "customer_data.portfolio",
    "pipeline": "customer_data.pipeline",
    "comp_set": "customer_data.comp_set",
}

_UPSERT_KEY = {
    "portfolio": "(client_id, project_name)",
    "pipeline": "(client_id, project_name)",
    "comp_set": None,  # append-only
}


def persist_run(run_id: str, *, client_id: str) -> dict[str, Any]:
    """Drain the staged run into Postgres. Idempotent for upsert types."""
    run = staging.load_run(run_id)
    if run is None:
        raise FileNotFoundError(run_id)
    if run.client_id != client_id:
        raise PermissionError(f"run {run_id!r} belongs to {run.client_id!r}")
    rows = staging.load_run_rows(run_id)
    if not rows:
        return {"persisted_count": 0}

    db.ensure_customer_data_schema()
    table = _TABLE_FOR[run.type_]
    if run.type_ == "portfolio":
        return _upsert_portfolio(client_id, rows)
    if run.type_ == "pipeline":
        return _upsert_pipeline(client_id, rows)
    return _append_comp_set(client_id, rows)


def _upsert_portfolio(client_id: str, rows: list[dict]) -> dict[str, Any]:
    sql = """
    INSERT INTO customer_data.portfolio (
        client_id, project_name, address, building_no, unit_type,
        monthly_rent_cny, occupancy_rate_pct, move_in_date,
        longitude, latitude
    ) VALUES (
        %(client_id)s, %(project_name)s, %(address)s, %(building_no)s, %(unit_type)s,
        %(monthly_rent_cny)s, %(occupancy_rate_pct)s, %(move_in_date)s,
        %(longitude)s, %(latitude)s
    )
    ON CONFLICT (client_id, project_name) DO UPDATE SET
        address = EXCLUDED.address,
        building_no = EXCLUDED.building_no,
        unit_type = EXCLUDED.unit_type,
        monthly_rent_cny = EXCLUDED.monthly_rent_cny,
        occupancy_rate_pct = EXCLUDED.occupancy_rate_pct,
        move_in_date = EXCLUDED.move_in_date,
        longitude = EXCLUDED.longitude,
        latitude = EXCLUDED.latitude,
        imported_at = now()
    """
    n = 0
    with db.postgres_connection() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(sql, {**r, "client_id": client_id})
                n += 1
        conn.commit()
    return {"persisted_count": n}


def _upsert_pipeline(client_id: str, rows: list[dict]) -> dict[str, Any]:
    sql = """
    INSERT INTO customer_data.pipeline (
        client_id, project_name, address, stage, est_price_cny,
        notes, longitude, latitude, updated_at
    ) VALUES (
        %(client_id)s, %(project_name)s, %(address)s, %(stage)s, %(est_price_cny)s,
        %(notes)s, %(longitude)s, %(latitude)s, %(updated_at)s
    )
    ON CONFLICT (client_id, project_name) DO UPDATE SET
        address = EXCLUDED.address,
        stage = EXCLUDED.stage,
        est_price_cny = EXCLUDED.est_price_cny,
        notes = EXCLUDED.notes,
        longitude = EXCLUDED.longitude,
        latitude = EXCLUDED.latitude,
        updated_at = EXCLUDED.updated_at,
        imported_at = now()
    """
    n = 0
    with db.postgres_connection() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(sql, {**r, "client_id": client_id})
                n += 1
        conn.commit()
    return {"persisted_count": n}


def _append_comp_set(client_id: str, rows: list[dict]) -> dict[str, Any]:
    sql = """
    INSERT INTO customer_data.comp_set (
        client_id, source, report_date, address,
        transaction_price_cny, rent_per_sqm_cny, area_sqm,
        longitude, latitude
    ) VALUES (
        %(client_id)s, %(source)s, %(report_date)s, %(address)s,
        %(transaction_price_cny)s, %(rent_per_sqm_cny)s, %(area_sqm)s,
        %(longitude)s, %(latitude)s
    )
    """
    n = 0
    with db.postgres_connection() as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(sql, {**r, "client_id": client_id})
                n += 1
        conn.commit()
    return {"persisted_count": n}
```

2. Append persist route to `api/domains/customer_data.py`:

```python
from api.customer_data.persistence import persist_run as _persist_run


@router.post(
    "/customer-data/imports/{run_id}/persist",
    status_code=status.HTTP_200_OK,
)
def persist_import(
    run_id: str,
    force: bool = False,
    user: CurrentUser = Depends(require_role("admin", "analyst")),
) -> dict:
    run = staging.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if run.error_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"run has {run.error_count} errors; pass ?force=true to persist anyway",
        )
    if not os.environ.get("POSTGRES_DSN"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="no database configured; set POSTGRES_DSN",
        )
    try:
        result = _persist_run(run.run_id, client_id=user.username)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run vanished")
    return {"runId": run.run_id, **result}
```

3. Append a persist test:

```python
def test_persist_without_postgres_returns_503(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_CUSTOMER_DATA_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    user_store.create_user(username="al", password="hunter22", role="analyst")
    client = TestClient(app)
    _login(client, "al", "hunter22")
    # Stage a good run
    csv_body = (
        "project_name,address,building_no,unit_type,monthly_rent_cny,"
        "occupancy_rate_pct,move_in_date,longitude,latitude\n"
        "Alpha,addr,1,2-1,7800,95,2024-09-01,121.59,31.21\n"
    ).encode("utf-8")
    upload = client.post(
        "/api/v2/customer-data/imports",
        data={"type": "portfolio"},
        files={"file": ("p.csv", csv_body, "text/csv")},
    )
    assert upload.status_code == 201
    run_id = upload.json()["run"]["runId"]
    persist = client.post(f"/api/v2/customer-data/imports/{run_id}/persist")
    assert persist.status_code == 503
    assert "POSTGRES_DSN" in persist.text
```

Note: a true Postgres-write test belongs in an integration suite (skipped if no `POSTGRES_DSN`). For v0.3 we ship the 503-without-DB test only and rely on manual verification with a live Postgres.

4. Run pytest:
```bash
pytest tests/api/test_customer_data_endpoints.py -v
```
Expected: 6 passed.

5. Commit:
```bash
git add api/customer_data/persistence.py api/domains/customer_data.py tests/api/test_customer_data_endpoints.py
git commit -m "$(cat <<'EOF'
feat(customer-data): persist endpoint stages → Postgres (M3)

POST /api/v2/customer-data/imports/{run_id}/persist drains a staged
run into customer_data.{portfolio,pipeline,comp_set}. Portfolio +
pipeline upsert by (client_id, project_name); comp_set is append-
only.

Refuses to persist a run with errors unless ?force=true. Returns
503 when POSTGRES_DSN is absent (matches the 3-mode runtime
contract — staged-only deploys don't have a database to drain to).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task C.3: Read endpoints

**Why:** Downstream features (dashboards, maps) read customer data. v0.3 ships flat list endpoints; filters/pagination are v0.4.

**Files:**
- Modify: `api/domains/customer_data.py` (add 3 read routes)
- Create: `tests/api/test_customer_data_read.py`

**Steps:**

1. Append to `api/domains/customer_data.py`:

```python
@router.get("/customer-data/portfolio", response_model=list[dict])
def list_portfolio(_: CurrentUser = Depends(current_user)) -> list[dict]:
    return _read_table("customer_data.portfolio")


@router.get("/customer-data/pipeline", response_model=list[dict])
def list_pipeline(_: CurrentUser = Depends(current_user)) -> list[dict]:
    return _read_table("customer_data.pipeline")


@router.get("/customer-data/comp_set", response_model=list[dict])
def list_comp_set(_: CurrentUser = Depends(current_user)) -> list[dict]:
    return _read_table("customer_data.comp_set")


def _read_table(qualified_name: str) -> list[dict]:
    if not os.environ.get("POSTGRES_DSN"):
        return []
    from api.persistence import query_rows
    sql = f"SELECT * FROM {qualified_name} ORDER BY imported_at DESC LIMIT 5000"
    return query_rows(sql)
```

> The hardcoded `qualified_name` is safe because it's a closed enum of strings the route module owns; it never sees user input. Use a literal table name string per route to make sqlfluff/static analysis happy.

2. Create `tests/api/test_customer_data_read.py`:

```python
"""Customer-data read endpoint tests (no-DB path)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.auth import storage as user_store


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.delenv("POSTGRES_DSN", raising=False)
    yield


def _seed_login(role="viewer"):
    user_store.create_user(username="r", password="hunter22", role=role)
    client = TestClient(app)
    client.post("/api/auth/login", json={"username": "r", "password": "hunter22"})
    return client


def test_portfolio_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/portfolio")
    assert r.status_code == 200
    assert r.json() == []


def test_pipeline_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/pipeline")
    assert r.status_code == 200
    assert r.json() == []


def test_comp_set_read_no_db_returns_empty():
    client = _seed_login()
    r = client.get("/api/v2/customer-data/comp_set")
    assert r.status_code == 200
    assert r.json() == []
```

3. Run:
```bash
pytest tests/api/test_customer_data_read.py -v
```
Expected: 3 passed.

4. Commit:
```bash
git add api/domains/customer_data.py tests/api/test_customer_data_read.py
git commit -m "$(cat <<'EOF'
feat(customer-data): read endpoints for portfolio/pipeline/comp_set (M3)

GET /api/v2/customer-data/{type} returns up to 5000 rows ordered
by imported_at DESC. Returns [] when no POSTGRES_DSN — matches the
runtime-mode contract (staged-only deploys have no database to
read from).

Filters + pagination deferred to v0.4 alongside the dashboards
that will consume these.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase D: Frontend admin/customer-data page (~1.5 工程日)

### Task D.1: HTML + CSS + JS for the upload page

**Files:**
- Create: `frontend/admin/customer-data.html`
- Create: `frontend/admin/customer-data.css`
- Create: `frontend/admin/customer-data.js`
- Modify: `api/main.py` (route + mount; the existing `/static-admin` mount serves both files)
- Create: `tests/frontend/test_customer_data_helpers.mjs`

**Steps:**

1. Create `frontend/admin/customer-data.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Yieldwise · 客户数据导入</title>
  <link rel="stylesheet" href="/static-admin/customer-data.css">
</head>
<body>
  <header class="cd-topbar">
    <h1>客户数据导入</h1>
    <div class="cd-meta">
      <span data-role="me-name"></span>
      <a class="cd-link" href="/admin/users">用户管理</a>
      <button type="button" data-role="logout">登出</button>
    </div>
  </header>
  <main class="cd-shell">
    <section class="cd-card">
      <h2>下载模板</h2>
      <p class="cd-help">填好后用对应类型上传。CSV 必须带 UTF-8 BOM（Excel 默认即可）和 longitude / latitude 列（GCJ-02）。</p>
      <ul class="cd-templates">
        <li><a href="/api/v2/customer-data/templates/portfolio.csv">portfolio.csv（在管房源）</a></li>
        <li><a href="/api/v2/customer-data/templates/pipeline.csv">pipeline.csv（候选标的）</a></li>
        <li><a href="/api/v2/customer-data/templates/comp_set.csv">comp_set.csv（比准数据）</a></li>
      </ul>
    </section>
    <section class="cd-card">
      <h2>上传</h2>
      <form id="upload-form" class="cd-form" novalidate>
        <label>
          <span>类型</span>
          <select name="type" required>
            <option value="portfolio">portfolio · 在管房源</option>
            <option value="pipeline">pipeline · 候选标的</option>
            <option value="comp_set">comp_set · 比准数据</option>
          </select>
        </label>
        <label>
          <span>CSV 文件</span>
          <input type="file" name="file" accept=".csv,text/csv" required>
        </label>
        <button type="submit">上传并入暂存区</button>
        <p class="cd-error" data-role="upload-error" hidden></p>
      </form>
    </section>
    <section class="cd-card">
      <h2>暂存区</h2>
      <table class="cd-runs">
        <thead><tr><th>Run</th><th>类型</th><th>行数</th><th>错误</th><th>时间</th><th>操作</th></tr></thead>
        <tbody data-role="runs"></tbody>
      </table>
    </section>
    <section class="cd-card cd-errors" hidden data-role="errors-card">
      <h2>错误明细（最近上传）</h2>
      <table class="cd-error-table">
        <thead><tr><th>行</th><th>错误</th></tr></thead>
        <tbody data-role="errors-body"></tbody>
      </table>
    </section>
  </main>
  <script type="module" src="/static-admin/customer-data.js"></script>
</body>
</html>
```

2. Create `frontend/admin/customer-data.css` — copy the `admin.css` palette (dark, accent green) and adapt selectors. Keep concise (~50 lines). Use the same `--bg / --fg / --accent / --border / --card-bg / --error` variables.

```css
:root {
  --bg: #0a0e14;
  --fg: #e5e7eb;
  --accent: #4ade80;
  --error: #f87171;
  --border: rgba(255,255,255,0.08);
  --card-bg: rgba(255,255,255,0.03);
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font-family: ui-sans-serif, system-ui, "PingFang SC", sans-serif; }
.cd-topbar { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); }
.cd-topbar h1 { font-size: 1.25rem; margin: 0; }
.cd-meta { display: flex; gap: 0.75rem; align-items: center; }
.cd-meta button, .cd-link { background: none; color: var(--fg); border: 1px solid var(--border); padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; text-decoration: none; font: inherit; }
.cd-shell { padding: 1.5rem; display: grid; gap: 1.5rem; max-width: 900px; margin: 0 auto; }
.cd-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem; }
.cd-card h2 { margin: 0 0 1rem; font-size: 1rem; opacity: 0.85; }
.cd-help { margin: 0 0 0.75rem; opacity: 0.7; font-size: 0.85rem; }
.cd-templates { padding-left: 1.25rem; line-height: 1.7; font-size: 0.9rem; }
.cd-templates a { color: var(--accent); text-decoration: none; }
.cd-templates a:hover { text-decoration: underline; }
.cd-form { display: grid; gap: 0.75rem; grid-template-columns: 1fr 1fr auto; align-items: end; }
.cd-form label { display: grid; gap: 0.3rem; font-size: 0.8rem; }
.cd-form select, .cd-form input { background: rgba(255,255,255,0.04); color: var(--fg); border: 1px solid var(--border); padding: 0.5rem; border-radius: 4px; font: inherit; }
.cd-form button { background: var(--accent); color: #052e16; border: 0; padding: 0.55rem 1rem; border-radius: 4px; font-weight: 600; cursor: pointer; }
.cd-error { color: var(--error); font-size: 0.85rem; margin: 0.5rem 0 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
th, td { text-align: left; padding: 0.4rem; border-bottom: 1px solid var(--border); }
th { font-weight: 500; opacity: 0.7; }
td button { background: none; color: var(--fg); border: 1px solid var(--border); padding: 0.3rem 0.6rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
td button:hover { background: rgba(255,255,255,0.04); }
```

3. Create `frontend/admin/customer-data.js`:

```javascript
const meEl = document.querySelector('[data-role="me-name"]');
const uploadForm = document.getElementById("upload-form");
const uploadErr = document.querySelector('[data-role="upload-error"]');
const runsBody = document.querySelector('[data-role="runs"]');
const errorsCard = document.querySelector('[data-role="errors-card"]');
const errorsBody = document.querySelector('[data-role="errors-body"]');
const logoutBtn = document.querySelector('[data-role="logout"]');

async function fetchJSON(url, opts = {}) {
  const r = await fetch(url, { credentials: "same-origin", ...opts });
  if (!r.ok) {
    const t = await r.text().catch(() => "");
    throw new Error(`${r.status} ${t}`);
  }
  return r.json();
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

async function loadMe() {
  const me = await fetchJSON("/api/auth/whoami");
  meEl.textContent = `${me.username} (${me.role})`;
  if (me.role === "viewer") {
    uploadForm.querySelector("button[type=submit]").disabled = true;
    uploadErr.textContent = "viewer 角色只读，无法上传";
    uploadErr.hidden = false;
  }
}

async function loadRuns() {
  const runs = await fetchJSON("/api/v2/customer-data/imports");
  runsBody.innerHTML = "";
  for (const run of runs) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHTML(run.runId)}</td>
      <td>${escapeHTML(run.type)}</td>
      <td>${run.rowCount}</td>
      <td>${run.errorCount}</td>
      <td>${escapeHTML(run.createdAt)}</td>
      <td></td>
    `;
    const actions = tr.querySelector("td:last-child");
    actions.appendChild(makePersistBtn(run));
    runsBody.appendChild(tr);
  }
}

function makePersistBtn(run) {
  const btn = document.createElement("button");
  btn.textContent = run.errorCount > 0 ? "持久化（含错误）" : "持久化";
  btn.addEventListener("click", async () => {
    const force = run.errorCount > 0
      ? window.confirm(`这次上传有 ${run.errorCount} 行解析失败。仍然持久化？`)
      : true;
    if (!force) return;
    try {
      const url = `/api/v2/customer-data/imports/${encodeURIComponent(run.runId)}/persist`
        + (run.errorCount > 0 ? "?force=true" : "");
      const result = await fetchJSON(url, { method: "POST" });
      window.alert(`已持久化 ${result.persisted_count} 行`);
    } catch (err) {
      window.alert(`持久化失败: ${err.message}`);
    }
  });
  return btn;
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  uploadErr.hidden = true;
  errorsCard.hidden = true;
  const data = new FormData(uploadForm);
  try {
    const r = await fetch("/api/v2/customer-data/imports", {
      method: "POST",
      credentials: "same-origin",
      body: data,
    });
    if (!r.ok) {
      const t = await r.text();
      uploadErr.textContent = `上传失败 (${r.status}): ${t.slice(0, 200)}`;
      uploadErr.hidden = false;
      return;
    }
    const body = await r.json();
    uploadForm.reset();
    if (body.errorsPreview && body.errorsPreview.length) {
      errorsBody.innerHTML = "";
      for (const e of body.errorsPreview) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${e.row_index}</td><td>${escapeHTML(JSON.stringify(e.error_messages))}</td>`;
        errorsBody.appendChild(tr);
      }
      errorsCard.hidden = false;
    }
    await loadRuns();
  } catch (err) {
    uploadErr.textContent = `网络错误: ${err.message}`;
    uploadErr.hidden = false;
  }
});

logoutBtn.addEventListener("click", async () => {
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
  window.location.href = "/login";
});

(async () => {
  try {
    await loadMe();
    await loadRuns();
  } catch (err) {
    if (err.message.startsWith("401")) {
      window.location.href = "/login";
    } else {
      uploadErr.textContent = `加载失败: ${err.message}`;
      uploadErr.hidden = false;
    }
  }
})();
```

4. Modify `api/main.py` — add a route alongside the existing `/admin/users`:

```python
@app.get("/admin/customer-data")
def serve_admin_customer_data() -> FileResponse:
    return FileResponse(ADMIN_DIR / "customer-data.html")
```

(Place it adjacent to `serve_admin_users()`. The existing `/static-admin` mount already covers `frontend/admin/customer-data.{css,js}` since it serves the directory.)

5. Create `tests/frontend/test_customer_data_helpers.mjs`:

```javascript
import { test } from "node:test";
import assert from "node:assert/strict";

// Mirror of escapeHTML from frontend/admin/customer-data.js
function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

test("escapeHTML escapes XSS-relevant chars", () => {
  assert.equal(escapeHTML("<img src=x onerror=alert(1)>"), "&lt;img src=x onerror=alert(1)&gt;");
  assert.equal(escapeHTML(`"';&`), "&quot;&#39;;&amp;");
});

test("escapeHTML coerces non-strings", () => {
  assert.equal(escapeHTML(42), "42");
  assert.equal(escapeHTML(null), "null");
});

test("escapeHTML round-trips ascii safe", () => {
  assert.equal(escapeHTML("hello world"), "hello world");
  assert.equal(escapeHTML(""), "");
});
```

6. Run + smoke:
```bash
node --check frontend/admin/customer-data.js
node --test tests/frontend/test_customer_data_helpers.mjs
```
Both expected pass.

7. Commit:
```bash
git add frontend/admin/customer-data.* api/main.py tests/frontend/test_customer_data_helpers.mjs
git commit -m "$(cat <<'EOF'
feat(customer-data): admin upload page (M3)

frontend/admin/customer-data.{html,css,js}. Template links + upload
form + staged-runs table + per-run persist button + errors preview.
Vanilla JS, fetch-based, escapeHTML for XSS safety. Viewer role
sees a disabled submit + explanatory message.

Wires GET /admin/customer-data in api/main.py; existing
/static-admin mount serves the new CSS/JS.

3 node:test cases for escapeHTML.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Phase E: Ship checks (~0.5 工程日)

### Task E.1: Update phase1_smoke

**File:** `scripts/phase1_smoke.py`

**Steps:**

1. Add to the authenticated checks block:

```python
            (f"{base}/api/v2/customer-data/templates/portfolio.csv", "project_name,address"),
            (f"{base}/api/v2/customer-data/imports", "[]"),
```

(The first asserts the CSV header; the second asserts the empty-list path.)

2. Run:
```bash
SESSION_SECRET=test python3 scripts/phase1_smoke.py
```
Expected: all checks pass + 2 new ones.

3. Commit:
```bash
git add scripts/phase1_smoke.py
git commit -m "$(cat <<'EOF'
test(smoke): add /api/v2/customer-data checks (M3)

Asserts the CSV template downloads with the right header line
and the empty-runs list serializes correctly.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task E.2: Documentation + README

**Files:**
- Create: `docs/deployment/customer-data-import.md`
- Create: `docs/customer-data-csv-spec.md`
- Modify: `README.md`

**Steps:**

1. Create `docs/customer-data-csv-spec.md` with column-by-column reference:

```markdown
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
```

2. Create `docs/deployment/customer-data-import.md`:

```markdown
# Customer Data Import — Deployment Guide

## Overview

Yieldwise v0.3 imports three customer-supplied data types via CSV: portfolio,
pipeline, comp_set. Uploads land in a staged area (filesystem) first; admin /
analyst then persists into PostgreSQL.

## Environment

| Var | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_DSN` | (none) | Required to persist; read endpoints return [] without it |
| `ATLAS_CUSTOMER_DATA_RUNS_DIR` | `<repo>/tmp/customer-data-runs/` | Staged-run directory |
| `ATLAS_CUSTOMER_DATA_MAX_BYTES` | 10485760 | Per-upload size cap (bytes) |
| `ATLAS_CUSTOMER_DATA_MAX_ROWS` | 50000 | Per-upload row cap (after parse) |

## First-Time Setup

1. Apply DDL (idempotent; the persist endpoint also runs it):
```bash
psql "$POSTGRES_DSN" < db/customer_data.sql
```
2. Visit `/admin/customer-data` as admin or analyst.
3. Download a template, fill it, upload. The staged-run row appears in the
   暂存区 table.
4. Click 持久化 to drain the run into Postgres.

## Run Lifecycle

- Staged runs accumulate under `tmp/customer-data-runs/<run_id>/`.
- Each run owns a self-contained `summary.json` + per-type `*.json` + `errors.json`.
- Persisting a run does NOT delete its staged files — they remain for audit.

## Pruning

`scripts/prune_customer_data_runs.py --older-than-days 30` deletes staged
folders older than the given threshold. Schedule it as a cron / systemd timer.

## Errors

If a run has parse errors, the persist endpoint returns 409 unless called with
`?force=true`. The admin UI prompts before forcing.

## Backup

Postgres `customer_data` schema dumps via `pg_dump --schema=customer_data`.
Staged runs are recreatable from the original CSV — no need to back them up
unless your audit policy requires preserving the upload history.
```

3. Add a Customer Data section to `README.md` after the Auth section:

```markdown
## 客户数据导入 / Customer Data (v0.3 起)

`/admin/customer-data` 让 admin / analyst 上传三类 CSV：在管房源 / 候选标的 / 比准数据。

- 模板下载：`/api/v2/customer-data/templates/{portfolio,pipeline,comp_set}.csv`
- 上传走暂存区（`tmp/customer-data-runs/<run_id>/`），按 run 单独持久化到 Postgres
- 部署细节：`docs/deployment/customer-data-import.md`
- CSV 列规范：`docs/customer-data-csv-spec.md`
```

4. Commit:
```bash
git add docs/deployment/customer-data-import.md docs/customer-data-csv-spec.md README.md
git commit -m "$(cat <<'EOF'
docs(customer-data): deployment + CSV spec + README section (M3)

deployment doc: env vars, first-time setup, run lifecycle, pruning,
errors, backup. csv-spec: column-by-column reference for the three
templates with required + type info. README gains a brief section
pointing at both.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task E.3: Optional pruning helper

**File:** `scripts/prune_customer_data_runs.py`

```python
"""Delete tmp/customer-data-runs/<run_id>/ folders older than a threshold."""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


def runs_dir() -> Path:
    override = os.environ.get("ATLAS_CUSTOMER_DATA_RUNS_DIR")
    return Path(override) if override else Path(__file__).resolve().parents[1] / "tmp" / "customer-data-runs"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--older-than-days", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.older_than_days)
    base = runs_dir()
    if not base.is_dir():
        print(f"runs dir does not exist: {base}")
        return 0
    pruned = 0
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        try:
            mtime = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if mtime < cutoff:
            print(f"{'DRY RUN: ' if args.dry_run else ''}removing {entry.name} (mtime {mtime.isoformat()})")
            if not args.dry_run:
                shutil.rmtree(entry, ignore_errors=True)
            pruned += 1
    print(f"pruned {pruned} runs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Commit:
```bash
git add scripts/prune_customer_data_runs.py
git commit -m "$(cat <<'EOF'
ops(customer-data): pruning script for old staged runs (M3)

scripts/prune_customer_data_runs.py --older-than-days 30
removes staged folders past the threshold. --dry-run for safety.
Schedule as cron / systemd timer.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

### Task E.4: Final regression

```bash
python3 -m compileall -q api jobs scripts
pytest tests/api -x --timeout=30 2>&1 | tail -3
for f in frontend/backstage/{data,lib}/*.js frontend/backstage/app.js frontend/user/modules/*.js frontend/login/login.js frontend/admin/admin.js frontend/admin/customer-data.js; do node --check "$f" || break; done
node --test tests/frontend/*.mjs
SESSION_SECRET=test python3 scripts/phase1_smoke.py
```

All should pass except the 4 known pre-existing failures in `test_drawer_data.mjs` (WIP files we never touch).

---

### Task E.5: Tag

```bash
git tag -a yieldwise-v0.3-import -m "$(cat <<'EOF'
Yieldwise v0.3 Customer Data Import

Plan 3 complete: customer-supplied CSV upload + persist for three
data types.

- DDL: customer_data.{portfolio,pipeline,comp_set,import_errors}
- 3 CSV templates (UTF-8 BOM + ISO dates + GCJ-02 lng/lat)
- Pydantic row models with field-level validation
- CSV parser: row-level error capture, no-fail-whole-batch
- Staged-first: tmp/customer-data-runs/<run_id>/ self-contained
- Persist: upsert (portfolio + pipeline) / append (comp_set);
  refuses errors-laden runs without ?force=true
- Read endpoints: list-up-to-5000-rows for each type (no-DB → [])
- Admin UI at /admin/customer-data (template links + upload + runs
  + per-run persist button + errors preview)
- File size + row count caps via env (10MB / 50000 default)
- Pruning helper script for staged-run rotation

Tests: +26 cases (5 models + 6 parser + 4 staging + 8 endpoints +
3 read).

Smoke: +2 checks (template HTTP, empty runs list).

Next: Plan 4 (M4 Reports + M5 Deployment Package).
EOF
)" HEAD
git push origin yieldwise-v0.3-import
```

---

## Self-Review (writing-plans)

**1. Spec coverage (against §5.1 M3):**

| Spec requirement | Plan 3 task | Status |
|---|---|---|
| Three customer data types | A.1 DDL + B.1 models | ✅ |
| CSV templates downloadable | A.2 + A.3 | ✅ |
| Upload → address resolve → ingest | C.1 + C.2 | ✅ (address resolve = explicit lng/lat in v0.3; geocoding deferred to v0.4) |
| Reuse staged-first pipeline | B.3 staging.py mirrors `tmp/import-runs/` pattern | ✅ |
| Failed rows → import_errors | B.2 parser + DDL `customer_data.import_errors` | ✅ |
| `customer-data` namespace | All paths under `tmp/customer-data-runs/` and `customer_data.*` schema | ✅ |
| v2: REST API for client BI push | (deferred — explicit out-of-scope) | — |

**2. Placeholder scan:** none — every code step shows full code; every command step shows the exact command.

**3. Type consistency:** `CustomerDataType`, `PortfolioRow`, `PipelineRow`, `CompSetRow`, `ROW_MODELS`, `ParseResult`, `parse_csv`, `StagedRun`, `save_run`, `load_run`, `load_run_rows`, `list_runs`, `persist_run`, `_TABLE_FOR`, `_UPSERT_KEY`, `StagedRunSummary`, `ImportResponse`, `_AUTH_REQUIRED` — names are consistent across tasks.

**4. Cross-bundle dependencies (sequential):**
- A.1 → A.2 → A.3 → B.1 → B.2 → B.3 → C.1 → C.2 → C.3 → D.1 → E.1 → E.2 → E.3 → E.4 → E.5
- No tasks can be executed out of order without breaking a downstream import.

**5. Open issues left to subsequent plans:**
- v0.4: address-only geocoding (replace required lng/lat columns)
- v0.4: BI-direct REST API (clients push without using the admin UI)
- v0.4: filters + pagination on read endpoints
- Plan 4 (M5 deploy package): add `db/customer_data.sql` to the offline install bundle
- Plan 5 (M6 backstage pivot): the customer-data tables become the source for new dashboards / ICs / reports

---

## Hand-off

After Plan 3 ships and tags `yieldwise-v0.3-import`, write Plan 4: **M4 Reports + M5 Deployment Package** (~7–10 工程日).
