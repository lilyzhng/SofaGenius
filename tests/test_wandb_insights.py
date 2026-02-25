"""Unit tests for W&B insight analysis functions.

Tests cover:
- _compute_summary_stats: initial/final/best value, improvement pct
- _detect_phases: phase segmentation via slope analysis
- _compute_convergence_speed: 90% improvement detection
- _detect_lr_schedule: LR shape classification
- _generate_trend_summary: narrative construction
"""

import math

import numpy as np
import pytest

from backend.tools.wandb_monitor import (
    _compute_summary_stats,
    _compute_convergence_speed,
    _detect_lr_schedule,
    _detect_phases,
    _generate_trend_summary,
)


# ---------------------------------------------------------------------------
# _compute_summary_stats
# ---------------------------------------------------------------------------

class TestComputeSummaryStats:
    def test_loss_basic(self):
        steps = list(range(10))
        vals = [2.0, 1.8, 1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.45, 0.4]
        stat = _compute_summary_stats("train/loss", steps, vals)
        assert stat.key == "train/loss"
        assert stat.initial_value == 2.0
        assert stat.final_value == 0.4
        assert stat.best_value == 0.4  # min for loss
        assert stat.improvement_pct == 80.0
        assert stat.total_points == 10

    def test_accuracy_metric(self):
        """For non-loss metrics, 'best' should be max."""
        steps = list(range(5))
        vals = [0.5, 0.6, 0.7, 0.65, 0.72]
        stat = _compute_summary_stats("accuracy", steps, vals)
        assert stat.best_value == 0.72  # max for non-loss

    def test_no_improvement(self):
        steps = list(range(5))
        vals = [1.0, 1.0, 1.0, 1.0, 1.0]
        stat = _compute_summary_stats("loss", steps, vals)
        assert stat.improvement_pct == 0.0

    def test_regression(self):
        """Loss going up should give negative improvement."""
        steps = list(range(5))
        vals = [0.5, 0.6, 0.7, 0.8, 1.0]
        stat = _compute_summary_stats("loss", steps, vals)
        assert stat.improvement_pct < 0

    def test_initial_zero(self):
        """Handle division by zero when initial value is 0."""
        steps = list(range(3))
        vals = [0.0, 0.5, 1.0]
        stat = _compute_summary_stats("loss", steps, vals)
        assert stat.improvement_pct == 0.0

    def test_nan_inf_cleaned(self):
        """NaN and Inf in values should be cleaned to 0."""
        steps = list(range(5))
        vals = [1.0, float("nan"), 0.5, float("inf"), 0.3]
        stat = _compute_summary_stats("loss", steps, vals)
        assert stat.total_points == 5
        assert not math.isnan(stat.final_value)
        assert not math.isinf(stat.final_value)


# ---------------------------------------------------------------------------
# _detect_phases
# ---------------------------------------------------------------------------

class TestDetectPhases:
    def test_typical_training_curve(self):
        """A typical loss curve: steep drop then plateau should produce 2+ phases."""
        n = 200
        steps = list(range(n))
        # Steep drop for first 60, gradual for next 60, flat for last 80
        steep = np.linspace(3.0, 1.0, 60)
        gradual = np.linspace(1.0, 0.5, 60)
        flat = np.full(80, 0.5) + np.random.normal(0, 0.005, 80)
        vals = list(np.concatenate([steep, gradual, flat]))
        phases = _detect_phases("loss", steps, vals)
        assert len(phases) >= 2
        # First phase should be warmup or active_learning
        assert phases[0].name in ("warmup", "active_learning")
        # All phases should have valid step ranges
        for p in phases:
            assert p.start_step <= p.end_step
            assert p.description != ""

    def test_short_series_returns_empty(self):
        """Very short series should return no phases."""
        steps = list(range(5))
        vals = [2.0, 1.5, 1.0, 0.8, 0.7]
        phases = _detect_phases("loss", steps, vals)
        assert phases == []

    def test_constant_series(self):
        """Constant values (zero range) should return empty."""
        steps = list(range(100))
        vals = [1.0] * 100
        phases = _detect_phases("loss", steps, vals)
        assert phases == []

    def test_phases_cover_full_range(self):
        """Phases should span from near the start to the end."""
        n = 300
        steps = list(range(n))
        vals = list(np.exp(-np.linspace(0, 5, n)) * 3 + 0.1)
        phases = _detect_phases("loss", steps, vals)
        if phases:
            assert phases[0].start_step <= 20  # starts near beginning
            assert phases[-1].end_step >= n - 20  # ends near end

    def test_no_duplicate_consecutive_phases(self):
        """Consecutive phases should not have the same name (they get merged)."""
        n = 200
        steps = list(range(n))
        vals = list(np.linspace(3.0, 0.3, n))
        phases = _detect_phases("loss", steps, vals)
        for i in range(1, len(phases)):
            assert phases[i].name != phases[i - 1].name


# ---------------------------------------------------------------------------
# _compute_convergence_speed
# ---------------------------------------------------------------------------

class TestComputeConvergenceSpeed:
    def test_fast_convergence(self):
        """90% improvement reached quickly."""
        steps = list(range(100))
        vals = list(np.exp(-np.linspace(0, 8, 100)) * 2 + 0.1)
        result = _compute_convergence_speed("loss", steps, vals)
        assert result is not None
        assert result.steps_to_90pct is not None
        assert result.steps_to_90pct < 50  # fast convergence
        assert result.efficiency_ratio is not None
        assert result.efficiency_ratio < 0.5

    def test_no_improvement(self):
        """Loss that doesn't decrease."""
        steps = list(range(100))
        vals = list(np.linspace(1.0, 2.0, 100))
        result = _compute_convergence_speed("loss", steps, vals)
        assert result is not None
        assert result.steps_to_90pct is None
        assert "No net improvement" in result.description

    def test_short_series(self):
        """Too few points should return None."""
        steps = [0, 1, 2]
        vals = [2.0, 1.0, 0.5]
        result = _compute_convergence_speed("loss", steps, vals)
        assert result is None

    def test_slow_convergence(self):
        """Linear decrease — 90% improvement at ~90% through training."""
        steps = list(range(100))
        vals = list(np.linspace(2.0, 0.2, 100))
        result = _compute_convergence_speed("loss", steps, vals)
        assert result is not None
        assert result.steps_to_90pct is not None
        # Linear: 90% improvement at ~step 90
        assert result.steps_to_90pct > 80


# ---------------------------------------------------------------------------
# _detect_lr_schedule
# ---------------------------------------------------------------------------

class TestDetectLrSchedule:
    def test_constant_lr(self):
        steps = list(range(100))
        vals = [3e-4] * 100
        result = _detect_lr_schedule(steps, vals)
        assert result is not None
        assert "Constant" in result

    def test_linear_decay(self):
        steps = list(range(100))
        vals = list(np.linspace(3e-4, 0, 100))
        result = _detect_lr_schedule(steps, vals)
        assert result is not None
        assert "decay" in result.lower() or "Linear" in result

    def test_cosine_decay(self):
        steps = list(range(100))
        vals = [3e-4 * 0.5 * (1 + math.cos(math.pi * i / 99)) for i in range(100)]
        result = _detect_lr_schedule(steps, vals)
        assert result is not None
        assert "osine" in result or "decay" in result.lower()

    def test_warmup_then_decay(self):
        steps = list(range(110))
        warmup = list(np.linspace(0, 3e-4, 10))
        decay = list(np.linspace(3e-4, 0, 100))
        vals = warmup + decay
        result = _detect_lr_schedule(steps, vals)
        assert result is not None
        assert "Warmup" in result or "decay" in result.lower()

    def test_too_few_points(self):
        steps = [0, 1, 2]
        vals = [1e-3, 1e-3, 1e-3]
        result = _detect_lr_schedule(steps, vals)
        assert result is None

    def test_step_schedule(self):
        """Step decay with discrete drops."""
        steps = list(range(100))
        vals = [3e-4] * 33 + [1e-4] * 33 + [3e-5] * 34
        result = _detect_lr_schedule(steps, vals)
        assert result is not None
        assert "tep" in result or "decay" in result.lower()


# ---------------------------------------------------------------------------
# _generate_trend_summary
# ---------------------------------------------------------------------------

class TestGenerateTrendSummary:
    def test_basic_summary(self):
        from backend.models import MetricStats, TrainingPhase, ConvergenceInfo

        stats = [MetricStats(
            key="train/loss",
            initial_value=2.5,
            final_value=0.4,
            best_value=0.35,
            improvement_pct=84.0,
            total_points=500,
        )]
        phases = [
            TrainingPhase(name="warmup", start_step=0, end_step=50, description=""),
            TrainingPhase(name="active_learning", start_step=51, end_step=200, description=""),
            TrainingPhase(name="convergence", start_step=201, end_step=500, description=""),
        ]
        convergence = ConvergenceInfo(
            metric="train/loss",
            steps_to_90pct=200,
            total_steps=500,
            efficiency_ratio=0.4,
            description="Reached 90% of total improvement in 200 steps (40% of training)",
        )

        summary = _generate_trend_summary(
            classified={"loss": ["train/loss"], "eval_loss": [], "grad": [], "lr": [], "other": []},
            raw_map={},
            stats=stats,
            phases=phases,
            convergence=convergence,
        )
        assert "2.5000" in summary
        assert "0.4000" in summary
        assert "84.0%" in summary
        assert "warmup" in summary
        assert "convergence" in summary

    def test_empty_data(self):
        summary = _generate_trend_summary(
            classified={"loss": [], "eval_loss": [], "grad": [], "lr": [], "other": []},
            raw_map={},
            stats=[],
            phases=[],
            convergence=None,
        )
        assert "Insufficient" in summary
