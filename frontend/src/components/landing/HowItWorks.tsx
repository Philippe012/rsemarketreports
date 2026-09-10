import { CheckCircle2, Download, FileSearch, LayoutDashboard, UploadCloud } from 'lucide-react';

import { Section } from './Section';

const STEPS = [
  { icon: UploadCloud, title: 'Upload', description: 'Drop in a PDF, Excel, Word, CSV or TXT file — no template or setup required.' },
  { icon: FileSearch, title: 'Extract', description: 'Text and tables are parsed deterministically: rows, columns, figures and structure are all recovered.' },
  { icon: CheckCircle2, title: 'Validate', description: 'Numbers are checked against the source and duplicates are flagged — every issue surfaces as a warning, never silently.' },
  { icon: LayoutDashboard, title: 'Visualize', description: 'KPIs, charts and tables are generated automatically, tailored to what the document contains.' },
  { icon: Download, title: 'Export', description: 'Download an organized, formatted Excel workbook whenever you need the data outside the dashboard.' },
];

export function HowItWorks() {
  return (
    <Section
      id="how-it-works"
      eyebrow="How it works"
      heading="From document to dashboard in five steps"
      subheading="The same deterministic pipeline runs on every upload nothing is invented, and every number traces back to the source."
    >
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
        {STEPS.map((step, i) => (
          <div key={step.title} className="relative">
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md"
                style={{ background: 'var(--brand-soft)', color: 'var(--brand)' }}
              >
                <step.icon size={16} />
              </div>
              <span className="text-xs font-semibold tabular-nums" style={{ color: 'var(--text-muted)' }}>
                {String(i + 1).padStart(2, '0')}
              </span>
            </div>
            <p className="mt-3 text-sm font-semibold" style={{ color: 'var(--text)' }}>{step.title}</p>
            <p className="mt-1.5 text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{step.description}</p>
          </div>
        ))}
      </div>
    </Section>
  );
}
