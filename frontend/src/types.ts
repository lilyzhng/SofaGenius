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

export type CardData = WandBHealthCard;

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: { name: string; input: Record<string, unknown> }[];
}

export interface SSEEvent {
  type: "text" | "tool_call" | "card" | "done";
  content?: string;
  name?: string;
  input?: Record<string, unknown>;
  card_type?: string;
  data?: CardData;
}
