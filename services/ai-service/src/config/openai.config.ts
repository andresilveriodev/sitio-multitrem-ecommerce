import { ConfigService } from '@nestjs/config'
import OpenAI from 'openai'

export const createOpenAIClient = (configService: ConfigService): OpenAI => {
  return new OpenAI({
    apiKey: configService.get<string>('OPENAI_API_KEY', ''),
  })
}

export const getOpenAIConfig = (configService: ConfigService) => ({
  model: configService.get<string>('OPENAI_MODEL', 'gpt-4'),
  temperature: configService.get<number>('OPENAI_TEMPERATURE', 0.7),
  maxTokens: configService.get<number>('OPENAI_MAX_TOKENS', 500),
})

