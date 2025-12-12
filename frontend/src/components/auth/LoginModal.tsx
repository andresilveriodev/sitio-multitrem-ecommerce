'use client'

import { useState } from 'react'
import { Mail, Lock, Eye, EyeOff, Phone, User, LogIn, UserPlus } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/contexts/AuthContext'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
}

type ModalView = 'choice' | 'register' | 'login'

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [view, setView] = useState<ModalView>('choice')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Register form state
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')
  const [registerPhone, setRegisterPhone] = useState('')
  const [registerFirstName, setRegisterFirstName] = useState('')
  const [registerLastName, setRegisterLastName] = useState('')
  const [showRegisterPassword, setShowRegisterPassword] = useState(false)

  // Login form state
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [showLoginPassword, setShowLoginPassword] = useState(false)

  const { login, register } = useAuth()

  const handleClose = () => {
    setView('choice')
    setError(null)
    setIsLoading(false)
    setRegisterEmail('')
    setRegisterPassword('')
    setRegisterPhone('')
    setRegisterFirstName('')
    setRegisterLastName('')
    setShowRegisterPassword(false)
    setLoginEmail('')
    setLoginPassword('')
    setShowLoginPassword(false)
    onClose()
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await register({
        email: registerEmail,
        password: registerPassword,
        phone: registerPhone,
        firstName: registerFirstName,
        lastName: registerLastName,
      })
      handleClose()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Erro ao criar conta. Tente novamente.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await login(loginEmail, loginPassword)
      handleClose()
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Erro ao fazer login. Tente novamente.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleLogin = () => {
    // TODO: Implementar login com Google
    setError('Login com Google ainda não implementado')
  }

  const handleFacebookLogin = () => {
    // TODO: Implementar login com Facebook
    setError('Login com Facebook ainda não implementado')
  }

  const getModalTitle = () => {
    switch (view) {
      case 'register':
        return 'Criar Conta'
      case 'login':
        return 'Entrar'
      default:
        return 'Boas vindas!'
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={getModalTitle()}
      size="sm"
    >
      {view === 'choice' && (
        <div className="space-y-4">
          <div className="text-center text-sm text-foreground/70">
            Escolha uma opção para continuar
          </div>

          <div className="flex flex-col gap-3">
            <Button
              variant="primary"
              size="md"
              leftIcon={<UserPlus className="h-4 w-4" />}
              className="w-full"
              onClick={() => setView('register')}
            >
              Quero criar uma conta
            </Button>

            <Button
              variant="outline"
              size="md"
              leftIcon={<LogIn className="h-4 w-4" />}
              className="w-full"
              onClick={() => setView('login')}
            >
              Já sou cliente
            </Button>
          </div>
        </div>
      )}

      {view === 'register' && (
        <form onSubmit={handleRegister} className="space-y-4">
          {error && (
            <div
              className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Nome"
              type="text"
              value={registerFirstName}
              onChange={(e) => setRegisterFirstName(e.target.value)}
              placeholder="Seu nome"
              leftIcon={<User className="h-4 w-4" />}
              required
              disabled={isLoading}
              autoComplete="given-name"
            />

            <Input
              label="Sobrenome"
              type="text"
              value={registerLastName}
              onChange={(e) => setRegisterLastName(e.target.value)}
              placeholder="Seu sobrenome"
              leftIcon={<User className="h-4 w-4" />}
              required
              disabled={isLoading}
              autoComplete="family-name"
            />
          </div>

          <Input
            label="E-mail"
            type="email"
            value={registerEmail}
            onChange={(e) => setRegisterEmail(e.target.value)}
            placeholder="seu@email.com"
            leftIcon={<Mail className="h-4 w-4" />}
            required
            disabled={isLoading}
            autoComplete="email"
          />

          <div className="space-y-1">
            <Input
              label="Senha"
              type={showRegisterPassword ? 'text' : 'password'}
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              placeholder="Mínimo 6 caracteres"
              leftIcon={<Lock className="h-4 w-4" />}
              required
              disabled={isLoading}
              autoComplete="new-password"
              minLength={6}
            />
            <button
              type="button"
              onClick={() => setShowRegisterPassword(!showRegisterPassword)}
              className="flex items-center gap-1 text-xs text-foreground/60 hover:text-foreground/80 transition-colors"
              disabled={isLoading}
            >
              {showRegisterPassword ? (
                <>
                  <EyeOff className="h-3 w-3" />
                  Ocultar senha
                </>
              ) : (
                <>
                  <Eye className="h-3 w-3" />
                  Mostrar senha
                </>
              )}
            </button>
          </div>

          <Input
            label="Telefone"
            type="tel"
            value={registerPhone}
            onChange={(e) => setRegisterPhone(e.target.value)}
            placeholder="(00) 00000-0000"
            leftIcon={<Phone className="h-4 w-4" />}
            required
            disabled={isLoading}
            autoComplete="tel"
          />

          <div className="flex flex-col gap-2 pt-2">
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={isLoading}
              className="w-full"
            >
              Cadastrar
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setView('choice')}
              disabled={isLoading}
              className="w-full"
            >
              Voltar
            </Button>
          </div>
        </form>
      )}

      {view === 'login' && (
        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <div
              className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700"
              role="alert"
            >
              {error}
            </div>
          )}

          <Input
            label="E-mail"
            type="email"
            value={loginEmail}
            onChange={(e) => setLoginEmail(e.target.value)}
            placeholder="seu@email.com"
            leftIcon={<Mail className="h-4 w-4" />}
            required
            disabled={isLoading}
            autoComplete="email"
          />

          <div className="space-y-1">
            <Input
              label="Senha"
              type={showLoginPassword ? 'text' : 'password'}
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              placeholder="Digite sua senha"
              leftIcon={<Lock className="h-4 w-4" />}
              required
              disabled={isLoading}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowLoginPassword(!showLoginPassword)}
              className="flex items-center gap-1 text-xs text-foreground/60 hover:text-foreground/80 transition-colors"
              disabled={isLoading}
            >
              {showLoginPassword ? (
                <>
                  <EyeOff className="h-3 w-3" />
                  Ocultar senha
                </>
              ) : (
                <>
                  <Eye className="h-3 w-3" />
                  Mostrar senha
                </>
              )}
            </button>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={isLoading}
              leftIcon={<LogIn className="h-4 w-4" />}
              className="w-full"
            >
              Entrar
            </Button>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-foreground/20"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-foreground/60">
                  Ou entre com
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleGoogleLogin}
                disabled={isLoading}
                className="w-full"
              >
                <svg
                  className="mr-2 h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Google
              </Button>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleFacebookLogin}
                disabled={isLoading}
                className="w-full"
              >
                <svg
                  className="mr-2 h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
                Facebook
              </Button>
            </div>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setView('choice')}
              disabled={isLoading}
              className="w-full mt-2"
            >
              Voltar
            </Button>
          </div>
        </form>
      )}
    </Modal>
  )
}
