import { useCallback, useMemo, useState } from 'react'
import {
  getCurrentUser,
  loginAccount,
  registerAccount,
} from '../services/authService.js'
import { AuthContext } from './authContext.js'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [accessToken, setAccessToken] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const startSession = useCallback(async (email, password) => {
    const tokenResponse = await loginAccount(email, password)
    const currentUser = await getCurrentUser(tokenResponse.access_token)
    setAccessToken(tokenResponse.access_token)
    setUser(currentUser)
  }, [])

  const login = useCallback(async (email, password) => {
    setIsLoading(true)
    try {
      await startSession(email, password)
    } finally {
      setIsLoading(false)
    }
  }, [startSession])

  const register = useCallback(async (details) => {
    setIsLoading(true)
    try {
      await registerAccount(details)
      await startSession(details.email, details.password)
    } finally {
      setIsLoading(false)
    }
  }, [startSession])

  const logout = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  const authState = useMemo(
    () => ({ user, accessToken, isLoading, login, register, logout }),
    [user, accessToken, isLoading, login, register, logout],
  )

  return (
    <AuthContext.Provider value={authState}>
      {children}
    </AuthContext.Provider>
  )
}
