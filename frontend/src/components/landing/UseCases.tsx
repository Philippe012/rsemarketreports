import { Section } from './Section';

const USE_CASES = [
  {
    tag: 'Specialized',
    title: 'RSE market reports',
    description: 'Rwanda Stock Exchange daily reports get a purpose-built dashboard: equities, bonds, indices, exchange rates and trading activity, laid out exactly as analysts expect.',
  },
  {
    tag: 'Generic',
    title: 'Sales & operations data',
    description: 'CSV exports or spreadsheets of sales, shipments or throughput are classified automatically and turned into KPIs and trend charts.',
  },
  {
    tag: 'Generic',
    title: 'HR & workforce records',
    description: 'Multi-sheet Excel workbooks employee rosters, department breakdowns become linked datasets you can browse and export.',
  },
  {
    tag: 'Generic',
    title: 'Narrative reports & notes',
    description: 'Word documents and text files with prose and embedded tables are split into sections, entities and datasets, even with no template at all.',
  },
];

export function UseCases() {
  return (
    <Section
      id="use-cases"
      eyebrow="Use cases"
      heading="One engine, many kinds of documents"
      subheading="RSE market reports are a specialized profile inside a universal document-intelligence engine — not the whole product."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {USE_CASES.map((useCase) => (
          <div key={useCase.title} className="rounded-lg border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <span
              className="inline-block rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide"
              style={{
                background: useCase.tag === 'Specialized' ? 'var(--brand-soft)' : 'var(--neutral-chip-soft)',
                color: useCase.tag === 'Specialized' ? 'var(--brand)' : 'var(--neutral-chip)',
              }}
            >
              {useCase.tag}
            </span>
            <p className="mt-3 text-[15px] font-semibold" style={{ color: 'var(--text)' }}>{useCase.title}</p>
            <p className="mt-1.5 text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{useCase.description}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
