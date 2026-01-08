/**
 * Configuração do Keycloak para autenticação
 * URL: https://auth.rendacontinua.com/auth
 */

export const keycloakConfig = {
  url: 'https://auth.rendacontinua.com/auth',
  realm: 'auth_sso',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'sitio-multitrem-app',
}

/**
 * Gera a URL de login do Keycloak
 * IMPORTANTE: Keycloak é sensível ao encoding da URL, então construímos manualmente
 */
export function getKeycloakLoginUrl(redirectUri: string): string {
  // Construir URL manualmente sem encoding automático
  const params = [
    `client_id=${keycloakConfig.clientId}`,
    `redirect_uri=${redirectUri}`,
    `response_type=code`,
    `scope=openid profile email`,
  ].join('&')

  return `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/auth?${params}`
}

/**
 * Gera a URL de logout do Keycloak
 */
export function getKeycloakLogoutUrl(redirectUri: string): string {
  const params = new URLSearchParams({
    redirect_uri: redirectUri,
  })

  return `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/logout?${params.toString()}`
}

/**
 * Redireciona o usuário para o login do Keycloak
 */
export function redirectToKeycloakLogin(): void {
  if (typeof window === 'undefined') return

  const redirectUri = `${window.location.origin}/auth/callback`
  const loginUrl = getKeycloakLoginUrl(redirectUri)
  
  // Debug: Log da URL gerada
  console.log('🔐 Keycloak Login URL:', loginUrl)
  console.log('📍 Redirect URI:', redirectUri)
  console.log('🆔 Client ID:', keycloakConfig.clientId)
  
  window.location.href = loginUrl
}

/**
 * Redireciona o usuário para o logout do Keycloak
 */
export function redirectToKeycloakLogout(): void {
  if (typeof window === 'undefined') return

  const redirectUri = window.location.origin
  const logoutUrl = getKeycloakLogoutUrl(redirectUri)
  window.location.href = logoutUrl
}

