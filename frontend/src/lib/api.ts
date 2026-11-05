import { API_BASE } from "./constants";
import type { Analysis, VideoSession, SessionStatus, SessionContent } from "@/types";

export class ApiError extends Error {
  session_id?: string;
  analysis_status?: string;
  processing_status?: string;

  constructor(message: string, data: Partial<ApiError> = {}) {
    super(message);
    this.name = "ApiError";
    this.session_id = data.session_id;
    this.analysis_status = data.analysis_status;
    this.processing_status = data.processing_status;
  }
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let body: Record<string, unknown> = {};
    try {
      body = await response.json();
    } catch { /* non-JSON error */ }
    if (typeof body.detail === "string") message = body.detail;
    throw new ApiError(message, body as Partial<ApiError>);
  }
  return response;
}

export async function healthCheck(): Promise<boolean> {
  try {
    await apiFetch("/health");
    return true;
  } catch {
    return false;
  }
}

export async function getSessions(): Promise<VideoSession[]> {
  const res = await apiFetch("/sessions");
  const body = await res.json();
  return body.sessions || [];
}

export async function getSession(id: string): Promise<SessionStatus> {
  const res = await apiFetch(`/sessions/${encodeURIComponent(id)}`);
  return res.json();
}

export async function getSessionContent(id: string): Promise<SessionContent> {
  const res = await apiFetch(`/sessions/${encodeURIComponent(id)}/content`);
  return res.json();
}

export async function processYouTube(url: string, language: string): Promise<Analysis> {
  const res = await apiFetch("/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source: url.trim(), language }),
  });
  return res.json();
}

export async function processUpload(file: File, language: string): Promise<Analysis> {
  const form = new FormData();
  form.set("file", file);
  form.set("language", language);
  const res = await apiFetch("/process/upload", { method: "POST", body: form });
  return res.json();
}

export async function retryAnalysis(id: string): Promise<Analysis> {
  const res = await apiFetch(
    `/sessions/${encodeURIComponent(id)}/analysis/retry`,
    { method: "POST" },
  );
  return res.json();
}

export async function chat(sessionId: string, question: string): Promise<string> {
  const res = await apiFetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  const body = await res.json();
  return body.answer as string;
}

export async function chatMulti(sessionIds: string[], question: string): Promise<string> {
  const res = await apiFetch("/chat/multi", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_ids: sessionIds, question }),
  });
  const body = await res.json();
  return body.answer as string;
}

export async function exportTranscript(transcript: string): Promise<Blob> {
  const res = await apiFetch("/exports/transcript", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript }),
  });
  return res.blob();
}

export async function exportAnalysis(payload: {
  title: string;
  summary: string;
  action_items: string;
  key_decisions: string;
  open_questions: string;
  transcript: string;
}): Promise<Blob> {
  const res = await apiFetch("/exports/analysis", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.blob();
}

export async function exportPdf(payload: {
  title: string;
  summary: string;
  action_items: string;
  key_decisions: string;
  open_questions: string;
  transcript: string;
}): Promise<Blob> {
  const res = await apiFetch("/exports/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.blob();
}

export async function deleteSession(id: string): Promise<void> {
  await apiFetch(`/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
