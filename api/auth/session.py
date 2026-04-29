"""Session payload helpers. Session is signed by SessionMiddleware in main.py.

Payload shape: {"user_id": str, "username": str, "role": str}
"""
from __future__ import annotations

from typing import Any

from starlette.requests import Request

from api.schemas.auth import CurrentUser

_SESSION_KEY = "yw"  # short to keep cookie compact


def store_session(request: Request, user: CurrentUser) -> None:
    request.session[_SESSION_KEY] = {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }


def clear_session(request: Request) -> None:
    request.session.pop(_SESSION_KEY, None)


def read_session(request: Request) -> dict[str, Any] | None:
    return request.session.get(_SESSION_KEY)
