'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'

interface User {
  id?: string
  email?: string
  preferred_username?: string
  given_name?: string
  family_name?: string
}

interface RegisterData {
  email: string
  password: string
  phone: string
  firstName: string
  lastName: string
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const AUTH_STORAGE_KEY = 'sitio-multitrem-auth'
const TOKEN_STORAGE_KEY = 'sitio-multitrem-token'
const REFRESH_TOKEN_STORAGE_KEY = 'sitio-multitrem-refresh-token'

function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

function getStoredRefreshToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY)
}

function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null
  try {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

function saveAuthData(token: string, refreshToken: string, user: User) {
  if (typeof window === 'undefined') return
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken)
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user))
}

function clearAuthData() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(TOKEN_STORAGE_KEY)
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY)
  localStorage.removeItem(AUTH_STORAGE_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => getStoredUser())
  const [isLoading, setIsLoading] = useState(true)
  const isAuthenticated = !!user

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

  const getUserInfo = useCallback(async (token: string): Promise<User | null> => {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 segundos

      const response = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        return null
      }

      const data = await response.json()
      return {
        id: data.id || data.sub,
        email: data.email,
        preferred_username: data.preferred_username || data.username,
        given_name: data.given_name || data.firstName,
        family_name: data.family_name || data.lastName,
      }
    } catch {
      return null
    }
  }, [API_URL])

  const refreshUser = useCallback(async () => {
    const token = getStoredToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const userInfo = await getUserInfo(token)
      if (userInfo) {
        setUser(userInfo)
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(userInfo))
      } else {
        // Token inválido, limpar dados
        clearAuthData()
        setUser(null)
      }
    } catch {
      clearAuthData()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [getUserInfo])

  useEffect(() => {
    // Verificar autenticação na inicialização
    const token = getStoredToken()
    if (token) {
      refreshUser()
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  const login = useCallback(
    async (username: string, password: string) => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 segundos

        const response = await fetch(`${API_URL}/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password }),
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const error = await response.json().catch(() => ({ 
            message: response.status === 504 
              ? 'Servidor não respondeu. Tente novamente mais tarde.' 
              : 'Erro ao fazer login' 
          }))
          throw new Error(error.message || 'Credenciais inválidas')
        }

        const data = await response.json()
        const { accessToken, refreshToken } = data

        if (!accessToken) {
          throw new Error('Token não recebido')
        }

        // Obter informações do usuário
        const userInfo = await getUserInfo(accessToken)
        if (!userInfo) {
          throw new Error('Não foi possível obter informações do usuário')
        }

        saveAuthData(accessToken, refreshToken || '', userInfo)
        setUser(userInfo)
      } catch (error) {
        clearAuthData()
        setUser(null)
        if (error instanceof Error && error.name === 'AbortError') {
          throw new Error('Tempo de espera esgotado. Verifique sua conexão e tente novamente.')
        }
        throw error
      }
    },
    [API_URL, getUserInfo]
  )

  const register = useCallback(
    async (data: RegisterData) => {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 segundos

        // Usar email como username também
        const response = await fetch(`${API_URL}/auth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: data.email,
            email: data.email,
            password: data.password,
            firstName: data.firstName,
            lastName: data.lastName,
            phone: data.phone,
          }),
          signal: controller.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const error = await response.json().catch(() => ({
            message:
              response.status === 409
                ? 'Este e-mail já está cadastrado'
                : 'Erro ao criar conta. Tente novamente.',
          }))
          throw new Error(error.message || 'Erro ao criar conta')
        }

        // Após registro bem-sucedido, fazer login automaticamente
        await login(data.email, data.password)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          throw new Error(
            'Tempo de espera esgotado. Verifique sua conexão e tente novamente.'
          )
        }
        throw error
      }
    },
    [API_URL, login]
  )

  const logout = useCallback(() => {
    const refreshToken = getStoredRefreshToken()
    
    // Tentar invalidar o token no servidor (não bloquear se falhar)
    if (refreshToken) {
      fetch(`${API_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken }),
      }).catch(() => {
        // Ignorar erros no logout
      })
    }

    clearAuthData()
    setUser(null)

    // Se for logout do Keycloak, redirecionar para logout do Keycloak
    // Isso garantirá que a sessão seja limpa no servidor Keycloak também
    if (typeof window !== 'undefined' && window.location.pathname !== '/auth/callback') {
      // Importar e usar a função de logout do Keycloak
      import('@/lib/keycloak').then(({ redirectToKeycloakLogout }) => {
        redirectToKeycloakLogout()
      }).catch(() => {
        // Se falhar, apenas redirecionar para a home
        window.location.href = '/'
      })
    }
  }, [API_URL])

  const value: AuthContextType = {
    isAuthenticated,
    user,
    isLoading,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

