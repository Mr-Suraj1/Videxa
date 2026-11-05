"use client";
import { create } from "zustand";
import type { VideoSession, SessionStatus, SessionContent, Analysis } from "@/types";
import * as api from "@/lib/api";

type SessionsState = {
  sessions: VideoSession[];
  loading: boolean;
  error: string | null;
  selectedIds: Set<string>;
  selectedSession: SessionStatus | null;
  sessionContent: SessionContent | null;
  contentLoading: boolean;
  analysis: Analysis | null;
  savedTranscript: string | null;
  busy: boolean;

  refreshSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
  loadSessionContent: (id: string) => Promise<void>;
  analyze: (source: string | File, language: string) => Promise<void>;
  retryAnalysis: (id: string) => Promise<void>;
  toggleSession: (id: string) => void;
  clearSelection: () => void;
  openSession: (session: VideoSession) => Promise<void>;
  setAnalysis: (a: Analysis | null) => void;
  setSavedTranscript: (t: string | null) => void;
};

export const useSessionsStore = create<SessionsState>((set, get) => ({
  sessions: [],
  loading: false,
  error: null,
  selectedIds: new Set(),
  selectedSession: null,
  sessionContent: null,
  contentLoading: false,
  analysis: null,
  savedTranscript: null,
  busy: false,

  refreshSessions: async () => {
    set({ loading: true, error: null });
    try {
      const sessions = await api.getSessions();
      set({ sessions, loading: false });
    } catch (err) {
      set({ loading: false, error: err instanceof Error ? err.message : "Failed to load sessions" });
    }
  },

  loadSession: async (id) => {
    try {
      const session = await api.getSession(id);
      set({ selectedSession: session });
    } catch { /* silent */ }
  },

  loadSessionContent: async (id) => {
    set({ contentLoading: true });
    try {
      const content = await api.getSessionContent(id);
      set({
        sessionContent: content,
        savedTranscript: content.transcript,
        contentLoading: false,
      });
    } catch {
      set({ contentLoading: false });
    }
  },

  analyze: async (source, language) => {
    set({ busy: true, analysis: null });
    try {
      const result =
        typeof source === "string"
          ? await api.processYouTube(source, language)
          : await api.processUpload(source, language);
      set({
        analysis: result,
        savedTranscript: result.transcript,
        busy: false,
      });
      await get().refreshSessions();
    } catch (err) {
      set({ busy: false });
      throw err;
    }
  },

  retryAnalysis: async (id) => {
    set({ busy: true });
    try {
      const result = await api.retryAnalysis(id);
      set({ analysis: result, savedTranscript: result.transcript, busy: false });
      await get().refreshSessions();
    } catch (err) {
      set({ busy: false });
      throw err;
    }
  },

  toggleSession: (id) => {
    set((s) => {
      const next = new Set(s.selectedIds);
      next.has(id) ? next.delete(id) : next.add(id);
      return { selectedIds: next };
    });
  },

  clearSelection: () => set({ selectedIds: new Set() }),

  openSession: async (session) => {
    set({ selectedSession: session as SessionStatus, analysis: null, savedTranscript: null });
    await get().loadSession(session.session_id);
    await get().loadSessionContent(session.session_id);
  },

  setAnalysis: (a) => set({ analysis: a }),
  setSavedTranscript: (t) => set({ savedTranscript: t }),
}));
