import type { VideoSession, SessionStatus } from "@/types";

export function statusLabel(status?: string): string {
  if (!status) return "Unknown";
  return status.replaceAll("_", " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

export function canRetryAnalysis(
  session?: SessionStatus | VideoSession | null,
): boolean {
  return (
    session?.processing_status === "completed" &&
    ["failed", "rate_limited", "quota"].includes(session.analysis_status || "")
  );
}

export function shortId(id: string): string {
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

export function humanDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Recently added"
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function extractYouTubeId(url: string): string | null {
  try {
    const u = new URL(url);
    if (u.hostname === "youtu.be") return u.pathname.slice(1).split("?")[0];
    if (u.hostname.includes("youtube.com")) return u.searchParams.get("v");
  } catch {
    // not a valid URL
  }
  return null;
}
