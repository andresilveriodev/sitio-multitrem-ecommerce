import Redis from 'ioredis'

interface RateLimitConfig {
  maxRequests: number
  windowMs: number
}

export class RateLimiter {
  private redis: Redis
  private config: RateLimitConfig

  constructor(redis: Redis, config: RateLimitConfig) {
    this.redis = redis
    this.config = config
  }

  async checkLimit(phoneNumber: string): Promise<{ allowed: boolean; remaining: number }> {
    const key = `rate_limit:whatsapp:${phoneNumber}`
    const now = Date.now()
    const windowStart = now - this.config.windowMs

    // Remover requisições antigas
    await this.redis.zremrangebyscore(key, 0, windowStart)

    // Contar requisições no window
    const count = await this.redis.zcard(key)

    if (count >= this.config.maxRequests) {
      return {
        allowed: false,
        remaining: 0,
      }
    }

    // Adicionar requisição atual
    await this.redis.zadd(key, now, `${now}-${Math.random()}`)
    await this.redis.expire(key, Math.ceil(this.config.windowMs / 1000))

    return {
      allowed: true,
      remaining: this.config.maxRequests - count - 1,
    }
  }
}








