"""W&B monitoring tools with anomaly detection heuristics."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import wandb

from backend.models import (
    Action,
    Anomaly,
    ComparisonCard,
    ComparisonSeries,
    HealthStatus,
    MetricPoint,
    MetricSeries,
    RiskLevel,
    RunInfo,
    RunSummary,
    Severity,
    WandBHealthCard,
)

# ---------------------------------------------------------------------------
# Anomaly detection config
# ---------------------------------------------------------------------------
SPIKE_WINDOW = 50
SPIKE_SIGMA = 3.0
DIVERGE_WINDOW = 10
OSCILLATION_WINDOW = 20
OSCILLATION_THRESHOLD = 0.5
GRAD_NORM_THRESHOLD = 100.0
OVERFIT_WINDOW = 5
PLATEAU_WINDOW = 50
PLATEAU_EPSILON = 1e-5


def _clean(vals: list[float]) -> list[float]:
    """Replace NaN/Inf with 0."""
    return [0.0 if (math.isnan(v) or math.isinf(v)) else v for v in vals]


# ---------------------------------------------------------------------------
# Anomaly detectors
# ---------------------------------------------------------------------------

def _detect_spikes(key: str, steps: list[int], vals: list[float]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    vals = _clean(vals)
    for i in range(SPIKE_WINDOW, len(vals)):
        window = vals[i - SPIKE_WINDOW : i]
        mean = np.mean(window)
        std = np.std(window)
        if std > 0 and vals[i] > mean + SPIKE_SIGMA * std:
            anomalies.append(Anomaly(
                type="loss_spike",
                severity=Severity.critical if vals[i] > mean + 5 * std else Severity.warning,
                step=steps[i],
                metric=key,
                message=f"Spike detected: {key}={vals[i]:.4f} (mean={mean:.4f}, +{SPIKE_SIGMA}\u03c3={mean + SPIKE_SIGMA * std:.4f})",
                value=vals[i],
                threshold=mean + SPIKE_SIGMA * std,
            ))
    return anomalies


def _detect_divergence(key: str, steps: list[int], vals: list[float]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    vals = _clean(vals)
    if len(vals) < DIVERGE_WINDOW:
        return anomalies
    for i in range(DIVERGE_WINDOW, len(vals)):
        window = vals[i - DIVERGE_WINDOW : i + 1]
        if all(window[j] < window[j + 1] for j in range(len(window) - 1)):
            anomalies.append(Anomaly(
                type="divergence",
                severity=Severity.critical,
                step=steps[i],
                metric=key,
                message=f"Monotonic increase in {key} for {DIVERGE_WINDOW} steps (diverging)",
                value=vals[i],
            ))
    return anomalies


def _detect_oscillation(key: str, steps: list[int], vals: list[float]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    vals = _clean(vals)
    if len(vals) < OSCILLATION_WINDOW:
        return anomalies
    for i in range(OSCILLATION_WINDOW, len(vals)):
        window = vals[i - OSCILLATION_WINDOW : i]
        var = float(np.var(window))
        if var > OSCILLATION_THRESHOLD:
            anomalies.append(Anomaly(
                type="oscillation",
                severity=Severity.warning,
                step=steps[i],
                metric=key,
                message=f"High variance in {key}: var={var:.4f} > {OSCILLATION_THRESHOLD}",
                value=var,
                threshold=OSCILLATION_THRESHOLD,
            ))
    return anomalies


def _detect_grad_explosion(key: str, steps: list[int], vals: list[float]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    vals = _clean(vals)
    for i, v in enumerate(vals):
        if v > GRAD_NORM_THRESHOLD:
            anomalies.append(Anomaly(
                type="gradient_explosion",
                severity=Severity.critical,
                step=steps[i],
                metric=key,
                message=f"Gradient norm explosion: {key}={v:.2f} > {GRAD_NORM_THRESHOLD}",
                value=v,
                threshold=GRAD_NORM_THRESHOLD,
            ))
    return anomalies


def _detect_overfitting(
    train_steps: list[int],
    train_vals: list[float],
    eval_steps: list[int],
    eval_vals: list[float],
) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    train_vals = _clean(train_vals)
    eval_vals = _clean(eval_vals)
    if len(eval_vals) < OVERFIT_WINDOW:
        return anomalies

    # Align eval points with closest train points
    for i in range(OVERFIT_WINDOW, len(eval_vals)):
        eval_window = eval_vals[i - OVERFIT_WINDOW : i + 1]
        train_window = train_vals[max(0, i - OVERFIT_WINDOW) : i + 1] if i < len(train_vals) else []
        if len(train_window) < OVERFIT_WINDOW:
            continue
        train_decreasing = all(train_window[j] >= train_window[j + 1] for j in range(len(train_window) - 1))
        eval_increasing = all(eval_window[j] <= eval_window[j + 1] for j in range(len(eval_window) - 1))
        if train_decreasing and eval_increasing:
            anomalies.append(Anomaly(
                type="overfitting",
                severity=Severity.warning,
                step=eval_steps[i],
                metric="train_loss vs eval_loss",
                message=f"Overfitting detected: train_loss decreasing while eval_loss increasing for {OVERFIT_WINDOW} eval points",
                value=eval_vals[i],
            ))
    return anomalies


def _detect_plateau(key: str, steps: list[int], vals: list[float]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    vals = _clean(vals)
    if len(vals) < PLATEAU_WINDOW:
        return anomalies
    for i in range(PLATEAU_WINDOW, len(vals)):
        window = vals[i - PLATEAU_WINDOW : i + 1]
        improvement = abs(window[-1] - window[0])
        if improvement < PLATEAU_EPSILON:
            anomalies.append(Anomaly(
                type="plateau",
                severity=Severity.info,
                step=steps[i],
                metric=key,
                message=f"Plateau in {key}: improvement={improvement:.6f} < {PLATEAU_EPSILON} over {PLATEAU_WINDOW} steps",
                value=improvement,
                threshold=PLATEAU_EPSILON,
            ))
    return anomalies


def _detect_nans(key: str, steps: list[int], raw_vals: list[Any]) -> list[Anomaly]:
    anomalies: list[Anomaly] = []
    for i, v in enumerate(raw_vals):
        if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
            anomalies.append(Anomaly(
                type="data_issue",
                severity=Severity.critical,
                step=steps[i],
                metric=key,
                message=f"NaN/Inf detected in {key} at step {steps[i]}",
            ))
    return anomalies


# ---------------------------------------------------------------------------
# Deduplicate anomalies — keep at most one per type+metric window
# ---------------------------------------------------------------------------

def _deduplicate(anomalies: list[Anomaly], step_gap: int = 50) -> list[Anomaly]:
    seen: dict[str, int] = {}
    result: list[Anomaly] = []
    for a in sorted(anomalies, key=lambda x: x.step):
        key = f"{a.type}:{a.metric}"
        if key in seen and a.step - seen[key] < step_gap:
            continue
        seen[key] = a.step
        result.append(a)
    return result


# ---------------------------------------------------------------------------
# Entity / project resolution
# ---------------------------------------------------------------------------

def _resolve_entity_project(api: Any, entity_project: str | None = None) -> str:
    """Resolve entity/project path. If only project given, prepend default entity."""
    if entity_project and "/" in entity_project:
        return entity_project
    entity = api.default_entity
    if entity_project:
        return f"{entity}/{entity_project}"
    return entity


# ---------------------------------------------------------------------------
# Public tool functions
# ---------------------------------------------------------------------------

def get_wandb_info() -> str:
    """Get the authenticated W&B user info and list their projects.

    Returns the username and recent projects so the agent can auto-resolve
    without asking the user.
    """
    api = wandb.Api()
    entity = api.default_entity
    projects = [
        {"name": p.name, "entity": p.entity, "url": p.url}
        for p in api.projects(entity)
    ]
    return json.dumps({
        "entity": entity,
        "projects": projects[:20],
    }, indent=2)


def list_wandb_runs(entity_project: str | None = None, limit: int = 10) -> str:
    """List recent W&B runs for a project.

    Args:
        entity_project: W&B entity/project path, e.g. "myteam/my-project".
                        If only a project name is given, the authenticated user's entity is used.
                        If omitted entirely, the latest project is used.
        limit: Maximum number of runs to return
    """
    api = wandb.Api()

    # If no project specified, find the most recent one
    if not entity_project:
        entity = api.default_entity
        projects = list(api.projects(entity))
        if not projects:
            return json.dumps({"error": "No projects found for your account"})
        entity_project = f"{entity}/{projects[0].name}"
    else:
        entity_project = _resolve_entity_project(api, entity_project)

    runs = api.runs(entity_project, per_page=limit)
    summaries: list[dict] = []
    for run in runs:
        summary_metrics = {}
        for k, v in (run.summary or {}).items():
            if isinstance(v, (int, float)) and not math.isnan(v):
                summary_metrics[k] = round(v, 6)
        summaries.append(RunSummary(
            name=run.name,
            id=run.id,
            state=run.state,
            metrics=summary_metrics,
            url=run.url,
        ).model_dump())
    return json.dumps(summaries, indent=2)


def _discover_metric_keys(run: Any) -> list[str]:
    """Auto-discover numeric metric keys from actual run history (not just summary).

    Scans a small history sample to find columns that have real time-series data,
    since run.summary can contain aggregate keys that don't exist in history.
    """
    SKIP_PREFIXES = ("_", "system/", "system.")
    SKIP_EXACT = {"_step", "_runtime", "_timestamp", "_wandb"}

    # Pull a small sample of history to see what columns actually exist
    try:
        sample = run.history(samples=5)
    except Exception:
        sample = None

    keys: list[str] = []
    if sample is not None and not sample.empty:
        for col in sample.columns:
            if col in SKIP_EXACT or any(col.startswith(p) for p in SKIP_PREFIXES):
                continue
            # Check that at least one value is numeric and not all NaN
            col_data = sample[col].dropna()
            if len(col_data) > 0 and all(isinstance(v, (int, float)) for v in col_data):
                keys.append(col)

    # Fallback: also check summary if history gave us nothing
    if not keys:
        for k, v in (run.summary or {}).items():
            if k in SKIP_EXACT or any(k.startswith(p) for p in SKIP_PREFIXES):
                continue
            if isinstance(v, (int, float)):
                keys.append(k)

    return sorted(keys)


# Patterns for classifying metric keys
_LOSS_PATTERNS = ["loss", "train_loss", "train/loss", "training_loss"]
_EVAL_LOSS_PATTERNS = ["eval_loss", "eval/loss", "val_loss", "val/loss", "validation_loss"]
_GRAD_PATTERNS = ["grad_norm", "grad/norm", "gradient_norm", "train/grad_norm"]
_LR_PATTERNS = ["learning_rate", "lr", "train/learning_rate", "train/lr"]


def _classify_key(key: str) -> str:
    """Classify a metric key into a category for anomaly detection."""
    key_lower = key.lower()
    for p in _EVAL_LOSS_PATTERNS:
        if p in key_lower:
            return "eval_loss"
    for p in _LOSS_PATTERNS:
        if p in key_lower:
            return "loss"
    for p in _GRAD_PATTERNS:
        if p in key_lower:
            return "grad"
    for p in _LR_PATTERNS:
        if p in key_lower:
            return "lr"
    return "other"


def get_run_metrics(entity_project: str, run_id: str, keys: list[str] | None = None, max_samples: int = 500) -> str:
    """Fetch metric time series for a W&B run.

    Args:
        entity_project: W&B entity/project path (or just project name)
        run_id: The run ID
        keys: Specific metric keys to fetch. If None, auto-discovers all numeric metrics.
        max_samples: Maximum number of sample points
    """
    api = wandb.Api()
    entity_project = _resolve_entity_project(api, entity_project)
    run = api.run(f"{entity_project}/{run_id}")
    if keys is None:
        keys = _discover_metric_keys(run)

    if not keys:
        return json.dumps([])

    history = run.history(samples=max_samples, keys=keys)
    series: list[dict] = []
    for key in keys:
        if key not in history.columns:
            continue
        col = history[["_step", key]].dropna()
        points = [
            MetricPoint(step=int(row["_step"]), value=float(row[key]))
            for _, row in col.iterrows()
        ]
        if points:
            series.append(MetricSeries(key=key, values=points).model_dump())
    return json.dumps(series, indent=2)


def analyze_run_health(entity_project: str, run_id: str) -> str:
    """Analyze a W&B run's health: fetch metrics, detect anomalies, return a Health Card.

    Args:
        entity_project: W&B entity/project path (or just project name)
        run_id: The run ID to analyze
    """
    api = wandb.Api()
    entity_project = _resolve_entity_project(api, entity_project)
    run = api.run(f"{entity_project}/{run_id}")

    # Auto-discover all numeric metric keys from actual history
    metric_keys = _discover_metric_keys(run)
    print(f"[wandb_monitor] Discovered metric keys: {metric_keys}")

    if not metric_keys:
        # Fallback: try a broad history sample to find keys
        sample = run.history(samples=1)
        metric_keys = [
            c for c in sample.columns
            if not c.startswith("_") and c not in {"_step", "_runtime", "_timestamp"}
        ]
        print(f"[wandb_monitor] Fallback keys from history columns: {metric_keys}")

    history = run.history(samples=500, keys=metric_keys) if metric_keys else None
    if history is not None:
        print(f"[wandb_monitor] History shape: {history.shape}, columns: {list(history.columns)}")
    else:
        print("[wandb_monitor] History is None — no data fetched")

    # Build metric series
    series_map: dict[str, MetricSeries] = {}
    raw_map: dict[str, tuple[list[int], list[Any]]] = {}
    for key in metric_keys:
        if history is None or key not in history.columns:
            continue
        col = history[["_step", key]].dropna()
        steps = [int(r["_step"]) for _, r in col.iterrows()]
        vals = [r[key] for _, r in col.iterrows()]
        if not steps:
            continue
        raw_map[key] = (steps, vals)
        points = [MetricPoint(step=s, value=float(v) if isinstance(v, (int, float)) and not (math.isnan(v) or math.isinf(v)) else 0.0) for s, v in zip(steps, vals)]
        if points:
            series_map[key] = MetricSeries(key=key, values=points)

    print(f"[wandb_monitor] Built series for: {list(series_map.keys())} ({sum(len(s.values) for s in series_map.values())} total points)")

    # Classify discovered keys for anomaly detection
    classified: dict[str, list[str]] = {"loss": [], "eval_loss": [], "grad": [], "lr": [], "other": []}
    for key in raw_map:
        category = _classify_key(key)
        classified[category].append(key)
    print(f"[wandb_monitor] Classified keys: {dict(classified)}")

    # Run anomaly detectors based on classification
    all_anomalies: list[Anomaly] = []

    for key in classified["loss"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) else 0.0 for v in vals]
        all_anomalies.extend(_detect_spikes(key, steps, floats))
        all_anomalies.extend(_detect_divergence(key, steps, floats))
        all_anomalies.extend(_detect_oscillation(key, steps, floats))
        all_anomalies.extend(_detect_plateau(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    for key in classified["eval_loss"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) else 0.0 for v in vals]
        all_anomalies.extend(_detect_spikes(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    for key in classified["grad"]:
        steps, vals = raw_map[key]
        floats = [float(v) if isinstance(v, (int, float)) else 0.0 for v in vals]
        all_anomalies.extend(_detect_grad_explosion(key, steps, floats))
        all_anomalies.extend(_detect_nans(key, steps, vals))

    # Also run basic checks on unclassified numeric metrics
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

    anomalies = _deduplicate(all_anomalies)

    # Determine health status
    has_critical = any(a.severity == Severity.critical for a in anomalies)
    has_warning = any(a.severity == Severity.warning for a in anomalies)
    if has_critical:
        status = HealthStatus.critical
    elif has_warning:
        status = HealthStatus.warning
    else:
        status = HealthStatus.ok

    # Build summary
    if status == HealthStatus.ok:
        summary = f"Run '{run.name}' looks healthy. No anomalies detected across {len(series_map)} tracked metrics."
    elif status == HealthStatus.warning:
        summary = f"Run '{run.name}' has {len(anomalies)} potential issue(s). Review the anomalies below."
    else:
        summary = f"Run '{run.name}' has {len(anomalies)} issue(s) including critical problems that may need immediate attention."

    # Suggested actions based on anomalies
    actions: list[Action] = []
    anomaly_types = {a.type for a in anomalies}
    if "loss_spike" in anomaly_types or "divergence" in anomaly_types:
        actions.append(Action(
            label="Reduce learning rate",
            risk_level=RiskLevel.low,
            description="Lower the learning rate by 2-10x to stabilize training",
        ))
    if "gradient_explosion" in anomaly_types:
        actions.append(Action(
            label="Enable gradient clipping",
            risk_level=RiskLevel.low,
            description="Add or tighten gradient clipping (e.g. max_grad_norm=1.0)",
        ))
    if "overfitting" in anomaly_types:
        actions.append(Action(
            label="Increase regularization",
            risk_level=RiskLevel.medium,
            description="Add dropout, weight decay, or data augmentation to reduce overfitting",
        ))
    if "plateau" in anomaly_types:
        actions.append(Action(
            label="Adjust LR schedule",
            risk_level=RiskLevel.low,
            description="Try a cosine/warmup schedule or increase the learning rate slightly",
        ))
    if "data_issue" in anomaly_types:
        actions.append(Action(
            label="Check data pipeline",
            risk_level=RiskLevel.medium,
            description="NaN values detected \u2014 inspect data loading, preprocessing, and loss computation",
        ))
    if not actions:
        actions.append(Action(
            label="Continue training",
            risk_level=RiskLevel.low,
            description="All metrics look stable. No action needed.",
        ))

    card = WandBHealthCard(
        title=f"Health Check: {run.name}",
        run_id=run_id,
        run_name=run.name,
        project=entity_project,
        status=status,
        summary=summary,
        url=run.url,
        metrics=list(series_map.values()),
        anomalies=anomalies,
        actions=actions,
    )
    return card.model_dump_json(indent=2)


def compare_runs(
    entity_project: str,
    run_ids_json: str,
    metric_keys: list[str] | None = None,
    max_samples: int = 500,
) -> str:
    """Compare metrics across multiple W&B runs.

    Args:
        entity_project: W&B entity/project path (or just project name)
        run_ids_json: JSON array of run IDs to compare
        metric_keys: Specific metrics to compare. If None, auto-discovers common metrics.
        max_samples: Maximum number of sample points per run
    """
    api = wandb.Api()
    entity_project = _resolve_entity_project(api, entity_project)

    try:
        run_ids = json.loads(run_ids_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "run_ids_json must be a valid JSON array of run IDs"})

    if not isinstance(run_ids, list) or len(run_ids) < 2:
        return json.dumps({"error": "Need at least 2 run IDs to compare"})

    runs_info: list[RunInfo] = []
    all_series: list[ComparisonSeries] = []

    # Discover common metric keys across all runs if not specified
    if metric_keys is None:
        keys_per_run: list[set[str]] = []
        run_objects = []
        for rid in run_ids:
            run = api.run(f"{entity_project}/{rid}")
            run_objects.append(run)
            discovered = _discover_metric_keys(run)
            keys_per_run.append(set(discovered))
        # Use the intersection so we only compare metrics all runs share
        common_keys = keys_per_run[0]
        for ks in keys_per_run[1:]:
            common_keys = common_keys & ks
        metric_keys = sorted(common_keys) if common_keys else []
    else:
        run_objects = [api.run(f"{entity_project}/{rid}") for rid in run_ids]

    if not metric_keys:
        return json.dumps({"error": "No common metrics found across the selected runs"})

    for run, rid in zip(run_objects, run_ids):
        runs_info.append(RunInfo(
            run_id=rid,
            run_name=run.name,
            url=run.url,
        ))

        history = run.history(samples=max_samples, keys=metric_keys)
        for key in metric_keys:
            if key not in history.columns:
                continue
            col = history[["_step", key]].dropna()
            points = [
                MetricPoint(step=int(row["_step"]), value=float(row[key]))
                for _, row in col.iterrows()
                if isinstance(row[key], (int, float)) and not (math.isnan(row[key]) or math.isinf(row[key]))
            ]
            if points:
                all_series.append(ComparisonSeries(
                    key=key,
                    run_name=run.name,
                    run_id=rid,
                    values=points,
                ))

    run_names = ", ".join(r.run_name for r in runs_info)
    card = ComparisonCard(
        title=f"Comparison: {len(runs_info)} Runs",
        project=entity_project,
        runs=runs_info,
        series=all_series,
        summary=f"Comparing {len(metric_keys)} metric(s) across runs: {run_names}",
    )
    return card.model_dump_json(indent=2)
