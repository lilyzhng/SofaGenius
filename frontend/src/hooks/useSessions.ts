import { useState, useCallback } from "react";
import { API_BASE } from "../config";
import type { SessionSummary } from "../types";

export function useSessions(getAccessToken: () => Promise<string | null>) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);

  const refreshSessions = useCallback(async () => {
    setLoading(true);
    try {
      const token = await getAccessToken();
      if (!token) return;
      const res = await fetch(`${API_BASE}/api/sessions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch {
      // Silently fail — sidebar will show empty
    } finally {
      setLoading(false);
    }
  }, [getAccessToken]);

  const deleteSession = useCallback(
    async (id: string) => {
      const token = await getAccessToken();
      if (!token) return;
      await fetch(`${API_BASE}/api/sessions/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setSessions((prev) => prev.filter((s) => s.id !== id));
    },
    [getAccessToken],
  );

  const renameSession = useCallback(
    async (id: string, title: string) => {
      const token = await getAccessToken();
      if (!token) return;
      await fetch(`${API_BASE}/api/sessions/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title }),
      });
      setSessions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, title } : s)),
      );
    },
    [getAccessToken],
  );

  return { sessions, loading, refreshSessions, deleteSession, renameSession };
}
