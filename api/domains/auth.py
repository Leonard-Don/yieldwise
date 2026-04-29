"""Auth endpoints: /api/auth/login, /logout, /whoami, plus admin user CRUD."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from api.auth import storage as user_store
from api.auth.deps import current_user, require_role
from api.auth.session import clear_session, store_session
from api.schemas.auth import (
    AdminUserCreate,
    AdminUserPatch,
    CurrentUser,
    LoginRequest,
    LoginResponse,
)

router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request) -> LoginResponse:
    user_row = user_store.verify_credentials(payload.username, payload.password)
    if user_row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    user = CurrentUser(
        id=user_row.id, username=user_row.username, role=user_row.role, disabled=False
    )
    store_session(request, user)
    return LoginResponse(user=user, redirect="/")


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> Response:
    clear_session(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/auth/whoami", response_model=CurrentUser)
def whoami(user: CurrentUser = Depends(current_user)) -> CurrentUser:
    return user


# --- admin user management (gated by require_role("admin")) ---

@router.get("/auth/admin/users", response_model=list[CurrentUser])
def admin_list_users(_: CurrentUser = Depends(require_role("admin"))) -> list[CurrentUser]:
    return [
        CurrentUser(id=u.id, username=u.username, role=u.role, disabled=u.disabled)
        for u in user_store.list_users()
    ]


@router.post("/auth/admin/users", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: AdminUserCreate,
    _: CurrentUser = Depends(require_role("admin")),
) -> CurrentUser:
    try:
        u = user_store.create_user(
            username=payload.username, password=payload.password, role=payload.role
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return CurrentUser(id=u.id, username=u.username, role=u.role, disabled=u.disabled)


@router.patch("/auth/admin/users/{user_id}", response_model=CurrentUser)
def admin_patch_user(
    user_id: str,
    payload: AdminUserPatch,
    _: CurrentUser = Depends(require_role("admin")),
) -> CurrentUser:
    if user_store.get_by_id(user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    if payload.role is not None:
        user_store.set_role(user_id, payload.role)
    if payload.disabled is not None:
        user_store.set_disabled(user_id, payload.disabled)
    if payload.password is not None:
        user_store.set_password(user_id, payload.password)
    refreshed = user_store.get_by_id(user_id)
    assert refreshed is not None
    return CurrentUser(
        id=refreshed.id, username=refreshed.username, role=refreshed.role, disabled=refreshed.disabled
    )
