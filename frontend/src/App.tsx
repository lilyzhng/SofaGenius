import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw } from "lucide-react";
import ChatPanel from "./components/ChatPanel";
import CardsPanel from "./components/CardsPanel";
import LandingPage from "./components/LandingPage";
import { useChat } from "./hooks/useChat";

const spring = { type: "spring" as const, stiffness: 80, damping: 15 };

export default function App() {
  const { messages, cards, isLoading, activeToolCall, sendMessage, stop, clearChat, launchJob, updateCardWandbUrl } =
    useChat();

  const [showLanding, setShowLanding] = useState(true);

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

  return (
    <div className="h-screen flex flex-col bg-nobel-cream">
      {/* Top nav */}
      <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-stone-200 flex-shrink-0">
        <button
          onClick={handleClearChat}
          className="flex items-center gap-3 hover:opacity-80 transition-opacity"
        >
          <img src="/logo.png" alt="SofaGenius" className="w-8 h-8 rounded-full object-cover shadow-sm" />
          <span className="font-serif font-bold text-lg tracking-wide text-stone-900">
            SOFAGENIUS
          </span>
        </button>
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
          {!showLanding && (
            <div className="flex items-center gap-2 text-xs text-stone-400">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              Agent Active
            </div>
          )}
        </div>
      </nav>

      {/* Content area */}
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
              <CardsPanel cards={cards} onWandbUrl={updateCardWandbUrl} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
