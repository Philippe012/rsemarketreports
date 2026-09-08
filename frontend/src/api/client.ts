import axios from 'axios';

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://rsemarketreports.localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

/** Extracts a human-readable message from any API error, including network failures. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    if (detail) return detail;
    if (error.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
    if (!error.response) return 'Could not reach the server. Make sure the backend is running.';
    return `Request failed (${error.response.status}). Please try again.`;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
