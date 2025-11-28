import { IsString, IsEnum, IsDateString, IsOptional, IsNumber, ValidateNested, IsObject } from 'class-validator'
import { Type } from 'class-transformer'
import { DeliveryPeriod, PaymentMethod } from '../types'

export class AddressDto {
  @IsString()
  street!: string

  @IsString()
  number!: string

  @IsString()
  @IsOptional()
  complement?: string

  @IsString()
  neighborhood!: string

  @IsString()
  city!: string

  @IsString()
  state!: string

  @IsString()
  zipCode!: string
}

export class CreateOrderDto {
  @IsString()
  visitorId!: string

  @IsString()
  customerName!: string

  @IsString()
  customerPhone!: string

  @ValidateNested()
  @Type(() => AddressDto)
  address!: AddressDto

  @IsDateString()
  deliveryDate!: string

  @IsEnum(['manha'])
  deliveryPeriod!: DeliveryPeriod

  @IsEnum(['pix', 'boleto', 'cartao'])
  paymentMethod!: PaymentMethod

  @IsNumber()
  @IsOptional()
  customerId?: number
}

export class UpdateOrderStatusDto {
  @IsEnum(['pending', 'confirmed', 'preparing', 'delivering', 'delivered', 'cancelled'])
  status!: string
}

