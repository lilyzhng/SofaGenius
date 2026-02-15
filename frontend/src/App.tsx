import { RotateCcw } from "lucide-react";
import ChatPanel from "./components/ChatPanel";
import CardsPanel from "./components/CardsPanel";
import { useChat } from "./hooks/useChat";

export default function App() {
  const { messages, cards, isLoading, activeToolCall, sendMessage, stop, clearChat, launchJob } =
    useChat();

  return (
    <div className="h-screen flex flex-col bg-nobel-cream">
      {/* Top nav */}
      <nav className="flex items-center justify-between px-6 py-3 bg-white border-b border-stone-200 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-nobel-gold rounded-full flex items-center justify-center text-white font-serif font-bold text-lg shadow-sm">
            S
          </div>
          <span className="font-serif font-bold text-lg tracking-wide text-stone-900">
            SOFA GENIUS
          </span>
        </div>
        <div className="flex items-center gap-4">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-stone-500 hover:text-stone-900 border border-stone-200 hover:border-stone-400 rounded-full transition-colors"
            >
              <RotateCcw size={12} />
              New Chat
            </button>
          )}
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            W&B Monitor
          </div>
        </div>
      </nav>

      {/* Two-panel layout */}
      <div className="flex flex-1 min-h-0">
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
          <CardsPanel cards={cards} />
        </div>
      </div>
    </div>
  );
}
