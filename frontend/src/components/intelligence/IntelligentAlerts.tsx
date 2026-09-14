import { Bell, Trash2 } from 'lucide-react';
import { useState } from 'react';

import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { EmptyState } from '../common/EmptyState';
import { createAlert, deleteAlert } from '../../api/analysis';
import { getApiErrorMessage } from '../../api/client';
import { formatNumber } from '../../utils/formatters';
import type { AlertStatus } from '../../types/intelligence';

const OPERATOR_LABEL: Record<AlertStatus['operator'], string> = {
  gt: 'is greater than',
  gte: 'is at least',
  lt: 'is less than',
  lte: 'is at most',
};

export function IntelligentAlerts({
  reportId,
  alerts,
  onChange,
}: {
  reportId: string;
  alerts: AlertStatus[];
  onChange: () => void;
}) {
  const [label, setLabel] = useState('');
  const [dataset, setDataset] = useState('');
  const [column, setColumn] = useState('');
  const [operator, setOperator] = useState<AlertStatus['operator']>('gt');
  const [threshold, setThreshold] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const numericThreshold = Number(threshold);
    if (!label.trim() || !dataset.trim() || !column.trim() || Number.isNaN(numericThreshold)) {
      setError('Fill in a label, dataset, column, and a numeric threshold.');
      return;
    }
    setSubmitting(true);
    try {
      await createAlert(reportId, { metric_label: label, dataset, column, operator, threshold: numericThreshold });
      setLabel(''); setDataset(''); setColumn(''); setThreshold('');
      onChange();
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number | null) {
    if (id === null) return;
    await deleteAlert(reportId, id);
    onChange();
  }

  return (
    <Card title="Intelligent Alerts" subtitle="Threshold rules evaluated live against this document's totals" icon={<Bell size={16} />}>
      {alerts.length === 0 ? (
        <EmptyState message="No alerts set up yet, add one below." />
      ) : (
        <ul className="mb-4 space-y-2">
          {alerts.map((alert) => (
            <li
              key={alert.id ?? `${alert.dataset}-${alert.column}`}
              className="flex items-center justify-between gap-3 rounded-md border px-3 py-2.5"
              style={{ borderColor: 'var(--border)' }}
            >
              <div className="min-w-0 text-sm" style={{ color: 'var(--text)' }}>
                <p className="font-medium">{alert.metric_label}</p>
                <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                  {alert.dataset} · {alert.column} {OPERATOR_LABEL[alert.operator]} {formatNumber(alert.threshold, 2)}
                  {alert.current_value !== null && ` (currently ${formatNumber(alert.current_value, 2)})`}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Badge tone={alert.triggered ? 'negative' : 'positive'}>{alert.triggered ? 'Triggered' : 'OK'}</Badge>
                <button
                  type="button"
                  onClick={() => handleDelete(alert.id)}
                  className="text-xs"
                  style={{ color: 'var(--text-muted)' }}
                  aria-label="Delete alert"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        <input
          className="rounded-md border px-2.5 py-1.5 text-sm sm:col-span-1"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          placeholder="Label" value={label} onChange={(e) => setLabel(e.target.value)}
        />
        <input
          className="rounded-md border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          placeholder="Dataset name" value={dataset} onChange={(e) => setDataset(e.target.value)}
        />
        <input
          className="rounded-md border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          placeholder="Column name" value={column} onChange={(e) => setColumn(e.target.value)}
        />
        <select
          className="rounded-md border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          value={operator} onChange={(e) => setOperator(e.target.value as AlertStatus['operator'])}
        >
          <option value="gt">greater than</option>
          <option value="gte">at least</option>
          <option value="lt">less than</option>
          <option value="lte">at most</option>
        </select>
        <div className="flex gap-2">
          <input
            className="w-full min-w-0 rounded-md border px-2.5 py-1.5 text-sm"
            style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            placeholder="Threshold" value={threshold} onChange={(e) => setThreshold(e.target.value)}
          />
          <button
            type="submit"
            disabled={submitting}
            className="shrink-0 rounded-md px-3 py-1.5 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
            style={{ background: 'var(--brand)' }}
          >
            Add
          </button>
        </div>
      </form>
      {error && <p className="mt-2 text-sm" style={{ color: 'var(--negative)' }}>{error}</p>}
      <p className="mt-2 text-sm" style={{ color: 'var(--text-muted)' }}>
        Dataset/column names must match one shown in the datasets above (e.g. "Equities" / "closing", or a generic dataset's column name). The threshold compares against the column's total.
      </p>
    </Card>
  );
}
