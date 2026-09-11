import type { MarketOverview } from '../../types/report';
import { formatCompactCurrency, formatNumber, formatPlainPercent } from '../../utils/formatters';
import { KpiCard } from './KpiCard';

export function MarketOverviewSection({ overview }: { overview: MarketOverview }) {
  const cards = [
    { label: 'Equity turnover', value: formatCompactCurrency(overview.equity_turnover) },
    { label: 'Shares traded', value: formatNumber(overview.shares_traded) },
    { label: 'Equity deals', value: formatNumber(overview.equity_deals) },
    { label: 'Bond market turnover', value: formatCompactCurrency(overview.bond_turnover) },
    { label: 'Bond deals', value: formatNumber(overview.bond_deals) },
    { label: 'Market capitalization', value: formatCompactCurrency(overview.market_capitalization) },
  ];

  const hasRepoActivity = [overview.repo_deals, overview.repo_turnover, overview.repo_tenor, overview.repo_rate].some(
    (v) => v !== null,
  );

  return (
    <section>
      <div className="mb-3">
        <h2 className="text-base font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
          Market overview
        </h2>
        <p className="mt-0.5 text-sm" style={{ color: 'var(--text-secondary)' }}>
          Today&apos;s key market figures
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
        {cards.map((card) => (
          <KpiCard key={card.label} {...card} />
        ))}
      </div>
      {hasRepoActivity && (
        <p className="mt-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
          Repo market:{' '}
          <span style={{ color: 'var(--text)' }} className="tabular-nums">
            {formatNumber(overview.repo_deals)} deals
          </span>
          {' · '}
          <span style={{ color: 'var(--text)' }} className="tabular-nums">
            {formatCompactCurrency(overview.repo_turnover)} turnover
          </span>
          {overview.repo_tenor && (
            <>
              {' · '}
              <span style={{ color: 'var(--text)' }}>{overview.repo_tenor} tenor</span>
            </>
          )}
          {overview.repo_rate !== null && (
            <>
              {' · '}
              <span style={{ color: 'var(--text)' }} className="tabular-nums">
                {formatPlainPercent(overview.repo_rate)} avg. rate
              </span>
            </>
          )}
        </p>
      )}
    </section>
  );
}
