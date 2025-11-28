import { NestFactory } from '@nestjs/core'
import { ValidationPipe } from '@nestjs/common'
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger'
import { AppModule } from './app.module'

async function bootstrap() {
  const app = await NestFactory.create(AppModule)

  // Configurar Swagger
  const config = new DocumentBuilder()
    .setTitle('WhatsApp Service API')
    .setDescription('API do serviço de WhatsApp do Sítio Multitrem (Evolution API)')
    .setVersion('1.0')
    .addTag('whatsapp', 'Operações relacionadas ao WhatsApp')
    .addTag('webhooks', 'Webhooks do Evolution API')
    .addServer('http://localhost:3006', 'Desenvolvimento')
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

  const port = process.env.PORT || 3006
  await app.listen(port)
  console.log(`📱 WhatsApp Service running on port ${port}`)
  console.log(`📚 Swagger docs: http://localhost:${port}/api/docs`)
}

bootstrap()
