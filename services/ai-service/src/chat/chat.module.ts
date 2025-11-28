import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { ChatController } from './chat.controller'
import { ChatService } from './chat.service'
import { ExecutorService } from '../functions/executor.service'
import { createOpenAIClient } from '../config/openai.config'
import { createRedisClient } from '../config/redis.config'

@Module({
  imports: [ConfigModule],
  controllers: [ChatController],
  providers: [
    ChatService,
    ExecutorService,
    {
      provide: 'OPENAI_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createOpenAIClient(configService)
      },
      inject: [ConfigService],
    },
    {
      provide: 'REDIS_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createRedisClient(configService)
      },
      inject: [ConfigService],
    },
  ],
  exports: [ChatService],
})
export class ChatModule {}

