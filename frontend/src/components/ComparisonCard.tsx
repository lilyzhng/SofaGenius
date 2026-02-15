import { useState } from "react";
import { motion } from "framer-motion";
import {
  ChevronDown,
  ChevronUp,
  ExternalLink,
  GitCompareArrows,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ComparisonCard as ComparisonCardType } from "../types";

const RUN_COLORS = [
  "#C5A059", "#ef4444", "#3b82f6", "#8b5cf6", "#10b981",
  "#f59e0b", "#ec4899", "#06b6d4", "#84cc16", "#f97316",
];

interface Props {
  card: ComparisonCardType;
}

export default function ComparisonCard({ card }: Props) {
  const [expanded, setExpanded] = useState(true);

  // Discover unique metric keys
  const metricKeys = Array.from(new Set(card.series.map((s) => s.key)));
  const [activeMetrics, setActiveMetrics] = useState<Set<string>>(
    new Set(metricKeys),
  );

  // Assign a color per run (consistent across all metrics)
  const runColorMap = new Map<string, string>();
  card.runs.forEach((r, i) => {
    runColorMap.set(r.run_id, RUN_COLORS[i % RUN_COLORS.length]);
  });

  const toggleMetric = (key: string) => {
    setActiveMetrics((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size > 1) next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  // Build merged data: one row per step with columns like "runName — metric"
  const dataMap = new Map<number, Record<string, number>>();
  const lineKeys: { dataKey: string; color: string; runName: string; metric: string }[] = [];

  for (const series of card.series) {
    if (!activeMetrics.has(series.key)) continue;
    const dataKey = `${series.run_name} \u2014 ${series.key}`;
    const color = runColorMap.get(series.run_id) || "#a8a29e";
    lineKeys.push({ dataKey, color, runName: series.run_name, metric: series.key });

    for (const pt of series.values) {
      const row = dataMap.get(pt.step) || { step: pt.step };
      row[dataKey] = pt.value;
      dataMap.set(pt.step, row);
    }
  }

  const data = Array.from(dataMap.values()).sort((a, b) => a.step - b.step);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 80, damping: 15 }}
      className="bg-white rounded-xl border border-stone-200 shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-1">
              Run Comparison
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-stone-100 text-stone-600 border border-stone-200">
            <GitCompareArrows size={12} />
            {card.runs.length} runs
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Summary */}
        <p className="text-sm text-stone-600 leading-relaxed">{card.summary}</p>

        {/* Run legend */}
        <div className="flex flex-wrap gap-3 mt-3">
          {card.runs.map((run) => (
            <div key={run.run_id} className="flex items-center gap-1.5 text-xs text-stone-500">
              <span
                className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: runColorMap.get(run.run_id) }}
              />
              <span className="font-medium text-stone-700">{run.run_name}</span>
              {run.url && (
                <a
                  href={run.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-nobel-gold hover:text-stone-900 transition-colors"
                >
                  <ExternalLink size={10} />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-center gap-1 py-2 border-t border-stone-100 text-xs text-stone-400 hover:text-stone-600 hover:bg-stone-50 transition-colors"
      >
        {expanded ? (
          <>
            <ChevronUp size={12} /> Hide charts
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show charts
          </>
        )}
      </button>

      {/* Expandable details */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-stone-100"
        >
          <div className="px-5 py-4">
            {/* Metric toggle pills */}
            <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
              Metrics
            </div>
            <div className="flex flex-wrap gap-2 mb-4">
              {metricKeys.map((key) => (
                <button
                  key={key}
                  onClick={() => toggleMetric(key)}
                  className={`px-3 py-1 text-xs font-bold tracking-wide uppercase rounded-full border transition-all duration-200 ${
                    activeMetrics.has(key)
                      ? "border-stone-900 bg-stone-900 text-white"
                      : "border-stone-300 text-stone-400 hover:border-stone-400"
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>

            {/* Chart */}
            <div className="bg-nobel-cream rounded-lg p-3 border border-stone-100">
              <ResponsiveContainer width="100%" height={280}>
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
                    width={55}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e7e5e4",
                      borderRadius: "8px",
                      fontSize: "11px",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                    }}
                  />
                  {lineKeys.map((lk) => (
                    <Line
                      key={lk.dataKey}
                      type="monotone"
                      dataKey={lk.dataKey}
                      stroke={lk.color}
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 3, strokeWidth: 0 }}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
