import { SearchInput } from '../common/SearchInput';
import { Dropdown } from '../common/Dropdown';
import type {
  ReportFacets,
  ReportListParams,
  ReportStatus,
} from '../../types/report';

const STATUS_OPTIONS: { value: ReportStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'completed', label: 'Processed' },
  { value: 'processing', label: 'Processing' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
];

const SORT_OPTIONS: {
  value: NonNullable<ReportListParams['sort']>;
  label: string;
}[] = [
  { value: '-created_at', label: 'Newest uploaded' },
  { value: 'created_at', label: 'Oldest uploaded' },
  { value: '-report_date', label: 'Document date (newest)' },
  { value: 'report_date', label: 'Document date (oldest)' },
  { value: 'filename', label: 'Name (A-Z)' },
  { value: '-filename', label: 'Name (Z-A)' },
  { value: '-value', label: 'Highest value' },
  { value: 'value', label: 'Lowest value' },
];

export function DocumentFilterBar({
  params,
  onChange,
  facets,
}: {
  params: ReportListParams;
  onChange: (patch: Partial<ReportListParams>) => void;
  facets: ReportFacets | null;
  showOwnerFilter?: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <SearchInput value={params.search ?? ''} onChange={(v) => onChange({ search: v, page: 1 })} placeholder="Search documents…" />

      <Dropdown
  label="Format"
  value={params.source_type ?? ''}
  onChange={(v) => onChange({ source_type: v as ReportListParams['source_type'], page: 1 })}
  placeholder="All formats"
  options={[
    { value: '', label: 'All formats' },
    ...(facets?.source_types ?? []).map((t) => ({ value: t, label: t.toUpperCase() })),
  ]}
/>

<Dropdown
  label="Status"
  value={params.status ?? ''}
  onChange={(v) => onChange({ status: v as ReportListParams['status'], page: 1 })}
  placeholder="All statuses"
  options={STATUS_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
/>

{facets && facets.years.length > 0 && (
  <Dropdown
    label="Year"
    value={params.year ?? ''}
    onChange={(v) => onChange({ year: v, page: 1 })}
    placeholder="All years"
    options={[
      { value: '', label: 'All years' },
      ...facets.years.map((y) => ({ value: String(y), label: String(y) })),
    ]}
  />
)}

{facets && facets.document_types.length > 1 && (
  <Dropdown
    label="Document type"
    value={params.document_type ?? ''}
    onChange={(v) => onChange({ document_type: v, page: 1 })}
    placeholder="All types"
    options={[
      { value: '', label: 'All types' },
      ...facets.document_types.map((t) => ({ value: t, label: t })),
    ]}
  />
)}

<Dropdown
  label="Sort by"
  value={params.sort ?? '-created_at'}
  onChange={(v) => onChange({ sort: v as ReportListParams['sort'] })}
  placeholder="Newest uploaded"
  options={SORT_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
/>
    </div>
  );
}
