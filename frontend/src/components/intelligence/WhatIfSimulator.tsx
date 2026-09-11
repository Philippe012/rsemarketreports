import { SlidersHorizontal } from 'lucide-react';
import { useState } from 'react';

import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { formatNumber } from '../../utils/formatters';
import type { DocumentMetric } from '../../types/report';
export function WhatIfSimulator({ metrics }: { metrics: DocumentMetric[] }) {
  const numericMetrics = metrics.filter((m) => typeof m.value === 'number');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [percentChange, setPercentChange] = useState(0);

  if (numericMetrics.length === 0) {
    return (
      <Card title="What-If Simulator" subtitle="Scenario analysis on top of actual figures" icon={<SlidersHorizontal size={16} />}>
        <EmptyState message="No numeric metrics are available in this document to simulate against." />
      </Card>
    );
  }

  const metric = numericMetrics[selectedIndex];
  const actual = metric.value as number;
  const projection = actual * (1 + percentChange / 100);

  return (
    <Card title="What-If Simulator" subtitle="Scenario analysis, clearly separated from actual data" icon={<SlidersHorizontal size={16} />}>
      <div className="flex flex-wrap items-center gap-3">
        <select
          className="rounded-md border px-2.5 py-1.5 text-sm"
          style={{ borderColor: 'var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
          value={selectedIndex}
          onChange={(e) => setSelectedIndex(Number(e.target.value))}
        >
          {numericMetrics.map((m, i) => (
            <option key={`${m.dataset}-${m.label}`} value={i}>{m.label}</option>
          ))}
        </select>
        <input
          type="range" min={-50} max={50} value={percentChange}
          onChange={(e) => setPercentChange(Number(e.target.value))}
          className="w-40"
        />
        <span className="text-sm tabular-nums" style={{ color: 'var(--text)' }}>{percentChange > 0 ? '+' : ''}{percentChange}%</span>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
        <div className="rounded-md border px-3 py-3" style={{ borderColor: 'var(--border)' }}>
          <p className="text-sm uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Actual</p>
          <p className="mt-1 text-lg font-semibold tabular-nums" style={{ color: 'var(--text)' }}>{formatNumber(actual, 2)}</p>
        </div>
        <div className="rounded-md border px-3 py-3" style={{ borderColor: 'var(--border)' }}>
          <p className="text-sm uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Assumption</p>
          <p className="mt-1 text-lg font-semibold tabular-nums" style={{ color: 'var(--warning)' }}>{percentChange > 0 ? '+' : ''}{percentChange}%</p>
        </div>
        <div className="rounded-md border px-3 py-3" style={{ borderColor: 'var(--brand)' }}>
          <p className="text-sm uppercase tracking-wide" style={{ color: 'var(--text-muted)' }}>Projection</p>
          <p className="mt-1 text-lg font-semibold tabular-nums" style={{ color: 'var(--brand)' }}>{formatNumber(projection, 2)}</p>
        </div>
      </div>
      <p className="mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>
        The projection is a client-side calculation (actual × (1 + assumption)) and is never written back as extracted data.
      </p>
    </Card>
  );
}
