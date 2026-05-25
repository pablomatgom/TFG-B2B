"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/lib/api";
import {
  clearToken, decodeToken, getToken, isTokenExpired, setToken,
} from "@/lib/auth";
import type { AuthUser } from "@/types/auth";

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>(null!);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Hydrate user from cookie on mount
  useEffect(() => {
    const token = getToken();
    if (token) {
      const payload = decodeToken(token);
      if (payload && !isTokenExpired(payload)) {
        setUser({
          email:      payload.sub,
          company_id: payload.company_id,
          role:       payload.role,
          full_name:  payload.full_name,
        });
      } else {
        clearToken();
      }
    }
    setLoading(false);
  }, []);

  async function login(email: string, password: string): Promise<void> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? "Credenciales incorrectas");
    }

    const { access_token } = await res.json();
    setToken(access_token);
    const payload = decodeToken(access_token)!;
    setUser({
      email:      payload.sub,
      company_id: payload.company_id,
      role:       payload.role,
      full_name:  payload.full_name,
    });
    router.push("/");
  }

  function logout(): void {
    clearToken();
    setUser(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  return useContext(AuthContext);
}