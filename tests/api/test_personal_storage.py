from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from api import personal_storage


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(tmp_path))
    return tmp_path


def test_read_returns_none_when_file_missing(data_dir: Path) -> None:
    assert personal_storage.read_json("missing.json") is None


def test_write_then_read_roundtrip(data_dir: Path) -> None:
    payload = {"budget_max_wan": 1500, "districts": ["pudong"]}
    personal_storage.write_json("user_prefs.json", payload)
    assert personal_storage.read_json("user_prefs.json") == payload


def test_write_creates_data_dir_if_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "nested" / "personal"
    monkeypatch.setenv("ATLAS_PERSONAL_DATA_DIR", str(target))
    personal_storage.write_json("user_prefs.json", {"a": 1})
    assert (target / "user_prefs.json").is_file()


def test_write_backs_up_existing_file_to_trash(data_dir: Path) -> None:
    personal_storage.write_json("user_prefs.json", {"v": 1})
    personal_storage.write_json("user_prefs.json", {"v": 2})
    trash_files = sorted((data_dir / ".trash").glob("*-user_prefs.json"))
    assert len(trash_files) == 1
    backed = json.loads(trash_files[0].read_text(encoding="utf-8"))
    assert backed == {"v": 1}


def test_trash_rotation_keeps_at_most_twenty(data_dir: Path) -> None:
    for i in range(25):
        personal_storage.write_json("user_prefs.json", {"v": i})
    trash_files = list((data_dir / ".trash").glob("*-user_prefs.json"))
    assert len(trash_files) == 20


def test_read_returns_none_on_corrupt_json(data_dir: Path) -> None:
    bad = data_dir / "user_prefs.json"
    bad.write_text("{not valid", encoding="utf-8")
    assert personal_storage.read_json("user_prefs.json") is None


def test_write_uses_atomic_rename(data_dir: Path) -> None:
    personal_storage.write_json("user_prefs.json", {"a": 1})
    # No leftover *.tmp file should remain.
    leftovers = list(data_dir.glob("*.tmp"))
    assert leftovers == []
