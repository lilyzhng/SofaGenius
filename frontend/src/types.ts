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

export type CardData = WandBHealthCard | DataCard;

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
