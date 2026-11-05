"use client";
import { useEffect, useCallback } from "react";
import { healthCheck } from "@/lib/api";
import { useSessionsStore } from "@/store/sessions";
import { useChatStore } from "@/store/chat";
import { useUiStore } from "@/store/ui";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";
import { IngestCard } from "@/components/ingest/IngestCard";
import { ResultsSection } from "@/components/analysis/ResultsSection";
import { SessionStatusPanel } from "@/components/analysis/SessionStatusPanel";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { Skeleton } from "@/components/ui/Skeleton";

export default function HomePage() {
  const {
    selectedIds,
    selectedSession,
    analysis,
    busy,
    analyze,
    retryAnalysis,
    refreshSessions,
  } = useSessionsStore();

  const { clear: clearChat } = useChatStore();
  const { setApiOnline, addToast } = useUiStore();

  /* health check */
  useEffect(() => {
    healthCheck().then(setApiOnline);
    const interval = setInterval(() => healthCheck().then(setApiOnline), 30_000);
    return () => clearInterval(interval);
  }, [setApiOnline]);

  /* initial load */
  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const handleAnalyze = useCallback(
    async (source: string | File, language: string) => {
      clearChat();
      try {
        await analyze(source, language);
        addToast("Analysis complete", "success");
      } catch (err) {
        addToast(err instanceof Error ? err.message : "Analysis failed", "error");
      }
    },
    [analyze, clearChat, addToast],
  );

  const handleRetry = useCallback(async () => {
    if (!selectedSession) return;
    try {
      await retryAnalysis(selectedSession.session_id);
      addToast("Analysis retried", "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Retry failed", "error");
    }
  }, [retryAnalysis, selectedSession, addToast]);

  const selectedIdArray = Array.from(selectedIds);

  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-column">
        <Topbar />

        <div className="content-wrap">
          {/* Welcome row */}
          <div className="welcome-row">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" />
                VIDEXA&nbsp;AI
              </div>
              <h1>Your meeting,&nbsp;decoded.</h1>
              <p>Paste a YouTube link or upload audio/video to extract insights instantly.</p>
            </div>
            <div className="welcome-orb" aria-hidden="true">
              <div className="orb-core">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
              </div>
              <div className="orb-ring ring-one" />
              <div className="orb-ring ring-two" />
              <div className="orb-dot dot-one" />
              <div className="orb-dot dot-two" />
            </div>
          </div>

          {/* Ingest */}
          <IngestCard onAnalyze={handleAnalyze} busy={busy} />

          {/* Processing indicator */}
          {busy && (
            <div className="processing-card">
              <div className="processing-icon">
                <svg className="spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
              </div>
              <div>
                <b>Processing…</b>
                <p>Transcribing and analysing your video</p>
              </div>
              <div className="processing-bars">
                <i /><i /><i /><i />
              </div>
            </div>
          )}

          {/* Session status panel (when a session is loaded) */}
          {selectedSession && !analysis && (
            <SessionStatusPanel
              session={selectedSession}
              onRetry={handleRetry}
              retryBusy={busy}
            />
          )}

          {/* Results */}
          {analysis && <ResultsSection analysis={analysis} />}

          {/* Loading skeleton when fetching session content */}
          {!analysis && !selectedSession && busy && (
            <div style={{ marginTop: 20 }}>
              <Skeleton height={120} />
            </div>
          )}

          {/* Chat */}
          {(selectedIdArray.length > 0 || selectedSession) && (
            <div style={{ marginTop: 16 }}>
              <ChatPanel
                sessionId={selectedSession?.session_id ?? null}
                sessionIds={selectedIdArray}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
