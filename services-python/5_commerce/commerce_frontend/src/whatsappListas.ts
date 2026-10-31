import type { Order } from "./types";
import { quantidadeColheita } from "./colheitaMath";

function qtdItem(item: Order["itens"][number]): number {
  if (item.qtdEntregue != null && item.qtdEntregue > 0) return item.qtdEntregue;
  return item.qtd > 0 ? item.qtd : 0;
}

/** Texto plano da lista de pedidos (boletas na tela) para WhatsApp. */
export function textoListaPedidos(orders: Order[]): string {
  const vendas = orders.filter((order) => order.tipo !== "compra");
  if (!vendas.length) return "";
  const blocos: string[] = ["Lista de pedidos"];
  const datas = [...new Set(vendas.map((o) => o.data.trim()).filter(Boolean))];
  if (datas.length) blocos.push(datas.join(", "));
  blocos.push("");
  for (const order of vendas) {
    const quem = order.cliente.trim() || "Cliente";
    const onde = order.endereco.trim();
    blocos.push(onde ? `${quem} — ${onde}` : quem);
    const itens = order.itens.filter((item) => qtdItem(item) > 0 && item.produto.trim());
    if (!itens.length) {
      blocos.push("  (sem itens)");
    } else {
      for (const item of itens) {
        blocos.push(`  ${quantidadeColheita(qtdItem(item))} ${item.produto.trim()}`);
      }
    }
    blocos.push("");
  }
  return blocos.join("\n").trim();
}

export function periodoDasBoletas(orders: Order[]): string {
  const datas = [
    ...new Set(
      orders
        .filter((order) => order.tipo !== "compra")
        .map((order) => order.data.trim())
        .filter(Boolean),
    ),
  ].sort();
  return datas.join(", ");
}

function isoDaDataNota(data: string): string {
  const bruto = data.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(bruto)) return bruto;
  const match = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(bruto);
  if (!match) return "";
  const dia = match[1].padStart(2, "0");
  const mes = match[2].padStart(2, "0");
  let ano = match[3] ? Number(match[3]) : new Date().getFullYear();
  if (ano < 100) ano += 2000;
  return `${ano}-${mes}-${dia}`;
}

/** Data ISO mais comum nas boletas (para carregar rota-do-dia). */
export function dataPrincipalBoletas(orders: Order[]): string {
  const contagem = new Map<string, number>();
  for (const order of orders) {
    if (order.tipo === "compra") continue;
    const iso = isoDaDataNota(order.data);
    if (!iso) continue;
    contagem.set(iso, (contagem.get(iso) || 0) + 1);
  }
  let melhor = "";
  let max = 0;
  for (const [data, n] of contagem) {
    if (n > max) {
      max = n;
      melhor = data;
    }
  }
  if (melhor) return melhor;
  const hoje = new Date();
  const m = String(hoje.getMonth() + 1).padStart(2, "0");
  const d = String(hoje.getDate()).padStart(2, "0");
  return `${hoje.getFullYear()}-${m}-${d}`;
}
