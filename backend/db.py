"""Supabase database operations for profiles, sessions, messages, and cards."""

from __future__ import annotations

import logging
from typing import Any

from backend.auth import get_supabase

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def get_user_profile(user_id: str) -> dict[str, Any] | None:
    """Fetch a user's profile. Returns None if not found."""
    sb = get_supabase()
    result = sb.table("profiles").select("*").eq("id", user_id).execute()
    rows = result.data
    return rows[0] if rows else None


def update_user_profile(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update profile fields. Returns the updated profile."""
    sb = get_supabase()
    result = sb.table("profiles").update(updates).eq("id", user_id).execute()
    return result.data[0] if result.data else {}


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def create_session(user_id: str, title: str = "New Chat", preview: str = "") -> dict[str, Any]:
    """Create a new chat session. Returns the created row."""
    sb = get_supabase()
    result = sb.table("sessions").insert({
        "user_id": user_id,
        "title": title,
        "preview": preview[:200],
    }).execute()
    return result.data[0] if result.data else {}


def list_sessions(user_id: str) -> list[dict[str, Any]]:
    """List all sessions for a user, most recent first."""
    sb = get_supabase()
    result = (
        sb.table("sessions")
        .select("id, title, preview, created_at, updated_at")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data or []


def update_session(session_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Update session fields (e.g. title, preview)."""
    sb = get_supabase()
    result = sb.table("sessions").update(updates).eq("id", session_id).execute()
    return result.data[0] if result.data else {}


def delete_session(session_id: str) -> None:
    """Delete a session and cascade to messages + cards."""
    sb = get_supabase()
    sb.table("sessions").delete().eq("id", session_id).execute()


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def get_session_messages(session_id: str) -> list[dict[str, Any]]:
    """Get all messages for a session, ordered chronologically."""
    sb = get_supabase()
    result = (
        sb.table("messages")
        .select("id, role, content, segments, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def save_message(
    session_id: str,
    role: str,
    content: str,
    segments: list[dict] | None = None,
) -> dict[str, Any]:
    """Save a message to a session."""
    sb = get_supabase()
    row: dict[str, Any] = {
        "session_id": session_id,
        "role": role,
        "content": content,
    }
    if segments is not None:
        row["segments"] = segments
    result = sb.table("messages").insert(row).execute()
    return result.data[0] if result.data else {}


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def get_session_cards(session_id: str) -> list[dict[str, Any]]:
    """Get all cards for a session, ordered chronologically."""
    sb = get_supabase()
    result = (
        sb.table("cards")
        .select("id, card_type, title, data, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def save_card(
    session_id: str,
    card_type: str,
    title: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    """Save a card to a session."""
    sb = get_supabase()
    result = sb.table("cards").insert({
        "session_id": session_id,
        "card_type": card_type,
        "title": title,
        "data": data,
    }).execute()
    return result.data[0] if result.data else {}
