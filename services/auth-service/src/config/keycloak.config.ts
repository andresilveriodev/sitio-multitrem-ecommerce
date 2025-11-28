import { ConfigService } from '@nestjs/config'
import KcAdminClient from '@keycloak/keycloak-admin-client'

export const createKeycloakAdminClient = async (
  configService: ConfigService,
): Promise<KcAdminClient> => {
  const kcAdminClient = new KcAdminClient({
    baseUrl: configService.get<string>('KEYCLOAK_URL', 'http://localhost:8080'),
    realmName: configService.get<string>('KEYCLOAK_REALM', 'sitio-multitrem'),
  })

  // Autenticar como admin
  await kcAdminClient.auth({
    username: configService.get<string>('KEYCLOAK_ADMIN_USER', 'admin'),
    password: configService.get<string>('KEYCLOAK_ADMIN_PASSWORD', 'admin'),
    grantType: 'password',
    clientId: configService.get<string>(
      'KEYCLOAK_ADMIN_CLIENT_ID',
      'admin-cli',
    ),
  })

  return kcAdminClient
}

export const getKeycloakConfig = (configService: ConfigService) => ({
  realm: configService.get<string>('KEYCLOAK_REALM', 'sitio-multitrem'),
  serverUrl: configService.get<string>('KEYCLOAK_URL', 'http://localhost:8080'),
  clientId: configService.get<string>('KEYCLOAK_CLIENT_ID', 'sitio-app'),
  clientSecret: configService.get<string>('KEYCLOAK_CLIENT_SECRET', ''),
  bearerOnly: false,
})


