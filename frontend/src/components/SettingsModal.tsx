import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Key, Check, AlertCircle, Loader2 } from "lucide-react";
import type { UserProfile } from "../types";

interface Props {
  open: boolean;
  onClose: () => void;
  profile: UserProfile | null;
  onSaveCredential: (
    key: "wandb_api_key" | "hf_token",
    value: string,
  ) => Promise<{ success: boolean; entity?: string; username?: string; error?: string }>;
}

function CredentialRow({
  label,
  credKey,
  hasKey,
  connectedAs,
  onSave,
}: {
  label: string;
  credKey: "wandb_api_key" | "hf_token";
  hasKey: boolean;
  connectedAs: string;
  onSave: Props["onSaveCredential"];
}) {
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "saving" | "success" | "error">("idle");
  const [statusText, setStatusText] = useState("");
  const [editing, setEditing] = useState(!hasKey);

  useEffect(() => {
    if (hasKey && connectedAs) {
      setStatus("success");
      setStatusText(connectedAs);
      setEditing(false);
    }
  }, [hasKey, connectedAs]);

  const handleSave = async () => {
    if (!value.trim()) return;
    setStatus("saving");
    setStatusText("");
    const result = await onSave(credKey, value.trim());
    if (result.success) {
      setStatus("success");
      setStatusText(result.entity || result.username || "Connected");
      setValue("");
      setEditing(false);
    } else {
      setStatus("error");
      setStatusText(result.error || "Validation failed");
    }
  };

  const handleClear = async () => {
    setStatus("saving");
    const result = await onSave(credKey, "");
    if (result.success) {
      setStatus("idle");
      setStatusText("");
      setEditing(true);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-stone-500 uppercase tracking-widest">
          {label}
        </label>
        {status === "success" && !editing && (
          <button
            onClick={() => setEditing(true)}
            className="text-xs text-stone-400 hover:text-stone-600"
          >
            Change
          </button>
        )}
      </div>

      {editing ? (
        <div className="flex gap-2">
          <input
            type="password"
            value={value}
            onChange={(e) => {
              setValue(e.target.value);
              if (status === "error") setStatus("idle");
            }}
            placeholder={hasKey ? "Enter new key to replace" : "Paste your key here"}
            className="flex-1 px-3 py-2 border border-stone-200 rounded-lg text-sm focus:outline-none focus:border-nobel-gold focus:ring-1 focus:ring-nobel-gold/30 transition-colors"
          />
          <button
            onClick={handleSave}
            disabled={!value.trim() || status === "saving"}
            className="px-4 py-2 bg-stone-900 text-white text-sm rounded-lg hover:bg-stone-800 transition-colors disabled:opacity-50 flex items-center gap-1.5"
          >
            {status === "saving" ? <Loader2 size={14} className="animate-spin" /> : <Key size={14} />}
            Save
          </button>
        </div>
      ) : null}

      {/* Status indicator */}
      {status === "success" && statusText && (
        <div className="flex items-center gap-2 text-sm">
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
          <span className="text-stone-600">
            Connected{" "}
            <span className="text-stone-900 font-medium">
              ({credKey === "wandb_api_key" ? "entity" : "username"}: {statusText})
            </span>
          </span>
          <button onClick={handleClear} className="ml-auto text-xs text-stone-400 hover:text-red-500">
            Remove
          </button>
        </div>
      )}
      {status === "error" && (
        <div className="flex items-center gap-2 text-sm text-red-500">
          <AlertCircle size={14} />
          {statusText}
        </div>
      )}
    </div>
  );
}

export default function SettingsModal({ open, onClose, profile, onSaveCredential }: Props) {
  const isFirstTime = profile != null && !profile.has_wandb_key && !profile.has_hf_token;
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/30 z-40"
            onClick={onClose}
          />
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl border border-stone-200 shadow-lg w-full max-w-lg p-6">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="font-serif text-xl font-semibold text-stone-900">
                    {isFirstTime ? "Welcome to SofaGenius" : "Settings"}
                  </h2>
                  <div className="w-10 h-0.5 bg-nobel-gold mt-1.5" />
                </div>
                <button
                  onClick={onClose}
                  className="p-1.5 text-stone-400 hover:text-stone-600 rounded-lg hover:bg-stone-50 transition-colors"
                >
                  <X size={18} />
                </button>
              </div>

              <p className="text-sm text-stone-500 mb-6">
                {isFirstTime
                  ? "Connect your API keys to get started. SofaGenius needs these to access your W&B runs and HuggingFace datasets."
                  : "Connect your API keys so SofaGenius can access your W&B runs and HuggingFace datasets. Keys are stored securely per-account. The Anthropic API key and Modal credentials stay server-side."}
              </p>

              <div className="space-y-6">
                <CredentialRow
                  label="Weights & Biases API Key"
                  credKey="wandb_api_key"
                  hasKey={profile?.has_wandb_key ?? false}
                  connectedAs={profile?.wandb_entity ?? ""}
                  onSave={onSaveCredential}
                />
                <CredentialRow
                  label="HuggingFace Token"
                  credKey="hf_token"
                  hasKey={profile?.has_hf_token ?? false}
                  connectedAs={profile?.hf_username ?? ""}
                  onSave={onSaveCredential}
                />
              </div>

              <div className="mt-8 pt-4 border-t border-stone-100">
                <button
                  onClick={onClose}
                  className="px-5 py-2 bg-stone-900 text-white text-sm rounded-full hover:bg-stone-800 transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
