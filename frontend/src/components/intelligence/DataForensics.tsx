import { FlaskConical } from 'lucide-react';

import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import type { ForensicsReport } from '../../types/intelligence';
import { severityTone } from './severity';

function scoreTone(score: number): 'positive' | 'warning' | 'negative' {
  if (score >= 90) return 'positive';
  if (score >= 70) return 'warning';
  return 'negative';
}

export function DataForensics({ forensics }: { forensics: ForensicsReport }) {
  return (
    <Card title="Data Forensics" subtitle="Missing values, duplicates, invalid dates, unit consistency" icon={<FlaskConical size={16} />}>
      <div className="mb-4 flex items-center gap-4 rounded-md border px-4 py-3" style={{ borderColor: 'var(--border)' }}>
        <div
          className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full text-lg font-semibold tabular-nums"
          style={{
            background: scoreTone(forensics.quality_score) === 'positive' ? 'var(--positive-soft)'
              : scoreTone(forensics.quality_score) === 'warning' ? 'var(--warning-soft)' : 'var(--negative-soft)',
            color: scoreTone(forensics.quality_score) === 'positive' ? 'var(--positive)'
              : scoreTone(forensics.quality_score) === 'warning' ? 'var(--warning)' : 'var(--negative)',
          }}
        >
          {forensics.quality_score}
        </div>
        <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Data quality score</p>
          <p className="mt-0.5">
            {forensics.total_rows} record(s) · {forensics.missing_cells} missing value(s) ·{' '}
            {forensics.duplicate_rows} duplicate row(s) · {forensics.invalid_dates} invalid date(s)
          </p>
        </div>
      </div>

      {forensics.issues.length === 0 ? (
        <EmptyState message="No data-quality issues were found." />
      ) : (
        <ul className="space-y-2.5">
          {forensics.issues.map((issue, i) => (
            <li key={i} className="flex items-start gap-3 rounded-md border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
              <Badge tone={severityTone(issue.severity)}>{issue.severity}</Badge>
              <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>{issue.message}</p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
