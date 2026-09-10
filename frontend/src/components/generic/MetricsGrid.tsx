import type { DocumentMetric } from '../../types/report';
import { formatNumber } from '../../utils/formatters';
import { KpiCard } from '../dashboard/KpiCard';
import { EmptyState } from '../common/EmptyState';

function formatMetricValue(metric: DocumentMetric): string {
  const value = typeof metric.value === 'number' ? metric.value : Number(metric.value);
  if (!Number.isFinite(value)) return String(metric.value);
  if (metric.format_hint === 'percentage') return `${formatNumber(value, 2)}%`;
  return formatNumber(value, Number.isInteger(value) ? 0 : 2);
}

export function MetricsGrid({ metrics }: { metrics: DocumentMetric[] }) {
  if (metrics.length === 0) {
    return <EmptyState message="There isn't enough numeric data in this document to compute headline metrics." />;
  }
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      {metrics.map((metric) => (
        <KpiCard
          key={`${metric.dataset}-${metric.label}`}
          label={metric.label}
          value={formatMetricValue(metric)}
          sublabel={metric.dataset}
        />
      ))}
    </div>
  );
}
