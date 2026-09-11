import { LineChart } from 'lucide-react';

import { Card } from '../common/Card';
import { TableShell, TD, TH } from '../dashboard/TableShell';
import { EmptyState } from '../common/EmptyState';
import { formatNumber, formatSignedNumber } from '../../utils/formatters';
import type { TradingAnalytics } from '../../types/intelligence';

function EquityRow({ label, value }: { label: string; value: number | null }) {
  return (
    <li className="flex items-center justify-between rounded-md border px-3 py-2" style={{ borderColor: 'var(--border)' }}>
      <span className="font-medium" style={{ color: 'var(--text)' }}>{label}</span>
      <span className="tabular-nums text-sm" style={{ color: 'var(--text-secondary)' }}>{formatNumber(value ?? undefined, 2)}</span>
    </li>
  );
}

export function TradingView({ trading }: { trading: TradingAnalytics }) {
  const hasEquities = trading.top_gainers.length > 0 || trading.top_losers.length > 0;

  return (
    <Card title="Trading / Market View" subtitle="Leaders, laggards, and rankings drawn from today's extracted market data" icon={<LineChart size={16} />}>
      {!hasEquities && trading.index_performance.length === 0 && trading.bond_yield_ranking.length === 0 ? (
        <EmptyState message="No equities, indices, or bonds were found to rank." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {trading.top_gainers.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Top Gainers</p>
              <ul className="space-y-2">
                {trading.top_gainers.slice(0, 5).map((eq) => (
                  <EquityRow key={eq.ticker} label={`${eq.ticker} · ${formatSignedNumber(eq.change, 2)}`} value={eq.closing} />
                ))}
              </ul>
            </div>
          )}
          {trading.top_losers.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Top Losers</p>
              <ul className="space-y-2">
                {trading.top_losers.slice(0, 5).map((eq) => (
                  <EquityRow key={eq.ticker} label={`${eq.ticker} · ${formatSignedNumber(eq.change, 2)}`} value={eq.closing} />
                ))}
              </ul>
            </div>
          )}
          {trading.volume_leaders.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Volume Leaders</p>
              <ul className="space-y-2">
                {trading.volume_leaders.slice(0, 5).map((eq) => (
                  <EquityRow key={eq.ticker} label={eq.ticker} value={eq.volume} />
                ))}
              </ul>
            </div>
          )}
          {trading.index_performance.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Index Performance</p>
              <ul className="space-y-2">
                {trading.index_performance.map((idx) => (
                  <EquityRow key={idx.name} label={`${idx.name} · ${formatSignedNumber(idx.percent_change, 2)}%`} value={idx.closing} />
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {trading.bond_yield_ranking.length > 0 && (
        <div className="mt-6">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wide" style={{ color: 'var(--text-secondary)' }}>Bond Yield Ranking</p>
          <TableShell>
            <thead>
              <tr>
                <TH>Security</TH>
                <TH align="right">Yield to maturity</TH>
                <TH align="right">Closing price</TH>
              </tr>
            </thead>
            <tbody>
              {trading.bond_yield_ranking.map((bond) => (
                <tr key={bond.isin ?? bond.security} className="table-row-hover">
                  <TD>{bond.security}</TD>
                  <TD align="right">{formatNumber(bond.yield_tm ?? undefined, 2)}%</TD>
                  <TD align="right">{formatNumber(bond.closing_price ?? undefined, 2)}</TD>
                </tr>
              ))}
            </tbody>
          </TableShell>
        </div>
      )}
    </Card>
  );
}
