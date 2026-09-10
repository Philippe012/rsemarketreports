import type { GenericReport, Report, RseReport } from '../types/report';
import { GenericDashboard } from './GenericDashboard';
import { RseDashboard } from './RseDashboard';

export function Dashboard({ report }: { report: Report }) {
  const data = report.extracted_data;
  if (!data) return null;

  if (data.kind === 'rse_market_report') {
    return <RseDashboard report={report as RseReport} />;
  }
  return <GenericDashboard report={report as GenericReport} />;
}
