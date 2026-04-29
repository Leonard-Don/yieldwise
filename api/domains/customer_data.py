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
