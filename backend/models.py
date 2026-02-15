from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RunStatus(str, Enum):
    running = "running"
    finished = "finished"
    crashed = "crashed"
    failed = "failed"


class HealthStatus(str, Enum):
    ok = "ok"
    warning = "warning"
    critical = "critical"


class MetricPoint(BaseModel):
    step: int
    value: float


class MetricSeries(BaseModel):
    key: str
    values: list[MetricPoint]


class Anomaly(BaseModel):
    type: str
    severity: Severity
    step: int
    metric: str
    message: str
    value: Optional[float] = None
    threshold: Optional[float] = None


class Action(BaseModel):
    label: str
    risk_level: RiskLevel
    description: str
    requires_approval: bool = False


class RunSummary(BaseModel):
    name: str
    id: str
    state: str
    metrics: dict[str, float]
    url: Optional[str] = None


class WandBHealthCard(BaseModel):
    card_type: str = "wandb_health"
    title: str
    run_id: str
    run_name: str
    project: str
    status: HealthStatus
    summary: str
    url: Optional[str] = None
    metrics: list[MetricSeries]
    anomalies: list[Anomaly]
    actions: list[Action]
