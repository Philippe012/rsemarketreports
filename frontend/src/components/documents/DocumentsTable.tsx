import { Check, FileSpreadsheet, FileText, FileType, Pencil, Table, Trash2, UploadCloud, X } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '../common/Badge';
import { formatCompactNumber, formatDate } from '../../utils/formatters';
import type { ReportSummary, ReportStatus, SourceType } from '../../types/report';

const SOURCE_ICON: Record<SourceType, typeof FileText> = {
  pdf: FileText,
  excel: FileSpreadsheet,
  csv: Table,
  docx: FileType,
  txt: FileText,
};

const STATUS_TONE: Record<ReportStatus, 'positive' | 'negative' | 'neutral'> = {
  completed: 'positive',
  failed: 'negative',
  processing: 'neutral',
  pending: 'neutral',
};

const STATUS_LABEL: Record<ReportStatus, string> = {
  completed: 'Processed',
  failed: 'Failed',
  processing: 'Processing',
  pending: 'Pending',
};

type Row = ReportSummary & { owner_email?: string | null };

function RowFilename({ report, onRename }: { report: Row; onRename: (id: string, name: string) => Promise<void> }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(report.original_filename);
  const [saving, setSaving] = useState(false);

  if (!editing) {
    return (
      <div className="flex min-w-0 items-center gap-1.5">
        <Link to={`/app/documents/${report.id}`} className="truncate text-sm font-medium hover:underline" style={{ color: 'var(--text)' }}>
          {report.original_filename}
        </Link>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            setDraft(report.original_filename);
            setEditing(true);
          }}
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded transition hover:opacity-70"
          style={{ color: 'var(--text-muted)' }}
          aria-label="Rename"
        >
          <Pencil size={12} />
        </button>
      </div>
    );
  }

  const save = async () => {
    if (!draft.trim() || draft === report.original_filename) {
      setEditing(false);
      return;
    }
    setSaving(true);
    try {
      await onRename(report.id, draft.trim());
      setEditing(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex min-w-0 items-center gap-1.5" onClick={(e) => e.preventDefault()}>
      <input
        autoFocus
        value={draft}
        disabled={saving}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') void save();
          if (e.key === 'Escape') setEditing(false);
        }}
        className="w-full min-w-0 rounded-md border px-2 py-1 text-sm outline-none"
        style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
      />
      <button type="button" onClick={() => void save()} disabled={saving} className="flex h-6 w-6 shrink-0 items-center justify-center rounded" style={{ color: 'var(--positive)' }} aria-label="Save">
        <Check size={13} />
      </button>
      <button type="button" onClick={() => setEditing(false)} className="flex h-6 w-6 shrink-0 items-center justify-center rounded" style={{ color: 'var(--text-muted)' }} aria-label="Cancel">
        <X size={13} />
      </button>
    </div>
  );
}

/** The documents table shared by the personal Documents page and the
 * staff-only admin management page — an `owner` column and filter are the
 * only thing that differs between the two, controlled by `showOwner`. */
export function DocumentsTable({
  reports,
  selected,
  onToggleSelect,
  onToggleSelectAll,
  onRename,
  onDelete,
  showOwner = false,
}: {
  reports: Row[];
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
  onToggleSelectAll: () => void;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => void;
  showOwner?: boolean;
}) {
  const allSelected = reports.length > 0 && reports.every((r) => selected.has(r.id));

  return (
    <div className="overflow-x-auto rounded-lg border" style={{ borderColor: 'var(--border)', background: 'var(--surface)' }}>
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b text-xs" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
            <th className="w-10 px-4 py-3">
              <input type="checkbox" checked={allSelected} onChange={onToggleSelectAll} aria-label="Select all" />
            </th>
            <th className="px-2 py-3 font-medium">Document</th>
            <th className="px-3 py-3 font-medium">Type</th>
            {showOwner && <th className="px-3 py-3 font-medium">Owner</th>}
            <th className="px-3 py-3 font-medium">Date</th>
            <th className="px-3 py-3 font-medium">Value</th>
            <th className="px-3 py-3 font-medium">Status</th>
            <th className="w-10 px-3 py-3" />
          </tr>
        </thead>
        <tbody>
          {reports.map((report) => {
            const Icon = SOURCE_ICON[report.source_type];
            return (
              <tr key={report.id} className="border-b last:border-0 transition hover:opacity-95" style={{ borderColor: 'var(--border)' }}>
                <td className="px-4 py-3 align-top">
                  <input
                    type="checkbox"
                    checked={selected.has(report.id)}
                    onChange={() => onToggleSelect(report.id)}
                    aria-label={`Select ${report.original_filename}`}
                  />
                </td>
                <td className="max-w-[280px] px-2 py-3 align-top">
                  <div className="flex items-start gap-2.5">
                    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md" style={{ background: 'var(--neutral-icon)', color: 'var(--neutral-icon-fg)' }}>
                      <Icon size={14} />
                    </div>
                    <div className="min-w-0">
                      <RowFilename report={report} onRename={onRename} />
                      <p className="mt-0.5 text-sm" style={{ color: 'var(--text-muted)' }}>{report.source_type.toUpperCase()}</p>
                    </div>
                  </div>
                </td>
                <td className="px-3 py-3 align-top text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {report.document_type || '—'}
                </td>
                {showOwner && (
                  <td className="px-3 py-3 align-top text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {report.owner_email ?? '—'}
                  </td>
                )}
                <td className="px-3 py-3 align-top text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {report.report_date ? formatDate(report.report_date) : formatDate(report.created_at.slice(0, 10))}
                </td>
                <td className="px-3 py-3 align-top text-xs tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                  {report.headline_metric_value !== null ? (
                    <span title={report.headline_metric_label}>{formatCompactNumber(report.headline_metric_value)}</span>
                  ) : '—'}
                </td>
                <td className="px-3 py-3 align-top">
                  <Badge tone={STATUS_TONE[report.status]}>{STATUS_LABEL[report.status]}</Badge>
                </td>
                <td className="px-3 py-3 align-top">
                  <button
                    type="button"
                    onClick={() => onDelete(report.id)}
                    className="flex h-7 w-7 items-center justify-center rounded-md transition hover:opacity-70"
                    style={{ color: 'var(--negative)' }}
                    aria-label={`Delete ${report.original_filename}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function DocumentRowSkeleton() {
  return (
    <div className="flex items-center gap-4 px-5 py-4 sm:px-6">
      <div className="skeleton h-9 w-9 rounded-lg" />
      <div className="flex-1 space-y-2">
        <div className="skeleton h-3.5 w-48 rounded" />
        <div className="skeleton h-3 w-24 rounded" />
      </div>
      <div className="skeleton h-5 w-20 rounded-full" />
    </div>
  );
}

export function DocumentsEmptyIcon() {
  return <UploadCloud size={26} strokeWidth={1.5} />;
}
