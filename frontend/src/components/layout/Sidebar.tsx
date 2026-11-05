"use client";
import { useEffect, useCallback } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { useSessionsStore } from "@/store/sessions";
import { useUiStore } from "@/store/ui";
import { LibraryCard } from "@/components/library/LibraryCard";
import { SkeletonCard } from "@/components/ui/Skeleton";

const FAILED_STATUSES = new Set(["quota", "rate_limited", "failed", "pending"]);

export function Sidebar() {
  const { sessions, loading, selectedIds, toggleSession, openSession, refreshSessions, deleteSession } =
    useSessionsStore();
  const { sidebarOpen, setSidebarOpen, addToast } = useUiStore();

  const failedSessions = sessions.filter(
    (s) => s.analysis_status && FAILED_STATUSES.has(s.analysis_status),
  );

  const clearFailed = useCallback(async () => {
    let cleared = 0;
    for (const s of failedSessions) {
      try {
        await deleteSession(s.session_id);
        cleared++;
      } catch { /* skip */ }
    }
    if (cleared > 0) {
      addToast(`Cleared ${cleared} session${cleared !== 1 ? "s" : ""}`, "success");
    } else {
      addToast("Delete failed — restart the backend server", "error");
    }
  }, [failedSessions, deleteSession, addToast]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar${sidebarOpen ? " sidebar--open" : ""}`}>
        <div className="sidebar__header">
          <Link href="/" className="sidebar__brand" onClick={() => setSidebarOpen(false)}>
            Videxa
          </Link>
        </div>

        <nav className="sidebar__nav">
          <div className="sidebar__section-row">
            <span className="sidebar__section-label">Library</span>
            {failedSessions.length > 0 && (
              <button
                className="sidebar__clear-btn"
                onClick={clearFailed}
                title={`Clear ${failedSessions.length} failed session${failedSessions.length !== 1 ? "s" : ""}`}
              >
                <Trash2 size={11} />
                Clear failed ({failedSessions.length})
              </button>
            )}
          </div>
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : sessions.length === 0 ? (
            <p className="sidebar__empty">No sessions yet</p>
          ) : (
            sessions.map((s) => (
              <LibraryCard
                key={s.session_id}
                session={s}
                selected={selectedIds.has(s.session_id)}
                onSelect={() => toggleSession(s.session_id)}
                onOpen={() => {
                  openSession(s);
                  setSidebarOpen(false);
                }}
              />
            ))
          )}
        </nav>
      </aside>
    </>
  );
}
