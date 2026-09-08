export type SourceType = 'pdf' | 'excel';

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
}

export interface Report {
  id: string;
  original_filename: string;
  source_type: SourceType;
  status: ReportStatus;
  report_date: string | null;
  extracted_data: ReportData | null;
  warnings: string[];
  error_message: string;
  download_url: string | null;
  created_at: string;
  processed_at: string | null;
}

export interface ApiErrorBody {
  detail?: string;
  [key: string]: unknown;
}
