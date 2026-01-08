import { NextRequest, NextResponse } from 'next/server'

const keycloakConfig = {
  url: 'https://auth.rendacontinua.com/auth',
  realm: 'auth_sso',
  clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'sitio-multitrem-app',
}

/**
 * API Route para trocar o código de autorização do Keycloak por tokens
 * POST /api/auth/keycloak/token
 */
export async function POST(request: NextRequest) {
  try {
    const { code } = await request.json()

    if (!code) {
      return NextResponse.json(
        { error: 'Código de autorização não fornecido' },
        { status: 400 }
      )
    }

    const redirectUri = `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/auth/callback`

    // Trocar código por token no Keycloak
    const tokenResponse = await fetch(
      `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/token`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: keycloakConfig.clientId,
          code,
          redirect_uri: redirectUri,
        }),
      }
    )

    if (!tokenResponse.ok) {
      const error = await tokenResponse.text()
      console.error('Erro ao trocar código por token:', error)
      return NextResponse.json(
        { error: 'Erro ao obter token do Keycloak' },
        { status: 500 }
      )
    }

    const tokens = await tokenResponse.json()

    // Obter informações do usuário do Keycloak
    const userInfoResponse = await fetch(
      `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/userinfo`,
      {
        headers: {
          Authorization: `Bearer ${tokens.access_token}`,
        },
      }
    )

    if (!userInfoResponse.ok) {
      console.error('Erro ao obter informações do usuário')
      return NextResponse.json(
        { error: 'Erro ao obter informações do usuário' },
        { status: 500 }
      )
    }

    const userInfo = await userInfoResponse.json()

    // Retornar tokens e informações do usuário
    return NextResponse.json({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      expiresIn: tokens.expires_in,
      user: {
        id: userInfo.sub,
        email: userInfo.email,
        preferred_username: userInfo.preferred_username,
        given_name: userInfo.given_name,
        family_name: userInfo.family_name,
        name: userInfo.name,
      },
    })
  } catch (error) {
    console.error('Erro no callback do Keycloak:', error)
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    )
  }
}





