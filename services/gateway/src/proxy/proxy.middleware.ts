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

    // Ignorar rotas do próprio gateway
    if (path.startsWith('/health')) {
      return next()
    }

    // Mapear rotas para serviços
    let targetService: string | null = null
    let pathRewritePattern: string = ''
    let pathRewriteReplacement: string = ''

    if (path.startsWith('/api/products')) {
      targetService = 'product'
      pathRewritePattern = '^/api/products'
      pathRewriteReplacement = ''
    } else if (path.startsWith('/api/cart')) {
      targetService = 'cart'
      pathRewritePattern = '^/api/cart'
      pathRewriteReplacement = ''
    } else if (path.startsWith('/api/orders')) {
      targetService = 'order'
      pathRewritePattern = '^/api/orders'
      pathRewriteReplacement = ''
    } else if (path.startsWith('/api/delivery')) {
      targetService = 'order'
      pathRewritePattern = '^/api/delivery'
      pathRewriteReplacement = ''
    } else if (path.startsWith('/api/payments')) {
      targetService = 'payment'
      pathRewritePattern = '^/api/payments'
      pathRewriteReplacement = ''
    } else if (path.startsWith('/api/webhooks')) {
      targetService = 'payment'
      pathRewritePattern = '^/api/webhooks'
      pathRewriteReplacement = '/webhooks'
    } else if (path.startsWith('/api/auth')) {
      targetService = 'auth'
      pathRewritePattern = '^/api/auth'
      pathRewriteReplacement = '/auth'
    } else if (path.startsWith('/api/whatsapp')) {
      targetService = 'whatsapp'
      pathRewritePattern = '^/api/whatsapp'
      pathRewriteReplacement = '/whatsapp'
    } else if (path.startsWith('/api/ai')) {
      targetService = 'ai'
      pathRewritePattern = '^/api/ai'
      pathRewriteReplacement = '/ai'
    }

    if (!targetService || !this.servicesConfig[targetService]) {
      console.log(`[Gateway] No service found for path: ${path}`)
      return next()
    }

    const serviceConfig = this.servicesConfig[targetService]
    console.log(`[Gateway] Routing ${path} -> ${serviceConfig.url} (rewrite: ${pathRewritePattern} -> ${pathRewriteReplacement})`)
    
    const proxyOptions: any = {
      target: serviceConfig.url,
      changeOrigin: true,
      pathRewrite: {
        [pathRewritePattern]: pathRewriteReplacement,
      },
      logLevel: 'debug',
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
        console.error(`[Gateway] Proxy error for ${targetService} (${serviceConfig.url}):`, err.message)
        if (!res.headersSent) {
          res.status(HttpStatus.BAD_GATEWAY).json({
            error: 'Service unavailable',
            service: targetService,
            url: serviceConfig.url,
            message: err.message,
          })
        }
      },
    }

    const proxy = createProxyMiddleware(proxyOptions)
    proxy(req, res, next)
  }
}

