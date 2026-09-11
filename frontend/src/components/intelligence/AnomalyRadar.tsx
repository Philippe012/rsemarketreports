import { Radar } from 'lucide-react';

import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import type { AnomalyRecord } from '../../types/intelligence';
import { severityTone } from './severity';

export function AnomalyRadar({ anomalies }: { anomalies: AnomalyRecord[] }) {
  return (
    <Card
      title="Anomaly Radar"
      subtitle="Statistical outliers, sudden changes, and mismatched totals"
      icon={<Radar size={16} />}
    >
      {anomalies.length === 0 ? (
        <EmptyState message="No statistical anomalies were detected in this document's numeric data." />
      ) : (
        <ul className="space-y-3">
          {anomalies.map((anomaly, i) => (
            <li key={i} className="flex items-start gap-3 rounded-md border px-3 py-2.5" style={{ borderColor: 'var(--border)' }}>
              <Badge tone={severityTone(anomaly.severity)}>{anomaly.severity}</Badge>
              <div className="min-w-0">
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>{anomaly.message}</p>
                <p className="mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                  {anomaly.dataset} · {anomaly.column} · {anomaly.type.replace(/_/g, ' ')}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
