import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

import * as authApi from '../api/auth';
import { AuthContext } from './auth-context';
import type { AuthStatus, LoginPayload, SignupPayload, User } from '../types/auth';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      // The CSRF cookie must exist before any POST (login/signup/etc.) can
      // succeed, so this is primed once here, ahead of restoring the session.
      await authApi.primeCsrf().catch(() => {});
      const me = await authApi.getMe();
      if (cancelled) return;
      setUser(me);
      setStatus(me ? 'authenticated' : 'anonymous');
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    const loggedInUser = await authApi.login(payload);
    setUser(loggedInUser);
    setStatus('authenticated');
  }, []);

  const signup = useCallback(async (payload: SignupPayload) => {
    const newUser = await authApi.signup(payload);
    setUser(newUser);
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
    setStatus('anonymous');
  }, []);

  const value = useMemo(() => ({ user, status, login, signup, logout }), [user, status, login, signup, logout]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
