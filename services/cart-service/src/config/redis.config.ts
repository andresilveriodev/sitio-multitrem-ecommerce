import { ConfigService } from '@nestjs/config'
import Redis from 'ioredis'

export const createRedisClient = (configService: ConfigService): Redis => {
  return new Redis({
    host: configService.get<string>('REDIS_HOST', 'localhost'),
    port: configService.get<number>('REDIS_PORT', 6379),
    password: configService.get<string>('REDIS_PASSWORD', undefined),
    db: configService.get<number>('REDIS_DB', 0),
    retryStrategy: (times) => {
      const delay = Math.min(times * 50, 2000)
      return delay
    },
  })
}


