type Props = { title: string; summary: string };

export function SummaryPanel({ title, summary }: Props) {
  return (
    <section className="summary-panel">
      <h1 className="summary-panel__title">{title}</h1>
      <p className="summary-panel__text">{summary}</p>
    </section>
  );
}
