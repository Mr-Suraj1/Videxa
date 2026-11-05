"use client";
import { useState, useEffect } from "react";
import { use } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { getSession, getSessionContent } from "@/lib/api";
import type { SessionStatus, SessionContent } from "@/types";
import { SummaryPanel } from "@/components/analysis/SummaryPanel";
import { InsightGrid } from "@/components/analysis/InsightGrid";
import { TranscriptPanel } from "@/components/analysis/TranscriptPanel";
import { ExportActions } from "@/components/export/ExportActions";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { SkeletonText } from "@/components/ui/Skeleton";
import type { Analysis } from "@/types";

type Tab = "summary" | "transcript" | "chat";

export default function SessionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [tab, setTab] = useState<Tab>("summary");
  const [session, setSession] = useState<SessionStatus | null>(null);
  const [content, setContent] = useState<SessionContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [s, c] = await Promise.all([getSession(id), getSessionContent(id)]);
        setSession(s);
        setContent(c);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load session");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  const analysis: Analysis | null =
    content?.analysis
      ? {
          status: "completed",
          session_id: id,
          transcript: content.transcript,
          analysis: content.analysis,
        }
      : null;

  return (
    <div className="session-page">
      <Link href="/" className="btn btn--ghost btn--sm" style={{ marginBottom: 16, display: "inline-flex" }}>
        <ArrowLeft size={14} /> Back
      </Link>

      {loading && <SkeletonText lines={6} />}
      {error && <p style={{ color: "var(--red, #f0aaaa)" }}>{error}</p>}

      {session && (
        <>
          <h1 className="session-page__title">{session.title}</h1>

          <div className="session-tabs">
            {(["summary", "transcript", "chat"] as Tab[]).map((t) => (
              <button
                key={t}
                className={`session-tab${tab === t ? " session-tab--active" : ""}`}
                onClick={() => setTab(t)}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          {tab === "summary" && analysis && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <SummaryPanel title={analysis.analysis.title} summary={analysis.analysis.summary} />
              <InsightGrid
                actionItems={analysis.analysis.action_items}
                keyDecisions={analysis.analysis.key_decisions}
                openQuestions={analysis.analysis.open_questions}
              />
              <ExportActions analysis={analysis} />
            </div>
          )}

          {tab === "summary" && !analysis && (
            <p style={{ color: "var(--muted)" }}>Analysis not available for this session.</p>
          )}

          {tab === "transcript" && content && (
            <TranscriptPanel transcript={content.transcript} />
          )}

          {tab === "chat" && (
            <ChatPanel sessionId={id} />
          )}
        </>
      )}
    </div>
  );
}
