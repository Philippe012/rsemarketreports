import { Search } from 'lucide-react';

import { Card } from '../common/Card';
import { formatNumber } from '../../utils/formatters';
import type { InvestigateSummary } from '../../types/intelligence';

export function InvestigatePanel({ investigate }: { investigate: InvestigateSummary }) {
  return (
    <Card title="Investigate Document" subtitle="One-click analysis of key metrics, trends, and issues" icon={<Search size={16} />}>
      <p className="text-sm leading-relaxed" style={{ color: 'var(--text)' }}>{investigate.summary}</p>
      {investigate.key_metrics.length > 0 && (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {investigate.key_metrics.map((metric) => (
            <div key={`${metric.dataset}-${metric.label}`} className="rounded-md border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
              <p className="text-[11px] uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>{metric.label}</p>
              <p className="mt-1 text-sm font-semibold tabular-nums" style={{ color: 'var(--text)' }}>
                {typeof metric.value === 'number' ? formatNumber(metric.value, Number.isInteger(metric.value) ? 0 : 2) : String(metric.value)}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
