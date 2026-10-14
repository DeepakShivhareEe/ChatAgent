"""Per-site API key authorization for public endpoints.

When `SITE_TOKENS` is configured, the public `POST /chat` route requires a
matching `X-Site-Key` header carrying one of the configured tokens. When
`SITE_TOKENS` is empty the check is a no-op, so local/demo installs keep
working without configuration.
"""

import secrets
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings


def verify_site_key(x_site_key: Optional[str] = Header(default=None)) -> Optional[str]:
    """Validate the per-site key and return the site name it belongs to.

    Returns ``None`` when the feature is disabled (no `SITE_TOKENS` configured).
    Raises ``401`` when tokens are configured but the supplied key is missing or
    unknown.
    """
    tokens = settings.site_tokens_map
    if not tokens:
        return None

    if not x_site_key:
        raise HTTPException(status_code=401, detail="Missing site API key.")

    candidate = x_site_key.encode("utf-8")
    for token, site in tokens.items():
        if secrets.compare_digest(candidate, token.encode("utf-8")):
            return site

    raise HTTPException(status_code=401, detail="Invalid site API key.")
