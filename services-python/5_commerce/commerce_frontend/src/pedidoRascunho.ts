import type { Order } from "./types";

const CHAVE = "sitio-pedidos-rascunho";

export type RascunhoPedidos = {
  orders: Order[];
  catalog: string[];
  onlyWithQty: boolean;
  chatAberto: boolean;
  filtroCliente: string;
  filtroClienteNome: string;
  filtroDe: string;
  filtroAte: string;
};

function valido(data: unknown): data is RascunhoPedidos {
  if (!data || typeof data !== "object") return false;
  const rascunho = data as RascunhoPedidos;
  return Array.isArray(rascunho.orders);
}

export function lerRascunhoPedidos(): RascunhoPedidos | null {
  try {
    if (typeof localStorage === "undefined") return null;
    const raw = localStorage.getItem(CHAVE);
    if (!raw) return null;
    const data = JSON.parse(raw) as unknown;
    if (!valido(data)) return null;
    return {
      orders: data.orders,
      catalog: Array.isArray(data.catalog) ? data.catalog : [],
      onlyWithQty: data.onlyWithQty !== false,
      chatAberto: data.chatAberto !== false,
      filtroCliente: typeof data.filtroCliente === "string" ? data.filtroCliente : "",
      filtroClienteNome: typeof data.filtroClienteNome === "string" ? data.filtroClienteNome : "",
      filtroDe: typeof data.filtroDe === "string" ? data.filtroDe : "",
      filtroAte: typeof data.filtroAte === "string" ? data.filtroAte : "",
    };
  } catch {
    return null;
  }
}

export function gravarRascunhoPedidos(rascunho: RascunhoPedidos): void {
  try {
    if (typeof localStorage === "undefined") return;
    if (!rascunho.orders.length) {
      localStorage.removeItem(CHAVE);
      return;
    }
    localStorage.setItem(CHAVE, JSON.stringify(rascunho));
  } catch {
    /* quota / modo privado */
  }
}

export function limparRascunhoPedidos(): void {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem(CHAVE);
  } catch {
    /* ignore */
  }
}
