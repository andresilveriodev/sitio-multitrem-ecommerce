import { Injectable } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios, { AxiosInstance } from 'axios'
import { getServicesConfig } from '../config/services.config'

export interface ServiceHealth {
  name: string
  status: 'healthy' | 'unhealthy' | 'unknown'
  url: string
  responseTime?: number
  error?: string
}

@Injectable()
export class HealthService {
  private readonly servicesConfig: Record<string, any>

  constructor(private readonly configService: ConfigService) {
    this.servicesConfig = getServicesConfig(configService)
  }

  async checkGatewayHealth(): Promise<{ status: string; timestamp: string }> {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
    }
  }

  async checkServicesHealth(): Promise<{
    gateway: ServiceHealth
    services: ServiceHealth[]
  }> {
    const gatewayHealth: ServiceHealth = {
      name: 'gateway',
      status: 'healthy',
      url: 'http://localhost:3000',
    }

    const servicesHealth: ServiceHealth[] = await Promise.all(
      Object.entries(this.servicesConfig).map(async ([name, config]) => {
        const startTime = Date.now()
        try {
          const response = await axios.get(`${config.url}/health`, {
            timeout: 5000,
          })
          const responseTime = Date.now() - startTime

          return {
            name,
            status: response.status === 200 ? 'healthy' : 'unhealthy',
            url: config.url,
            responseTime,
          }
        } catch (error: any) {
          const responseTime = Date.now() - startTime
          return {
            name,
            status: 'unhealthy',
            url: config.url,
            responseTime,
            error: error.message || 'Service unavailable',
          }
        }
      }),
    )

    return {
      gateway: gatewayHealth,
      services: servicesHealth,
    }
  }
}

