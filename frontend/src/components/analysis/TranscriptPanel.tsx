"use client";
import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

type Props = { transcript: string };

export function TranscriptPanel({ transcript }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="transcript-panel">
      <button
        className="transcript-panel__toggle"
        onClick={() => setExpanded((v) => !v)}
        type="button"
      >
        <span>Transcript</span>
        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {expanded && <pre className="transcript-panel__text">{transcript}</pre>}
    </section>
  );
}
