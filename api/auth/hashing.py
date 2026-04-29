"""Password hashing — bcrypt, cost factor 12."""
from __future__ import annotations

import bcrypt

_ROUNDS = 12


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password with bcrypt cost factor 12. Returns the bcrypt
    string (utf-8 decoded) safe to store in JSON."""
    if not isinstance(plaintext, str):
        raise TypeError("password must be str")
    salt = bcrypt.gensalt(rounds=_ROUNDS)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash. Never raises;
    returns False on any malformed input."""
    if not isinstance(plaintext, str) or not isinstance(hashed, str) or not hashed:
        return False
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False
