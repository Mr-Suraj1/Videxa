"use client";
import { create } from "zustand";
import type { Toast, ToastType } from "@/types";

type UiState = {
  apiOnline: boolean | null;
  sidebarOpen: boolean;
  toasts: Toast[];
  setApiOnline: (v: boolean) => void;
  setSidebarOpen: (v: boolean) => void;
  toggleSidebar: () => void;
  addToast: (message: string, type?: ToastType) => void;
  removeToast: (id: string) => void;
};

let toastCounter = 0;

export const useUiStore = create<UiState>((set) => ({
  apiOnline: null,
  sidebarOpen: false,
  toasts: [],

  setApiOnline: (v) => set({ apiOnline: v }),
  setSidebarOpen: (v) => set({ sidebarOpen: v }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  addToast: (message, type = "info") => {
    const id = `toast-${++toastCounter}`;
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },

  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));
