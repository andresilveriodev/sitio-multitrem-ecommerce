import { ConfigService } from '@nestjs/config'

export const getEvolutionConfig = (configService: ConfigService) => ({
  baseUrl: configService.get<string>(
    'EVOLUTION_API_URL',
    'http://localhost:8081',
  ),
  apiKey: configService.get<string>('EVOLUTION_API_KEY', ''),
  instanceName: configService.get<string>(
    'EVOLUTION_INSTANCE',
    'sitio-multitrem',
  ),
})

