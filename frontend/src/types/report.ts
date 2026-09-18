export type SourceType = 'pdf' | 'excel' | 'csv' | 'docx' | 'txt' | 'json';

export type ReportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface MarketOverview {
  equity_turnover: number | null;
  equity_deals: number | null;
  shares_traded: number | null;
  bond_turnover: number | null;
  bond_deals: number | null;
  market_capitalization: number | null;
  repo_deals: number | null;
  repo_turnover: number | null;
  repo_tenor: string | null;
  repo_rate: number | null;
}

export interface MarketIndex {
  name: string;
  previous: number | null;
  today: number | null;
  closing: number | null;
  points_change: number | null;
  percent_change: number | null;
}

export interface TradingStat {
  label: string;
  previous: number | null;
  today: number | null;
  change: number | null;
  percent_change: number | null;
}

export interface Equity {
  isin: string | null;
  ticker: string;
  high_12m: number | null;
  low_12m: number | null;
  high_today: number | null;
  low_today: number | null;
  closing: number | null;
  previous: number | null;
  change: number | null;
  volume: number | null;
  value: number | null;
}

export interface Bond {
  isin: string | null;
  status: string | null;
  security: string;
  label: string;
  maturity_date: string | null;
  coupon_rate: number | null;
  closing_price: number | null;
  previous_price: number | null;
  bids: number | null;
  offers: number | null;
  bond_traded: number | null;
  category: string;
  issue_date: string | null;
  yield_tm: number | null;
  t_bond_no: string | null;
}

export interface BondTrade {
  bond: string;
  category: string | null;
  volume: number | null;
  previous: number | null;
  closing: number | null;
  change: number | null;
}

export interface ExchangeRate {
  currency: string;
  buying: number | null;
  selling: number | null;
  average: number | null;
}

export interface ReportData {
  kind: 'rse_market_report';
  report_title: string | null;
  report_date: string | null;
  source_type: SourceType;
  market_overview: MarketOverview;
  indices: MarketIndex[];
  trading_stats: TradingStat[];
  equities: Equity[];
  government_bonds: Bond[];
  corporate_bonds: Bond[];
  bond_trades: BondTrade[];
  exchange_rates: ExchangeRate[];
  insights: string[];
}


export type SemanticType =
  | 'identifier' | 'category' | 'date' | 'datetime' | 'number'
  | 'currency' | 'percentage' | 'quantity' | 'text' | 'boolean';

export interface ColumnStats {
  min: number | null;
  max: number | null;
  mean: number | null;
  std: number | null;
  unique_count: number | null;
  missing_count: number;
}

export interface DatasetColumn {
  name: string;
  display_name: string;
  semantic_type: SemanticType;
  data_type: string;
  nullable: boolean;
  non_null_count: number;
  total_count: number;
  confidence: 'high' | 'medium' | 'low';
  sample_values: unknown[];
  stats: ColumnStats | null;
}

export interface Dataset {
  name: string;
  source: string;
  columns: DatasetColumn[];
  rows: Record<string, unknown>[];
  row_count: number;
  duplicate_row_count: number;
}

export interface DocumentMetric {
  label: string;
  value: number | string;
  dataset: string;
  column: string;
  kind: 'sum' | 'average' | 'count';
  format_hint: 'number' | 'currency' | 'percentage' | 'quantity';
}

export interface DocumentChart {
  dataset: string;
  chart_type: 'line' | 'bar' | 'pie';
  x: string;
  y: string;
  title: string;
}

export interface DocumentSection {
  title: string | null;
  content: string;
}

export interface DocumentFigure {
  source: string;
  width: number | null;
  height: number | null;
  format: string;
  thumbnail: string | null;
}

export interface DocumentEntities {
  numbers: string[];
  dates: string[];
  keywords: string[];
}

export interface GenericDocument {
  kind: 'generic_document';
  filename: string;
  source_type: SourceType;
  document_type: string;
  document_type_confidence: 'high' | 'medium' | 'low';
  sections: DocumentSection[];
  datasets: Dataset[];
  metrics: DocumentMetric[];
  charts: DocumentChart[];
  figures: DocumentFigure[];
  insights: string[];
  entities: DocumentEntities;
}

export type ExtractedData = ReportData | GenericDocument;

export interface Report {
  id: string;
  original_filename: string;
  source_type: SourceType;
  status: ReportStatus;
  report_date: string | null;
  extracted_data: ExtractedData | null;
  warnings: string[];
  error_message: string;
  download_url: string | null;
  created_at: string;
  processed_at: string | null;
}

export type RseReport = Report & { extracted_data: ReportData };
export type GenericReport = Report & { extracted_data: GenericDocument };

export interface ApiErrorBody {
  detail?: string;
  [key: string]: unknown;
}

export interface ReportSummary {
  id: string;
  original_filename: string;
  source_type: SourceType;
  status: ReportStatus;
  report_date: string | null;
  created_at: string;
  document_type: string;
  headline_metric_label: string;
  headline_metric_value: number | null;
}

export interface AdminReportSummary extends ReportSummary {
  owner_email: string | null;
}

export interface ReportFacets {
  years: number[];
  source_types: SourceType[];
  document_types: string[];
}

export interface ReportListParams {
  search?: string;
  source_type?: SourceType | '';
  status?: ReportStatus | '';
  year?: string;
  document_type?: string;
  owner?: string;
  sort?: 'created_at' | '-created_at' | 'report_date' | '-report_date' | 'filename' | '-filename' | 'value' | '-value';
  page?: number;
  page_size?: number;
}

export interface ReportListResponse<T = ReportSummary> {
  results: T[];
  count: number;
  page: number;
  page_size: number;
  total_pages: number;
  facets: ReportFacets;
}
