import type { ReactNode } from 'react';

import { SearchInput } from '../common/SearchInput';
import type { ReportFacets, ReportListParams, ReportStatus } from '../../types/report';

const STATUS_OPTIONS: { value: ReportStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'completed', label: 'Processed' },
  { value: 'processing', label: 'Processing' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
];

const SORT_OPTIONS: { value: NonNullable<ReportListParams['sort']>; label: string }[] = [
  { value: '-created_at', label: 'Newest uploaded' },
  { value: 'created_at', label: 'Oldest uploaded' },
  { value: '-report_date', label: 'Document date (newest)' },
  { value: 'report_date', label: 'Document date (oldest)' },
  { value: 'filename', label: 'Name (A–Z)' },
  { value: '-filename', label: 'Name (Z–A)' },
  { value: '-value', label: 'Highest value' },
  { value: 'value', label: 'Lowest value' },
];

function Select({ value, onChange, children, label }: { value: string; onChange: (v: string) => void; children: ReactNode; label: string }) {
  return (
    <label className="block">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border px-2.5 py-2 text-sm outline-none transition focus:ring-2"
        style={{ borderColor: 'var(--border)', background: 'var(--bg-subtle)', color: 'var(--text)' }}
      >
        {children}
      </select>
    </label>
  );
}

export function DocumentFilterBar({
  params,
  onChange,
  facets,
  showOwnerFilter = false,
}: {
  params: ReportListParams;
  onChange: (patch: Partial<ReportListParams>) => void;
  facets: ReportFacets | null;
  showOwnerFilter?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <SearchInput value={params.search ?? ''} onChange={(v) => onChange({ search: v, page: 1 })} placeholder="Search documents…" />

      <Select label="Format" value={params.source_type ?? ''} onChange={(v) => onChange({ source_type: v as ReportListParams['source_type'], page: 1 })}>
        <option value="">All formats</option>
        {facets?.source_types.map((t) => (
          <option key={t} value={t}>{t.toUpperCase()}</option>
        ))}
      </Select>

      <Select label="Status" value={params.status ?? ''} onChange={(v) => onChange({ status: v as ReportListParams['status'], page: 1 })}>
        {STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </Select>

      {facets && facets.years.length > 0 && (
        <Select label="Year" value={params.year ?? ''} onChange={(v) => onChange({ year: v, page: 1 })}>
          <option value="">All years</option>
          {facets.years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </Select>
      )}

      {facets && facets.document_types.length > 1 && (
        <Select label="Document type" value={params.document_type ?? ''} onChange={(v) => onChange({ document_type: v, page: 1 })}>
          <option value="">All types</option>
          {facets.document_types.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </Select>
      )}

      {showOwnerFilter && (
        <input
          type="text"
          value={params.owner ?? ''}
          onChange={(e) => onChange({ owner: e.target.value, page: 1 })}
          placeholder="Filter by owner email…"
          className="rounded-lg border px-3 py-2 text-sm outline-none transition focus:ring-2"
          style={{ borderColor: 'var(--border)', background: 'var(--bg-subtle)', color: 'var(--text)' }}
        />
      )}

      <Select label="Sort by" value={params.sort ?? '-created_at'} onChange={(v) => onChange({ sort: v as ReportListParams['sort'] })}>
        {SORT_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </Select>
    </div>
  );
}
