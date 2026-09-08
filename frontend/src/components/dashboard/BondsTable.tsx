import type { LucideIcon } from 'lucide-react';
import { useMemo, useState } from 'react';

import type { Bond } from '../../types/report';
import { formatDate, formatNumber, formatPlainPercent } from '../../utils/formatters';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { SearchInput } from '../common/SearchInput';
import { TD, TH, TableShell } from './TableShell';

export function BondsTable({ title, subtitle, icon, bonds }: { title: string; subtitle: string; icon: LucideIcon; bonds: Bond[] }) {
  const [query, setQuery] = useState('');
  const Icon = icon;

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return bonds;
    return bonds.filter((b) => b.security.toLowerCase().includes(q) || b.isin?.toLowerCase().includes(q));
  }, [bonds, query]);

  return (
    <Card
      title={title}
      subtitle={subtitle}
      icon={<Icon size={17} />}
      actions={bonds.length > 0 && <SearchInput value={query} onChange={setQuery} placeholder="Search security or ISIN…" />}
    >
      {bonds.length === 0 ? (
        <EmptyState message={`No ${title.toLowerCase()} were found in this report.`} />
      ) : (
        <TableShell>
          <thead>
            <tr>
              <TH>ISIN</TH>
              <TH>Security</TH>
              <TH>Maturity</TH>
              <TH align="right">Coupon</TH>
              <TH align="right">Closing</TH>
              <TH align="right">Previous</TH>
              <TH align="right">Bids</TH>
              <TH align="right">Offers</TH>
              <TH align="right">Traded</TH>
            </tr>
          </thead>
          <tbody>
            {filtered.map((bond, i) => (
              <tr key={`${bond.isin}-${i}`} className="table-row-hover">
                <TD className="font-mono text-xs" style={{ color: 'var(--text-muted)' }}>{bond.isin ?? '—'}</TD>
                <TD className="font-medium" style={{ color: 'var(--text)' }}>
                  {bond.security}
                  {bond.status && (
                    <span className="ml-1.5 font-normal" style={{ color: 'var(--text-muted)' }}>
                      ({bond.status})
                    </span>
                  )}
                </TD>
                <TD>{formatDate(bond.maturity_date)}</TD>
                <TD align="right">{formatPlainPercent(bond.coupon_rate, 3)}</TD>
                <TD align="right" className="font-medium tabular-nums">{formatNumber(bond.closing_price, 3)}</TD>
                <TD align="right">{formatNumber(bond.previous_price, 3)}</TD>
                <TD align="right">{formatNumber(bond.bids)}</TD>
                <TD align="right">{formatNumber(bond.offers)}</TD>
                <TD
                  align="right"
                  className="font-medium tabular-nums"
                  style={bond.bond_traded ? { color: 'var(--positive)' } : undefined}
                >
                  {formatNumber(bond.bond_traded)}
                </TD>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
                  No bonds match “{query}”.
                </td>
              </tr>
            )}
          </tbody>
        </TableShell>
      )}
    </Card>
  );
}
