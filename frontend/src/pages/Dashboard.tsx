import { Building2, ScrollText } from 'lucide-react';

import { BondsTable } from '../components/dashboard/BondsTable';
import { BondTradesTable } from '../components/dashboard/BondTradesTable';
import { EquitiesTable } from '../components/dashboard/EquitiesTable';
import { ExchangeRateTable } from '../components/dashboard/ExchangeRateTable';
import { ExportButton } from '../components/dashboard/ExportButton';
import { IndicesSection } from '../components/dashboard/IndicesSection';
import { MarketOverviewSection } from '../components/dashboard/MarketOverviewSection';
import { ReportHeader } from '../components/dashboard/ReportHeader';
import { SessionActivityStrip } from '../components/dashboard/SessionActivityStrip';
import { TradingStatsSection } from '../components/dashboard/TradingStatsSection';
import type { Report } from '../types/report';

export function Dashboard({ report, onBackToReports }: { report: Report; onBackToReports: () => void }) {
  const data = report.extracted_data;
  if (!data) return null;

  return (
    <div className="mx-auto max-w-[1400px] space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <ReportHeader report={report} onBackToReports={onBackToReports} />

      <SessionActivityStrip trades={data.bond_trades} />

      <MarketOverviewSection overview={data.market_overview} />

      <div className="grid gap-6 xl:grid-cols-1">
        <IndicesSection indices={data.indices} />
        <TradingStatsSection stats={data.trading_stats} />
      </div>

      <EquitiesTable equities={data.equities} />

      <div className="grid gap-6 2xl:grid-cols-2">
        <BondsTable
          title="Government bonds"
          subtitle="Treasury bonds listed on the RSE"
          icon={Building2}
          bonds={data.government_bonds}
        />
        <BondsTable
          title="Corporate bonds"
          subtitle="Corporate debt securities listed on the RSE"
          icon={ScrollText}
          bonds={data.corporate_bonds}
        />
      </div>

      <BondTradesTable trades={data.bond_trades} />

      <ExchangeRateTable rates={data.exchange_rates} />

      <div
        className="flex flex-col items-center gap-3 rounded-lg border px-6 py-8 text-center animate-fade-in sm:flex-row sm:justify-between sm:text-left"
        style={{ background: 'var(--brand-soft)', borderColor: 'var(--border)' }}
      >
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--text)' }}>
            Reviewed everything? Export the full report.
          </p>
          <p className="mt-0.5 text-xs" style={{ color: 'var(--text-secondary)' }}>
            Downloads a validated, organized Excel workbook with every section above.
          </p>
        </div>
        <ExportButton reportId={report.id} />
      </div>
    </div>
  );
}
