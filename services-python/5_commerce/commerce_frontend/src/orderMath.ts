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

/** Quantidade fisicamente entregue nesta nota. */
export function qtdCobrada(item: OrderItem): number {
  return item.qtdEntregue == null ? item.qtd : item.qtdEntregue;
}

export function faltaDoItem(item: OrderItem): number {
  return Math.max(0, item.qtd - qtdCobrada(item));
}

function foldObs(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Observação "Pago" / "já pagas": reagendamento só entrega, sem nova cobrança. */
export function itemJaPago(observacao?: string): boolean {
  return /\b(ja\s+)?pag[oa]s?\b/.test(foldObs(observacao || ""));
}

/**
 * Quantidade que entra no valor da nota.
 * Entregue + reagendada quando "Já pago" na origem: cobra agora e o outro dia só entrega.
 * No destino (reagendado já pago): quantidade faturada é zero.
 */
export function qtdFaturada(item: OrderItem): number {
  if ((item.origemId || item.origemData) && itemJaPago(item.observacao)) return 0;
  const entregue = qtdCobrada(item);
  if (!item.reagendar || !itemJaPago(item.observacao)) return entregue;
  const reagendada = Math.min(Math.max(0, item.qtdReagendada || 0), faltaDoItem(item));
  return entregue + reagendada;
}

export function marcarComoPago(observacao?: string): string {
  if (itemJaPago(observacao)) return (observacao || "").trim() || "Pago";
  const limpo = (observacao || "").trim();
  return limpo ? `${limpo} · Pago` : "Pago";
}

export function limparMarcaDePago(observacao?: string): string | undefined {
  const limpo = (observacao || "")
    .replace(/\s*[·\-–]?\s*\bj[áa]\s+pag[oa]s?\b/gi, " ")
    .replace(/\s*[·\-–]?\s*\bpag[oa]s?\b/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
  return limpo || undefined;
}

export function lineGross(item: OrderItem): number {
  return qtdFaturada(item) * (item.valor || 0);
}

export function lineDiscount(item: OrderItem): number {
  const gross = lineGross(item);
  const fixed = qtdFaturada(item) * (item.desconto || 0);
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

function dataDaNota(data: string, hoje: Date): Date | null {
  const match = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(data.trim());
  if (!match) return null;
  const dia = Number(match[1]);
  const mes = Number(match[2]);
  let ano = match[3] ? Number(match[3]) : hoje.getFullYear();
  if (ano < 100) ano += 2000;
  const nota = new Date(ano, mes - 1, dia, 12);
  if (nota.getFullYear() !== ano || nota.getMonth() !== mes - 1 || nota.getDate() !== dia) return null;
  return nota;
}

function meioDia(data: Date): Date {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate(), 12);
}

function textoData(data: Date): string {
  const dia = String(data.getDate()).padStart(2, "0");
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  return `${dia}/${mes}/${data.getFullYear()}`;
}

/**
 * O reagendamento vai para o dia seguinte ao pedido.
 * Se esse dia já chegou, a entrega fica hoje: a falta de ontem sai hoje, não amanhã.
 */
export function diaDoReagendamento(dataPedido: string, hoje = new Date()): string {
  const hojeMeio = meioDia(hoje);
  const nota = dataDaNota(dataPedido, hoje);
  const seguinte = nota ? new Date(nota.getFullYear(), nota.getMonth(), nota.getDate(), 12) : new Date(hojeMeio);
  if (nota) seguinte.setDate(seguinte.getDate() + 1);
  if (seguinte.getTime() < hojeMeio.getTime()) return textoData(hojeMeio);
  return textoData(seguinte);
}

/**
 * Data do reagendamento: usa a marcada se houver; senão o padrão (dia seguinte ao pedido,
 * ou hoje se esse dia já passou). Não reescreve escolha explícita (ex.: amanhã).
 */
export function dataReagendadaEfetiva(dataPedido: string, marcada: string | undefined, hoje = new Date()): string {
  const sugerida = diaDoReagendamento(dataPedido, hoje);
  if (!marcada?.trim()) return sugerida;
  const salva = dataDaNota(marcada, hoje);
  if (!salva) return sugerida;
  return textoData(salva);
}

/** O dia do pedido ficou mais de um dia para trás (só informativo; não bloqueia reagendar). */
export function pedidoJaPassou(data: string, hoje = new Date()): boolean {
  const nota = dataDaNota(data, hoje);
  if (!nota) return false;
  const dia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate(), 12);
  const pedido = new Date(nota.getFullYear(), nota.getMonth(), nota.getDate(), 12);
  return Math.round((dia.getTime() - pedido.getTime()) / 86400000) > 1;
}

/** Mantido por compatibilidade nas rotas de salvar; reagendar só é bloqueado na UI se a nota estiver concluída. */
export function semReagenda(order: Order): Order {
  return order;
}

const SEMANA = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"];
const SEMANA_ROTULO = [
  "Domingo",
  "Segunda-Feira",
  "Terça-Feira",
  "Quarta-Feira",
  "Quinta-Feira",
  "Sexta-Feira",
  "Sábado",
];

/** Nome do dia da semana a partir da data da nota (DD/MM ou DD/MM/AAAA). */
export function nomeDiaSemana(data: string, hoje = new Date()): string {
  const nota = dataDaNota(data, hoje);
  if (!nota) return "";
  return SEMANA_ROTULO[nota.getDay()] || "";
}

export function ordemDeImpressao(orders: Order[]): number[] {
  const ranked = orders.map((order, index) => ({
    index,
    data: dataDaNota(order.data, new Date())?.getTime() ?? Number.POSITIVE_INFINITY,
    cliente: order.cliente.trim().toLocaleLowerCase("pt-BR"),
  }));
  ranked.sort((a, b) => a.data - b.data || a.cliente.localeCompare(b.cliente, "pt-BR") || a.index - b.index);
  const ordem = orders.map(() => 0);
  ranked.forEach((item, posicao) => {
    ordem[item.index] = posicao;
  });
  return ordem;
}

export type LinhaCobranca = { chave: string; rotulo: string; total: number };
export type BlocoCobranca = { cliente: string; linhas: LinhaCobranca[]; total: number };

function linhasDoCliente(orders: Order[]): LinhaCobranca[] {
  const porDia = new Map<string, { nota: Date | null; total: number }>();
  for (const order of orders) {
    const nota = dataDaNota(order.data, new Date());
    const chave = nota
      ? `${nota.getFullYear()}-${String(nota.getMonth() + 1).padStart(2, "0")}-${String(nota.getDate()).padStart(2, "0")}`
      : "sem-data";
    const atual = porDia.get(chave) ?? { nota, total: 0 };
    atual.total += orderTotal(order);
    porDia.set(chave, atual);
  }
  return [...porDia.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([chave, item]) => ({
      chave,
      rotulo: item.nota
        ? `${String(item.nota.getDate()).padStart(2, "0")}/${String(item.nota.getMonth() + 1).padStart(2, "0")} — ${SEMANA[item.nota.getDay()]}`
        : "Sem data",
      total: item.total,
    }));
}

/** Uma soma do valor da nota por dia, separada por cliente. */
export function resumoCobranca(orders: Order[]): BlocoCobranca[] {
  const grupos = new Map<string, Order[]>();
  for (const order of orders) {
    if (order.tipo === "compra") continue;
    const nome = order.cliente.trim() || "Sem cliente";
    const lista = grupos.get(nome) ?? [];
    lista.push(order);
    grupos.set(nome, lista);
  }
  return [...grupos.entries()]
    .sort((a, b) => a[0].localeCompare(b[0], "pt-BR"))
    .map(([cliente, lista]) => {
      const linhas = linhasDoCliente(lista);
      return { cliente, linhas, total: linhas.reduce((soma, linha) => soma + linha.total, 0) };
    });
}

export type LinhaContabilidade = {
  chave: string;
  dataIso: string;
  dataCurta: string;
  dia: string;
  periodo: string;
  recebeu: string;
  palitos: number;
  salsas: number;
  valor: number;
  rowspan: number;
  mostrarData: boolean;
};

export type BlocoContabilidade = {
  cliente: string;
  precoPalito: number;
  precoSalsa: number;
  precoPalitoComDesconto: number;
  precoSalsaComDesconto: number;
  temSalsa: boolean;
  linhas: LinhaContabilidade[];
  totalPalitos: number;
  totalSalsas: number;
  /** Soma palitos×preço + salsas×preço (tabela cheia). */
  brutoTabela: number;
  /** Diferença entre tabela cheia e o total cobrado nas notas. */
  desconto: number;
  /** Percentual do desconto sobre a tabela cheia. */
  percentualDesconto: number;
  total: number;
};

function ehPalito(item: OrderItem): boolean {
  const tipo = foldObs(item.tipo || "");
  const prod = foldObs(item.produto);
  return tipo.includes("palito") || /\bpal(ito)?s?\b/.test(prod);
}

function ehSalsa(item: OrderItem): boolean {
  return /\bsals(a|inha)s?\b/.test(foldObs(item.produto));
}

function periodoDaObs(observacao?: string): string {
  const t = foldObs(observacao || "");
  if (/(^| )manha( |$)/.test(` ${t} `)) return "Manhã";
  if (/(^| )noite( |$)/.test(` ${t} `)) return "Noite";
  return "—";
}

/** Quem recebeu: prioriza nome entre parênteses; ignora manhã/noite e restos como "a"/"à". */
function recebeuDaObs(observacao?: string): string {
  const texto = (observacao || "").trim();
  if (!texto) return "Não informado";

  const nomes = [...texto.matchAll(/\(([^)]+)\)/g)]
    .map((m) => m[1].replace(/\s+/g, " ").trim())
    .filter((nome) => {
      if (!nome) return false;
      const fold = foldObs(nome);
      return fold !== "manha" && fold !== "noite" && fold.length > 1;
    });
  if (nomes.length) return nomes.join(", ");

  const limpo = texto
    .replace(/\([^)]*\)/g, " ")
    .replace(/à/gi, " ")
    .replace(/manh[ãa]/gi, " ")
    .replace(/noite/gi, " ")
    .replace(/[·\-–|,;/:]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const fold = foldObs(limpo);
  if (!fold || fold.length <= 1 || fold === "a" || fold === "o" || fold === "de") {
    return "Não informado";
  }
  return limpo;
}

function precoMaisComum(valores: number[]): number {
  const mapa = new Map<number, number>();
  for (const valor of valores) {
    if (!(valor > 0)) continue;
    mapa.set(valor, (mapa.get(valor) || 0) + 1);
  }
  let melhor = 0;
  let vezes = 0;
  for (const [valor, qtd] of mapa) {
    if (qtd > vezes) {
      melhor = valor;
      vezes = qtd;
    }
  }
  return melhor;
}

/** Preço cobrado na boleta: tabela menos o desconto da linha e o desconto do pedido. */
function precoCobrado(item: OrderItem, descontoPedido: number): number {
  const tabela = item.valor || 0;
  const fixo = item.desconto || 0;
  const percentual = (item.descontoPercentual || 0) / 100;
  const depoisDaLinha = tabela - fixo - tabela * percentual;
  const pedido = (descontoPedido || 0) / 100;
  const liquido = depoisDaLinha * (1 - pedido);
  return Math.round(Math.max(0, liquido) * 100) / 100;
}

function ordemPeriodo(periodo: string): number {
  if (periodo === "Manhã") return 0;
  if (periodo === "Noite") return 1;
  return 2;
}

function qtdTexto(qtd: number): string {
  if (!(qtd > 0)) return "—";
  if (Number.isInteger(qtd)) return String(qtd);
  return String(qtd).replace(".", ",");
}

export { qtdTexto as qtdContabilidade };

/** Relatório CONTABILIDADE: data, período, palitos/salsas e valor — por cliente. */
export function contabilidadeCobranca(orders: Order[]): BlocoContabilidade[] {
  const grupos = new Map<string, Order[]>();
  for (const order of orders) {
    if (order.tipo === "compra") continue;
    const nome = order.cliente.trim() || "Sem cliente";
    const lista = grupos.get(nome) ?? [];
    lista.push(order);
    grupos.set(nome, lista);
  }
  return [...grupos.entries()]
    .sort((a, b) => a[0].localeCompare(b[0], "pt-BR"))
    .map(([cliente, lista]) => {
      const precosPalito: number[] = [];
      const precosSalsa: number[] = [];
      const cobradosPalito: number[] = [];
      const cobradosSalsa: number[] = [];
      const brutas = lista.map((order, index) => {
        let palitos = 0;
        let salsas = 0;
        for (const item of order.itens) {
          const qtd = qtdFaturada(item);
          if (!(qtd > 0)) continue;
          if (ehSalsa(item)) {
            salsas += qtd;
            precosSalsa.push(item.valor || 0);
            cobradosSalsa.push(precoCobrado(item, order.desconto));
          } else if (ehPalito(item)) {
            palitos += qtd;
            precosPalito.push(item.valor || 0);
            cobradosPalito.push(precoCobrado(item, order.desconto));
          }
        }
        const nota = dataDaNota(order.data, new Date());
        const dataIso = nota
          ? `${nota.getFullYear()}-${String(nota.getMonth() + 1).padStart(2, "0")}-${String(nota.getDate()).padStart(2, "0")}`
          : `sem-${index}`;
        return {
          chave: order.id || `${dataIso}-${index}`,
          dataIso,
          dataCurta: nota
            ? `${String(nota.getDate()).padStart(2, "0")}/${String(nota.getMonth() + 1).padStart(2, "0")}`
            : order.data.trim() || "—",
          dia: nota ? SEMANA_ROTULO[nota.getDay()] : "—",
          periodo: periodoDaObs(order.observacao),
          recebeu: recebeuDaObs(order.observacao),
          palitos,
          salsas,
          valor: orderTotal(order),
        };
      });
      brutas.sort(
        (a, b) =>
          a.dataIso.localeCompare(b.dataIso) ||
          ordemPeriodo(a.periodo) - ordemPeriodo(b.periodo) ||
          a.chave.localeCompare(b.chave),
      );
      const linhas: LinhaContabilidade[] = [];
      let i = 0;
      while (i < brutas.length) {
        let rowspan = 1;
        while (i + rowspan < brutas.length && brutas[i + rowspan].dataIso === brutas[i].dataIso) rowspan += 1;
        for (let j = 0; j < rowspan; j += 1) {
          const item = brutas[i + j];
          linhas.push({
            ...item,
            rowspan,
            mostrarData: j === 0,
          });
        }
        i += rowspan;
      }
      const totalPalitos = linhas.reduce((soma, linha) => soma + linha.palitos, 0);
      const totalSalsas = linhas.reduce((soma, linha) => soma + linha.salsas, 0);
      const precoPalito = precoMaisComum(precosPalito);
      const precoSalsa = precoMaisComum(precosSalsa);
      const total = linhas.reduce((soma, linha) => soma + linha.valor, 0);
      const brutoTabela = totalPalitos * precoPalito + totalSalsas * precoSalsa;
      const desconto = Math.max(0, Math.round((brutoTabela - total) * 100) / 100);
      const percentualDesconto =
        brutoTabela > 0.009 ? Math.round((desconto / brutoTabela) * 10000) / 100 : 0;
      return {
        cliente,
        precoPalito,
        precoSalsa,
        precoPalitoComDesconto: precoMaisComum(cobradosPalito) || precoPalito,
        precoSalsaComDesconto: precoMaisComum(cobradosSalsa) || precoSalsa,
        temSalsa: totalSalsas > 0 || precosSalsa.some((v) => v > 0),
        linhas,
        totalPalitos,
        totalSalsas,
        brutoTabela,
        desconto,
        percentualDesconto,
        total,
      };
    });
}
