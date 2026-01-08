import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { RedisModule } from './redis/redis.module'
import { WhatsAppModule } from './whatsapp/whatsapp.module'
import { WebhooksModule } from './webhooks/webhooks.module'
import { AgnoModule } from './agno/agno.module'

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    RedisModule, // Redis deve ser importado antes dos outros módulos
    WhatsAppModule,
    WebhooksModule,
    AgnoModule,
  ],
})
export class AppModule {}

