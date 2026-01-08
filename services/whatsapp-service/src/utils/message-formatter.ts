/**
 * Formata mensagens para WhatsApp
 * Converte markdown para formatação do WhatsApp
 */
export class MessageFormatter {
  /**
   * Converte markdown para formatação do WhatsApp
   * - **texto** → *texto* (negrito)
   * - _texto_ → _texto_ (itálico)
   * - Listas com bullets → emojis
   */
  static formatForWhatsApp(text: string): string {
    let formatted = text

    // Converter markdown bold (**texto**) para WhatsApp bold (*texto*)
    formatted = formatted.replace(/\*\*(.+?)\*\*/g, '*$1*')

    // Manter itálico (_texto_)
    // Já está no formato correto

    // Converter listas com bullets para emojis
    formatted = formatted.replace(/^[-•]\s+/gm, '• ')

    // Converter listas numeradas para emojis
    formatted = formatted.replace(/^\d+\.\s+/gm, '• ')

    // Remover quebras de linha excessivas
    formatted = formatted.replace(/\n{3,}/g, '\n\n')

    return formatted.trim()
  }

  /**
   * Detecta se a mensagem contém código Pix
   */
  static hasPixCode(text: string): boolean {
    return /pix|qr.?code|pagamento/i.test(text) && /[0-9]{26,}/.test(text)
  }

  /**
   * Detecta se a mensagem lista produtos
   */
  static isProductList(text: string): boolean {
    return /produtos?|hortaliças?|ovos|kits?|combos?/i.test(text) && 
           (/\n.*R\$/m.test(text) || /•|[-*]/.test(text))
  }

  /**
   * Detecta se a mensagem pede confirmação
   */
  static isConfirmationRequest(text: string): boolean {
    return /confirmar|finalizar|pagar|prosseguir|continuar/i.test(text) &&
           /\?/.test(text)
  }

  /**
   * Extrai código Pix da mensagem
   */
  static extractPixCode(text: string): string | null {
    const match = text.match(/([0-9]{26,})/)
    return match ? match[1] : null
  }
}













