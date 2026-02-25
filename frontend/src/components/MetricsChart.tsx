import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
  ReferenceArea,
} from "recharts";
import type { MetricSeries, Anomaly, TrainingPhase } from "../types";

const KNOWN_COLORS: Record<string, string> = {
  loss: "#C5A059",
  train_loss: "#C5A059",
  "train/loss": "#C5A059",
  training_loss: "#C5A059",
  eval_loss: "#ef4444",
  "eval/loss": "#ef4444",
  val_loss: "#ef4444",
  learning_rate: "#3b82f6",
  "train/learning_rate": "#3b82f6",
  lr: "#3b82f6",
  grad_norm: "#8b5cf6",
  "train/grad_norm": "#8b5cf6",
};

const PALETTE = [
  "#C5A059", "#ef4444", "#3b82f6", "#8b5cf6", "#10b981",
  "#f59e0b", "#ec4899", "#06b6d4", "#84cc16", "#f97316",
];

function getColor(key: string, index: number): string {
  const lower = key.toLowerCase();
  for (const [pattern, color] of Object.entries(KNOWN_COLORS)) {
    if (lower === pattern || lower.includes(pattern)) return color;
  }
  return PALETTE[index % PALETTE.length];
}

const ANOMALY_COLORS: Record<string, string> = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#3b82f6",
};

const PHASE_FILL: Record<string, string> = {
  warmup: "#3b82f6",
  active_learning: "#10b981",
  convergence: "#C5A059",
  plateau: "#a8a29e",
  overfitting: "#ef4444",
};

interface Props {
  metrics: MetricSeries[];
  anomalies: Anomaly[];
  phases?: TrainingPhase[];
}

export default function MetricsChart({ metrics, anomalies, phases }: Props) {
  const [activeKeys, setActiveKeys] = useState<Set<string>>(
    new Set(metrics.map((m) => m.key)),
  );

  const toggleKey = (key: string) => {
    setActiveKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Merge all metrics into one data array keyed by step
  const dataMap = new Map<number, Record<string, number>>();
  for (const series of metrics) {
    if (!activeKeys.has(series.key)) continue;
    for (const pt of series.values) {
      const row = dataMap.get(pt.step) || { step: pt.step };
      row[series.key] = pt.value;
      dataMap.set(pt.step, row);
    }
  }
  const data = Array.from(dataMap.values()).sort((a, b) => a.step - b.step);

  // Map anomalies to chart reference dots
  const anomalyDots = anomalies
    .filter((a) => {
      const metricKey = a.metric.includes(" vs ") ? a.metric.split(" vs ")[0] : a.metric;
      return activeKeys.has(metricKey) || activeKeys.has(a.metric);
    })
    .map((a) => {
      const metricKey = a.metric.includes(" vs ") ? a.metric.split(" vs ")[0] : a.metric;
      const row = dataMap.get(a.step);
      const value = row?.[metricKey] ?? a.value ?? 0;
      return { ...a, metricKey, chartValue: value };
    });

  return (
    <div>
      {/* Metric toggle pills */}
      <div className="flex flex-wrap gap-2 mb-4">
        {metrics.map((m) => (
          <button
            key={m.key}
            onClick={() => toggleKey(m.key)}
            className={`px-3 py-1 text-xs font-bold tracking-wide uppercase rounded-full border transition-all duration-200 ${
              activeKeys.has(m.key)
                ? "border-stone-900 bg-stone-900 text-white"
                : "border-stone-300 text-stone-400 hover:border-stone-400"
            }`}
          >
            <span
              className="inline-block w-2 h-2 rounded-full mr-1.5"
              style={{
                backgroundColor: getColor(m.key, metrics.indexOf(m)),
              }}
            />
            {m.key}
          </button>
        ))}
      </div>

      {/* Chart */}
      <div className="bg-nobel-cream rounded-lg p-3 border border-stone-100">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
            <XAxis
              dataKey="step"
              tick={{ fontSize: 10, fill: "#a8a29e" }}
              tickLine={false}
              axisLine={{ stroke: "#d6d3d1" }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "#a8a29e" }}
              tickLine={false}
              axisLine={{ stroke: "#d6d3d1" }}
              width={50}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "white",
                border: "1px solid #e7e5e4",
                borderRadius: "8px",
                fontSize: "12px",
                boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
              }}
            />
            {/* Phase overlay areas */}
            {phases?.map((phase, i) => (
              <ReferenceArea
                key={`phase-${i}`}
                x1={phase.start_step}
                x2={phase.end_step}
                fill={PHASE_FILL[phase.name] || "#a8a29e"}
                fillOpacity={0.06}
                strokeOpacity={0}
              />
            ))}
            {metrics
              .filter((m) => activeKeys.has(m.key))
              .map((m) => (
                <Line
                  key={m.key}
                  type="monotone"
                  dataKey={m.key}
                  stroke={getColor(m.key, metrics.indexOf(m))}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3, strokeWidth: 0 }}
                />
              ))}
            {anomalyDots.map((a, i) => (
              <ReferenceDot
                key={i}
                x={a.step}
                y={a.chartValue}
                r={5}
                fill={ANOMALY_COLORS[a.severity] || "#f59e0b"}
                stroke="white"
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
