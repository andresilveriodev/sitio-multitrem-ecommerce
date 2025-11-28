import { Injectable, Inject } from '@nestjs/common'
import { ConfigService } from '@nestjs/config'
import axios, { AxiosInstance } from 'axios'
import { FunctionName } from './functions.registry'

@Injectable()
export class ExecutorService {
  private readonly productServiceUrl: string
  private readonly cartServiceUrl: string
  private readonly orderServiceUrl: string
  private readonly paymentServiceUrl: string

  constructor(private readonly configService: ConfigService) {
    this.productServiceUrl =
      configService.get<string>('PRODUCT_SERVICE_URL') ||
      'http://localhost:3001'
    this.cartServiceUrl =
      configService.get<string>('CART_SERVICE_URL') || 'http://localhost:3002'
    this.orderServiceUrl =
      configService.get<string>('ORDER_SERVICE_URL') ||
      'http://localhost:3003'
    this.paymentServiceUrl =
      configService.get<string>('PAYMENT_SERVICE_URL') ||
      'http://localhost:3004'
  }

  async executeFunction(
    functionName: FunctionName,
    params: any,
    context: { visitorId: string },
  ): Promise<any> {
    try {
      switch (functionName) {
        case 'list_products': {
          const url = params.category
            ? `${this.productServiceUrl}/products?category=${params.category}`
            : `${this.productServiceUrl}/products`
          const response = await axios.get(url)
          return {
            success: true,
            products: response.data,
          }
        }

        case 'add_to_cart': {
          const response = await axios.post(
            `${this.cartServiceUrl}/cart/${context.visitorId}/items`,
            {
              productId: params.productId,
              quantity: params.quantity,
              selectedItems: params.selectedItems,
            },
          )
          return {
            success: true,
            cart: response.data,
            message: 'Produto adicionado ao carrinho',
          }
        }

        case 'remove_from_cart': {
          const response = await axios.delete(
            `${this.cartServiceUrl}/cart/${context.visitorId}/items/${params.productId}`,
          )
          return {
            success: true,
            cart: response.data,
            message: 'Produto removido do carrinho',
          }
        }

        case 'view_cart': {
          const response = await axios.get(
            `${this.cartServiceUrl}/cart/${context.visitorId}`,
          )
          return {
            success: true,
            cart: response.data,
          }
        }

        case 'check_delivery_slots': {
          const response = await axios.get(
            `${this.orderServiceUrl}/delivery/slots`,
          )
          return {
            success: true,
            slots: response.data,
          }
        }

        case 'create_order': {
          // Primeiro, buscar o carrinho
          const cartResponse = await axios.get(
            `${this.cartServiceUrl}/cart/${context.visitorId}`,
          )
          const cart = cartResponse.data

          if (!cart.items || cart.items.length === 0) {
            return {
              success: false,
              error: 'Carrinho vazio',
            }
          }

          // Criar pedido
          const orderResponse = await axios.post(
            `${this.orderServiceUrl}/orders`,
            {
              visitorId: context.visitorId,
              items: cart.items,
              deliveryDate: params.deliveryDate,
              customerName: params.customerName,
              customerPhone: params.customerPhone,
              customerAddress: params.customerAddress,
            },
          )

          return {
            success: true,
            order: orderResponse.data,
            message: 'Pedido criado com sucesso',
          }
        }

        case 'generate_payment_link': {
          const response = await axios.post(
            `${this.paymentServiceUrl}/payments/${params.method}`,
            {
              orderId: params.orderId,
            },
          )
          return {
            success: true,
            payment: response.data,
            message: `Link de pagamento ${params.method} gerado`,
          }
        }

        default:
          return {
            success: false,
            error: `Função ${functionName} não implementada`,
          }
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message,
      }
    }
  }
}

