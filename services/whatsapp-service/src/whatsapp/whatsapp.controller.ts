import {
  Controller,
  Post,
  Get,
  Body,
  HttpCode,
  HttpStatus,
} from '@nestjs/common'
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBody,
} from '@nestjs/swagger'
import { WhatsAppService } from './whatsapp.service'
import { SendMessageDto, SendButtonsDto, SendListDto } from './dto'

@ApiTags('whatsapp')
@Controller('whatsapp')
export class WhatsAppController {
  constructor(private readonly whatsappService: WhatsAppService) {}

  @Post('send')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Enviar mensagem de texto' })
  @ApiBody({ type: SendMessageDto })
  @ApiResponse({ status: 200, description: 'Mensagem enviada com sucesso' })
  async sendText(@Body() dto: SendMessageDto) {
    return this.whatsappService.sendText(dto.to, dto.message)
  }

  @Post('send-buttons')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Enviar mensagem com botões' })
  @ApiBody({ type: SendButtonsDto })
  @ApiResponse({ status: 200, description: 'Mensagem com botões enviada' })
  async sendButtons(@Body() dto: SendButtonsDto) {
    return this.whatsappService.sendButtons(dto)
  }

  @Post('send-list')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Enviar mensagem com lista' })
  @ApiBody({ type: SendListDto })
  @ApiResponse({ status: 200, description: 'Mensagem com lista enviada' })
  async sendList(@Body() dto: SendListDto) {
    return this.whatsappService.sendList(dto)
  }

  @Get('status')
  @ApiOperation({ summary: 'Verificar status da conexão WhatsApp' })
  @ApiResponse({ status: 200, description: 'Status da conexão' })
  async getStatus() {
    return this.whatsappService.getStatus()
  }
}

