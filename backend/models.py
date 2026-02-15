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


# --- Phase 2: Data / SQL Analyst models ---


class ColumnInfo(BaseModel):
    name: str
    type: str
    sample_values: list[str]


class QueryResult(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    execution_time_ms: float
    truncated: bool = False


class StatsSummary(BaseModel):
    column: str
    kind: str  # "numeric" or "categorical"
    # numeric stats
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    # categorical stats
    unique_count: Optional[int] = None
    top_values: Optional[list[dict[str, int]]] = None


class PlotData(BaseModel):
    plot_type: str  # "bar", "line", "scatter", "histogram"
    title: str
    x_label: str
    y_label: str
    x_values: list
    y_values: list


class DataCard(BaseModel):
    card_type: str = "data_card"
    title: str
    dataset_path: str
    sql_query: str
    summary: str
    query_result: Optional[QueryResult] = None
    stats: Optional[list[StatsSummary]] = None
    plot: Optional[PlotData] = None
    next_suggestions: Optional[list[str]] = None
