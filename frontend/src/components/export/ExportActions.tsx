"use client";
import { useState } from "react";
import { FileText, FileSpreadsheet, FileDown } from "lucide-react";
import type { Analysis } from "@/types";
import * as api from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { useUiStore } from "@/store/ui";

type Props = { analysis: Analysis };

export function ExportActions({ analysis }: Props) {
  const addToast = useUiStore((s) => s.addToast);
  const [busy, setBusy] = useState<"transcript" | "analysis" | "pdf" | null>(null);

  const a = analysis.analysis;

  async function download(type: "transcript" | "analysis" | "pdf") {
    setBusy(type);
    try {
      let blob: Blob;
      let filename: string;
      if (type === "transcript") {
        blob = await api.exportTranscript(analysis.transcript);
        filename = "transcript.txt";
      } else if (type === "analysis") {
        blob = await api.exportAnalysis({ ...a, transcript: analysis.transcript });
        filename = "analysis.md";
      } else {
        blob = await api.exportPdf({ ...a, transcript: analysis.transcript });
        filename = "analysis.pdf";
      }
      api.downloadBlob(blob, filename);
      addToast(`${filename} downloaded`, "success");
    } catch (err) {
      addToast(err instanceof Error ? err.message : "Export failed", "error");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="export-actions">
      <Button variant="secondary" size="sm" loading={busy === "transcript"} onClick={() => download("transcript")}>
        <FileText size={14} /> Transcript
      </Button>
      <Button variant="secondary" size="sm" loading={busy === "analysis"} onClick={() => download("analysis")}>
        <FileSpreadsheet size={14} /> Analysis MD
      </Button>
      <Button variant="secondary" size="sm" loading={busy === "pdf"} onClick={() => download("pdf")}>
        <FileDown size={14} /> Analysis PDF
      </Button>
    </div>
  );
}
