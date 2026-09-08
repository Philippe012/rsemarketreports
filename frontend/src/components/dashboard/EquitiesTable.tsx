import { LineChart } from 'lucide-react';
import { useMemo, useState } from 'react';

import type { Equity } from '../../types/report';
import { formatNumber, formatSignedNumber } from '../../utils/formatters';
import { ChangeBadge } from '../common/Badge';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { SearchInput } from '../common/SearchInput';
import { TH, TD, TableShell } from './TableShell';

export function EquitiesTable({ equities }: { equities: Equity[] }) {
  const [query, setQuery] = useState('');

  const hasFullData = equities.some((e) => e.isin);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return equities;
    return equities.filter((e) => e.ticker.toLowerCase().includes(q) || e.isin?.toLowerCase().includes(q));
  }, [equities, query]);

  return (
    <Card
      title="Equities"
      subtitle={`${equities.length} listed securities`}
      icon={<LineChart size={17} />}
      actions={equities.length > 0 && <SearchInput value={query} onChange={setQuery} placeholder="Search ticker or ISIN…" />}
    >
      {equities.length === 0 ? (
        <EmptyState message="No equities data was found in this report." />
      ) : (
        <TableShell>
          <thead>
            <tr>
              <TH>Ticker</TH>
              {hasFullData && <TH>ISIN</TH>}
              {hasFullData && <TH align="right">12M High</TH>}
              {hasFullData && <TH align="right">12M Low</TH>}
              <TH align="right">Closing</TH>
              {hasFullData && <TH align="right">Previous</TH>}
              {hasFullData && <TH align="right">Change</TH>}
              <TH align="right">Volume</TH>
              <TH align="right">Value</TH>
            </tr>
          </thead>
          <tbody>
            {filtered.map((equity) => (
              <tr key={equity.ticker} className="table-row-hover">
                <TD className="font-semibold" style={{ color: 'var(--text)' }}>{equity.ticker}</TD>
                {hasFullData && <TD className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{equity.isin ?? '—'}</TD>}
                {hasFullData && <TD align="right">{formatNumber(equity.high_12m)}</TD>}
                {hasFullData && <TD align="right">{formatNumber(equity.low_12m)}</TD>}
                <TD align="right" className="font-medium tabular-nums">{formatNumber(equity.closing)}</TD>
                {hasFullData && <TD align="right">{formatNumber(equity.previous)}</TD>}
                {hasFullData && (
                  <TD align="right">
                    <ChangeBadge value={equity.change} formatted={formatSignedNumber(equity.change)} />
                  </TD>
                )}
                <TD align="right">{formatNumber(equity.volume)}</TD>
                <TD align="right">{formatNumber(equity.value)}</TD>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                  No equities match “{query}”.
                </td>
              </tr>
            )}
          </tbody>
        </TableShell>
      )}
    </Card>
  );
}
