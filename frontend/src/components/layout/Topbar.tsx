"use client";
import Link from "next/link";
import { Menu } from "lucide-react";
import { useUiStore } from "@/store/ui";

export function Topbar() {
  const { apiOnline, toggleSidebar } = useUiStore();

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button className="topbar__hamburger" onClick={toggleSidebar} aria-label="Toggle sidebar">
          <Menu size={18} />
        </button>
        <div className="topbar__breadcrumb">
          <Link href="/" className="topbar__home-link">VIDEXA</Link>
          <span className="topbar__sep">/</span>
          <span className="topbar__page">Dashboard</span>
        </div>
      </div>
      <div className="topbar__right">
        <div className={`topbar__status topbar__status--${apiOnline === null ? "offline" : apiOnline ? "online" : "offline"}`}>
          <span className="topbar__status-dot" />
          {apiOnline === null ? "Connecting" : apiOnline ? "Online" : "Offline"}
        </div>
      </div>
    </header>
  );
}
