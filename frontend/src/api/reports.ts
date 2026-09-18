import axios, { type AxiosProgressEvent } from 'axios';

import { apiClient } from './client';
import type {
  AdminReportSummary,
  Report,
  ReportListParams,
  ReportListResponse,
} from '../types/report';

export async function uploadReport(
  file: File,
  onUploadProgress?: (percent: number) => void,
): Promise<Report> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await apiClient.post<Report>('/api/reports/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (!onUploadProgress || !event.total) return;
        onUploadProgress(Math.round((event.loaded / event.total) * 100));
      },
      timeout: 120_000,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data && typeof error.response.data === 'object') {
      const body = error.response.data as Partial<Report>;
      if (body.status === 'failed') {
        return body as Report;
      }
    }
    throw error;
  }
}

export async function getReport(id: string): Promise<Report> {
  const response = await apiClient.get<Report>(`/api/reports/${id}/`);
  return response.data;
}

export async function renameReport(id: string, filename: string): Promise<Report> {
  const response = await apiClient.patch<Report>(`/api/reports/${id}/`, { original_filename: filename });
  return response.data;
}

export async function deleteReport(id: string): Promise<void> {
  await apiClient.delete(`/api/reports/${id}/`);
}

export async function bulkDeleteReports(ids: string[]): Promise<{ deleted: string[] }> {
  const response = await apiClient.post<{ deleted: string[] }>('/api/reports/bulk-delete/', { ids });
  return response.data;
}

export async function listReports(params: ReportListParams = {}): Promise<ReportListResponse> {
  const response = await apiClient.get<ReportListResponse>('/api/reports/', { params });
  return response.data;
}

export async function listAllReportsAdmin(
  params: ReportListParams & { owner?: string } = {},
): Promise<ReportListResponse<AdminReportSummary>> {
  const response = await apiClient.get<ReportListResponse<AdminReportSummary>>('/api/reports/admin/', { params });
  return response.data;
}

export function getDownloadUrl(id: string): string {
  return `${apiClient.defaults.baseURL}/api/reports/${id}/download/`;
}

export function getJsonDownloadUrl(id: string): string {
  return `${apiClient.defaults.baseURL}/api/reports/${id}/download/json/`;
}
