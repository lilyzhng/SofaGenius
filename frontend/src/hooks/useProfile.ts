import { useState, useCallback } from "react";
import { API_BASE } from "../config";
import type { UserProfile } from "../types";

export function useProfile(getAccessToken: () => Promise<string | null>) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchProfile = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch {
      // Silently fail
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  const updateCredentials = useCallback(
    async (
      key: "wandb_api_key" | "hf_token",
      value: string,
    ): Promise<{ success: boolean; entity?: string; username?: string; error?: string }> => {
      const token = await getAccessToken();
      if (!token) return { success: false, error: "Not authenticated" };
      try {
        const res = await fetch(`${API_BASE}/api/profile`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ [key]: value }),
        });
        const data = await res.json();
        if (!res.ok) {
          return { success: false, error: data.error || "Validation failed" };
        }
        // Update local profile state
        setProfile((prev) => {
          if (!prev) return prev;
          if (key === "wandb_api_key") {
            return {
              ...prev,
              has_wandb_key: !!value,
              wandb_entity: data.wandb_entity || "",
            };
          }
          return {
            ...prev,
            has_hf_token: !!value,
            hf_username: data.hf_username || "",
          };
        });
        return {
          success: true,
          entity: data.wandb_entity,
          username: data.hf_username,
        };
      } catch (e) {
        return { success: false, error: e instanceof Error ? e.message : "Network error" };
      }
    },
    [getAccessToken],
  );

  return { profile, isLoading, fetchProfile, updateCredentials };
}
