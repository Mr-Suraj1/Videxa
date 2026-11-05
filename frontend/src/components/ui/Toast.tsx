"use client";
import { X } from "lucide-react";
import { useUiStore } from "@/store/ui";
import type { Toast as ToastItem } from "@/types";

function ToastItem({ toast }: { toast: ToastItem }) {
  const removeToast = useUiStore((s) => s.removeToast);
  return (
    <div className={`toast toast--${toast.type}`} role="alert">
      <span className="toast__msg">{toast.message}</span>
      <button
        className="toast__close"
        onClick={() => removeToast(toast.id)}
        aria-label="Dismiss"
      >
        <X size={14} />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useUiStore((s) => s.toasts);
  if (!toasts.length) return null;
  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
