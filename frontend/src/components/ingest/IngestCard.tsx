"use client";
import { useState } from "react";
import { UrlInput } from "./UrlInput";
import { FileDropzone } from "./FileDropzone";

type Mode = "url" | "file";

type Props = {
  onAnalyze: (source: string | File, language: string) => void;
  busy: boolean;
};

export function IngestCard({ onAnalyze, busy }: Props) {
  const [mode, setMode] = useState<Mode>("url");

  return (
    <div className="ingest-card">
      <div className="ingest-card__tabs">
        <button
          className={`ingest-tab${mode === "url" ? " ingest-tab--active" : ""}`}
          onClick={() => setMode("url")}
          type="button"
        >
          YouTube URL
        </button>
        <button
          className={`ingest-tab${mode === "file" ? " ingest-tab--active" : ""}`}
          onClick={() => setMode("file")}
          type="button"
        >
          Upload File
        </button>
      </div>
      <div className="ingest-card__body">
        {mode === "url" ? (
          <UrlInput onSubmit={(url, lang) => onAnalyze(url, lang)} busy={busy} />
        ) : (
          <FileDropzone onSubmit={(file, lang) => onAnalyze(file, lang)} busy={busy} />
        )}
      </div>
    </div>
  );
}
