"use client";
import { useState, useRef, useEffect } from "react";
import { Trash2, Pencil } from "lucide-react";
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
  const updateTitle = useSessionsStore((s) => s.updateTitle);
  const addToast = useUiStore((s) => s.addToast);
  const [deleting, setDeleting] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(session.title);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

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

  function startEdit(e: React.MouseEvent) {
    e.stopPropagation();
    setDraft(session.title);
    setEditing(true);
  }

  async function commitEdit() {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === session.title) {
      setEditing(false);
      return;
    }
    try {
      await updateTitle(session.session_id, trimmed);
      addToast("Title updated", "success");
    } catch {
      addToast("Failed to update title", "error");
      setDraft(session.title);
    }
    setEditing(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") { e.preventDefault(); commitEdit(); }
    if (e.key === "Escape") { setDraft(session.title); setEditing(false); }
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

      {editing ? (
        <input
          ref={inputRef}
          className="lib-card__title-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commitEdit}
          onKeyDown={handleKeyDown}
          onClick={(e) => e.stopPropagation()}
          maxLength={200}
          aria-label="Edit session title"
        />
      ) : (
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
      )}

      {!editing && (
        <button
          className="lib-card__edit"
          onClick={startEdit}
          aria-label="Rename session"
          title="Rename"
        >
          <Pencil size={12} />
        </button>
      )}

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
