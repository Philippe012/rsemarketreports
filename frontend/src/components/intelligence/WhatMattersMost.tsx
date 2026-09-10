import { Trophy } from 'lucide-react';

import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import type { RankedFinding } from '../../types/intelligence';
import { severityTone } from './severity';

const CATEGORY_LABEL: Record<RankedFinding['category'], string> = {
  data_quality: 'Data quality',
  anomaly: 'Anomaly',
  discovery: 'Discovery',
};

export function WhatMattersMost({ findings }: { findings: RankedFinding[] }) {
  return (
    <Card title="What Matters Most" subtitle="The top findings across data quality, anomalies, and discoveries" icon={<Trophy size={16} />}>
      {findings.length === 0 ? (
        <EmptyState message="No significant findings to rank yet." />
      ) : (
        <ol className="space-y-3">
          {findings.map((finding, i) => (
            <li key={i} className="flex items-start gap-3 rounded-md border px-3 py-2.5" style={{ borderColor: 'var(--border)' }}>
              <span className="mt-0.5 w-5 shrink-0 text-xs font-semibold tabular-nums" style={{ color: 'var(--text-muted)' }}>
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>{finding.text}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge>
                <span className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>
                  {CATEGORY_LABEL[finding.category]}
                </span>
              </div>
            </li>
          ))}
        </ol>
      )}
    </Card>
  );
}
