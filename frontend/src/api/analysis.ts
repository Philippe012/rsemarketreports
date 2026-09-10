import { apiClient } from './client';
import type {
  AlertRule,
  AnalysisBundle,
  CompareResult,
  DashboardBuilderResult,
  ExplainResult,
} from '../types/intelligence';

export async function getAnalysis(reportId: string): Promise<AnalysisBundle> {
  const response = await apiClient.get<AnalysisBundle>(`/api/reports/${reportId}/analysis/`);
  return response.data;
}

export async function explainMetric(
  reportId: string,
  dataset: string,
  column: string,
  kind: string,
): Promise<ExplainResult> {
  const response = await apiClient.post<ExplainResult>(`/api/reports/${reportId}/explain/`, { dataset, column, kind });
  return response.data;
}

export async function explainChart(
  reportId: string,
  chart: Record<string, unknown>,
): Promise<ExplainResult> {
  const response = await apiClient.post<ExplainResult>(`/api/reports/${reportId}/explain/`, { chart });
  return response.data;
}

export async function buildDashboard(reportId: string, query: string): Promise<DashboardBuilderResult> {
  const response = await apiClient.post<DashboardBuilderResult>(`/api/reports/${reportId}/dashboard-builder/`, { query });
  return response.data;
}

export async function compareReports(reportId: string, otherId: string): Promise<CompareResult> {
  const response = await apiClient.get<CompareResult>(`/api/reports/${reportId}/compare/`, { params: { with: otherId } });
  return response.data;
}

export async function listAlerts(reportId: string): Promise<AlertRule[]> {
  const response = await apiClient.get<AlertRule[]>(`/api/reports/${reportId}/alerts/`);
  return response.data;
}

export async function createAlert(
  reportId: string,
  rule: { metric_label: string; dataset: string; column: string; operator: string; threshold: number },
): Promise<AlertRule> {
  const response = await apiClient.post<AlertRule>(`/api/reports/${reportId}/alerts/`, rule);
  return response.data;
}

export async function deleteAlert(reportId: string, alertId: number): Promise<void> {
  await apiClient.delete(`/api/reports/${reportId}/alerts/${alertId}/`);
}
