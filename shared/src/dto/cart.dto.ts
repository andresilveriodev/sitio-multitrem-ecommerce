import { IsNumber, IsArray, IsString, IsOptional, Min, Max, ArrayMinSize } from 'class-validator'

export class AddToCartDto {
  @IsNumber()
  productId!: number

  @IsNumber()
  @Min(1)
  @Max(10)
  quantity!: number

  @IsArray()
  @IsString({ each: true })
  @IsOptional()
  @ArrayMinSize(1)
  selectedItems?: string[]
}

export class UpdateCartItemDto {
  @IsNumber()
  @Min(1)
  @Max(10)
  quantity!: number
}

