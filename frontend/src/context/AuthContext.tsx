import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'

import * as authApi from '@/api/auth'
import type { LoginData, User } from '@/types/auth'

type AuthContextType = {
  user: User | null
  isLoading: boolean
  login: (data: LoginData) => Promise<User>
  logout: () => Promise<void>
  setUser: (user: User | null) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // On page load: if the refresh-token cookie is still valid, restore the session.
  useEffect(() => {
    let cancelled = false
    authApi
      .restoreSession()
      .then((ok) => (ok ? authApi.getCurrentUser() : null))
      .then((current) => {
        if (!cancelled) setUser(current)
      })
      .catch(() => {
        if (!cancelled) setUser(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (data: LoginData) => {
    await authApi.login(data)
    const current = await authApi.getCurrentUser()
    setUser(current)
    return current
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  )
}

// A context file exporting its hook next to the provider is intended.
// oxlint-disable-next-line react/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return context
}
