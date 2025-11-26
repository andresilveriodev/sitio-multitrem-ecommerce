import type { AIIntent } from '@/types'
import { PRODUCTS } from './mock-data'

interface CartActions {
  addItem: (product: any, quantity: number, selectedItems?: string[]) => void
  items: any[]
  total: number
}

interface AIResponse {
  content: string
  intent?: AIIntent
  action?: 'add_to_cart' | 'redirect_checkout'
  productId?: number
  quantity?: number
  selectedItems?: string[]
}

export async function simulateAIResponse(
  message: string,
  cartActions: CartActions
): Promise<AIResponse> {
  // Simular delay de digitação (1-2 segundos)
  const delay = Math.random() * 1000 + 1000
  await new Promise((resolve) => setTimeout(resolve, delay))

  const lowerMessage = message.toLowerCase().trim()

  // Saudações
  if (
    /^(oi|olá|ola|bom dia|boa tarde|boa noite|hey|hi)$/i.test(lowerMessage)
  ) {
    return {
      content:
        'Olá! 🌿 Que bom ter você aqui! Posso ajudar a montar seu pedido?',
      intent: 'greeting',
    }
  }

  // Listar produtos
  if (
    /(produtos|cardápio|cardapio|o que tem|o que vocês têm|catálogo|catalogo)/i.test(
      lowerMessage
    )
  ) {
    return {
      content:
        'Temos hortaliças fresquinhas (R$ 5 cada), ovos caipiras e kits especiais! Quer ver alguma categoria específica?',
      intent: 'list_products',
    }
  }

  // Preços
  if (/(quanto custa|preço|preços|valor|valores)/i.test(lowerMessage)) {
    const prices = `
💰 *Nossos Preços:*

🥬 *Hortaliças:* R$ 5,00 cada
   - Alface Americana, Alface Crespa, Coentro, Cebolinha, Salsa, Rúcula

🥚 *Ovos Caipiras:*
   - 12 unidades: R$ 15,00
   - 20 unidades: R$ 24,00
   - 30 unidades: R$ 35,00

🥗 *Kits:*
   - Kit 1 Pessoa (3 hortaliças): R$ 12,00
   - Kit 2 Pessoas (5 hortaliças): R$ 20,00
   - Kit 3 Pessoas (7 hortaliças): R$ 28,00
   - Kit 4 Pessoas (9 hortaliças): R$ 35,00
   - Kit 5 Pessoas (12 hortaliças): R$ 45,00

🥕 *Combos:*
   - Combo Família 2: R$ 49,50
    `.trim()

    return {
      content: prices,
      intent: 'list_products',
    }
  }

  // Adicionar ao carrinho
  const addToCartMatch = lowerMessage.match(
    /(quero|adicionar|adiciona|coloca|colocar|preciso|vou querer)\s+(\d+)?\s*(alface|coentro|cebolinha|salsa|rúcula|rucula|ovos|kit|combo)/i
  )

  if (addToCartMatch) {
    const quantity = addToCartMatch[2] ? parseInt(addToCartMatch[2]) : 1
    const productName = addToCartMatch[3]

    // Encontrar produto
    const product = PRODUCTS.find((p) =>
      p.name.toLowerCase().includes(productName.toLowerCase())
    )

    if (product) {
      cartActions.addItem(product, quantity)
      return {
        content: `Adicionei ${quantity}x ${product.name} ao seu carrinho! 🛒 Quer mais alguma coisa?`,
        intent: 'add_to_cart',
        action: 'add_to_cart',
        productId: product.id,
        quantity,
      }
    }
  }

  // Ver carrinho
  if (
    /(meu carrinho|carrinho|o que tem no carrinho|itens|pedido atual)/i.test(
      lowerMessage
    )
  ) {
    if (cartActions.items.length === 0) {
      return {
        content: 'Seu carrinho está vazio. Que tal adicionar alguns produtos? 🛒',
        intent: 'view_cart',
      }
    }

    const itemsList = cartActions.items
      .map(
        (item) =>
          `• ${item.quantity}x ${item.productName} - R$ ${item.subtotal.toFixed(2)}`
      )
      .join('\n')

    return {
      content: `🛒 *Seu Carrinho:*\n\n${itemsList}\n\n*Total: R$ ${cartActions.total.toFixed(2)}*`,
      intent: 'view_cart',
    }
  }

  // Finalizar pedido
  if (
    /(finalizar|fechar pedido|pagar|checkout|comprar|quero comprar)/i.test(
      lowerMessage
    )
  ) {
    if (cartActions.items.length === 0) {
      return {
        content:
          'Seu carrinho está vazio. Adicione produtos antes de finalizar! 🛒',
        intent: 'checkout',
      }
    }

    return {
      content: `Ótimo! Seu pedido está em R$ ${cartActions.total.toFixed(2)}. Posso gerar o link de pagamento. Qual forma prefere: Pix, Boleto ou Cartão?`,
      intent: 'checkout',
      action: 'redirect_checkout',
    }
  }

  // Entrega
  if (
    /(entrega|quando chega|quando entrega|agendar|data de entrega)/i.test(
      lowerMessage
    )
  ) {
    return {
      content:
        'Entregamos de quarta a sábado, pela manhã (8h às 12h). Quer agendar para qual dia?',
      intent: 'schedule_delivery',
    }
  }

  // Resposta padrão
  return {
    content:
      'Desculpe, só posso ajudar com pedidos e entregas. 😊 Quer ver nossos produtos?',
    intent: 'other',
  }
}

