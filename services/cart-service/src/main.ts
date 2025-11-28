import { NestFactory } from '@nestjs/core'
import { ValidationPipe } from '@nestjs/common'
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger'
import { AppModule } from './app.module'

async function bootstrap() {
  const app = await NestFactory.create(AppModule)

  // Configurar Swagger
  const config = new DocumentBuilder()
    .setTitle('Cart Service API')
    .setDescription('API do serviço de carrinho do Sítio Multitrem')
    .setVersion('1.0')
    .addTag('cart', 'Operações relacionadas ao carrinho de compras')
    .addServer('http://localhost:3002', 'Desenvolvimento')
    .build()

  const document = SwaggerModule.createDocument(app, config)
  SwaggerModule.setup('api/docs', app, document)

  // Habilitar CORS
  app.enableCors({
    origin: true,
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    credentials: true,
  })

  // Validação global
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  )

  const port = process.env.PORT || 3002
  await app.listen(port)
  console.log(`🛒 Cart Service running on port ${port}`)
  console.log(`📚 Swagger docs: http://localhost:${port}/api/docs`)
}

bootstrap()
