import { AlertTriangle, CheckCircle2 } from 'lucide-react';

import { Section } from './Section';

const PRINCIPLES = [
  'Every figure on the dashboard traces back to a specific place in the source document.',
  'Nothing is estimated, interpolated or invented to fill a gap missing data stays missing.',
  'Duplicate rows and inconsistent values are detected automatically, not assumed away.',
  'Extraction is deterministic: the same document produces the same result every time.',
];

export function DataQuality() {
  return (
    <Section tone="subtle" eyebrow="Data quality" heading="Nothing invented, nothing hidden" subheading="">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <ul className="space-y-4">
          {PRINCIPLES.map((principle) => (
            <li key={principle} className="flex items-start gap-3">
              <CheckCircle2 size={18} className="mt-0.5 shrink-0" style={{ color: 'var(--positive)' }} />
              <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{principle}</span>
            </li>
          ))}
        </ul>

        <div className="overflow-hidden rounded-lg border" style={{ borderColor: 'color-mix(in srgb, var(--warning) 35%, var(--border))', background: 'var(--warning-soft)' }}>
          <div className="flex items-center gap-2.5 px-4 py-3">
            <AlertTriangle size={15} style={{ color: 'var(--warning)' }} />
            <div>
              <span className="block text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--warning)' }}>Data quality</span>
              <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>2 issues require review</span>
            </div>
          </div>
          <ul className="space-y-2 border-t px-4 py-3 text-sm" style={{ borderColor: 'var(--warning)', color: 'var(--text)' }}>
            <li className="flex gap-2">
              <span style={{ color: 'var(--warning)' }}>•</span>
              <span>Duplicate row detected for Invoice #INV-2024-0183 both instances kept, flagged for review.</span>
            </li>
            <li className="flex gap-2">
              <span style={{ color: 'var(--warning)' }}>•</span>
              <span>3 rows in &ldquo;Revenue&rdquo; had non-numeric values and were excluded from totals.</span>
            </li>
          </ul>
        </div>
      </div>
    </Section>
  );
}
