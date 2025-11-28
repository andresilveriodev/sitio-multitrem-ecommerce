import { Injectable, NotFoundException, BadRequestException, Inject } from '@nestjs/common'
import { InjectRepository } from '@nestjs/typeorm'
import { Repository } from 'typeorm'
import { ConfigService } from '@nestjs/config'
import { Payment } from 'mercadopago'
import axios from 'axios'
import { PaymentEntity } from './entities/payment.entity'
import { CreatePaymentDto, PaymentMethod, PaymentStatus } from '@sitio/shared'

@Injectable()
export class PaymentsService {
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

  private async fetchOrder(orderId: number) {
    try {
      const response = await axios.get(
        `${this.orderServiceUrl}/orders/${orderId}`,
      )
      return response.data
    } catch (error) {
      throw new NotFoundException(`Order ${orderId} not found`)
    }
  }

  async createPixPayment(orderId: number): Promise<PaymentEntity> {
    // Verificar se já existe pagamento para este pedido
    const existingPayment = await this.paymentRepository.findOne({
      where: { orderId, method: 'pix' },
    })

    if (existingPayment && existingPayment.status === 'paid') {
      throw new BadRequestException('Order already paid')
    }

    // Buscar pedido
    const order = await this.fetchOrder(orderId)

    if (order.paymentStatus === 'paid') {
      throw new BadRequestException('Order already paid')
    }

    // Criar pagamento no Mercado Pago
    const paymentData = {
      transaction_amount: parseFloat(order.total),
      description: `Pedido #${order.id} - Sítio Multitrem`,
      payment_method_id: 'pix',
      payer: {
        email: `${order.visitorId}@sitio-multitrem.com`,
        first_name: order.customerName.split(' ')[0] || order.customerName,
        last_name: order.customerName.split(' ').slice(1).join(' ') || '',
      },
    }

    try {
      const mpPayment = await this.mercadoPago.create({ body: paymentData })

      // Extrair dados do Pix
      const pointOfInteraction =
        mpPayment.point_of_interaction?.transaction_data
      const qrCode = pointOfInteraction?.qr_code
      const qrCodeBase64 = pointOfInteraction?.qr_code_base64
      const expirationDate = mpPayment.date_of_expiration
        ? new Date(mpPayment.date_of_expiration)
        : null

      // Salvar payment
      let payment: PaymentEntity

      if (existingPayment) {
        existingPayment.mercadoPagoId = mpPayment.id?.toString() || null
        existingPayment.pixQrCode = qrCode || null
        existingPayment.pixQrCodeBase64 = qrCodeBase64 || null
        existingPayment.expiresAt = expirationDate
        existingPayment.status = 'processing' as PaymentStatus
        payment = await this.paymentRepository.save(existingPayment)
      } else {
        payment = this.paymentRepository.create({
          orderId,
          method: 'pix' as PaymentMethod,
          status: 'processing' as PaymentStatus,
          amount: parseFloat(order.total),
          mercadoPagoId: mpPayment.id?.toString() || null,
          pixQrCode: qrCode || null,
          pixQrCodeBase64: qrCodeBase64 || null,
          expiresAt: expirationDate,
        })
        payment = await this.paymentRepository.save(payment)
      }

      return payment
    } catch (error: any) {
      throw new BadRequestException(
        `Mercado Pago error: ${error.message || 'Unknown error'}`,
      )
    }
  }

  async createBoletoPayment(orderId: number): Promise<PaymentEntity> {
    // Verificar se já existe pagamento
    const existingPayment = await this.paymentRepository.findOne({
      where: { orderId, method: 'boleto' },
    })

    if (existingPayment && existingPayment.status === 'paid') {
      throw new BadRequestException('Order already paid')
    }

    // Buscar pedido
    const order = await this.fetchOrder(orderId)

    if (order.paymentStatus === 'paid') {
      throw new BadRequestException('Order already paid')
    }

    // Criar pagamento no Mercado Pago
    const paymentData = {
      transaction_amount: parseFloat(order.total),
      description: `Pedido #${order.id} - Sítio Multitrem`,
      payment_method_id: 'bolbradesco',
      payer: {
        email: `${order.visitorId}@sitio-multitrem.com`,
        first_name: order.customerName.split(' ')[0] || order.customerName,
        last_name: order.customerName.split(' ').slice(1).join(' ') || '',
        identification: {
          type: 'CPF',
          number: '00000000000', // TODO: coletar CPF do cliente
        },
      },
    }

    try {
      const mpPayment = await this.mercadoPago.create({ body: paymentData })

      // Extrair dados do boleto
      const transactionDetails = mpPayment.transaction_details
      const externalResourceUrl = transactionDetails?.external_resource_url
      // Boleto barcode pode estar em diferentes lugares dependendo da resposta
      const barcodeContent = (mpPayment as any).barcode?.content || 
                           (mpPayment as any).transaction_details?.barcode ||
                           null
      const expirationDate = mpPayment.date_of_expiration
        ? new Date(mpPayment.date_of_expiration)
        : null

      // Salvar payment
      let payment: PaymentEntity

      if (existingPayment) {
        existingPayment.mercadoPagoId = mpPayment.id?.toString() || null
        existingPayment.boletoUrl = externalResourceUrl || null
        existingPayment.boletoBarcode = barcodeContent
        existingPayment.expiresAt = expirationDate
        existingPayment.status = 'processing' as PaymentStatus
        payment = await this.paymentRepository.save(existingPayment)
      } else {
        payment = this.paymentRepository.create({
          orderId,
          method: 'boleto' as PaymentMethod,
          status: 'processing' as PaymentStatus,
          amount: parseFloat(order.total),
          mercadoPagoId: mpPayment.id?.toString() || null,
          boletoUrl: externalResourceUrl || null,
          boletoBarcode: barcodeContent,
          expiresAt: expirationDate,
        })
        payment = await this.paymentRepository.save(payment)
      }

      return payment
    } catch (error: any) {
      throw new BadRequestException(
        `Mercado Pago error: ${error.message || 'Unknown error'}`,
      )
    }
  }

  async findOne(id: number): Promise<PaymentEntity> {
    const payment = await this.paymentRepository.findOne({
      where: { id },
    })

    if (!payment) {
      throw new NotFoundException(`Payment ${id} not found`)
    }

    return payment
  }

  async findByOrder(orderId: number): Promise<PaymentEntity | null> {
    return this.paymentRepository.findOne({
      where: { orderId },
      order: { createdAt: 'DESC' },
    })
  }

  async updateStatus(
    id: number,
    status: PaymentStatus,
    mercadoPagoId?: string,
  ): Promise<PaymentEntity> {
    const payment = await this.findOne(id)
    payment.status = status

    if (status === 'paid') {
      payment.paidAt = new Date()
    }

    if (mercadoPagoId) {
      payment.mercadoPagoId = mercadoPagoId
    }

    return this.paymentRepository.save(payment)
  }
}

