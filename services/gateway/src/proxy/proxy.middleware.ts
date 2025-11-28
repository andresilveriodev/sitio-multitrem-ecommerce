import { Injectable, NestMiddleware, HttpException, HttpStatus } from '@nestjs/common'
import { Request, Response, NextFunction } from 'express'
import { createProxyMiddleware, Options } from 'http-proxy-middleware'
import { ConfigService } from '@nestjs/config'
import { getServicesConfig } from '../config/services.config'

@Injectable()
export class ProxyMiddleware implements NestMiddleware {
  private readonly servicesConfig: Record<string, any>

  constructor(private readonly configService: ConfigService) {
    this.servicesConfig = getServicesConfig(configService)
  }

  use(req: Request, res: Response, next: NextFunction) {
    const path = req.path

    // Mapear rotas para serviços
    let targetService: string | null = null
    let targetPath = path

    if (path.startsWith('/api/products')) {
      targetService = 'product'
      targetPath = path.replace('/api/products', '')
    } else if (path.startsWith('/api/cart')) {
      targetService = 'cart'
      targetPath = path.replace('/api/cart', '')
    } else if (path.startsWith('/api/orders')) {
      targetService = 'order'
      targetPath = path.replace('/api/orders', '')
    } else if (path.startsWith('/api/delivery')) {
      targetService = 'order'
      targetPath = path.replace('/api/delivery', '')
    } else if (path.startsWith('/api/payments')) {
      targetService = 'payment'
      targetPath = path.replace('/api/payments', '')
    } else if (path.startsWith('/api/webhooks')) {
      targetService = 'payment'
      targetPath = path.replace('/api/webhooks', '/webhooks')
    } else if (path.startsWith('/api/auth')) {
      targetService = 'auth'
      targetPath = path.replace('/api/auth', '/auth')
    } else if (path.startsWith('/api/whatsapp')) {
      targetService = 'whatsapp'
      targetPath = path.replace('/api/whatsapp', '/whatsapp')
    } else if (path.startsWith('/api/ai')) {
      targetService = 'ai'
      targetPath = path.replace('/api/ai', '/ai')
    }

    if (!targetService || !this.servicesConfig[targetService]) {
      return next()
    }

    const serviceConfig = this.servicesConfig[targetService]
    const proxyOptions: any = {
      target: serviceConfig.url,
      changeOrigin: true,
      pathRewrite: {
        [`^${req.path}`]: targetPath,
      },
      timeout: serviceConfig.timeout,
      onProxyReq: (proxyReq: any, req: Request) => {
        // Preservar headers importantes
        if (req.headers.authorization) {
          proxyReq.setHeader('authorization', req.headers.authorization)
        }
        if (req.headers['content-type']) {
          proxyReq.setHeader('content-type', req.headers['content-type'])
        }
      },
      onError: (err: Error, req: Request, res: Response) => {
        console.error(`Proxy error for ${targetService}:`, err.message)
        if (!res.headersSent) {
          res.status(HttpStatus.BAD_GATEWAY).json({
            error: 'Service unavailable',
            service: targetService,
            message: err.message,
          })
        }
      },
    }

    const proxy = createProxyMiddleware(proxyOptions)
    proxy(req, res, next)
  }
}

