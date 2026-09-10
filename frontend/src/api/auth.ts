import { apiClient } from './client';
import type {
  ChangePasswordPayload,
  LoginPayload,
  ResetPasswordConfirmPayload,
  SignupPayload,
  User,
} from '../types/auth';

export async function primeCsrf(): Promise<void> {
  await apiClient.get('/api/auth/csrf/');
}

export async function signup(payload: SignupPayload): Promise<User> {
  const response = await apiClient.post<User>('/api/auth/signup/', payload);
  return response.data;
}

export async function login(payload: LoginPayload): Promise<User> {
  const response = await apiClient.post<User>('/api/auth/login/', payload);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post('/api/auth/logout/');
}

export async function getMe(): Promise<User | null> {
  try {
    const response = await apiClient.get<User>('/api/auth/me/');
    return response.data;
  } catch {
    return null;
  }
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await apiClient.post('/api/auth/change-password/', payload);
}

export async function requestPasswordReset(email: string): Promise<void> {
  await apiClient.post('/api/auth/password-reset/', { email });
}

export async function confirmPasswordReset(payload: ResetPasswordConfirmPayload): Promise<void> {
  await apiClient.post('/api/auth/password-reset-confirm/', payload);
}
