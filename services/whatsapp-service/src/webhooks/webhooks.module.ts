import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { WebhooksController } from './webhooks.controller'
import { WebhooksService } from './webhooks.service'
import { WhatsAppModule } from '../whatsapp/whatsapp.module'
import { createRedisClient } from '../config/redis.config'

@Module({
  imports: [WhatsAppModule, ConfigModule],
  controllers: [WebhooksController],
  providers: [
    WebhooksService,
    {
      provide: 'REDIS_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createRedisClient(configService)
      },
      inject: [ConfigService],
    },
  ],
})
export class WebhooksModule {}

