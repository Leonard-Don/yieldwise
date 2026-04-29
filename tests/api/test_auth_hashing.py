"""Auth password hashing tests."""
from __future__ import annotations

import pytest

from api.auth.hashing import hash_password, verify_password


def test_hash_password_returns_bcrypt_string():
    h = hash_password("hunter2")
    assert isinstance(h, str)
    assert h.startswith("$2") and len(h) >= 60


def test_verify_password_round_trip():
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h) is True
    assert verify_password("wrong password", h) is False


def test_verify_password_rejects_invalid_hash():
    # Garbage input must not crash; must return False.
    assert verify_password("any", "not-a-bcrypt-hash") is False
    assert verify_password("any", "") is False
