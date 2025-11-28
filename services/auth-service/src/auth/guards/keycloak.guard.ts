import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common'
import { Reflector } from '@nestjs/core'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import { IS_PUBLIC_KEY } from '../decorators/public.decorator'

@Injectable()
export class KeycloakGuard implements CanActivate {
  private readonly keycloakUrl: string
  private readonly realm: string

  constructor(
    private readonly reflector: Reflector,
    private readonly configService: ConfigService,
  ) {
    this.keycloakUrl = configService.get<string>(
      'KEYCLOAK_URL',
      'http://localhost:8080',
    )
    this.realm = configService.get<string>('KEYCLOAK_REALM', 'sitio-multitrem')
  }

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ])

    if (isPublic) {
      return true
    }

    const request = context.switchToHttp().getRequest()
    const authorization = request.headers.authorization

    if (!authorization) {
      throw new UnauthorizedException('Authorization header is required')
    }

    const token = authorization.replace('Bearer ', '')

    try {
      // Validar token no Keycloak
      const introspectEndpoint = `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/token/introspect`
      const clientId = this.configService.get<string>(
        'KEYCLOAK_CLIENT_ID',
        'sitio-app',
      )
      const clientSecret = this.configService.get<string>(
        'KEYCLOAK_CLIENT_SECRET',
        '',
      )

      const params = new URLSearchParams()
      params.append('token', token)
      params.append('client_id', clientId)
      if (clientSecret) {
        params.append('client_secret', clientSecret)
      }

      const response = await axios.post(introspectEndpoint, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      if (!response.data.active) {
        throw new UnauthorizedException('Token is invalid or expired')
      }

      // Adicionar informações do usuário à request
      request.user = {
        id: response.data.sub,
        username: response.data.preferred_username,
        email: response.data.email,
        roles: response.data.realm_access?.roles || [],
      }

      return true
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new UnauthorizedException('Invalid token')
      }
      throw new UnauthorizedException('Token validation failed')
    }
  }
}


