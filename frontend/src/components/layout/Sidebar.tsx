"use client";
import { useEffect, useCallback, useState, useRef } from "react";
import Link from "next/link";
import { Search, Trash2, X, ArrowDownUp } from "lucide-react";
import { useSessionsStore } from "@/store/sessions";
import { useUiStore } from "@/store/ui";
import { LibraryCard } from "@/components/library/LibraryCard";
import { SkeletonCard } from "@/components/ui/Skeleton";
import type { VideoSession } from "@/types";

const FAILED_STATUSES = new Set(["quota", "rate_limited", "failed", "pending"]);
const ACTIVE_STATUSES = new Set(["pending", "processing"]);
const POLL_INTERVAL = 5000;

type SortKey = "newest" | "oldest";

function sortSessions(sessions: VideoSession[], key: SortKey): VideoSession[] {
  return [...sessions].sort((a, b) => {
    const diff = a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : 0;
    return key === "newest" ? -diff : diff;
  });
}

export function Sidebar() {
  const { sessions, loading, selectedIds, toggleSession, openSession, refreshSessions, deleteSession, clearSelection } =
    useSessionsStore();
  const { sidebarOpen, setSidebarOpen, addToast } = useUiStore();

  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("newest");
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const failedSessions = sessions.filter(
    (s) => s.analysis_status && FAILED_STATUSES.has(s.analysis_status),
  );

  const hasActive = sessions.some(
    (s) => s.analysis_status && ACTIVE_STATUSES.has(s.analysis_status),
  );

  // Polling: fast while sessions are actively processing, slow otherwise
  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (hasActive) {
      pollRef.current = setInterval(() => { refreshSessions(); }, POLL_INTERVAL);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [hasActive, refreshSessions]);

  // Initial load
  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const clearFailed = useCallback(async () => {
    let cleared = 0;
    for (const s of failedSessions) {
      try { await deleteSession(s.session_id); cleared++; } catch { /* skip */ }
    }
    if (cleared > 0) {
      addToast(`Cleared ${cleared} session${cleared !== 1 ? "s" : ""}`, "success");
    } else {
      addToast("Delete failed — restart the backend server", "error");
    }
  }, [failedSessions, deleteSession, addToast]);

  const bulkDelete = useCallback(async () => {
    if (selectedIds.size === 0) return;
    setBulkDeleting(true);
    const ids = Array.from(selectedIds);
    let deleted = 0;
    for (const id of ids) {
      try { await deleteSession(id); deleted++; } catch { /* skip */ }
    }
    setBulkDeleting(false);
    if (deleted > 0) {
      addToast(`Deleted ${deleted} session${deleted !== 1 ? "s" : ""}`, "success");
    } else {
      addToast("Delete failed — restart the backend server", "error");
    }
  }, [selectedIds, deleteSession, addToast]);

  const filtered = sortSessions(
    query.trim()
      ? sessions.filter((s) => s.title.toLowerCase().includes(query.trim().toLowerCase()))
      : sessions,
    sort,
  );

  return (
    <>
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside className={`sidebar${sidebarOpen ? " sidebar--open" : ""}`}>
        <div className="sidebar__header">
          <Link href="/app" className="sidebar__brand" onClick={() => setSidebarOpen(false)}>
            <span className="sidebar__brand-icon">▶</span>
            VIDEXA
          </Link>
        </div>

        <nav className="sidebar__nav">
          {/* Section row: label + sort + clear-failed */}
          <div className="sidebar__section-row">
            <span className="sidebar__section-label">Library</span>
            <div className="sidebar__section-actions">
              <button
                className="sidebar__icon-btn"
                title={sort === "newest" ? "Sorted: newest first" : "Sorted: oldest first"}
                onClick={() => setSort((s) => s === "newest" ? "oldest" : "newest")}
              >
                <ArrowDownUp size={11} />
              </button>
              {failedSessions.length > 0 && (
                <button
                  className="sidebar__clear-btn"
                  onClick={clearFailed}
                  title={`Clear ${failedSessions.length} failed`}
                >
                  <Trash2 size={11} />
                  Clear ({failedSessions.length})
                </button>
              )}
            </div>
          </div>

          {/* Search box */}
          <div className="sidebar__search">
            <Search size={12} className="sidebar__search-icon" />
            <input
              className="sidebar__search-input"
              type="search"
              placeholder="Filter sessions…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label="Filter sessions"
            />
            {query && (
              <button className="sidebar__search-clear" onClick={() => setQuery("")} aria-label="Clear filter">
                <X size={11} />
              </button>
            )}
          </div>

          {/* Session list */}
          {loading ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : filtered.length === 0 ? (
            <p className="sidebar__empty">
              {query ? "No sessions match" : "No sessions yet"}
            </p>
          ) : (
            filtered.map((s) => (
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

          {/* Bulk delete bar */}
          {selectedIds.size > 0 && (
            <div className="sidebar__bulk-bar">
              <span className="sidebar__bulk-count">{selectedIds.size} selected</span>
              <button className="sidebar__bulk-clear" onClick={clearSelection} title="Deselect all">
                <X size={11} /> Deselect
              </button>
              <button
                className="sidebar__bulk-delete"
                onClick={bulkDelete}
                disabled={bulkDeleting}
                title={`Delete ${selectedIds.size} session${selectedIds.size !== 1 ? "s" : ""}`}
              >
                <Trash2 size={11} />
                {bulkDeleting ? "Deleting…" : `Delete (${selectedIds.size})`}
              </button>
            </div>
          )}
        </nav>
      </aside>
    </>
  );
}
