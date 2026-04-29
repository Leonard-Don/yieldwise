from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .persistence import (
    persist_geo_asset_run_to_postgres,
    persist_import_run_to_postgres,
    persist_reference_dictionary_manifest_to_postgres,
    postgres_runtime_status,
)
from .backstage.anchors import anchor_watchlist_payload, confirm_community_anchor
from .backstage.geo_qa import (
    create_geo_asset_work_order,
    geo_asset_run_comparison,
    geo_asset_run_detail,
    geo_asset_work_orders,
    geo_task_watchlist,
    update_geo_asset_task_review,
    update_geo_asset_work_order,
)
from .backstage.review import (
    browser_capture_run_detail,
    browser_review_inbox_payload,
    browser_sampling_pack_payload,
    build_browser_sampling_pack_csv,
    create_browser_review_current_task_fixture,
    list_browser_capture_runs,
    restore_browser_review_fixture,
    submit_browser_sampling_capture,
    update_browser_capture_review_queue,
    update_browser_capture_review_queue_batch,
)
from .backstage.runs import (
    list_geo_asset_runs,
    list_import_runs,
    list_metrics_runs,
    list_reference_runs,
    runtime_data_state,
)
from .service import (
    bootstrap_local_database,
    bootstrap_payload,
    build_building_geojson,
    build_floor_watchlist_geojson,
    build_floor_watchlist_kml,
    build_geo_task_watchlist_csv,
    build_geo_task_watchlist_geojson,
    build_geo_work_order_csv,
    build_geo_work_order_geojson,
    build_geojson,
    build_kml,
    floor_watchlist,
    get_building,
    get_community,
    get_floor_detail,
    import_run_comparison,
    import_run_detail,
    list_districts,
    map_buildings_payload,
    map_communities_payload,
    operations_payload,
    opportunities,
    refresh_metrics_snapshot,
    summarize,
    system_strategy_payload,
    update_import_queue_review,
)

from .domains import (
    alerts as v2_alerts,
    annotations as v2_annotations,
    auth as v2_auth,
    buildings as v2_buildings,
    communities as v2_communities,
    config as v2_config,
    districts as v2_districts,
    health as v2_health,
    map_tiles as v2_map_tiles,
    opportunities as v2_opportunities,
    search as v2_search,
    user_prefs as v2_user_prefs,
    watchlist as v2_watchlist,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(
    title="Yieldwise API",
    version="0.1.0",
    description="Yieldwise · 租知 — 租赁资产投研工作台后端。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not _SESSION_SECRET:
    # In dev/staged solo mode, allow boot with a noisy fallback. Production
    # MUST set SESSION_SECRET (an admin-seed warning is logged on first boot).
    import secrets as _secrets
    _SESSION_SECRET = _secrets.token_urlsafe(32)
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "SESSION_SECRET not set; using ephemeral random secret. "
        "All sessions will be invalidated on app restart. "
        "Set SESSION_SECRET in production."
    )

_HTTPS_ONLY = os.environ.get("ATLAS_HTTPS_ONLY", "").lower() in ("1", "true", "yes")
app.add_middleware(
    SessionMiddleware,
    secret_key=_SESSION_SECRET,
    session_cookie="yieldwise_session",
    same_site="lax",
    https_only=_HTTPS_ONLY,
    max_age=60 * 60 * 24 * 14,  # 14 days
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(v2_auth.router, prefix="/api")
app.include_router(v2_alerts.router, prefix="/api/v2")
app.include_router(v2_health.router, prefix="/api/v2")
app.include_router(v2_config.router, prefix="/api/v2")
app.include_router(v2_opportunities.router, prefix="/api/v2")
app.include_router(v2_map_tiles.router, prefix="/api/v2")
app.include_router(v2_buildings.router, prefix="/api/v2")
app.include_router(v2_communities.router, prefix="/api/v2")
app.include_router(v2_districts.router, prefix="/api/v2")
app.include_router(v2_user_prefs.router, prefix="/api/v2")
app.include_router(v2_watchlist.router, prefix="/api/v2")
app.include_router(v2_annotations.router, prefix="/api/v2")
app.include_router(v2_search.router, prefix="/api/v2")


@app.get("/api/bootstrap")
def bootstrap() -> dict:
    return bootstrap_payload()


@app.get("/api/system/strategy")
def system_strategy() -> dict:
    return system_strategy_payload()


@app.get("/api/runtime-config")
def runtime_config() -> dict:
    amap_key = os.getenv("AMAP_API_KEY", "").strip()
    amap_security_js_code = os.getenv("AMAP_SECURITY_JSCODE", "").strip()
    runtime = runtime_data_state()
    return {
        "amapApiKey": amap_key or None,
        "hasAmapKey": bool(amap_key),
        "amapSecurityJsCode": amap_security_js_code or None,
        "hasAmapSecurityJsCode": bool(amap_security_js_code),
        **postgres_runtime_status(),
        "databaseConnected": runtime["databaseConnected"],
        "databaseReadable": runtime["databaseReadable"],
        "databaseSeeded": runtime["databaseSeeded"],
        "latestBootstrapAt": runtime["latestBootstrapAt"],
        "mockEnabled": runtime["mockEnabled"],
        "activeDataMode": runtime["activeDataMode"],
        "hasRealData": runtime["hasRealData"],
        "stagedArtifactsPresent": runtime["stagedArtifactsPresent"],
        "stagedReferenceRunCount": runtime["stagedReferenceRunCount"],
        "stagedImportRunCount": runtime["stagedImportRunCount"],
        "stagedGeoRunCount": runtime["stagedGeoRunCount"],
        "stagedMetricsRunCount": runtime["stagedMetricsRunCount"],
    }


@app.get("/api/map/districts")
def map_districts(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
) -> dict:
    return {
        "districts": list_districts(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
        "summary": summarize(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
        ),
    }


@app.get("/api/map/communities")
def map_communities(
    district: str | None = Query(default="all"),
    sample_status: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="all"),
    zoom: float | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict:
    return map_communities_payload(
        district=district,
        sample_status=sample_status,
        focus_scope=focus_scope,
        zoom=zoom,
        viewport=viewport,
    )


@app.get("/api/map/buildings")
def map_buildings(
    district: str | None = Query(default="all"),
    focus_scope: str | None = Query(default="priority"),
    geometry_quality: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    viewport: str | None = Query(default=None),
) -> dict:
    return map_buildings_payload(
        district=district,
        focus_scope=focus_scope,
        geometry_quality=geometry_quality,
        geo_run_id=geo_run_id,
        viewport=viewport,
    )


@app.get("/api/anchor-watchlist")
def anchor_watchlist(
    district: str | None = Query(default="all"),
    limit: int = Query(default=12, ge=1, le=100),
) -> dict:
    return anchor_watchlist_payload(district=district, limit=limit)


@app.get("/api/communities/{community_id}")
def community_detail(community_id: str) -> dict:
    community = get_community(community_id)
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    return community


@app.post("/api/communities/{community_id}/anchor-confirmation")
def community_anchor_confirmation(community_id: str, payload: dict = Body(...)) -> dict:
    action = str(payload.get("action") or "").strip()
    try:
        response = confirm_community_anchor(
            community_id,
            action=action,
            candidate_index=payload.get("candidate_index"),
            center_lng=payload.get("center_lng"),
            center_lat=payload.get("center_lat"),
            anchor_source_label=payload.get("anchor_source_label"),
            review_note=payload.get("review_note"),
            alias_hint=payload.get("alias_hint"),
            reference_run_id=payload.get("reference_run_id"),
            review_owner=str(payload.get("review_owner") or "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not response:
        raise HTTPException(status_code=404, detail="Community or reference run not found")
    return response


@app.get("/api/buildings/{building_id}")
def building_detail(building_id: str) -> dict:
    building = get_building(building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@app.get("/api/buildings/{building_id}/floors/{floor_no}")
def building_floor_detail(building_id: str, floor_no: int) -> dict:
    floor_detail = get_floor_detail(building_id, floor_no)
    if not floor_detail:
        raise HTTPException(status_code=404, detail="Floor detail not found")
    return floor_detail


@app.get("/api/ops/overview")
def ops_overview() -> dict:
    return operations_payload()


@app.get("/api/import-runs")
def import_runs() -> dict:
    return {"items": list_import_runs()}


@app.get("/api/browser-capture-runs")
def browser_capture_runs(limit: int = Query(default=10, ge=1, le=100)) -> dict:
    return {"items": list_browser_capture_runs(limit=limit)}


@app.get("/api/browser-review-inbox")
def browser_review_inbox(district: str | None = Query(default="all"), limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return browser_review_inbox_payload(district=district, limit=limit)


@app.get("/api/browser-capture-runs/{run_id}")
def browser_capture_run(run_id: str) -> dict:
    payload = browser_capture_run_detail(run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Browser capture run not found")
    return payload


@app.post("/api/browser-capture-runs/{run_id}/review-queue/batch")
def review_browser_capture_queue_batch(run_id: str, payload: dict = Body(default={})) -> dict:
    queue_ids = payload.get("queueIds") or []
    try:
        result = update_browser_capture_review_queue_batch(
            run_id,
            queue_ids,
            status=payload.get("status", "resolved"),
            resolution_notes=payload.get("resolutionNotes"),
            review_owner=payload.get("reviewOwner", "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Browser capture review queue batch not found")
    return result


@app.post("/api/browser-capture-runs/{run_id}/review-queue/{queue_id}")
def review_browser_capture_queue_item(run_id: str, queue_id: str, payload: dict = Body(default={})) -> dict:
    try:
        result = update_browser_capture_review_queue(
            run_id,
            queue_id,
            status=payload.get("status", "resolved"),
            resolution_notes=payload.get("resolutionNotes"),
            review_owner=payload.get("reviewOwner", "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Browser capture review queue item not found")
    return result


@app.post("/api/dev/browser-review-fixtures/review-current-task")
def create_review_current_task_fixture() -> dict:
    try:
        return create_browser_review_current_task_fixture()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/dev/browser-review-fixtures/{fixture_id}")
def restore_review_fixture(fixture_id: str) -> dict:
    try:
        return restore_browser_review_fixture(fixture_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/reference-runs")
def reference_runs() -> dict:
    return {"items": list_reference_runs()}


@app.get("/api/metrics-runs")
def metrics_runs() -> dict:
    return {"items": list_metrics_runs()}


@app.post("/api/jobs/refresh-metrics")
def refresh_metrics_job(payload: dict | None = Body(default=None)) -> dict:
    payload = payload or {}
    snapshot_date_raw = str(payload.get("snapshot_date") or payload.get("snapshotDate") or date.today().isoformat()).strip()
    try:
        snapshot_date = date.fromisoformat(snapshot_date_raw).isoformat()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="snapshot_date must be YYYY-MM-DD") from exc

    batch_name = str(payload.get("batch_name") or payload.get("batchName") or f"staged-metrics-{snapshot_date}").strip()
    if not batch_name:
        raise HTTPException(status_code=400, detail="batch_name cannot be empty")

    try:
        return refresh_metrics_snapshot(
            snapshot_date=snapshot_date,
            batch_name=batch_name,
            write_postgres=bool(payload.get("write_postgres") or payload.get("writePostgres")),
            apply_schema=bool(payload.get("apply_schema") or payload.get("applySchema")),
            dsn=str(payload.get("dsn") or "").strip() or None,
            trigger_source="atlas-ui",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Metrics refresh failed: {exc}") from exc


@app.get("/api/geo-assets/runs")
def geo_asset_runs() -> dict:
    return {"items": list_geo_asset_runs()}


@app.get("/api/geo-assets/runs/{run_id}")
def geo_asset_run(run_id: str, baseline_run_id: str | None = Query(default=None)) -> dict:
    payload = geo_asset_run_detail(run_id, baseline_run_id=baseline_run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Geo asset run not found")
    return payload


@app.get("/api/geo-assets/runs/{run_id}/compare")
def compare_geo_asset_run(run_id: str, baseline_run_id: str | None = Query(default=None)) -> dict:
    payload = geo_asset_run_comparison(run_id, baseline_run_id=baseline_run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Geo asset comparison baseline not found")
    return payload


@app.get("/api/geo-assets/runs/{run_id}/work-orders")
def geo_asset_run_work_orders(
    run_id: str,
    district: str | None = Query(default="all"),
    status: str | None = Query(default="all"),
    assignee: str | None = Query(default="all"),
    limit: int = Query(default=200, ge=1, le=500),
) -> dict:
    payload = geo_asset_work_orders(run_id, district=district, status=status, assignee=assignee, limit=limit)
    if not payload and not geo_asset_run_detail(run_id):
        raise HTTPException(status_code=404, detail="Geo asset run not found")
    return {"items": payload}


@app.post("/api/geo-assets/runs/{run_id}/work-orders")
def create_geo_asset_run_work_order(run_id: str, payload: dict = Body(default={})) -> dict:
    try:
        response = create_geo_asset_work_order(
            run_id,
            task_ids=payload.get("taskIds") or [],
            assignee=str(payload.get("assignee") or "gis-team"),
            due_at=payload.get("dueAt"),
            notes=payload.get("notes"),
            created_by=str(payload.get("createdBy") or "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not response:
        raise HTTPException(status_code=404, detail="Geo asset run not found")
    return response


@app.post("/api/geo-assets/runs/{run_id}/work-orders/{work_order_id}")
def update_geo_asset_run_work_order(run_id: str, work_order_id: str, payload: dict = Body(default={})) -> dict:
    try:
        response = update_geo_asset_work_order(
            run_id,
            work_order_id,
            status=str(payload.get("status") or ""),
            assignee=payload.get("assignee"),
            notes=payload.get("notes"),
            changed_by=str(payload.get("changedBy") or "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not response:
        raise HTTPException(status_code=404, detail="Geo work order not found")
    return response


@app.get("/api/import-runs/{run_id}")
def import_run(run_id: str, baseline_run_id: str | None = Query(default=None)) -> dict:
    payload = import_run_detail(run_id, baseline_run_id=baseline_run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Import run not found")
    return payload


@app.get("/api/import-runs/{run_id}/compare")
def compare_import_run(run_id: str, baseline_run_id: str | None = Query(default=None)) -> dict:
    payload = import_run_comparison(run_id, baseline_run_id=baseline_run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Comparison baseline not found")
    return payload


@app.post("/api/import-runs/{run_id}/persist")
def persist_import_run(run_id: str, payload: dict = Body(default={})):
    try:
        return persist_import_run_to_postgres(run_id, apply_schema=bool(payload.get("applySchema", False)))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reference-runs/{run_id}/persist")
def persist_reference_run(run_id: str, payload: dict = Body(default={})):
    run = next((item for item in list_reference_runs() if item.get("runId") == run_id), None)
    if not run or not run.get("manifestPath"):
        raise HTTPException(status_code=404, detail=f"Reference run not found: {run_id}")
    try:
        return persist_reference_dictionary_manifest_to_postgres(
            run["manifestPath"],
            apply_schema=bool(payload.get("applySchema", False)),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/import-runs/{run_id}/review-queue/{queue_id}")
def review_queue_item(run_id: str, queue_id: str, payload: dict = Body(default={})):
    try:
        result = update_import_queue_review(
            run_id,
            queue_id,
            parse_status=payload.get("status", "resolved"),
            resolution_notes=payload.get("resolutionNotes"),
            review_owner=payload.get("reviewOwner", "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return result


@app.post("/api/database/bootstrap-local")
def bootstrap_local(payload: dict = Body(default={})):
    try:
        return bootstrap_local_database(
            reference_run_id=payload.get("reference_run_id"),
            import_run_id=payload.get("import_run_id"),
            geo_run_id=payload.get("geo_run_id"),
            apply_schema=bool(payload.get("applySchema", False)),
            refresh_metrics=bool(payload.get("refreshMetrics", True)),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/geo-assets/runs/{run_id}/persist")
def persist_geo_asset_run(run_id: str, payload: dict = Body(default={})):
    try:
        return persist_geo_asset_run_to_postgres(run_id, apply_schema=bool(payload.get("applySchema", False)))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/geo-assets/runs/{run_id}/tasks/{task_id}")
def review_geo_asset_task(run_id: str, task_id: str, payload: dict = Body(default={})):
    try:
        result = update_geo_asset_task_review(
            run_id,
            task_id,
            status=payload.get("status", "scheduled"),
            resolution_notes=payload.get("resolutionNotes"),
            review_owner=payload.get("reviewOwner", "atlas-ui"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not result:
        raise HTTPException(status_code=404, detail="Geo asset task not found")
    return result


@app.get("/api/opportunities")
def opportunity_list(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
) -> dict:
    return {
        "items": opportunities(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
            min_score=min_score,
        )
    }


@app.get("/api/floor-watchlist")
def floor_watchlist_endpoint(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    run_id: str | None = Query(default=None),
    baseline_run_id: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
) -> dict:
    return {
        "items": floor_watchlist(
            district=district,
            min_yield=min_yield,
            max_budget=max_budget,
            min_samples=min_samples,
            run_id=run_id,
            baseline_run_id=baseline_run_id,
            limit=limit,
        )
    }


@app.get("/api/geo-task-watchlist")
def geo_task_watchlist_endpoint(
    district: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=12, ge=1, le=50),
    include_resolved: bool = Query(default=False),
) -> dict:
    return {
        "items": geo_task_watchlist(
            district=district,
            geo_run_id=geo_run_id,
            limit=limit,
            include_resolved=include_resolved,
        )
    }


@app.get("/api/browser-sampling-pack")
def browser_sampling_pack_endpoint(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    focus_scope: str | None = Query(default="all"),
    limit: int = Query(default=12, ge=1, le=100),
) -> dict:
    return browser_sampling_pack_payload(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        focus_scope=focus_scope,
        limit=limit,
    )


@app.post("/api/browser-sampling-captures")
def browser_sampling_captures(payload: dict = Body(...)) -> dict:
    try:
        return submit_browser_sampling_capture(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/geo-assets/buildings")
def geo_assets_buildings(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    geo_run_id: str | None = Query(default=None),
) -> dict:
    return build_building_geojson(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        geo_run_id=geo_run_id,
        include_svg_props=True,
    )


@app.get("/api/geo-assets/floor-watchlist")
def geo_assets_floor_watchlist(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    run_id: str | None = Query(default=None),
    baseline_run_id: str | None = Query(default=None),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    return build_floor_watchlist_geojson(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        geo_run_id=geo_run_id,
        limit=limit,
        include_svg_props=True,
    )


@app.get("/api/export/geojson")
def export_geojson(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
) -> dict:
    return build_geojson(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    )


@app.get("/api/export/kml")
def export_kml(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
) -> Response:
    content = build_kml(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
    )
    headers = {"Content-Disposition": 'attachment; filename="shanghai-yield-atlas.kml"'}
    return Response(content=content, media_type="application/vnd.google-earth.kml+xml", headers=headers)


@app.get("/api/export/floor-watchlist.geojson")
def export_floor_watchlist_geojson(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    run_id: str | None = Query(default=None),
    baseline_run_id: str | None = Query(default=None),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    return build_floor_watchlist_geojson(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        geo_run_id=geo_run_id,
        limit=limit,
    )


@app.get("/api/export/floor-watchlist.kml")
def export_floor_watchlist_kml(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    run_id: str | None = Query(default=None),
    baseline_run_id: str | None = Query(default=None),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> Response:
    content = build_floor_watchlist_kml(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        run_id=run_id,
        baseline_run_id=baseline_run_id,
        geo_run_id=geo_run_id,
        limit=limit,
    )
    headers = {"Content-Disposition": 'attachment; filename="shanghai-yield-floor-watchlist.kml"'}
    return Response(content=content, media_type="application/vnd.google-earth.kml+xml", headers=headers)


@app.get("/api/export/geo-task-watchlist.geojson")
def export_geo_task_watchlist_geojson(
    district: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    include_resolved: bool = Query(default=False),
) -> dict:
    return build_geo_task_watchlist_geojson(
        district=district,
        geo_run_id=geo_run_id,
        limit=limit,
        include_resolved=include_resolved,
    )


@app.get("/api/export/geo-task-watchlist.csv")
def export_geo_task_watchlist_csv(
    district: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    include_resolved: bool = Query(default=False),
) -> Response:
    content = build_geo_task_watchlist_csv(
        district=district,
        geo_run_id=geo_run_id,
        limit=limit,
        include_resolved=include_resolved,
    )
    headers = {"Content-Disposition": 'attachment; filename="shanghai-geo-task-watchlist.csv"'}
    return Response(content=content, media_type="text/csv; charset=utf-8", headers=headers)


@app.get("/api/export/browser-sampling-pack.csv")
def export_browser_sampling_pack_csv(
    district: str | None = Query(default="all"),
    min_yield: float = Query(default=0.0, ge=0),
    max_budget: float = Query(default=10000.0, gt=0),
    min_samples: int = Query(default=0, ge=0),
    focus_scope: str | None = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
) -> Response:
    content = build_browser_sampling_pack_csv(
        district=district,
        min_yield=min_yield,
        max_budget=max_budget,
        min_samples=min_samples,
        focus_scope=focus_scope,
        limit=limit,
    )
    headers = {"Content-Disposition": 'attachment; filename="shanghai-browser-sampling-pack.csv"'}
    return Response(content=content, media_type="text/csv; charset=utf-8", headers=headers)


@app.get("/api/export/geo-work-orders.geojson")
def export_geo_work_orders_geojson(
    district: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    status: str | None = Query(default="all"),
    assignee: str | None = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    return build_geo_work_order_geojson(
        district=district,
        geo_run_id=geo_run_id,
        status=status,
        assignee=assignee,
        limit=limit,
    )


@app.get("/api/export/geo-work-orders.csv")
def export_geo_work_orders_csv(
    district: str | None = Query(default="all"),
    geo_run_id: str | None = Query(default=None),
    status: str | None = Query(default="all"),
    assignee: str | None = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=500),
) -> Response:
    content = build_geo_work_order_csv(
        district=district,
        geo_run_id=geo_run_id,
        status=status,
        assignee=assignee,
        limit=limit,
    )
    headers = {"Content-Disposition": 'attachment; filename="shanghai-geo-work-orders.csv"'}
    return Response(content=content, media_type="text/csv; charset=utf-8", headers=headers)


@app.get("/favicon.svg", include_in_schema=False)
def favicon_svg() -> FileResponse:
    path = ROOT_DIR / "favicon.svg"
    if not path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/svg+xml")


@app.get("/favicon.ico", include_in_schema=False)
def favicon_ico() -> FileResponse:
    path = ROOT_DIR / "favicon.ico"
    if not path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(path, media_type="image/x-icon")


app.mount(
    "/backstage",
    StaticFiles(directory=FRONTEND_DIR / "backstage", html=True),
    name="backstage",
)

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR / "user", html=True),
    name="user",
)
