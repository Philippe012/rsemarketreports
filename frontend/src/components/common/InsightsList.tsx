import { TrendingUp } from 'lucide-react';

import { Card } from '../common/Card';

export function InsightsList({ insights }: { insights: string[] }) {
  if (insights.length === 0) return null;

  return (
    <Card title="Insights" subtitle="Observations computed from the extracted data" icon={<TrendingUp size={16} />}>
      <ul className="space-y-3">
        {insights.map((insight, i) => (
          <li key={i} className="flex gap-2.5 text-sm leading-relaxed" style={{ color: 'var(--text)' }}>
            <span
              className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full"
              style={{ background: 'var(--brand)' }}
              aria-hidden="true"
            />
            {insight}
          </li>
        ))}
      </ul>
    </Card>
  );
}
