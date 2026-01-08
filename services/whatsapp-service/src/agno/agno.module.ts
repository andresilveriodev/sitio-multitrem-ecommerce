import { Module } from '@nestjs/common'
import { ConfigModule } from '@nestjs/config'
import { AgnoService } from './agno.service'

@Module({
  imports: [ConfigModule],
  providers: [AgnoService],
  exports: [AgnoService],
})
export class AgnoModule {}





