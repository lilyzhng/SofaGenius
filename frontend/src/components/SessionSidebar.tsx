import { useMemo, useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Pencil, Settings, LogOut, MessageSquare, Check, X } from "lucide-react";
import type { SessionSummary } from "../types";

interface Props {
  open: boolean;
  sessions: SessionSummary[];
  currentSessionId: string | null;
  user: { email?: string; user_metadata?: { full_name?: string; avatar_url?: string } } | null;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, title: string) => void;
  onNewChat: () => void;
  onOpenSettings: () => void;
  onSignOut: () => void;
}

function groupByDate(sessions: SessionSummary[]) {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);

  const groups: { label: string; items: SessionSummary[] }[] = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Previous 7 Days", items: [] },
    { label: "Older", items: [] },
  ];

  for (const s of sessions) {
    const d = new Date(s.updated_at || s.created_at);
    if (d >= today) groups[0].items.push(s);
    else if (d >= yesterday) groups[1].items.push(s);
    else if (d >= weekAgo) groups[2].items.push(s);
    else groups[3].items.push(s);
  }

  return groups.filter((g) => g.items.length > 0);
}

function SessionItem({
  session,
  isCurrent,
  onSelect,
  onDelete,
  onRename,
}: {
  session: SessionSummary;
  isCurrent: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: (title: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editValue, setEditValue] = useState(session.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const handleSave = () => {
    const trimmed = editValue.trim();
    if (trimmed && trimmed !== session.title) {
      onRename(trimmed);
    }
    setEditing(false);
  };

  const handleCancel = () => {
    setEditValue(session.title);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="flex items-center gap-1 px-2 py-1.5">
        <input
          ref={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSave();
            if (e.key === "Escape") handleCancel();
          }}
          className="flex-1 px-2 py-1 text-sm border border-nobel-gold rounded-md focus:outline-none focus:ring-1 focus:ring-nobel-gold/30 min-w-0"
        />
        <button onClick={handleSave} className="p-1 text-emerald-500 hover:text-emerald-700">
          <Check size={13} />
        </button>
        <button onClick={handleCancel} className="p-1 text-stone-400 hover:text-stone-600">
          <X size={13} />
        </button>
      </div>
    );
  }

  return (
    <div
      className={`group flex items-center gap-1 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm ${
        isCurrent ? "bg-stone-100 text-stone-900" : "text-stone-600 hover:bg-stone-50"
      }`}
      onClick={onSelect}
    >
      <span className="flex-1 truncate">{session.title}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setEditValue(session.title);
          setEditing(true);
        }}
        className="opacity-0 group-hover:opacity-100 p-1 hover:text-nobel-gold transition-all"
      >
        <Pencil size={13} />
      </button>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-all"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}

export default function SessionSidebar({
  open,
  sessions,
  currentSessionId,
  user,
  onSelectSession,
  onDeleteSession,
  onRenameSession,
  onNewChat,
  onOpenSettings,
  onSignOut,
}: Props) {
  const grouped = useMemo(() => groupByDate(sessions), [sessions]);

  const displayName =
    user?.user_metadata?.full_name || user?.email?.split("@")[0] || "User";
  const avatarUrl = user?.user_metadata?.avatar_url;

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 260, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="flex-shrink-0 bg-white border-r border-stone-200 flex flex-col overflow-hidden h-full"
        >
          {/* New Chat button */}
          <div className="p-3 border-b border-stone-100">
            <button
              onClick={onNewChat}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-stone-600 hover:bg-stone-50 rounded-lg transition-colors"
            >
              <Plus size={16} />
              New Chat
            </button>
          </div>

          {/* Session list */}
          <div className="flex-1 overflow-y-auto px-2 py-2">
            {grouped.length === 0 && (
              <div className="px-3 py-8 text-center">
                <MessageSquare size={24} className="mx-auto text-stone-300 mb-2" />
                <p className="text-xs text-stone-400">No conversations yet</p>
              </div>
            )}
            {grouped.map((group) => (
              <div key={group.label} className="mb-3">
                <p className="px-3 py-1 text-[10px] font-bold text-stone-400 uppercase tracking-widest">
                  {group.label}
                </p>
                {group.items.map((s) => (
                  <SessionItem
                    key={s.id}
                    session={s}
                    isCurrent={s.id === currentSessionId}
                    onSelect={() => onSelectSession(s.id)}
                    onDelete={() => onDeleteSession(s.id)}
                    onRename={(title) => onRenameSession(s.id, title)}
                  />
                ))}
              </div>
            ))}
          </div>

          {/* User section */}
          <div className="border-t border-stone-100 p-3">
            <div className="flex items-center gap-2 mb-2">
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="w-7 h-7 rounded-full" />
              ) : (
                <div className="w-7 h-7 rounded-full bg-stone-200 flex items-center justify-center text-xs font-bold text-stone-500">
                  {displayName[0]?.toUpperCase()}
                </div>
              )}
              <span className="flex-1 text-sm text-stone-700 truncate">{displayName}</span>
            </div>
            <div className="flex gap-1">
              <button
                onClick={onOpenSettings}
                className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-stone-500 hover:text-stone-900 hover:bg-stone-50 rounded-lg transition-colors"
              >
                <Settings size={13} />
                Settings
              </button>
              <button
                onClick={onSignOut}
                className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs text-stone-500 hover:text-red-600 hover:bg-stone-50 rounded-lg transition-colors"
              >
                <LogOut size={13} />
                Sign Out
              </button>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
