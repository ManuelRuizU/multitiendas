//AuthContext.jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user,           setUser]           = useState(null)
  const [loading,        setLoading]        = useState(true)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)

  const loadUser = useCallback(async () => {
    const token = localStorage.getItem('access_token')
    if (!token) { setLoading(false); return }
    try {
      const { data } = await api.get('usuarios/users/me/')
      setUser(data)
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadUser() }, [loadUser])

  const login = useCallback((tokens, userData) => {
    localStorage.setItem('access_token',  tokens.access)
    localStorage.setItem('refresh_token', tokens.refresh)
    setUser(userData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('guest_id')
    setUser(null)
  }, [])

  const openAuthModal  = useCallback(() => setIsAuthModalOpen(true),  [])
  const closeAuthModal = useCallback(() => setIsAuthModalOpen(false), [])

  return (
    <AuthContext.Provider value={{
      user, loading, login, logout, loadUser,
      isAuthModalOpen, openAuthModal, closeAuthModal,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
