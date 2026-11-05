"use client";
import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { useChatStore } from "@/store/chat";
import { useUiStore } from "@/store/ui";

type Props = {
  sessionId: string | null;
  sessionIds?: string[];
};

export function ChatPanel({ sessionId, sessionIds = [] }: Props) {
  const [input, setInput] = useState("");
  const { messages, busy, error, ask } = useChatStore();
  const addToast = useUiStore((s) => s.addToast);
  const bottomRef = useRef<HTMLDivElement>(null);

  const allIds = sessionIds.length ? sessionIds : sessionId ? [sessionId] : [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !allIds.length) return;
    const q = input.trim();
    setInput("");
    try {
      await ask(sessionId, allIds, q);
    } catch {
      addToast("Chat request failed", "error");
    }
  }

  if (!allIds.length) {
    return (
      <div className="chat-panel chat-panel--empty">
        Select a session to start chatting.
      </div>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <p className="chat-panel__hint">Ask anything about the meeting…</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-msg--${m.role}`}>
            {m.content}
          </div>
        ))}
        {error && <p className="chat-panel__error">{error}</p>}
        <div ref={bottomRef} />
      </div>
      <form className="chat-panel__input-row" onSubmit={handleSubmit}>
        <input
          className="chat-panel__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about this meeting…"
          disabled={busy}
        />
        <button
          type="submit"
          className="chat-panel__send"
          disabled={busy || !input.trim()}
          aria-label="Send"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
