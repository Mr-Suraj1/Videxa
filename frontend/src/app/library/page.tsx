"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useSessionsStore } from "@/store/sessions";
import { LibraryCard } from "@/components/library/LibraryCard";
import { SkeletonCard } from "@/components/ui/Skeleton";

export default function LibraryPage() {
  const { sessions, loading, refreshSessions, toggleSession, selectedIds, openSession } =
    useSessionsStore();

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  return (
    <div className="library-page">
      <h1 className="library-page__title">Library</h1>
      <p className="library-page__sub">{sessions.length} session{sessions.length !== 1 ? "s" : ""}</p>

      {loading ? (
        <div className="library-grid">
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : sessions.length === 0 ? (
        <div style={{ color: "var(--muted)", fontSize: 12 }}>
          No sessions yet.{" "}
          <Link href="/" style={{ color: "var(--purple)" }}>Analyze your first video →</Link>
        </div>
      ) : (
        <div className="library-grid">
          {sessions.map((s) => (
            <LibraryCard
              key={s.session_id}
              session={s}
              selected={selectedIds.has(s.session_id)}
              onSelect={() => toggleSession(s.session_id)}
              onOpen={() => openSession(s)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
