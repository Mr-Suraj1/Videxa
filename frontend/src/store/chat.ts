"use client";
import { create } from "zustand";
import type { ChatMessage } from "@/types";
import * as api from "@/lib/api";

type ChatState = {
  messages: ChatMessage[];
  busy: boolean;
  error: string | null;
  ask: (sessionId: string | null, sessionIds: string[], question: string) => Promise<void>;
  clear: () => void;
};

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  busy: false,
  error: null,

  ask: async (sessionId, sessionIds, question) => {
    set((s) => ({
      messages: [...s.messages, { role: "user", content: question }],
      busy: true,
      error: null,
    }));
    try {
      const answer =
        sessionId && sessionIds.length <= 1
          ? await api.chat(sessionId, question)
          : await api.chatMulti(sessionIds, question);
      set((s) => ({
        messages: [...s.messages, { role: "assistant", content: answer }],
        busy: false,
      }));
    } catch (err) {
      set({ busy: false, error: err instanceof Error ? err.message : "Chat failed" });
    }
  },

  clear: () => set({ messages: [], error: null }),
}));
