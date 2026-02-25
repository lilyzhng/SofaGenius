import { useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Info,
  TrendingDown,
  TrendingUp,
  Zap,
} from "lucide-react";
import MetricsChart from "./MetricsChart";
import type {
  WandBHealthCard as WandBHealthCardType,
  Anomaly,
  TrainingPhase,
  MetricStats,
} from "../types";

const STATUS_CONFIG = {
  ok: {
    label: "Healthy",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    icon: CheckCircle,
  },
  warning: {
    label: "Warning",
    color: "text-amber-600",
    bg: "bg-amber-50",
    border: "border-amber-200",
    icon: AlertTriangle,
  },
  critical: {
    label: "Critical",
    color: "text-red-600",
    bg: "bg-red-50",
    border: "border-red-200",
    icon: AlertCircle,
  },
};

const SEVERITY_CONFIG = {
  info: { icon: Info, color: "text-blue-500", bg: "bg-blue-50" },
  warning: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-50" },
  critical: { icon: AlertCircle, color: "text-red-500", bg: "bg-red-50" },
};

const RISK_BORDER = {
  low: "border-emerald-300 text-emerald-700 hover:bg-emerald-50",
  medium: "border-amber-300 text-amber-700 hover:bg-amber-50",
  high: "border-red-300 text-red-700 hover:bg-red-50",
};

const PHASE_COLORS: Record<string, { bg: string; text: string; bar: string }> = {
  warmup: { bg: "bg-blue-50", text: "text-blue-700", bar: "bg-blue-400" },
  active_learning: { bg: "bg-emerald-50", text: "text-emerald-700", bar: "bg-emerald-400" },
  convergence: { bg: "bg-amber-50", text: "text-amber-700", bar: "bg-nobel-gold" },
  plateau: { bg: "bg-stone-100", text: "text-stone-600", bar: "bg-stone-400" },
  overfitting: { bg: "bg-red-50", text: "text-red-700", bar: "bg-red-400" },
};

interface Props {
  card: WandBHealthCardType;
  hasWandbKey?: boolean;
}

function AnomalyRow({ anomaly }: { anomaly: Anomaly }) {
  const config = SEVERITY_CONFIG[anomaly.severity];
  const Icon = config.icon;

  return (
    <div className="flex gap-3 items-start py-2">
      <div className={`p-1 rounded ${config.bg} flex-shrink-0 mt-0.5`}>
        <Icon size={12} className={config.color} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs font-medium text-stone-800">{anomaly.message}</div>
        <div className="text-xs text-stone-400 mt-0.5">
          Step {anomaly.step} &middot; {anomaly.type.replace(/_/g, " ")}
        </div>
      </div>
    </div>
  );
}

function PhasesTimeline({ phases }: { phases: TrainingPhase[] }) {
  if (phases.length === 0) return null;
  const totalRange = phases[phases.length - 1].end_step - phases[0].start_step;
  if (totalRange <= 0) return null;

  return (
    <div className="px-5 py-4 border-t border-stone-100">
      <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
        Training Phases
      </div>
      {/* Segmented bar */}
      <div className="flex rounded-full overflow-hidden h-3 mb-2">
        {phases.map((phase, i) => {
          const width = ((phase.end_step - phase.start_step) / totalRange) * 100;
          const colors = PHASE_COLORS[phase.name] || PHASE_COLORS.convergence;
          return (
            <div
              key={i}
              className={`${colors.bar} relative group`}
              style={{ width: `${Math.max(width, 2)}%` }}
              title={`${phase.name.replace(/_/g, " ")} (step ${phase.start_step}–${phase.end_step})`}
            />
          );
        })}
      </div>
      {/* Phase labels */}
      <div className="flex flex-wrap gap-2 mt-2">
        {phases.map((phase, i) => {
          const colors = PHASE_COLORS[phase.name] || PHASE_COLORS.convergence;
          return (
            <div
              key={i}
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs ${colors.bg} ${colors.text}`}
              title={phase.description}
            >
              <span className={`w-2 h-2 rounded-full ${colors.bar}`} />
              {phase.name.replace(/_/g, " ")}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MetricStatsGrid({ stats }: { stats: MetricStats[] }) {
  if (stats.length === 0) return null;
  // Show up to 4 most interesting metrics (loss metrics first)
  const sorted = [...stats].sort((a, b) => {
    const aIsLoss = a.key.toLowerCase().includes("loss") ? 0 : 1;
    const bIsLoss = b.key.toLowerCase().includes("loss") ? 0 : 1;
    return aIsLoss - bIsLoss;
  });
  const shown = sorted.slice(0, 4);

  return (
    <div className="px-5 py-4 border-t border-stone-100">
      <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
        Key Metrics
      </div>
      <div className="grid grid-cols-2 gap-3">
        {shown.map((stat) => {
          const improved = stat.improvement_pct > 0;
          return (
            <div
              key={stat.key}
              className="bg-[#F9F8F4] rounded-lg p-3 border border-stone-100"
            >
              <div className="text-xs text-stone-500 font-medium truncate mb-1">
                {stat.key}
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-semibold text-stone-900">
                  {stat.final_value < 0.001
                    ? stat.final_value.toExponential(2)
                    : stat.final_value.toFixed(4)}
                </span>
                <span
                  className={`inline-flex items-center gap-0.5 text-xs font-medium ${
                    improved ? "text-emerald-600" : "text-red-500"
                  }`}
                >
                  {improved ? (
                    <TrendingDown size={10} />
                  ) : (
                    <TrendingUp size={10} />
                  )}
                  {Math.abs(stat.improvement_pct).toFixed(1)}%
                </span>
              </div>
              <div className="text-xs text-stone-400 mt-1">
                {stat.initial_value.toFixed(4)} &rarr; {stat.final_value.toFixed(4)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ConvergenceBar({
  convergence,
}: {
  convergence: NonNullable<WandBHealthCardType["insights"]>["convergence"];
}) {
  if (!convergence) return null;
  const ratio = convergence.efficiency_ratio ?? 1;

  return (
    <div className="px-5 py-4 border-t border-stone-100">
      <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-2">
        Convergence Speed
      </div>
      <div className="flex items-center gap-3">
        <Zap size={14} className="text-nobel-gold flex-shrink-0" />
        <div className="flex-1">
          <div className="h-2 rounded-full bg-stone-100 overflow-hidden">
            <div
              className="h-full rounded-full bg-nobel-gold transition-all duration-500"
              style={{ width: `${Math.min(ratio * 100, 100)}%` }}
            />
          </div>
        </div>
        <span className="text-xs text-stone-600 whitespace-nowrap">
          {convergence.steps_to_90pct != null
            ? `${convergence.steps_to_90pct} steps (${Math.round(ratio * 100)}%)`
            : "N/A"}
        </span>
      </div>
      <p className="text-xs text-stone-500 mt-1">{convergence.description}</p>
    </div>
  );
}

export default function WandBHealthCard({ card, hasWandbKey }: Props) {
  const [expanded, setExpanded] = useState(true);
  const statusCfg = STATUS_CONFIG[card.status];
  const StatusIcon = statusCfg.icon;
  const insights = card.insights;

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
            <div className="flex items-center gap-2 mb-1">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase">
                W&B Health
              </div>
              {card.alias && (
                <span className="px-2.5 py-0.5 border border-nobel-gold text-nobel-gold text-xs tracking-[0.15em] uppercase font-bold rounded-full">
                  {card.alias}
                </span>
              )}
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${statusCfg.bg} ${statusCfg.color} ${statusCfg.border} border`}
          >
            <StatusIcon size={12} />
            {statusCfg.label}
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Summary */}
        <p className="text-sm text-stone-600 leading-relaxed">{card.summary}</p>

        {/* W&B link */}
        {card.url && hasWandbKey && (
          <a
            href={card.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 mt-2 text-xs text-nobel-gold hover:text-stone-900 transition-colors"
          >
            <ExternalLink size={10} />
            Open in W&B
          </a>
        )}
        {card.url && !hasWandbKey && (
          <span className="inline-flex items-center gap-1 mt-2 text-xs text-stone-400">
            <Activity size={10} />
            Metrics visible here — add W&B token in Settings for external link
          </span>
        )}
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-center gap-1 py-2 border-t border-stone-100 text-xs text-stone-400 hover:text-stone-600 hover:bg-stone-50 transition-colors"
      >
        {expanded ? (
          <>
            <ChevronUp size={12} /> Hide details
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show metrics & anomalies
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
          {/* Trend Summary */}
          {insights?.trend_summary && (
            <div className="px-5 py-4">
              <div className="p-4 bg-[#F9F8F4] border border-stone-200 rounded-lg border-l-4 border-l-nobel-gold">
                <p className="font-serif italic text-sm text-stone-700 leading-relaxed">
                  {insights.trend_summary}
                </p>
                {insights.lr_analysis && (
                  <p className="text-xs text-stone-500 mt-2">
                    LR Schedule: {insights.lr_analysis}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Training Phases Timeline */}
          {insights?.phases && <PhasesTimeline phases={insights.phases} />}

          {/* Key Metrics Grid */}
          {insights?.metric_stats && (
            <MetricStatsGrid stats={insights.metric_stats} />
          )}

          {/* Convergence Speed */}
          {insights?.convergence && (
            <ConvergenceBar convergence={insights.convergence} />
          )}

          {/* Metrics chart */}
          {card.metrics.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Metrics
              </div>
              <MetricsChart
                metrics={card.metrics}
                anomalies={card.anomalies}
                phases={insights?.phases}
              />
            </div>
          )}

          {/* Anomalies */}
          {card.anomalies.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Anomalies ({card.anomalies.length})
              </div>
              <div className="divide-y divide-stone-100">
                {card.anomalies.map((a, i) => (
                  <AnomalyRow key={i} anomaly={a} />
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          {card.actions.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Suggested Actions
              </div>
              <div className="flex flex-wrap gap-2">
                {card.actions.map((action, i) => (
                  <button
                    key={i}
                    className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${RISK_BORDER[action.risk_level]}`}
                    title={action.description}
                  >
                    {action.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
