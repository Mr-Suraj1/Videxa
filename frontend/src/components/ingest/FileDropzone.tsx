"use client";
import { useState, useRef, useCallback } from "react";
import { Upload, File as FileIcon } from "lucide-react";
import { Button } from "@/components/ui/Button";

type Props = {
  onSubmit: (file: File, language: string) => void;
  busy: boolean;
};

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "auto", label: "Auto-detect" },
];

export function FileDropzone({ onSubmit, busy }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("en");
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const accept = useCallback((f: File) => setFile(f), []);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) accept(f);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) accept(f);
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (file) onSubmit(file, language);
  }

  return (
    <div className="dropzone-wrapper">
      <div
        className={`dropzone${dragging ? " dropzone--active" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !busy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        aria-label="Upload audio or video file"
      >
        <input
          ref={inputRef}
          type="file"
          accept="audio/*,video/*,.mp4,.webm,.m4a,.mp3,.wav"
          className="dropzone__input"
          onChange={handleChange}
          disabled={busy}
        />
        {file ? (
          <div className="dropzone__file">
            <FileIcon size={18} />
            <span>{file.name}</span>
          </div>
        ) : (
          <div className="dropzone__hint">
            <Upload size={22} />
            <span>Drop audio/video or click to browse</span>
          </div>
        )}
      </div>
      {file && (
        <form className="dropzone__controls" onSubmit={handleSubmit}>
          <select
            className="url-input__lang"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            disabled={busy}
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
          <Button type="submit" loading={busy}>Analyze</Button>
          <Button type="button" variant="ghost" onClick={() => setFile(null)}>Clear</Button>
        </form>
      )}
    </div>
  );
}
