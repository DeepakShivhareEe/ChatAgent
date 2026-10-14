"""Per-site API key authorization for public endpoints.

When `SITE_TOKENS` is configured, the public `POST /chat` route requires a
matching `X-Site-Key` header carrying one of the configured tokens. When
`SITE_TOKENS` is empty the check is a no-op, so local/demo installs keep
working without configuration.

A token may also be bound to the origins allowed to use it
(`site:token:https://a.com|https://b.com`). The key travels in the browser, so
anyone can copy it; binding it to origins means a copied key is useless from
another site. Bound tokens require a matching `Origin` header and are refused
with `403` when it is missing or different.
"""

import logging
import secrets
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


def enforce_site_tokens_configured() -> None:
    """Refuse to start in production when `SITE_TOKENS` is empty.

    Without tokens `POST /chat` answers anyone from any origin, which is
    convenient for local work but is a misconfiguration in production. `DEBUG`
    is the existing mode switch (`true` = development), so development keeps
    the warning while production fails fast instead of running open.
    """
    if settings.site_token_entries:
        return

    if settings.DEBUG:
        logger.warning(
            "SITE_TOKENS is empty — POST /chat is open to any origin "
            "(development mode; set SITE_TOKENS before production)."
        )
        return

    raise RuntimeError(
        "SITE_TOKENS is empty while DEBUG is false: refusing to start so that "
        "POST /chat is not left open to any origin. Configure at least one "
        "'site:token:origin1|origin2' entry, or set DEBUG=true for local "
        "development."
    )


def _entry_for_token(token: str) -> Optional[tuple[str, tuple[str, ...]]]:
    """Return (site, allowed_origins) for a token, or None when unknown."""
    candidate = token.encode("utf-8")
    for known, entry in settings.site_token_entries.items():
        if secrets.compare_digest(candidate, known.encode("utf-8")):
            return entry
    return None


def site_for_token(token: Optional[str]) -> Optional[str]:
    """Return the site a valid token belongs to, or None when unknown/disabled.

    Used for attribution (per-site rate limiting); authorization still goes
    through :func:`verify_site_key`.
    """
    if not token:
        return None
    entry = _entry_for_token(token)
    return entry[0] if entry else None


def verify_site_key(
    x_site_key: Optional[str] = Header(default=None),
    origin: Optional[str] = Header(default=None),
) -> Optional[str]:
    """Validate the per-site key and return the site name it belongs to.

    Returns ``None`` when the feature is disabled (no `SITE_TOKENS` configured).
    Raises ``401`` when tokens are configured but the supplied key is missing or
    unknown, and ``403`` when the key is bound to origins and the request does
    not come from one of them.
    """
    entries = settings.site_token_entries
    if not entries:
        return None

    if not x_site_key:
        raise HTTPException(status_code=401, detail="Missing site API key.")

    entry = _entry_for_token(x_site_key)
    if entry is None:
        raise HTTPException(status_code=401, detail="Invalid site API key.")

    site, allowed_origins = entry
    if allowed_origins and (
        not origin or origin.rstrip("/") not in allowed_origins
    ):
        raise HTTPException(
            status_code=403,
            detail="Origin not allowed for this site key.",
        )
    return site
