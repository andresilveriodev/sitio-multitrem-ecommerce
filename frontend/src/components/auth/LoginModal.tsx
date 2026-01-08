'use client'

import { useState } from 'react'
import { Shield } from 'lucide-react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { redirectToKeycloakLogin } from '@/lib/keycloak'

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [isLoading, setIsLoading] = useState(false)

  const handleClose = () => {
    setIsLoading(false)
    onClose()
  }

  const handleKeycloakLogin = () => {
    setIsLoading(true)
    // Redirecionar para o Keycloak
    redirectToKeycloakLogin()
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Autenticação"
      size="sm"
    >
      <div className="space-y-6">
        {/* Informação sobre o Keycloak */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="rounded-full bg-primary/10 p-4">
              <Shield className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h3 className="text-lg font-semibold">Autenticação Segura</h3>
          <p className="text-sm text-foreground/70">
            Faça login usando a plataforma de autenticação segura do Renda Contínua.
          </p>
        </div>

        {/* Botão de Login com Keycloak */}
        <Button
          variant="primary"
          size="lg"
          onClick={handleKeycloakLogin}
          loading={isLoading}
          disabled={isLoading}
          className="w-full"
          leftIcon={<Shield className="h-5 w-5" />}
        >
          {isLoading ? 'Redirecionando...' : 'Entrar com Keycloak'}
        </Button>

        {/* Informações adicionais */}
        <div className="space-y-3 pt-4 border-t border-foreground/10">
          <div className="flex items-start gap-2 text-sm text-foreground/60">
            <svg
              className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            <span>Autenticação centralizada e segura</span>
          </div>

          <div className="flex items-start gap-2 text-sm text-foreground/60">
            <svg
              className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            <span>Seus dados protegidos com criptografia</span>
          </div>

          <div className="flex items-start gap-2 text-sm text-foreground/60">
            <svg
              className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            <span>Login rápido e sem complicações</span>
          </div>
        </div>

        {/* Nota sobre registro */}
        <div className="text-xs text-center text-foreground/50 pt-2">
          Não tem uma conta? O registro será feito automaticamente no primeiro acesso.
        </div>
      </div>
    </Modal>
  )
}
