export interface User {
  id: number;
  email: string;
  date_joined: string;
  is_staff: boolean;
}

export interface SignupPayload {
  email: string;
  password: string;
  password_confirm: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export interface ResetPasswordConfirmPayload {
  uid: string;
  token: string;
  new_password: string;
  new_password_confirm: string;
}

export type AuthStatus = 'loading' | 'authenticated' | 'anonymous';
