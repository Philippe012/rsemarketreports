import { AlertTriangle, CheckCircle2 } from 'lucide-react';
import { Section } from './Section';

const PRINCIPLES = [
  'Every figure on the dashboard traces back to a specific place in the source document.',
  'Nothing is estimated, interpolated or invented to fill a gap missing data stays missing.',
  'Duplicate rows and inconsistent values are detected automatically, not assumed away.',
  'Extraction is deterministic: the same document produces the same result every time.',
];

const ISSUES = [
  'Duplicate row detected for Invoice #INV-2024-0183 both instances kept, flagged for review.',
  '3 rows in “Revenue” had non-numeric values and were excluded from totals.',
];

export function DataQuality() {
  return (
    <Section
      tone="subtle"
      eyebrow="Data quality"
      heading="Nothing invented, nothing hidden"
      subheading="Every extracted value is checked before it reaches your dashboard, and anything uncertain is surfaced instead of silently corrected."
    >
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <ul className="space-y-3">
          {PRINCIPLES.map((principle) => (
            <li
              key={principle}
              className="principle-item flex items-start gap-3 rounded-xl border p-3.5"
              style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}
            >
              <span
                className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
                style={{ background: 'var(--positive-soft)' }}
              >
                <CheckCircle2 size={14} style={{ color: 'var(--positive)' }} strokeWidth={2.5} />
              </span>
              <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                {principle}
              </span>
            </li>
          ))}
        </ul>

        <div className="quality-glow-wrap">
          <div
            className="quality-card overflow-hidden rounded-2xl border"
            style={{
              borderColor: 'color-mix(in srgb, var(--warning) 35%, var(--border))',
              background: 'var(--warning-soft)',
              boxShadow: 'var(--shadow-md)',
            }}
          >
            <div className="flex items-center gap-3 px-5 py-4">
              <span
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
                style={{ background: 'color-mix(in srgb var(--warning) 18%, transparent)' }}
              >
                <AlertTriangle size={18} style={{ color: 'var(--warning)' }} strokeWidth={2} />
              </span>
              <div>
                <span className="block text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--warning)' }}>
                  Data quality
                </span>
                <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
                  2 issues require review
                </span>
              </div>
            </div>

            <ul
              className="space-y-3 border-t px-5 py-4 text-sm"
              style={{ borderColor: 'color-mix(in srgb, var(--warning) 25%, var(--border))', color: 'var(--text)' }}
            >
              {ISSUES.map((issue) => (
                <li key={issue} className="flex gap-2.5">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: 'var(--warning)' }} />
                  <span className="leading-relaxed">{issue}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Section>
  );
}