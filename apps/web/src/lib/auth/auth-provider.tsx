"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import {
  apiClient,
  type AuthTokens,
  type UserResponse,
} from "@/lib/api-client";

interface AuthContextValue {
  user: UserResponse | null;
  tokens: AuthTokens | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [tokens, setTokens] = useState<AuthTokens | null>(
    apiClient.getTokens(),
  );
  const [isLoading, setIsLoading] = useState<boolean>(!!tokens);

  useEffect(() => {
    if (tokens && !user) {
      setIsLoading(true);
      apiClient
        .getCurrentUser()
        .then(setUser)
        .catch((error) => {
          console.warn("Failed to get current user:", error);
          // Clear invalid tokens completely
          setTokens(null);
          // Use logout to properly clear all tokens and storage
          apiClient.logout();
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [tokens, user]);

  const login = async (username: string, password: string) => {
    try {
      const currentUser = await apiClient.login({ email: username, password });
      setUser(currentUser);
      setTokens(apiClient.getTokens());
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  };

  const logout = async () => {
    await apiClient.logout();
    setUser(null);
    setTokens(null);
  };

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider
      value={{ user, tokens, login, logout, isAuthenticated, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function useRequireAuth(): AuthContextValue {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      router.replace("/login");
    }
  }, [auth.isLoading, auth.isAuthenticated, router]);

  return auth;
}
