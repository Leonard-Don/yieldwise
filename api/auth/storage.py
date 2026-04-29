"""JSON-backed, file-locked user store. Matches personal_storage.py pattern.

Storage path: <ATLAS_PERSONAL_DATA_DIR or data/personal/>/auth_users.json
"""
from __future__ import annotations

import fcntl
import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .hashing import hash_password, verify_password

_FILENAME = "auth_users.json"
_LOCK_RETRY_DELAY_S = 0.05
_LOCK_MAX_ATTEMPTS = 100  # ~5 seconds at 50ms each, then re-raise
_VALID_ROLES = ("admin", "analyst", "viewer")


@dataclass(frozen=True)
class User:
    id: str
    username: str
    role: str
    disabled: bool
    created_at: str
    password_hash: str = ""  # never serialized to clients


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_PERSONAL_DATA_DIR")
    base = Path(override) if override else Path(__file__).resolve().parents[2] / "data" / "personal"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _store_path() -> Path:
    return _data_dir() / _FILENAME


@contextmanager
def _locked_file(mode: str) -> Iterator:
    """Acquire an exclusive flock via a sidecar .lock file, then yield the data fh.

    The lock is held on a sidecar `<file>.lock` rather than the data file itself:
    `_write_all` uses tmp + os.replace() which swaps the inode, so a flock on the
    old inode would be silently dropped. Sidecar lock survives the inode swap.

    Retries up to `_LOCK_MAX_ATTEMPTS` times on BlockingIOError, then re-raises.
    """
    path = _store_path()
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    lock_path = path.with_suffix(path.suffix + ".lock")

    lock_fd = open(lock_path, "w")
    try:
        for attempt in range(1, _LOCK_MAX_ATTEMPTS + 1):
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if attempt == _LOCK_MAX_ATTEMPTS:
                    raise
                time.sleep(_LOCK_RETRY_DELAY_S)

        fh = open(path, mode, encoding="utf-8")
        try:
            yield fh
        finally:
            fh.close()
    finally:
        try:
            fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
        finally:
            lock_fd.close()


def _read_all() -> list[dict]:
    path = _store_path()
    if not path.exists():
        return []
    with _locked_file("r") as fh:
        text = fh.read()
    if not text.strip():
        return []
    return json.loads(text)


def _write_all(rows: list[dict]) -> None:
    """Atomic write: dump to <path>.tmp, fsync, os.replace() onto the real path.

    A crash mid-write leaves the original auth_users.json untouched rather than
    a truncated half-write that would break json.loads and lock all logins out.
    """
    path = _store_path()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with _locked_file("r") as _fh:  # acquire sidecar lock; we don't use this fh
        del _fh
        with open(tmp_path, "w", encoding="utf-8") as tmp_fh:
            json.dump(rows, tmp_fh, ensure_ascii=False, indent=2, sort_keys=True)
            tmp_fh.flush()
            os.fsync(tmp_fh.fileno())
        os.replace(tmp_path, path)


def _row_to_user(row: dict) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        disabled=row.get("disabled", False),
        created_at=row.get("created_at", ""),
        password_hash=row.get("password_hash", ""),
    )


def list_users() -> list[User]:
    return [_row_to_user(r) for r in _read_all()]


def get_by_id(user_id: str) -> User | None:
    for r in _read_all():
        if r["id"] == user_id:
            return _row_to_user(r)
    return None


def get_by_username(username: str) -> User | None:
    for r in _read_all():
        if r["username"] == username:
            return _row_to_user(r)
    return None


def create_user(*, username: str, password: str, role: str) -> User:
    if role not in _VALID_ROLES:
        raise ValueError(f"role must be one of {_VALID_ROLES}, got {role!r}")
    rows = _read_all()
    if any(r["username"] == username for r in rows):
        raise ValueError(f"user {username!r} exists")
    new_row = {
        "id": str(uuid.uuid4()),
        "username": username,
        "role": role,
        "disabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "password_hash": hash_password(password),
    }
    rows.append(new_row)
    _write_all(rows)
    return _row_to_user(new_row)


def set_role(user_id: str, role: str) -> None:
    if role not in _VALID_ROLES:
        raise ValueError(f"role must be one of {_VALID_ROLES}")
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["role"] = role
            _write_all(rows)
            return
    raise KeyError(user_id)


def set_disabled(user_id: str, disabled: bool) -> None:
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["disabled"] = bool(disabled)
            _write_all(rows)
            return
    raise KeyError(user_id)


def set_password(user_id: str, password: str) -> None:
    rows = _read_all()
    for r in rows:
        if r["id"] == user_id:
            r["password_hash"] = hash_password(password)
            _write_all(rows)
            return
    raise KeyError(user_id)


def verify_credentials(username: str, password: str) -> User | None:
    """Return User if username + password match AND user is not disabled."""
    user = get_by_username(username)
    if user is None or user.disabled:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
