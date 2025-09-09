'use client'

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiClient, type AuthTokens, type UserResponse } from '@/lib/api-client'

interface AuthContextValue {
  user: UserResponse | null
  tokens: AuthTokens | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [tokens, setTokens] = useState<AuthTokens | null>(apiClient.getTokens())

  useEffect(() => {
    if (tokens && !user) {
      apiClient
        .getCurrentUser()
        .then(setUser)
        .catch(() => {
          setTokens(null)
        })
    }
  }, [tokens, user])

  const login = async (username: string, password: string) => {
    const currentUser = await apiClient.login({ email: username, password })
    setUser(currentUser)
    setTokens(apiClient.getTokens())
  }

  const logout = async () => {
    await apiClient.logout()
    setUser(null)
    setTokens(null)
  }

  return <AuthContext.Provider value={{ user, tokens, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function useRequireAuth(): AuthContextValue {
  return useAuth()
}
