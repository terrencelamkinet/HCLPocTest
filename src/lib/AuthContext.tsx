/**
 * Penguin CRM Auth Context
 * 
 * Provides login, logout, and user state across the app.
 * Token storage + refresh handled by api.ts.
 */

import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import {
  login as apiLogin,
  sendMfa,
  verifyMfa as apiVerifyMfa,
  storeAuth,
  clearAuth,
  getStoredAuth,
  isAuthenticated,
} from './api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AuthUser {
  email: string;
  displayName?: string;
  /** Google 頭像或自己上載嘅頭像 URL（相對路徑 → 同源）。 */
  avatarUrl?: string;
  locale?: string;
  timezone?: string;
}

export interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<'mfa' | 'success'>;
  verifyMfa: (otp: string) => Promise<void>;
  logout: () => void;
  sendMfaCode: () => Promise<void>;
  /** 重新由 /auth/me 拉最新 profile（改名／換頭像之後用）。 */
  refreshMe: () => Promise<void>;
  mfaEmail: string;
}

const AuthContext = createContext<AuthState | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [mfaEmail, setMfaEmail] = useState('');

  // Fetch real user profile (display_name) from backend — AuthContext only
  // stores email on login; /auth/me returns display_name + verified flags.
  const fetchMe = useCallback(async (): Promise<AuthUser | null> => {
    try {
      const auth = getStoredAuth();
      if (!auth?.access_token) return null;
      const res = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${auth.access_token}` },
      });
      if (!res.ok) return null;
      const me = await res.json();
      return {
        email: me.email,
        displayName: me.display_name || undefined,
        avatarUrl: me.avatar_url || undefined,
        locale: me.locale || undefined,
        timezone: me.timezone || undefined,
      };
    } catch {
      return null;
    }
  }, []);

  const applyMe = useCallback((me: AuthUser | null, fallbackEmail?: string) => {
    if (me) setUser(me);
    else if (fallbackEmail) setUser({ email: fallbackEmail });
  }, []);

  // 改名／換頭像之後由呼叫方主動 refresh（AuthContext 唔會輪詢）
  const refreshMe = useCallback(async () => {
    const me = await fetchMe();
    if (me) setUser(me);
  }, [fetchMe]);

  // Restore session from localStorage on mount — then refresh real identity
  useEffect(() => {
    const stored = getStoredAuth();
    if (stored && isAuthenticated()) {
      setUser({ email: stored.email });
      fetchMe().then((me) => applyMe(me, stored.email));
    }
    setLoading(false);
  }, [fetchMe, applyMe]);

  const login = useCallback(async (email: string, password: string): Promise<'mfa' | 'success'> => {
    const res = await apiLogin(email, password);

    if (res.mfa_required) {
      setMfaEmail(email);
      await sendMfa(email);
      return 'mfa';
    }

    // Trust device — store both access + refresh tokens
    storeAuth(res.access_token, email, res.refresh_token);
    setUser({ email });
    fetchMe().then((me) => applyMe(me, email));
    setMfaEmail('');
    return 'success';
  }, [fetchMe, applyMe]);

  const sendMfaCode = useCallback(async () => {
    if (mfaEmail) {
      await sendMfa(mfaEmail);
    }
  }, [mfaEmail]);

  const verifyMfa = useCallback(async (otp: string) => {
    if (!mfaEmail) throw new Error('No MFA session');
    const res = await apiVerifyMfa(mfaEmail, otp);
    storeAuth(res.access_token, mfaEmail, res.refresh_token);
    setUser({ email: mfaEmail });
    fetchMe().then((me) => applyMe(me, mfaEmail));
    setMfaEmail('');
  }, [mfaEmail, fetchMe, applyMe]);

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    setMfaEmail('');
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, verifyMfa, logout, sendMfaCode, refreshMe, mfaEmail }}>
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
