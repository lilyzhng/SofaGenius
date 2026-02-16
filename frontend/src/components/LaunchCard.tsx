import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Rocket,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Loader2,
  Cpu,
  DollarSign,
  Clock,
  XCircle,
} from "lucide-react";
// Rocket kept for header icon
import type { LaunchCard as LaunchCardType, LaunchStatus } from "../types";

interface Props {
  card: LaunchCardType;
  onWandbUrl?: (url: string) => void;
}

const STATUS_CONFIG: Record<
  LaunchStatus,
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

const STEP_ORDER: LaunchStatus[] = [
  "proposed",
  "launching",
  "running",
  "completed",
];

function Stepper({ currentStatus }: { currentStatus: LaunchStatus }) {
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
            {String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function LaunchCard({ card, onWandbUrl }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [jobStatus, setJobStatus] = useState<
    "pending" | "running" | "completed" | "failed"
  >("pending");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [wandbUrl, setWandbUrl] = useState<string | null>(
    card.wandb_url || null,
  );
  const [functionCallId, setFunctionCallId] = useState<string | null>(
    card.modal_function_call_id || null,
  );
  const [actualCost, setActualCost] = useState<{
    execution_seconds: number;
    cost_usd: number;
    gpu_type: string;
  } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Exact per-second rates from https://modal.com/pricing
  const GPU_RATE_PER_SEC: Record<string, number> = {
    B200: 0.001736, H200: 0.001261, H100: 0.001097,
    A100: 0.000694, "A100-40GB": 0.000583, L40S: 0.000542,
    A10: 0.000306, L4: 0.000222, T4: 0.000164,
  };

  const pollStatus = useCallback(async (fcId: string) => {
    try {
      // Pass run_key so backend can look up W&B URL from modal.Dict
      const runKey = (card.config.experiment_name || card.config.run_name || "") as string;
      const params = runKey ? `?run_key=${encodeURIComponent(runKey)}` : "";
      const res = await fetch(`/api/launch/status/${fcId}${params}`);
      const data = await res.json();
      if (data.status === "completed") {
        setJobStatus("completed");
        if (data.result?.wandb_url) {
          setWandbUrl(data.result.wandb_url);
          onWandbUrl?.(data.result.wandb_url);
        }
        // Compute actual cost from Modal's execution time
        if (data.execution_seconds != null) {
          const gpuType = (card.config.gpu_type as string) || "A100";
          const rate = GPU_RATE_PER_SEC[gpuType] ?? GPU_RATE_PER_SEC.A100;
          const seconds = data.execution_seconds;
          setActualCost({
            execution_seconds: seconds,
            cost_usd: seconds * rate,
            gpu_type: gpuType,
          });
        }
        if (pollRef.current) clearInterval(pollRef.current);
      } else if (data.status === "failed") {
        setJobStatus("failed");
        setErrorMsg(data.error || "Modal job failed");
        if (pollRef.current) clearInterval(pollRef.current);
      } else if (data.status === "running" && data.wandb_url) {
        // Got the real W&B run URL from modal.Dict while job is still running
        setWandbUrl(data.wandb_url);
        onWandbUrl?.(data.wandb_url);
      }
    } catch {
      // Network error, keep polling
    }
  }, [card.config]);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = useCallback((fcId: string) => {
    setFunctionCallId(fcId);
    setJobStatus("running");
    // Fire immediately, then every 5 seconds
    pollStatus(fcId);
    pollRef.current = setInterval(() => pollStatus(fcId), 5_000);
  }, [pollStatus]);

  // If card already has a function_call_id (chat path), start polling
  useEffect(() => {
    if (card.modal_function_call_id && card.status === "running" && !pollRef.current) {
      startPolling(card.modal_function_call_id);
    }
  }, [card.modal_function_call_id, card.status, startPolling]);

  const effectiveStatus = jobStatus === "completed" ? "completed"
    : jobStatus === "failed" ? "failed"
    : card.status;
  const statusConfig = STATUS_CONFIG[effectiveStatus] || STATUS_CONFIG[card.status];
  const isRunningOrDone =
    effectiveStatus === "running" || effectiveStatus === "completed";

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
              <Rocket size={14} className="text-nobel-gold" />
              <span className="text-xs font-bold tracking-widest text-stone-400 uppercase">
                {card.launch_type === "finetune"
                  ? "Fine-tuning Job"
                  : "Evaluation Job"}
              </span>
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

        {/* Cost — only show once we have actual data from Modal */}
        {actualCost && (
          <div className="flex items-center gap-4 px-3 py-2 bg-[#F9F8F4] rounded-lg border border-stone-200 mb-3">
            <div className="flex items-center gap-1.5">
              <Cpu size={12} className="text-stone-400" />
              <span className="text-xs text-stone-600">
                {actualCost.gpu_type}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <Clock size={12} className="text-stone-400" />
              <span className="text-xs text-stone-600">
                {actualCost.execution_seconds < 60
                  ? `${Math.round(actualCost.execution_seconds)}s`
                  : `${(actualCost.execution_seconds / 60).toFixed(1)}min`}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign size={12} className="text-stone-400" />
              <span className="text-xs text-stone-900 font-bold">
                ${actualCost.cost_usd.toFixed(4)}
              </span>
            </div>
          </div>
        )}

        {/* Job failure message */}
        {jobStatus === "failed" && errorMsg && (
          <div className="flex items-start gap-2 px-3 py-2 bg-red-50 rounded-lg border border-red-200 mb-3">
            <XCircle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
            <span className="text-xs text-red-700">{errorMsg}</span>
          </div>
        )}

        {/* Status row */}
        <div className="flex items-center gap-2 mt-2">
          {isRunningOrDone && jobStatus === "running" && (
            <span className="inline-flex items-center gap-1.5 text-xs text-stone-500">
              <Loader2 size={12} className="animate-spin text-nobel-gold" />
              Running on Modal...
            </span>
          )}
          {wandbUrl && (
            <a
              href={wandbUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-nobel-gold hover:text-stone-700 transition-colors"
            >
              {wandbUrl.includes("/runs/")
                ? `View run ${wandbUrl.split("/runs/").pop()?.split("?")[0] ?? ""}`
                : "W&B project"}
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

          {card.cost_estimate?.note && (
            <div className="mt-3 flex items-start gap-1.5">
              <AlertTriangle
                size={11}
                className="text-stone-400 mt-0.5 flex-shrink-0"
              />
              <span className="text-[10px] text-stone-400 italic">
                {card.cost_estimate.note}
              </span>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
