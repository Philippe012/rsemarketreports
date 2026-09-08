import { Repeat2 } from 'lucide-react';

import type { BondTrade } from '../../types/report';
import { formatNumber, formatSignedNumber } from '../../utils/formatters';
import { Badge, ChangeBadge } from '../common/Badge';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { TD, TH, TableShell } from './TableShell';

export function BondTradesTable({ trades }: { trades: BondTrade[] }) {
  return (
    <Card title="Bond trades" subtitle="Bonds that changed hands this session" icon={<Repeat2 size={17} />}>
      {trades.length === 0 ? (
        <EmptyState message="No bond trades were recorded in this report." />
      ) : (
        <TableShell>
          <thead>
            <tr>
              <TH>Bond</TH>
              <TH>Category</TH>
              <TH align="right">Volume</TH>
              <TH align="right">Previous</TH>
              <TH align="right">Closing</TH>
              <TH align="right">Change</TH>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, i) => (
              <tr key={`${trade.bond}-${i}`} className="table-row-hover">
                <TD className="font-medium" style={{ color: 'var(--text)' }}>{trade.bond}</TD>
                <TD>{trade.category && <Badge tone="neutral">{trade.category}</Badge>}</TD>
                <TD align="right" className="font-medium tabular-nums">{formatNumber(trade.volume)}</TD>
                <TD align="right">{formatNumber(trade.previous, 3)}</TD>
                <TD align="right">{formatNumber(trade.closing, 3)}</TD>
                <TD align="right">
                  <ChangeBadge value={trade.change} formatted={formatSignedNumber(trade.change, 3)} />
                </TD>
              </tr>
            ))}
          </tbody>
        </TableShell>
      )}
    </Card>
  );
}
