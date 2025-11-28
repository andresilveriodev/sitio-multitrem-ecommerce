import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { WhatsAppModule } from './whatsapp/whatsapp.module'
import { WebhooksModule } from './webhooks/webhooks.module'

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    WhatsAppModule,
    WebhooksModule,
  ],
})
export class AppModule {}

