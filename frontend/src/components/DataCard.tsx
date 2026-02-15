import { useState } from "react";
import { motion } from "framer-motion";
import {
  Database,
  ChevronDown,
  ChevronUp,
  Clock,
  TrendingUp,
  Code,
} from "lucide-react";
import DataTable from "./DataTable";
import DataPlot from "./DataPlot";
import type { DataCard as DataCardType, StatsSummary } from "../types";

interface Props {
  card: DataCardType;
}

function StatCard({ stat }: { stat: StatsSummary }) {
  if (stat.kind === "numeric") {
    return (
      <div className="bg-nobel-cream rounded-lg p-3 border border-stone-100">
        <div className="text-xs font-bold text-stone-600 uppercase tracking-wider mb-2">
          {stat.column}
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <div className="text-stone-400">Mean</div>
          <div className="text-stone-700 font-medium">{stat.mean?.toFixed(4)}</div>
          <div className="text-stone-400">Std</div>
          <div className="text-stone-700 font-medium">{stat.std?.toFixed(4)}</div>
          <div className="text-stone-400">Min</div>
          <div className="text-stone-700 font-medium">{stat.min?.toFixed(4)}</div>
          <div className="text-stone-400">Max</div>
          <div className="text-stone-700 font-medium">{stat.max?.toFixed(4)}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-nobel-cream rounded-lg p-3 border border-stone-100">
      <div className="text-xs font-bold text-stone-600 uppercase tracking-wider mb-2">
        {stat.column}
      </div>
      <div className="text-xs text-stone-400 mb-1">
        {stat.unique_count} unique values
      </div>
      {stat.top_values && (
        <div className="space-y-1">
          {stat.top_values.slice(0, 5).map((entry, i) => {
            const [key, count] = Object.entries(entry)[0];
            return (
              <div key={i} className="flex justify-between text-xs">
                <span className="text-stone-600 truncate mr-2">{key}</span>
                <span className="text-stone-400 flex-shrink-0">{count}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function DataCard({ card }: Props) {
  const [expanded, setExpanded] = useState(true);
  const [sqlExpanded, setSqlExpanded] = useState(false);

  const isLongQuery = card.sql_query.length > 80;

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
              Data Analysis
            </div>
            <h3 className="font-serif text-lg text-stone-900 leading-snug">
              {card.title}
            </h3>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-600 border border-blue-200">
            <Database size={12} />
            {card.query_result
              ? `${card.query_result.row_count} rows`
              : "Query"}
          </div>
        </div>

        {/* Gold divider */}
        <div className="w-12 h-0.5 bg-nobel-gold mb-3" />

        {/* Summary */}
        <p className="text-sm text-stone-600 leading-relaxed">{card.summary}</p>

        {/* SQL Query */}
        <div className="mt-3">
          <button
            onClick={() => setSqlExpanded(!sqlExpanded)}
            className="inline-flex items-center gap-1.5 text-xs text-stone-400 hover:text-stone-600 transition-colors"
          >
            <Code size={12} />
            SQL Query
            {card.query_result && (
              <span className="text-stone-300">
                <Clock size={10} className="inline ml-1" />
                {card.query_result.execution_time_ms}ms
              </span>
            )}
          </button>
          {(sqlExpanded || !isLongQuery) && (
            <pre className="mt-1.5 p-3 bg-stone-900 text-stone-100 rounded-lg text-xs overflow-x-auto font-mono">
              {card.sql_query}
            </pre>
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
            <ChevronUp size={12} /> Hide details
          </>
        ) : (
          <>
            <ChevronDown size={12} /> Show results & stats
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
          {/* Plot */}
          {card.plot && (
            <div className="px-5 py-4">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Visualization
              </div>
              <DataPlot plot={card.plot} />
            </div>
          )}

          {/* Stats */}
          {card.stats && card.stats.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Column Statistics
              </div>
              <div className="grid grid-cols-2 gap-3">
                {card.stats.map((stat, i) => (
                  <StatCard key={i} stat={stat} />
                ))}
              </div>
            </div>
          )}

          {/* Query results table */}
          {card.query_result && card.query_result.rows.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Query Results
              </div>
              <DataTable result={card.query_result} />
            </div>
          )}

          {/* Suggested next queries */}
          {card.next_suggestions && card.next_suggestions.length > 0 && (
            <div className="px-5 py-4 border-t border-stone-100">
              <div className="text-xs font-bold tracking-widest text-stone-400 uppercase mb-3">
                Try Next
              </div>
              <div className="flex flex-wrap gap-2">
                {card.next_suggestions.map((suggestion, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border border-stone-200 text-stone-600 hover:border-nobel-gold/50 hover:text-stone-800 transition-colors cursor-default"
                  >
                    <TrendingUp size={10} className="text-nobel-gold" />
                    {suggestion}
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
