from __future__ import annotations

import fcntl
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT_DIR / "data" / "personal"
TRASH_DIRNAME = ".trash"
TRASH_RETENTION = 20
LOCK_RETRY_DELAY_S = 0.05


def _data_dir() -> Path:
    override = os.environ.get("ATLAS_PERSONAL_DATA_DIR")
    return Path(override) if override else DEFAULT_DATA_DIR


def read_json(filename: str) -> dict[str, Any] | None:
    path = _data_dir() / filename
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def write_json(filename: str, payload: dict[str, Any]) -> None:
    base = _data_dir()
    base.mkdir(parents=True, exist_ok=True)
    trash = base / TRASH_DIRNAME
    trash.mkdir(parents=True, exist_ok=True)
    target = base / filename
    lock_path = base / f".{filename}.lock"

    for attempt in (1, 2):
        lock_fd = open(lock_path, "w")
        try:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                lock_fd.close()
                if attempt == 2:
                    raise
                time.sleep(LOCK_RETRY_DELAY_S)
                continue

            try:
                if target.is_file():
                    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")
                    backup_name = f"{timestamp}-{filename}"
                    shutil.copy2(target, trash / backup_name)
                    _rotate_trash(trash, filename, TRASH_RETENTION)

                tmp_path = target.with_suffix(target.suffix + ".tmp")
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, ensure_ascii=False, indent=2)
                os.replace(tmp_path, target)
            finally:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()
            return
        except Exception:
            try:
                lock_fd.close()
            except Exception:
                pass
            raise


def _rotate_trash(trash_dir: Path, filename: str, keep: int) -> None:
    matches = sorted(trash_dir.glob(f"*-{filename}"), reverse=True)
    for old in matches[keep:]:
        try:
            old.unlink()
        except OSError:
            pass
