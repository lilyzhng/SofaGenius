import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Loader2, Square, Rocket } from "lucide-react";
import MessageBubble from "./MessageBubble";
import type { Message, CardData, LaunchCard } from "../types";

interface Props {
  messages: Message[];
  cards: CardData[];
  isLoading: boolean;
  activeToolCall: string | null;
  onSend: (message: string) => void;
  onStop: () => void;
  onLaunch: (card: LaunchCard) => Promise<{ success: boolean; error?: string }>;
}

function LaunchApprovalButton({
  card,
  onLaunch,
}: {
  card: LaunchCard;
  onLaunch: (card: LaunchCard) => Promise<{ success: boolean; error?: string }>;
}) {
  const [status, setStatus] = useState<"idle" | "launching" | "launched" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApprove = async () => {
    setStatus("launching");
    const result = await onLaunch(card);
    if (result.success) {
      setStatus("launched");
    } else {
      setStatus("error");
      setErrorMsg(result.error || "Failed to launch");
    }
  };

  if (status === "launched") return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="ml-11"
    >
      {status === "idle" && (
        <button
          onClick={handleApprove}
          className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold rounded-full border-2 border-nobel-gold text-stone-700 bg-nobel-gold/10 hover:bg-nobel-gold/20 transition-colors"
        >
          <Rocket size={12} />
          Approve & Launch
        </button>
      )}
      {status === "launching" && (
        <span className="inline-flex items-center gap-1.5 ml-1 text-xs text-stone-400">
          <Loader2 size={12} className="animate-spin" />
          Launching on Modal...
        </span>
      )}
      {status === "error" && (
        <div className="flex items-center gap-2">
          <button
            onClick={handleApprove}
            className="px-4 py-1.5 text-xs font-bold rounded-full border-2 border-red-400 text-red-700 bg-red-50 hover:bg-red-100 transition-colors"
          >
            Retry
          </button>
          {errorMsg && <span className="text-xs text-red-600">{errorMsg}</span>}
        </div>
      )}
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
  onLaunch,
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
            <p className="text-sm text-stone-400">
              Type a message to get started.
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {/* Inline approval button for pending launch cards */}
            {pendingLaunchCard && !isLoading && (
              <LaunchApprovalButton card={pendingLaunchCard} onLaunch={onLaunch} />
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
