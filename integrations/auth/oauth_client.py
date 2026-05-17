"""OAuth 2.0 client-credentials flow stub.

In production: posts client_id + client_secret to the customer's Epic
auth endpoint, gets a bearer token, caches it until expiry. Refreshes
silently.

Here: returns a fake token + records the call. The shape is right so
ehr_adapter.py can pretend to authenticate without real Epic credentials.
"""
from __future__ import annotations
import os
import time
from dataclasses import dataclass


@dataclass
class OAuthToken:
    access_token: str
    expires_at: float  # epoch seconds
    scope: str


_CACHE: OAuthToken | None = None


def get_access_token(
    *,
    token_url: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    scope: str = "system/Patient.read system/Encounter.read",
) -> OAuthToken:
    """
    Return a cached or newly-fetched OAuth token.

    In production:
        response = httpx.post(token_url, data={...}, auth=(client_id, client_secret))
        token = response.json()["access_token"]
        expires_in = response.json()["expires_in"]

    Here: returns a deterministic fake token. Honest stub.
    """
    global _CACHE
    if _CACHE and _CACHE.expires_at > time.time() + 60:
        return _CACHE

    token_url = token_url or os.environ.get("EHR_TOKEN_URL", "https://fake.example/oauth/token")
    client_id = client_id or os.environ.get("EHR_CLIENT_ID", "demo-client")

    # In real engagement: real HTTP call here.
    _CACHE = OAuthToken(
        access_token=f"fake-bearer-{int(time.time())}",
        expires_at=time.time() + 3600,
        scope=scope,
    )
    return _CACHE


def revoke_token() -> None:
    """Wipe the in-process cache. Call on auth failure."""
    global _CACHE
    _CACHE = None
