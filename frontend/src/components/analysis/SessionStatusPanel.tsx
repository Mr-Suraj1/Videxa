"use client";
import { RefreshCw } from "lucide-react";
import type { SessionStatus } from "@/types";
import { statusLabel, canRetryAnalysis } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

type BadgeVariant = "green" | "amber" | "red" | "cyan" | "default";

function statusVariant(status?: string): BadgeVariant {
  if (status === "completed") return "green";
  if (status === "processing") return "cyan";
  if (status === "failed" || status === "quota" || status === "rate_limited") return "red";
  if (status === "pending") return "amber";
  return "default";
}

type Props = {
  session: SessionStatus;
  onRetry: () => void;
  retryBusy: boolean;
};

export function SessionStatusPanel({ session, onRetry, retryBusy }: Props) {
  const canRetry = canRetryAnalysis(session);
  return (
    <div className="status-panel">
      <div className="status-panel__row">
        <h2 className="status-panel__title">{session.title}</h2>
        <div className="status-panel__badges">
          {session.processing_status && (
            <Badge variant={statusVariant(session.processing_status)}>
              Processing: {statusLabel(session.processing_status)}
            </Badge>
          )}
          {session.analysis_status && (
            <Badge variant={statusVariant(session.analysis_status)}>
              Analysis: {statusLabel(session.analysis_status)}
            </Badge>
          )}
        </div>
      </div>
      {session.analysis_error && (
        <p className="status-panel__error">{session.analysis_error}</p>
      )}
      {canRetry && (
        <Button variant="secondary" size="sm" loading={retryBusy} onClick={onRetry}>
          <RefreshCw size={13} />
          Retry Analysis
        </Button>
      )}
    </div>
  );
}
