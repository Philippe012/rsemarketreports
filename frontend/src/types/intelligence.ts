import type { Bond, DocumentChart, DocumentMetric, Equity, ExchangeRate, MarketIndex, MarketOverview } from './report';

export type Severity = 'high' | 'medium' | 'low';

export interface ForensicsIssue {
  type: 'missing_values' | 'duplicates' | 'invalid_dates' | 'inconsistent_units';
  severity: Severity;
  dataset: string;
  column: string | null;
  message: string;
}

export interface ForensicsReport {
  quality_score: number;
  total_rows: number;
  total_cells: number;
  missing_cells: number;
  duplicate_rows: number;
  invalid_dates: number;
  issues: ForensicsIssue[];
}

export interface AnomalyRecord {
  type: 'outlier' | 'sudden_change' | 'mismatched_total';
  severity: Severity;
  dataset: string;
  column: string;
  row_index: number | null;
  value: number;
  message: string;
}

export interface RankedFinding {
  category: 'data_quality' | 'anomaly' | 'discovery';
  severity: Severity;
  text: string;
  dataset: string | null;
  column: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'category' | 'measure';
  dataset: string;
  weight: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'co_occurs' | 'correlates';
  weight: number;
  correlation?: number;
  evidence_count?: number;
}

export interface RelationshipGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GeoPoint {
  label: string;
  lat: number;
  lon: number;
  dataset: string;
  value: number | null;
  count?: number;
}

export interface GeographicIntelligence {
  has_geo: boolean;
  points: GeoPoint[];
}

export interface VisionSummary {
  tables_detected: number;
  charts_suggested: number;
  figures_total: number;
  figures_chart_like: number;
  figures_photo_or_diagram: number;
  forms_detected: number;
}

export interface AlertStatus {
  id: number | null;
  metric_label: string;
  dataset: string;
  column: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte';
  threshold: number;
  current_value: number | null;
  triggered: boolean;
}

export interface AlertRule {
  id: number;
  metric_label: string;
  dataset: string;
  column: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte';
  threshold: number;
  created_at: string;
}

export interface TradingAnalytics {
  top_gainers: Equity[];
  top_losers: Equity[];
  volume_leaders: Equity[];
  value_leaders: Equity[];
  index_performance: MarketIndex[];
  bond_yield_ranking: Bond[];
  exchange_rates: ExchangeRate[];
  market_overview: MarketOverview;
}

export interface InvestigateSummary {
  summary: string;
  key_metrics: DocumentMetric[];
}

export interface AnalysisBundle {
  investigate: InvestigateSummary;
  forensics: ForensicsReport;
  anomalies: AnomalyRecord[];
  discoveries: string[];
  what_matters_most: RankedFinding[];
  relationships: RelationshipGraph;
  geography: GeographicIntelligence;
  vision: VisionSummary;
  alerts: AlertStatus[];
  trading: TradingAnalytics | null;
}

export interface ExplainResult {
  explanation: string;
  calculation: string;
  source_rows: Record<string, unknown>[];
}

export interface DashboardBuilderResult {
  dataset: string | null;
  chart: DocumentChart | null;
  reason: string;
}

export interface MetricDiff {
  label: string;
  before: number | string | null;
  after: number | string | null;
  delta: number | null;
  percent_delta: number | null;
}

export interface DatasetDiff {
  dataset: string;
  status: 'added' | 'removed' | 'changed' | 'unchanged';
  row_count_before: number;
  row_count_after: number;
  rows_added: number;
  rows_removed: number;
}

export interface CompareResult {
  comparable: boolean;
  reason?: string;
  metric_diffs?: MetricDiff[];
  dataset_diffs?: DatasetDiff[];
}
