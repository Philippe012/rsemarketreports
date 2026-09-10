import { LayoutDashboard } from 'lucide-react';
import { useState } from 'react';

import { Card } from '../common/Card';
import { Spinner } from '../common/Spinner';
import { DatasetChart } from '../generic/DatasetChart';
import { buildDashboard } from '../../api/analysis';
import { getApiErrorMessage } from '../../api/client';
import type { Dataset } from '../../types/report';
import type { DashboardBuilderResult } from '../../types/intelligence';

export function AIDashboardBuilder({ reportId, datasets }: { reportId: string; datasets?: Dataset[] }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<DashboardBuilderResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await buildDashboard(reportId, query));
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const matchedDataset = result?.dataset ? datasets?.find((d) => d.name === result.dataset) : undefined;

  return (
    <Card title="AI Dashboard Builder" subtitle="Describe what you want to see — matched against this document's own data" icon={<LayoutDashboard size={16} />}>
      <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
        <input
          className="min-w-0 flex-1 rounded-md border px-3 py-2 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          placeholder='e.g. "show revenue by region" or "closing price over time"'
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-md px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:opacity-50"
          style={{ background: 'var(--brand)' }}
        >
          {loading ? <Spinner size={14} /> : 'Build'}
        </button>
      </form>

      {error && <p className="mt-3 text-xs" style={{ color: 'var(--negative)' }}>{error}</p>}

      {result && (
        <div className="mt-4">
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{result.reason}</p>
          {result.chart && matchedDataset && (
            <div className="mt-3">
              <DatasetChart chart={result.chart} dataset={matchedDataset} />
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
