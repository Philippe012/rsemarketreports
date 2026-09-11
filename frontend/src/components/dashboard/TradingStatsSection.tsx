import type { TradingStat } from '../../types/report';
import { formatNumber, formatPercent } from '../../utils/formatters';
import { Badge, ChangeBadge } from '../common/Badge';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';


function ChangeIndicator({ stat }: { stat: TradingStat }) {
  const noPriorBaseline = stat.previous === null || stat.previous === 0;
  if (noPriorBaseline) {
    const hasActivity = stat.today !== null && stat.today > 0;
    return <Badge tone="neutral">{hasActivity ? 'New activity' : 'No prior activity'}</Badge>;
  }
  if (stat.percent_change === null) return null;
  return <ChangeBadge value={stat.percent_change} formatted={formatPercent(stat.percent_change)} />;
}

export function TradingStatsSection({ stats }: { stats: TradingStat[] }) {
  return (
    <Card title="Trading statistics" subtitle="Session-over-session comparison">
      {stats.length === 0 ? (
        <EmptyState message="This report does not include a trading-statistics comparison table." />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-lg border p-4"
              style={{ borderColor: 'var(--border)', background: 'var(--bg-subtle)' }}
            >
              <p className="text-sm font-medium uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>
                {stat.label}
              </p>
              <p className="mt-2 text-xl font-semibold tabular-nums" style={{ color: 'var(--text)' }}>
                {formatNumber(stat.today)}
              </p>
              <div className="mt-2 flex items-center justify-between text-sm" style={{ color: 'var(--text-muted)' }}>
                <span>Previous: {formatNumber(stat.previous)}</span>
                <ChangeIndicator stat={stat} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
