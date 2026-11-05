"use client";
import type { VideoSession } from "@/types";
import { humanDate, statusLabel } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";

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
  return (
    <div className={`lib-card${selected ? " lib-card--selected" : ""}`}>
      <label className="lib-card__check">
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
    </div>
  );
}
