"""Phase 1 smoke: boot uvicorn in a subprocess, hit the four key routes,
assert each response, then shut down.

Run:
    python3 scripts/phase1_smoke.py
    python3 scripts/phase1_smoke.py --port 8014
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import subprocess
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, ProxyHandler, build_opener


# Bypass any system HTTP proxy (common in dev/CI environments) so that
# requests to 127.0.0.1 are sent directly to the local uvicorn process.
# CookieJar lets us authenticate once (POST /api/auth/login) and carry
# the session cookie through subsequent /api/v2/* checks.
_cookie_jar = http.cookiejar.CookieJar()
_opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(_cookie_jar))


class _NoRedirect(HTTPRedirectHandler):
    """Used by fetch_no_redirect() to assert 302s instead of following them."""

    def http_error_302(self, req, fp, code, msg, headers):
        raise HTTPError(req.full_url, code, msg, headers, fp)

    http_error_301 = http_error_303 = http_error_307 = http_error_302


_no_redirect_opener = build_opener(ProxyHandler({}), _NoRedirect())


def _urlopen(url: str, timeout: float):
    return _opener.open(url, timeout=timeout)


def wait_for_server(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with _urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return
        except URLError as err:
            last_err = err
        time.sleep(0.2)
    raise TimeoutError(f"server at {url} did not come up within {timeout}s: {last_err}")


def fetch(url: str) -> tuple[int, str]:
    with _urlopen(url, timeout=5.0) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, body


def fetch_redirect_status(url: str) -> int:
    """Like fetch() but returns the redirect status without following it.

    Returns the HTTP status code (302/301/etc) for a redirect, or 200 on a
    successful non-redirect response.
    """
    try:
        with _no_redirect_opener.open(url, timeout=5.0) as resp:
            return resp.status
    except HTTPError as exc:
        return exc.code


def login(base: str, username: str, password: str) -> None:
    """POST credentials to /api/auth/login; session cookie lands in _cookie_jar."""
    payload = json.dumps({"username": username, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/api/auth/login",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with _opener.open(req, timeout=5.0) as resp:
        if resp.status != 200:
            raise RuntimeError(f"login failed: {resp.status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"

    # Smoke runs against demo data — CI has no DB and no staged tmp/ runs, so
    # without this flag list_districts() returns [] and /api/v2/districts/{id}
    # 404s. The flag is per-subprocess; the parent shell is untouched.
    # Plan 2 (M2 auth) added: smoke uses a fresh tmp ATLAS_PERSONAL_DATA_DIR
    # (so seed runs on every invocation regardless of cross-run state) +
    # SESSION_SECRET + admin credentials. Login lands a session cookie
    # that the authed checks below carry into /api/v2/* (gated by
    # Depends(current_user) since P2-B3).
    import tempfile
    smoke_data_dir = tempfile.mkdtemp(prefix="yw-smoke-")
    smoke_env = {
        **os.environ,
        "ATLAS_ENABLE_DEMO_MOCK": "true",
        "ATLAS_PERSONAL_DATA_DIR": smoke_data_dir,
        "SESSION_SECRET": "yieldwise-smoke-only-not-for-prod",
        "ATLAS_ADMIN_USERNAME": "smoke",
        "ATLAS_ADMIN_PASSWORD": "smoke-pw-12chars",
    }
    proc = subprocess.Popen(
        ["uvicorn", "api.main:app", "--port", str(args.port), "--log-level", "warning"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=smoke_env,
    )
    try:
        wait_for_server(f"{base}/api/health")

        # Phase A: anonymous checks — no session cookie. Verify auth gate +
        # public surface (login HTML, /api/health, /api/v2/health).
        anonymous_checks = [
            (f"{base}/login", "<title>Yieldwise · 登录</title>"),
            (f"{base}/api/health", '"status":"ok"'),
            (f"{base}/api/v2/health", '"surface":"user-platform-v2"'),
        ]
        # Anonymous /, /backstage/, /admin/users must redirect to /login.
        anonymous_redirects = [
            f"{base}/",
            f"{base}/backstage/",
            f"{base}/admin/users",
        ]

        failed: list[str] = []
        for url, expected_substring in anonymous_checks:
            status, body = fetch(url)
            ok = status == 200 and expected_substring in body
            print(f"[{status}] {url}  expect {expected_substring!r} -> {'OK' if ok else 'FAIL'}")
            if not ok:
                failed.append(url)

        for url in anonymous_redirects:
            status = fetch_redirect_status(url)
            ok = status == 302
            print(f"[{status}] {url}  expect 302 redirect -> {'OK' if ok else 'FAIL'}")
            if not ok:
                failed.append(url)

        # Phase B: log in as the seeded admin. Cookie lands in _cookie_jar.
        login(base, "smoke", "smoke-pw-12chars")

        # Phase C: authenticated checks. Cookie carried automatically.
        authed_checks = [
            (f"{base}/", 'data-user-shell="atlas"'),
            (f"{base}/", 'data-component="mode-chips"'),
            (f"{base}/", 'data-component="drawer"'),
            (f"{base}/", 'data-component="help-overlay"'),
            (f"{base}/", 'data-role="filter-chips"'),
            (f"{base}/", 'data-component="onboarding"'),
            (f"{base}/backstage/", "<title>Yieldwise Workbench · 租知</title>"),
            (f"{base}/api/v2/config/city", '"cityId":"shanghai"'),
            (f"{base}/api/v2/opportunities", '"items"'),
            (f"{base}/api/v2/map/districts", '"districts"'),
            (f"{base}/api/v2/map/districts", '"summary"'),
            (f"{base}/api/v2/map/communities", '"items"'),
            (f"{base}/api/v2/map/buildings", '"features"'),
            (f"{base}/api/v2/user/prefs", '"districts"'),
            (f"{base}/api/v2/watchlist", '"items"'),
            (f"{base}/api/v2/annotations/by-target/probe", '"items"'),
            (f"{base}/api/v2/alerts/rules", '"yield_delta_abs"'),
            (f"{base}/api/v2/alerts/since-last-open", '"last_open_at"'),
            (f"{base}/api/v2/search?q=%E6%B5%A6%E4%B8%9C", '"items"'),
            (f"{base}/api/v2/districts/pudong", '"communities"'),
            (f"{base}/api/auth/whoami", '"username":"smoke"'),
            (f"{base}/api/v2/customer-data/templates/portfolio.csv", "project_name,address"),
            (f"{base}/api/v2/customer-data/imports", "[]"),
        ]
        for url, expected_substring in authed_checks:
            status, body = fetch(url)
            ok = status == 200 and expected_substring in body
            print(f"[{status}] {url}  expect {expected_substring!r} -> {'OK' if ok else 'FAIL'}")
            if not ok:
                failed.append(url)

        if failed:
            print(f"\nFAIL ({len(failed)} routes):", ", ".join(failed))
            return 1
        print("\nPhase 1 smoke OK")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
