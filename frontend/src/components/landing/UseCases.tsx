import { LineChart, Receipt, Truck, Sprout, FileStack } from 'lucide-react';
import { Section } from './Section';

const USE_CASES = [
  {
    tag: 'Finance',
    title: 'Financial document intelligence',
    description: 'Market reports and financial statements are structured into equities, bonds, indices and exchange-rate datasets. Rwanda Stock Exchange reports get a purpose-built dashboard as one specialized profile.',
    icon: LineChart,
    accent: 'finance',
  },
  {
    tag: 'Accounting',
    title: 'Invoices & accounting automation',
    description: 'Invoices, receipts and accounting documents are parsed into line items, totals and dates, validated against each other, and ready to export or reconcile.',
    icon: Receipt,
    accent: 'accounting',
  },
  {
    tag: 'Logistics',
    title: 'Logistics & shipping documents',
    description: 'Waybills, manifests and shipment records are classified automatically and turned into trackable datasets, KPIs and trend charts.',
    icon: Truck,
    accent: 'logistics',
  },
  {
    tag: 'Agriculture',
    title: 'Agriculture & operations reports',
    description: 'Yield reports, supply logs and field data however they arrive are profiled, structured and organized into datasets you can browse and export.',
    icon: Sprout,
    accent: 'agriculture',
  },
  {
    tag: 'Generic',
    title: 'Any business document',
    description: 'Spreadsheets, Word documents and text files with no template at all are split into sections, entities and datasets by the same underlying engine.',
    icon: FileStack,
    accent: 'generic',
  },
];

export function UseCases() {
  return (
    <Section
      id="use-cases"
      eyebrow="Use cases"
      heading="One engine, every business document"
      subheading="A general-purpose document intelligence engine with specialized workflows for the domains that need them, RSE market reports included."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {USE_CASES.map((useCase) => {
          const Icon = useCase.icon;
          const glowVars = {
            '--card-tint': `var(--accent-${useCase.accent}-soft)`,
            '--glow-a': `var(--accent-${useCase.accent})`,
            '--glow-b': `var(--accent-${useCase.accent})`,
          } as React.CSSProperties;

          return (
            <div
              key={useCase.title}
              className="usecase-card flex h-full flex-col rounded-2xl border p-5 sm:p-6"
              style={{ borderColor: 'var(--border)', ...glowVars }}
            >
              <div className="flex items-start justify-between gap-3">
                <span className="glass-icon">
                  <Icon size={20} style={{ color: `var(--accent-${useCase.accent})` }} strokeWidth={2} />
                </span>
                <span className="glass-pill" style={{ color: `var(--accent-${useCase.accent})` }}>
                  {useCase.tag}
                </span>
              </div>

              <p className="mt-4 text-[15px] font-semibold leading-snug" style={{ color: 'var(--text)' }}>
                {useCase.title}
              </p>
              <p className="mt-2 flex-1 text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                {useCase.description}
              </p>
            </div>
          );
        })}
      </div>
    </Section>
  );
}