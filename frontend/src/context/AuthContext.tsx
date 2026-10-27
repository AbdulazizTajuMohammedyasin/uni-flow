import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode, type RefObject } from 'react'

import * as authApi from '@/api/auth'
import { registerDevice, unregisterDevice } from '@/api/notifications'
import { PUSH_TOKEN_EVENT, pushToken, tellApp, type PushTokenDetail } from '@/lib/app'
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

  const registered = useRef(new Set<string>()) // push addresses sent this page load
  usePhoneRegistration(user, isLoading, registered)

  const login = useCallback(async (data: LoginData) => {
    await authApi.login(data)
    const current = await authApi.getCurrentUser()
    setUser(current)
    return current
  }, [])

  const logout = useCallback(async () => {
    // Inside the phone app, the phone stops getting my alerts first (never blocks logging out).
    const token = pushToken()
    if (token) {
      await unregisterDevice(token).catch(() => undefined)
      registered.current.clear()
      tellApp({ type: 'push-registration', status: 'unregistered' })
    }
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

/** Inside the UniFlow phone app: tell the app whether someone is logged in, and register the
 * phone for a logged-in student's push notifications, once per push address per page load.
 * The address comes from window.UniFlowApp or, when the app's script runs late (a page
 * restored by Back on Android), from its "uniflow:push-token" event. */
function usePhoneRegistration(user: User | null, isLoading: boolean, registered: RefObject<Set<string>>) {
  useEffect(() => {
    if (isLoading) return
    tellApp({ type: 'session', signedIn: user !== null })
    if (user?.role !== 'student') return

    function register(token: string | null, platform = window.UniFlowApp?.platform) {
      if (!token || !platform || registered.current.has(token)) return
      registered.current.add(token)
      registerDevice({ token, platform, app_version: window.UniFlowApp?.appVersion ?? '' })
        .then(() => tellApp({ type: 'push-registration', status: 'registered' }))
        .catch(() => tellApp({ type: 'push-registration', status: 'failed' }))
    }

    register(pushToken())
    const onToken = (event: Event) => {
      const detail = (event as CustomEvent<PushTokenDetail>).detail
      register(detail?.token ?? null, detail?.platform)
    }
    window.addEventListener(PUSH_TOKEN_EVENT, onToken)
    return () => window.removeEventListener(PUSH_TOKEN_EVENT, onToken)
  }, [user, isLoading, registered])
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
