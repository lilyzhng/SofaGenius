"""Unit tests for run alias system.

Tests cover:
- Theme picker and alias generation
- Alias assignment (idempotent, session-scoped)
- Alias resolution from user text
- Session isolation
- Alias context building for system prompt
"""

import pytest

from backend.tools.run_aliases import THEMES, generate_alias, pick_session_theme
from backend.orchestrator import (
    assign_run_alias,
    resolve_alias,
    _build_alias_context,
    _get_session_context,
    _session_contexts,
)


@pytest.fixture(autouse=True)
def _clean_session_contexts():
    """Ensure session state is clean before each test."""
    _session_contexts.clear()
    yield
    _session_contexts.clear()


# ---------------------------------------------------------------------------
# run_aliases module
# ---------------------------------------------------------------------------

class TestAliasGeneration:
    def test_pick_session_theme(self):
        theme = pick_session_theme()
        assert theme in THEMES

    def test_generate_alias(self):
        alias = generate_alias("Strawberry", 1)
        assert alias == "Strawberry-1"

    def test_generate_alias_counter(self):
        alias = generate_alias("Espresso", 42)
        assert alias == "Espresso-42"


# ---------------------------------------------------------------------------
# Orchestrator alias management
# ---------------------------------------------------------------------------

class TestAssignRunAlias:
    def test_basic_assignment(self):
        alias = assign_run_alias("s1", "run123", "lively-wave-42", "entity/project")
        assert "-" in alias  # e.g. "Strawberry-1"
        # Theme word should be from THEMES
        theme_word = alias.rsplit("-", 1)[0]
        assert theme_word in THEMES

    def test_idempotent(self):
        """Assigning the same run twice returns the same alias."""
        a1 = assign_run_alias("s1", "run123", "lively-wave-42", "entity/proj")
        a2 = assign_run_alias("s1", "run123", "lively-wave-42", "entity/proj")
        assert a1 == a2

    def test_different_runs_different_aliases(self):
        a1 = assign_run_alias("s1", "run1", "run-one", "e/p")
        a2 = assign_run_alias("s1", "run2", "run-two", "e/p")
        assert a1 != a2

    def test_counter_increments(self):
        a1 = assign_run_alias("s1", "r1", "n1", "e/p")
        a2 = assign_run_alias("s1", "r2", "n2", "e/p")
        # Same theme, sequential counters
        num1 = int(a1.rsplit("-", 1)[1])
        num2 = int(a2.rsplit("-", 1)[1])
        assert num2 == num1 + 1

    def test_session_isolation(self):
        """Different sessions get independent alias spaces."""
        a1 = assign_run_alias("session_A", "run1", "n1", "e/p")
        a2 = assign_run_alias("session_B", "run1", "n1", "e/p")
        # Both sessions may assign the same run but have independent contexts
        # The aliases might differ if themes differ, or be the same if themes match
        # Key: they should be independently tracked
        ctx_a = _get_session_context("session_A")
        ctx_b = _get_session_context("session_B")
        assert "run_aliases" in ctx_a
        assert "run_aliases" in ctx_b
        assert a1 in ctx_a["run_aliases"]
        assert a2 in ctx_b["run_aliases"]


class TestResolveAlias:
    def test_resolve_exact(self):
        alias = assign_run_alias("s1", "abc123", "my-run", "e/p")
        result = resolve_alias("s1", f"check {alias}")
        assert result is not None
        assert result["run_id"] == "abc123"
        assert result["alias"] == alias

    def test_resolve_case_insensitive(self):
        alias = assign_run_alias("s1", "abc123", "my-run", "e/p")
        result = resolve_alias("s1", f"check {alias.lower()}")
        assert result is not None
        assert result["run_id"] == "abc123"

    def test_resolve_not_found(self):
        assign_run_alias("s1", "abc123", "my-run", "e/p")
        result = resolve_alias("s1", "check some-other-thing")
        assert result is None

    def test_resolve_empty_session(self):
        result = resolve_alias("empty_session", "check Strawberry-1")
        assert result is None


class TestBuildAliasContext:
    def test_empty(self):
        ctx = _build_alias_context("empty_session")
        assert ctx == ""

    def test_with_aliases(self):
        assign_run_alias("s1", "run1", "fast-run", "e/p1")
        assign_run_alias("s1", "run2", "slow-run", "e/p2")
        ctx = _build_alias_context("s1")
        assert "RUN ALIASES" in ctx
        assert "fast-run" in ctx
        assert "slow-run" in ctx
        assert "run1" in ctx
        assert "run2" in ctx
