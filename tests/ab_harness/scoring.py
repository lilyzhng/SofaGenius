"""Five-dimension scoring rubric for A/B quality comparison.

Each dimension scores 0.0-1.0 and is weighted to produce an aggregate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.models import ConvergenceInfo, MetricStats, RunInsights, TrainingPhase

from .scenarios import Scenario


@dataclass
class AnalysisResult:
    """Output of a code path for a single scenario."""

    anomaly_types: list[str]
    anomaly_count: int
    insights: RunInsights
    elapsed_ms: float
    error: str | None = None


@dataclass
class DimensionScores:
    """Per-dimension scores for a single scenario."""

    correctness: float = 0.0
    coverage: float = 0.0
    informativeness: float = 0.0
    robustness: float = 0.0
    performance: float = 0.0

    @property
    def aggregate(self) -> float:
        return (
            self.correctness * WEIGHTS["correctness"]
            + self.coverage * WEIGHTS["coverage"]
            + self.informativeness * WEIGHTS["informativeness"]
            + self.robustness * WEIGHTS["robustness"]
            + self.performance * WEIGHTS["performance"]
        )


WEIGHTS = {
    "correctness": 0.30,
    "coverage": 0.25,
    "informativeness": 0.20,
    "robustness": 0.15,
    "performance": 0.10,
}

# Pass thresholds
PASS_THRESHOLD = 0.70
FLOOR_THRESHOLD = 0.40
PASS_RATE_THRESHOLD = 0.85
REGRESSION_TOLERANCE = 0.02

# ---------------------------------------------------------------------------
# Capability checks — extensibility point for new features
# ---------------------------------------------------------------------------

CAPABILITY_CHECKS: dict[str, callable] = {
    "summary_stats": lambda r: len(r.metric_stats) > 0,
    "phase_detection": lambda r: len(r.phases) > 0,
    "convergence_speed": lambda r: r.convergence is not None,
    "lr_classification": lambda r: r.lr_analysis is not None,
    "anomaly_detection": lambda r: True,  # always present
    "trend_summary": lambda r: r.trend_summary and "Insufficient" not in r.trend_summary,
}


# ---------------------------------------------------------------------------
# Dimension scorers
# ---------------------------------------------------------------------------


def score_correctness(scenario: Scenario, result: AnalysisResult) -> float:
    """Anomaly recall + phase accuracy vs ground truth. Penalizes false positives on clean."""
    if result.error:
        return 0.0

    score_parts: list[float] = []

    # --- Anomaly recall ---
    expected = set(scenario.expected_anomaly_types)
    detected = set(result.anomaly_types)

    if expected:
        recall = len(expected & detected) / len(expected)
        score_parts.append(recall)
    else:
        # Clean scenario: penalize false positives
        # data_issue on NaN-containing metrics and plateau are acceptable false positives
        # on some clean scenarios, so we use a lenient penalty
        if detected:
            penalty = min(len(detected) * 0.15, 0.5)
            score_parts.append(1.0 - penalty)
        else:
            score_parts.append(1.0)

    # --- Phase accuracy ---
    expected_phases = set(scenario.expected_phases)
    detected_phases = {p.name for p in result.insights.phases}

    if expected_phases:
        if detected_phases:
            overlap = len(expected_phases & detected_phases)
            precision = overlap / len(detected_phases) if detected_phases else 0
            recall = overlap / len(expected_phases)
            phase_score = (precision + recall) / 2
        else:
            phase_score = 0.0
        score_parts.append(phase_score)
    elif scenario.is_edge_case:
        # Edge cases with no expected phases: don't penalize
        score_parts.append(1.0)

    return sum(score_parts) / len(score_parts) if score_parts else 0.0


def score_coverage(scenario: Scenario, result: AnalysisResult) -> float:
    """How many capabilities fire? Each entry in CAPABILITY_CHECKS is tested."""
    if result.error:
        return 0.0

    insights = result.insights
    fired = sum(1 for check in CAPABILITY_CHECKS.values() if check(insights))
    return fired / len(CAPABILITY_CHECKS)


def score_informativeness(scenario: Scenario, result: AnalysisResult) -> float:
    """Are outputs actionable? Non-trivial summary, populated descriptions."""
    if result.error:
        return 0.0

    insights = result.insights
    checks: list[bool] = []

    # Trend summary is non-empty and non-generic
    if insights.trend_summary:
        checks.append(len(insights.trend_summary) > 20)
        checks.append("Insufficient" not in insights.trend_summary)
    else:
        checks.extend([False, False])

    # Metric stats have real values
    if insights.metric_stats:
        checks.append(any(s.total_points > 0 for s in insights.metric_stats))
    else:
        checks.append(False)

    # Phases have descriptions
    if insights.phases:
        checks.append(all(p.description for p in insights.phases))
    elif not scenario.is_edge_case:
        checks.append(False)
    else:
        checks.append(True)

    # Convergence has description
    if insights.convergence:
        checks.append(bool(insights.convergence.description))
    elif scenario.should_converge:
        checks.append(False)
    else:
        checks.append(True)

    return sum(checks) / len(checks) if checks else 0.0


def score_robustness(scenario: Scenario, result: AnalysisResult) -> float:
    """Edge cases survive without crash, NaN, or Inf in outputs."""
    if result.error:
        return 0.0

    insights = result.insights

    # Check for NaN/Inf in numeric outputs
    def is_clean(v: float | None) -> bool:
        if v is None:
            return True
        return not (math.isnan(v) or math.isinf(v))

    checks: list[bool] = [True]  # Start with "no crash" = True

    for stat in insights.metric_stats:
        checks.append(is_clean(stat.initial_value))
        checks.append(is_clean(stat.final_value))
        checks.append(is_clean(stat.best_value))
        checks.append(is_clean(stat.improvement_pct))

    if insights.convergence:
        checks.append(is_clean(insights.convergence.efficiency_ratio))

    return sum(checks) / len(checks) if checks else 1.0


def score_performance(scenario: Scenario, result: AnalysisResult) -> float:
    """Latency scoring: < 100ms = 1.0, degrades linearly to 0.0 at 500ms."""
    ms = result.elapsed_ms
    if ms <= 100:
        return 1.0
    if ms >= 500:
        return 0.0
    return 1.0 - (ms - 100) / 400


def score_scenario(scenario: Scenario, result: AnalysisResult) -> DimensionScores:
    """Compute all dimension scores for a single scenario."""
    return DimensionScores(
        correctness=score_correctness(scenario, result),
        coverage=score_coverage(scenario, result),
        informativeness=score_informativeness(scenario, result),
        robustness=score_robustness(scenario, result),
        performance=score_performance(scenario, result),
    )
