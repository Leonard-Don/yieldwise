"""Static-shell auth gate. Anonymous visits to /, /backstage/, /admin/ get
redirected to /login. Public exceptions: /login, /api/*, /api/health,
favicon, static assets.

This runs as a Starlette BaseHTTPMiddleware. It reads request.session
(populated by SessionMiddleware, which MUST be added BEFORE this).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from api.auth.session import read_session

_PUBLIC_PREFIXES = (
    "/login",
    "/api/",  # all API requests handle their own auth via Depends
    "/favicon",
    "/assets/",
)
_GATED_SHELLS = (
    "/",
    "/backstage",
    "/admin",
)


def _is_gated(path: str) -> bool:
    if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
        return False
    return any(path == p or path.startswith(p + "/") for p in _GATED_SHELLS)


class StaticShellAuthGate(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if _is_gated(request.url.path):
            payload = read_session(request)
            if not payload:
                next_url = request.url.path
                if request.url.query:
                    next_url += "?" + request.url.query
                return RedirectResponse(
                    url=f"/login?next={next_url}",
                    status_code=302,
                )
        return await call_next(request)
