import { Injectable, Inject } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { ConfigService } from '@nestjs/config'
import { Payment } from 'mercadopago'
import axios from 'axios'
import { PaymentEntity } from '../payments/entities/payment.entity'
import { PaymentStatus } from '@sitio/shared'

@Injectable()
export class WebhooksService {
  private readonly mercadoPago: Payment
  private readonly orderServiceUrl: string

  constructor(
    @InjectRepository(PaymentEntity)
    private readonly paymentRepository: Repository<PaymentEntity>,
    @Inject('MERCADO_PAGO_CLIENT') private readonly mpClient: Payment,
    private readonly configService: ConfigService,
  ) {
    this.mercadoPago = mpClient
    this.orderServiceUrl = configService.get<string>(
      'ORDER_SERVICE_URL',
      'http://localhost:3003',
    )
  }

  private mapMercadoPagoStatus(status: string): PaymentStatus {
    switch (status) {
      case 'pending':
        return 'pending'
      case 'approved':
        return 'paid'
      case 'rejected':
      case 'cancelled':
        return 'failed'
      case 'refunded':
        return 'refunded'
      default:
        return 'processing'
    }
  }

  async handlePaymentNotification(data: any): Promise<void> {
    if (data.type !== 'payment') {
      return // Ignorar outros tipos de notificação
    }

    const paymentId = data.data?.id

    if (!paymentId) {
      return
    }

    try {
      // Buscar detalhes do pagamento no Mercado Pago
      const mpPayment = await this.mercadoPago.get({ id: paymentId })

      // Buscar payment no banco pelo mercadoPagoId
      const payment = await this.paymentRepository.findOne({
        where: { mercadoPagoId: paymentId.toString() },
      })

      if (!payment) {
        console.warn(`Payment not found for Mercado Pago ID: ${paymentId}`)
        return
      }

      // Mapear status
      const status = this.mapMercadoPagoStatus(mpPayment.status || 'pending')

      // Atualizar payment
      await this.paymentRepository.update(payment.id, {
        status,
        paidAt: status === 'paid' ? new Date() : payment.paidAt,
      })

      // Se aprovado, atualizar pedido
      if (status === 'paid') {
        try {
          await axios.put(
            `${this.orderServiceUrl}/orders/${payment.orderId}/payment-status`,
            { paymentStatus: 'paid' },
          )
        } catch (error) {
          console.error(
            `Failed to update order ${payment.orderId} payment status:`,
            error,
          )
        }
      }
    } catch (error) {
      console.error('Error processing payment notification:', error)
      throw error
    }
  }
}


