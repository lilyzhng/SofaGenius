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


# --- Phase 3: Scout + Draft models ---


class ConfidenceLevel(str, Enum):
    finding = "finding"
    hypothesis = "hypothesis"


class ScoutRecommendation(BaseModel):
    name: str
    resource_type: str  # "dataset" or "model"
    url: str
    description: str
    downloads: int = 0
    likes: int = 0
    tags: list[str] = []
    reasoning: str = ""
    tradeoffs: str = ""


class ScoutCard(BaseModel):
    card_type: str = "scout_card"
    title: str
    query: str
    summary: str
    recommendations: list[ScoutRecommendation]
    resource_type_filter: Optional[str] = None  # "dataset", "model", or None for both


class EvidenceRef(BaseModel):
    source: str
    snippet: str
    link: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.hypothesis


class DraftPostCard(BaseModel):
    card_type: str = "draft_post_card"
    title: str
    draft_text: str
    thread: list[str] = []
    evidence: list[EvidenceRef] = []
    tone: str = "professional"
    char_count: int = 0
    requires_approval: bool = True


# --- Phase 4: Launch models ---


class LaunchStatus(str, Enum):
    proposed = "proposed"
    launching = "launching"
    running = "running"
    completed = "completed"
    failed = "failed"


class LaunchType(str, Enum):
    finetune = "finetune"
    eval = "eval"


class FinetuneConfig(BaseModel):
    model_name: str = "Qwen/Qwen2.5-Coder-14B"
    dataset_name: str = ""
    max_seq_length: int = 4096
    load_in_4bit: bool = True
    lora_r: int = 32
    lora_alpha: int = 32
    learning_rate: float = 2e-4
    num_epochs: int = 1
    max_steps: int = -1
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    gpu_type: str = "A100"
    push_to_hub: bool = True
    hf_repo_name: Optional[str] = None
    wandb_project: str = "qwen-coder-code-gen"


class EvalConfig(BaseModel):
    base_model: str = "Qwen/Qwen2.5-Coder-14B"
    lora_model: str = ""
    hf_dataset: str = "lilyzhng/uigen-ui-code-gen"
    limit: int = 20
    use_judge: bool = True
    judge_model: str = "google/gemini-3-pro-preview"
    wandb_project: str = "uiux-eval"


class CostEstimate(BaseModel):
    gpu_type: str
    estimated_hours: float
    estimated_cost_usd: float
    note: str = ""


class LaunchCard(BaseModel):
    card_type: str = "launch_card"
    title: str
    launch_type: LaunchType
    status: LaunchStatus = LaunchStatus.proposed
    config: dict = {}
    cost_estimate: Optional[CostEstimate] = None
    summary: str = ""
    modal_function_call_id: Optional[str] = None
    wandb_url: Optional[str] = None
    requires_approval: bool = True
