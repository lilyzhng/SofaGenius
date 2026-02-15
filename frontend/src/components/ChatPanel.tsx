import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Square, Activity, Database, Search, Compass, PenLine, Rocket } from "lucide-react";
import MessageBubble from "./MessageBubble";
import type { Message, CardData, LaunchCard } from "../types";

interface Props {
  messages: Message[];
  cards: CardData[];
  isLoading: boolean;
  activeToolCall: string | null;
  onSend: (message: string) => void;
  onStop: () => void;
}

const EXAMPLES = [
  { icon: Activity, text: "Check my latest W&B run health", query: "Analyze the health of my latest W&B run" },
  { icon: Database, text: "List my recent runs", query: "List my W&B runs" },
  { icon: Search, text: "Find loss anomalies", query: "Check for any loss spikes or anomalies in my training run" },
  { icon: Compass, text: "Scout models & datasets", query: "Scout datasets and models for fine-tuning Qwen2.5-Coder-14B" },
  { icon: PenLine, text: "Draft a tweet about findings", query: "Draft a tweet about what we found" },
  { icon: Rocket, text: "Fine-tune a model on Modal", query: "Fine-tune Qwen2.5-Coder-14B on lilyzhng/uigen-ui-code-gen" },
];

function LaunchApprovalButton({
  onSend,
}: {
  onSend: (msg: string) => void;
}) {
  const [approved, setApproved] = useState(false);

  const handleApprove = () => {
    setApproved(true);
    // Send a natural approval message — the agent will call launch_finetune/launch_eval
    onSend("Approved. Go ahead and launch it.");
  };

  if (approved) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="ml-11"
    >
      <button
        onClick={handleApprove}
        className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-nobel-gold text-stone-700 bg-nobel-gold/10 hover:bg-nobel-gold/20 transition-colors"
      >
        <Rocket size={12} />
        Approve & Launch
      </button>
    </motion.div>
  );
}

export default function ChatPanel({
  messages,
  cards,
  isLoading,
  activeToolCall,
  onSend,
  onStop,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, activeToolCall]);

  const handleSubmit = () => {
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  // Show approval button only if the latest launch card is "proposed"
  // (once a running/completed card appears, the proposal has been acted on)
  const launchCards = cards.filter((c): c is LaunchCard => c.card_type === "launch_card");
  const latestLaunchCard = launchCards.length > 0 ? launchCards[launchCards.length - 1] : null;
  const pendingLaunchCard = latestLaunchCard?.status === "proposed" ? latestLaunchCard : null;

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-6">
            <div className="w-12 h-12 bg-nobel-gold rounded-full flex items-center justify-center text-white font-serif font-bold text-2xl mb-4 shadow-sm">
              S
            </div>
            <h2 className="font-serif text-2xl text-stone-900 mb-2">
              Sofa Genius
            </h2>
            <div className="w-12 h-0.5 bg-nobel-gold mb-4" />
            <p className="text-sm text-stone-500 max-w-sm mb-8">
              Your AI research assistant. Ask me to monitor your W&B training
              runs, detect anomalies, and suggest fixes.
            </p>
            <div className="grid gap-3 w-full max-w-sm">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.text}
                  onClick={() => onSend(ex.query)}
                  className="flex items-center gap-3 px-4 py-3 bg-white border border-stone-200 rounded-xl text-left text-sm text-stone-600 hover:border-nobel-gold/50 hover:shadow-sm transition-all duration-200"
                >
                  <ex.icon size={16} className="text-nobel-gold flex-shrink-0" />
                  <span>{ex.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Inline approval button for pending launch cards */}
            {pendingLaunchCard && !isLoading && (
              <LaunchApprovalButton onSend={onSend} />
            )}
          </>
        )}

        {/* Active tool call indicator */}
        <AnimatePresence>
          {activeToolCall && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex items-center gap-2 px-4 py-2 text-xs text-stone-500"
            >
              <Loader2 size={12} className="animate-spin text-nobel-gold" />
              <span>
                Calling{" "}
                <span className="font-mono text-stone-700">
                  {activeToolCall}
                </span>
                ...
              </span>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-stone-200 bg-white px-4 py-3">
        <div className="flex items-end gap-2 bg-nobel-cream rounded-xl border border-stone-200 focus-within:border-nobel-gold/50 focus-within:ring-2 focus-within:ring-nobel-gold/20 transition-all duration-200 px-4 py-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your W&B runs..."
            rows={1}
            className="flex-1 bg-transparent text-sm text-stone-800 placeholder:text-stone-400 outline-none resize-none leading-relaxed"
          />
          {isLoading ? (
            <button
              onClick={onStop}
              className="p-1.5 rounded-lg bg-stone-900 text-white hover:bg-stone-700 transition-colors"
            >
              <Square size={14} />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!input.trim()}
              className="p-1.5 rounded-lg bg-stone-900 text-white hover:bg-stone-700 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Send size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
