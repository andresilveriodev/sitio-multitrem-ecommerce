import {
  Controller,
  Post,
  Get,
  Body,
  HttpCode,
  HttpStatus,
} from '@nestjs/common'
import { WhatsAppService } from './whatsapp.service'
import { SendMessageDto, SendButtonsDto, SendListDto } from './dto'

@Controller('whatsapp')
export class WhatsAppController {
  constructor(private readonly whatsappService: WhatsAppService) {}

  @Post('send')
  @HttpCode(HttpStatus.OK)
  async sendText(@Body() dto: SendMessageDto) {
    return this.whatsappService.sendText(dto.to, dto.message)
  }

  @Post('send-buttons')
  @HttpCode(HttpStatus.OK)
  async sendButtons(@Body() dto: SendButtonsDto) {
    return this.whatsappService.sendButtons(dto)
  }

  @Post('send-list')
  @HttpCode(HttpStatus.OK)
  async sendList(@Body() dto: SendListDto) {
    return this.whatsappService.sendList(dto)
  }

  @Get('status')
  async getStatus() {
    return this.whatsappService.getStatus()
  }
}

