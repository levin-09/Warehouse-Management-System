import { createContext, useContext, useState, type ReactNode } from "react";
import { clearSession, getAuthUser, setSession } from "../api/client";
import type { AuthUser } from "../api/types";

interface AuthCtx {
  user: AuthUser | null;
  isSeller: boolean;
  login: (u: AuthUser) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({
  user: null, isSeller: false,
  login: () => {}, logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const u = getAuthUser();
    return u && u.access_token ? u : null;
  });

  const login = (u: AuthUser) => {
    setSession(u.access_token, u);
    setUser(u);
  };
  const logout = () => {
    clearSession();
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, isSeller: user?.role === "seller", login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
