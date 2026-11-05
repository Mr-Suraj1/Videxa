"use client";
import { useState, useRef, useEffect } from "react";
import { Send, X, Layers } from "lucide-react";
import { useChatStore } from "@/store/chat";
import { useSessionsStore } from "@/store/sessions";
import { useUiStore } from "@/store/ui";

type Props = {
  sessionId: string | null;
  sessionIds?: string[];
};

export function ChatPanel({ sessionId, sessionIds = [] }: Props) {
  const [input, setInput] = useState("");
  const { messages, busy, error, ask, clear } = useChatStore();
  const sessions = useSessionsStore((s) => s.sessions);
  const addToast = useUiStore((s) => s.addToast);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevIdsKey = useRef<string>("");

  const allIds = sessionIds.length ? sessionIds : sessionId ? [sessionId] : [];
  const isMulti = allIds.length > 1;
  const idsKey = [...allIds].sort().join(",");

  // Clear chat history when the session context changes
  useEffect(() => {
    if (prevIdsKey.current && prevIdsKey.current !== idsKey) {
      clear();
    }
    prevIdsKey.current = idsKey;
  }, [idsKey, clear]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const titleMap = Object.fromEntries(sessions.map((s) => [s.session_id, s.title]));

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
        <Layers size={22} style={{ marginBottom: 8, opacity: 0.4 }} />
        <span>Select a session to start chatting.</span>
      </div>
    );
  }

  return (
    <div className="chat-panel">
      {/* Header: chips + clear */}
      <div className="chat-panel__header">
        <div className="chat-panel__chips">
          {allIds.map((id) => (
            <span key={id} className={`chat-panel__chip${isMulti ? " chat-panel__chip--multi" : ""}`}>
              {titleMap[id] ?? id.slice(0, 10) + "…"}
            </span>
          ))}
        </div>
        {messages.length > 0 && (
          <button className="chat-panel__clear-btn" onClick={clear} title="Clear chat history">
            <X size={11} />
            Clear
          </button>
        )}
      </div>

      {/* Multi-session info bar */}
      {isMulti && (
        <div className="chat-panel__multi-bar">
          <Layers size={11} />
          Querying across <strong>{allIds.length}</strong> sessions — answers draw from all selected transcripts
        </div>
      )}

      {/* Messages */}
      <div className="chat-panel__messages">
        {messages.length === 0 && (
          <p className="chat-panel__hint">
            {isMulti
              ? `Ask anything across ${allIds.length} selected meetings…`
              : "Ask anything about this meeting…"}
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg chat-msg--${m.role}`}>
            {m.content}
          </div>
        ))}
        {busy && (
          <div className="chat-msg chat-msg--assistant chat-typing">
            <span /><span /><span />
          </div>
        )}
        {error && <p className="chat-panel__error">{error}</p>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form className="chat-panel__input-row" onSubmit={handleSubmit}>
        <input
          className="chat-panel__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            isMulti
              ? `Ask across ${allIds.length} sessions…`
              : "Ask about this meeting…"
          }
          disabled={busy}
          autoComplete="off"
        />
        <button
          type="submit"
          className="chat-panel__send"
          disabled={busy || !input.trim()}
          aria-label="Send"
        >
          <Send size={15} />
        </button>
      </form>
    </div>
  );
}
