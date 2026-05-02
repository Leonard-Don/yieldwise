from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ..backstage.runs import list_import_runs
from ..data_quality import build_data_quality_gate
from ..service import current_community_dataset

router = APIRouter(tags=["data-quality"])


@router.get("/data-quality")
def data_quality_gate(
    latest_only: bool = Query(default=False, description="Only inspect the latest import run for dirty listing rows."),
) -> dict[str, Any]:
    return build_data_quality_gate(
        communities=current_community_dataset(),
        import_runs=list_import_runs(),
        latest_only=latest_only,
    )
