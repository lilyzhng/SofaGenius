import { useState } from "react";
import { motion } from "framer-motion";
import {
  Compass,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Download,
  Heart,
  Database,
  Cpu,
} from "lucide-react";
import type { ScoutCard as ScoutCardType, ScoutRecommendation } from "../types";

interface Props {
  card: ScoutCardType;
}

function ResourceBadge({ type }: { type: string }) {
  if (type === "model") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-purple-50 text-purple-600 border border-purple-200">
        <Cpu size={10} />
        Model
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
      <Database size={10} />
      Dataset
    </span>
  );
}

function RecommendationItem({ rec }: { rec: ScoutRecommendation }) {
  return (
    <div className="bg-white rounded-lg border border-stone-200 p-4 hover:shadow-sm transition-all duration-200">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <ResourceBadge type={rec.resource_type} />
          </div>
          <a
            href={rec.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-stone-900 hover:text-nobel-gold transition-colors inline-flex items-center gap-1"
          >
            {rec.name}
            <ExternalLink size={12} className="text-stone-400" />
          </a>
        </div>
        <div className="flex items-center gap-3 text-xs text-stone-400 flex-shrink-0">
          <span className="inline-flex items-center gap-1">
            <Download size={10} />
            {rec.downloads >= 1000
              ? `${(rec.downloads / 1000).toFixed(1)}k`
              : rec.downloads}
          </span>
          <span className="inline-flex items-center gap-1">
            <Heart size={10} />
            {rec.likes}
          </span>
        </div>
      </div>

      {/* Description */}
      {rec.description && (
        <p className="text-xs text-stone-500 mb-2 leading-relaxed">
          {rec.description}
        </p>
      )}

      {/* Tags */}
      {rec.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {rec.tags.slice(0, 6).map((tag, i) => (
            <span
              key={i}
              className="px-1.5 py-0.5 text-[10px] font-medium rounded bg-stone-100 text-stone-500"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Reasoning */}
      {rec.reasoning && (
        <div className="p-3 bg-[#F9F8F4] border border-stone-200 rounded-lg border-l-4 border-l-nobel-gold mb-2">
          <div className="text-[10px] font-bold tracking-widest text-stone-400 uppercase mb-1">
            Why this pick
          </div>
          <p className="text-xs text-stone-600 italic leading-relaxed">
            {rec.reasoning}
          </p>
        </div>
      )}

      {/* Tradeoffs */}
      {rec.tradeoffs && (
        <div className="p-3 bg-amber-50/50 border border-amber-200/50 rounded-lg">
          <div className="text-[10px] font-bold tracking-widest text-amber-600 uppercase mb-1">
            Tradeoffs
          </div>
          <p className="text-xs text-stone-600 leading-relaxed">
            {rec.tradeoffs}
          </p>
        </div>
      )}
    </div>
  );
}

export default function ScoutCard({ card }: Props) {
  const [expanded, setExpanded] = useState(true);

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
              Scout
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-nobel-gold/10 text-nobel-gold border border-nobel-gold/30">
            <Compass size={12} />
            {card.recommendations.length} picks
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Summary */}
        <p className="text-sm text-stone-600 leading-relaxed">{card.summary}</p>
      </div>

      {/* Expand toggle */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-center gap-1 py-2 border-t border-stone-100 text-xs text-stone-400 hover:text-stone-600 hover:bg-stone-50 transition-colors"
      >
        {expanded ? (
          <>
            <ChevronUp size={12} /> Hide recommendations
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show recommendations
          </>
        )}
      </button>

      {/* Expandable recommendations */}
      {expanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="border-t border-stone-100 px-5 py-4"
        >
          <div className="space-y-3">
            {card.recommendations.map((rec, i) => (
              <RecommendationItem key={i} rec={rec} />
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
