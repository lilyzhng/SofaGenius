import { useState } from "react";
import { motion } from "framer-motion";
import {
  PenLine,
  ChevronDown,
  ChevronUp,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Edit3,
  Loader2,
} from "lucide-react";
import type { DraftPostCard as DraftPostCardType, EvidenceRef } from "../types";

interface Props {
  card: DraftPostCardType;
}

function CharCountIndicator({ count }: { count: number }) {
  let color = "text-emerald-600 bg-emerald-50 border-emerald-200";
  if (count > 300) {
    color = "text-red-600 bg-red-50 border-red-200";
  } else if (count > 280) {
    color = "text-amber-600 bg-amber-50 border-amber-200";
  }
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold border ${color}`}
    >
      {count}/280
    </span>
  );
}

function ConfidenceBadge({ confidence }: { confidence: string }) {
  if (confidence === "finding") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
        <CheckCircle2 size={10} />
        Finding
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-600 border border-amber-200">
      <AlertTriangle size={10} />
      Hypothesis
    </span>
  );
}

function EvidenceItem({ evidence }: { evidence: EvidenceRef }) {
  return (
    <div className="flex items-start gap-3 py-2">
      <div className="flex-shrink-0 mt-0.5">
        <span className="inline-block px-1.5 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded bg-stone-100 text-stone-500">
          {evidence.source}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-stone-600 leading-relaxed">
          {evidence.snippet}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <ConfidenceBadge confidence={evidence.confidence} />
          {evidence.link && (
            <a
              href={evidence.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[10px] text-nobel-gold hover:text-stone-700 transition-colors"
            >
              <ExternalLink size={10} />
              Source
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DraftPostCard({ card }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [postStatus, setPostStatus] = useState<
    "idle" | "posting" | "posted" | "error"
  >("idle");
  const [tweetUrl, setTweetUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApprove = async () => {
    setPostStatus("posting");
    setErrorMsg(null);
    try {
      const res = await fetch("/api/tweet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: card.draft_text,
          thread: card.thread.length > 0 ? card.thread : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setPostStatus("error");
        setErrorMsg(data.error || "Failed to post tweet");
        return;
      }
      setPostStatus("posted");
      setTweetUrl(data.tweet_url);
    } catch (e) {
      setPostStatus("error");
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
            <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-1">
              Draft Post
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-600 border border-amber-200">
            <ShieldAlert size={12} />
            Requires Approval
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Tweet preview card */}
        <div className="bg-[#F9F8F4] rounded-lg border border-stone-200 p-4">
          <p className="text-sm text-stone-800 leading-relaxed whitespace-pre-wrap">
            {card.draft_text}
          </p>
          <div className="flex items-center justify-between mt-3 pt-2 border-t border-stone-200">
            <CharCountIndicator count={card.char_count} />
            {card.tone && (
              <span className="px-2 py-0.5 text-[10px] font-bold tracking-wider uppercase rounded-full border border-stone-200 text-stone-400">
                {card.tone}
              </span>
            )}
          </div>
        </div>

        {/* Thread (if any) */}
        {card.thread.length > 0 && (
          <div className="mt-2 space-y-2 pl-4 border-l-2 border-nobel-gold/30">
            {card.thread.map((tweet, i) => (
              <div
                key={i}
                className="bg-[#F9F8F4] rounded-lg border border-stone-200 p-3"
              >
                <div className="text-[10px] text-stone-400 mb-1">
                  {i + 2}/{card.thread.length + 1}
                </div>
                <p className="text-xs text-stone-700 leading-relaxed whitespace-pre-wrap">
                  {tweet}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Approval buttons */}
        <div className="flex items-center gap-2 mt-4">
          {postStatus === "idle" && (
            <button
              onClick={handleApprove}
              className="px-4 py-1.5 text-xs font-bold rounded-full border-2 border-amber-400 text-amber-700 bg-amber-50 hover:bg-amber-100 transition-colors"
            >
              Approve & Post
            </button>
          )}
          {postStatus === "posting" && (
            <button
              disabled
              className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-stone-300 text-stone-400 bg-stone-50 cursor-not-allowed"
            >
              <Loader2 size={12} className="animate-spin" />
              Posting...
            </button>
          )}
          {postStatus === "posted" && (
            <span className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-emerald-400 text-emerald-700 bg-emerald-50">
              <CheckCircle2 size={12} />
              Posted!
              {tweetUrl && (
                <a
                  href={tweetUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 ml-1 underline hover:text-emerald-900 transition-colors"
                >
                  View <ExternalLink size={10} />
                </a>
              )}
            </span>
          )}
          {postStatus === "error" && (
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
          {postStatus !== "posted" && (
            <button className="inline-flex items-center gap-1 px-4 py-1.5 text-xs font-bold rounded-full border border-stone-300 text-stone-500 hover:border-stone-400 hover:text-stone-600 transition-colors cursor-default">
              <Edit3 size={10} />
              Edit Draft
            </button>
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
            <ChevronUp size={12} /> Hide evidence
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show evidence
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
          {/* Evidence references */}
          {card.evidence.length > 0 && (
            <div className="px-5 py-4">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Evidence
              </div>
              <div className="divide-y divide-stone-100">
                {card.evidence.map((ev, i) => (
                  <EvidenceItem key={i} evidence={ev} />
                ))}
              </div>
            </div>
          )}

          {card.evidence.length === 0 && (
            <div className="px-5 py-4">
              <div className="text-xs text-stone-400 italic">
                No evidence references attached. All claims should be treated as hypotheses.
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
