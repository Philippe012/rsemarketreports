import { AlertTriangle, BarChart3, FileCheck2, Sheet } from 'lucide-react';

import { Section } from './Section';

const CAPABILITIES = [
  {
    icon: FileCheck2,
    title: 'Structured extraction',
    description: 'Tables, columns and figures are recovered with their types inferred currency, percentage, date, identifier and more.',
  },
  {
    icon: AlertTriangle,
    title: 'Validation & warnings',
    description: 'Duplicate rows, out-of-range values and inconsistencies are flagged in a dedicated data-quality panel, not hidden.',
  },
  {
    icon: BarChart3,
    title: 'KPIs & charts',
    description: 'Relevant metrics and charts are generated automatically from whatever the document actually contains.',
  },
  {
    icon: Sheet,
    title: 'Excel export',
    description: 'Every dashboard exports to a clean, formatted Excel workbook that mirrors what you reviewed on screen.',
  },
];

export function Capabilities() {
  return (
    <Section
      id="capabilities"
      tone="subtle"
      eyebrow="Capabilities"
      heading="Built for accuracy, not guesswork"
      subheading="A general-purpose document engine with a specialized profile for Rwanda Stock Exchange market reports."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {CAPABILITIES.map((capability) => (
          <div
            key={capability.title}
            className="rounded-lg border p-5"
            style={{ background: 'var(--surface)', borderColor: 'var(--border)' }}
          >
            <div
              className="mb-3.5 flex h-9 w-9 items-center justify-center rounded-md"
              style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}
            >
              <capability.icon size={17} />
            </div>
            <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{capability.title}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{capability.description}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
