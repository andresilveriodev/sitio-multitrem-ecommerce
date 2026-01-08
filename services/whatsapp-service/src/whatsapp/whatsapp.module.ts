import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { WhatsAppController } from './whatsapp.controller'
import { WhatsAppService } from './whatsapp.service'
import { getEvolutionConfig } from '../config/evolution.config'

@Module({
  imports: [ConfigModule],
  controllers: [WhatsAppController],
  providers: [
    WhatsAppService,
    {
      provide: 'EVOLUTION_CONFIG',
      useFactory: (configService: ConfigService) => {
        return getEvolutionConfig(configService)
      },
      inject: [ConfigService],
    },
  ],
  exports: [WhatsAppService],
})
export class WhatsAppModule {}

