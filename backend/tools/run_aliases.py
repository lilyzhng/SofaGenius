"""Friendly run alias generator — assigns voice-friendly names to W&B runs."""

from __future__ import annotations

import random

THEMES = [
    "Strawberry", "Blueberry", "Espresso", "Moonlight", "Coral",
    "Sage", "Amber", "Crimson", "Glacier", "Dusk",
    "Velvet", "Maple", "Cobalt", "Cedar", "Orchid",
    "Peach", "Slate", "Ember", "Jade", "Hazel",
]


def pick_session_theme() -> str:
    """Pick a random theme word for this session's aliases."""
    return random.choice(THEMES)


def generate_alias(theme: str, counter: int) -> str:
    """Generate a voice-friendly alias like 'Strawberry-1'."""
    return f"{theme}-{counter}"
