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
