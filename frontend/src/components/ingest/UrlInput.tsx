"use client";
import { useState } from "react";
import { Youtube } from "lucide-react";
import { extractYouTubeId } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

type Props = {
  onSubmit: (url: string, language: string) => void;
  busy: boolean;
};

const LANGUAGES = [
  { value: "english", label: "English" },
  { value: "hinglish", label: "Hinglish" },
];

export function UrlInput({ onSubmit, busy }: Props) {
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("english");

  const ytId = extractYouTubeId(url);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim(), language);
  }

  return (
    <div className="url-input">
      {ytId && (
        <div className="url-input__thumbnail">
          <img
            src={`https://img.youtube.com/vi/${ytId}/mqdefault.jpg`}
            alt="YouTube thumbnail"
            className="url-input__yt-img"
          />
          <Youtube size={16} className="url-input__yt-icon" />
        </div>
      )}
      <form className="url-input__form" onSubmit={handleSubmit}>
        <input
          className="url-input__field"
          type="url"
          placeholder="Paste YouTube URL…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={busy}
        />
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
        <Button type="submit" loading={busy} disabled={!url.trim()}>
          Analyze
        </Button>
      </form>
    </div>
  );
}
