import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";
import type { Message } from "../types";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar */}
      {isUser ? (
        <img
          src="/avatar.png"
          alt="You"
          className="w-8 h-8 rounded-full object-cover flex-shrink-0"
        />
      ) : (
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-nobel-gold text-white">
          <Bot size={14} />
        </div>
      )}

      {/* Bubble */}
      <div
        className={`max-w-[80%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
          isUser
            ? "bg-stone-900 text-white rounded-br-sm"
            : "bg-white border border-stone-200 shadow-sm text-stone-700 rounded-bl-sm"
        }`}
      >
        {message.content ? (
          <div className="prose prose-sm prose-stone max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            <ReactMarkdown
              components={{
                h1: ({ children }) => <h3 className="text-base font-serif font-bold text-stone-900 mt-3 mb-1">{children}</h3>,
                h2: ({ children }) => <h3 className="text-sm font-serif font-bold text-stone-900 mt-3 mb-1">{children}</h3>,
                h3: ({ children }) => <h4 className="text-sm font-bold text-stone-800 mt-2 mb-1">{children}</h4>,
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
                li: ({ children }) => <li className="text-sm">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-stone-900">{children}</strong>,
                code: ({ children, className }) => {
                  const isBlock = className?.includes("language-");
                  return isBlock ? (
                    <code className="block bg-stone-100 rounded-lg p-3 text-xs font-mono overflow-x-auto my-2">{children}</code>
                  ) : (
                    <code className="bg-stone-100 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
                  );
                },
                pre: ({ children }) => <pre className="bg-stone-100 rounded-lg p-3 overflow-x-auto my-2 text-xs">{children}</pre>,
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="text-nobel-gold underline hover:text-stone-900 transition-colors">
                    {children}
                  </a>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-nobel-gold pl-3 my-2 text-stone-500 italic">{children}</blockquote>
                ),
                hr: () => <hr className="border-stone-200 my-3" />,
                table: ({ children }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="min-w-full text-xs border-collapse">{children}</table>
                  </div>
                ),
                th: ({ children }) => <th className="border border-stone-200 bg-stone-50 px-2 py-1 text-left font-semibold">{children}</th>,
                td: ({ children }) => <td className="border border-stone-200 px-2 py-1">{children}</td>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-stone-400">
            <div className="w-1.5 h-1.5 bg-nobel-gold rounded-full animate-pulse" />
            <span className="text-xs">Thinking...</span>
          </div>
        )}

        {/* Tool call indicators */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 pt-2 border-t border-stone-100 space-y-1">
            {message.toolCalls.map((tc, i) => (
              <div
                key={i}
                className="text-xs text-stone-400 flex items-center gap-1.5"
              >
                <div className="w-1 h-1 bg-nobel-gold rounded-full" />
                <span className="font-mono">{tc.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
