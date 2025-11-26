// Máscara de telefone: (99) 99999-9999
export function maskPhone(value: string): string {
  const numbers = value.replace(/\D/g, '')
  if (numbers.length <= 10) {
    return numbers
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2')
  }
  return numbers
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
}

// Máscara de CEP: 99999-999
export function maskCEP(value: string): string {
  const numbers = value.replace(/\D/g, '')
  return numbers.replace(/(\d{5})(\d)/, '$1-$2')
}

// Remove máscaras
export function unmask(value: string): string {
  return value.replace(/\D/g, '')
}

