"""JWT verification and FastAPI auth dependency for Supabase Auth."""

from __future__ import annotations

import os
import logging

from fastapi import Request, HTTPException
from supabase import create_client, Client

log = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Singleton Supabase client using the service role key."""
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        _supabase_client = create_client(url, key)
    return _supabase_client


async def get_current_user(request: Request) -> str:
    """FastAPI dependency — extracts user_id from Bearer token.

    Uses the Supabase client to verify the token server-side,
    which works with both legacy HS256 and new ECC signing keys.

    Returns the user's UUID string. Raises 401 if missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        sb = get_supabase()
        user_response = sb.auth.get_user(token)
        user = user_response.user
        if not user or not user.id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user.id)
    except HTTPException:
        raise
    except Exception as e:
        log.warning("Auth verification failed: %s", e)
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
