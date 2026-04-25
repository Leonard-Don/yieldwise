"""Phase 1 smoke: boot uvicorn in a subprocess, hit the four key routes,
assert each response, then shut down.

Run:
    python3 scripts/phase1_smoke.py
    python3 scripts/phase1_smoke.py --port 8014
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

# Bypass any system HTTP proxy (common in dev/CI environments) so that
# requests to 127.0.0.1 are sent directly to the local uvicorn process.
_opener = build_opener(ProxyHandler({}))


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"

    proc = subprocess.Popen(
        ["uvicorn", "api.main:app", "--port", str(args.port), "--log-level", "warning"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server(f"{base}/api/health")

        checks = [
            (f"{base}/", 'data-user-shell="atlas"'),
            (f"{base}/", 'data-component="mode-chips"'),
            (f"{base}/", 'data-component="drawer"'),
            (f"{base}/", 'data-role="filter-chips"'),
            (f"{base}/", 'data-component="onboarding"'),
            (f"{base}/backstage/", "<title>Shanghai Yield Atlas</title>"),
            (f"{base}/api/v2/health", '"surface":"user-platform-v2"'),
            (f"{base}/api/health", '"status":"ok"'),
            (f"{base}/api/v2/opportunities", '"items"'),
            (f"{base}/api/v2/map/districts", '"districts"'),
            (f"{base}/api/v2/map/districts", '"summary"'),
            (f"{base}/api/v2/map/communities", '"items"'),
            (f"{base}/api/v2/map/buildings", '"features"'),
            (f"{base}/api/v2/user/prefs", '"districts"'),
            (f"{base}/api/v2/watchlist", '"items"'),
            (f"{base}/api/v2/annotations/by-target/probe", '"items"'),
            (f"{base}/api/v2/alerts/rules", '"yield_delta_abs"'),
        ]
        failed: list[str] = []
        for url, expected_substring in checks:
            status, body = fetch(url)
            ok = status == 200 and expected_substring in body
            line = f"[{status}] {url}  expect {expected_substring!r} -> {'OK' if ok else 'FAIL'}"
            print(line)
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
