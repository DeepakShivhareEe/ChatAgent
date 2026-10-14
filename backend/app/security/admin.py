"""Shared admin-endpoint authorization."""

import secrets
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings


def verify_admin_key(x_admin_key: Optional[str] = Header(default=None)) -> None:
    """Verify that administrative features are enabled and authorized."""
    configured_key = settings.ADMIN_API_KEY.strip()
    if not configured_key:
        raise HTTPException(
            status_code=503,
            detail="Administrative endpoints are disabled until ADMIN_API_KEY is configured.",
        )
    if not x_admin_key or not secrets.compare_digest(x_admin_key, configured_key):
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key.")
