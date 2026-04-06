"use client";

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { auth, setAccessToken, clearAccessToken, registerSessionExpiredHandler } from "./api";

interface AuthUser {
  id: string;
  username: string;
  email: string;
  is_admin: boolean;
  google_sub?: string;
}

interface GoogleLoginResult {
  needsLink: boolean;
  linkToken?: string;
  email?: string;
  googleName?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  googleLogin: (idToken: string) => Promise<GoogleLoginResult>;
  confirmGoogleLink: (linkToken: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Register the session-expired handler so api.ts can trigger a redirect
  useEffect(() => {
    registerSessionExpiredHandler(() => {
      setUser(null);
      router.push("/login");
    });
  }, [router]);

  const tryRefresh = useCallback(async () => {
    try {
      const { access_token } = await auth.refresh();
      setAccessToken(access_token);
      const me = await auth.me();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    tryRefresh();
  }, [tryRefresh]);

  const login = async (username: string, password: string) => {
    const { access_token } = await auth.login(username, password);
    setAccessToken(access_token);
    const me = await auth.me();
    setUser(me);
  };

  const logout = async () => {
    await auth.logout();
    clearAccessToken();
    setUser(null);
  };

  const googleLogin = async (idToken: string): Promise<GoogleLoginResult> => {
    const result = await auth.googleLogin(idToken);
    if (result.link_token) {
      // Existing password account found — needs linking confirmation
      return {
        needsLink: true,
        linkToken: result.link_token,
        email: result.email,
        googleName: result.google_name,
      };
    }
    // New or existing Google user — session established
    if (result.access_token) {
      setAccessToken(result.access_token);
      const me = await auth.me();
      setUser(me);
    }
    return { needsLink: false };
  };

  const confirmGoogleLink = async (linkToken: string): Promise<void> => {
    const { access_token } = await auth.confirmGoogleLink(linkToken);
    setAccessToken(access_token);
    const me = await auth.me();
    setUser(me);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, googleLogin, confirmGoogleLink }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
