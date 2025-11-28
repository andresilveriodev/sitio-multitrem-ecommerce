import { Injectable, Inject, UnauthorizedException, BadRequestException } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios from 'axios'
import KcAdminClient from '@keycloak/keycloak-admin-client'
import { RegisterDto, LoginDto, RefreshDto } from './dto'

@Injectable()
export class AuthService {
  private readonly keycloakUrl: string
  private readonly realm: string
  private readonly clientId: string
  private readonly clientSecret: string

  constructor(
    @Inject('KEYCLOAK_ADMIN_CLIENT')
    private readonly kcAdminClient: KcAdminClient,
    private readonly configService: ConfigService,
  ) {
    this.keycloakUrl = configService.get<string>(
      'KEYCLOAK_URL',
      'http://localhost:8080',
    )
    this.realm = configService.get<string>('KEYCLOAK_REALM', 'sitio-multitrem')
    this.clientId = configService.get<string>('KEYCLOAK_CLIENT_ID', 'sitio-app')
    this.clientSecret = configService.get<string>(
      'KEYCLOAK_CLIENT_SECRET',
      '',
    )
  }

  private async getTokenEndpoint(): Promise<string> {
    return `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/token`
  }

  async register(dto: RegisterDto) {
    try {
      // Criar usuário no Keycloak
      const user = await this.kcAdminClient.users.create({
        realm: this.realm,
        username: dto.username,
        email: dto.email,
        firstName: dto.firstName,
        lastName: dto.lastName,
        enabled: true,
        emailVerified: false,
        credentials: [
          {
            type: 'password',
            value: dto.password,
            temporary: false,
          },
        ],
        attributes: {
          phone: [dto.phone],
        },
      })

      return {
        id: user.id,
        username: dto.username,
        email: dto.email,
        message: 'User created successfully',
      }
    } catch (error: any) {
      if (error.response?.status === 409) {
        throw new BadRequestException('User already exists')
      }
      throw new BadRequestException(
        `Failed to create user: ${error.message || 'Unknown error'}`,
      )
    }
  }

  async login(dto: LoginDto) {
    try {
      const tokenEndpoint = await this.getTokenEndpoint()

      const params = new URLSearchParams()
      params.append('grant_type', 'password')
      params.append('client_id', this.clientId)
      if (this.clientSecret) {
        params.append('client_secret', this.clientSecret)
      }
      params.append('username', dto.username)
      params.append('password', dto.password)

      const response = await axios.post(tokenEndpoint, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      return {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in,
        tokenType: response.data.token_type,
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new UnauthorizedException('Invalid credentials')
      }
      throw new BadRequestException(
        `Login failed: ${error.message || 'Unknown error'}`,
      )
    }
  }

  async refresh(dto: RefreshDto) {
    try {
      const tokenEndpoint = await this.getTokenEndpoint()

      const params = new URLSearchParams()
      params.append('grant_type', 'refresh_token')
      params.append('client_id', this.clientId)
      if (this.clientSecret) {
        params.append('client_secret', this.clientSecret)
      }
      params.append('refresh_token', dto.refreshToken)

      const response = await axios.post(tokenEndpoint, params, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      return {
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
        expiresIn: response.data.expires_in,
        tokenType: response.data.token_type,
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new UnauthorizedException('Invalid refresh token')
      }
      throw new BadRequestException(
        `Refresh failed: ${error.message || 'Unknown error'}`,
      )
    }
  }

  async logout(refreshToken: string) {
    try {
      const tokenEndpoint = await this.getTokenEndpoint()

      const params = new URLSearchParams()
      params.append('grant_type', 'refresh_token')
      params.append('client_id', this.clientId)
      if (this.clientSecret) {
        params.append('client_secret', this.clientSecret)
      }
      params.append('refresh_token', refreshToken)

      await axios.post(
        `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/logout`,
        params,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        },
      )

      return { message: 'Logged out successfully' }
    } catch (error: any) {
      // Não falhar se o token já foi invalidado
      return { message: 'Logout processed' }
    }
  }

  async getUserInfo(accessToken: string) {
    try {
      const userInfoEndpoint = `${this.keycloakUrl}/realms/${this.realm}/protocol/openid-connect/userinfo`

      const response = await axios.get(userInfoEndpoint, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      return response.data
    } catch (error: any) {
      if (error.response?.status === 401) {
        throw new UnauthorizedException('Invalid access token')
      }
      throw new BadRequestException(
        `Failed to get user info: ${error.message || 'Unknown error'}`,
      )
    }
  }
}


