import { motion } from "framer-motion";
import { Bot, Check, Loader2, AlertCircle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Message, ToolCall, MessageSegment } from "../types";

interface Props {
  message: Message;
}

const TOOL_LABELS: Record<string, string> = {
  get_wandb_info: "Fetching W&B info",
  list_wandb_runs: "Listing runs",
  get_run_metrics: "Fetching metrics",
  analyze_run_health: "Analyzing run health",
  search_hf_datasets: "Searching HF datasets",
  discover_dataset_schema: "Discovering schema",
  run_sql_query: "Running SQL query",
  compute_stats: "Computing statistics",
  generate_plot_data: "Generating visualization",
  create_data_card: "Creating data card",
  search_hf_models: "Searching HF models",
  create_scout_card: "Creating scout card",
  create_draft_post_card: "Creating draft post",
};

function ToolStep({ tool }: { tool: ToolCall }) {
  const label = TOOL_LABELS[tool.name] || tool.name;

  return (
    <div className="flex items-start gap-2 py-0.5 pl-3 border-l-2 border-stone-200 ml-1">
      <div className="flex-shrink-0 mt-0.5">
        {tool.status === "running" && (
          <Loader2 size={11} className="animate-spin text-nobel-gold" />
        )}
        {tool.status === "done" && (
          <Check size={11} className="text-emerald-500" />
        )}
        {tool.status === "error" && (
          <AlertCircle size={11} className="text-red-500" />
        )}
      </div>
      <div className="min-w-0">
        <span
          className={`text-xs ${
            tool.status === "running"
              ? "text-stone-600"
              : tool.status === "error"
                ? "text-red-500"
                : "text-stone-400"
          }`}
        >
          {label}
        </span>
        {tool.result && (
          <span className="text-xs text-stone-300 ml-1">
            — {tool.result}
          </span>
        )}
      </div>
    </div>
  );
}

const markdownComponents = {
  h1: ({ children }: { children?: React.ReactNode }) => <h3 className="text-base font-serif font-bold text-stone-900 mt-3 mb-1">{children}</h3>,
  h2: ({ children }: { children?: React.ReactNode }) => <h3 className="text-sm font-serif font-bold text-stone-900 mt-3 mb-1">{children}</h3>,
  h3: ({ children }: { children?: React.ReactNode }) => <h4 className="text-sm font-bold text-stone-800 mt-2 mb-1">{children}</h4>,
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="text-sm">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => <strong className="font-semibold text-stone-900">{children}</strong>,
  code: ({ children, className }: { children?: React.ReactNode; className?: string }) => {
    const isBlock = className?.includes("language-");
    return isBlock ? (
      <code className="block bg-stone-100 rounded-lg p-3 text-xs font-mono overflow-x-auto my-2">{children}</code>
    ) : (
      <code className="bg-stone-100 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
    );
  },
  pre: ({ children }: { children?: React.ReactNode }) => <pre className="bg-stone-100 rounded-lg p-3 overflow-x-auto my-2 text-xs">{children}</pre>,
  a: ({ href, children }: { href?: string; children?: React.ReactNode }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-nobel-gold underline hover:text-stone-900 transition-colors">
      {children}
    </a>
  ),
  blockquote: ({ children }: { children?: React.ReactNode }) => (
    <blockquote className="border-l-2 border-nobel-gold pl-3 my-2 text-stone-500 italic">{children}</blockquote>
  ),
  hr: () => <hr className="border-stone-200 my-3" />,
  table: ({ children }: { children?: React.ReactNode }) => (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full text-xs border-collapse">{children}</table>
    </div>
  ),
  th: ({ children }: { children?: React.ReactNode }) => <th className="border border-stone-200 bg-stone-50 px-2 py-1 text-left font-semibold">{children}</th>,
  td: ({ children }: { children?: React.ReactNode }) => <td className="border border-stone-200 px-2 py-1">{children}</td>,
};

function TextSegment({ content }: { content: string }) {
  return (
    <div className="prose prose-sm prose-stone max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
      <ReactMarkdown components={markdownComponents}>{content}</ReactMarkdown>
    </div>
  );
}

function SegmentRenderer({ segments }: { segments: MessageSegment[] }) {
  return (
    <div className="space-y-2">
      {segments.map((seg, i) =>
        seg.type === "text" ? (
          <TextSegment key={i} content={seg.content} />
        ) : (
          <ToolStep key={i} tool={seg.tool} />
        ),
      )}
    </div>
  );
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const hasSegments = message.segments && message.segments.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      {isUser ? (
        <img
          src="/avatar.png"
          alt="You"
          className="w-8 h-8 rounded-full object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-nobel-gold text-white">
          <Bot size={14} />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
          isUser
            ? "bg-stone-900 text-white rounded-br-sm"
            : "bg-white border border-stone-200 shadow-sm text-stone-700 rounded-bl-sm"
        }`}
      >
        {isUser ? (
          // User messages: just render content
          <p>{message.content}</p>
        ) : hasSegments ? (
          // Assistant with segments: render interleaved text + tools
          <SegmentRenderer segments={message.segments!} />
        ) : message.content ? (
          // Assistant with content but no segments (older messages)
          <TextSegment content={message.content} />
        ) : (
          // Empty: thinking state
          <div className="flex items-center gap-2 text-stone-400">
            <div className="w-1.5 h-1.5 bg-nobel-gold rounded-full animate-pulse" />
            <span className="text-xs">Thinking...</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
