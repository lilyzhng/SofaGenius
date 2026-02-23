import { useState, useCallback, useRef } from "react";
import type { Message, CardData, SSEEvent, ToolCall, LaunchCard, SessionDetail } from "../types";
import { API_BASE } from "../config";

let messageId = 0;
function nextId() {
  return `msg-${++messageId}`;
}

export function useChat(getAccessToken: () => Promise<string | null>) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [cards, setCards] = useState<CardData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeToolCall, setActiveToolCall] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
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
      const token = await getAccessToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: content,
          history,
          active_run: activeRun,
          session_id: currentSessionId,
        }),
        signal: controller.signal,
      });

      if (!res.ok || !res.body) {
        throw new Error(`HTTP ${res.status}`);
      }

      // Read session ID from response header (new sessions)
      const sessionHeader = res.headers.get("X-Session-Id");
      if (sessionHeader && !currentSessionId) {
        setCurrentSessionId(sessionHeader);
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
              if (newCard.card_type === "launch_card" && newCard.status !== "proposed") {
                for (let i = prev.length - 1; i >= 0; i--) {
                  const c = prev[i];
                  if (c.card_type === "launch_card" && c.status === "proposed") {
                    const updated = [...prev];
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
  }, [isLoading, messages, currentSessionId, getAccessToken]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setActiveToolCall(null);
  }, []);

  const launchJob = useCallback(async (card: LaunchCard): Promise<{ success: boolean; error?: string }> => {
    try {
      const token = await getAccessToken();
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/launch`, {
        method: "POST",
        headers,
        body: JSON.stringify({ launch_type: card.launch_type, config: card.config }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { success: false, error: data.error || "Failed to launch" };
      }
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
  }, [getAccessToken]);

  const updateCardWandbUrl = useCallback((wandbUrl: string) => {
    setCards((prev) => {
      const updated = [...prev];
      for (let i = updated.length - 1; i >= 0; i--) {
        const c = updated[i];
        if (c.card_type === "launch_card" && !c.wandb_url) {
          updated[i] = { ...c, wandb_url: wandbUrl };
          return updated;
        }
        if (c.card_type === "launch_card" && c.wandb_url && !c.wandb_url.includes("/runs/") && wandbUrl.includes("/runs/")) {
          updated[i] = { ...c, wandb_url: wandbUrl };
          return updated;
        }
      }
      return prev;
    });
  }, []);

  const restoreSession = useCallback(async (sessionId: string) => {
    const token = await getAccessToken();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const detail: SessionDetail = await res.json();

      // Convert DB messages to frontend Message format
      const restoredMessages: Message[] = detail.messages.map((m) => ({
        id: nextId(),
        role: m.role,
        content: m.content,
        segments: m.segments || undefined,
      }));

      setMessages(restoredMessages);
      setCards(detail.cards || []);
      setCurrentSessionId(sessionId);
      setIsLoading(false);
      setActiveToolCall(null);
    } catch {
      // Silently fail
    }
  }, [getAccessToken]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setCards([]);
    setCurrentSessionId(null);
    setIsLoading(false);
    setActiveToolCall(null);
    abortRef.current?.abort();
  }, []);

  return {
    messages,
    cards,
    isLoading,
    activeToolCall,
    currentSessionId,
    sendMessage,
    stop,
    clearChat,
    launchJob,
    updateCardWandbUrl,
    restoreSession,
  };
}
