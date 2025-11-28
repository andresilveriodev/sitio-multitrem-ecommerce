import { ChatCompletionTool } from 'openai/resources/chat/completions'

export const FUNCTION_DEFINITIONS: ChatCompletionTool[] = [
  {
    type: 'function',
    function: {
      name: 'list_products',
      description: 'Lista produtos disponíveis, opcionalmente por categoria',
      parameters: {
        type: 'object',
        properties: {
          category: {
            type: 'string',
            enum: ['hortalicas', 'ovos', 'kits', 'combos'],
            description: 'Categoria do produto (opcional)',
          },
        },
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'add_to_cart',
      description: 'Adiciona produto ao carrinho do cliente',
      parameters: {
        type: 'object',
        properties: {
          productId: {
            type: 'number',
            description: 'ID do produto',
          },
          quantity: {
            type: 'number',
            description: 'Quantidade a adicionar',
          },
          selectedItems: {
            type: 'array',
            items: { type: 'string' },
            description: 'Itens selecionados (para kits)',
          },
        },
        required: ['productId', 'quantity'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'remove_from_cart',
      description: 'Remove produto do carrinho',
      parameters: {
        type: 'object',
        properties: {
          productId: {
            type: 'number',
            description: 'ID do produto a remover',
          },
        },
        required: ['productId'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'view_cart',
      description: 'Mostra o carrinho atual do cliente',
      parameters: {
        type: 'object',
        properties: {},
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'check_delivery_slots',
      description: 'Verifica dias disponíveis para entrega (quarta a sábado)',
      parameters: {
        type: 'object',
        properties: {},
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'create_order',
      description: 'Cria o pedido com data de entrega e dados do cliente',
      parameters: {
        type: 'object',
        properties: {
          deliveryDate: {
            type: 'string',
            description: 'Data de entrega no formato YYYY-MM-DD',
          },
          customerName: {
            type: 'string',
            description: 'Nome completo do cliente',
          },
          customerPhone: {
            type: 'string',
            description: 'Telefone do cliente',
          },
          customerAddress: {
            type: 'string',
            description: 'Endereço completo para entrega',
          },
        },
        required: ['deliveryDate', 'customerName', 'customerPhone', 'customerAddress'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'generate_payment_link',
      description: 'Gera link/QR de pagamento (Pix ou Boleto)',
      parameters: {
        type: 'object',
        properties: {
          orderId: {
            type: 'number',
            description: 'ID do pedido',
          },
          method: {
            type: 'string',
            enum: ['pix', 'boleto'],
            description: 'Método de pagamento',
          },
        },
        required: ['orderId', 'method'],
      },
    },
  },
]

export type FunctionName =
  | 'list_products'
  | 'add_to_cart'
  | 'remove_from_cart'
  | 'view_cart'
  | 'check_delivery_slots'
  | 'create_order'
  | 'generate_payment_link'

