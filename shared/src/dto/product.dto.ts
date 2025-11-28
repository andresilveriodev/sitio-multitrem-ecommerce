import { IsString, IsNumber, IsEnum, IsOptional, IsBoolean, Min, Max } from 'class-validator'
import { ProductCategory } from '../types'

export class CreateProductDto {
  @IsString()
  name!: string

  @IsString()
  slug!: string

  @IsString()
  @IsOptional()
  description?: string

  @IsNumber()
  @Min(0.01)
  price!: number

  @IsEnum(['hortalica', 'ovos', 'kit', 'combo'])
  category!: ProductCategory

  @IsString()
  @IsOptional()
  imageUrl?: string

  @IsBoolean()
  @IsOptional()
  active?: boolean

  @IsNumber()
  @IsOptional()
  @Min(1)
  @Max(100)
  maxQuantity?: number

  @IsNumber()
  @IsOptional()
  @Min(1)
  kitSize?: number
}

export class UpdateProductDto {
  @IsString()
  @IsOptional()
  name?: string

  @IsString()
  @IsOptional()
  slug?: string

  @IsString()
  @IsOptional()
  description?: string

  @IsNumber()
  @IsOptional()
  @Min(0.01)
  price?: number

  @IsEnum(['hortalica', 'ovos', 'kit', 'combo'])
  @IsOptional()
  category?: ProductCategory

  @IsString()
  @IsOptional()
  imageUrl?: string

  @IsBoolean()
  @IsOptional()
  active?: boolean

  @IsNumber()
  @IsOptional()
  @Min(1)
  @Max(100)
  maxQuantity?: number

  @IsNumber()
  @IsOptional()
  @Min(1)
  kitSize?: number
}

