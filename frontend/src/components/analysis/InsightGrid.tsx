type InsightCardProps = { label: string; content: string; accent?: string };

function InsightCard({ label, content, accent }: InsightCardProps) {
  return (
    <div className="insight-card" style={accent ? { borderTopColor: accent } : undefined}>
      <h3 className="insight-card__label">{label}</h3>
      <p className="insight-card__content">{content}</p>
    </div>
  );
}

type Props = {
  actionItems: string;
  keyDecisions: string;
  openQuestions: string;
};

export function InsightGrid({ actionItems, keyDecisions, openQuestions }: Props) {
  return (
    <div className="insight-grid">
      <InsightCard label="Action Items" content={actionItems} accent="var(--cyan)" />
      <InsightCard label="Key Decisions" content={keyDecisions} accent="var(--green)" />
      <InsightCard label="Open Questions" content={openQuestions} accent="var(--amber)" />
    </div>
  );
}
