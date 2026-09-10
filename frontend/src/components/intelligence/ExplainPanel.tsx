import { HelpCircle } from 'lucide-react';
import { useState } from 'react';

import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { Spinner } from '../common/Spinner';
import { explainChart, explainMetric } from '../../api/analysis';
import { getApiErrorMessage } from '../../api/client';
import type { DocumentChart, DocumentMetric } from '../../types/report';
import type { ExplainResult } from '../../types/intelligence';

type Item =
  | { kind: 'metric'; key: string; label: string; metric: DocumentMetric }
  | { kind: 'chart'; key: string; label: string; chart: DocumentChart };

function ExplainRow({ reportId, item }: { reportId: string; item: Item }) {
  const [result, setResult] = useState<ExplainResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  async function handleExplain() {
    setOpen(true);
    if (result) return;
    setLoading(true);
    setError(null);
    try {
      const data = item.kind === 'metric'
        ? await explainMetric(reportId, item.metric.dataset, item.metric.column, item.metric.kind)
        : await explainChart(reportId, item.chart as unknown as Record<string, unknown>);
      setResult(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <li className="rounded-md border px-3 py-2.5" style={{ borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm" style={{ color: 'var(--text)' }}>{item.label}</span>
        <button
          type="button"
          onClick={handleExplain}
          className="shrink-0 rounded-full border px-3 py-1 text-xs font-medium transition hover:opacity-80"
          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
        >
          Explain
        </button>
      </div>
      {open && (
        <div className="mt-2 border-t pt-2 text-xs" style={{ borderColor: 'var(--border)' }}>
          {loading && <Spinner size={14} />}
          {error && <p style={{ color: 'var(--negative)' }}>{error}</p>}
          {result && (
            <div className="space-y-1.5">
              <p style={{ color: 'var(--text)' }}>{result.explanation}</p>
              <p className="font-mono" style={{ color: 'var(--text-muted)' }}>{result.calculation}</p>
              {result.source_rows.length > 0 && (
                <p style={{ color: 'var(--text-muted)' }}>
                  Based on {result.source_rows.length} source row(s) from the extracted data.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </li>
  );
}

export function ExplainPanel({
  reportId,
  metrics,
  charts,
}: {
  reportId: string;
  metrics: DocumentMetric[];
  charts: DocumentChart[];
}) {
  const items: Item[] = [
    ...metrics.map((metric) => ({
      kind: 'metric' as const, key: `m-${metric.dataset}-${metric.label}`, label: metric.label, metric,
    })),
    ...charts.map((chart) => ({
      kind: 'chart' as const, key: `c-${chart.dataset}-${chart.title}`, label: chart.title, chart,
    })),
  ];

  return (
    <Card title="Explain This" subtitle="How each metric and chart was calculated, and which rows back it" icon={<HelpCircle size={16} />}>
      {items.length === 0 ? (
        <EmptyState message="No metrics or charts to explain yet." />
      ) : (
        <ul className="space-y-2">
          {items.map((item) => <ExplainRow key={item.key} reportId={reportId} item={item} />)}
        </ul>
      )}
    </Card>
  );
}
