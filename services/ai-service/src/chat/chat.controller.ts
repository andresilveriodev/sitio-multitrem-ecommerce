import { Controller, Post, Get, Body, Param, HttpCode, HttpStatus } from '@nestjs/common'
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiBody,
} from '@nestjs/swagger'
import { ChatService } from './chat.service'
import { ChatMessageDto } from './dto'

@ApiTags('ai')
@Controller('ai')
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  @Post('chat')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Processar mensagem do assistente IA' })
  @ApiBody({ type: ChatMessageDto })
  @ApiResponse({ status: 200, description: 'Resposta do assistente IA' })
  @ApiResponse({ status: 500, description: 'Erro interno do servidor' })
  async chat(@Body() dto: ChatMessageDto) {
    try {
      return await this.chatService.processMessage(dto)
    } catch (error: any) {
      console.error('Error processing message:', error)
      throw new Error(
        error.message || 'Erro ao processar mensagem. Verifique se os serviços estão rodando.',
      )
    }
  }

  @Get('conversation/:visitorId')
  @ApiOperation({ summary: 'Obter histórico de conversa' })
  @ApiParam({ name: 'visitorId', description: 'ID do visitante', type: String })
  @ApiResponse({ status: 200, description: 'Histórico de conversa' })
  async getConversation(@Param('visitorId') visitorId: string) {
    return {
      visitorId,
      history: await this.chatService.getConversationHistory(visitorId),
    }
  }
}

