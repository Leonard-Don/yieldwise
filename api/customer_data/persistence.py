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
