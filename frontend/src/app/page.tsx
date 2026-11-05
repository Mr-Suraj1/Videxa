"use client";

import {
  Activity, ArrowDownToLine, ArrowRight, AudioLines, Check, ChevronDown,
  CircleHelp, Clock3, FileText, Film, FolderOpen, Globe2, Layers3, LoaderCircle,
  MessageCircle, Mic2, MoreHorizontal, Play, Plus, Send, Settings2,
  Sparkles, Upload, Video, X, Youtube,
} from "lucide-react";
import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type Analysis = {
  status: "completed";
  session_id: string;
  transcript: string;
  analysis: {
    title: string;
    summary: string;
    action_items: string;
    key_decisions: string;
    open_questions: string;
  };
};
type AnalysisStatus = "pending" | "processing" | "completed" | "failed" | "rate_limited" | "quota" | string;
type VideoSession = {
  session_id: string;
  title: string;
  created_at: string;
  processing_status?: string;
  analysis_status?: AnalysisStatus;
};
type SessionStatus = VideoSession & { analysis_error?: string | null };
type ChatMessage = { role: "user" | "assistant"; content: string };

class ApiError extends Error {
  session_id?: string;
  analysis_status?: AnalysisStatus;
  processing_status?: string;

  constructor(message: string, data: Partial<ApiError> = {}) {
    super(message);
    this.name = "ApiError";
    this.session_id = data.session_id;
    this.analysis_status = data.analysis_status;
    this.processing_status = data.processing_status;
  }
}

async function apiFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let body: Record<string, unknown> = {};
    try {
      body = await response.json();
    } catch { /* Keep the status message for non-JSON errors. */ }
    if (typeof body.detail === "string") message = body.detail;
    throw new ApiError(message, body as Partial<ApiError>);
  }
  return response;
}

function upsertSession(list: VideoSession[], session: VideoSession) {
  const next = list.filter((item) => item.session_id !== session.session_id);
  return [session, ...next];
}

function statusLabel(status?: string) {
  if (!status) return "Unknown";
  return status.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function canRetryAnalysis(session?: SessionStatus | VideoSession | null) {
  return session?.processing_status === "completed"
    && ["failed", "rate_limited", "quota"].includes(session.analysis_status || "");
}

function shortId(id: string) {
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}

function humanDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Recently added" : date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function Home() {
  const [apiOnline, setApiOnline] = useState(false);
  const [sessions, setSessions] = useState<VideoSession[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);
  const [sessionsError, setSessionsError] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionStatus | null>(null);
  const [sessionStatusLoading, setSessionStatusLoading] = useState(false);
  const [sessionContentLoading, setSessionContentLoading] = useState(false);
  const [sessionContentError, setSessionContentError] = useState("");
  const [savedTranscript, setSavedTranscript] = useState<string | null>(null);
  const [retryingSessionId, setRetryingSessionId] = useState("");
  const [sessionError, setSessionError] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [source, setSource] = useState("");
  const [language, setLanguage] = useState("english");
  const [inputMode, setInputMode] = useState<"youtube" | "upload">("youtube");
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [chatBusy, setChatBusy] = useState(false);
  const [exporting, setExporting] = useState("");
  const [processError, setProcessError] = useState("");
  const [chatError, setChatError] = useState("");
  const [exportError, setExportError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeNav, setActiveNav] = useState("Overview");
  const [showAllSessions, setShowAllSessions] = useState(false);
  const statusRequestId = useRef(0);
  const contentRequestId = useRef(0);

  const refreshSessions = useCallback(async () => {
    setSessionsLoading(true);
    setSessionsError("");
    try {
      const response = await apiFetch("/sessions");
      const body = await response.json();
      setSessions(body.sessions || []);
      setApiOnline(true);
    } catch (caught) {
      setApiOnline(false);
      setSessionsError(caught instanceof Error ? caught.message : "The session library could not be loaded.");
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  const loadSessionStatus = useCallback(async (sessionId: string) => {
    const requestId = ++statusRequestId.current;
    setSessionStatusLoading(true);
    setSessionError("");
    setSelectedSession((current) => current?.session_id === sessionId ? current : null);
    try {
      const response = await apiFetch(`/sessions/${encodeURIComponent(sessionId)}`);
      const session: SessionStatus = await response.json();
      setSessions((current) => upsertSession(current, session));
      if (requestId === statusRequestId.current) setSelectedSession(session);
    } catch (caught) {
      if (requestId === statusRequestId.current) {
        setSessionError(caught instanceof Error ? caught.message : "Session status could not be loaded.");
      }
    } finally {
      if (requestId === statusRequestId.current) setSessionStatusLoading(false);
    }
  }, []);

  const loadSessionContent = useCallback(async (sessionId: string) => {
    const requestId = ++contentRequestId.current;
    setSessionContentLoading(true);
    setSessionContentError("");
    try {
      const response = await apiFetch(`/sessions/${encodeURIComponent(sessionId)}/content`);
      const body: { session_id: string; title: string; transcript: string; analysis: Analysis["analysis"] | null } = await response.json();
      if (requestId === contentRequestId.current) {
        setSavedTranscript(body.transcript);
        setAnalysis(body.analysis ? { status: "completed", session_id: body.session_id, transcript: body.transcript, analysis: body.analysis } : null);
      }
    } catch (caught) {
      if (requestId === contentRequestId.current) {
        setSavedTranscript(null);
        setAnalysis(null);
        setSessionContentError(caught instanceof Error ? caught.message : "Saved session content could not be loaded.");
      }
    } finally {
      if (requestId === contentRequestId.current) setSessionContentLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshSessions();
    try {
      sessionStorage.removeItem("videxa:analyses");
      const selectedSessionId = sessionStorage.getItem("videxa:selected-session");
      if (selectedSessionId) {
        setSelectedIds([selectedSessionId]);
        setActiveNav("Library");
        void loadSessionStatus(selectedSessionId);
        void loadSessionContent(selectedSessionId);
      }
    } catch { /* Browser storage is optional; the library remains available. */ }
  }, [loadSessionContent, loadSessionStatus, refreshSessions]);

  const selectedSessions = useMemo(
    () => sessions.filter((session) => selectedIds.includes(session.session_id)),
    [sessions, selectedIds],
  );

  function rememberAnalysis(result: Analysis) {
    statusRequestId.current += 1;
    contentRequestId.current += 1;
    setSessionStatusLoading(false);
    setSessionContentLoading(false);
    setSessionContentError("");
    setAnalysis(result);
    setSavedTranscript(result.transcript);
    setSelectedIds([result.session_id]);
    try { sessionStorage.setItem("videxa:selected-session", result.session_id); } catch { /* Selection persistence is optional. */ }
    setSelectedSession({
      session_id: result.session_id,
      title: result.analysis.title,
      created_at: sessions.find((session) => session.session_id === result.session_id)?.created_at || new Date().toISOString(),
      processing_status: "completed",
      analysis_status: "completed",
      analysis_error: null,
    });
    setMessages([]);
    setProcessError("");
    setChatError("");
    setExportError("");
    setSessionError("");
    setNotice("Analysis complete. Your transcript and insights are ready.");
    void refreshSessions();
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProcessError("");
    setNotice("");
    if (inputMode === "youtube" && !source.trim()) {
      setProcessError("Add a YouTube link to get started.");
      return;
    }
    if (inputMode === "upload" && !mediaFile) {
      setProcessError("Choose an audio or video file to upload.");
      return;
    }

    setBusy(true);
    try {
      let response: Response;
      if (inputMode === "youtube") {
        response = await apiFetch("/process", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source: source.trim(), language }),
        });
      } else {
        const form = new FormData();
        form.set("file", mediaFile as File);
        form.set("language", language);
        response = await apiFetch("/process/upload", { method: "POST", body: form });
      }
      rememberAnalysis(await response.json());
    } catch (caught) {
      const apiError = caught instanceof ApiError ? caught : null;
      setProcessError(caught instanceof Error ? caught.message : "Videxa could not process this video.");
      if (apiError?.session_id) {
        const sessionId = apiError.session_id;
        setSelectedIds([sessionId]);
        try { sessionStorage.setItem("videxa:selected-session", sessionId); } catch { /* Selection persistence is optional. */ }
        setAnalysis(null);
        setSavedTranscript(null);
        setMessages([]);
        setActiveNav("Library");
        setSelectedSession(null);
        await refreshSessions();
        await loadSessionStatus(sessionId);
        await loadSessionContent(sessionId);
        setSessionError(apiError.message);
      }
    } finally {
      setBusy(false);
    }
  }

  function toggleSession(sessionId: string) {
    const next = selectedIds.includes(sessionId)
      ? selectedIds.filter((id) => id !== sessionId)
      : [...selectedIds, sessionId].slice(-20);
    setSelectedIds(next);
    if (next.length === 1) {
      try { sessionStorage.setItem("videxa:selected-session", next[0]); } catch { /* Selection persistence is optional. */ }
      setAnalysis(null);
      setSavedTranscript(null);
      setSessionError("");
      setSessionContentError("");
      setExportError("");
      setChatError("");
      void loadSessionStatus(next[0]);
      void loadSessionContent(next[0]);
    } else {
      try { sessionStorage.removeItem("videxa:selected-session"); } catch { /* Selection persistence is optional. */ }
      statusRequestId.current += 1;
      contentRequestId.current += 1;
      setSessionStatusLoading(false);
      setSessionContentLoading(false);
      setSelectedSession(null);
      setSavedTranscript(null);
      setSessionContentError("");
      if (!next.includes(analysis?.session_id || "")) setAnalysis(null);
    }
    setMessages([]);
  }

  function openSession(sessionId: string) {
    setSelectedIds([sessionId]);
    try { sessionStorage.setItem("videxa:selected-session", sessionId); } catch { /* Selection persistence is optional. */ }
    setAnalysis(null);
    setSavedTranscript(null);
    void loadSessionStatus(sessionId);
    void loadSessionContent(sessionId);
    setMessages([]);
    setSessionError("");
    setSessionContentError("");
    setExportError("");
    setChatError("");
    setActiveNav("Library");
  }

  async function retryAnalysis(sessionId: string) {
    setRetryingSessionId(sessionId);
    setSessionError("");
    setSessionContentError("");
    setNotice("");
    try {
      const response = await apiFetch(`/sessions/${encodeURIComponent(sessionId)}/analysis/retry`, { method: "POST" });
      const result: Analysis = await response.json();
      rememberAnalysis(result);
      setNotice("Analysis completed using the saved transcript.");
      await loadSessionStatus(sessionId);
    } catch (caught) {
      const apiError = caught instanceof ApiError ? caught : null;
      const message = caught instanceof Error ? caught.message : "Analysis retry could not be completed.";
      if (apiError && selectedSession?.session_id === sessionId) {
        setSelectedSession((current) => current ? {
          ...current,
          analysis_status: apiError.analysis_status || current.analysis_status,
          processing_status: apiError.processing_status || current.processing_status,
          analysis_error: apiError.message,
        } : current);
      }
      await loadSessionStatus(sessionId);
      if (apiError?.session_id && apiError.session_id !== sessionId) {
        setSessionError(`${message} (Session ${apiError.session_id})`);
      } else {
        setSessionError(message);
      }
    } finally {
      setRetryingSessionId("");
      void refreshSessions();
    }
  }

  async function ask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed) return;
    if (!selectedIds.length) {
      setChatError("Select a video from the library before asking a question.");
      return;
    }
    setChatError("");
    setMessages((current) => [...current, { role: "user", content: trimmed }]);
    setQuestion("");
    setChatBusy(true);
    try {
      const multi = selectedIds.length > 1;
      const response = await apiFetch(multi ? "/chat/multi" : "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(multi
          ? { session_ids: selectedIds, question: trimmed }
          : { session_id: selectedIds[0], question: trimmed }),
      });
      const body = await response.json();
      setMessages((current) => [...current, { role: "assistant", content: body.answer }]);
    } catch (caught) {
      setMessages((current) => current.slice(0, -1));
      setChatError(caught instanceof Error ? caught.message : "The answer could not be generated.");
    } finally {
      setChatBusy(false);
    }
  }

  async function downloadExport(kind: "transcript" | "analysis" | "pdf") {
    if (kind === "transcript" ? savedTranscript === null : !analysis) return;
    setExportError("");
    const endpoint = kind === "pdf" ? "/exports/pdf" : `/exports/${kind}`;
    const payload = kind === "transcript"
      ? { transcript: savedTranscript }
      : { ...analysis!.analysis, title: analysis!.analysis.title, transcript: savedTranscript || analysis!.transcript };
    setExporting(kind);
    try {
      const response = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = kind === "pdf" ? "videxa-report.pdf" : kind === "transcript" ? "transcript.txt" : "analysis.md";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (caught) {
      setExportError(caught instanceof Error ? caught.message : "Export could not be created.");
    } finally {
      setExporting("");
    }
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setMediaFile(event.target.files?.[0] || null);
  }

  function navigateLibrary() {
    setActiveNav("Library");
    setShowAllSessions(true);
    document.getElementById("library")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function navigateOverview() {
    setActiveNav("Overview");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const currentTitle = analysis?.analysis.title || selectedSessions[0]?.title || "Your video workspace";
  const greeting = analysis ? "Your video, understood." : "Make every minute count.";

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#home" onClick={() => setActiveNav("Overview")}>
          <span className="brand-mark"><AudioLines size={21} strokeWidth={2.4} /></span>
          <span><strong>videxa</strong><small>VIDEO INTELLIGENCE</small></span>
        </a>

        <button className="new-analysis" onClick={() => { statusRequestId.current += 1; contentRequestId.current += 1; try { sessionStorage.removeItem("videxa:selected-session"); } catch { /* Selection persistence is optional. */ } setSessionStatusLoading(false); setSessionContentLoading(false); setAnalysis(null); setSavedTranscript(null); setSelectedSession(null); setSessionError(""); setSessionContentError(""); setProcessError(""); setChatError(""); setExportError(""); setNotice(""); setSelectedIds([]); setMessages([]); setActiveNav("Overview"); }}>
          <Plus size={17} /> New analysis <span>⌘ N</span>
        </button>

        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          <button className={activeNav === "Overview" ? "nav-item active" : "nav-item"} onClick={navigateOverview}><Layers3 size={17} /> Overview</button>
          <button className={activeNav === "Library" ? "nav-item active" : "nav-item"} onClick={navigateLibrary}><FolderOpen size={17} /> Video library <span className="nav-count">{sessions.length}</span></button>
        </nav>

        <div className="library-head"><span className="nav-label">RECENT VIDEOS</span><button aria-label="Refresh library" className="icon-button small" onClick={() => void refreshSessions()}><MoreHorizontal size={16} /></button></div>
        <div className="recent-list">
          {sessionsLoading ? <p className="empty-recent">Loading sessions…</p> : sessionsError ? <p className="empty-recent">Library unavailable. <button className="inline-retry" onClick={() => void refreshSessions()}>Retry</button></p> : sessions.length ? sessions.slice(0, 8).map((session) => (
            <button className={`recent-item ${selectedIds.includes(session.session_id) ? "selected" : ""}`} key={session.session_id} onClick={() => openSession(session.session_id)} title={session.title}>
              <span className="recent-icon"><Video size={15} /></span><span className="recent-copy"><b>{session.title || "Untitled video"}</b><small>{humanDate(session.created_at)}</small></span>
            </button>
          )) : <p className="empty-recent">Your analyzed videos will appear here.</p>}
        </div>

        <div className="sidebar-bottom">
          <div className="help-card"><span className="help-icon"><CircleHelp size={16} /></span><div><b>Need a hand?</b><small>Learn how Videxa works</small></div><ArrowRight size={15} /></div>
          <div className="profile-row"><div className="avatar">V</div><div><b>Personal workspace</b><small>Local session</small></div><Settings2 size={17} /></div>
        </div>
      </aside>

      <section className="main-column" id="home">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><b>{activeNav}</b></div>
          <div className="top-actions"><span className={`api-state ${apiOnline ? "online" : "offline"}`}><i />{apiOnline ? "API connected" : "API offline"}</span><button className="icon-button" title="Activity"><Activity size={18} /></button><div className="avatar top-avatar">V</div></div>
        </header>
        <nav className="mobile-nav" aria-label="Mobile navigation"><button className={activeNav === "Overview" ? "active" : ""} onClick={navigateOverview}><Layers3 size={15}/> Overview</button><button className={activeNav === "Library" ? "active" : ""} onClick={navigateLibrary}><FolderOpen size={15}/> Library <span>{sessions.length}</span></button></nav>

        <div className="content-wrap">
          <section className="welcome-row">
            <div><div className="eyebrow"><span className="eyebrow-line" /> YOUR AI VIDEO WORKSPACE</div><h1>{greeting}</h1><p>Turn long-form video into clear notes, decisions, and answers.</p></div>
            <div className="welcome-orb"><div className="orb-core"><AudioLines size={29} /></div><span className="orb-ring ring-one" /><span className="orb-ring ring-two" /><span className="orb-dot dot-one" /><span className="orb-dot dot-two" /></div>
          </section>

          <section className="ingest-card">
            <div className="ingest-top"><div><div className="section-kicker"><Sparkles size={15} /> START WITH A VIDEO</div><h2>Bring your video into focus</h2><p>Paste a YouTube link or upload a recording. We’ll take it from there.</p></div><div className="supported-pill"><Check size={13} /> MP4, MOV, MP3, WAV</div></div>
            <div className="source-tabs"><button className={inputMode === "youtube" ? "source-tab active" : "source-tab"} onClick={() => setInputMode("youtube")}><Youtube size={16} /> YouTube link</button><button className={inputMode === "upload" ? "source-tab active" : "source-tab"} onClick={() => setInputMode("upload")}><Upload size={16} /> Upload a file</button></div>
            <form onSubmit={analyze}>
              {inputMode === "youtube" ? <label className="url-field"><Youtube size={18} /><input value={source} onChange={(event) => setSource(event.target.value)} placeholder="Paste a YouTube video link" aria-label="YouTube URL"/><span className="field-hint">YOUTUBE</span></label> : <label className={`upload-field ${mediaFile ? "has-file" : ""}`}><input type="file" accept="audio/*,video/*,.mkv,.avi,.webm" onChange={chooseFile}/><span className="upload-icon"><Upload size={19}/></span><b>{mediaFile ? mediaFile.name : "Choose a video or audio file"}</b><small>{mediaFile ? `${(mediaFile.size / 1024 / 1024).toFixed(1)} MB · ready to analyze` : "Browse your device · Max 2 GB"}</small></label>}
              <div className="form-bottom"><label className="language-select"><Globe2 size={16}/><span>Transcription language</span><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="english">English</option><option value="hinglish">Hinglish</option></select><ChevronDown size={14}/></label><button className="analyze-button" type="submit" disabled={busy || !apiOnline}>{busy ? <><LoaderCircle className="spin" size={17}/> Analyzing…</> : <><Sparkles size={16}/> Analyze video <ArrowRight size={16}/></>}</button></div>
            </form>
            {processError && processError !== selectedSession?.analysis_error && <div className="alert error-alert" role="alert"><X size={16}/><span>{processError}</span></div>}
            {notice && <div className="alert success-alert"><Check size={16}/><span>{notice}</span><button onClick={() => setNotice("")} aria-label="Dismiss"><X size={14}/></button></div>}
            <div className="pipeline-note"><span><Mic2 size={14}/> Transcribe</span><i/><span><Sparkles size={14}/> Summarize</span><i/><span><MessageCircle size={14}/> Ask anything</span><small>Usually takes a few minutes</small></div>
          </section>

          {busy && <section className="processing-card"><div className="processing-icon"><LoaderCircle size={22} className="spin"/></div><div><b>Listening closely…</b><p>Videxa is preparing your transcript and insights. You can leave this tab open.</p></div><div className="processing-bars"><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/></div></section>}

          {(analysis || (selectedIds.length && !analysis)) && <section className="results-section">
            <div className="results-heading"><div><div className="section-kicker"><Sparkles size={15}/> VIDEO BRIEF</div><h2>{currentTitle}</h2><p>{analysis ? "A clear, searchable view of what matters." : savedTranscript ? "Your saved transcript is ready; analysis is not available yet." : "Open a saved session to load its transcript and analysis."}</p></div>{(analysis || savedTranscript) && <div className="export-actions"><button onClick={() => void downloadExport("transcript")} disabled={!!exporting || !savedTranscript}>{exporting === "transcript" ? <LoaderCircle size={15} className="spin"/> : <FileText size={15}/>} Transcript</button>{analysis && <><button onClick={() => void downloadExport("analysis")} disabled={!!exporting}>{exporting === "analysis" ? <LoaderCircle size={15} className="spin"/> : <FileText size={15}/>} Notes</button><button onClick={() => void downloadExport("pdf")} disabled={!!exporting}>{exporting === "pdf" ? <LoaderCircle size={15} className="spin"/> : <ArrowDownToLine size={15}/>} PDF</button></>}</div>}</div>
            {exportError && <div className="operation-error" role="alert">Export failed: {exportError}</div>}
            <div className="session-status-panel" aria-live="polite">
              {sessionStatusLoading && <span className="session-status-loading"><LoaderCircle size={14} className="spin"/> Loading session status…</span>}
              {sessionContentLoading && <span className="session-status-loading"><LoaderCircle size={14} className="spin"/> Loading saved transcript and analysis…</span>}
              {selectedSession && <>
                <div className="session-status-item"><span>Processing</span><b className={`status-badge status-${selectedSession.processing_status || "unknown"}`}>{statusLabel(selectedSession.processing_status)}</b></div>
                <div className="session-status-item"><span>Analysis</span><b className={`status-badge status-${selectedSession.analysis_status || "unknown"}`}>{statusLabel(selectedSession.analysis_status)}</b></div>
                {canRetryAnalysis(selectedSession) && <button className="retry-analysis-button" onClick={() => void retryAnalysis(selectedSession.session_id)} disabled={!!retryingSessionId || sessionStatusLoading}>
                  {retryingSessionId === selectedSession.session_id ? <><LoaderCircle size={14} className="spin"/> Retrying…</> : <><Sparkles size={14}/> Retry analysis</>}
                </button>}
              </>}
              {(sessionError || selectedSession?.analysis_error) && <div className="session-status-error" role="alert">{sessionError || selectedSession?.analysis_error}</div>}
              {sessionContentError && <div className="session-status-error" role="alert">{sessionContentError}</div>}
            </div>
            {analysis && <><div className="summary-panel"><div className="summary-icon"><Sparkles size={18}/></div><div><div className="summary-label">THE SHORT VERSION</div><p>{analysis.analysis.summary}</p></div></div><div className="insight-grid"><article className="insight-card"><div className="insight-heading"><span className="insight-symbol purple"><Check size={15}/></span><b>Action items</b></div><p>{analysis.analysis.action_items || "No action items were identified."}</p></article><article className="insight-card"><div className="insight-heading"><span className="insight-symbol cyan"><Layers3 size={15}/></span><b>Key decisions</b></div><p>{analysis.analysis.key_decisions || "No key decisions were identified."}</p></article><article className="insight-card"><div className="insight-heading"><span className="insight-symbol amber"><CircleHelp size={15}/></span><b>Open questions</b></div><p>{analysis.analysis.open_questions || "No open questions were identified."}</p></article></div></>}
            {savedTranscript !== null && <details className="transcript-panel"><summary><span><FileText size={16}/> Full transcript</span><span className="transcript-length">{savedTranscript.length.toLocaleString()} characters <ChevronDown size={15}/></span></summary><div className="transcript-body">{savedTranscript}<button onClick={() => void downloadExport("transcript")} disabled={!!exporting}>{exporting === "transcript" ? <LoaderCircle size={14} className="spin"/> : <ArrowDownToLine size={14}/>} Download transcript</button></div></details>}
          </section>}

          <section className="bottom-grid">
            <div className="library-card" id="library">
              <div className="card-heading"><div><div className="section-kicker"><FolderOpen size={14}/> YOUR LIBRARY</div><h3>{showAllSessions ? "Video library" : "Recent videos"}</h3></div><button className="text-button" onClick={() => { setShowAllSessions((current) => !current); setActiveNav("Library"); }}>{showAllSessions ? "Show recent" : "View library"} <ArrowRight size={14}/></button></div>
              {sessionsLoading ? <div className="library-empty"><LoaderCircle size={20} className="spin"/><p>Loading your sessions…</p></div> : sessionsError ? <div className="library-empty"><b>Couldn’t load your library</b><p>{sessionsError}</p><button onClick={() => void refreshSessions()}>Try again <ArrowRight size={14}/></button></div> : sessions.length ? <div className="library-list">{(showAllSessions ? sessions : sessions.slice(0, 4)).map((session, index) => <div className="library-row" key={session.session_id}><button className="session-check" aria-label={`Toggle ${session.title} for cross-video chat`} onClick={() => toggleSession(session.session_id)}>{selectedIds.includes(session.session_id) && <Check size={12}/>}</button><div className={`video-thumb thumb-${index % 4}`}><Play size={14} fill="currentColor"/></div><button className="library-title" onClick={() => openSession(session.session_id)}><b>{session.title}</b><small>{shortId(session.session_id)} · {statusLabel(session.analysis_status)}</small></button><span className="date-label"><Clock3 size={13}/>{humanDate(session.created_at)}</span><button className="icon-button small" onClick={() => toggleSession(session.session_id)} aria-label="Select for multi-video chat"><Layers3 size={15}/></button></div>)}</div> : <div className="library-empty"><div className="empty-illustration"><Film size={22}/><span/></div><b>Your library is ready</b><p>Analyze your first video to build a personal knowledge base.</p><button onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>Add your first video <ArrowRight size={14}/></button></div>}
              {!!selectedIds.length && <div className="selection-note"><Check size={14}/> {selectedIds.length} video{selectedIds.length === 1 ? "" : "s"} selected for grounded chat</div>}
            </div>

            <div className="chat-card">
              <div className="card-heading"><div><div className="section-kicker"><MessageCircle size={14}/> ASK YOUR VIDEOS</div><h3>Talk it through</h3></div><span className="chat-count">{selectedIds.length} selected</span></div>
              <div className="chat-messages">
                {!messages.length && <div className="chat-empty"><div className="chat-spark"><Sparkles size={17}/></div><b>{selectedIds.length ? "Ask a better question" : "Choose a video to begin"}</b><p>{selectedIds.length ? `Get a grounded answer from ${selectedIds.length > 1 ? "your selected videos" : "the video transcript"}.` : "Open a session from your library to ask questions about it."}</p>{!!selectedIds.length && <div className="suggestion-chips"><button onClick={() => setQuestion("What are the main takeaways?")}>Main takeaways</button><button onClick={() => setQuestion("What actions should I take next?")}>Next steps</button></div>}</div>}
                {messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><span className="message-avatar">{message.role === "assistant" ? <AudioLines size={14}/> : "Y"}</span><p>{message.content}</p></div>)}
                {chatBusy && <div className="message assistant"><span className="message-avatar"><AudioLines size={14}/></span><p className="typing"><i/><i/><i/></p></div>}
              </div>
              <form className="chat-input" onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={selectedIds.length ? "Ask about your video…" : "Select a video to begin"} disabled={!selectedIds.length || chatBusy}/><button type="submit" aria-label="Send question" disabled={!selectedIds.length || !question.trim() || chatBusy}><Send size={16}/></button></form>
              {chatError && <div className="operation-error" role="alert">{chatError}</div>}
              <div className="chat-footnote"><span><span className="tiny-shield">✓</span> Answers grounded in your videos</span><span>{selectedIds.length > 1 ? "Multi-video mode" : "Private workspace"}</span></div>
            </div>
          </section>

          <footer className="page-footer"><span>VIDEXA <i>·</i> VIDEO INTELLIGENCE</span><span>Made for the moments that matter.</span></footer>
        </div>
      </section>
    </main>
  );
}
