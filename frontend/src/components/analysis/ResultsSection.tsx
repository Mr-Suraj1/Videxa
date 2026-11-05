import type { Analysis } from "@/types";
import { SummaryPanel } from "./SummaryPanel";
import { InsightGrid } from "./InsightGrid";
import { TranscriptPanel } from "./TranscriptPanel";
import { ExportActions } from "@/components/export/ExportActions";

type Props = { analysis: Analysis };

export function ResultsSection({ analysis }: Props) {
  const a = analysis.analysis;
  return (
    <div className="results">
      <SummaryPanel title={a.title} summary={a.summary} />
      <InsightGrid
        actionItems={a.action_items}
        keyDecisions={a.key_decisions}
        openQuestions={a.open_questions}
      />
      <TranscriptPanel transcript={analysis.transcript} />
      <ExportActions analysis={analysis} />
    </div>
  );
}
