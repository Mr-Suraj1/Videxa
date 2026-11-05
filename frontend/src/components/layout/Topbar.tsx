"use client";
import { Menu, Wifi, WifiOff } from "lucide-react";
import { useUiStore } from "@/store/ui";

export function Topbar() {
  const { apiOnline, toggleSidebar } = useUiStore();

  return (
    <header className="topbar">
      <button
        className="topbar__hamburger"
        onClick={toggleSidebar}
        aria-label="Toggle sidebar"
      >
        <Menu size={20} />
      </button>
      <span className="topbar__brand">Videxa</span>
      <div className="topbar__status">
        {apiOnline === null ? null : apiOnline ? (
          <Wifi size={15} className="topbar__status--online" aria-label="API online" />
        ) : (
          <WifiOff size={15} className="topbar__status--offline" aria-label="API offline" />
        )}
      </div>
    </header>
  );
}
