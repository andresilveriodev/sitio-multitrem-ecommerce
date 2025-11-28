import { Controller, Post, Get, Body, Param, HttpCode, HttpStatus } from '@nestjs/common'
import { ChatService } from './chat.service'
import { ChatMessageDto } from './dto'

@Controller('ai')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post('chat')
  @HttpCode(HttpStatus.OK)
  async chat(@Body() dto: ChatMessageDto) {
    return this.chatService.processMessage(dto)
  }

  @Get('conversation/:visitorId')
  async getConversation(@Param('visitorId') visitorId: string) {
    return {
      visitorId,
      history: await this.chatService.getConversationHistory(visitorId),
    }
  }
}

