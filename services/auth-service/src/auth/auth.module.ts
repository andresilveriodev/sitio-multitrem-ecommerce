import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { APP_GUARD } from '@nestjs/core'
import { AuthController } from './auth.controller'
import { AuthService } from './auth.service'
import { KeycloakGuard } from './guards/keycloak.guard'
import { createKeycloakAdminClient } from '../config/keycloak.config'

@Module({
  imports: [ConfigModule],
  controllers: [AuthController],
  providers: [
    AuthService,
    {
      provide: 'KEYCLOAK_ADMIN_CLIENT',
      useFactory: async (configService: ConfigService) => {
        return createKeycloakAdminClient(configService)
      },
      inject: [ConfigService],
    },
    {
      provide: APP_GUARD,
      useClass: KeycloakGuard,
    },
  ],
  exports: [AuthService],
})
export class AuthModule {}


