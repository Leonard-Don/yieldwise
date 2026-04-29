"""FastAPI dependency injectors for auth. Use as Depends(current_user) etc."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, Request, status

from api.auth.session import read_session
from api.auth import storage as user_store
from api.schemas.auth import CurrentUser


def current_user(request: Request) -> CurrentUser:
    """Return the current logged-in user or raise 401."""
    payload = read_session(request)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    user = user_store.get_by_id(payload.get("user_id", ""))
    if user is None or user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user gone or disabled")
    return CurrentUser(id=user.id, username=user.username, role=user.role, disabled=user.disabled)


def require_role(*allowed: str) -> Callable[[CurrentUser], CurrentUser]:
    """Build a dependency that requires the current user to have one of the allowed roles."""

    def _checker(user: CurrentUser = Depends(current_user)) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="role not permitted")
        return user

    return _checker
