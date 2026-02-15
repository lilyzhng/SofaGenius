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
} from "lucide-react";
import MetricsChart from "./MetricsChart";
import type { WandBHealthCard as WandBHealthCardType, Anomaly } from "../types";

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

interface Props {
  card: WandBHealthCardType;
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

export default function WandBHealthCard({ card }: Props) {
  const [expanded, setExpanded] = useState(true);
  const statusCfg = STATUS_CONFIG[card.status];
  const StatusIcon = statusCfg.icon;

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
              W&B Health
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
        {card.url && (
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
          {/* Metrics chart */}
          {card.metrics.length > 0 && (
            <div className="px-5 py-4">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Metrics
              </div>
              <MetricsChart metrics={card.metrics} anomalies={card.anomalies} />
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
