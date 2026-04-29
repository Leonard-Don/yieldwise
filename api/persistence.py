from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit, urlunsplit

from .mock_data import DISTRICTS
from .provider_adapters import provider_readiness_snapshot


def postgres_dsn() -> str | None:
    value = os.getenv("POSTGRES_DSN", "").strip()
    return value or None


def mask_dsn(dsn: str | None) -> str | None:
    if not dsn:
        return None
    parts = urlsplit(dsn)
    if not parts.hostname:
        return "***"
    user = parts.username or "user"
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{user}:***@{parts.hostname}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def postgres_runtime_status() -> dict[str, Any]:
    dsn = postgres_dsn()
    return {
        "hasPostgresDsn": bool(dsn),
        "postgresDsnMasked": mask_dsn(dsn),
    }


def _load_psycopg():
    try:
        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.json import Jsonb
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("缺少 psycopg，请先安装 api/requirements.txt 里的依赖。") from exc
    return psycopg, dict_row, Jsonb


# Per-DSN connection pool registry. Pools are lazily created on first use and
# kept for the process lifetime — FastAPI keeps a single process per worker, so
# this acts as a long-lived pool without requiring a startup hook.
_POOL_REGISTRY: dict[str, Any] = {}


# T1 (audited 2026-04-29): all DB access routes through this pool.
# Adding direct psycopg.connect() calls bypasses pool sizing and breaks
# multi-user private deploy. See tests/api/test_persistence_pool.py.
def _get_pool(dsn: str) -> Any:
    pool = _POOL_REGISTRY.get(dsn)
    if pool is not None:
        return pool
    try:
        from psycopg_pool import ConnectionPool
    except ImportError as exc:  # pragma: no cover - depends on local env
        raise RuntimeError("缺少 psycopg-pool，请先安装 api/requirements.txt 里的依赖。") from exc
    _, dict_row, _ = _load_psycopg()
    pool = ConnectionPool(
        conninfo=dsn,
        min_size=1,
        max_size=8,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    _POOL_REGISTRY[dsn] = pool
    return pool


@contextmanager
def postgres_connection(*, dsn: str | None = None) -> Iterator[Any]:
    """Acquire a pooled connection. Caller may use it for cursors and explicit commits.

    All callers (read-path cursors and write-path multi-statement transactions)
    route through here so connection lifecycle stays in one place.
    """
    resolved_dsn = dsn or postgres_dsn()
    if not resolved_dsn:
        raise RuntimeError("未配置 POSTGRES_DSN。")
    pool = _get_pool(resolved_dsn)
    with pool.connection() as conn:
        yield conn


@contextmanager
def postgres_cursor(*, dsn: str | None = None) -> Iterator[Any]:
    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            yield cur


def query_rows(sql: str, params: tuple[Any, ...] | list[Any] = (), *, dsn: str | None = None) -> list[dict[str, Any]]:
    with postgres_cursor(dsn=dsn) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def query_row(sql: str, params: tuple[Any, ...] | list[Any] = (), *, dsn: str | None = None) -> dict[str, Any] | None:
    with postgres_cursor(dsn=dsn) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None


def query_value(sql: str, params: tuple[Any, ...] | list[Any] = (), *, dsn: str | None = None) -> Any:
    with postgres_cursor(dsn=dsn) as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        if not row:
            return None
        values = list(row.values()) if isinstance(row, dict) else list(row)
        return values[0] if values else None


def postgres_data_snapshot(*, dsn: str | None = None) -> dict[str, Any]:
    resolved_dsn = dsn or postgres_dsn()
    if not resolved_dsn:
        return {
            "databaseConnected": False,
            "databaseReadable": False,
            "databaseSeeded": False,
            "communityCount": 0,
            "buildingCount": 0,
            "saleListingCount": 0,
            "rentListingCount": 0,
            "floorSnapshotCount": 0,
            "geoAssetCount": 0,
            "cityCoveragePct": 0.0,
            "buildingCoveragePct": 0.0,
            "latestSampleAt": None,
            "latestSuccessfulRunAt": None,
            "latestReferencePersistAt": None,
            "latestImportPersistAt": None,
            "latestGeoPersistAt": None,
            "latestMetricsRefreshAt": None,
            "latestBootstrapAt": None,
        }

    try:
        query_value("SELECT 1", dsn=resolved_dsn)
    except Exception:
        return {
            "databaseConnected": False,
            "databaseReadable": False,
            "databaseSeeded": False,
            "communityCount": 0,
            "buildingCount": 0,
            "saleListingCount": 0,
            "rentListingCount": 0,
            "floorSnapshotCount": 0,
            "geoAssetCount": 0,
            "cityCoveragePct": 0.0,
            "buildingCoveragePct": 0.0,
            "latestSampleAt": None,
            "latestSuccessfulRunAt": None,
            "latestReferencePersistAt": None,
            "latestImportPersistAt": None,
            "latestGeoPersistAt": None,
            "latestMetricsRefreshAt": None,
            "latestBootstrapAt": None,
        }

    try:
        snapshot = query_row(
            """
            SELECT
                (SELECT COUNT(*) FROM communities) AS community_count,
                (SELECT COUNT(*) FROM buildings) AS building_count,
                (SELECT COUNT(*) FROM listings_sale WHERE status = 'active') AS sale_listing_count,
                (SELECT COUNT(*) FROM listings_rent WHERE status = 'active') AS rent_listing_count,
                (SELECT COUNT(*) FROM floor_evidence_snapshots) AS floor_snapshot_count,
                (SELECT COUNT(*) FROM geo_assets WHERE asset_type = 'building_footprint') AS geo_asset_count,
                (
                    SELECT GREATEST(
                        COALESCE(MAX(ls.crawled_at), TIMESTAMPTZ 'epoch'),
                        COALESCE(MAX(lr.crawled_at), TIMESTAMPTZ 'epoch')
                    )
                    FROM listings_sale ls
                    FULL OUTER JOIN listings_rent lr ON FALSE
                ) AS latest_sample_at,
                (SELECT MAX(completed_at) FROM ingestion_runs WHERE status = 'completed') AS latest_successful_run_at,
                (SELECT MAX(completed_at) FROM ingestion_runs WHERE business_scope = 'dictionary' AND status = 'completed') AS latest_reference_persist_at,
                (SELECT MAX(completed_at) FROM ingestion_runs WHERE business_scope = 'sale_rent' AND status = 'completed') AS latest_import_persist_at,
                (SELECT MAX(completed_at) FROM ingestion_runs WHERE business_scope = 'geo_assets' AND status = 'completed') AS latest_geo_persist_at,
                (
                    SELECT GREATEST(
                        COALESCE((SELECT MAX(created_at) FROM metrics_community), TIMESTAMPTZ 'epoch'),
                        COALESCE((SELECT MAX(created_at) FROM metrics_building_floor), TIMESTAMPTZ 'epoch')
                    )
                ) AS latest_metrics_refresh_at,
                (
                    SELECT COUNT(DISTINCT community_id)
                    FROM (
                        SELECT community_id FROM listings_sale WHERE community_id IS NOT NULL AND status = 'active'
                        UNION
                        SELECT community_id FROM listings_rent WHERE community_id IS NOT NULL AND status = 'active'
                    ) AS covered_communities
                ) AS covered_community_count,
                (
                    SELECT COUNT(DISTINCT building_id)
                    FROM geo_assets
                    WHERE asset_type = 'building_footprint' AND building_id IS NOT NULL
                ) AS covered_building_count
            """
        ,
            dsn=resolved_dsn,
        )
    except Exception:
        return {
            "databaseConnected": True,
            "databaseReadable": False,
            "databaseSeeded": False,
            "communityCount": 0,
            "buildingCount": 0,
            "saleListingCount": 0,
            "rentListingCount": 0,
            "floorSnapshotCount": 0,
            "geoAssetCount": 0,
            "cityCoveragePct": 0.0,
            "buildingCoveragePct": 0.0,
            "latestSampleAt": None,
            "latestSuccessfulRunAt": None,
            "latestReferencePersistAt": None,
            "latestImportPersistAt": None,
            "latestGeoPersistAt": None,
            "latestMetricsRefreshAt": None,
            "latestBootstrapAt": None,
        }

    community_count = int(snapshot.get("community_count") or 0)
    building_count = int(snapshot.get("building_count") or 0)
    covered_community_count = int(snapshot.get("covered_community_count") or 0)
    covered_building_count = int(snapshot.get("covered_building_count") or 0)
    database_seeded = community_count > 0 and (
        int(snapshot.get("sale_listing_count") or 0) > 0
        or int(snapshot.get("rent_listing_count") or 0) > 0
        or int(snapshot.get("geo_asset_count") or 0) > 0
    )
    latest_reference_persist_at = snapshot.get("latest_reference_persist_at")
    latest_import_persist_at = snapshot.get("latest_import_persist_at")
    latest_geo_persist_at = snapshot.get("latest_geo_persist_at")
    latest_metrics_refresh_at = snapshot.get("latest_metrics_refresh_at")
    latest_bootstrap_candidates = [
        value
        for value in (
            latest_reference_persist_at,
            latest_import_persist_at,
            latest_geo_persist_at,
            latest_metrics_refresh_at,
        )
        if value not in (None, "")
    ]
    latest_bootstrap_at = None
    if latest_bootstrap_candidates:
        latest_bootstrap_at = max(latest_bootstrap_candidates)
    return {
        "databaseConnected": True,
        "databaseReadable": True,
        "databaseSeeded": database_seeded,
        "communityCount": community_count,
        "buildingCount": building_count,
        "saleListingCount": int(snapshot.get("sale_listing_count") or 0),
        "rentListingCount": int(snapshot.get("rent_listing_count") or 0),
        "floorSnapshotCount": int(snapshot.get("floor_snapshot_count") or 0),
        "geoAssetCount": int(snapshot.get("geo_asset_count") or 0),
        "cityCoveragePct": round(covered_community_count / max(community_count, 1) * 100, 1) if community_count else 0.0,
        "buildingCoveragePct": round(covered_building_count / max(building_count, 1) * 100, 1) if building_count else 0.0,
        "latestSampleAt": snapshot.get("latest_sample_at"),
        "latestSuccessfulRunAt": snapshot.get("latest_successful_run_at"),
        "latestReferencePersistAt": latest_reference_persist_at.isoformat() if hasattr(latest_reference_persist_at, "isoformat") else latest_reference_persist_at,
        "latestImportPersistAt": latest_import_persist_at.isoformat() if hasattr(latest_import_persist_at, "isoformat") else latest_import_persist_at,
        "latestGeoPersistAt": latest_geo_persist_at.isoformat() if hasattr(latest_geo_persist_at, "isoformat") else latest_geo_persist_at,
        "latestMetricsRefreshAt": latest_metrics_refresh_at.isoformat() if hasattr(latest_metrics_refresh_at, "isoformat") else latest_metrics_refresh_at,
        "latestBootstrapAt": latest_bootstrap_at.isoformat() if hasattr(latest_bootstrap_at, "isoformat") else latest_bootstrap_at,
    }


def database_has_real_data(*, dsn: str | None = None) -> bool:
    snapshot = postgres_data_snapshot(dsn=dsn)
    return bool(snapshot.get("databaseSeeded", False))


def _load_service_detail(detail_type: str, run_id: str) -> dict[str, Any] | None:
    if detail_type == "import":
        from .service import import_run_detail_full

        return import_run_detail_full(run_id)
    from .backstage.geo_qa import geo_asset_run_detail_full

    return geo_asset_run_detail_full(run_id)


def _apply_schema_if_needed(cur) -> None:
    schema_path = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
    with schema_path.open("r", encoding="utf-8") as handle:
        statements = handle.read()
    for statement in statements.split(";"):
        sql = statement.strip()
        if sql:
            cur.execute(sql)


def ensure_customer_data_schema(*, dsn: str | None = None) -> None:
    """Apply db/customer_data.sql idempotently. Called by the customer_data
    domain before every persist; cheap because every statement is IF NOT EXISTS."""
    sql_path = Path(__file__).resolve().parent.parent / "db" / "customer_data.sql"
    sql_text = sql_path.read_text(encoding="utf-8")
    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_text)
        conn.commit()


def _upsert_source_providers(cur) -> None:
    for item in provider_readiness_snapshot():
        cur.execute(
            """
            INSERT INTO source_providers (
                provider_id,
                provider_name,
                provider_category,
                acquisition_mode,
                priority_level,
                status,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (provider_id) DO UPDATE
            SET provider_name = EXCLUDED.provider_name,
                provider_category = EXCLUDED.provider_category,
                acquisition_mode = EXCLUDED.acquisition_mode,
                priority_level = EXCLUDED.priority_level,
                status = EXCLUDED.status,
                notes = EXCLUDED.notes,
                updated_at = NOW()
            """,
            (
                item["id"],
                item["name"],
                item["category"],
                item["category"],
                item["priority"],
                item.get("connectionState", "planned"),
                item.get("note") or item.get("role"),
            ),
        )


DISTRICT_NAME_INDEX = {district["id"]: district for district in DISTRICTS}


def _upsert_district_rows(cur, districts: list[dict[str, Any]]) -> None:
    for district in districts:
        cur.execute(
            """
            INSERT INTO districts (district_id, district_name, short_name)
            VALUES (%s, %s, %s)
            ON CONFLICT (district_id) DO UPDATE
            SET district_name = EXCLUDED.district_name,
                short_name = EXCLUDED.short_name,
                updated_at = NOW()
            """,
            (district["district_id"], district["district_name"], district["short_name"]),
        )


def _district_rows_from_catalog(communities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    district_map: dict[str, dict[str, Any]] = {}
    for community in communities:
        district_id = community.get("district_id")
        if not district_id:
            continue
        fallback = DISTRICT_NAME_INDEX.get(district_id, {})
        district_map[district_id] = {
            "district_id": district_id,
            "district_name": community.get("district_name") or fallback.get("name") or district_id,
            "short_name": community.get("district_short_name") or fallback.get("short") or community.get("district_name") or district_id,
        }
    if district_map:
        return list(district_map.values())
    return [
        {
            "district_id": district["id"],
            "district_name": district["name"],
            "short_name": district["short"],
        }
        for district in DISTRICTS
    ]


def _upsert_reference_catalog(cur, Jsonb, communities: list[dict[str, Any]], buildings: list[dict[str, Any]]) -> None:
    for community in communities:
        cur.execute(
            """
            INSERT INTO communities (
                community_id,
                district_id,
                name,
                aliases_json,
                centroid_gcj02,
                source_confidence,
                anchor_source,
                anchor_quality,
                anchor_decision_state,
                latest_anchor_reviewed_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                CASE
                    WHEN %s IS NOT NULL AND %s IS NOT NULL THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    ELSE NULL
                END,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            ON CONFLICT (community_id) DO UPDATE
            SET district_id = EXCLUDED.district_id,
                name = EXCLUDED.name,
                aliases_json = EXCLUDED.aliases_json,
                centroid_gcj02 = COALESCE(EXCLUDED.centroid_gcj02, communities.centroid_gcj02),
                source_confidence = EXCLUDED.source_confidence,
                anchor_source = COALESCE(EXCLUDED.anchor_source, communities.anchor_source),
                anchor_quality = COALESCE(EXCLUDED.anchor_quality, communities.anchor_quality),
                anchor_decision_state = COALESCE(EXCLUDED.anchor_decision_state, communities.anchor_decision_state),
                latest_anchor_reviewed_at = COALESCE(EXCLUDED.latest_anchor_reviewed_at, communities.latest_anchor_reviewed_at),
                updated_at = NOW()
            """,
            (
                community["community_id"],
                community["district_id"],
                community["community_name"],
                Jsonb(sorted({alias for alias in community.get("aliases", []) if alias})),
                community.get("center_lng"),
                community.get("center_lat"),
                community.get("center_lng"),
                community.get("center_lat"),
                float(community.get("source_confidence") or 0.82),
                community.get("anchor_source"),
                community.get("anchor_quality"),
                community.get("anchor_decision_state") or ("confirmed" if community.get("center_lng") not in (None, "") and community.get("center_lat") not in (None, "") else "pending"),
                community.get("latest_anchor_reviewed_at"),
            ),
        )
        for alias in {alias for alias in community.get("aliases", []) if alias and alias != community["community_name"]}:
            cur.execute(
                """
                INSERT INTO community_aliases (community_id, alias_name, alias_source, confidence_score)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (community_id, alias_name) DO UPDATE
                SET alias_source = EXCLUDED.alias_source,
                    confidence_score = EXCLUDED.confidence_score
                """,
                (
                    community["community_id"],
                    alias,
                    community.get("alias_source") or "provider_import",
                    float(community.get("alias_confidence") or 0.88),
                ),
            )

    for building in buildings:
        cur.execute(
            """
            INSERT INTO buildings (building_id, community_id, building_no, total_floors, unit_count, geom_gcj02)
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                CASE
                    WHEN %s IS NOT NULL AND %s IS NOT NULL THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    ELSE NULL
                END
            )
            ON CONFLICT (building_id) DO UPDATE
            SET community_id = EXCLUDED.community_id,
                building_no = EXCLUDED.building_no,
                total_floors = COALESCE(EXCLUDED.total_floors, buildings.total_floors),
                unit_count = COALESCE(EXCLUDED.unit_count, buildings.unit_count),
                geom_gcj02 = COALESCE(EXCLUDED.geom_gcj02, buildings.geom_gcj02),
                updated_at = NOW()
            """,
            (
                building["building_id"],
                building["community_id"],
                building["building_name"],
                building.get("total_floors"),
                building.get("unit_count"),
                building.get("center_lng"),
                building.get("center_lat"),
                building.get("center_lng"),
                building.get("center_lat"),
            ),
        )
        alias_candidates = {building["building_name"], *(building.get("aliases") or [])}
        for alias in {alias for alias in alias_candidates if alias}:
            cur.execute(
                """
                INSERT INTO building_aliases (building_id, alias_name, alias_source, source_ref, confidence_score)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (building_id, alias_name) DO UPDATE
                SET alias_source = EXCLUDED.alias_source,
                    source_ref = EXCLUDED.source_ref,
                    confidence_score = EXCLUDED.confidence_score
                """,
                (
                    building["building_id"],
                    alias,
                    building.get("alias_source") or "provider_import",
                    building.get("source_ref"),
                    float(building.get("alias_confidence") or 0.88),
                ),
            )


def _collect_reference_catalog_from_import_detail(detail: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    community_map: dict[str, dict[str, Any]] = {}
    building_map: dict[str, dict[str, Any]] = {}

    for row in [*detail.get("saleIndex", {}).values(), *detail.get("rentIndex", {}).values()]:
        community_id = row.get("community_id")
        building_id = row.get("building_id")
        district_id = row.get("district_id")
        community_name = row.get("resolved_community_name") or row.get("raw_community_name")
        building_name = row.get("resolved_building_name") or row.get("raw_building_text")
        district_name = row.get("resolved_district_name")
        if community_id and district_id and community_name:
            entry = community_map.setdefault(
                community_id,
                {
                    "community_id": community_id,
                    "district_id": district_id,
                    "community_name": community_name,
                    "aliases": [],
                    "source_confidence": max(float(row.get("resolution_confidence") or 0.82), 0.7),
                },
            )
            for alias in {community_name, row.get("raw_community_name")}:
                if alias and alias not in entry["aliases"]:
                    entry["aliases"].append(alias)
            if district_name and "district_name" not in entry:
                entry["district_name"] = district_name

        if building_id and community_id and building_name:
            entry = building_map.setdefault(
                building_id,
                {
                    "building_id": building_id,
                    "community_id": community_id,
                    "building_name": building_name,
                    "total_floors": row.get("total_floors"),
                    "aliases": [],
                    "source_ref": row.get("source_listing_id"),
                },
            )
            if row.get("total_floors") and not entry.get("total_floors"):
                entry["total_floors"] = row.get("total_floors")
            for alias in {building_name, row.get("raw_building_text")}:
                if alias and alias not in entry["aliases"]:
                    entry["aliases"].append(alias)

    for queue_row in detail.get("queueRows", []):
        community_id = queue_row.get("parsed_community_id")
        building_id = queue_row.get("parsed_building_id")
        if community_id and community_id in community_map and queue_row.get("raw_text"):
            raw_text = str(queue_row["raw_text"])
            if raw_text not in community_map[community_id]["aliases"]:
                community_map[community_id]["aliases"].append(raw_text)
        if building_id and building_id in building_map and queue_row.get("raw_text"):
            raw_text = str(queue_row["raw_text"])
            if raw_text not in building_map[building_id]["aliases"]:
                building_map[building_id]["aliases"].append(raw_text)

    return list(community_map.values()), list(building_map.values())


def _collect_reference_catalog_from_geo_detail(detail: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    community_map: dict[str, dict[str, Any]] = {}
    building_map: dict[str, dict[str, Any]] = {}
    for feature in detail.get("features", []):
        properties = feature.get("properties") or {}
        community_id = properties.get("community_id")
        building_id = properties.get("building_id")
        district_id = properties.get("district_id")
        community_name = properties.get("community_name")
        building_name = properties.get("building_name")
        if community_id and district_id and community_name:
            entry = community_map.setdefault(
                community_id,
                {
                    "community_id": community_id,
                    "district_id": district_id,
                    "community_name": community_name,
                    "aliases": [community_name],
                    "source_confidence": 0.9,
                },
            )
            if properties.get("source_ref") and properties["source_ref"] not in entry["aliases"]:
                entry["aliases"].append(properties["source_ref"])
        if building_id and community_id and building_name:
            entry = building_map.setdefault(
                building_id,
                {
                    "building_id": building_id,
                    "community_id": community_id,
                    "building_name": building_name,
                    "total_floors": properties.get("total_floors"),
                    "aliases": [building_name],
                    "source_ref": properties.get("source_ref"),
                    "alias_source": detail.get("providerId"),
                    "alias_confidence": 0.92,
                },
            )
            for alias in {properties.get("source_ref"), properties.get("name"), properties.get("building_no")}:
                if alias and alias not in entry["aliases"]:
                    entry["aliases"].append(alias)
    return list(community_map.values()), list(building_map.values())


def _upsert_ingestion_run(cur, Jsonb, detail: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO ingestion_runs (
            external_run_id,
            provider_id,
            batch_name,
            acquisition_mode,
            business_scope,
            status,
            sale_input_file,
            rent_input_file,
            output_manifest_path,
            summary_json,
            created_at,
            completed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_run_id) DO UPDATE
        SET provider_id = EXCLUDED.provider_id,
            batch_name = EXCLUDED.batch_name,
            status = EXCLUDED.status,
            sale_input_file = EXCLUDED.sale_input_file,
            rent_input_file = EXCLUDED.rent_input_file,
            output_manifest_path = EXCLUDED.output_manifest_path,
            summary_json = EXCLUDED.summary_json,
            completed_at = EXCLUDED.completed_at
        RETURNING run_id
        """,
        (
            detail["runId"],
            detail["providerId"],
            detail["batchName"],
            "authorized_import",
            "sale_rent",
            "completed",
            detail["manifest"].get("inputs", {}).get("sale_file"),
            detail["manifest"].get("inputs", {}).get("rent_file"),
            str(detail["manifestPath"]),
            Jsonb(detail["manifest"].get("summary", {})),
            detail["createdAt"],
            detail["createdAt"],
        ),
    )
    row = cur.fetchone()
    return int(row[0])


def _upsert_geo_asset_run(cur, Jsonb, detail: dict[str, Any]) -> int:
    cur.execute(
        """
        INSERT INTO ingestion_runs (
            external_run_id,
            provider_id,
            batch_name,
            acquisition_mode,
            business_scope,
            status,
            output_manifest_path,
            summary_json,
            created_at,
            completed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_run_id) DO UPDATE
        SET provider_id = EXCLUDED.provider_id,
            batch_name = EXCLUDED.batch_name,
            acquisition_mode = EXCLUDED.acquisition_mode,
            business_scope = EXCLUDED.business_scope,
            status = EXCLUDED.status,
            output_manifest_path = EXCLUDED.output_manifest_path,
            summary_json = EXCLUDED.summary_json,
            completed_at = EXCLUDED.completed_at
        RETURNING run_id
        """,
        (
            detail["runId"],
            detail["providerId"],
            detail["batchName"],
            "authorized_import",
            "geo_assets",
            "completed",
            str(detail["manifestPath"]),
            Jsonb(detail.get("summary", {})),
            detail["createdAt"],
            detail["createdAt"],
        ),
    )
    row = cur.fetchone()
    return int(row[0])


def _upsert_reference_dictionary_run(cur, Jsonb, manifest: dict[str, Any], manifest_path: Path) -> int:
    cur.execute(
        """
        INSERT INTO ingestion_runs (
            external_run_id,
            provider_id,
            batch_name,
            acquisition_mode,
            business_scope,
            status,
            output_manifest_path,
            summary_json,
            created_at,
            completed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (external_run_id) DO UPDATE
        SET provider_id = EXCLUDED.provider_id,
            batch_name = EXCLUDED.batch_name,
            acquisition_mode = EXCLUDED.acquisition_mode,
            business_scope = EXCLUDED.business_scope,
            status = EXCLUDED.status,
            output_manifest_path = EXCLUDED.output_manifest_path,
            summary_json = EXCLUDED.summary_json,
            completed_at = EXCLUDED.completed_at
        RETURNING run_id
        """,
        (
            manifest["run_id"],
            manifest.get("provider_id"),
            manifest.get("batch_name") or manifest["run_id"],
            "authorized_import",
            "dictionary",
            "completed",
            str(manifest_path),
            Jsonb(manifest.get("summary", {})),
            manifest.get("created_at"),
            manifest.get("created_at"),
        ),
    )
    row = cur.fetchone()
    return int(row[0])


def _upsert_raw_listing(cur, Jsonb, run_pk: int, row: dict[str, Any], *, business_type: str) -> None:
    table = "raw_listings_sale" if business_type == "sale" else "raw_listings_rent"
    cur.execute(
        f"""
        INSERT INTO {table} (
            ingestion_run_id,
            source,
            source_listing_id,
            url,
            raw_payload_json
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source, source_listing_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            url = EXCLUDED.url,
            raw_payload_json = EXCLUDED.raw_payload_json,
            crawled_at = NOW()
        """,
        (
            run_pk,
            row.get("source"),
            row.get("source_listing_id"),
            row.get("url"),
            Jsonb(row.get("raw_row") or {}),
        ),
    )


def _upsert_listing(cur, Jsonb, run_pk: int, row: dict[str, Any], *, business_type: str) -> None:
    table = "listings_sale" if business_type == "sale" else "listings_rent"
    price_column = "price_total_wan, unit_price_yuan" if business_type == "sale" else "monthly_rent"
    price_placeholders = "%s, %s" if business_type == "sale" else "%s"
    update_columns = (
        "price_total_wan = EXCLUDED.price_total_wan, unit_price_yuan = EXCLUDED.unit_price_yuan"
        if business_type == "sale"
        else "monthly_rent = EXCLUDED.monthly_rent"
    )
    price_values = (
        (row.get("price_total_wan"), row.get("unit_price_yuan"))
        if business_type == "sale"
        else (row.get("monthly_rent"),)
    )
    cur.execute(
        f"""
        INSERT INTO {table} (
            ingestion_run_id,
            source,
            source_listing_id,
            community_id,
            building_id,
            raw_community_name,
            raw_address,
            raw_building_text,
            floor_no,
            total_floors,
            floor_bucket,
            area_sqm,
            bedrooms,
            living_rooms,
            bathrooms,
            orientation,
            decoration,
            {price_column},
            published_at,
            status,
            raw_payload_json
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            {price_placeholders}, %s, %s, %s
        )
        ON CONFLICT (source, source_listing_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            community_id = EXCLUDED.community_id,
            building_id = EXCLUDED.building_id,
            raw_community_name = EXCLUDED.raw_community_name,
            raw_address = EXCLUDED.raw_address,
            raw_building_text = EXCLUDED.raw_building_text,
            floor_no = EXCLUDED.floor_no,
            total_floors = EXCLUDED.total_floors,
            floor_bucket = EXCLUDED.floor_bucket,
            area_sqm = EXCLUDED.area_sqm,
            bedrooms = EXCLUDED.bedrooms,
            living_rooms = EXCLUDED.living_rooms,
            bathrooms = EXCLUDED.bathrooms,
            orientation = EXCLUDED.orientation,
            decoration = EXCLUDED.decoration,
            {update_columns},
            published_at = EXCLUDED.published_at,
            status = EXCLUDED.status,
            raw_payload_json = EXCLUDED.raw_payload_json,
            crawled_at = NOW()
        """,
        (
            run_pk,
            row.get("source"),
            row.get("source_listing_id"),
            row.get("community_id"),
            row.get("building_id"),
            row.get("raw_community_name"),
            row.get("raw_address"),
            row.get("raw_building_text"),
            row.get("floor_no"),
            row.get("total_floors"),
            row.get("floor_bucket"),
            row.get("area_sqm"),
            row.get("bedrooms"),
            row.get("living_rooms"),
            row.get("bathrooms"),
            row.get("orientation"),
            row.get("decoration"),
            *price_values,
            row.get("published_at"),
            row.get("parse_status", "active"),
            Jsonb(row),
        ),
    )


def _upsert_queue_item(cur, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO address_resolution_queue (
            ingestion_run_id,
            source,
            source_listing_id,
            raw_text,
            parsed_district_id,
            parsed_community_id,
            parsed_building_id,
            parsed_unit,
            parsed_floor_no,
            parse_status,
            confidence_score,
            resolution_notes,
            review_owner,
            reviewed_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (source, source_listing_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            raw_text = EXCLUDED.raw_text,
            parsed_district_id = EXCLUDED.parsed_district_id,
            parsed_community_id = EXCLUDED.parsed_community_id,
            parsed_building_id = EXCLUDED.parsed_building_id,
            parsed_unit = EXCLUDED.parsed_unit,
            parsed_floor_no = EXCLUDED.parsed_floor_no,
            parse_status = EXCLUDED.parse_status,
            confidence_score = EXCLUDED.confidence_score,
            resolution_notes = EXCLUDED.resolution_notes,
            review_owner = EXCLUDED.review_owner,
            reviewed_at = EXCLUDED.reviewed_at,
            updated_at = NOW()
        """,
        (
            run_pk,
            item.get("source"),
            item.get("source_listing_id"),
            item.get("raw_text"),
            item.get("parsed_district_id"),
            item.get("parsed_community_id"),
            item.get("parsed_building_id"),
            item.get("parsed_unit"),
            item.get("parsed_floor_no"),
            item.get("parse_status"),
            item.get("confidence_score"),
            item.get("resolution_notes"),
            item.get("review_owner"),
            item.get("reviewed_at"),
        ),
    )


def _insert_review_event(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO address_review_events (
            event_id,
            ingestion_run_id,
            queue_id,
            source,
            source_listing_id,
            parsed_community_id,
            parsed_building_id,
            floor_no,
            previous_status,
            new_status,
            resolution_notes,
            review_owner,
            reviewed_at,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (
            item.get("eventId"),
            run_pk,
            item.get("queueId"),
            item.get("sourceId"),
            item.get("sourceListingId"),
            item.get("communityId"),
            item.get("buildingId"),
            item.get("floorNo"),
            item.get("previousStatus"),
            item.get("newStatus"),
            item.get("resolutionNotes"),
            item.get("reviewOwner"),
            item.get("reviewedAt"),
            Jsonb(item),
        ),
    )


def _upsert_floor_pair(cur, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO floor_evidence_pairs (
            pair_id,
            ingestion_run_id,
            community_id,
            building_id,
            floor_no,
            sale_source,
            sale_source_listing_id,
            rent_source,
            rent_source_listing_id,
            sale_price_wan,
            monthly_rent,
            annual_yield_pct,
            area_gap_sqm,
            floor_gap,
            match_confidence,
            normalized_address
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (pair_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            community_id = EXCLUDED.community_id,
            building_id = EXCLUDED.building_id,
            floor_no = EXCLUDED.floor_no,
            sale_source = EXCLUDED.sale_source,
            sale_source_listing_id = EXCLUDED.sale_source_listing_id,
            rent_source = EXCLUDED.rent_source,
            rent_source_listing_id = EXCLUDED.rent_source_listing_id,
            sale_price_wan = EXCLUDED.sale_price_wan,
            monthly_rent = EXCLUDED.monthly_rent,
            annual_yield_pct = EXCLUDED.annual_yield_pct,
            area_gap_sqm = EXCLUDED.area_gap_sqm,
            floor_gap = EXCLUDED.floor_gap,
            match_confidence = EXCLUDED.match_confidence,
            normalized_address = EXCLUDED.normalized_address
        """,
        (
            item.get("pair_id"),
            run_pk,
            item.get("community_id"),
            item.get("building_id"),
            item.get("floor_no"),
            item.get("sale_source"),
            item.get("sale_source_listing_id"),
            item.get("rent_source"),
            item.get("rent_source_listing_id"),
            item.get("sale_price_wan"),
            item.get("monthly_rent"),
            item.get("annual_yield_pct"),
            item.get("area_gap_sqm"),
            item.get("floor_gap"),
            item.get("match_confidence"),
            item.get("normalized_address"),
        ),
    )


def _upsert_floor_snapshot(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO floor_evidence_snapshots (
            ingestion_run_id,
            community_id,
            building_id,
            floor_no,
            pair_count,
            sale_median_wan,
            rent_median_monthly,
            yield_pct,
            best_pair_confidence,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ingestion_run_id, building_id, floor_no) DO UPDATE
        SET community_id = EXCLUDED.community_id,
            pair_count = EXCLUDED.pair_count,
            sale_median_wan = EXCLUDED.sale_median_wan,
            rent_median_monthly = EXCLUDED.rent_median_monthly,
            yield_pct = EXCLUDED.yield_pct,
            best_pair_confidence = EXCLUDED.best_pair_confidence,
            payload_json = EXCLUDED.payload_json
        """,
        (
            run_pk,
            item.get("community_id"),
            item.get("building_id"),
            item.get("floor_no"),
            item.get("pair_count"),
            item.get("sale_median_wan"),
            item.get("rent_median_monthly"),
            item.get("yield_pct"),
            item.get("best_pair_confidence"),
            Jsonb(item),
        ),
    )


def _upsert_geo_asset(cur, Jsonb, run_pk: int, feature: dict[str, Any], *, provider_id: str, created_at: str | None) -> None:
    properties = feature.get("properties", {})
    geometry = feature.get("geometry") or {}
    geometry_json = Jsonb(geometry)
    cur.execute(
        """
        INSERT INTO geo_assets (
            ingestion_run_id,
            asset_type,
            provider_id,
            district_id,
            community_id,
            building_id,
            source_ref,
            geom_wgs84,
            payload_json,
            captured_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            CASE
                WHEN %s::jsonb ? 'type' THEN ST_SetSRID(ST_GeomFromGeoJSON(%s::json), 4326)
                ELSE NULL
            END,
            %s,
            %s
        )
        ON CONFLICT (ingestion_run_id, asset_type, building_id, source_ref) DO UPDATE
        SET provider_id = EXCLUDED.provider_id,
            district_id = EXCLUDED.district_id,
            community_id = EXCLUDED.community_id,
            geom_wgs84 = EXCLUDED.geom_wgs84,
            payload_json = EXCLUDED.payload_json,
            captured_at = EXCLUDED.captured_at
        """,
        (
            run_pk,
            "building_footprint",
            provider_id,
            properties.get("district_id"),
            properties.get("community_id"),
            properties.get("building_id"),
            properties.get("source_ref"),
            geometry_json,
            json.dumps(geometry, ensure_ascii=False),
            Jsonb(feature),
            properties.get("captured_at") or created_at,
        ),
    )
    if properties.get("building_id"):
        cur.execute(
            """
            UPDATE buildings
            SET geom_wgs84 = COALESCE(
                    CASE
                        WHEN %s::jsonb ? 'type' THEN ST_SetSRID(ST_GeomFromGeoJSON(%s::json), 4326)
                        ELSE NULL
                    END,
                    buildings.geom_wgs84
                ),
                updated_at = NOW()
            WHERE building_id = %s
            """,
            (
                geometry_json,
                json.dumps(geometry, ensure_ascii=False),
                properties.get("building_id"),
            ),
        )
    if properties.get("community_id"):
        cur.execute(
            """
            UPDATE communities
            SET centroid_wgs84 = COALESCE(
                    centroid_wgs84,
                    CASE
                        WHEN %s::jsonb ? 'type' THEN ST_Centroid(ST_SetSRID(ST_GeomFromGeoJSON(%s::json), 4326))
                        ELSE NULL
                    END
                ),
                updated_at = NOW()
            WHERE community_id = %s
            """,
            (
                geometry_json,
                json.dumps(geometry, ensure_ascii=False),
                properties.get("community_id"),
            ),
        )


def _upsert_geo_asset_task(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO geo_asset_capture_tasks (
            task_id,
            ingestion_run_id,
            provider_id,
            task_scope,
            status,
            priority,
            district_id,
            community_id,
            building_id,
            source_ref,
            community_name,
            building_name,
            resolution_notes,
            review_owner,
            reviewed_at,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (task_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            provider_id = EXCLUDED.provider_id,
            task_scope = EXCLUDED.task_scope,
            status = EXCLUDED.status,
            priority = EXCLUDED.priority,
            district_id = EXCLUDED.district_id,
            community_id = EXCLUDED.community_id,
            building_id = EXCLUDED.building_id,
            source_ref = EXCLUDED.source_ref,
            community_name = EXCLUDED.community_name,
            building_name = EXCLUDED.building_name,
            resolution_notes = EXCLUDED.resolution_notes,
            review_owner = EXCLUDED.review_owner,
            reviewed_at = EXCLUDED.reviewed_at,
            payload_json = EXCLUDED.payload_json,
            updated_at = NOW()
        """,
        (
            item.get("task_id"),
            run_pk,
            item.get("provider_id"),
            item.get("task_scope"),
            item.get("status"),
            item.get("priority"),
            item.get("district_id"),
            item.get("community_id"),
            item.get("building_id"),
            item.get("source_ref"),
            item.get("community_name"),
            item.get("building_name"),
            item.get("resolution_notes"),
            item.get("review_owner"),
            item.get("reviewed_at"),
            Jsonb(item),
        ),
    )


def _insert_geo_asset_review_event(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO geo_asset_review_events (
            event_id,
            ingestion_run_id,
            task_id,
            task_scope,
            previous_status,
            new_status,
            review_owner,
            reviewed_at,
            resolution_notes,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (
            item.get("eventId") or item.get("event_id"),
            run_pk,
            item.get("taskId") or item.get("task_id"),
            item.get("taskScope") or item.get("task_scope"),
            item.get("previousStatus") or item.get("previous_status"),
            item.get("newStatus") or item.get("new_status"),
            item.get("reviewOwner") or item.get("review_owner"),
            item.get("reviewedAt") or item.get("reviewed_at"),
            item.get("resolutionNotes") or item.get("resolution_notes"),
            Jsonb(item),
        ),
    )


def _upsert_geo_capture_work_order(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO geo_capture_work_orders (
            work_order_id,
            ingestion_run_id,
            provider_id,
            status,
            district_id,
            community_id,
            building_id,
            title,
            assignee,
            task_ids_json,
            task_count,
            primary_task_id,
            focus_floor_no,
            focus_yield_pct,
            watchlist_hits,
            impact_score,
            impact_band,
            notes,
            due_at,
            created_by,
            payload_json,
            created_at,
            updated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (work_order_id) DO UPDATE
        SET ingestion_run_id = EXCLUDED.ingestion_run_id,
            provider_id = EXCLUDED.provider_id,
            status = EXCLUDED.status,
            district_id = EXCLUDED.district_id,
            community_id = EXCLUDED.community_id,
            building_id = EXCLUDED.building_id,
            title = EXCLUDED.title,
            assignee = EXCLUDED.assignee,
            task_ids_json = EXCLUDED.task_ids_json,
            task_count = EXCLUDED.task_count,
            primary_task_id = EXCLUDED.primary_task_id,
            focus_floor_no = EXCLUDED.focus_floor_no,
            focus_yield_pct = EXCLUDED.focus_yield_pct,
            watchlist_hits = EXCLUDED.watchlist_hits,
            impact_score = EXCLUDED.impact_score,
            impact_band = EXCLUDED.impact_band,
            notes = EXCLUDED.notes,
            due_at = EXCLUDED.due_at,
            created_by = EXCLUDED.created_by,
            payload_json = EXCLUDED.payload_json,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at
        """,
        (
            item.get("work_order_id") or item.get("workOrderId"),
            run_pk,
            item.get("provider_id") or item.get("providerId"),
            item.get("status"),
            item.get("district_id") or item.get("districtId"),
            item.get("community_id") or item.get("communityId"),
            item.get("building_id") or item.get("buildingId"),
            item.get("title"),
            item.get("assignee"),
            Jsonb(item.get("task_ids") or item.get("taskIds") or []),
            item.get("task_count") or item.get("taskCount") or 0,
            item.get("primary_task_id") or item.get("primaryTaskId"),
            item.get("focus_floor_no") or item.get("focusFloorNo"),
            item.get("focus_yield_pct") or item.get("focusYieldPct"),
            item.get("watchlist_hits") or item.get("watchlistHits") or 0,
            item.get("impact_score") or item.get("impactScore"),
            item.get("impact_band") or item.get("impactBand"),
            item.get("notes"),
            item.get("due_at") or item.get("dueAt"),
            item.get("created_by") or item.get("createdBy"),
            Jsonb(item),
            item.get("created_at") or item.get("createdAt"),
            item.get("updated_at") or item.get("updatedAt") or item.get("created_at") or item.get("createdAt"),
        ),
    )


def _insert_geo_capture_work_order_event(cur, Jsonb, run_pk: int, item: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO geo_capture_work_order_events (
            event_id,
            ingestion_run_id,
            work_order_id,
            previous_status,
            new_status,
            changed_by,
            changed_at,
            notes,
            payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id) DO NOTHING
        """,
        (
            item.get("eventId") or item.get("event_id"),
            run_pk,
            item.get("workOrderId") or item.get("work_order_id"),
            item.get("previousStatus") or item.get("previous_status"),
            item.get("newStatus") or item.get("new_status"),
            item.get("changedBy") or item.get("changed_by"),
            item.get("changedAt") or item.get("changed_at"),
            item.get("notes"),
            Jsonb(item),
        ),
    )


def sync_anchor_confirmation_to_postgres(
    payload: dict[str, Any],
    *,
    dsn: str | None = None,
    apply_schema: bool = False,
) -> dict[str, Any]:
    resolved_dsn = dsn or postgres_dsn()
    if not resolved_dsn:
        raise RuntimeError("未配置 POSTGRES_DSN。")
    psycopg, _, Jsonb = _load_psycopg()
    community_row = payload.get("communityRow") or {}
    community_id = community_row.get("community_id") or payload.get("communityId")
    if not community_id:
        raise RuntimeError("缺少 community_id，无法同步锚点确认。")
    district_id = community_row.get("district_id") or payload.get("districtId")
    district_name = community_row.get("district_name") or payload.get("districtName") or district_id
    if not district_id:
        raise RuntimeError("缺少 district_id，无法同步锚点确认。")

    with postgres_connection(dsn=resolved_dsn) as conn:
        with conn.cursor() as cur:
            if apply_schema:
                _apply_schema_if_needed(cur)
            _upsert_source_providers(cur)
            _upsert_district_rows(
                cur,
                [
                    {
                        "district_id": district_id,
                        "district_name": district_name,
                        "short_name": district_name[:2] if district_name else district_id,
                    }
                ],
            )
            aliases = sorted({alias for alias in (payload.get("communityAliases") or community_row.get("aliases") or []) if alias})
            center_lng = community_row.get("center_lng")
            center_lat = community_row.get("center_lat")
            cur.execute(
                """
                INSERT INTO communities (
                    community_id,
                    district_id,
                    name,
                    aliases_json,
                    centroid_gcj02,
                    source_confidence,
                    anchor_source,
                    anchor_quality,
                    anchor_decision_state,
                    latest_anchor_reviewed_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    CASE
                        WHEN %s IS NOT NULL AND %s IS NOT NULL THEN ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                        ELSE NULL
                    END,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (community_id) DO UPDATE
                SET district_id = EXCLUDED.district_id,
                    name = EXCLUDED.name,
                    aliases_json = EXCLUDED.aliases_json,
                    centroid_gcj02 = COALESCE(EXCLUDED.centroid_gcj02, communities.centroid_gcj02),
                    source_confidence = COALESCE(EXCLUDED.source_confidence, communities.source_confidence),
                    anchor_source = COALESCE(EXCLUDED.anchor_source, communities.anchor_source),
                    anchor_quality = COALESCE(EXCLUDED.anchor_quality, communities.anchor_quality),
                    anchor_decision_state = COALESCE(EXCLUDED.anchor_decision_state, communities.anchor_decision_state),
                    latest_anchor_reviewed_at = COALESCE(EXCLUDED.latest_anchor_reviewed_at, communities.latest_anchor_reviewed_at),
                    updated_at = NOW()
                """,
                (
                    community_id,
                    district_id,
                    community_row.get("community_name") or payload.get("communityName") or community_id,
                    Jsonb(aliases),
                    center_lng,
                    center_lat,
                    center_lng,
                    center_lat,
                    float(community_row.get("source_confidence") or payload.get("anchorQuality") or 0.95),
                    community_row.get("anchor_source") or payload.get("anchorSource"),
                    community_row.get("anchor_quality") or payload.get("anchorQuality"),
                    payload.get("decisionState") or community_row.get("anchor_decision_state") or "confirmed",
                    payload.get("reviewedAt"),
                ),
            )
            for alias in aliases:
                if alias == (community_row.get("community_name") or payload.get("communityName")):
                    continue
                cur.execute(
                    """
                    INSERT INTO community_aliases (community_id, alias_name, alias_source, confidence_score)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (community_id, alias_name) DO UPDATE
                    SET alias_source = EXCLUDED.alias_source,
                        confidence_score = EXCLUDED.confidence_score
                    """,
                    (
                        community_id,
                        alias,
                        "anchor_confirmation",
                        float(community_row.get("source_confidence") or payload.get("anchorQuality") or 0.96),
                    ),
                )
            cur.execute(
                """
                INSERT INTO anchor_review_events (
                    event_id,
                    community_id,
                    district_id,
                    reference_run_id,
                    action,
                    decision_state,
                    candidate_index,
                    previous_center_lng,
                    previous_center_lat,
                    center_lng,
                    center_lat,
                    anchor_source,
                    anchor_quality,
                    review_note,
                    alias_appended,
                    review_owner,
                    reviewed_at,
                    payload_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    payload.get("eventId"),
                    community_id,
                    district_id,
                    payload.get("referenceRunId"),
                    payload.get("action"),
                    payload.get("decisionState"),
                    payload.get("candidateIndex"),
                    payload.get("previousCenterLng"),
                    payload.get("previousCenterLat"),
                    payload.get("centerLng"),
                    payload.get("centerLat"),
                    payload.get("anchorSource"),
                    payload.get("anchorQuality"),
                    payload.get("reviewNote"),
                    payload.get("aliasAppended"),
                    payload.get("reviewOwner") or "atlas-ui",
                    payload.get("reviewedAt"),
                    Jsonb(payload),
                ),
            )
        conn.commit()
    return {
        "communityId": community_id,
        "districtId": district_id,
        "aliasCount": len(aliases),
        "reviewedAt": payload.get("reviewedAt"),
    }


def persist_import_run_to_postgres(run_id: str, *, dsn: str | None = None, apply_schema: bool = False) -> dict[str, Any]:
    detail = _load_service_detail("import", run_id)
    if not detail:
        raise KeyError(f"Import run not found: {run_id}")

    dsn = dsn or postgres_dsn()
    if not dsn:
        raise RuntimeError("未配置 POSTGRES_DSN，无法写入 PostgreSQL。")

    psycopg, dict_row, Jsonb = _load_psycopg()
    sale_rows = list(detail["saleIndex"].values())
    rent_rows = list(detail["rentIndex"].values())
    queue_rows = list(detail["queueRows"])
    review_history = list(detail["reviewHistory"])
    floor_pairs = list(detail["floorPairs"])
    floor_evidence = list(detail["floorEvidence"])
    communities, buildings = _collect_reference_catalog_from_import_detail(detail)
    district_rows = _district_rows_from_catalog(communities)

    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            if apply_schema:
                _apply_schema_if_needed(cur)
            _upsert_source_providers(cur)
            _upsert_district_rows(cur, district_rows)
            _upsert_reference_catalog(cur, Jsonb, communities, buildings)
            run_pk = _upsert_ingestion_run(cur, Jsonb, detail)
            for row in sale_rows:
                _upsert_raw_listing(cur, Jsonb, run_pk, row, business_type="sale")
                _upsert_listing(cur, Jsonb, run_pk, row, business_type="sale")
            for row in rent_rows:
                _upsert_raw_listing(cur, Jsonb, run_pk, row, business_type="rent")
                _upsert_listing(cur, Jsonb, run_pk, row, business_type="rent")
            for item in queue_rows:
                _upsert_queue_item(cur, run_pk, item)
            for item in review_history:
                _insert_review_event(cur, Jsonb, run_pk, item)
            for item in floor_pairs:
                _upsert_floor_pair(cur, run_pk, item)
            for item in floor_evidence:
                _upsert_floor_snapshot(cur, Jsonb, run_pk, item)
        conn.commit()

    return {
        "runId": run_id,
        "ingestionRunId": run_pk,
        "saleUpserts": len(sale_rows),
        "rentUpserts": len(rent_rows),
        "queueUpserts": len(queue_rows),
        "reviewEventInserts": len(review_history),
        "pairUpserts": len(floor_pairs),
        "snapshotUpserts": len(floor_evidence),
        "postgresDsnMasked": mask_dsn(dsn),
    }


def persist_geo_asset_run_to_postgres(run_id: str, *, dsn: str | None = None, apply_schema: bool = False) -> dict[str, Any]:
    detail = _load_service_detail("geo", run_id)
    if not detail:
        raise KeyError(f"Geo asset run not found: {run_id}")

    dsn = dsn or postgres_dsn()
    if not dsn:
        raise RuntimeError("未配置 POSTGRES_DSN，无法写入 PostgreSQL。")

    psycopg, dict_row, Jsonb = _load_psycopg()
    features = list(detail.get("features", []))
    coverage_tasks = list(detail.get("coverageTaskRows", []))
    review_history = list(detail.get("reviewHistoryRows", []))
    work_orders = list(detail.get("workOrderRows", []))
    work_order_events = list(detail.get("workOrderEventRows", []))
    communities, buildings = _collect_reference_catalog_from_geo_detail(detail)
    district_rows = _district_rows_from_catalog(communities)

    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            if apply_schema:
                _apply_schema_if_needed(cur)
            _upsert_source_providers(cur)
            _upsert_district_rows(cur, district_rows)
            _upsert_reference_catalog(cur, Jsonb, communities, buildings)
            run_pk = _upsert_geo_asset_run(cur, Jsonb, detail)
            for feature in features:
                _upsert_geo_asset(cur, Jsonb, run_pk, feature, provider_id=detail["providerId"], created_at=detail.get("createdAt"))
            for item in coverage_tasks:
                _upsert_geo_asset_task(cur, Jsonb, run_pk, item)
            for item in review_history:
                _insert_geo_asset_review_event(cur, Jsonb, run_pk, item)
            for item in work_orders:
                _upsert_geo_capture_work_order(cur, Jsonb, run_pk, item)
            for item in work_order_events:
                _insert_geo_capture_work_order_event(cur, Jsonb, run_pk, item)
        conn.commit()

    return {
        "runId": run_id,
        "ingestionRunId": run_pk,
        "geoAssetUpserts": len(features),
        "taskUpserts": len(coverage_tasks),
        "reviewEventInserts": len(review_history),
        "workOrderUpserts": len(work_orders),
        "workOrderEventInserts": len(work_order_events),
        "postgresDsnMasked": mask_dsn(dsn),
    }


def persist_reference_dictionary_manifest_to_postgres(
    manifest_path: str | Path,
    *,
    dsn: str | None = None,
    apply_schema: bool = False,
) -> dict[str, Any]:
    resolved_manifest_path = Path(manifest_path)
    manifest = json.loads(resolved_manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest.get("run_id"):
        raise KeyError(f"Dictionary manifest is invalid: {resolved_manifest_path}")

    outputs = manifest.get("outputs", {})
    district_rows = json.loads(Path(outputs["district_dictionary"]).read_text(encoding="utf-8"))
    community_rows = json.loads(Path(outputs["community_dictionary"]).read_text(encoding="utf-8"))
    building_rows = json.loads(Path(outputs["building_dictionary"]).read_text(encoding="utf-8"))

    dsn = dsn or postgres_dsn()
    if not dsn:
        raise RuntimeError("未配置 POSTGRES_DSN，无法写入 PostgreSQL。")

    psycopg, dict_row, Jsonb = _load_psycopg()
    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            if apply_schema:
                _apply_schema_if_needed(cur)
            _upsert_source_providers(cur)
            _upsert_district_rows(cur, district_rows)
            _upsert_reference_catalog(cur, Jsonb, community_rows, building_rows)
            run_pk = _upsert_reference_dictionary_run(cur, Jsonb, manifest, resolved_manifest_path)
        conn.commit()

    return {
        "runId": manifest["run_id"],
        "ingestionRunId": run_pk,
        "districtUpserts": len(district_rows),
        "communityUpserts": len(community_rows),
        "buildingUpserts": len(building_rows),
        "postgresDsnMasked": mask_dsn(dsn),
    }


def persist_metrics_snapshot_to_postgres(
    snapshot: dict[str, Any],
    *,
    dsn: str | None = None,
    apply_schema: bool = False,
) -> dict[str, Any]:
    dsn = dsn or postgres_dsn()
    if not dsn:
        raise RuntimeError("未配置 POSTGRES_DSN，无法写入 PostgreSQL。")

    community_metrics = list(snapshot.get("community_metrics") or [])
    building_floor_metrics = list(snapshot.get("building_floor_metrics") or [])

    psycopg, dict_row, _ = _load_psycopg()
    with postgres_connection(dsn=dsn) as conn:
        with conn.cursor() as cur:
            if apply_schema:
                _apply_schema_if_needed(cur)
            for item in community_metrics:
                cur.execute(
                    """
                    INSERT INTO metrics_community (
                        community_id,
                        snapshot_date,
                        sale_median_wan,
                        rent_median_monthly,
                        yield_pct,
                        rent_sale_ratio,
                        sale_sample_size,
                        rent_sample_size,
                        opportunity_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (community_id, snapshot_date) DO UPDATE
                    SET sale_median_wan = EXCLUDED.sale_median_wan,
                        rent_median_monthly = EXCLUDED.rent_median_monthly,
                        yield_pct = EXCLUDED.yield_pct,
                        rent_sale_ratio = EXCLUDED.rent_sale_ratio,
                        sale_sample_size = EXCLUDED.sale_sample_size,
                        rent_sample_size = EXCLUDED.rent_sample_size,
                        opportunity_score = EXCLUDED.opportunity_score,
                        created_at = NOW()
                    """,
                    (
                        item.get("community_id"),
                        item.get("snapshot_date"),
                        item.get("sale_median_wan"),
                        item.get("rent_median_monthly"),
                        item.get("yield_pct"),
                        item.get("rent_sale_ratio"),
                        item.get("sale_sample_size") or 0,
                        item.get("rent_sample_size") or 0,
                        item.get("opportunity_score"),
                    ),
                )
            for item in building_floor_metrics:
                cur.execute(
                    """
                    INSERT INTO metrics_building_floor (
                        community_id,
                        building_id,
                        floor_bucket,
                        snapshot_date,
                        sale_median_wan,
                        rent_median_monthly,
                        yield_pct,
                        rent_sale_ratio,
                        sample_size,
                        opportunity_score
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (building_id, floor_bucket, snapshot_date) DO UPDATE
                    SET sale_median_wan = EXCLUDED.sale_median_wan,
                        rent_median_monthly = EXCLUDED.rent_median_monthly,
                        yield_pct = EXCLUDED.yield_pct,
                        rent_sale_ratio = EXCLUDED.rent_sale_ratio,
                        sample_size = EXCLUDED.sample_size,
                        opportunity_score = EXCLUDED.opportunity_score,
                        created_at = NOW()
                    """,
                    (
                        item.get("community_id"),
                        item.get("building_id"),
                        item.get("floor_bucket"),
                        item.get("snapshot_date"),
                        item.get("sale_median_wan"),
                        item.get("rent_median_monthly"),
                        item.get("yield_pct"),
                        item.get("rent_sale_ratio"),
                        item.get("sample_size") or 0,
                        item.get("opportunity_score"),
                    ),
                )
        conn.commit()

    return {
        "snapshotDate": snapshot.get("snapshot_date"),
        "communityMetricUpserts": len(community_metrics),
        "buildingFloorMetricUpserts": len(building_floor_metrics),
        "postgresDsnMasked": mask_dsn(dsn),
    }
