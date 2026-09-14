import { History } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { Spinner } from '../common/Spinner';
import { compareReports } from '../../api/analysis';
import { listReports } from '../../api/reports';
import { getApiErrorMessage } from '../../api/client';
import { formatNumber, formatSignedNumber } from '../../utils/formatters';
import type { CompareResult } from '../../types/intelligence';
import type { ReportSummary } from '../../types/report';
import { Dropdown } from '../common/Dropdown';

export function TimeMachine({ reportId }: { reportId: string }) {
  const [candidates, setCandidates] = useState<ReportSummary[]>([]);
  const [selected, setSelected] = useState('');
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listReports({ page_size: 50 }).then((res) => {
      setCandidates(res.results.filter((r) => r.id !== reportId && r.status === 'completed'));
    }).catch(() => setCandidates([]));
  }, [reportId]);

  async function handleCompare() {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await compareReports(reportId, selected));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card title="Time Machine" subtitle="Compare this document against another of your reports" icon={<History size={16} />}>
      {candidates.length === 0 ? (
        <EmptyState message="Upload another completed report of the same kind to compare against." />
      ) : (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <Dropdown
            className="w-full sm:w-80"
            menuPlacement="up"
            label="Report"
            value={selected}
            onChange={setSelected}
            placeholder="Select a report..."
            options={[
              { value: '', label: 'Select a report...' },
              ...candidates.map((report) => ({
                value: report.id,
                label: report.original_filename,
              })),
            ]}
          />
          <button
            type="button"
            onClick={handleCompare}
            disabled={!selected || loading}
            className="inline-flex h-11 items-center justify-center rounded-xl px-5 text-sm font-semibold transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            style={{
              background: 'var(--brand)',
              color: 'var(--brand-contrast)',
            }}
          >
            {loading ? <Spinner size={14} /> : 'Compare'}
          </button>
        </div>
      )}

      {error && <p className="mt-3 text-sm" style={{ color: 'var(--negative)' }}>{error}</p>}

      {result && !result.comparable && (
        <p className="mt-4 text-sm" style={{ color: 'var(--text-secondary)' }}>{result.reason}</p>
      )}

      {result?.comparable && (
        <div className="mt-4 space-y-4">
          {(result.metric_diffs ?? []).length > 0 && (
            <ul className="space-y-2">
              {result.metric_diffs!.filter((m) => m.delta !== null).map((metric) => (
                <li key={metric.label} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm" style={{ borderColor: 'var(--border)' }}>
                  <span style={{ color: 'var(--text)' }}>{metric.label}</span>
                  <span className="tabular-nums" style={{ color: 'var(--text-secondary)' }}>
                    {formatNumber(Number(metric.before), 2)} → {formatNumber(Number(metric.after), 2)}
                    {' '}({formatSignedNumber(metric.percent_delta, 1)}%)
                  </span>
                </li>
              ))}
            </ul>
          )}
          {(result.dataset_diffs ?? []).length > 0 && (
            <ul className="space-y-2">
              {result.dataset_diffs!.map((diff) => (
                <li key={diff.dataset} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm" style={{ borderColor: 'var(--border)' }}>
                  <span style={{ color: 'var(--text)' }}>{diff.dataset}</span>
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {diff.status} · {diff.row_count_before} → {diff.row_count_after} row(s)
                    {diff.rows_added > 0 && ` · +${diff.rows_added} added`}
                    {diff.rows_removed > 0 && ` · -${diff.rows_removed} removed`}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Card>
  );
}
