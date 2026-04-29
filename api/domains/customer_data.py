"""Customer data import endpoints — templates, upload, persist, read."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status

from api.auth.deps import current_user, require_role
from api.customer_data import staging
from api.customer_data.parser import parse_csv
from api.customer_data.persistence import persist_run as _persist_run
from api.schemas.auth import CurrentUser
from api.schemas.customer_data import (
    CustomerDataType,
    ImportResponse,
    StagedRunSummary,
)

router = APIRouter(tags=["customer-data"])

_TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "customer_data" / "templates"
_TEMPLATE_TYPES = ("portfolio", "pipeline", "comp_set")


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
