import { IsString, IsNotEmpty, IsOptional, IsArray, IsObject } from 'class-validator'

export class ChatMessageDto {
  @IsString()
  @IsNotEmpty()
  visitorId!: string

  @IsString()
  @IsNotEmpty()
  message!: string

  @IsOptional()
  @IsArray()
  conversationHistory?: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp?: string
  }>

  @IsOptional()
  @IsString()
  source?: string
}

