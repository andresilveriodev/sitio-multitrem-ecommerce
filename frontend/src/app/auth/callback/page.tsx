'use client'?
?
export const dynamic = 'force-dynamic'?
?
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

/**
 * Página de callback do Keycloak
 * Recebe o código de autorização e troca por tokens
 */
export default function AuthCallbackPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(true)

  useEffect(() => {
    const code = searchParams.get('code')
    const errorParam = searchParams.get('error')
    const errorDescription = searchParams.get('error_description')

    // Verificar se houve erro no Keycloak
    if (errorParam) {
      setError(errorDescription || `Erro na autenticação: ${errorParam}`)
      setIsProcessing(false)
      setTimeout(() => router.push('/'), 3000)
      return
    }

    // Verificar se o código foi recebido
    if (!code) {
      setError('Código de autenticação não encontrado')
      setIsProcessing(false)
      setTimeout(() => router.push('/'), 3000)
      return
    }

    // Trocar o código pelo token
    const exchangeCodeForToken = async () => {
      try {
        const response = await fetch('/api/auth/keycloak/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.error || 'Erro ao processar autenticação')
        }

        const data = await response.json()

        // Salvar tokens e informações do usuário no localStorage
        localStorage.setItem('sitio-multitrem-token', data.accessToken)
        localStorage.setItem('sitio-multitrem-refresh-token', data.refreshToken)
        localStorage.setItem('sitio-multitrem-auth', JSON.stringify(data.user))

        // Aguardar um pouco para garantir que os dados foram salvos
        await new Promise(resolve => setTimeout(resolve, 500))

        // Redirecionar para a home
        window.location.href = '/'
      } catch (err) {
        console.error('Erro ao trocar código por token:', err)
        setError(err instanceof Error ? err.message : 'Erro ao processar autenticação')
        setIsProcessing(false)
        setTimeout(() => router.push('/'), 3000)
      }
    }

    exchangeCodeForToken()
  }, [searchParams, router])

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="mb-4">
            <svg
              className="mx-auto h-16 w-16 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-red-600 mb-4">Erro na Autenticação</h1>
          <p className="text-foreground/70 mb-4">{error}</p>
          <p className="text-sm text-foreground/50">
            Redirecionando para a página inicial...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center max-w-md mx-auto p-6">
        <div className="mb-6">
          <svg
            className="mx-auto h-16 w-16 text-primary"
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
        </div>
        <h1 className="text-2xl font-bold mb-4">
          {isProcessing ? 'Autenticando...' : 'Autenticado com sucesso!'}
        </h1>
        <p className="text-foreground/70 mb-6">
          {isProcessing
            ? 'Verificando suas credenciais com o Keycloak'
            : 'Redirecionando você para a página inicial'}
        </p>
        <div className="flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    </div>
  )
}


