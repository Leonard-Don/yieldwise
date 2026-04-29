"""Initial admin seed. Idempotent. No-op if user store is non-empty
or if ATLAS_ADMIN_USERNAME / ATLAS_ADMIN_PASSWORD env vars are missing.
"""
from __future__ import annotations

import logging
import os

from api.auth import storage as user_store

_logger = logging.getLogger(__name__)


def seed_initial_admin() -> None:
    """Called once on FastAPI startup. Creates an admin user if store is empty
    AND ATLAS_ADMIN_USERNAME + ATLAS_ADMIN_PASSWORD are set.

    Logs a clear warning if store is empty but env is unset (typical solo-dev
    starting state); this lets the app boot without forcing auth setup.
    """
    if user_store.list_users():
        return  # idempotent: already seeded
    username = os.environ.get("ATLAS_ADMIN_USERNAME")
    password = os.environ.get("ATLAS_ADMIN_PASSWORD")
    if not username or not password:
        _logger.warning(
            "Yieldwise auth: user store empty and ATLAS_ADMIN_USERNAME/"
            "ATLAS_ADMIN_PASSWORD not set; no users seeded. "
            "App will allow anonymous access to legacy /api/* routes; "
            "/api/v2/* and static shells require login. "
            "Set the env vars to seed an admin on next boot."
        )
        return
    if len(password) < 8:
        _logger.error(
            "Yieldwise auth: ATLAS_ADMIN_PASSWORD must be at least 8 chars; refusing to seed."
        )
        return
    user_store.create_user(username=username, password=password, role="admin")
    _logger.info("Yieldwise auth: seeded initial admin user %r", username)
