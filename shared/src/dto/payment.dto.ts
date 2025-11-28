import { IsString, IsNumber, IsEnum, IsOptional } from 'class-validator'
import { PaymentMethod } from '../types'

export class CreatePaymentDto {
  @IsString()
  orderId!: string

  @IsEnum(['pix', 'boleto', 'cartao'])
  method!: PaymentMethod

  @IsNumber()
  amount!: number

  @IsString()
  @IsOptional()
  mercadoPagoId?: string
}

