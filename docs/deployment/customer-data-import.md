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
