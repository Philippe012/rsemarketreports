import axios from 'axios';

export const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://rsemarketreports.localhost:8000';

const CSRF_COOKIE_NAME = 'csrftoken';
const CSRF_HEADER_NAME = 'X-CSRFToken';
const SAFE_METHODS = new Set(['get', 'head', 'options', 'trace']);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

// Django's CSRF protection requires the token cookie's value echoed back as
// a request header on any state-changing request. The cookie itself is set
// by GET /api/auth/csrf/ (primed once on app boot — see AuthContext).
apiClient.interceptors.request.use((config) => {
  const method = (config.method ?? 'get').toLowerCase();
  if (!SAFE_METHODS.has(method)) {
    const token = readCookie(CSRF_COOKIE_NAME);
    if (token) {
      config.headers.set(CSRF_HEADER_NAME, token);
    }
  }
  return config;
});

/** Extracts a human-readable message from any API error, including network failures. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as Record<string, unknown> | undefined;
    const detail = body?.detail;
    if (typeof detail === 'string') return detail;
    // DRF serializer validation errors come back as {field: [messages]} —
    // surface the first one rather than a generic "request failed".
    if (body && typeof body === 'object') {
      for (const value of Object.values(body)) {
        if (Array.isArray(value) && typeof value[0] === 'string') return value[0];
      }
    }
    if (error.code === 'ECONNABORTED') return 'The request timed out. Please try again.';
    if (!error.response) return 'Could not reach the server. Make sure the backend is running.';
    return `Request failed (${error.response.status}). Please try again.`;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
