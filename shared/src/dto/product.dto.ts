import { IsString, IsNumber, IsEnum, IsOptional, IsBoolean, Min, Max } from 'class-validator'
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger'
import { ProductCategory } from '../types'

export class CreateProductDto {
  @ApiProperty({ description: 'Nome do produto', example: 'Alface Americana' })
  @IsString()
  name!: string

  @ApiProperty({ description: 'Slug único do produto', example: 'alface-americana' })
  @IsString()
  slug!: string

  @ApiPropertyOptional({ description: 'Descrição do produto', example: 'Alface fresca colhida no dia' })
  @IsString()
  @IsOptional()
  description?: string

  @ApiProperty({ description: 'Preço do produto', example: 5.0, minimum: 0.01 })
  @IsNumber()
  @Min(0.01)
  price!: number

  @ApiProperty({ description: 'Categoria do produto', enum: ['hortalica', 'ovos', 'kit', 'combo'], example: 'hortalica' })
  @IsEnum(['hortalica', 'ovos', 'kit', 'combo'])
  category!: ProductCategory

  @ApiPropertyOptional({ description: 'URL da imagem do produto' })
  @IsString()
  @IsOptional()
  imageUrl?: string

  @ApiPropertyOptional({ description: 'Produto ativo', example: true, default: true })
  @IsBoolean()
  @IsOptional()
  active?: boolean

  @ApiPropertyOptional({ description: 'Quantidade máxima permitida', example: 10, minimum: 1, maximum: 100 })
  @IsNumber()
  @IsOptional()
  @Min(1)
  @Max(100)
  maxQuantity?: number

  @ApiPropertyOptional({ description: 'Tamanho do kit (para produtos kit)', example: 3, minimum: 1 })
  @IsNumber()
  @IsOptional()
  @Min(1)
  kitSize?: number
}

export class UpdateProductDto {
  @ApiPropertyOptional({ description: 'Nome do produto', example: 'Alface Americana' })
  @IsString()
  @IsOptional()
  name?: string

  @ApiPropertyOptional({ description: 'Slug único do produto', example: 'alface-americana' })
  @IsString()
  @IsOptional()
  slug?: string

  @ApiPropertyOptional({ description: 'Descrição do produto', example: 'Alface fresca colhida no dia' })
  @IsString()
  @IsOptional()
  description?: string

  @ApiPropertyOptional({ description: 'Preço do produto', example: 5.0, minimum: 0.01 })
  @IsNumber()
  @IsOptional()
  @Min(0.01)
  price?: number

  @ApiPropertyOptional({ description: 'Categoria do produto', enum: ['hortalica', 'ovos', 'kit', 'combo'] })
  @IsEnum(['hortalica', 'ovos', 'kit', 'combo'])
  @IsOptional()
  category?: ProductCategory

  @ApiPropertyOptional({ description: 'URL da imagem do produto' })
  @IsString()
  @IsOptional()
  imageUrl?: string

  @ApiPropertyOptional({ description: 'Produto ativo', example: true })
  @IsBoolean()
  @IsOptional()
  active?: boolean

  @ApiPropertyOptional({ description: 'Quantidade máxima permitida', example: 10, minimum: 1, maximum: 100 })
  @IsNumber()
  @IsOptional()
  @Min(1)
  @Max(100)
  maxQuantity?: number

  @ApiPropertyOptional({ description: 'Tamanho do kit (para produtos kit)', example: 3, minimum: 1 })
  @IsNumber()
  @IsOptional()
  @Min(1)
  kitSize?: number
}

