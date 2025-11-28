import { Module } from '@nestjs/common'
import { ConfigModule, ConfigService } from '@nestjs/config'
import { CartController } from './cart.controller'
import { CartService } from './cart.service'
import { createRedisClient } from '../config/redis.config'

@Module({
  imports: [ConfigModule],
  controllers: [CartController],
  providers: [
    CartService,
    {
      provide: 'REDIS_CLIENT',
      useFactory: (configService: ConfigService) => {
        return createRedisClient(configService)
      },
      inject: [ConfigService],
    },
  ],
  exports: [CartService],
})
export class CartModule {}



