import { Download, FileSpreadsheet } from 'lucide-react';

import { Section } from './Section';

export function ExportWorkflow() {
  return (
    <Section tone="subtle">
      <div className="grid items-center gap-10 lg:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--brand)' }}>Export</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl" style={{ color: 'var(--text)' }}>
            Take the data with you
          </h2>
          <p className="mt-3 max-w-md text-[15px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
            Once you&rsquo;ve reviewed the dashboard, download a clean, formatted Excel workbook — every
            dataset, table and figure organized onto its own sheet, matching what you saw on screen.
            No manual re-entry, no reformatting.
          </p>
          <div className="mt-6 inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold" style={{ background: 'var(--brand)', color: 'var(--brand-contrast)' }}>
            <Download size={15} />
            Download Excel workbook
          </div>
        </div>

        <div className="rounded-lg border p-6" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
          <div className="flex items-center gap-3 border-b pb-4" style={{ borderColor: 'var(--border)' }}>
            <div className="flex h-10 w-10 items-center justify-center rounded-md" style={{ background: 'var(--positive-soft)', color: 'var(--positive)' }}>
              <FileSpreadsheet size={18} />
            </div>
            <div>
              <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>RSE_Report_2026-09-07.xlsx</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>7 sheets · generated just now</p>
            </div>
          </div>
          <ul className="mt-4 space-y-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
            {['MARKET SUMMARY', 'STOCK', 'BONDS', 'BONDS TRADES', 'EXCHANGE RATE'].map((sheet) => (
              <li key={sheet} className="flex items-center justify-between rounded-md px-3 py-2" style={{ background: 'var(--bg-subtle)' }}>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{sheet}</span>
                <span className="text-xs" style={{ color: 'var(--text-muted)' }}>sheet</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Section>
  );
}
