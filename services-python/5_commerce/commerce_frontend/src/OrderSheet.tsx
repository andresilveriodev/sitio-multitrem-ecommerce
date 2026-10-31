import { Fragment, useEffect, useId, useMemo, useRef, useState, type CSSProperties, type FocusEvent, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { Cliente, Lista } from "./cadastroApi";
import { PedidoIgualPopup } from "./PedidoIgualPopup";
import type { Order, OrderItem } from "./types";
import { dataReagendadaEfetiva, diaDoReagendamento, discountLabel, faltaDoItem, formatMoney, itemJaPago, limparMarcaDePago, lineTotal, marcarComoPago, nomeDiaSemana, orderDiscountValue, orderSubtotal, orderTotal, qtdCobrada, reais } from "./orderMath";
import {
  isoDaDataNota,
  pareceNavegacaoMes,
  patchDesmarcarReagenda,
  patchMarcarReagenda,
  textoAvisoReagenda,
  verificarConflito,
  type LinhaDestinoConflito,
  type ReagendaConduta,
} from "./reagendaConflito";

type ConflitoReagenda = {
  destino: LinhaDestinoConflito;
  onSomar: () => void;
  onSubstituir: () => void;
  onMudarDia: () => void;
  onCancelar: () => void;
};

type ResultadoCopia = { status: "ok" } | { status: "ja-existe"; pedido: Order };

type Props = {
  order: Order;
  catalog: string[];
  clientes: Cliente[];
  listas?: Lista[];
  onlyWithQty: boolean;
  ordemImpressao: number;
  onChange: (order: Order) => void;
  onCliente: (nome: string, commit: boolean) => void;
  onFechar: () => void;
  onExcluir: () => Promise<void> | void;
  onSalvar: () => Promise<void> | void;
  onConcluir: () => Promise<void> | void;
  onDesconcluir: () => Promise<void> | void;
  onPago?: () => Promise<void> | void;
  onPrecos?: () => Promise<void> | void;
  onCopiar?: (dataIso: string, forcar?: boolean) => Promise<ResultadoCopia> | ResultadoCopia;
  onAviso?: (texto: string) => void;
  onCadastrar?: (item: OrderItem) => void;
  onCadastrarCliente?: () => void;
};

function blankItem(): OrderItem {
  return { produto: "", qtd: 1, valor: 0, conhecido: false };
}

function selecionarCampo(event: FocusEvent<HTMLInputElement>) {
  const campo = event.currentTarget;
  campo.select();
  requestAnimationFrame(() => campo.select());
}

function manterSelecao(event: MouseEvent<HTMLInputElement>) {
  event.preventDefault();
}

function numeroDoCampo(texto: string): number | undefined {
  const normal = texto.trim().replace(",", ".");
  if (normal === "" || normal === ".") return undefined;
  const valor = Number(normal);
  return Number.isFinite(valor) ? valor : undefined;
}

function textoNumero(value: number, vazio: boolean, dinheiro = false): string {
  if (vazio) return "";
  if (dinheiro) return reais(value);
  return String(value).replace(".", ",");
}

function qtdDoCampo(texto: string): Pick<OrderItem, "qtd" | "quantidadeEmBranco"> {
  const qtd = numeroDoCampo(texto);
  if (qtd == null || qtd <= 0) return { qtd: 0, quantidadeEmBranco: true };
  return { qtd, quantidadeEmBranco: false };
}

function CampoNumero({
  value,
  vazio,
  dinheiro = false,
  ariaLabel,
  title,
  onValue,
}: {
  value: number;
  vazio: boolean;
  dinheiro?: boolean;
  ariaLabel?: string;
  title?: string;
  onValue: (texto: string) => void;
}) {
  const [rascunho, setRascunho] = useState<string | null>(null);
  return (
    <input
      type="text"
      inputMode="decimal"
      aria-label={ariaLabel}
      title={title}
      value={rascunho ?? textoNumero(value, vazio, dinheiro)}
      onMouseDown={(event) => {
        event.preventDefault();
        const campo = event.currentTarget;
        campo.focus();
        setRascunho(campo.value);
        campo.select();
      }}
      onFocus={(event) => {
        setRascunho(event.currentTarget.value);
        selecionarCampo(event);
      }}
      onBlur={() => setRascunho(null)}
      onMouseUp={manterSelecao}
      onChange={(event) => {
        setRascunho(event.target.value);
        onValue(event.target.value);
      }}
    />
  );
}

function linhaVisivel(item: OrderItem, onlyWithQty: boolean): boolean {
  return !onlyWithQty || item.qtd > 0 || Boolean(item.quantidadeEmBranco);
}

function dinheiro(valor: number): string {
  return valor > 0 ? formatMoney(valor) : "";
}

function isoDaNota(data: string): string {
  return isoDaDataNota(data);
}

function notaDoIso(valor: string): string {
  const [ano, mes, dia] = valor.split("-");
  if (!dia || !mes || !ano) return "";
  return `${dia}/${mes}/${ano}`;
}

function qtdTexto(valor: number): string {
  if (Number.isInteger(valor)) return String(valor);
  return valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

/** Observação sem a marca interna "Pago" / "já pago" — isso fica só no checkbox. */
function obsLivre(observacao?: string): string | undefined {
  return limparMarcaDePago(observacao);
}

function itensReagendados(items: OrderItem[]): OrderItem[] {
  return items.filter((item) => item.reagendar && (item.qtdReagendada || 0) > 0);
}

function textoItemReagendado(item: OrderItem, dataPedido: string): string {
  const qtd = qtdTexto(item.qtdReagendada || 0);
  const nome = item.produto.trim() || "item";
  const dia = dataReagendadaEfetiva(dataPedido, item.dataReagendada);
  const pago = itemJaPago(item.observacao) ? " · pago" : "";
  return `${qtd} ${nome} → ${dia}${pago}`;
}

function NotaImpressa({ order, items }: { order: Order; items: OrderItem[] }) {
  const colunas = 5;
  const rotulo = 4;
  const subtotal = orderSubtotal(order);
  const desconto = orderDiscountValue(order);
  const total = orderTotal(order);
  const origens = [
    ...new Set(items.map((item) => item.origemData?.trim()).filter((data): data is string => Boolean(data))),
  ];
  const saidas = itensReagendados(items);
  return (
    <table className="so-impressao">
      <tbody>
        {order.cliente.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>Nome: {order.cliente}</td>
          </tr>
        ) : null}
        {order.data.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>
              Data: {order.data}
              {(() => {
                const dia = nomeDiaSemana(order.data);
                return dia ? ` (${dia})` : "";
              })()}
            </td>
          </tr>
        ) : null}
        {order.endereco.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>End.: {order.endereco}</td>
          </tr>
        ) : null}
        {order.observacao?.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>Obs.: {order.observacao.trim()}</td>
          </tr>
        ) : null}
        <tr>
          <th className="produto">Produto</th>
          <th className="qtde">Qtde</th>
          <th className="valor">Preço</th>
          <th className="valor">Desc.</th>
          <th className="valor">Val. Tot</th>
        </tr>
        {items.map((item, index) => (
          <tr key={index}>
            <td className="produto">
              {item.origemData ? "*" : ""}
              {item.produto}
              {item.origemData && itemJaPago(item.observacao) ? " (pago)" : ""}
            </td>
            <td className="qtde">
              {item.quantidadeEmBranco || !(item.qtd > 0) ? "" : item.qtd}
              {item.qtd > 0 && qtdCobrada(item) !== item.qtd
                ? ` (entregue ${qtdTexto(qtdCobrada(item))})`
                : ""}
            </td>
            <td className="valor">{dinheiro(item.valor)}</td>
            <td className="valor">{discountLabel(item)}</td>
            <td className="valor">{dinheiro(lineTotal(item))}</td>
          </tr>
        ))}
        {order.desconto > 0 ? (
          <>
            <tr className="total">
              <td colSpan={rotulo}>SUBTOTAL</td>
              <td className="valor">{formatMoney(subtotal)}</td>
            </tr>
            <tr className="total">
              <td colSpan={rotulo}>DESCONTO {order.desconto}%</td>
              <td className="valor">- {formatMoney(desconto)}</td>
            </tr>
          </>
        ) : null}
        <tr className="total total-nota">
          <td colSpan={rotulo}>VALOR DA NOTA</td>
          <td className="valor">{formatMoney(total)}</td>
        </tr>
        {origens.map((data) => (
          <tr className="rodape-reagenda" key={data}>
            <td colSpan={colunas}>*Reagendado de {data}</td>
          </tr>
        ))}
        {saidas.map((item, index) => (
          <tr className="rodape-reagenda" key={`saida-${index}`}>
            <td colSpan={colunas}>Reagendado: {textoItemReagendado(item, order.data)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function IconeComando({
  nome,
}: {
  nome: "pago" | "editar" | "concluir" | "salvar" | "precos" | "copiar" | "imprimir" | "excluir" | "fechar";
}) {
  const traco = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.6,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };
  if (nome === "copiar") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M2.2 2.4h5.2l1.6 1.6v5.8H2.2V2.4z" {...traco} />
        <path d="M4.2 4.2h1.8M4.2 5.8h2.4M4.2 7.4h1.6" {...traco} />
        <path d="M6.2 5.2h5.2l1.6 1.6v5.8H6.2V5.2z" {...traco} />
        <path d="M8 8.4h2.6M8 10h2.6M8 11.6h1.8" {...traco} />
        <path d="M3.4 11.2c.4 1.6 1.8 2.4 3.4 2.4" {...traco} />
        <path d="M5.6 12.4 6.8 13.6 5.4 14.2" {...traco} />
      </svg>
    );
  }
  if (nome === "precos") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 8a5 5 0 0 1 8.5-3.5M13 3.5V7H9.5M13 8a5 5 0 0 1-8.5 3.5M3 12.5V9h3.5" {...traco} />
      </svg>
    );
  }
  if (nome === "pago") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 2.2v11.6" {...traco} />
        <path d="M10.6 4.8c-.7-1.2-1.7-1.8-2.6-1.8-1.2 0-2.2.7-2.2 1.8 0 1.1.7 1.6 2.8 2.2 2.2.6 3.1 1.5 3.1 2.9 0 1.5-1.3 2.5-3.1 2.5-1.2 0-2.3-.5-3.1-1.6" {...traco} />
      </svg>
    );
  }
  if (nome === "imprimir") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4.2 5.5V2.4h7.6v3.1" {...traco} />
        <path d="M3 5.5h10v5.2H3V5.5z" {...traco} />
        <path d="M5 10.7h6v2.9H5v-2.9z" {...traco} />
      </svg>
    );
  }
  if (nome === "fechar") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M4 4l8 8M12 4l-8 8" {...traco} />
      </svg>
    );
  }
  if (nome === "excluir") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3.2 4.5h9.6M6.2 4.4V3.2h3.6v1.2M4.6 4.5l.6 8.2h5.6l.6-8.2" {...traco} />
      </svg>
    );
  }
  if (nome === "salvar") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 2.4h7.2L13 5.1v8.5H3V2.4zM5 2.4V6h5.2V2.4M5 13.6v-3.4h6V13.6" {...traco} />
      </svg>
    );
  }
  if (nome === "concluir") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3.2 8.4l3 3.1 6.6-7" {...traco} />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M9.2 2.6l4.2 4.2L5.8 14.4H1.6v-4.2L9.2 2.6z" {...traco} />
      <path d="M8 3.8l4.2 4.2" {...traco} />
    </svg>
  );
}

function amanhaIso(): string {
  const dia = new Date();
  dia.setDate(dia.getDate() + 1);
  const mes = String(dia.getMonth() + 1).padStart(2, "0");
  const diaMes = String(dia.getDate()).padStart(2, "0");
  return `${dia.getFullYear()}-${mes}-${diaMes}`;
}

export function OrderSheet({ order, catalog, clientes, listas = [], onlyWithQty, ordemImpressao, onChange, onCliente, onFechar, onExcluir, onSalvar, onConcluir, onDesconcluir, onPago, onPrecos, onCopiar, onAviso, onCadastrar, onCadastrarCliente }: Props) {
  const listaClientes = useId();
  const nomeRef = useRef<HTMLInputElement>(null);
  const folhaRef = useRef<HTMLDivElement>(null);
  const [confirma, setConfirma] = useState<"excluir" | "desconcluir" | "pago" | "copiar" | "copiar-duplicado" | null>(null);
  const [dataCopia, setDataCopia] = useState(amanhaIso);
  const [pedidoIgual, setPedidoIgual] = useState<Order | null>(null);
  const [verPedidoIgual, setVerPedidoIgual] = useState(false);
  const [ocupado, setOcupado] = useState(false);
  const [excluirLinha, setExcluirLinha] = useState<number | null>(null);
  const [conflitoReagenda, setConflitoReagenda] = useState<ConflitoReagenda | null>(null);
  const conflitoAbertoRef = useRef(false);
  const orderRef = useRef(order);
  orderRef.current = order;

  function abrirConflitoReagenda(conflito: ConflitoReagenda) {
    conflitoAbertoRef.current = true;
    setConflitoReagenda(conflito);
  }

  function fecharConflitoReagenda() {
    conflitoAbertoRef.current = false;
    setConflitoReagenda(null);
  }
  const items = order.itens
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => linhaVisivel(item, onlyWithQty));
  const compra = order.tipo === "compra";
  const mostrarComprado = !compra;
  const diaSemana = nomeDiaSemana(order.data);
  /** Largura única da coluna Produto = maior nome da nota (tabela alinhada). */
  const produtoCh = useMemo(() => {
    let maior = "Produto".length;
    for (const { item } of items) {
      maior = Math.max(maior, (item.produto || "").trim().length);
    }
    return Math.min(36, Math.max(10, maior + 2));
  }, [items]);

  useEffect(() => {
    if (compra || order.concluido || order.clienteId) return;
    if (!order.cliente.trim() || (order.tabela || "").trim()) return;
    onChange({ ...order, tabela: "Varejo" });
  }, [compra, order, onChange]);

  function update(patch: Partial<Order>) {
    if (order.concluido) return;
    onChange({ ...order, ...patch });
  }

  function cliente(nome: string, commit: boolean) {
    if (order.concluido) return;
    onCliente(nome, commit);
  }

  async function executar(acao: () => Promise<void> | void) {
    setOcupado(true);
    try {
      await acao();
      setConfirma(null);
    } catch (err) {
      onAviso?.(err instanceof Error ? err.message : "Não consegui concluir esta ação.");
    } finally {
      setOcupado(false);
    }
  }

  function imprimirBoleta() {
    const folha = folhaRef.current;
    if (!folha) return;
    document.body.classList.add("imprimindo-boleta");
    folha.classList.add("imprimindo-esta");
    const limpar = () => {
      document.body.classList.remove("imprimindo-boleta");
      folha.classList.remove("imprimindo-esta");
      window.removeEventListener("afterprint", limpar);
    };
    window.addEventListener("afterprint", limpar);
    window.print();
  }

  function updateItem(index: number, patch: Partial<OrderItem>) {
    const atual = orderRef.current;
    const itens = atual.itens.map((item, i) => (i === index ? { ...item, ...patch } : item));
    onChange({ ...atual, itens });
  }

  function qtdTextoCurto(valor: number): string {
    if (Number.isInteger(valor)) return String(valor);
    return valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
  }

  function focarDataReagenda(produto: string) {
    const rotulo = `Dia do reagendamento de ${produto.trim() || "produto"}`;
    requestAnimationFrame(() => {
      const campo = document.querySelector(`input[aria-label="${rotulo}"]`) as HTMLInputElement | null;
      campo?.focus();
      campo?.showPicker?.();
    });
  }

  /** Único ponto de consulta de conflito: checkbox, data confirmada ou “Reagendar o que faltou”. */
  async function resolverConflitoReagenda(
    index: number,
    item: OrderItem,
    patch: Partial<OrderItem>,
    opcoes?: { silencioso?: boolean },
  ): Promise<"livre" | "somar" | "substituir" | "mudar-dia" | "cancelar" | "sem-cliente"> {
    while (conflitoAbertoRef.current) {
      await new Promise((r) => setTimeout(r, 40));
    }
    const atual = orderRef.current;
    const data = dataReagendadaEfetiva(atual.data, patch.dataReagendada ?? item.dataReagendada);
    const patchLimpo = { ...patch, reagendaConduta: undefined as ReagendaConduta | undefined };
    updateItem(index, patchLimpo);

    if (compra) {
      if (!opcoes?.silencioso) onAviso?.(textoAvisoReagenda(true, item, atual.data, patchLimpo));
      return "livre";
    }

    const resultado = await verificarConflito(atual.clienteId, data, item.produto, atual.id);
    if (resultado.tipo === "sem-cliente") {
      onAviso?.("Ligue o cliente do cadastro antes de reagendar (para checar se o produto já está na data).");
      return "sem-cliente";
    }
    if (resultado.tipo === "livre") {
      if (!opcoes?.silencioso) onAviso?.(textoAvisoReagenda(true, item, atual.data, patchLimpo));
      return "livre";
    }

    return new Promise((resolve) => {
      abrirConflitoReagenda({
        destino: resultado.destino,
        onSomar: () => {
          updateItem(index, { ...patchLimpo, reagendaConduta: "somar" });
          fecharConflitoReagenda();
          onAviso?.(textoAvisoReagenda(true, item, orderRef.current.data, patchLimpo, "somar"));
          resolve("somar");
        },
        onSubstituir: () => {
          updateItem(index, { ...patchLimpo, reagendaConduta: "substituir" });
          fecharConflitoReagenda();
          onAviso?.(textoAvisoReagenda(true, item, orderRef.current.data, patchLimpo, "substituir"));
          resolve("substituir");
        },
        onMudarDia: () => {
          updateItem(index, { ...patchLimpo, reagendaConduta: undefined });
          fecharConflitoReagenda();
          focarDataReagenda(item.produto);
          onAviso?.(`${item.produto.trim() || "Item"}: escolha outro dia.`);
          resolve("mudar-dia");
        },
        onCancelar: () => {
          const limpo = patchDesmarcarReagenda(item);
          updateItem(index, limpo);
          fecharConflitoReagenda();
          onAviso?.(textoAvisoReagenda(false, item, orderRef.current.data, limpo));
          resolve("cancelar");
        },
      });
    });
  }

  function removerLinha(index: number) {
    update({ itens: order.itens.filter((_, i) => i !== index) });
    setExcluirLinha(null);
  }

  const subtotal = orderSubtotal(order);
  const discount = orderDiscountValue(order);
  const total = orderTotal(order);
  const faltas = order.itens.filter((item) => faltaDoItem(item) > 0);
  const reagendados = itensReagendados(order.itens);
  /** Só bloqueia reagendar se a nota estiver concluída; dia passado deixa o checkbox desmarcado por padrão. */
  const podeReagendar = !order.concluido;
  const temFalta = podeReagendar && faltas.length > 0;
  const faltasReagendadas = temFalta && faltas.every((item) => item.reagendar && (item.qtdReagendada || 0) > 0);

  async function reagendarFaltas() {
    const data = diaDoReagendamento(order.data);
    const desligar = faltasReagendadas;
    const pendentes = order.itens
      .map((item, index) => ({ item, index }))
      .filter(({ item }) => faltaDoItem(item) > 0);
    if (pendentes.length === 0) {
      onAviso?.("Não há item faltando para reagendar nesta nota.");
      return;
    }
    if (desligar) {
      const atual = orderRef.current;
      const itens = atual.itens.map((item) => {
        if (faltaDoItem(item) <= 0) return item;
        return { ...item, ...patchDesmarcarReagenda(item) };
      });
      onChange({ ...atual, itens });
      onAviso?.(
        pendentes.length === 1
          ? "Reagendamento desmarcado neste item."
          : `Reagendamento desmarcado em ${pendentes.length} itens.`,
      );
      return;
    }

    for (const { item, index } of pendentes) {
      const atualItem = orderRef.current.itens[index] ?? item;
      const patch = patchMarcarReagenda(atualItem, orderRef.current.data, data);
      await resolverConflitoReagenda(index, atualItem, patch, { silencioso: true });
    }
    const marcados = orderRef.current.itens.filter((i) => i.reagendar && (i.qtdReagendada || 0) > 0).length;
    if (marcados > 0) {
      onAviso?.(
        marcados === 1
          ? `Pronto: 1 item marcado para reagendar. A boleta do destino só atualiza ao gravar em Atualizar pedidos.`
          : `Pronto: ${marcados} itens marcados para reagendar. A boleta do destino só atualiza ao gravar em Atualizar pedidos.`,
      );
    }
  }

  const entrega = (item: OrderItem) => (
    <CampoNumero
      value={item.qtdEntregue ?? item.qtd}
      vazio={item.qtdEntregue == null && !(item.qtd > 0)}
      ariaLabel={`Entregue de ${item.produto || "produto"}`}
      title="O que foi entregue. A nota cobra esta quantidade."
      onValue={(texto) => {
        const valor = numeroDoCampo(texto);
        const index = order.itens.indexOf(item);
        const entregue = valor == null ? 0 : valor;
        const falta = Math.max(0, item.qtd - entregue);
        const patch: Partial<OrderItem> = { qtdEntregue: entregue };
        if (falta <= 0) {
          patch.reagendar = false;
          patch.qtdReagendada = undefined;
          patch.dataReagendada = undefined;
          patch.reagendaConduta = undefined;
          if (!item.origemId) patch.observacao = undefined;
        } else if (item.reagendar && (item.qtdReagendada ?? falta) > falta) {
          patch.qtdReagendada = falta;
        }
        updateItem(index, patch);
      }}
    />
  );

  function linhaTotal(rotulo: ReactNode, valor: string, destaque = false) {
    return (
      <div className={`nota-linha${destaque ? " nota-linha-destaque" : ""}`}>
        <div className={`miolo faixa-total${destaque ? " faixa-total-destaque" : ""}`}>
          <div className="rotulo-total">{rotulo}</div>
          <div className="num valor-nota">{valor}</div>
        </div>
      </div>
    );
  }

  const campoDesconto = (
    <span className="desconto-nota no-print">
      desconto
      <input
        type="number"
        min={0}
        step="1"
        aria-label="Desconto da nota"
        value={order.desconto}
        onChange={(event) => update({ desconto: Number(event.target.value) })}
      />
      %
    </span>
  );

  return (
    <div
      ref={folhaRef}
      className={[compra ? "pedido folha compra" : mostrarComprado ? "pedido folha com-compra" : "pedido folha", order.concluido ? "concluido" : ""].filter(Boolean).join(" ")}
      style={{ "--print-order": ordemImpressao, "--produto-ch": produtoCh } as CSSProperties}
    >
      <div className="caixa screen-only">
      <div className="pedido-acoes no-print">
        {temFalta && !order.concluido ? (
          <button
            type="button"
            className={faltasReagendadas ? "reagendar ligado" : "reagendar"}
            aria-pressed={faltasReagendadas}
            title={faltasReagendadas ? "Clique para desmarcar o reagendamento" : "Clique para marcar o que faltou"}
            disabled={Boolean(order.concluido) || ocupado}
            onClick={() => void reagendarFaltas()}
          >
            {faltasReagendadas ? "Desmarcar reagendamento" : "Reagendar o que faltou"}
          </button>
        ) : null}
        {confirma === "excluir" ? (
          <span className="confirma-boleta">
            <span>Excluir este pedido do banco?</span>
            <button className="danger" type="button" disabled={ocupado} onClick={() => void executar(onExcluir)}>
              Confirmar
            </button>
            <button type="button" disabled={ocupado} onClick={() => setConfirma(null)}>
              Cancelar
            </button>
          </span>
        ) : confirma === "desconcluir" ? (
          <span className="confirma-boleta">
            <span>Desbloquear este pedido para edição?</span>
            <button className="primary" type="button" disabled={ocupado} onClick={() => void executar(onDesconcluir)}>
              Confirmar
            </button>
            <button type="button" disabled={ocupado} onClick={() => setConfirma(null)}>
              Cancelar
            </button>
          </span>
        ) : confirma === "pago" ? (
          <span className="confirma-boleta">
            <span>{order.pago ? "Voltar para em aberto?" : "Marcar como paga?"}</span>
            <button
              className="primary"
              type="button"
              disabled={ocupado || !onPago}
              onClick={() => onPago && void executar(onPago)}
            >
              Confirmar
            </button>
            <button type="button" disabled={ocupado} onClick={() => setConfirma(null)}>
              Cancelar
            </button>
          </span>
        ) : confirma === "copiar" ? (
          <span className="confirma-boleta">
            <span>Copiar para</span>
            <input
              type="date"
              aria-label="Data de destino da cópia"
              value={dataCopia}
              onChange={(event) => setDataCopia(event.target.value)}
              disabled={ocupado}
            />
            <button
              className="primary"
              type="button"
              disabled={ocupado || !onCopiar || !dataCopia}
              onClick={() => {
                if (!onCopiar || !dataCopia) return;
                setOcupado(true);
                void Promise.resolve(onCopiar(dataCopia, false))
                  .then((resultado) => {
                    if (resultado.status === "ja-existe") {
                      setPedidoIgual(resultado.pedido);
                      setVerPedidoIgual(false);
                      setConfirma("copiar-duplicado");
                    } else {
                      setPedidoIgual(null);
                      setVerPedidoIgual(false);
                      setConfirma(null);
                    }
                  })
                  .catch((err) => {
                    onAviso?.(err instanceof Error ? err.message : "Não consegui copiar este pedido.");
                  })
                  .finally(() => setOcupado(false));
              }}
            >
              Confirmar
            </button>
            <button
              type="button"
              disabled={ocupado}
              onClick={() => {
                setPedidoIgual(null);
                setVerPedidoIgual(false);
                setConfirma(null);
              }}
            >
              Cancelar
            </button>
          </span>
        ) : confirma === "copiar-duplicado" ? (
          <span className="confirma-boleta">
            <span>Já existe um pedido igual neste dia. Duplicar de novo?</span>
            {pedidoIgual ? (
              <button
                type="button"
                disabled={ocupado}
                onClick={() => setVerPedidoIgual((aberto) => !aberto)}
              >
                {verPedidoIgual ? "Ocultar pedido" : "Ver pedido"}
              </button>
            ) : null}
            <button
              className="primary"
              type="button"
              disabled={ocupado || !onCopiar || !dataCopia}
              onClick={() =>
                onCopiar &&
                void executar(async () => {
                  await onCopiar(dataCopia, true);
                  setPedidoIgual(null);
                  setVerPedidoIgual(false);
                })
              }
            >
              Duplicar
            </button>
            <button
              type="button"
              disabled={ocupado}
              onClick={() => {
                setPedidoIgual(null);
                setVerPedidoIgual(false);
                setConfirma(null);
              }}
            >
              Cancelar
            </button>
          </span>
        ) : (
          <div className="boleta-comandos" role="toolbar" aria-label="Comandos da boleta">
            <button
              type="button"
              className={order.pago ? "pago ligado" : "pago"}
              title={
                order.concluido
                  ? order.pago
                    ? "Paga — confirme para voltar a em aberto"
                    : "Em aberto — confirme para marcar como paga"
                  : order.pago
                    ? "Paga — clique para marcar em aberto"
                    : "Em aberto — clique para marcar como paga"
              }
              aria-label={order.pago ? "Nota paga" : "Nota em aberto"}
              aria-pressed={Boolean(order.pago)}
              disabled={ocupado || !onPago}
              onClick={() => {
                if (!onPago) return;
                if (order.concluido) setConfirma("pago");
                else void executar(onPago);
              }}
            >
              <IconeComando nome="pago" />
            </button>
            <button
              type="button"
              title="Editar"
              aria-label="Editar"
              disabled={Boolean(order.concluido) || ocupado}
              onClick={() => nomeRef.current?.focus()}
            >
              <IconeComando nome="editar" />
            </button>
            <button
              type="button"
              className={order.concluido ? "ativo" : undefined}
              title={order.concluido ? "Desconcluir para editar" : "Concluir"}
              aria-label={order.concluido ? "Desconcluir" : "Concluir"}
              aria-pressed={Boolean(order.concluido)}
              disabled={ocupado}
              onClick={() => (order.concluido ? setConfirma("desconcluir") : void executar(onConcluir))}
            >
              <IconeComando nome="concluir" />
            </button>
            <button
              type="button"
              title="Salvar"
              aria-label="Salvar"
              disabled={Boolean(order.concluido) || ocupado}
              onClick={() => void executar(onSalvar)}
            >
              <IconeComando nome="salvar" />
            </button>
            <button
              type="button"
              title="Atualizar preços desta boleta com a tabela do cadastro"
              aria-label="Atualizar preços"
              disabled={Boolean(order.concluido) || ocupado || !onPrecos || order.tipo === "compra"}
              onClick={() => onPrecos && void executar(onPrecos)}
            >
              <IconeComando nome="precos" />
            </button>
            <button
              type="button"
              title="Copiar este pedido para outro dia"
              aria-label="Copiar pedido"
              disabled={ocupado || !onCopiar || order.tipo === "compra"}
              onClick={() => {
                setDataCopia(amanhaIso());
                setPedidoIgual(null);
                setVerPedidoIgual(false);
                setConfirma("copiar");
              }}
            >
              <IconeComando nome="copiar" />
            </button>
            <button
              type="button"
              title="Imprimir esta boleta para o cliente"
              aria-label="Imprimir boleta"
              disabled={ocupado}
              onClick={imprimirBoleta}
            >
              <IconeComando nome="imprimir" />
            </button>
            <button
              type="button"
              title="Excluir"
              aria-label="Excluir"
              disabled={Boolean(order.concluido) || ocupado}
              onClick={() => setConfirma("excluir")}
            >
              <IconeComando nome="excluir" />
            </button>
            <button type="button" className="fechar" title="Fechar" aria-label="Fechar" onClick={onFechar}>
              <IconeComando nome="fechar" />
            </button>
          </div>
        )}
      </div>
      <fieldset className="boleta-campos">
      <div className="cabecalho">
        <label className={order.cliente.trim() ? undefined : "missing"}>
          <span>{compra ? "Fornecedor" : "Nome"}</span>
          <span className="nome-linha">
            {!compra && onCadastrarCliente && order.cliente.trim() && !order.clienteId ? (
              <button className="link-cadastro cadastrar-cliente screen-only" type="button" onClick={onCadastrarCliente}>
                Cadastrar cliente
              </button>
            ) : null}
            <input
              ref={nomeRef}
              value={order.cliente}
              placeholder={compra ? "quem vendeu" : "quem pediu"}
              list={listaClientes}
              onChange={(event) => cliente(event.target.value, false)}
              onBlur={(event) => cliente(event.target.value, true)}
              onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
                if (event.key === "Enter") cliente(event.currentTarget.value, true);
              }}
            />
          </span>
          <datalist id={listaClientes}>
            {clientes
              .filter((cliente) => (compra ? cliente.kind === "fornecedor" : cliente.kind !== "fornecedor"))
              .map((cliente) => (
                <option key={cliente.id} value={cliente.name} />
              ))}
          </datalist>
        </label>
        <label className={order.data.trim() ? undefined : "missing"}>
          <span>Data</span>
          <span className="campo-data">
            <input
              value={order.data}
              placeholder="DD/MM"
              onChange={(event) => update({ data: event.target.value })}
            />
            {diaSemana ? <span className="dia-semana">({diaSemana})</span> : null}
          </span>
        </label>
        {!compra ? (
          <label
            className={order.clienteId || (order.tabela || "").trim() ? undefined : "missing"}
            title={
              order.clienteId
                ? "Tabela do cadastro do cliente. Pode trocar só nesta nota."
                : "Cliente eventual: tabela padrão Varejo. Pode trocar só nesta nota."
            }
          >
            <span>Tabela</span>
            <select
              value={order.tabela || ""}
              onChange={(event) => update({ tabela: event.target.value || undefined })}
            >
              <option value="">—</option>
              {listas.map((lista) => (
                <option key={lista.id} value={lista.name}>
                  {lista.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <label>
          <span>Endereço</span>
          {(() => {
            const ficha = clientes.find((item) => item.id === order.clienteId) ||
              clientes.find((item) => item.name.trim().toLocaleLowerCase("pt-BR") === order.cliente.trim().toLocaleLowerCase("pt-BR"));
            const opcoes = (ficha?.enderecos || []).filter((item) => item.endereco?.trim());
            if (opcoes.length > 1) {
              return (
                <select
                  value={order.endereco}
                  title="Endereços cadastrados deste cliente"
                  onChange={(event) => update({ endereco: event.target.value })}
                >
                  {!opcoes.some((item) => item.endereco === order.endereco) && order.endereco.trim() ? (
                    <option value={order.endereco}>{order.endereco}</option>
                  ) : null}
                  {opcoes.map((item) => (
                    <option key={`${item.rotulo}-${item.endereco}`} value={item.endereco}>
                      {item.rotulo ? `${item.rotulo}: ${item.endereco}` : item.endereco}
                    </option>
                  ))}
                </select>
              );
            }
            return (
              <input
                value={order.endereco}
                onChange={(event) => update({ endereco: event.target.value })}
              />
            );
          })()}
        </label>
        <label>
          <span>Observação</span>
          <input
            value={order.observacao || ""}
            placeholder="ex.: entrega da manhã, à noite"
            title="Serve para distinguir dois pedidos do mesmo cliente no mesmo dia"
            onChange={(event) => update({ observacao: event.target.value })}
          />
        </label>
      </div>
      </fieldset>
      </div>
      <fieldset className="boleta-campos">
      <div className="faixa screen-only">
      <div className="nota-linha">
        <div className="miolo titulo">
          <div>Produto</div>
          <div className="qtde-par" title="Quantidade pedida e a que foi entregue. A nota cobra o entregue. A edição do entregue fica na coluna ao lado.">
            <div className="qtde-nome">Qtde</div>
            <div className="qtde-nomes">
              <span>solicitado</span>
              <span>entregue</span>
            </div>
          </div>
          <div className="num">Preço</div>
          <div className="num">Desc.</div>
          <div className="num" title="Valor cobrado: quantidade entregue × preço (mais a reagendada se Pago), menos o desconto da linha.">Val. Tot</div>
          <div />
        </div>
        <div className="entrega-rotulo" title="O que foi entregue. A nota cobra esta quantidade, salvo o reagendado marcado como Pago.">Entregue</div>
        {mostrarComprado ? (
          <div className="compra-rotulo" title="Quantidade comprada deste fornecedor. Entra na boleta de compra.">
            <button
              type="button"
              className="copiar-entregue"
              aria-label="Copiar todos os entregues para comprados"
              title="Copia todas as quantidades entregues para Comprados desta nota."
              onClick={() =>
                update({
                  itens: order.itens.map((item) =>
                    item.produto.trim() && item.qtd > 0 ? { ...item, qtdComprada: qtdCobrada(item) } : item,
                  ),
                })
              }
            >
              ›
            </button>
            Comprados
          </div>
        ) : null}
      </div>
          {items.map(({ item, index }) => {
            const options = catalog.includes(item.produto) || !item.produto ? catalog : [item.produto, ...catalog];
            const entregue = qtdCobrada(item);
            const faltou = item.qtd > 0 && entregue < item.qtd;
            const comentario = obsLivre(item.observacao);
            const jaPago = itemJaPago(item.observacao);
            const faltaPreco = !compra && !(item.valor > 0) && !jaPago;
            return (
              <Fragment key={index}>
              <div className="nota-linha">
              <div className={faltou ? "miolo falta" : item.conhecido === false ? "miolo unknown" : "miolo"}>
                <div className="produto">
                  <span className="print-only">{item.produto}</span>
                  {item.origemData ? (
                    <span className="origem">
                      Reagendado de {item.origemData}
                      {jaPago ? " · pago" : ""}
                      {comentario ? `. ${comentario}` : ""}
                    </span>
                  ) : jaPago ? (
                    <span className="origem">Pago{comentario ? `. ${comentario}` : ""}</span>
                  ) : comentario ? (
                    <span className="origem">{comentario}</span>
                  ) : null}
                  <select
                    className="screen-only"
                    value={item.produto}
                    title={item.produto || undefined}
                    onChange={(event) =>
                      updateItem(index, {
                        produto: event.target.value,
                        conhecido: catalog.includes(event.target.value),
                      })
                    }
                  >
                    <option value="">—</option>
                    {options.map((name) => (
                      <option key={name} value={name}>
                        {name}
                      </option>
                    ))}
                  </select>
                  {onCadastrar && item.produto.trim() && (item.conhecido === false || faltaPreco) ? (
                    <button className="link-cadastro screen-only" type="button" onClick={() => onCadastrar(item)}>
                      {item.conhecido === false ? "Cadastrar" : "Definir preço"}
                    </button>
                  ) : null}
                  {item.origemData && !compra && !order.concluido ? (
                    <label
                      className="ja-pago screen-only"
                      title="Cobrado na nota de origem. Esta nota só entrega, sem nova fatura."
                    >
                      <input
                        type="checkbox"
                        checked={jaPago}
                        onChange={(event) => {
                          const ligado = event.target.checked;
                          updateItem(index, {
                            observacao: ligado ? marcarComoPago(item.observacao) : limparMarcaDePago(item.observacao),
                            valor: 0,
                            preco_tabela: !ligado,
                          });
                          if (onAviso) {
                            const nome = item.produto.trim() || "Item";
                            onAviso(
                              ligado
                                ? `${nome}: pago na origem. Esta nota só entrega.`
                                : `${nome}: volta a cobrar nesta nota com o preço da tabela.`,
                            );
                          }
                        }}
                      />
                      Pago
                    </label>
                  ) : null}
                </div>
                <div className="qtde-par valores">
                  <div className="qtde-num">
                    <CampoNumero
                      value={item.qtd}
                      vazio={Boolean(item.quantidadeEmBranco)}
                      ariaLabel="Quantidade solicitada"
                      title="Quantidade pedida"
                      onValue={(texto) => updateItem(index, qtdDoCampo(texto))}
                    />
                  </div>
                  <div className="qtde-num qtde-lida" title="Espelho do entregue. Altere na coluna Entregue, ao lado da boleta.">
                    {item.qtd > 0 || item.qtdEntregue != null ? qtdTexto(entregue) : ""}
                  </div>
                </div>
                <div className={item.valor > 0 || jaPago ? "num" : "num missing"}>
                  {jaPago && (Boolean(item.origemData) || !(item.valor > 0)) ? (
                    <span className="origem" title="Cobrado na nota de origem. Este dia só entrega — Val. Tot fica R$ 0.">
                      pago
                    </span>
                  ) : (
                    <>
                      <CampoNumero
                        value={item.valor}
                        vazio={!(item.valor > 0)}
                        dinheiro
                        ariaLabel="Valor unitário"
                        onValue={(texto) =>
                          updateItem(index, { valor: numeroDoCampo(texto) ?? 0, preco_tabela: false })
                        }
                      />
                      {item.preco_tabela ? <span className="origem">{order.tabela || "tabela"}</span> : null}
                    </>
                  )}
                </div>
                <div className="num">
                  <span className="descontos screen-only">
                    <span>R$</span>
                    <CampoNumero
                      ariaLabel="Desconto em reais"
                      title="Desconto em reais por unidade"
                      dinheiro
                      value={item.desconto ?? 0}
                      vazio={item.desconto == null}
                      onValue={(texto) => {
                        const valor = numeroDoCampo(texto);
                        updateItem(index, { desconto: valor == null ? undefined : valor });
                      }}
                    />
                    <span>%</span>
                    <CampoNumero
                      ariaLabel="Desconto percentual"
                      title="Desconto percentual da linha"
                      value={item.descontoPercentual ?? 0}
                      vazio={item.descontoPercentual == null}
                      onValue={(texto) => {
                        const valor = numeroDoCampo(texto);
                        updateItem(index, { descontoPercentual: valor == null ? undefined : valor });
                      }}
                    />
                  </span>
                  <span className="print-only">{discountLabel(item)}</span>
                </div>
                <div
                  className="num"
                  title={
                    item.origemData && jaPago
                      ? "Reagendado pago: este dia só entrega, sem cobrança."
                      : "Quantidade faturada × preço. Com Pago na origem, inclui a qtd reagendada."
                  }
                >
                  {formatMoney(lineTotal(item))}
                </div>
                {order.concluido ? (
                  <div className="linha-acao no-print" />
                ) : (
                  <div className="linha-acao no-print">
                    {excluirLinha === index ? (
                      <span className="confirma-linha">
                        <span>Excluir?</span>
                        <button className="danger" type="button" onClick={() => removerLinha(index)}>
                          Sim
                        </button>
                        <button type="button" onClick={() => setExcluirLinha(null)}>
                          Não
                        </button>
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="excluir-linha"
                        title="Excluir linha"
                        aria-label={`Excluir linha ${item.produto || index + 1}`}
                        onClick={() => setExcluirLinha(index)}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                )}
              </div>
              <div className={faltou ? "entrega-campo menor" : "entrega-campo"}>{entrega(item)}</div>
              {mostrarComprado ? (
                <div className="compra-campo">
                  <button
                    type="button"
                    className="copiar-entregue"
                    aria-label={`Copiar entregue de ${item.produto || "produto"}`}
                    title="Copia o entregue desta linha para Comprados."
                    onClick={() => {
                      if (!item.produto.trim() || !(item.qtd > 0)) return;
                      updateItem(index, { qtdComprada: qtdCobrada(item) });
                    }}
                  >
                    ›
                  </button>
                  <CampoNumero
                    value={item.qtdComprada ?? 0}
                    vazio={item.qtdComprada == null}
                    ariaLabel={`Comprado de ${item.produto || "produto"}`}
                    title="Quantidade comprada deste fornecedor. Entra na boleta de compra."
                    onValue={(texto) => {
                      const valor = numeroDoCampo(texto);
                      updateItem(index, { qtdComprada: valor == null ? 0 : valor });
                    }}
                  />
                </div>
              ) : null}
              </div>
              {faltou && podeReagendar ? (
                <div className="nota-linha">
                  <div className="miolo reagenda">
                    <label>
                      <input
                        type="checkbox"
                        checked={Boolean(item.reagendar)}
                        onChange={(event) => {
                          const ligado = event.target.checked;
                          if (!ligado) {
                            const limpo = patchDesmarcarReagenda(item);
                            updateItem(index, limpo);
                            onAviso?.(textoAvisoReagenda(false, item, order.data, limpo));
                            return;
                          }
                          const patch = patchMarcarReagenda(item, order.data);
                          void resolverConflitoReagenda(index, item, patch);
                        }}
                      />
                      Reagendar
                    </label>
                    <span className="qtd-reagenda">
                      <CampoNumero
                        value={item.qtdReagendada || faltaDoItem(item)}
                        vazio={false}
                        ariaLabel={`Quantidade reagendada de ${item.produto || "produto"}`}
                        title="Quantidade que vai para o outro dia. Menor que a falta, o restante não é reagendado."
                        onValue={(texto) => {
                          const falta = faltaDoItem(item);
                          const bruto = numeroDoCampo(texto);
                          const qtd = bruto == null ? 0 : Math.min(Math.max(bruto, 0), falta);
                          if (qtd <= 0) {
                            if (item.reagendar) {
                              const limpo = patchDesmarcarReagenda(item);
                              updateItem(index, limpo);
                              onAviso?.(textoAvisoReagenda(false, item, order.data, limpo));
                            } else {
                              updateItem(index, { qtdReagendada: undefined });
                            }
                            return;
                          }
                          // Só ajusta qtde; conflito só ao marcar checkbox / confirmar data / botão em lote.
                          updateItem(index, {
                            qtdReagendada: qtd,
                            ...(item.reagendar
                              ? {}
                              : { dataReagendada: dataReagendadaEfetiva(order.data, item.dataReagendada) }),
                          });
                        }}
                      />
                    </span>
                    <span>para</span>
                    <input
                      type="date"
                      aria-label={`Dia do reagendamento de ${item.produto || "produto"}`}
                      title="Sempre editável. Ao confirmar o dia, pergunta se soma ou substitui (exceto ao só mudar o mês no calendário)."
                      value={isoDaNota(dataReagendadaEfetiva(order.data, item.dataReagendada))}
                      onChange={(event) => {
                        const dataNota = notaDoIso(event.target.value);
                        if (!dataNota) return;
                        const anterior = dataReagendadaEfetiva(order.data, item.dataReagendada);
                        const soNavegouMes = pareceNavegacaoMes(anterior, dataNota);
                        const patch = {
                          ...patchMarcarReagenda(item, order.data, dataNota),
                          dataReagendada: dataNota,
                        };
                        if (soNavegouMes) {
                          // Só navegação de mês: atualiza data e marca, sem diálogo.
                          updateItem(index, { ...patch, reagendaConduta: undefined });
                          return;
                        }
                        void resolverConflitoReagenda(index, item, patch);
                      }}
                    />
                    <label
                      className="ja-pago"
                      title="Já cobrado nesta nota. O reagendamento só entrega no outro dia, sem gerar nova fatura."
                    >
                      <input
                        type="checkbox"
                        checked={itemJaPago(item.observacao)}
                        disabled={!item.reagendar}
                        onChange={(event) => {
                          const ligado = event.target.checked;
                          updateItem(index, {
                            observacao: ligado ? marcarComoPago(item.observacao) : limparMarcaDePago(item.observacao),
                          });
                          if (onAviso) {
                            const nome = item.produto.trim() || "Item";
                            onAviso(
                              ligado
                                ? `${nome}: pago. Reagendamento só entrega, sem nova fatura.`
                                : `${nome}: reagendamento volta a cobrar no outro dia.`,
                            );
                          }
                        }}
                      />
                      Pago
                    </label>
                    <input
                      className="obs"
                      aria-label={`Observação de ${item.produto || "produto"}`}
                      placeholder="Observação"
                      disabled={!item.reagendar}
                      value={obsLivre(item.observacao) || ""}
                      onChange={(event) => {
                        const texto = event.target.value;
                        updateItem(index, {
                          observacao: itemJaPago(item.observacao)
                            ? marcarComoPago(texto)
                            : texto.trim() || undefined,
                        });
                      }}
                    />
                  </div>
                  <div />
                </div>
              ) : null}
              </Fragment>
            );
          })}
          {!order.concluido || reagendados.length > 0 ? (
            <div className="nota-linha">
              <div className="miolo uma">
                {order.concluido ? (
                  <div className="resumo-reagendados" title="Itens reagendados desta nota.">
                    <span className="resumo-reagendados-titulo">Reagendados</span>
                    <ul>
                      {reagendados.map((item, index) => (
                        <li key={`${item.produto}-${index}`}>{textoItemReagendado(item, order.data)}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <button type="button" onClick={() => update({ itens: [...order.itens, blankItem()] })}>
                    Incluir item
                  </button>
                )}
              </div>
            </div>
          ) : null}
          {order.desconto > 0 ? (
            <>
              {linhaTotal("SUBTOTAL", formatMoney(subtotal))}
              {linhaTotal(
                <>
                  DESCONTO
                  <span className="desconto-nota no-print">
                    <input
                      type="number"
                      min={0}
                      step="1"
                      aria-label="Desconto da nota"
                      value={order.desconto}
                      onChange={(event) => update({ desconto: Number(event.target.value) })}
                    />
                    %
                  </span>
                </>,
                `- ${formatMoney(discount)}`,
              )}
              {linhaTotal("VALOR DA NOTA", formatMoney(total), true)}
            </>
          ) : (
            linhaTotal(
              <>
                VALOR DA NOTA
                {campoDesconto}
              </>,
              formatMoney(total),
              true,
            )
          )}
      </div>
      </fieldset>
      <NotaImpressa order={order} items={items.map(({ item }) => item)} />
      <p className="no-print origem">
        {podeReagendar
          ? "A quantidade entregue fica ao lado da nota. A nota cobra o que foi entregue. O que faltou pode ir para outro dia (checkbox desmarcado por padrão). Se já foi pago, marque Pago: a nota de hoje cobra essa falta e o reagendamento só entrega, sem nova fatura."
          : "A quantidade entregue fica ao lado da nota. A nota cobra o que foi entregue. Nota concluída: o que faltou não é reagendado até desconcluir."}
      </p>
      <p className="no-print empty">{items.length === 0 ? "Nenhum item neste pedido." : ""}</p>
      {verPedidoIgual && pedidoIgual
        ? createPortal(
            <PedidoIgualPopup pedido={pedidoIgual} onFechar={() => setVerPedidoIgual(false)} />,
            document.body,
          )
        : null}
      {conflitoReagenda
        ? createPortal(
            <div className="reagenda-conflito no-print" role="dialog" aria-modal="true" aria-labelledby="reagenda-conflito-titulo">
              <strong id="reagenda-conflito-titulo">Produto já na data</strong>
              <p>
                Existe um pedido para esta data ({conflitoReagenda.destino.data}) com este produto
                ({conflitoReagenda.destino.produto}) e nesta qtde {qtdTextoCurto(conflitoReagenda.destino.qtde)}.
                Deseja somar ou substituir?
              </p>
              <div className="reagenda-conflito-boleta">
                <p>
                  <span>Nome</span> {conflitoReagenda.destino.nome}
                </p>
                <p>
                  <span>Data</span> {conflitoReagenda.destino.data}
                  {nomeDiaSemana(conflitoReagenda.destino.data)
                    ? ` (${nomeDiaSemana(conflitoReagenda.destino.data)})`
                    : ""}
                </p>
                <table>
                  <thead>
                    <tr>
                      <th>Produto</th>
                      <th className="num">Qtde</th>
                      <th className="num">Preço</th>
                      <th className="num">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>{conflitoReagenda.destino.produto}</td>
                      <td className="num">{qtdTextoCurto(conflitoReagenda.destino.qtde)}</td>
                      <td className="num">{formatMoney(conflitoReagenda.destino.preco)}</td>
                      <td className="num">{formatMoney(conflitoReagenda.destino.total)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="reagenda-conflito-acoes">
                <button type="button" onClick={conflitoReagenda.onSomar}>
                  Somar
                </button>
                <button type="button" onClick={conflitoReagenda.onSubstituir}>
                  Substituir
                </button>
                <button type="button" className="secundario" onClick={conflitoReagenda.onMudarDia}>
                  Mudar dia
                </button>
                <button type="button" className="secundario" onClick={conflitoReagenda.onCancelar}>
                  Cancelar
                </button>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
