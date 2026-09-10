import { ArrowLeft } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

import { ExportButton } from './ExportButton';
import { WarningsPanel } from './WarningsPanel';
import type { SourceType } from '../../types/report';

/** The single header used by both the RSE and generic-document dashboards.
 * Shows each fact about the current document exactly once: an optional
 * eyebrow/category, the title, one metadata line (date · source · status),
 * the download action, and an optional subtle secondary line (e.g. the
 * original filename or a one-line dataset summary) — never repeated across
 * a breadcrumb, heading and metadata block the way the old per-dashboard
 * headers did. */
export function DocumentHeader({
  eyebrow,
  title,
  dateLabel,
  sourceType,
  secondaryLine,
  reportId,
  warnings,
}: {
  eyebrow?: string;
  title: string;
  dateLabel?: string | null;
  sourceType: SourceType;
  secondaryLine?: ReactNode;
  reportId: string;
  warnings: string[];
}) {
  return (
    <div className="animate-fade-in space-y-4">
      <Link
        to="/app/documents"
        className="inline-flex items-center gap-1.5 text-xs font-medium transition hover:underline"
        style={{ color: 'var(--text-secondary)' }}
      >
        <ArrowLeft size={12} />
        Documents
      </Link>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {eyebrow && (
            <p className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
              {eyebrow}
            </p>
          )}
          <h1 className="mt-1 truncate text-2xl font-semibold tracking-tight sm:text-[28px]" style={{ color: 'var(--text)' }} title={title}>
            {title}
          </h1>
          <p className="mt-1.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
            {dateLabel && (
              <>
                {dateLabel}
                <span style={{ color: 'var(--text-muted)' }}> · </span>
              </>
            )}
            {sourceType.toUpperCase()}
            <span style={{ color: 'var(--text-muted)' }}> · </span>
            <span style={{ color: 'var(--positive)' }} className="font-medium">Processed</span>
          </p>
          {secondaryLine && (
            <p className="mt-1 truncate text-xs" style={{ color: 'var(--text-muted)' }}>{secondaryLine}</p>
          )}
        </div>

        <ExportButton reportId={reportId} />
      </div>

      <WarningsPanel warnings={warnings} />
    </div>
  );
}
