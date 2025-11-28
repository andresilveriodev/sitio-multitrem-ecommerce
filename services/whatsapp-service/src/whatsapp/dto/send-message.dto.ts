import { IsString, IsNotEmpty, IsOptional, IsArray } from 'class-validator'

export class SendMessageDto {
  @IsString()
  @IsNotEmpty()
  to!: string

  @IsString()
  @IsNotEmpty()
  message!: string
}

export class SendButtonsDto {
  @IsString()
  @IsNotEmpty()
  to!: string

  @IsString()
  @IsNotEmpty()
  message!: string

  @IsArray()
  @IsString({ each: true })
  buttons!: string[]
}

export class SendListDto {
  @IsString()
  @IsNotEmpty()
  to!: string

  @IsString()
  @IsNotEmpty()
  title!: string

  @IsString()
  @IsNotEmpty()
  description!: string

  @IsString()
  @IsNotEmpty()
  buttonText!: string

  @IsArray()
  sections!: Array<{
    title: string
    rows: Array<{
      id: string
      title: string
      description?: string
    }>
  }>
}

