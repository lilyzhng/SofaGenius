import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, PanelLeftOpen, PanelLeftClose, Loader2, Bug } from "lucide-react";
import ChatPanel from "./components/ChatPanel";
import CardsPanel from "./components/CardsPanel";
import CredentialBanner from "./components/CredentialBanner";
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import SessionSidebar from "./components/SessionSidebar";
import SettingsModal from "./components/SettingsModal";
import { useAuthContext } from "./contexts/AuthContext";
import { useChat } from "./hooks/useChat";
import { useSessions } from "./hooks/useSessions";
import { useProfile } from "./hooks/useProfile";

const spring = { type: "spring" as const, stiffness: 80, damping: 15 };

export default function App() {
  const { user, loading: authLoading, signOut, getAccessToken } = useAuthContext();

  const {
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
  } = useChat(getAccessToken);

  const { sessions, refreshSessions, deleteSession, renameSession } = useSessions(getAccessToken);
  const { profile, fetchProfile, updateCredentials } = useProfile(getAccessToken);

  const [showLanding, setShowLanding] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Fetch sessions and profile when user signs in
  useEffect(() => {
    if (user) {
      refreshSessions();
      fetchProfile();
    }
  }, [user, refreshSessions, fetchProfile]);

  // Credential banner handles the reminder — no auto-popup needed

  // Refresh session list when a new session is created
  useEffect(() => {
    if (currentSessionId && user) {
      refreshSessions();
    }
  }, [currentSessionId, user, refreshSessions]);

  const handleModeSelect = useCallback(
    (query?: string) => {
      setShowLanding(false);
      if (query) {
        setTimeout(() => sendMessage(query), 50);
      }
    },
    [sendMessage],
  );

  const handleClearChat = useCallback(() => {
    clearChat();
    setShowLanding(true);
  }, [clearChat]);

  const handleSelectSession = useCallback(
    async (id: string) => {
      setShowLanding(false);
      await restoreSession(id);
    },
    [restoreSession],
  );

  const handleDeleteSession = useCallback(
    async (id: string) => {
      await deleteSession(id);
      // If we deleted the current session, go back to landing
      if (id === currentSessionId) {
        handleClearChat();
      }
    },
    [deleteSession, currentSessionId, handleClearChat],
  );

  // Auth loading spinner
  if (authLoading) {
    return (
      <div className="h-screen bg-nobel-cream flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-stone-400" />
      </div>
    );
  }

  // Auth gate
  if (!user) {
    return <AuthPage />;
  }

  return (
    <div className="h-screen flex flex-col bg-nobel-cream">
      {/* Top nav */}
      <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-stone-200 flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Sidebar toggle */}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-1.5 text-stone-400 hover:text-stone-700 rounded-lg hover:bg-stone-50 transition-colors"
          >
            {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>

          <button
            onClick={handleClearChat}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <img src="/logo.png" alt="SofaGenius" className="w-8 h-8 rounded-full object-cover shadow-sm" />
            <span className="font-serif font-bold text-lg tracking-wide text-stone-900">
              SOFAGENIUS
            </span>
          </button>
        </div>
        <div className="flex items-center gap-4">
          {messages.length > 0 && (
            <button
              onClick={handleClearChat}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-stone-500 hover:text-stone-900 border border-stone-200 hover:border-stone-400 rounded-full transition-colors"
            >
              <RotateCcw size={12} />
              New Chat
            </button>
          )}
          <a
            href="https://github.com/lilyzhng/SofaGenius/issues/new?title=%5BBug%5D+&body=%23%23+What+happened%3F%0A%0A%0A%23%23+Steps+to+reproduce%0A1.+%0A2.+%0A3.+%0A%0A%23%23+Expected+behavior%0A%0A"
            target="_blank"
            rel="noopener noreferrer"
            title="Report issue"
            className="p-1.5 text-stone-400 hover:text-nobel-gold rounded-lg hover:bg-stone-50 transition-colors"
          >
            <Bug size={16} />
          </a>
        </div>
      </nav>

      {/* Content area with sidebar */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <SessionSidebar
          open={sidebarOpen}
          sessions={sessions}
          currentSessionId={currentSessionId}
          user={user}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onRenameSession={renameSession}
          onNewChat={handleClearChat}
          onOpenSettings={() => setSettingsOpen(true)}
          onSignOut={signOut}
        />

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Credential banner */}
          {profile && (
            <CredentialBanner
              hasWandbKey={profile.has_wandb_key}
              hasHfToken={profile.has_hf_token}
              onOpenSettings={() => setSettingsOpen(true)}
            />
          )}

          <AnimatePresence mode="wait">
            {showLanding ? (
              <motion.div
                key="landing"
                className="flex-1 min-h-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <LandingPage onModeSelect={handleModeSelect} />
              </motion.div>
            ) : (
              <motion.div
                key="panels"
                className="flex flex-1 min-h-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={spring}
              >
                {/* Left: Chat */}
                <div className="w-1/2 border-r border-stone-200 bg-white flex flex-col">
                  <ChatPanel
                    messages={messages}
                    cards={cards}
                    isLoading={isLoading}
                    activeToolCall={activeToolCall}
                    onSend={sendMessage}
                    onStop={stop}
                    onLaunch={launchJob}
                  />
                </div>

                {/* Right: Cards */}
                <div className="w-1/2 bg-nobel-cream flex flex-col">
                  <CardsPanel
                    cards={cards}
                    onWandbUrl={updateCardWandbUrl}
                    hasWandbKey={profile?.has_wandb_key ?? false}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Settings modal */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        profile={profile}
        onSaveCredential={updateCredentials}
      />
    </div>
  );
}
