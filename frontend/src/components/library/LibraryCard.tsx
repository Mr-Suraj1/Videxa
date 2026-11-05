"use client";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import type { VideoSession } from "@/types";
import { humanDate, statusLabel } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { useSessionsStore } from "@/store/sessions";
import { useUiStore } from "@/store/ui";

type BadgeVariant = "green" | "amber" | "red" | "purple" | "cyan" | "default";

function statusVariant(status?: string): BadgeVariant {
  if (!status) return "default";
  if (status === "completed") return "green";
  if (status === "processing") return "cyan";
  if (status === "failed" || status === "quota" || status === "rate_limited") return "red";
  if (status === "pending") return "amber";
  return "default";
}

type Props = {
  session: VideoSession;
  selected: boolean;
  onSelect: () => void;
  onOpen: () => void;
};

export function LibraryCard({ session, selected, onSelect, onOpen }: Props) {
  const deleteSession = useSessionsStore((s) => s.deleteSession);
  const addToast = useUiStore((s) => s.addToast);
  const [deleting, setDeleting] = useState(false);

  async function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    setDeleting(true);
    try {
      await deleteSession(session.session_id);
      addToast("Session deleted", "success");
    } catch {
      addToast("Failed to delete session", "error");
      setDeleting(false);
    }
  }

  return (
    <div className={`lib-card${selected ? " lib-card--selected" : ""}`}>
      <label className="lib-card__check" onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          checked={selected}
          onChange={onSelect}
          aria-label={`Select ${session.title}`}
        />
      </label>
      <button className="lib-card__body" onClick={onOpen}>
        <span className="lib-card-title">{session.title}</span>
        <div className="lib-card__meta">
          <span className="lib-card__date">{humanDate(session.created_at)}</span>
          {session.analysis_status && (
            <Badge variant={statusVariant(session.analysis_status)}>
              {statusLabel(session.analysis_status)}
            </Badge>
          )}
        </div>
      </button>
      <button
        className="lib-card__delete"
        onClick={handleDelete}
        disabled={deleting}
        aria-label="Delete session"
        title="Delete session"
      >
        <Trash2 size={13} />
      </button>
    </div>
  );
}
