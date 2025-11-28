import { IsString, IsEmail, MinLength } from 'class-validator'

export class RegisterDto {
  @IsString()
  @MinLength(3)
  username!: string

  @IsEmail()
  email!: string

  @IsString()
  @MinLength(6)
  password!: string

  @IsString()
  firstName!: string

  @IsString()
  lastName!: string

  @IsString()
  phone!: string
}


