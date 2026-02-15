export type Severity = "info" | "warning" | "critical";
export type RiskLevel = "low" | "medium" | "high";
export type HealthStatus = "ok" | "warning" | "critical";

export interface MetricPoint {
  step: number;
  value: number;
}

export interface MetricSeries {
  key: string;
  values: MetricPoint[];
}

export interface Anomaly {
  type: string;
  severity: Severity;
  step: number;
  metric: string;
  message: string;
  value?: number;
  threshold?: number;
}

export interface Action {
  label: string;
  risk_level: RiskLevel;
  description: string;
  requires_approval?: boolean;
}

export interface WandBHealthCard {
  card_type: "wandb_health";
  title: string;
  run_id: string;
  run_name: string;
  project: string;
  status: HealthStatus;
  summary: string;
  url?: string;
  metrics: MetricSeries[];
  anomalies: Anomaly[];
  actions: Action[];
}

// --- Phase 2: Data / SQL Analyst types ---

export interface ColumnInfo {
  name: string;
  type: string;
  sample_values: string[];
}

export interface QueryResult {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_time_ms: number;
  truncated: boolean;
}

export interface StatsSummary {
  column: string;
  kind: "numeric" | "categorical";
  mean?: number;
  std?: number;
  min?: number;
  max?: number;
  unique_count?: number;
  top_values?: Record<string, number>[];
}

export interface PlotData {
  plot_type: "bar" | "line" | "scatter" | "histogram";
  title: string;
  x_label: string;
  y_label: string;
  x_values: unknown[];
  y_values: unknown[];
}

export interface DataCard {
  card_type: "data_card";
  title: string;
  dataset_path: string;
  sql_query: string;
  summary: string;
  query_result?: QueryResult;
  stats?: StatsSummary[];
  plot?: PlotData;
  next_suggestions?: string[];
}

// --- Phase 3: Scout + Draft types ---

export type ConfidenceLevel = "finding" | "hypothesis";

export interface ScoutRecommendation {
  name: string;
  resource_type: "dataset" | "model";
  url: string;
  description: string;
  downloads: number;
  likes: number;
  tags: string[];
  reasoning: string;
  tradeoffs: string;
}

export interface ScoutCard {
  card_type: "scout_card";
  title: string;
  query: string;
  summary: string;
  recommendations: ScoutRecommendation[];
  resource_type_filter?: string;
}

export interface EvidenceRef {
  source: string;
  snippet: string;
  link?: string;
  confidence: ConfidenceLevel;
}

export interface DraftPostCard {
  card_type: "draft_post_card";
  title: string;
  draft_text: string;
  thread: string[];
  evidence: EvidenceRef[];
  tone: string;
  char_count: number;
  requires_approval: boolean;
}

// --- Phase 4: Launch types ---

export type LaunchStatus = "proposed" | "launching" | "running" | "completed" | "failed";
export type LaunchType = "finetune" | "eval";

export interface CostEstimate {
  gpu_type: string;
  estimated_seconds: number;
  estimated_cost_usd: number;
  note: string;
}

export interface LaunchCard {
  card_type: "launch_card";
  title: string;
  launch_type: LaunchType;
  status: LaunchStatus;
  config: Record<string, unknown>;
  cost_estimate?: CostEstimate;
  summary: string;
  modal_function_call_id?: string;
  wandb_url?: string;
  requires_approval: boolean;
}

// --- Compare Runs types ---

export interface ComparisonSeries {
  key: string;
  run_name: string;
  run_id: string;
  values: MetricPoint[];
}

export interface RunInfo {
  run_id: string;
  run_name: string;
  url?: string;
}

export interface ComparisonCard {
  card_type: "comparison_card";
  title: string;
  project: string;
  runs: RunInfo[];
  series: ComparisonSeries[];
  summary: string;
}

export type CardData = WandBHealthCard | DataCard | ScoutCard | DraftPostCard | LaunchCard | ComparisonCard;

export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  status: "running" | "done" | "error";
  result?: string;
}

export type MessageSegment =
  | { type: "text"; content: string }
  | { type: "tool"; tool: ToolCall };

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string; // full text for conversation history
  segments?: MessageSegment[]; // ordered text + tool steps for rendering
}

export interface SSEEvent {
  type: "text" | "tool_call" | "tool_result" | "card" | "done";
  content?: string;
  name?: string;
  input?: Record<string, unknown>;
  summary?: string;
  card_type?: string;
  data?: CardData;
}
