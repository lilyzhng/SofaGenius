import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  ClipboardCheck,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  ExternalLink,
  Loader2,
  Cpu,
  DollarSign,
  Clock,
  XCircle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Bot,
  FlaskConical,
  Palette,
} from "lucide-react";
import type {
  EvalResultsCard as EvalResultsCardType,
  EvalStatus,
  EvalTier,
  TaskScore,
} from "../types";
import { API_BASE } from "../config";

interface Props {
  card: EvalResultsCardType;
  onWandbUrl?: (url: string) => void;
}

const STATUS_CONFIG: Record<
  EvalStatus,
  { label: string; color: string; icon: React.ReactNode }
> = {
  proposed: {
    label: "Proposed",
    color: "bg-amber-50 text-amber-600 border-amber-200",
    icon: <ShieldAlert size={12} />,
  },
  launching: {
    label: "Launching",
    color: "bg-blue-50 text-blue-600 border-blue-200",
    icon: <Loader2 size={12} className="animate-spin" />,
  },
  running: {
    label: "Running",
    color: "bg-blue-50 text-blue-600 border-blue-200",
    icon: <Loader2 size={12} className="animate-spin" />,
  },
  completed: {
    label: "Completed",
    color: "bg-emerald-50 text-emerald-600 border-emerald-200",
    icon: <CheckCircle2 size={12} />,
  },
  failed: {
    label: "Failed",
    color: "bg-red-50 text-red-600 border-red-200",
    icon: <XCircle size={12} />,
  },
};

const TIER_CONFIG: Record<
  EvalTier,
  { label: string; icon: React.ReactNode; color: string }
> = {
  agent: {
    label: "Agent Eval",
    icon: <Bot size={12} />,
    color: "bg-violet-50 text-violet-600 border-violet-200",
  },
  benchmark: {
    label: "Benchmark",
    icon: <FlaskConical size={12} />,
    color: "bg-sky-50 text-sky-600 border-sky-200",
  },
  custom: {
    label: "Custom Eval",
    icon: <Palette size={12} />,
    color: "bg-rose-50 text-rose-600 border-rose-200",
  },
};

const STEP_ORDER: EvalStatus[] = ["proposed", "launching", "running", "completed"];

function Stepper({ currentStatus }: { currentStatus: EvalStatus }) {
  const isFailed = currentStatus === "failed";
  const currentIdx = isFailed
    ? STEP_ORDER.length
    : STEP_ORDER.indexOf(currentStatus);

  return (
    <div className="flex items-center gap-1 mb-4">
      {STEP_ORDER.map((step, i) => {
        const isActive = i === currentIdx;
        const isCompleted = i < currentIdx && !isFailed;
        const isAllDone = currentStatus === "completed";
        let bg = "bg-stone-200";
        if (isCompleted) bg = "bg-emerald-400";
        if (isActive && !isFailed && !isAllDone) bg = "bg-nobel-gold";
        if (isActive && isAllDone) bg = "bg-emerald-400";
        if (isFailed && i === currentIdx - 1) bg = "bg-red-400";

        return (
          <div key={step} className="flex items-center gap-1 flex-1">
            <div className="flex flex-col items-center flex-1">
              <div
                className={`w-full h-1.5 rounded-full ${bg} transition-colors duration-300`}
              />
              <span
                className={`text-[10px] mt-1 ${
                  isActive ? "text-stone-700 font-bold" : "text-stone-400"
                }`}
              >
                {step.charAt(0).toUpperCase() + step.slice(1)}
              </span>
            </div>
          </div>
        );
      })}
      {isFailed && (
        <div className="flex flex-col items-center flex-1">
          <div className="w-full h-1.5 rounded-full bg-red-400 transition-colors duration-300" />
          <span className="text-[10px] mt-1 text-red-600 font-bold">
            Failed
          </span>
        </div>
      )}
    </div>
  );
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const color =
    score >= 80
      ? "bg-emerald-400"
      : score >= 60
        ? "bg-amber-400"
        : "bg-red-400";

  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-stone-500 w-24 truncate font-medium">
        {label}
      </span>
      <div className="flex-1 bg-stone-100 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${Math.min(score, 100)}%` }}
        />
      </div>
      <span className="text-xs text-stone-700 font-bold w-12 text-right">
        {score.toFixed(1)}%
      </span>
    </div>
  );
}

function BenchmarkScores({ scores }: { scores: TaskScore[] }) {
  if (!scores.length) return null;

  return (
    <div className="space-y-2 mt-3">
      <div className="text-[10px] font-bold tracking-widest text-stone-400 uppercase">
        Benchmark Results
      </div>
      <div className="space-y-1.5">
        {scores.map((s) => (
          <div key={s.task}>
              <ScoreBar score={s.score} label={s.task} />
            </div>
        ))}
      </div>
    </div>
  );
}

function AgentResults({
  scores,
  totalTasks,
}: {
  scores?: TaskScore[];
  totalTasks?: number;
}) {
  if (!scores?.length) return null;

  return (
    <div className="space-y-2 mt-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold tracking-widest text-stone-400 uppercase">
          Task Results
        </span>
        {totalTasks && (
          <span className="text-[10px] text-stone-400">
            {totalTasks} tasks
          </span>
        )}
      </div>
      <div className="space-y-1.5">
        {scores.map((s) => (
          <div key={s.task}>
              <ScoreBar score={s.score} label={s.task} />
            </div>
        ))}
      </div>
    </div>
  );
}

function CustomResults({
  scores,
}: {
  scores?: {
    base_avg_score?: number;
    lora_avg_score?: number;
    score_improvement?: number;
    num_samples: number;
  };
}) {
  if (!scores) return null;

  const improvement = scores.score_improvement ?? 0;
  const isPositive = improvement > 0;

  return (
    <div className="space-y-2 mt-3">
      <div className="text-[10px] font-bold tracking-widest text-stone-400 uppercase">
        Comparison Results
      </div>
      <div className="grid grid-cols-3 gap-3">
        {scores.base_avg_score != null && (
          <div className="bg-stone-50 rounded-lg p-3 text-center">
            <div className="text-[10px] text-stone-400 uppercase font-bold">
              Base
            </div>
            <div className="text-lg font-serif text-stone-700">
              {scores.base_avg_score.toFixed(1)}
            </div>
          </div>
        )}
        {scores.lora_avg_score != null && (
          <div className="bg-stone-50 rounded-lg p-3 text-center">
            <div className="text-[10px] text-stone-400 uppercase font-bold">
              Fine-tuned
            </div>
            <div className="text-lg font-serif text-stone-700">
              {scores.lora_avg_score.toFixed(1)}
            </div>
          </div>
        )}
        <div className="bg-stone-50 rounded-lg p-3 text-center">
          <div className="text-[10px] text-stone-400 uppercase font-bold">
            Delta
          </div>
          <div
            className={`text-lg font-serif flex items-center justify-center gap-1 ${
              isPositive ? "text-emerald-600" : "text-red-600"
            }`}
          >
            {isPositive ? (
              <TrendingUp size={14} />
            ) : (
              <TrendingDown size={14} />
            )}
            {improvement > 0 ? "+" : ""}
            {improvement.toFixed(1)}
          </div>
        </div>
      </div>
      <div className="text-[10px] text-stone-400 text-center">
        {scores.num_samples} samples evaluated
      </div>
    </div>
  );
}

function ConfigGrid({ config }: { config: Record<string, unknown> }) {
  const entries = Object.entries(config).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-baseline gap-2 min-w-0">
          <span className="text-[10px] text-stone-400 font-bold tracking-wider uppercase flex-shrink-0">
            {key.replace(/_/g, " ")}
          </span>
          <span className="text-xs text-stone-700 truncate">
            {typeof value === "object" ? JSON.stringify(value) : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function EvalResultsCard({ card, onWandbUrl }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [jobStatus, setJobStatus] = useState<
    "pending" | "running" | "completed" | "failed"
  >("pending");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [wandbUrl, setWandbUrl] = useState<string | null>(
    card.wandb_url || null,
  );
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const pollStatus = useCallback(
    async (fcId: string) => {
      try {
        const runKey = (card.config.experiment_name || "") as string;
        const params = runKey
          ? `?run_key=${encodeURIComponent(runKey)}`
          : "";
        const res = await fetch(
          `${API_BASE}/api/launch/status/${fcId}${params}`,
        );
        const data = await res.json();
        if (data.status === "completed") {
          setJobStatus("completed");
          if (data.result?.wandb_url) {
            setWandbUrl(data.result.wandb_url);
            onWandbUrl?.(data.result.wandb_url);
          }
          if (pollRef.current) clearInterval(pollRef.current);
        } else if (data.status === "failed") {
          setJobStatus("failed");
          setErrorMsg(data.error || "Modal job failed");
          if (pollRef.current) clearInterval(pollRef.current);
        } else if (data.status === "running" && data.wandb_url) {
          setWandbUrl(data.wandb_url);
          onWandbUrl?.(data.wandb_url);
        }
      } catch {
        // Network error, keep polling
      }
    },
    [card.config, onWandbUrl],
  );

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = useCallback(
    (fcId: string) => {
      setJobStatus("running");
      pollStatus(fcId);
      pollRef.current = setInterval(() => pollStatus(fcId), 5_000);
    },
    [pollStatus],
  );

  useEffect(() => {
    if (
      card.modal_function_call_id &&
      card.status === "running" &&
      !pollRef.current
    ) {
      startPolling(card.modal_function_call_id);
    }
  }, [card.modal_function_call_id, card.status, startPolling]);

  const effectiveStatus =
    jobStatus === "completed"
      ? "completed"
      : jobStatus === "failed"
        ? "failed"
        : card.status;
  const statusConfig =
    STATUS_CONFIG[effectiveStatus] || STATUS_CONFIG[card.status];
  const tierConfig = TIER_CONFIG[card.eval_tier];

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
              <ClipboardCheck size={14} className="text-nobel-gold" />
              <span className="text-xs font-bold tracking-widest text-stone-400 uppercase">
                Evaluation
              </span>
              <div
                className={`flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold border ${tierConfig.color}`}
              >
                {tierConfig.icon}
                {tierConfig.label}
              </div>
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold border ${statusConfig.color}`}
          >
            {statusConfig.icon}
            {statusConfig.label}
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Stepper */}
        <Stepper currentStatus={effectiveStatus} />

        {/* Summary */}
        <p className="text-sm text-stone-600 leading-relaxed mb-3">
          {card.summary}
        </p>

        {/* Average Score Badge */}
        {card.avg_score != null && effectiveStatus === "completed" && (
          <div className="flex items-center gap-3 px-3 py-2 bg-[#F9F8F4] rounded-lg border border-stone-200 mb-3">
            <BarChart3 size={14} className="text-nobel-gold" />
            <span className="text-xs text-stone-500 font-medium">
              Average Score
            </span>
            <span className="text-sm text-stone-900 font-bold">
              {card.avg_score.toFixed(1)}
              {card.eval_tier !== "custom" ? "%" : "/10"}
            </span>
          </div>
        )}

        {/* Cost estimate for proposed state */}
        {card.cost_estimate && effectiveStatus === "proposed" && (
          <div className="flex items-center gap-4 px-3 py-2 bg-[#F9F8F4] rounded-lg border border-stone-200 mb-3">
            <div className="flex items-center gap-1.5">
              <Cpu size={12} className="text-stone-400" />
              <span className="text-xs text-stone-600">
                {card.cost_estimate.gpu_type}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock size={12} className="text-stone-400" />
              <span className="text-xs text-stone-600">
                {card.cost_estimate.estimated_seconds < 60
                  ? `${Math.round(card.cost_estimate.estimated_seconds)}s`
                  : card.cost_estimate.estimated_seconds < 3600
                    ? `${(card.cost_estimate.estimated_seconds / 60).toFixed(1)}min`
                    : `${(card.cost_estimate.estimated_seconds / 3600).toFixed(1)}h`}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign size={12} className="text-stone-400" />
              <span className="text-xs text-stone-900 font-bold">
                ${card.cost_estimate.estimated_cost_usd.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* Tier-specific completed results */}
        {effectiveStatus === "completed" && (
          <>
            {card.eval_tier === "agent" && (
              <AgentResults
                scores={card.task_scores}
                totalTasks={card.total_tasks}
              />
            )}
            {card.eval_tier === "benchmark" && (
              <BenchmarkScores scores={card.benchmark_scores || []} />
            )}
            {card.eval_tier === "custom" && (
              <CustomResults scores={card.custom_scores} />
            )}
          </>
        )}

        {/* Job failure message */}
        {jobStatus === "failed" && errorMsg && (
          <div className="flex items-start gap-2 px-3 py-2 bg-red-50 rounded-lg border border-red-200 mb-3">
            <XCircle
              size={14}
              className="text-red-500 mt-0.5 flex-shrink-0"
            />
            <span className="text-xs text-red-700">{errorMsg}</span>
          </div>
        )}

        {/* Status row */}
        <div className="flex items-center gap-2 mt-2">
          {effectiveStatus === "running" && jobStatus === "running" && (
            <span className="inline-flex items-center gap-1.5 text-xs text-stone-500">
              <Loader2 size={12} className="animate-spin text-nobel-gold" />
              Running on Modal...
            </span>
          )}
          {(wandbUrl || card.wandb_url) && (
            <a
              href={wandbUrl || card.wandb_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-nobel-gold hover:text-stone-700 transition-colors"
            >
              View on W&B
              <ExternalLink size={11} />
            </a>
          )}
        </div>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-center gap-1 py-2 border-t border-stone-100 text-xs text-stone-400 hover:text-stone-600 hover:bg-stone-50 transition-colors"
      >
        {expanded ? (
          <>
            <ChevronUp size={12} /> Hide configuration
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show configuration
          </>
        )}
      </button>

      {/* Expandable config */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-stone-100 px-5 py-4"
        >
          <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
            Configuration
          </div>
          <ConfigGrid config={card.config} />
        </motion.div>
      )}
    </motion.div>
  );
}
