import { useState } from "react";
import { Info, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Props {
  hasWandbKey: boolean;
  hasHfToken: boolean;
  onOpenSettings: () => void;
}

export default function CredentialBanner({ hasWandbKey, hasHfToken, onOpenSettings }: Props) {
  const [dismissed, setDismissed] = useState(false);

  if ((hasWandbKey && hasHfToken) || dismissed) return null;

  const missing: string[] = [];
  if (!hasWandbKey) missing.push("W&B");
  if (!hasHfToken) missing.push("HuggingFace");

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.15 }}
        className="relative flex items-center justify-center gap-2 px-4 py-1.5 bg-stone-100 border-b border-stone-200 text-xs text-stone-500"
      >
        <Info size={12} className="flex-shrink-0" />
        <span>
          No {missing.join(" or ")} token set, results won't save to your account.
        </span>
        <button
          onClick={onOpenSettings}
          className="text-stone-600 underline underline-offset-2 hover:text-stone-900 transition-colors"
        >
          Add in Settings
        </button>
        <button
          onClick={() => setDismissed(true)}
          className="absolute right-3 p-0.5 text-stone-400 hover:text-stone-600 transition-colors"
          title="Dismiss"
        >
          <X size={12} />
        </button>
      </motion.div>
    </AnimatePresence>
  );
}
