from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def _parse_env_file(path: Path) -> dict[str, str]:
    payload: dict[str, str] = {}
    if not path.exists():
        return payload
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            payload[key] = value
    return payload


def load_local_env() -> None:
    for candidate in (ROOT_DIR / ".env.local", ROOT_DIR / ".env"):
        for key, value in _parse_env_file(candidate).items():
            os.environ.setdefault(key, value)
