import { Module, Global } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import { createRedisClient } from '../config/redis.config'

@Global()
@Module({
  providers: [
    {
      provide: 'REDIS_CLIENT',
      useFactory: (configService: ConfigService) => {
        const redis = createRedisClient(configService)
        
        // Logs de conexão
        redis.on('connect', () => {
          console.log('✅ Redis conectado com sucesso')
        })
        
        redis.on('error', (error) => {
          console.error('❌ Erro no Redis:', error.message)
        })
        
        redis.on('ready', () => {
          console.log('🚀 Redis pronto para uso')
        })
        
        redis.on('reconnecting', () => {
          console.log('🔄 Redis reconectando...')
        })
        
        redis.on('close', () => {
          console.log('⚠️ Conexão Redis fechada')
        })
        
        return redis
      },
      inject: [ConfigService],
    },
  ],
  exports: ['REDIS_CLIENT'],
})
export class RedisModule {}



