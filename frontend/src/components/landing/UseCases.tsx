import { Section } from './Section';

const USE_CASES = [
  {
    tag: 'Finance',
    title: 'Financial document intelligence',
    description: 'Market reports and financial statements are structured into equities, bonds, indices and exchange-rate datasets. Rwanda Stock Exchange reports get a purpose-built dashboard as one specialized profile.',
  },
  {
    tag: 'Accounting',
    title: 'Invoices & accounting automation',
    description: 'Invoices, receipts and accounting documents are parsed into line items, totals and dates, validated against each other, and ready to export or reconcile.',
  },
  {
    tag: 'Logistics',
    title: 'Logistics & shipping documents',
    description: 'Waybills, manifests and shipment records are classified automatically and turned into trackable datasets, KPIs and trend charts.',
  },
  {
    tag: 'Agriculture',
    title: 'Agriculture & operations reports',
    description: 'Yield reports, supply logs and field data however they arrive are profiled, structured and organized into datasets you can browse and export.',
  },
  {
    tag: 'Generic',
    title: 'Any business document',
    description: 'Spreadsheets, Word documents and text files with no template at all are split into sections, entities and datasets by the same underlying engine.',
  },
];

export function UseCases() {
  return (
    <Section
      id="use-cases"
      eyebrow="Use cases"
      heading="One engine, every business document"
      subheading="A general-purpose document intelligence engine with specialized workflows for the domains that need them RSE market reports included."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {USE_CASES.map((useCase) => (
          <div key={useCase.title} className="rounded-lg border p-5" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
            <span
              className="inline-block rounded-full px-2.5 py-1 text-sm font-semibold uppercase tracking-wide"
              style={{ background: 'var(--neutral-chip-soft)', color: 'var(--neutral-chip)' }}
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
