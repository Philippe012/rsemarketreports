import { Landmark } from 'lucide-react';

import type { ExchangeRate } from '../../types/report';
import { formatNumber } from '../../utils/formatters';
import { Card } from '../common/Card';
import { EmptyState } from '../common/EmptyState';
import { TD, TH, TableShell } from './TableShell';

export function ExchangeRateTable({ rates }: { rates: ExchangeRate[] }) {
  return (
    <Card title="Exchange rates" subtitle="Against the Rwandan Franc (FRW)" icon={<Landmark size={17} />}>
      {rates.length === 0 ? (
        <EmptyState message="No exchange rate data was found in this report." />
      ) : (
        <TableShell>
          <thead>
            <tr>
              <TH>Currency</TH>
              <TH align="right">Buying</TH>
              <TH align="right">Selling</TH>
              <TH align="right">Average</TH>
            </tr>
          </thead>
          <tbody>
            {rates.map((rate) => (
              <tr key={rate.currency} className="table-row-hover">
                <TD className="font-semibold" style={{ color: 'var(--text)' }}>{rate.currency}</TD>
                <TD align="right">{formatNumber(rate.buying, 2)}</TD>
                <TD align="right">{formatNumber(rate.selling, 2)}</TD>
                <TD align="right" className="font-medium tabular-nums">{formatNumber(rate.average, 2)}</TD>
              </tr>
            ))}
          </tbody>
        </TableShell>
      )}
    </Card>
  );
}
