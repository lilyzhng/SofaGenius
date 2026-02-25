"""Synthetic training data scenarios with ground-truth labels.

Each scenario generates deterministic metric data (seeded by name hash)
and declares what anomalies, phases, and LR schedule the analysis
functions *should* detect.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class ScenarioMetric:
    """A single metric time series within a scenario."""

    key: str
    steps: list[int]
    values: list[float]
    category: str  # "loss" | "eval_loss" | "grad" | "lr" | "other"


@dataclass
class Scenario:
    """A complete synthetic training scenario."""

    name: str
    metrics: list[ScenarioMetric]
    expected_anomaly_types: list[str]
    expected_phases: list[str]
    expected_lr_schedule: str | None
    should_converge: bool
    is_edge_case: bool
    tags: list[str] = field(default_factory=list)


def _seed(name: str) -> int:
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def _steps(n: int) -> list[int]:
    return list(range(n))


# ---------------------------------------------------------------------------
# Scenario factories
# ---------------------------------------------------------------------------


def healthy_exponential_decay() -> Scenario:
    rng = np.random.default_rng(_seed("healthy_exponential_decay"))
    n = 500
    t = np.linspace(0, 5, n)
    loss = 2.0 * np.exp(-t) + 0.1 + rng.normal(0, 0.01, n)
    lr = np.concatenate([
        np.linspace(0, 3e-4, 50),  # warmup
        3e-4 * np.cos(np.linspace(0, np.pi / 2, n - 50)),  # cosine decay
    ])
    return Scenario(
        name="healthy_exponential_decay",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
            ScenarioMetric("learning_rate", _steps(n), lr.tolist(), "lr"),
        ],
        expected_anomaly_types=[],
        expected_phases=["warmup", "active_learning", "convergence"],
        expected_lr_schedule="cosine",
        should_converge=True,
        is_edge_case=False,
        tags=["insight", "lr"],
    )


def plateau_then_overfit() -> Scenario:
    n = 400
    # Train loss: drops, plateaus (truly flat for plateau detector: epsilon=1e-5),
    # then strictly decreases (for overfitting detector: 5+ monotonic steps)
    train_loss = np.concatenate([
        np.linspace(2.0, 0.5, 200),
        np.full(100, 0.5),                 # dead-flat plateau
        np.linspace(0.5, 0.3, 100),        # strictly decreasing
    ])
    # Eval loss: follows train during drop, flat during plateau,
    # then strictly increases (overfitting: eval up while train down)
    eval_loss = np.concatenate([
        np.linspace(2.1, 0.55, 200),
        np.full(100, 0.55),                # flat during plateau
        np.linspace(0.55, 0.9, 100),       # strictly increasing
    ])
    return Scenario(
        name="plateau_then_overfit",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), train_loss.tolist(), "loss"),
            ScenarioMetric("eval/loss", _steps(n), eval_loss.tolist(), "eval_loss"),
        ],
        expected_anomaly_types=["overfitting", "plateau"],
        expected_phases=["active_learning", "convergence", "overfitting"],
        expected_lr_schedule=None,
        should_converge=True,
        is_edge_case=False,
        tags=["anomaly", "insight"],
    )


def spike_mid_training() -> Scenario:
    rng = np.random.default_rng(_seed("spike_mid_training"))
    n = 500
    t = np.linspace(0, 5, n)
    loss = 2.0 * np.exp(-t) + 0.1 + rng.normal(0, 0.01, n)
    # Inject a spike at step 250
    loss[250] = loss[250] + 3.0
    return Scenario(
        name="spike_mid_training",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
        ],
        expected_anomaly_types=["loss_spike"],
        expected_phases=["warmup", "active_learning", "convergence"],
        expected_lr_schedule=None,
        should_converge=True,
        is_edge_case=False,
        tags=["anomaly"],
    )


def divergence_run() -> Scenario:
    rng = np.random.default_rng(_seed("divergence_run"))
    n = 300
    # Starts normal, then monotonically increases
    loss = np.concatenate([
        np.linspace(2.0, 0.8, 150),
        np.linspace(0.8, 5.0, 150),
    ]) + rng.normal(0, 0.005, n)
    return Scenario(
        name="divergence_run",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
        ],
        expected_anomaly_types=["divergence"],
        expected_phases=["active_learning", "overfitting"],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=False,
        tags=["anomaly"],
    )


def gradient_explosion() -> Scenario:
    rng = np.random.default_rng(_seed("gradient_explosion"))
    n = 200
    grad_norm = rng.uniform(0.5, 5.0, n)
    # Inject explosion near end
    grad_norm[150:] = rng.uniform(150, 500, 50)
    loss = np.linspace(1.0, 0.5, n) + rng.normal(0, 0.01, n)
    return Scenario(
        name="gradient_explosion",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
            ScenarioMetric("grad_norm", _steps(n), grad_norm.tolist(), "grad"),
        ],
        expected_anomaly_types=["gradient_explosion"],
        expected_phases=[],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=False,
        tags=["anomaly"],
    )


def noisy_chaotic() -> Scenario:
    rng = np.random.default_rng(_seed("noisy_chaotic"))
    n = 500
    # High-variance oscillating loss
    base = np.linspace(2.0, 1.0, n)
    noise = rng.normal(0, 1.5, n)
    loss = base + noise
    return Scenario(
        name="noisy_chaotic",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
        ],
        expected_anomaly_types=["oscillation"],
        expected_phases=[],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=True,
        tags=["anomaly", "edge_case"],
    )


def short_run() -> Scenario:
    rng = np.random.default_rng(_seed("short_run"))
    n = 30
    loss = np.linspace(2.0, 1.5, n) + rng.normal(0, 0.01, n)
    return Scenario(
        name="short_run",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
        ],
        expected_anomaly_types=[],
        expected_phases=[],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=True,
        tags=["edge_case"],
    )


def constant_loss() -> Scenario:
    n = 200
    loss = [1.0] * n
    return Scenario(
        name="constant_loss",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss, "loss"),
        ],
        expected_anomaly_types=[],
        expected_phases=[],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=True,
        tags=["edge_case"],
    )


def nan_in_metrics() -> Scenario:
    rng = np.random.default_rng(_seed("nan_in_metrics"))
    n = 200
    loss = np.linspace(2.0, 0.5, n) + rng.normal(0, 0.01, n)
    loss_list = loss.tolist()
    # Inject NaN/None at various points
    loss_list[50] = float("nan")
    loss_list[100] = float("inf")
    loss_list[150] = float("nan")
    return Scenario(
        name="nan_in_metrics",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss_list, "loss"),
        ],
        expected_anomaly_types=["data_issue"],
        expected_phases=[],
        expected_lr_schedule=None,
        should_converge=False,
        is_edge_case=True,
        tags=["anomaly", "edge_case"],
    )


def cosine_lr() -> Scenario:
    rng = np.random.default_rng(_seed("cosine_lr"))
    n = 300
    t = np.linspace(0, 4, n)
    loss = 1.5 * np.exp(-t) + 0.2 + rng.normal(0, 0.01, n)
    lr = np.concatenate([
        np.linspace(0, 5e-4, 30),
        0.5 * 5e-4 * (1 + np.cos(np.pi * np.linspace(0, 1, n - 30))),
    ])
    return Scenario(
        name="cosine_lr",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
            ScenarioMetric("learning_rate", _steps(n), lr.tolist(), "lr"),
        ],
        expected_anomaly_types=[],
        expected_phases=["warmup", "active_learning", "convergence"],
        expected_lr_schedule="cosine",
        should_converge=True,
        is_edge_case=False,
        tags=["lr"],
    )


def step_lr() -> Scenario:
    rng = np.random.default_rng(_seed("step_lr"))
    n = 300
    loss = np.linspace(1.5, 0.4, n) + rng.normal(0, 0.01, n)
    lr = np.concatenate([
        np.full(100, 1e-3),
        np.full(100, 1e-4),
        np.full(100, 1e-5),
    ])
    return Scenario(
        name="step_lr",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
            ScenarioMetric("lr", _steps(n), lr.tolist(), "lr"),
        ],
        expected_anomaly_types=[],
        expected_phases=[],
        expected_lr_schedule="step",
        should_converge=True,
        is_edge_case=False,
        tags=["lr"],
    )


def warmup_linear_decay_lr() -> Scenario:
    rng = np.random.default_rng(_seed("warmup_linear_decay_lr"))
    n = 300
    loss = np.linspace(2.0, 0.3, n) + rng.normal(0, 0.01, n)
    lr = np.concatenate([
        np.linspace(0, 5e-4, 30),
        np.linspace(5e-4, 1e-5, n - 30),
    ])
    return Scenario(
        name="warmup_linear_decay_lr",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
            ScenarioMetric("learning_rate", _steps(n), lr.tolist(), "lr"),
        ],
        expected_anomaly_types=[],
        expected_phases=[],
        expected_lr_schedule="linear",
        should_converge=True,
        is_edge_case=False,
        tags=["lr"],
    )


def linear_convergence() -> Scenario:
    rng = np.random.default_rng(_seed("linear_convergence"))
    n = 500
    loss = np.linspace(3.0, 0.5, n) + rng.normal(0, 0.01, n)
    return Scenario(
        name="linear_convergence",
        metrics=[
            ScenarioMetric("train/loss", _steps(n), loss.tolist(), "loss"),
        ],
        expected_anomaly_types=[],
        expected_phases=["active_learning"],
        expected_lr_schedule=None,
        should_converge=True,
        is_edge_case=False,
        tags=["insight"],
    )


ALL_SCENARIOS: list[Scenario] = [
    healthy_exponential_decay(),
    plateau_then_overfit(),
    spike_mid_training(),
    divergence_run(),
    gradient_explosion(),
    noisy_chaotic(),
    short_run(),
    constant_loss(),
    nan_in_metrics(),
    cosine_lr(),
    step_lr(),
    warmup_linear_decay_lr(),
    linear_convergence(),
]
