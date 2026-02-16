import { useState, useCallback, useRef } from "react";
import type { Message, CardData, SSEEvent, ToolCall, MessageSegment, LaunchCard } from "../types";
import { API_BASE } from "../config";

let messageId = 0;
function nextId() {
  return `msg-${++messageId}`;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [cards, setCards] = useState<CardData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeToolCall, setActiveToolCall] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const cardsRef = useRef<CardData[]>(cards);
  cardsRef.current = cards;

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    const userMsg: Message = { id: nextId(), role: "user", content };
    const assistantMsg: Message = {
      id: nextId(),
      role: "assistant",
      content: "",
      segments: [],
    };

    // Build history from previous messages for multi-turn context
    const prevMessages = [...messages];
    const history = prevMessages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    // Extract active run context from launch cards (wandb_url → run ID + project)
    // Use cardsRef to always read the latest cards, avoiding stale closure
    const currentCards = cardsRef.current;
    const launchCard = [...currentCards].reverse().find(
      (c) => c.card_type === "launch_card" && "config" in c,
    );
    const activeRun = launchCard && "wandb_url" in launchCard && launchCard.wandb_url
      ? { wandb_url: launchCard.wandb_url }
      : undefined;

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    setActiveToolCall(null);

    const controller = new AbortController();
    abortRef.current = controller;

    const assistantId = assistantMsg.id;

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, history, active_run: activeRun }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          let event: SSEEvent;
          try {
            event = JSON.parse(jsonStr);
          } catch {
            continue;
          }

          if (event.type === "text" && event.content) {
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                const segs = [...(m.segments || [])];
                const last = segs[segs.length - 1];
                // Append to last text segment, or create a new one
                if (last && last.type === "text") {
                  segs[segs.length - 1] = {
                    type: "text",
                    content: last.content + event.content,
                  };
                } else {
                  segs.push({ type: "text", content: event.content! });
                }
                return {
                  ...m,
                  content: m.content + event.content,
                  segments: segs,
                };
              }),
            );
            setActiveToolCall(null);
          } else if (event.type === "tool_call" && event.name) {
            setActiveToolCall(event.name);
            const newTool: ToolCall = {
              name: event.name,
              input: event.input || {},
              status: "running",
            };
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                const segs = [...(m.segments || [])];
                segs.push({ type: "tool", tool: newTool });
                return { ...m, segments: segs };
              }),
            );
          } else if (event.type === "tool_result" && event.name) {
            setActiveToolCall(null);
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                const segs = [...(m.segments || [])];
                // Find last tool segment with this name that's still running
                for (let i = segs.length - 1; i >= 0; i--) {
                  const seg = segs[i];
                  if (
                    seg.type === "tool" &&
                    seg.tool.name === event.name &&
                    seg.tool.status === "running"
                  ) {
                    segs[i] = {
                      type: "tool",
                      tool: {
                        ...seg.tool,
                        status: event.summary?.startsWith("Error")
                          ? "error"
                          : "done",
                        result: event.summary,
                      },
                    };
                    break;
                  }
                }
                return { ...m, segments: segs };
              }),
            );
          } else if (event.type === "card" && event.data) {
            setCards((prev) => {
              const newCard = event.data!;
              // For launch cards: update the existing proposed card in-place
              // instead of adding a duplicate — keep title, summary, cost from proposal
              if (newCard.card_type === "launch_card" && newCard.status !== "proposed") {
                for (let i = prev.length - 1; i >= 0; i--) {
                  const c = prev[i];
                  if (c.card_type === "launch_card" && c.status === "proposed") {
                    const updated = [...prev];
                    // Merge: keep the proposal's rich info, update only status fields
                    updated[i] = {
                      ...c,
                      status: newCard.status,
                      modal_function_call_id: newCard.modal_function_call_id,
                      wandb_url: newCard.wandb_url || c.wandb_url,
                      requires_approval: false,
                    };
                    return updated;
                  }
                }
              }
              return [...prev, newCard];
            });
          } else if (event.type === "done") {
            setActiveToolCall(null);
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    m.content ||
                    "Sorry, something went wrong. Please check that the backend is running.",
                }
              : m,
          ),
        );
      }
    } finally {
      setIsLoading(false);
      setActiveToolCall(null);
      abortRef.current = null;
    }
  }, [isLoading, messages]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setActiveToolCall(null);
  }, []);

  const launchJob = useCallback(async (card: LaunchCard): Promise<{ success: boolean; error?: string }> => {
    try {
      const res = await fetch(`${API_BASE}/api/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ launch_type: card.launch_type, config: card.config }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, error: data.error || "Failed to launch" };
      }
      // Update the proposed card in-place → running with function_call_id
      setCards((prev) =>
        prev.map((c) =>
          c === card || (c.card_type === "launch_card" && c.status === "proposed")
            ? { ...c, status: "running" as const, modal_function_call_id: data.function_call_id, requires_approval: false }
            : c,
        ),
      );
      return { success: true };
    } catch (e) {
      return { success: false, error: e instanceof Error ? e.message : "Network error" };
    }
  }, []);

  const updateCardWandbUrl = useCallback((wandbUrl: string) => {
    setCards((prev) => {
      // Find the most recent launch card without a wandb_url and update it
      const updated = [...prev];
      for (let i = updated.length - 1; i >= 0; i--) {
        const c = updated[i];
        if (c.card_type === "launch_card" && !c.wandb_url) {
          updated[i] = { ...c, wandb_url: wandbUrl };
          return updated;
        }
        // Also update if the card already has a wandb_url but it's a project URL (not a run URL)
        if (c.card_type === "launch_card" && c.wandb_url && !c.wandb_url.includes("/runs/") && wandbUrl.includes("/runs/")) {
          updated[i] = { ...c, wandb_url: wandbUrl };
          return updated;
        }
      }
      return prev;
    });
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setCards([]);
    setIsLoading(false);
    setActiveToolCall(null);
    abortRef.current?.abort();
  }, []);

  return { messages, cards, isLoading, activeToolCall, sendMessage, stop, clearChat, launchJob, updateCardWandbUrl };
}
