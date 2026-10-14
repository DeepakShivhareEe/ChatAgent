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

import secrets
from typing import Optional

from fastapi import Header, HTTPException

from app.config import settings


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

    candidate = x_site_key.encode("utf-8")
    for token, (site, allowed_origins) in entries.items():
        if secrets.compare_digest(candidate, token.encode("utf-8")):
            if allowed_origins and (
                not origin or origin.rstrip("/") not in allowed_origins
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Origin not allowed for this site key.",
                )
            return site

    raise HTTPException(status_code=401, detail="Invalid site API key.")
