"""Baseline vs candidate code path wrappers.

Both call real production functions from wandb_monitor.py — no mocking
of analysis logic. The difference is which functions are executed.
"""

from __future__ import annotations

from backend.models import (
    Anomaly,
    ConvergenceInfo,
    MetricStats,
    RunInsights,
    Severity,
    TrainingPhase,
)
from backend.tools.wandb_monitor import (
    _classify_key,
    _clean,
    _compute_convergence_speed,
    _compute_summary_stats,
    _deduplicate,
    _detect_divergence,
    _detect_grad_explosion,
    _detect_lr_schedule,
    _detect_nans,
    _detect_oscillation,
    _detect_overfitting,
    _detect_phases,
    _detect_plateau,
    _detect_spikes,
    _generate_trend_summary,
)

from .scenarios import Scenario
from .scoring import AnalysisResult


def _run_anomaly_detectors(scenario: Scenario) -> list[Anomaly]:
    """Run all anomaly detectors on scenario metrics, matching production logic."""
    classified: dict[str, list] = {"loss": [], "eval_loss": [], "grad": [], "lr": [], "other": []}
    raw_map: dict[str, tuple[list[int], list[float]]] = {}

    for m in scenario.metrics:
        category = _classify_key(m.key)
        classified[category].append(m.key)
        raw_map[m.key] = (m.steps, m.values)

    all_anomalies: list[Anomaly] = []

    for key in classified["loss"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) and not (isinstance(v, float) and (v != v or abs(v) == float("inf"))) else 0.0 for v in vals]
        all_anomalies.extend(_detect_spikes(key, steps, floats))
        all_anomalies.extend(_detect_divergence(key, steps, floats))
        all_anomalies.extend(_detect_oscillation(key, steps, floats))
        all_anomalies.extend(_detect_plateau(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    for key in classified["eval_loss"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) and not (isinstance(v, float) and (v != v or abs(v) == float("inf"))) else 0.0 for v in vals]
        all_anomalies.extend(_detect_spikes(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    for key in classified["grad"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) and not (isinstance(v, float) and (v != v or abs(v) == float("inf"))) else 0.0 for v in vals]
        all_anomalies.extend(_detect_grad_explosion(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    for key in classified["other"]:
        steps, vals = raw_map[key]
        all_anomalies.extend(_detect_nans(key, steps, vals))

    # Overfitting detection
    if classified["loss"] and classified["eval_loss"]:
        t_key = classified["loss"][0]
        e_key = classified["eval_loss"][0]
        t_steps, t_vals = raw_map[t_key]
        e_steps, e_vals = raw_map[e_key]
        t_floats = [float(v) if isinstance(v, (int, float)) else 0.0 for v in t_vals]
        e_floats = [float(v) if isinstance(v, (int, float)) else 0.0 for v in e_vals]
        all_anomalies.extend(_detect_overfitting(t_steps, t_floats, e_steps, e_floats))

    return _deduplicate(all_anomalies)


def baseline_code_path(scenario: Scenario) -> AnalysisResult:
    """Baseline: anomaly detectors only, empty insights."""
    anomalies = _run_anomaly_detectors(scenario)
    return AnalysisResult(
        anomaly_types=list({a.type for a in anomalies}),
        anomaly_count=len(anomalies),
        insights=RunInsights(
            trend_summary="",
            metric_stats=[],
            phases=[],
            convergence=None,
            lr_analysis=None,
        ),
        elapsed_ms=0.0,
    )


def full_analysis_code_path(scenario: Scenario) -> AnalysisResult:
    """Candidate: anomaly detectors + all insight functions."""
    anomalies = _run_anomaly_detectors(scenario)

    # Classify keys (mirrors production logic)
    classified: dict[str, list[str]] = {"loss": [], "eval_loss": [], "grad": [], "lr": [], "other": []}
    raw_map: dict[str, tuple[list[int], list[float]]] = {}

    for m in scenario.metrics:
        category = _classify_key(m.key)
        classified[category].append(m.key)
        raw_map[m.key] = (m.steps, m.values)

    # Summary stats for all metrics
    all_stats: list[MetricStats] = []
    for m in scenario.metrics:
        floats = _clean([float(v) if isinstance(v, (int, float)) else 0.0 for v in m.values])
        if len(floats) >= 2:
            all_stats.append(_compute_summary_stats(m.key, m.steps, floats))

    # Phase detection on primary loss
    phases: list[TrainingPhase] = []
    primary_loss_key = classified["loss"][0] if classified["loss"] else None
    if primary_loss_key and primary_loss_key in raw_map:
        steps, vals = raw_map[primary_loss_key]
        floats = _clean([float(v) if isinstance(v, (int, float)) else 0.0 for v in vals])
        phases = _detect_phases(primary_loss_key, steps, floats)

    # Convergence speed on primary loss
    convergence: ConvergenceInfo | None = None
    if primary_loss_key and primary_loss_key in raw_map:
        steps, vals = raw_map[primary_loss_key]
        floats = _clean([float(v) if isinstance(v, (int, float)) else 0.0 for v in vals])
        convergence = _compute_convergence_speed(primary_loss_key, steps, floats)

    # LR schedule detection
    lr_analysis: str | None = None
    if classified["lr"]:
        lr_key = classified["lr"][0]
        if lr_key in raw_map:
            steps, vals = raw_map[lr_key]
            floats = _clean([float(v) if isinstance(v, (int, float)) else 0.0 for v in vals])
            lr_analysis = _detect_lr_schedule(steps, floats)

    trend_summary = _generate_trend_summary(classified, raw_map, all_stats, phases, convergence)

    insights = RunInsights(
        trend_summary=trend_summary,
        metric_stats=all_stats,
        phases=phases,
        convergence=convergence,
        lr_analysis=lr_analysis,
    )

    return AnalysisResult(
        anomaly_types=list({a.type for a in anomalies}),
        anomaly_count=len(anomalies),
        insights=insights,
        elapsed_ms=0.0,
    )
