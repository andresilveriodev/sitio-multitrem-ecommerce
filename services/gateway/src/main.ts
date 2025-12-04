import { NestFactory } from '@nestjs/core'
import { ValidationPipe } from '@nestjs/common'
import helmet from 'helmet'
import { AppModule } from './app.module'
import { NestExpressApplication } from '@nestjs/platform-express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { ConfigService } from '@nestjs/config'
import { getServicesConfig } from './config/services.config'

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule)
  const configService = app.get(ConfigService)
  const servicesConfig = getServicesConfig(configService)

  // Helmet para segurança
  app.use(helmet())

  // Habilitar CORS
  app.enableCors({
    origin: true,
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
    allowedHeaders: ['Content-Type', 'Authorization'],
  })

  // Middleware para rotear todas as requisições /api/* ANTES do roteamento do NestJS
  app.use((req, res, next) => {
    const path = req.path
    
    // Ignorar rotas do próprio gateway
    if (path.startsWith('/health')) {
      return next()
    }

    // Só processar rotas /api/*
    if (!path.startsWith('/api')) {
      return next()
    }

    let targetService: string | null = null
    let pathRewrite: Record<string, string> = {}

    // Determinar qual serviço usar baseado no path
    if (path.startsWith('/api/products')) {
      targetService = 'product'
      pathRewrite = { '^/api/products': '' }
    } else if (path.startsWith('/api/cart')) {
      targetService = 'cart'
      pathRewrite = { '^/api/cart': '' }
    } else if (path.startsWith('/api/orders')) {
      targetService = 'order'
      pathRewrite = { '^/api/orders': '' }
    } else if (path.startsWith('/api/delivery')) {
      targetService = 'order'
      pathRewrite = { '^/api/delivery': '' }
    } else if (path.startsWith('/api/payments')) {
      targetService = 'payment'
      pathRewrite = { '^/api/payments': '' }
    } else if (path.startsWith('/api/webhooks')) {
      targetService = 'payment'
      pathRewrite = { '^/api/webhooks': '/webhooks' }
    } else if (path.startsWith('/api/auth')) {
      targetService = 'auth'
      pathRewrite = { '^/api/auth': '/auth' }
    } else if (path.startsWith('/api/whatsapp')) {
      targetService = 'whatsapp'
      pathRewrite = { '^/api/whatsapp': '/whatsapp' }
    } else if (path.startsWith('/api/ai')) {
      targetService = 'ai'
      pathRewrite = { '^/api/ai': '/ai' }
    }

    if (!targetService || !servicesConfig[targetService]) {
      console.log(`[Gateway] No service found for path: ${path}`)
      return res.status(404).json({
        error: 'Not Found',
        message: `No service configured for path: ${path}`,
      })
    }

    const serviceConfig = servicesConfig[targetService]
    console.log(`[Gateway] Routing ${req.method} ${path} -> ${serviceConfig.url}`)

    return createProxyMiddleware({
      target: serviceConfig.url,
      changeOrigin: true,
      pathRewrite,
      timeout: serviceConfig.timeout,
      logLevel: 'debug',
      onProxyReq: (proxyReq, req: any) => {
        console.log(`[Gateway] Proxying ${req.method} ${req.path} -> ${serviceConfig.url}`)
      },
      onError: (err, req, res: any) => {
        console.error(`[Gateway] Proxy error for ${targetService}:`, err.message)
        if (!res.headersSent) {
          res.status(502).json({
            error: 'Service unavailable',
            service: targetService,
            url: serviceConfig.url,
            message: err.message,
          })
        }
      },
    })(req, res, next)
  })

  // Validação global
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  )

  const port = process.env.PORT || 8000
  await app.listen(port)
  console.log(`🚪 API Gateway running on port ${port}`)
  console.log(`📊 Health check: http://localhost:${port}/health`)
  console.log(`🔄 Proxy configured for /api/* routes`)
}

bootstrap()

