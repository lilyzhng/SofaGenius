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
import type { LaunchCard as LaunchCardType, LaunchStatus } from "../types";

interface Props {
  card: LaunchCardType;
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
        const isBefore = i < currentIdx;
        let bg = "bg-stone-200";
        if (isCompleted || (isBefore && !isFailed)) bg = "bg-emerald-400";
        if (isActive && !isFailed) bg = "bg-nobel-gold";
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

export default function LaunchCard({ card }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [launchStatus, setLaunchStatus] = useState<
    "idle" | "launching" | "launched" | "error"
  >("idle");
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
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const pollStatus = useCallback(async (fcId: string) => {
    try {
      const res = await fetch(`/api/launch/status/${fcId}`);
      const data = await res.json();
      if (data.status === "completed") {
        setJobStatus("completed");
        if (data.result?.wandb_url) {
          setWandbUrl(data.result.wandb_url);
        }
        if (pollRef.current) clearInterval(pollRef.current);
      } else if (data.status === "failed") {
        setJobStatus("failed");
        setErrorMsg(data.error || "Modal job failed");
        if (pollRef.current) clearInterval(pollRef.current);
      }
      // "running" — keep polling
    } catch {
      // Network error, keep polling
    }
  }, []);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = (fcId: string) => {
    setFunctionCallId(fcId);
    setJobStatus("running");
    // Poll every 10 seconds
    pollRef.current = setInterval(() => pollStatus(fcId), 10_000);
  };

  // If card already has a function_call_id (chat path), start polling
  useEffect(() => {
    if (card.modal_function_call_id && card.status === "running" && !pollRef.current) {
      startPolling(card.modal_function_call_id);
    }
  }, [card.modal_function_call_id, card.status]);

  const effectiveStatus = launchStatus === "launched"
    ? (jobStatus === "completed" ? "completed" : jobStatus === "failed" ? "failed" : "running")
    : card.status;
  const statusConfig = STATUS_CONFIG[effectiveStatus] || STATUS_CONFIG[card.status];
  const isProposed = card.status === "proposed";
  const isRunningOrDone =
    effectiveStatus === "running" || effectiveStatus === "completed";

  const handleApprove = async () => {
    setLaunchStatus("launching");
    setErrorMsg(null);
    try {
      const res = await fetch("/api/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          launch_type: card.launch_type,
          config: card.config,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setLaunchStatus("error");
        setErrorMsg(data.error || "Failed to launch job");
        return;
      }
      setLaunchStatus("launched");
      // Start polling for the real W&B run URL and job status
      if (data.function_call_id) {
        startPolling(data.function_call_id);
      }
    } catch (e) {
      setLaunchStatus("error");
      setErrorMsg(e instanceof Error ? e.message : "Network error");
    }
  };

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

        {/* Cost estimate */}
        {card.cost_estimate && (
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
                ~{card.cost_estimate.estimated_hours}h
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <DollarSign size={12} className="text-stone-400" />
              <span className="text-xs text-stone-600 font-bold">
                ~${card.cost_estimate.estimated_cost_usd.toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* W&B link */}
        {wandbUrl && isRunningOrDone && (
          <a
            href={wandbUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs text-nobel-gold hover:text-stone-700 transition-colors mb-3"
          >
            <ExternalLink size={12} />
            {wandbUrl.includes("/runs/") ? "View run on W&B" : "Monitor on W&B"}
          </a>
        )}

        {/* Job failure message */}
        {jobStatus === "failed" && errorMsg && (
          <div className="flex items-start gap-2 px-3 py-2 bg-red-50 rounded-lg border border-red-200 mb-3">
            <XCircle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
            <span className="text-xs text-red-700">{errorMsg}</span>
          </div>
        )}

        {/* Job completed message */}
        {jobStatus === "completed" && (
          <div className="flex items-start gap-2 px-3 py-2 bg-emerald-50 rounded-lg border border-emerald-200 mb-3">
            <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
            <span className="text-xs text-emerald-700">Job completed successfully.</span>
          </div>
        )}

        {/* Approval buttons */}
        {isProposed && (
          <div className="flex items-center gap-2 mt-2">
            {launchStatus === "idle" && (
              <button
                onClick={handleApprove}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-amber-400 text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors"
              >
                <Rocket size={12} />
                Approve & Launch
              </button>
            )}
            {launchStatus === "launching" && (
              <button
                disabled
                className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-stone-300 text-stone-400 bg-stone-50 cursor-not-allowed"
              >
                <Loader2 size={12} className="animate-spin" />
                Launching...
              </button>
            )}
            {launchStatus === "launched" && (
              <span className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-emerald-400 text-emerald-700 bg-emerald-50">
                <CheckCircle2 size={12} />
                Launched!
                {wandbUrl && (
                  <a
                    href={wandbUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-0.5 ml-1 underline hover:text-emerald-900 transition-colors"
                  >
                    W&B <ExternalLink size={10} />
                  </a>
                )}
              </span>
            )}
            {launchStatus === "error" && (
              <>
                <button
                  onClick={handleApprove}
                  className="px-4 py-1.5 text-xs font-bold rounded-full border-2 border-red-400 text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
                >
                  Retry
                </button>
                {errorMsg && (
                  <span className="text-xs text-red-600">{errorMsg}</span>
                )}
              </>
            )}
          </div>
        )}

        {/* Polling indicator */}
        {launchStatus === "launched" && jobStatus === "running" && (
          <div className="flex items-center gap-1.5 mt-2 text-xs text-stone-400">
            <Loader2 size={10} className="animate-spin" />
            Waiting for job result...
          </div>
        )}
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
