"use client";
import { useEffect } from "react";
import Link from "next/link";
import { useSessionsStore } from "@/store/sessions";
import { useUiStore } from "@/store/ui";
import { LibraryCard } from "@/components/library/LibraryCard";
import { SkeletonCard } from "@/components/ui/Skeleton";

export function Sidebar() {
  const { sessions, loading, selectedIds, toggleSession, openSession, refreshSessions } =
    useSessionsStore();
  const { sidebarOpen, setSidebarOpen } = useUiStore();

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
          <span className="sidebar__section-label">Library</span>
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
