import type { Order, OrderItem } from "./types";

export function reais(value: number): string {
  return value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatMoney(value: number): string {
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export function qtdCobrada(item: OrderItem): number {
  return item.qtdEntregue == null ? item.qtd : item.qtdEntregue;
}

export function lineGross(item: OrderItem): number {
  return qtdCobrada(item) * (item.valor || 0);
}

export function lineDiscount(item: OrderItem): number {
  const gross = lineGross(item);
  const fixed = qtdCobrada(item) * (item.desconto || 0);
  const percent = gross * ((item.descontoPercentual || 0) / 100);
  return fixed + percent;
}

export function lineOrderedTotal(item: OrderItem): number {
  const gross = item.qtd * (item.valor || 0);
  const fixed = item.qtd * (item.desconto || 0);
  const percent = gross * ((item.descontoPercentual || 0) / 100);
  return Math.max(0, gross - fixed - percent);
}

export function lineTotal(item: OrderItem): number {
  return Math.max(0, lineGross(item) - lineDiscount(item));
}

export function orderSubtotal(order: Order): number {
  return order.itens.reduce((sum, item) => sum + lineTotal(item), 0);
}

export function orderDiscountValue(order: Order): number {
  return orderSubtotal(order) * ((order.desconto || 0) / 100);
}

export function orderTotal(order: Order): number {
  return Math.max(0, orderSubtotal(order) - orderDiscountValue(order));
}

export function orderOrderedTotal(order: Order): number {
  const subtotal = order.itens.reduce((sum, item) => sum + lineOrderedTotal(item), 0);
  return Math.max(0, subtotal - subtotal * ((order.desconto || 0) / 100));
}

export function qtyLabel(item: OrderItem): string {
  const qty = String(item.qtd).padStart(2, "0");
  return item.tipo ? `${qty} ${item.tipo}` : qty;
}

export function discountLabel(item: OrderItem): string {
  const parts: string[] = [];
  if (item.desconto) parts.push(formatMoney(item.desconto));
  if (item.descontoPercentual) parts.push(`${item.descontoPercentual}%`);
  return parts.join(" + ");
}

export function ordemDeImpressao(orders: Order[], onlyWithQty: boolean): number[] {
  const ranked = orders.map((order, index) => ({
    index,
    n: order.itens.filter((item) => !onlyWithQty || item.qtd > 0 || item.quantidadeEmBranco).length,
  }));
  ranked.sort((a, b) => a.n - b.n || a.index - b.index);
  const ordem = orders.map(() => 0);
  ranked.forEach((item, posicao) => {
    ordem[item.index] = posicao;
  });
  return ordem;
}
