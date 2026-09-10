import { Building2, ScrollText } from 'lucide-react';

import { BondsTable } from '../components/dashboard/BondsTable';
import { BondTradesTable } from '../components/dashboard/BondTradesTable';
import { DocumentHeader } from '../components/dashboard/DocumentHeader';
import { EquitiesTable } from '../components/dashboard/EquitiesTable';
import { ExchangeRateTable } from '../components/dashboard/ExchangeRateTable';
import { ExportButton } from '../components/dashboard/ExportButton';
import { IndicesSection } from '../components/dashboard/IndicesSection';
import { MarketAnalyticsSection } from '../components/dashboard/MarketAnalyticsSection';
import { MarketOverviewSection } from '../components/dashboard/MarketOverviewSection';
import { SessionActivityStrip } from '../components/dashboard/SessionActivityStrip';
import { TradingStatsSection } from '../components/dashboard/TradingStatsSection';
import { InsightsList } from '../components/common/InsightsList';
import type { RseReport } from '../types/report';
import { formatDate } from '../utils/formatters';

export function RseDashboard({ report }: { report: RseReport }) {
  const data = report.extracted_data;

  return (
    <div className="mx-auto max-w-[1400px] space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <DocumentHeader
        eyebrow="Market report"
        title={data.report_title || 'Rwanda Stock Exchange Market Report'}
        dateLabel={formatDate(data.report_date)}
        sourceType={report.source_type}
        secondaryLine={`Source file: ${report.original_filename}`}
        reportId={report.id}
        warnings={report.warnings}
      />

      <SessionActivityStrip trades={data.bond_trades} />

      <MarketOverviewSection overview={data.market_overview} />

      {data.insights.length > 0 && <InsightsList insights={data.insights} />}

      <div className="grid gap-6 xl:grid-cols-1">
        <IndicesSection indices={data.indices} />
        <TradingStatsSection stats={data.trading_stats} />
      </div>

      <MarketAnalyticsSection equities={data.equities} />

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
