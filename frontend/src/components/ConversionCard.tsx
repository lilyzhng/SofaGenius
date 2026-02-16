import { useState } from "react";
import { motion } from "framer-motion";
import {
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Eye,
} from "lucide-react";
import type { ConversionCard as ConversionCardType } from "../types";

interface Props {
  card: ConversionCardType;
}

function FormatBadge({ format, variant }: { format: string; variant: "source" | "target" }) {
  const colors =
    variant === "source"
      ? "bg-stone-100 text-stone-600 border-stone-200"
      : "bg-nobel-gold/10 text-nobel-gold border-nobel-gold/30";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold tracking-wide uppercase border ${colors}`}
    >
      {format}
    </span>
  );
}

function SamplePanel({ label, sample }: { label: string; sample: Record<string, string> }) {
  return (
    <div className="flex-1 min-w-0">
      <div className="text-[10px] font-bold tracking-widest text-stone-400 uppercase mb-2">
        {label}
      </div>
      <div className="bg-stone-900 rounded-lg p-3 overflow-x-auto">
        <pre className="text-xs text-stone-300 whitespace-pre-wrap break-words leading-relaxed">
          {Object.entries(sample).map(([key, value]) => (
            <div key={key} className="mb-1.5">
              <span className="text-nobel-gold font-semibold">{key}</span>
              <span className="text-stone-500">: </span>
              <span className="text-stone-300">{value}</span>
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

export default function ConversionCard({ card }: Props) {
  const [expanded, setExpanded] = useState(false);

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
              <RefreshCw size={14} className="text-stone-400" />
              <span className="text-xs font-bold tracking-widest text-stone-400 uppercase">
                Conversion Preview
              </span>
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-nobel-gold/10 text-nobel-gold border border-nobel-gold/30">
            <Eye size={10} />
            {card.preview_count} rows
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-4" />

        {/* Format badges */}
        <div className="flex items-center gap-2 mb-3">
          <FormatBadge format={card.source_format} variant="source" />
          <ArrowRight size={14} className="text-stone-400" />
          <FormatBadge format={card.target_format} variant="target" />
        </div>

        {/* Source columns */}
        <div className="flex flex-wrap gap-1.5">
          {card.source_columns.map((col) => (
            <span
              key={col}
              className="px-2 py-0.5 text-[10px] font-medium rounded bg-stone-100 text-stone-500"
            >
              {col}
            </span>
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
            <ChevronUp size={12} /> Hide samples
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show before / after
          </>
        )}
      </button>

      {/* Expandable before/after */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-stone-100 px-5 py-4 space-y-4"
        >
          {card.before_samples.map((before, i) => (
            <div key={i} className="space-y-1">
              {i > 0 && <div className="border-t border-stone-100 pt-3" />}
              <div className="text-[10px] font-bold tracking-widest text-stone-300 uppercase mb-2">
                Row {i + 1}
              </div>
              <div className="flex gap-3">
                <SamplePanel label="Before" sample={before} />
                {card.after_samples[i] && (
                  <SamplePanel label="After" sample={card.after_samples[i]} />
                )}
              </div>
            </div>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
