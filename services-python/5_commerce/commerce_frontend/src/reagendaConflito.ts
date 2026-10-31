import { consultarBoletas } from "./cadastroApi";
import { dataReagendadaEfetiva, faltaDoItem, limparMarcaDePago } from "./orderMath";
import type { OrderItem } from "./types";

export type LinhaDestinoConflito = {
  nome: string;
  data: string;
  produto: string;
  qtde: number;
  preco: number;
  total: number;
};

export type ResultadoConflito =
  | { tipo: "sem-cliente" }
  | { tipo: "livre" }
  | { tipo: "conflito"; destino: LinhaDestinoConflito };

export type ReagendaConduta = "somar" | "substituir";

/** Nome sem formato (unidade/maço) — alinhado ao backend `_chave_produto`. */
function foldProduto(valor: string): string {
  const semFormato = valor.replace(/\s*\([^)]*\)\s*$/g, "").trim() || valor;
  return semFormato
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function isoDaDataNota(data: string): string {
  const texto = data.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) return texto;
  const match = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(texto);
  if (!match) return "";
  const dia = match[1].padStart(2, "0");
  const mes = match[2].padStart(2, "0");
  let ano = match[3] ? Number(match[3]) : new Date().getFullYear();
  if (ano < 100) ano += 2000;
  return `${ano}-${mes}-${dia}`;
}

/** Navegar o mês no input type=date costuma emitir onChange com dia 1. */
export function pareceNavegacaoMes(anterior: string | undefined, nova: string): boolean {
  const parse = (texto: string) => {
    const iso = isoDaDataNota(texto);
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
    if (!m) return null;
    return { y: Number(m[1]), m: Number(m[2]), d: Number(m[3]) };
  };
  const de = anterior?.trim() ? parse(anterior) : null;
  const para = parse(nova);
  if (!para || para.d !== 1 || !de) return false;
  return de.y !== para.y || de.m !== para.m;
}

/**
 * Consulta se o produto já existe na data destino.
 * Soma qtde se houver várias linhas do mesmo produto.
 * Ignora linhas trazidas desta própria origem.
 */
export async function verificarConflito(
  clienteId: number | undefined,
  dataDestino: string,
  produto: string,
  origemId?: string,
): Promise<ResultadoConflito> {
  if (!clienteId) return { tipo: "sem-cliente" };
  if (!dataDestino.trim() || !produto.trim()) return { tipo: "livre" };
  const iso = isoDaDataNota(dataDestino);
  if (!iso) return { tipo: "livre" };
  try {
    const extrato = await consultarBoletas(iso, iso, clienteId);
    const chave = foldProduto(produto);
    let qtde = 0;
    let preco = 0;
    let total = 0;
    let nome = "";
    let data = dataDestino;
    let nomeProduto = produto;
    let achou = false;
    for (const conta of extrato.clientes) {
      for (const pedido of conta.pedidos) {
        if (origemId && pedido.id === origemId) continue;
        for (const item of pedido.itens) {
          if (origemId && item.origem_id === origemId) continue;
          if (foldProduto(item.produto) !== chave) continue;
          if (!(item.qtd > 0)) continue;
          achou = true;
          qtde += item.qtd;
          preco = item.valor || preco;
          total += item.total || 0;
          nome = conta.nome.trim() || nome || "—";
          data = pedido.data.trim() || data;
          nomeProduto = item.produto.trim() || nomeProduto;
        }
      }
    }
    if (!achou) return { tipo: "livre" };
    return {
      tipo: "conflito",
      destino: { nome: nome || "—", data, produto: nomeProduto, qtde, preco, total },
    };
  } catch {
    return { tipo: "livre" };
  }
}

export function patchDesmarcarReagenda(item: OrderItem): Partial<OrderItem> {
  return {
    reagendar: false,
    qtdReagendada: undefined,
    dataReagendada: undefined,
    reagendaConduta: undefined,
    observacao: limparMarcaDePago(item.observacao),
  };
}

export function patchMarcarReagenda(
  item: OrderItem,
  dataPedido: string,
  dataDestino?: string,
): Partial<OrderItem> {
  const falta = faltaDoItem(item);
  const atual = item.qtdReagendada && item.qtdReagendada > 0 ? Math.min(item.qtdReagendada, falta) : falta;
  return {
    reagendar: true,
    qtdReagendada: atual,
    dataReagendada: dataReagendadaEfetiva(dataPedido, dataDestino ?? item.dataReagendada),
    reagendaConduta: undefined,
  };
}

export function textoAvisoReagenda(
  ligado: boolean,
  item: OrderItem,
  dataPedido: string,
  patch: Partial<OrderItem>,
  conduta?: ReagendaConduta,
): string {
  const nome = item.produto.trim() || "Item";
  if (!ligado) return `${nome}: reagendamento desmarcado.`;
  const qtd = patch.qtdReagendada ?? faltaDoItem(item);
  const data = dataReagendadaEfetiva(dataPedido, patch.dataReagendada);
  const acao =
    conduta === "somar"
      ? " (somar na boleta do destino)"
      : conduta === "substituir"
        ? " (substituir na boleta do destino)"
        : "";
  return `${nome}: ${qtd} marcado(s) para ${data}${acao}. A boleta do destino só é criada/atualizada ao gravar em Atualizar pedidos.`;
}
