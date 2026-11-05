export type AnalysisStatus = "pending" | "processing" | "completed" | "failed" | "rate_limited" | "quota" | string;

export type AnalysisData = {
  title: string;
  summary: string;
  action_items: string;
  key_decisions: string;
  open_questions: string;
};

export type Analysis = {
  status: "completed";
  session_id: string;
  transcript: string;
  analysis: AnalysisData;
};

export type VideoSession = {
  session_id: string;
  title: string;
  created_at: string;
  processing_status?: string;
  analysis_status?: AnalysisStatus;
};

export type SessionStatus = VideoSession & { analysis_error?: string | null };

export type SessionContent = {
  session_id: string;
  title: string;
  transcript: string;
  analysis: AnalysisData | null;
};

export type ChatMessage = { role: "user" | "assistant"; content: string };

export type ToastType = "success" | "error" | "warning" | "info";

export type Toast = {
  id: string;
  type: ToastType;
  message: string;
};
