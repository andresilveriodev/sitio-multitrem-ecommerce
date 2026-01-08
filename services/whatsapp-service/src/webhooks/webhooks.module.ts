import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { WebhooksController } from './webhooks.controller'
import { WebhooksService } from './webhooks.service'
import { WhatsAppModule } from '../whatsapp/whatsapp.module'
import { AgnoModule } from '../agno/agno.module'

@Module({
  imports: [WhatsAppModule, AgnoModule, ConfigModule],
  controllers: [WebhooksController],
  providers: [WebhooksService],
})
export class WebhooksModule {}

