import type { Order } from "./types";

export type LinhaColheita = {
  produto: string;
  qtd: number;
  clientes: { nome: string; qtd: number }[];
};

export function chaveColheita(produto: string): string {
  return fold(produto);
}

function fold(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .trim();
}

export function montarListaColheita(orders: Order[]): LinhaColheita[] {
  const mapa = new Map<string, LinhaColheita>();
  for (const order of orders) {
    const cliente = order.cliente.trim() || "Sem nome";
    for (const item of order.itens) {
      const produto = item.produto.trim();
      if (!produto || !(item.qtd > 0)) continue;
      const chave = chaveColheita(produto);
      let linha = mapa.get(chave);
      if (!linha) {
        linha = { produto, qtd: 0, clientes: [] };
        mapa.set(chave, linha);
      }
      linha.qtd += item.qtd;
      const quem = linha.clientes.find((c) => chaveColheita(c.nome) === chaveColheita(cliente));
      if (quem) quem.qtd += item.qtd;
      else linha.clientes.push({ nome: cliente, qtd: item.qtd });
    }
  }
  return [...mapa.values()].sort((a, b) => a.produto.localeCompare(b.produto, "pt-BR"));
}

export function quantidadeColheita(qtd: number): string {
  if (Number.isInteger(qtd)) return String(qtd).padStart(2, "0");
  return String(qtd).replace(".", ",");
}

export function qtdParaComprar(texto: string): number {
  const normal = texto.trim().replace(",", ".");
  if (!normal) return 0;
  const valor = Number(normal);
  return Number.isFinite(valor) && valor > 0 ? valor : 0;
}

/** Texto simples, um produto por linha, para colar numa mensagem. */
export function textoListaCompra(itens: { produto: string; qtd: number }[], datas: string[]): string {
  const compras = itens.filter((item) => item.qtd > 0 && item.produto.trim());
  if (!compras.length) return "";
  const cabeca = ["Lista de compras"];
  if (datas.length) cabeca.push(datas.join(", "));
  const linhas = compras.map((item) => `${quantidadeColheita(item.qtd)} ${item.produto}`);
  return [...cabeca, "", ...linhas].join("\n");
}

/** Lista de colheita (totais por produto) para WhatsApp / colheiteiros. */
export function textoListaColheita(linhas: LinhaColheita[], datas: string[]): string {
  const uteis = linhas.filter((linha) => linha.qtd > 0 && linha.produto.trim());
  if (!uteis.length) return "";
  const cabeca = ["Lista de colheita"];
  if (datas.length) cabeca.push(datas.join(", "));
  const corpo = uteis.map((linha) => `${quantidadeColheita(linha.qtd)} ${linha.produto}`);
  return [...cabeca, "", ...corpo].join("\n");
}
