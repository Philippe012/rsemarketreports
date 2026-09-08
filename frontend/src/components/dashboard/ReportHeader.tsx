import { ChevronRight } from 'lucide-react';

import type { Report } from '../../types/report';
import { formatDate, formatDateWithWeekday } from '../../utils/formatters';
import { ExportButton } from './ExportButton';
import { WarningsPanel } from './WarningsPanel';

export function ReportHeader({ report, onBackToReports }: { report: Report; onBackToReports: () => void }) {
  const data = report.extracted_data;
  const dateLabel = formatDate(data?.report_date);
  const sourceLabel = report.source_type.toUpperCase();

  return (
    <div className="animate-fade-in space-y-4">
      <nav className="flex items-center gap-1.5 text-xs" style={{ color: 'var(--text-muted)' }} aria-label="Breadcrumb">
        <button type="button" onClick={onBackToReports} className="transition hover:underline" style={{ color: 'var(--text-secondary)' }}>
          Reports
        </button>
        <ChevronRight size={12} />
        <span>{dateLabel}</span>
      </nav>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
            Market report
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight tabular-nums sm:text-[28px]" style={{ color: 'var(--text)' }}>
            {dateLabel}
          </h1>
          <p className="mt-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
            {sourceLabel}
            <span style={{ color: 'var(--text-muted)' }}> · </span>
            <span style={{ color: 'var(--positive)' }} className="font-medium">Processed</span>
          </p>

          <div className="mt-4 border-t pt-3" style={{ borderColor: 'var(--border)' }}>
            <p className="text-sm" style={{ color: 'var(--text)' }}>
              {data?.report_title || 'Rwanda Stock Exchange Market Report'}
            </p>
            <p className="mt-0.5 text-xs" style={{ color: 'var(--text-muted)' }}>
              {formatDateWithWeekday(data?.report_date)} · Source file: {report.original_filename}
            </p>
          </div>
        </div>

        <ExportButton reportId={report.id} />
      </div>

      <WarningsPanel warnings={report.warnings} />
    </div>
  );
}
