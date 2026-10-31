import { useEffect, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { AreaTrabalho, IconeAcao } from "./AreaTrabalho";
import { BuscaCliente } from "./BuscaCliente";
import { Cadastro } from "./Cadastro";
import { carregarContextosIa, montarContexto } from "./contextoIa";
import { ContextoIa } from "./TelaContexto";
import { Colaboradores } from "./Colaboradores";
import { Contas } from "./Contas";
import { FunilVendas } from "./FunilVendas";
import { PedidoIgualPopup } from "./PedidoIgualPopup";
import {
  diaIdDeIso,
  gravarPlanilhaRecorrente,
  incluirClienteNoDia,
  lerPlanilhaRecorrente,
  nomeClienteGrade,
} from "./pedidosRecorrentes";
import { clienteDoApelido, mesmoCliente } from "./nomeCliente";
import { convertConversation } from "./api";
import { avisarAdministrador, carregarPreferencia, consultarBoletas, createProduto, excluirBoleta, loadClientes, loadTabelas, salvarBoletas, salvarPreferencia, saveTablePrice, type Cliente, type Extrato, type Lista, type Produto } from "./cadastroApi";
import { EnviarWhatsApp } from "./EnviarWhatsApp";
import { ListaColheita } from "./ListaColheita";
import { ListaRota } from "./ListaRota";
import {
  contabilidadeCobranca,
  dataReagendadaEfetiva,
  formatMoney,
  itemJaPago,
  ordemDeImpressao,
  qtdContabilidade,
  resumoCobranca,
  semReagenda,
} from "./orderMath";
import { OrderSheet } from "./OrderSheet";
import { PedidoChat } from "./PedidoChat";
import { aberturaDoItem, ProdutoPopup, type AberturaProduto, type ProdutoSalvo } from "./ProdutoPopup";
import { alfaceDoHistorico, alfaceSemVariedade, amarrarAoPedidoUnico, aplicarDecisao, aplicarFalaCompra, aplicarFormatoDaConversa, aplicarResposta, aplicarSugestaoAlface, atualizarUm, clientesNovos, completarDatas, comPrecos, listarClientes, nomeNaBoleta, opcoesDeCliente, pareceAfirmacao, pareceNegacao, perguntaAlface, perguntaDeUm, podeAcrescentarDireto, prepararPedidos, precosForcadosNaNota, precosNaTroca, respostaDoPedido, revisaoDe, rotulosDoCatalogo, sincronizarCompra, temNomeNovo, TEXTO_INTERPRETADOR_FORA, type ClienteParaIncluir, type DecisaoListagem, type SugestaoAlface } from "./pedidoConversa";
import { gravarRascunhoPedidos, lerRascunhoPedidos, limparRascunhoPedidos } from "./pedidoRascunho";
import { gravarAreaLocal, lerAreaLocal, telaValida, type Tela } from "./preferenciaArea";
import { mesmoNome, normalizarFormato, separarFormato } from "./rascunho";
import type { Order, OrderItem } from "./types";

const rascunhoPedidos = lerRascunhoPedidos();
const areaLocal = lerAreaLocal();

function iso(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function diaMes(valor: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(valor);
  if (!match) return "";
  return `${match[3]}/${match[2]}`;
}

function dataParaNota(isoData: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoData.trim());
  if (!match) return "";
  return `${match[3]}/${match[2]}/${match[1]}`;
}

function amanhaIso(hoje = new Date()): string {
  const dia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + 1);
  return iso(dia);
}

function clonarPedido(order: Order, data: string): Order {
  return {
    tipo: order.tipo === "compra" ? "compra" : "venda",
    cliente: order.cliente,
    clienteId: order.clienteId,
    data,
    endereco: order.endereco,
    desconto: order.desconto,
    tabela: order.tabela,
    observacao: order.observacao,
    concluido: false,
    pago: false,
    itens: order.itens
      .filter((item) => item.qtd > 0 && item.produto.trim())
      .map((item) => ({
        produto: item.produto,
        qtd: item.qtd,
        valor: item.valor,
        desconto: item.desconto,
        descontoPercentual: item.descontoPercentual,
        conhecido: item.conhecido,
        preco_tabela: item.preco_tabela,
        observacao: item.observacao,
      })),
  };
}

function foldTexto(valor: string): string {
  return valor
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/\s+/g, " ")
    .trim();
}

/** Assinatura do conteúdo — cópia literal tem a mesma chave. */
function assinaturaPedido(order: Order): string {
  const quem = order.clienteId
    ? `id:${order.clienteId}`
    : `nome:${foldTexto(order.cliente)}`;
  const itens = order.itens
    .filter((item) => item.qtd > 0 && item.produto.trim())
    .map((item) =>
      [
        foldTexto(item.produto),
        String(item.qtd),
        String(item.valor || 0),
        String(item.desconto || 0),
        String(item.descontoPercentual || 0),
      ].join(":"),
    )
    .sort()
    .join("|");
  return [
    quem,
    String(order.desconto || 0),
    foldTexto(order.tabela || ""),
    foldTexto(order.endereco || ""),
    foldTexto(order.observacao || ""),
    itens,
  ].join("::");
}

/** Inclui entregue/reagendar — para detectar boleta alterada ainda não gravada. */
function assinaturaPersistencia(order: Order): string {
  const itens = order.itens
    .filter((item) => item.qtd > 0 && item.produto.trim())
    .map((item) =>
      [
        foldTexto(item.produto),
        String(item.qtd),
        String(item.qtdEntregue ?? ""),
        String(item.valor || 0),
        String(item.desconto || 0),
        String(item.descontoPercentual || 0),
        item.reagendar ? "1" : "0",
        String(item.qtdReagendada || 0),
        (item.dataReagendada || "").trim(),
        item.reagendaConduta || "",
        foldTexto(item.observacao || ""),
      ].join(":"),
    )
    .sort()
    .join("|");
  return [
    order.id || "",
    order.clienteId ? `id:${order.clienteId}` : `nome:${foldTexto(order.cliente)}`,
    order.data.trim(),
    String(order.desconto || 0),
    foldTexto(order.tabela || ""),
    foldTexto(order.endereco || ""),
    foldTexto(order.observacao || ""),
    order.concluido ? "1" : "0",
    order.pago ? "1" : "0",
    itens,
  ].join("::");
}

function isoDaDataNota(data: string): string {
  const match = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(data.trim());
  if (!match) return "";
  const dia = match[1].padStart(2, "0");
  const mes = match[2].padStart(2, "0");
  let ano = match[3] ? Number(match[3]) : new Date().getFullYear();
  if (ano < 100) ano += 2000;
  return `${ano}-${mes}-${dia}`;
}

function periodoDaPesquisa(de: string, ate: string): string {
  const inicio = diaMes(de);
  const fim = diaMes(ate);
  if (!inicio) return "";
  if (!fim || inicio === fim) return inicio;
  const anoDe = de.slice(0, 4);
  const anoAte = ate.slice(0, 4);
  if (anoDe && anoAte && anoDe !== anoAte) return `${inicio}/${anoDe} a ${fim}/${anoAte}`;
  return `${inicio} a ${fim}`;
}

function imprimirComClasse(classe: string, pagina?: string) {
  const estiloPagina = pagina
    ? Object.assign(document.createElement("style"), {
        id: "print-page-size",
        textContent: `@page { size: ${pagina}; margin: 8mm; }`,
      })
    : null;
  if (estiloPagina) document.head.appendChild(estiloPagina);
  document.body.classList.add(classe);
  const limpar = () => {
    document.body.classList.remove(classe);
    estiloPagina?.remove();
    window.removeEventListener("afterprint", limpar);
  };
  window.addEventListener("afterprint", limpar);
  window.print();
  setTimeout(limpar, 1000);
}

function imprimirCobranca() {
  imprimirComClasse("imprimindo-cobranca", "landscape");
}

function imprimirContabilidade() {
  imprimirComClasse("imprimindo-contabilidade");
}

function notasDoExtrato(extrato: Extrato): Order[] {
  return extrato.clientes.flatMap((cliente) =>
    cliente.pedidos.map((pedido) => ({
      id: pedido.id,
      cliente: cliente.nome,
      clienteId: cliente.id,
      data: pedido.data,
      endereco: pedido.endereco,
      desconto: pedido.desconto,
      tabela: pedido.tabela || "",
      tipo: pedido.tipo === "compra" ? "compra" : "venda",
      concluido: Boolean(pedido.concluido),
      pago: Boolean(pedido.pago),
      observacao: pedido.observacao || undefined,
      itens: pedido.itens.map((item) => ({
        produto: item.produto,
        qtd: item.qtd,
        qtdEntregue: item.qtd_entregue,
        valor: item.valor,
        desconto: item.desconto ? item.desconto : undefined,
        descontoPercentual: item.desconto_percentual ? item.desconto_percentual : undefined,
        reagendar: (item.qtd_reagendada || 0) > 0,
        qtdReagendada: (item.qtd_reagendada || 0) > 0 ? item.qtd_reagendada : undefined,
        dataReagendada: item.data_reagendada || undefined,
        observacao: item.observacao || undefined,
        origemId: item.origem_id || undefined,
        origemData: item.origem_data || undefined,
        conhecido: true,
        preco_tabela: false,
      })),
    })),
  );
}

function textoReagendados(quantidade: number): string {
  if (!quantidade) return "";
  return quantidade === 1
    ? " Atualizei 1 item na boleta do dia reagendado (só vale depois deste salvar)."
    : ` Atualizei ${quantidade} itens nas boletas dos dias reagendados (só vale depois deste salvar).`;
}

function compraComItem(order: Order): boolean {
  return order.tipo === "compra" && order.itens.some((item) => item.qtd > 0 && item.produto.trim());
}

/** Pedido ainda sem gravar — ignora o rascunho vazio de compra que fica oculto na tela. */
function pedidoNovoNaTela(order: Order): boolean {
  if (order.id) return false;
  if (order.tipo === "compra" && !compraComItem(order)) return false;
  return true;
}

function clonarPedidoSalvo(order: Order): Order {
  return JSON.parse(JSON.stringify(order)) as Order;
}

function nomesPedidosNovos(orders: Order[]): string[] {
  return orders
    .filter(pedidoNovoNaTela)
    .map((order) => order.cliente.trim() || (order.tipo === "compra" ? "Compra sem nome" : "Sem nome"));
}

function rascunhoDeCompra(orders: Order[]): number {
  return orders.findIndex((order) => order.tipo === "compra" && !order.id);
}

function garantirCompra(orders: Order[]): Order[] {
  if (rascunhoDeCompra(orders) >= 0) return orders;
  const data = orders.find((order) => order.tipo !== "compra" && order.data.trim())?.data || "";
  return [...orders, { tipo: "compra", cliente: "", data, endereco: "", desconto: 0, itens: [] }];
}

function semMarcasDeCompra(orders: Order[]): Order[] {
  return orders.map((order) => {
    if (order.tipo === "compra") return order;
    return {
      ...order,
      itens: order.itens.map((item) => {
        const { qtdComprada, ...resto } = item;
        void qtdComprada;
        return resto;
      }),
    };
  });
}

function pedidoParaSalvar(order: Order, concluir = false, desconcluir = false) {
  const pronto = semReagenda(order);
  return {
    cliente_id: pronto.clienteId,
    cliente: pronto.cliente.trim(),
    data: pronto.data,
    endereco: pronto.endereco,
    desconto: pronto.desconto,
    id: pronto.id,
    tabela: pronto.tabela || "",
    tipo: pronto.tipo === "compra" ? ("compra" as const) : ("venda" as const),
    concluir,
    desconcluir,
    pago: Boolean(pronto.pago),
    observacao: (pronto.observacao || "").trim(),
    itens: pronto.itens
      .filter((item) => item.qtd > 0 && item.produto.trim())
      .map((item) => ({
        produto: item.produto,
        qtd: item.qtd,
        qtd_entregue: item.qtdEntregue ?? item.qtd,
        valor: item.valor,
        desconto: item.desconto || 0,
        desconto_percentual: item.descontoPercentual || 0,
        qtd_reagendada: item.reagendar ? item.qtdReagendada || 0 : 0,
        data_reagendada: item.reagendar ? dataReagendadaEfetiva(pronto.data, item.dataReagendada) : "",
        reagenda_conduta: item.reagendar ? item.reagendaConduta : undefined,
        observacao: item.observacao || "",
        origem_id: item.origemId,
      })),
  };
}

function faltaParaSalvar(orders: Order[]): string {
  const faltas: string[] = [];
  orders.forEach((order, index) => {
    if (order.tipo === "compra" && !compraComItem(order)) return;
    const compra = order.tipo === "compra";
    const quem = order.cliente.trim() || `A nota ${index + 1}`;
    if (compra) {
      if (!order.clienteId) faltas.push(`${quem} ainda não está ligado a um fornecedor do cadastro.`);
    } else if (!order.cliente.trim()) {
      faltas.push(`${quem} está sem nome.`);
    } else if (!order.clienteId && !(order.tabela || "").trim()) {
      faltas.push(`${quem}: escolha a tabela (Varejo, Restaurantes, Revenda ou Amigos).`);
    }
    if (!order.data.trim()) faltas.push(`${quem} está sem data de entrega.`);
    const itens = order.itens.filter((item) => item.qtd > 0 && item.produto.trim());
    if (!itens.length) faltas.push(`${quem} não tem item com quantidade.`);
    if (!compra) {
      itens.forEach((item) => {
        if (!(item.valor > 0) && !itemJaPago(item.observacao)) {
          faltas.push(`${quem}: falta o preço de ${item.produto}.`);
        }
      });
    }
  });
  return faltas.join(" ");
}
type Aviso = { id: number; texto: string };

function notaMudou(antes: Order[], depois: Order[]): boolean {
  return antes.some((order, index) => {
    const outro = depois[index];
    if (!outro) return true;
    if ((order.tabela || "") !== (outro.tabela || "")) return true;
    if (order.endereco !== outro.endereco) return true;
    if (order.desconto !== outro.desconto) return true;
    return order.itens.some(
      (item, itemIndex) =>
        item.valor !== outro.itens[itemIndex]?.valor || item.desconto !== outro.itens[itemIndex]?.desconto,
    );
  });
}

export function App() {
  const [tela, setTela] = useState<Tela>(areaLocal?.tela ?? "pedidos");
  const [orders, setOrders] = useState<Order[]>(rascunhoPedidos?.orders ?? []);
  const [catalog, setCatalog] = useState<string[]>(rascunhoPedidos?.catalog ?? []);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [listas, setListas] = useState<Lista[]>([]);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [onlyWithQty, setOnlyWithQty] = useState(rascunhoPedidos?.onlyWithQty ?? true);
  const [chatAberto, setChatAberto] = useState(areaLocal?.chatAberto ?? rascunhoPedidos?.chatAberto ?? true);
  const [ferramentasAbertas, setFerramentasAbertas] = useState(areaLocal?.ferramentasAbertas ?? false);
  const [atualizando, setAtualizando] = useState(false);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [incluir, setIncluir] = useState<(ClienteParaIncluir & { seq: number }) | null>(null);
  const [revisao, setRevisao] = useState<{ fila: Order[]; indice: number } | null>(null);
  const [sugestaoAlface, setSugestaoAlface] = useState<SugestaoAlface | null>(null);
  const [interpretadorFora, setInterpretadorFora] = useState(false);
  const [confirmarSalvar, setConfirmarSalvar] = useState(false);
  const [pendenciaNaoSalvos, setPendenciaNaoSalvos] = useState<"abrir-pedidos" | "fechar-funil" | null>(null);
  const [avisoNaoSalvosSolto, setAvisoNaoSalvosSolto] = useState(false);
  const [avisoNaoSalvosPos, setAvisoNaoSalvosPos] = useState<{ x: number; y: number } | null>(null);
  const avisoNaoSalvosArrasto = useRef<{ dx: number; dy: number } | null>(null);
  const [confirmarLimpar, setConfirmarLimpar] = useState(false);
  const [confirmarDuplicar, setConfirmarDuplicar] = useState<"data" | "forcar" | null>(null);
  const [dataDuplicar, setDataDuplicar] = useState(() => amanhaIso());
  const [avisoDuplicata, setAvisoDuplicata] = useState("");
  const [pedidoIgualDuplicar, setPedidoIgualDuplicar] = useState<Order | null>(null);
  const [verPedidoIgual, setVerPedidoIgual] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [filtroCliente, setFiltroCliente] = useState(rascunhoPedidos?.filtroCliente ?? "");
  const [filtroClienteNome, setFiltroClienteNome] = useState(rascunhoPedidos?.filtroClienteNome ?? "");
  const [filtroDe, setFiltroDe] = useState(rascunhoPedidos?.filtroDe || iso(new Date()));
  const [filtroAte, setFiltroAte] = useState(rascunhoPedidos?.filtroAte ?? "");
  const [buscando, setBuscando] = useState(false);
  const [funilPedido, setFunilPedido] = useState<{ cliente: string; dataIso: string } | null>(null);
  const [funilJanela, setFunilJanela] = useState<"normal" | "min" | "max">("normal");
  const [funilPos, setFunilPos] = useState<{ left: number; top: number } | null>(null);
  const [funilVersao, setFunilVersao] = useState(0);
  const [mostrarColheita, setMostrarColheita] = useState(false);
  const [mostrarRota, setMostrarRota] = useState(false);
  const [mostrarWhatsApp, setMostrarWhatsApp] = useState(false);
  const [produtoNovo, setProdutoNovo] = useState<AberturaProduto | null>(null);
  const [modoNota, setModoNota] = useState<"venda" | "compra">("venda");
  const ordersRef = useRef(orders);
  ordersRef.current = orders;
  /** Assinatura/conteúdo da última gravação ou busca — detecta alteração (reagendar, entregue, etc.). */
  const assinaturasSalvasRef = useRef<Map<string, string>>(new Map());
  const snapshotsSalvosRef = useRef<Map<string, Order>>(new Map());
  const sugestaoAlfaceRef = useRef<SugestaoAlface | null>(null);
  sugestaoAlfaceRef.current = sugestaoAlface;
  const interpretadorForaRef = useRef(false);
  interpretadorForaRef.current = interpretadorFora;
  const avisoId = useRef(0);

  function registrarPedidosSalvos(lista: Order[]) {
    for (const order of lista) {
      if (!order.id) continue;
      assinaturasSalvasRef.current.set(order.id, assinaturaPersistencia(order));
      snapshotsSalvosRef.current.set(order.id, clonarPedidoSalvo(order));
    }
  }

  /** Novo sem id, ou já gravado com mudança local ainda não salva. */
  function pedidoPendenteNaTela(order: Order): boolean {
    if (pedidoNovoNaTela(order)) return true;
    if (!order.id) return false;
    const base = assinaturasSalvasRef.current.get(order.id);
    if (base == null) {
      // Sem baseline desta sessão: reagendar marcado ou entregue ≠ pedido = ainda não gravado.
      return order.itens.some(
        (item) =>
          (Boolean(item.reagendar) && (item.qtdReagendada || 0) > 0) ||
          (item.qtdEntregue != null && item.qtdEntregue !== item.qtd),
      );
    }
    return assinaturaPersistencia(order) !== base;
  }

  // Baseline ao montar (rascunho / F5): senão Buscar não detecta alteração de reagendar.
  useEffect(() => {
    registrarPedidosSalvos(ordersRef.current.filter((order) => Boolean(order.id)));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só na montagem
  }, []);
  const rascunhoAvisado = useRef(false);
  const preferenciaPronta = useRef(false);
  const mexeuArea = useRef(false);
  const areaAtual = useRef({ tela, chatAberto, ferramentasAbertas });
  areaAtual.current = { tela, chatAberto, ferramentasAbertas };

  function irPara(proxima: Tela) {
    mexeuArea.current = true;
    setTela(proxima);
  }

  function abrirChat(valor: boolean | ((atual: boolean) => boolean)) {
    mexeuArea.current = true;
    setChatAberto(valor);
  }

  function abrirFerramentas(abertas: boolean) {
    mexeuArea.current = true;
    setFerramentasAbertas(abertas);
  }

  useEffect(() => {
    gravarRascunhoPedidos({
      orders,
      catalog,
      onlyWithQty,
      chatAberto,
      filtroCliente,
      filtroClienteNome,
      filtroDe,
      filtroAte,
    });
  }, [orders, catalog, onlyWithQty, chatAberto, filtroCliente, filtroClienteNome, filtroDe, filtroAte]);

  useEffect(() => {
    let vivo = true;
    carregarPreferencia()
      .then((pref) => {
        if (!vivo || mexeuArea.current) return;
        if (telaValida(pref.tela)) setTela(pref.tela);
        setChatAberto(pref.chat_aberto);
        setFerramentasAbertas(pref.ferramentas_abertas);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!vivo) return;
        preferenciaPronta.current = true;
        if (!mexeuArea.current) return;
        const atual = areaAtual.current;
        void salvarPreferencia({
          usuario: "operacao",
          tela: atual.tela,
          chat_aberto: atual.chatAberto,
          ferramentas_abertas: atual.ferramentasAbertas,
        }).catch(() => undefined);
      });
    return () => {
      vivo = false;
    };
  }, []);

  useEffect(() => {
    gravarAreaLocal({ tela, chatAberto, ferramentasAbertas });
    if (!preferenciaPronta.current) return;
    void salvarPreferencia({
      usuario: "operacao",
      tela,
      chat_aberto: chatAberto,
      ferramentas_abertas: ferramentasAbertas,
    }).catch(() => undefined);
  }, [tela, chatAberto, ferramentasAbertas]);

  useEffect(() => {
    loadClientes().then(setClientes).catch(() => undefined);
  }, []);

  function publicar(texto: string) {
    if (!texto) return;
    avisoId.current += 1;
    setAviso({ id: avisoId.current, texto });
  }

  useEffect(() => {
    if (rascunhoAvisado.current || !rascunhoPedidos?.orders.length) return;
    rascunhoAvisado.current = true;
    publicar(
      `Recuperei ${rascunhoPedidos.orders.length} ${rascunhoPedidos.orders.length === 1 ? "pedido" : "pedidos"} que estavam na tela.`,
    );
  }, []);

  useEffect(() => {
    if (filtroAte && filtroDe > filtroAte) setFiltroAte(filtroDe);
  }, [filtroDe, filtroAte]);

  async function atualizarNotas(soSeMudou: boolean): Promise<string> {
    const [tabelas, pessoas] = await Promise.all([loadTabelas(), loadClientes()]);
    setListas(tabelas.listas);
    setProdutos(tabelas.produtos);
    setCatalog((atual) => rotulosDoCatalogo(tabelas.produtos, atual));
    setClientes(pessoas);
    const atual = ordersRef.current;
    const proximos = comPrecos(atual, { clientes: pessoas, listas: tabelas.listas, produtos: tabelas.produtos });
    setOrders(proximos);
    if (!proximos.length) return soSeMudou ? "" : "Cadastro atualizado. Ainda não há nota na tela.";
    if (soSeMudou && !notaMudou(atual, proximos)) return "";
    return respostaDoPedido(proximos, pessoas);
  }

  useEffect(() => {
    if (tela !== "pedidos") return;
    let ativo = true;
    atualizarNotas(true)
      .then((texto) => {
        if (ativo) publicar(texto);
      })
      .catch(() => undefined);
    return () => {
      ativo = false;
    };
  }, [tela]);

  async function aoAtualizar() {
    setAtualizando(true);
    try {
      publicar(await atualizarNotas(false));
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui atualizar o cadastro.");
    } finally {
      setAtualizando(false);
    }
  }

  async function carregarCatalogo() {
    const [tabelas, pessoas] = await Promise.all([loadTabelas(), loadClientes()]);
    setListas(tabelas.listas);
    setProdutos(tabelas.produtos);
    setCatalog((atual) => rotulosDoCatalogo(tabelas.produtos, atual));
    setClientes(pessoas);
    return { clientes: pessoas, listas: tabelas.listas, produtos: tabelas.produtos };
  }

  async function aoAtualizarPrecosTela() {
    setAtualizando(true);
    try {
      const catalogo = await carregarCatalogo();
      const atual = ordersRef.current;
      const abertas = atual.filter((order) => !order.concluido && order.tipo !== "compra");
      if (!abertas.length) {
        publicar(atual.length ? "Nenhuma boleta aberta para atualizar preço." : "Ainda não há nota na tela.");
        return;
      }
      const proximos = atual.map((order) =>
        order.concluido || order.tipo === "compra" ? order : precosForcadosNaNota(order, catalogo),
      );
      setOrders(proximos);
      const tabelas = [...new Set(proximos.filter((o) => !o.concluido && o.tipo !== "compra").map((o) => o.tabela).filter(Boolean))];
      publicar(
        tabelas.length === 1
          ? `Preços da tela atualizados pela tabela ${tabelas[0]}.`
          : `Preços da tela atualizados (${abertas.length} ${abertas.length === 1 ? "boleta" : "boletas"}).`,
      );
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui atualizar os preços.");
    } finally {
      setAtualizando(false);
    }
  }

  async function aoAtualizarPrecosNota(index: number) {
    const order = ordersRef.current[index];
    if (!order || order.concluido) return;
    if (order.tipo === "compra") {
      publicar("Compra não usa tabela de preço do cliente.");
      return;
    }
    const catalogo = await carregarCatalogo();
    const proxima = precosForcadosNaNota(order, catalogo);
    setOrders((current) => current.map((item, i) => (i === index ? proxima : item)));
    const nome = proxima.cliente.trim() || "Boleta";
    const pct = proxima.desconto > 0 ? ` Desconto geral: ${proxima.desconto}%.` : " Sem desconto geral.";
    publicar(
      proxima.tabela
        ? `${nome}: preços atualizados pela tabela ${proxima.tabela}.${pct}`
        : `${nome}: não achei tabela de preço para atualizar.`,
    );
  }

  function abrirCadastroProduto(item: OrderItem, tabela: string) {
    setProdutoNovo(aberturaDoItem(item, tabela));
  }

  async function salvarProdutoDoPedido(dados: ProdutoSalvo) {
    const formato = normalizarFormato(dados.formato);
    let produto = produtos.find(
      (item) => mesmoNome(item.name, dados.nome) && normalizarFormato(item.formato || "unidade") === formato,
    );
    if (!produto) {
      try {
        produto = await createProduto(dados.nome, formato);
      } catch (err) {
        const tabelas = await loadTabelas();
        produto = tabelas.produtos.find(
          (item) => mesmoNome(item.name, dados.nome) && normalizarFormato(item.formato || "unidade") === formato,
        );
        if (!produto) throw err;
      }
    }
    for (const [listaId, valor] of Object.entries(dados.precos)) {
      await saveTablePrice(Number(listaId), produto.id, valor);
    }
    const [tabelas, pessoas] = await Promise.all([loadTabelas(), loadClientes()]);
    setListas(tabelas.listas);
    setProdutos(tabelas.produtos);
    setCatalog((atual) => rotulosDoCatalogo(tabelas.produtos, atual));
    setClientes(pessoas);
    const base = separarFormato(dados.origem).nome || dados.origem;
    const proximos = comPrecos(
      ordersRef.current.map((order) => ({
        ...order,
        itens: order.itens.map((item) => {
          const nomeItem = separarFormato(item.produto).nome || item.produto;
          if (!mesmoNome(item.produto, dados.origem) && !mesmoNome(nomeItem, base)) return item;
          return { ...item, produto: dados.nome, tipo: formato, valor: 0, preco_tabela: true, conhecido: true };
        }),
      })),
      { clientes: pessoas, listas: tabelas.listas, produtos: tabelas.produtos },
    );
    setOrders(proximos);
    setProdutoNovo(null);
    publicar(`Cadastrei ${dados.nome}. ${respostaDoPedido(proximos, pessoas)}`);
  }

  function aoDigitarCliente(index: number, nome: string, commit: boolean) {
    const catalogo = { clientes, listas, produtos };
    setOrders((current) => current.map((order, i) => (i === index ? nomeNaBoleta(order, nome, catalogo, commit) : order)));
  }

  function escolherCliente(id: number) {
    const pessoa = clientes.find((item) => item.id === id);
    if (!pessoa) return;
    const proximos = comPrecos(
      ordersRef.current.map((order) => {
        const serve = !order.clienteId && listarClientes(order.cliente, clientes).some((item) => item.id === id);
        if (!serve) return order;
        return { ...order, cliente: pessoa.name, clienteId: pessoa.id, tabela: undefined };
      }),
      { clientes, listas, produtos },
    );
    setOrders(proximos);
    publicar(respostaDoPedido(proximos, clientes));
  }

  async function salvarDia(): Promise<boolean> {
    const atuais = ordersRef.current.filter((order) => order.tipo !== "compra" || compraComItem(order));
    const falta = faltaParaSalvar(atuais);
    if (falta) {
      setConfirmarSalvar(false);
      publicar(falta);
      return false;
    }
    setSalvando(true);
    try {
      const prontos = atuais.map(semReagenda);
      const resposta = await salvarBoletas(prontos.map((order) => pedidoParaSalvar(order)));
      setRevisao(null);
      setConfirmarSalvar(false);
      const gravados = semMarcasDeCompra(prontos).map((order, index) => ({
        ...order,
        id: resposta.ids[index] || order.id,
      }));
      ordersRef.current = gravados;
      setOrders(gravados);
      registrarPedidosSalvos(gravados);
      for (const order of prontos) registrarNaGradeDoDia(order);
      const verbo = atuais.every((order) => order.id) ? "Atualizei" : "Salvei";
      const reagendaTxt = textoReagendados(resposta.reagendados);
      publicar(
        `${verbo} ${resposta.salvos} ${resposta.salvos === 1 ? "pedido" : "pedidos"}. A conta usa o que foi entregue.${reagendaTxt}`,
      );
      return true;
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui salvar os pedidos.");
      return false;
    } finally {
      setSalvando(false);
    }
  }

  function boletasNaoSalvas(): { order: Order; index: number }[] {
    return orders
      .map((order, index) => ({ order, index }))
      .filter(({ order }) => pedidoPendenteNaTela(order));
  }

  function fecharAvisoNaoSalvos() {
    setPendenciaNaoSalvos(null);
    setAvisoNaoSalvosSolto(false);
    setAvisoNaoSalvosPos(null);
    avisoNaoSalvosArrasto.current = null;
  }

  function avisarNaoSalvos(acao: "abrir-pedidos" | "fechar-funil"): boolean {
    if (!ordersRef.current.some(pedidoPendenteNaTela)) return false;
    setAvisoNaoSalvosSolto(false);
    setAvisoNaoSalvosPos(null);
    avisoNaoSalvosArrasto.current = null;
    setPendenciaNaoSalvos(acao);
    return true;
  }

  function iniciarArrastoAviso(event: ReactMouseEvent<HTMLElement>) {
    if (event.button !== 0) return;
    const alvo = event.target as HTMLElement | null;
    if (alvo?.closest("button, a, input, select, textarea, label")) return;
    event.preventDefault();
    setAvisoNaoSalvosSolto(true);
    const caixa = event.currentTarget.closest(".aviso-nao-salvos") as HTMLElement | null;
    if (!caixa) return;
    const rect = caixa.getBoundingClientRect();
    const origem = { x: rect.left, y: rect.top };
    setAvisoNaoSalvosPos(origem);
    avisoNaoSalvosArrasto.current = { dx: event.clientX - origem.x, dy: event.clientY - origem.y };
    const mover = (ev: MouseEvent) => {
      const arrasto = avisoNaoSalvosArrasto.current;
      if (!arrasto) return;
      setAvisoNaoSalvosPos({ x: ev.clientX - arrasto.dx, y: ev.clientY - arrasto.dy });
    };
    const soltar = () => {
      avisoNaoSalvosArrasto.current = null;
      window.removeEventListener("mousemove", mover);
      window.removeEventListener("mouseup", soltar);
    };
    window.addEventListener("mousemove", mover);
    window.addEventListener("mouseup", soltar);
  }

  async function seguirAposNaoSalvos(acao: "abrir-pedidos" | "fechar-funil") {
    fecharAvisoNaoSalvos();
    if (acao === "abrir-pedidos") await abrirPedidos(true);
    else fecharPedidoFunil(true);
  }

  async function resolverNaoSalvos(modo: "salvar" | "descartar") {
    const pendencia = pendenciaNaoSalvos;
    if (!pendencia) return;
    if (modo === "salvar") {
      const ok = await salvarDia();
      if (!ok) return;
    } else {
      const pendentes = ordersRef.current.filter(pedidoPendenteNaTela);
      const nomes = pendentes.map((order) => order.cliente.trim() || "Sem nome");
      // Novos saem da tela; alterados voltam ao último conteúdo gravado/buscado.
      const resto = ordersRef.current
        .map((order) => {
          if (pedidoNovoNaTela(order)) return null;
          if (order.id && pedidoPendenteNaTela(order)) {
            const snap = snapshotsSalvosRef.current.get(order.id);
            return snap ? clonarPedidoSalvo(snap) : order;
          }
          return order;
        })
        .filter((order): order is Order => Boolean(order));
      ordersRef.current = resto;
      setOrders(resto);
      publicar(
        nomes.length === 1
          ? `Descartei alterações não salvas de ${nomes[0]}.`
          : `Descartei alterações não salvas em ${nomes.length} boletas.`,
      );
    }
    await seguirAposNaoSalvos(pendencia);
  }

  async function salvarUmaNaoSalva(order: Order, index: number) {
    const pendencia = pendenciaNaoSalvos;
    await salvarUma(order, index);
    const ainda = ordersRef.current.some(pedidoPendenteNaTela);
    if (!ainda && pendencia) await seguirAposNaoSalvos(pendencia);
  }

  function descartarUmaNaoSalva(order: Order, index: number) {
    const pendencia = pendenciaNaoSalvos;
    const nome = order.cliente.trim() || "Sem nome";
    const alvo = indiceDaNota(order, index);
    if (!pedidoNovoNaTela(order) && order.id) {
      const snap = snapshotsSalvosRef.current.get(order.id);
      if (snap) {
        const restaurado = clonarPedidoSalvo(snap);
        const lista = ordersRef.current.map((item, i) => (i === alvo ? restaurado : item));
        ordersRef.current = lista;
        setOrders(lista);
        publicar(`Descartei alterações não salvas de ${nome}.`);
        if (!lista.some(pedidoPendenteNaTela) && pendencia) void seguirAposNaoSalvos(pendencia);
        return;
      }
    }
    const resto = ordersRef.current.filter((_, i) => i !== alvo);
    ordersRef.current = resto;
    setOrders(resto);
    publicar(`Descartei a boleta não salva de ${nome}.`);
    if (!resto.some(pedidoPendenteNaTela) && pendencia) void seguirAposNaoSalvos(pendencia);
  }

  function falarCompra(frase: string): Promise<string> {
    const atuais = ordersRef.current;
    const index = rascunhoDeCompra(atuais);
    if (index < 0) return Promise.resolve("Marque Comprados numa nota de venda para montar a compra.");
    const aplicado = aplicarFalaCompra(atuais[index], frase, clientes);
    setOrders(atuais.map((order, i) => (i === index ? { ...aplicado.order, tipo: "compra", id: undefined } : order)));
    return Promise.resolve(aplicado.resposta);
  }

  function indiceDaNota(order: Order, index: number): number {
    if (order.id) {
      const peloId = ordersRef.current.findIndex((item) => item.id === order.id);
      if (peloId >= 0) return peloId;
    }
    return index;
  }

  function tirarDaTela(order: Order, index: number) {
    const alvo = indiceDaNota(order, index);
    setOrders((current) => {
      const restante = current.filter((_, i) => i !== alvo);
      return order.tipo === "compra" ? restante : sincronizarCompra(restante);
    });
  }

  async function salvarUma(order: Order, index: number, concluir = false) {
    if (order.concluido) return;
    const falta = faltaParaSalvar([order]);
    if (falta) {
      publicar(falta);
      return;
    }
    const pronto = semReagenda(order);
    const eraNova = !order.id;
    const resposta = await salvarBoletas([pedidoParaSalvar(pronto, concluir)]);
    const id = resposta.ids[0] || order.id;
    const nome = order.cliente.trim() || "este pedido";
    if (!id || resposta.salvos < 1) {
      publicar(`Não consegui gravar o pedido de ${nome}.`);
      return;
    }
    const alvo = indiceDaNota(order, index);
    setOrders((current) => {
      const next = current.map((item, i) => (i === alvo ? { ...pronto, id, concluido: concluir || item.concluido } : item));
      ordersRef.current = next;
      registrarPedidosSalvos(next.filter((item) => item.id === id));
      return next;
    });
    registrarNaGradeDoDia(pronto);
    publicar(concluir ? `Concluí o pedido de ${nome}.` : eraNova ? `Salvei o pedido de ${nome}.` : `Atualizei o pedido de ${nome}.`);
  }

  function registrarNaGradeDoDia(order: Order) {
    if (order.tipo === "compra") return;
    const nome = order.cliente.trim();
    if (!nome) return;
    const dataIso = isoDaDataNota(order.data);
    const dia = dataIso ? diaIdDeIso(dataIso) : null;
    if (!dia) return;
    const planilha = lerPlanilhaRecorrente();
    const proxima = incluirClienteNoDia(planilha, nome, dia, (a, b) => mesmoCliente(a, b, clientes));
    if (proxima) gravarPlanilhaRecorrente(proxima);
  }

  async function marcarPagoUma(order: Order, index: number) {
    const pago = !order.pago;
    const proximo = { ...order, pago };
    const alvo = indiceDaNota(order, index);
    setOrders((current) => current.map((item, i) => (i === alvo ? proximo : item)));
    const nome = order.cliente.trim() || "esta nota";
    if (!order.id && !order.clienteId && !(order.tabela || "").trim()) {
      publicar(pago ? `${nome}: marcada como paga. Grave a nota para registrar.` : `${nome}: em aberto.`);
      return;
    }
    const falta = faltaParaSalvar([proximo]);
    if (falta) {
      publicar(falta);
      return;
    }
    try {
      const resposta = await salvarBoletas([pedidoParaSalvar(semReagenda(proximo))]);
      const id = resposta.ids[0] || order.id;
      const gravado = { ...proximo, id };
      setOrders((current) => current.map((item, i) => (i === alvo ? gravado : item)));
      registrarPedidosSalvos([gravado]);
      publicar(pago ? `${nome}: paga.` : `${nome}: em aberto.`);
    } catch (err) {
      setOrders((current) => current.map((item, i) => (i === alvo ? order : item)));
      publicar(err instanceof Error ? err.message : "Não consegui gravar o pagamento.");
    }
  }

  async function desconcluirUma(order: Order, index: number) {
    if (!order.concluido || !order.id) return;
    const resposta = await salvarBoletas([pedidoParaSalvar(order, false, true)]);
    const id = resposta.ids[0] || order.id;
    const alvo = indiceDaNota(order, index);
    setOrders((current) => current.map((item, i) => (i === alvo ? { ...item, id, concluido: false } : item)));
    const nome = order.cliente.trim() || "este pedido";
    publicar(`Reabri o pedido de ${nome} para edição.`);
  }

  async function excluirUma(order: Order, index: number) {
    if (order.concluido) {
      publicar("Este pedido já foi concluído. Não dá para excluir.");
      return;
    }
    if (order.id) await excluirBoleta(order.id);
    tirarDaTela(order, index);
    const nome = order.cliente.trim() || "este pedido";
    publicar(order.id ? `Excluí o pedido de ${nome}.` : `Tirei o pedido de ${nome} da tela. Ele ainda não estava no banco.`);
  }

  async function pedidosIguaisNoDia(candidato: Order, dataIso: string, ignorarId?: string): Promise<Order[]> {
    const chave = assinaturaPedido(candidato);
    const naTela = ordersRef.current.filter(
      (order) =>
        order.tipo !== "compra" &&
        order.id !== ignorarId &&
        isoDaDataNota(order.data) === dataIso &&
        assinaturaPedido(order) === chave,
    );
    try {
      const extrato = await consultarBoletas(dataIso, dataIso, candidato.clienteId);
      const noBanco = notasDoExtrato(extrato).filter(
        (order) =>
          order.tipo !== "compra" &&
          order.id !== ignorarId &&
          !naTela.some((tela) => tela.id && tela.id === order.id) &&
          assinaturaPedido(order) === chave,
      );
      return [...naTela, ...noBanco];
    } catch {
      return naTela;
    }
  }

  async function copiarUma(
    order: Order,
    dataIso: string,
    forcar = false,
  ): Promise<{ status: "ok" } | { status: "ja-existe"; pedido: Order }> {
    if (order.tipo === "compra") {
      publicar("Só copio boleta de venda.");
      return { status: "ok" };
    }
    const data = dataParaNota(dataIso);
    if (!data) {
      publicar("Informe a data para a cópia.");
      return { status: "ok" };
    }
    const copia = clonarPedido(order, data);
    const falta = faltaParaSalvar([copia]);
    if (falta) {
      publicar(falta);
      return { status: "ok" };
    }
    if (!forcar) {
      const iguais = await pedidosIguaisNoDia(copia, dataIso, order.id);
      if (iguais.length) return { status: "ja-existe", pedido: iguais[0] };
    }
    const resposta = await salvarBoletas([pedidoParaSalvar(copia)]);
    const id = resposta.ids[0];
    const nome = order.cliente.trim() || "este pedido";
    if (!id || resposta.salvos < 1) {
      publicar(`Não consegui copiar o pedido de ${nome}.`);
      return { status: "ok" };
    }
    setOrders((current) => {
      const rascunho = current.find((item) => item.tipo === "compra" && !item.id);
      const base = current.filter((item) => !(item.tipo === "compra" && !item.id));
      const juntos = [...base, { ...copia, id }];
      return rascunho ? sincronizarCompra([...juntos, rascunho]) : garantirCompra(juntos);
    });
    publicar(`Copiei o pedido de ${nome} para ${data}.`);
    return { status: "ok" };
  }

  async function duplicarDia(dataIso: string, forcar = false) {
    const data = dataParaNota(dataIso);
    if (!data) {
      publicar("Informe a data de destino.");
      return;
    }
    const fontes = ordersRef.current.filter((order) => order.tipo !== "compra");
    if (!fontes.length) {
      publicar("Não há pedidos de venda na tela para duplicar.");
      return;
    }
    const copias = fontes.map((order) => clonarPedido(order, data));
    const falta = faltaParaSalvar(copias);
    if (falta) {
      publicar(falta);
      return;
    }
    setSalvando(true);
    try {
      if (!forcar) {
        const repetidos: string[] = [];
        let primeiroIgual: Order | null = null;
        for (let i = 0; i < copias.length; i++) {
          const iguais = await pedidosIguaisNoDia(copias[i], dataIso, fontes[i]?.id);
          if (iguais.length) {
            if (!primeiroIgual) primeiroIgual = iguais[0];
            const nome = copias[i].cliente.trim() || "pedido";
            if (!repetidos.includes(nome)) repetidos.push(nome);
          }
        }
        if (repetidos.length) {
          setAvisoDuplicata(
            repetidos.length === 1
              ? `Já existe um pedido igual de ${repetidos[0]} em ${data}. Duplicar de novo?`
              : `Já existem pedidos iguais neste dia (${repetidos.join(", ")}). Duplicar de novo?`,
          );
          setPedidoIgualDuplicar(primeiroIgual);
          setVerPedidoIgual(false);
          setConfirmarDuplicar("forcar");
          return;
        }
      }
      const resposta = await salvarBoletas(copias.map((order) => pedidoParaSalvar(order)));
      const gravados = copias.map((order, index) => ({ ...order, id: resposta.ids[index] || undefined }));
      if (gravados.some((order) => !order.id) || resposta.salvos < gravados.length) {
        publicar("Não consegui gravar todas as cópias.");
        return;
      }
      setOrders(garantirCompra(gravados));
      setFiltroDe(dataIso);
      setFiltroAte("");
      setFiltroCliente("");
      setFiltroClienteNome("");
      setMostrarColheita(false);
      setMostrarRota(false);
      setConfirmarDuplicar(null);
      setAvisoDuplicata("");
      setPedidoIgualDuplicar(null);
      setVerPedidoIgual(false);
      publicar(
        `Dupliquei ${gravados.length} ${gravados.length === 1 ? "pedido" : "pedidos"} para ${data}.`,
      );
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui duplicar os pedidos.");
    } finally {
      setSalvando(false);
    }
  }

  async function salvarCompra(): Promise<string> {
    const compra = ordersRef.current.find((order) => order.tipo === "compra" && !order.id && compraComItem(order));
    if (!compra) return "Marque Comprados numa nota antes de salvar a compra.";
    const falta = faltaParaSalvar([compra]);
    if (falta) return falta;
    setSalvando(true);
    try {
      const resposta = await salvarBoletas([pedidoParaSalvar(compra)]);
      const id = resposta.ids[0];
      if (!id) return "A compra não voltou gravada.";
      setOrders((current) =>
        semMarcasDeCompra(current).map((order) => (order.tipo === "compra" && !order.id ? { ...order, id } : order)),
      );
      const quem = compra.cliente.trim() || "o fornecedor";
      return `Salvei a compra de ${quem}. A boleta ficou na tela. Pode marcar a próxima.`;
    } catch (err) {
      return err instanceof Error ? err.message : "Não consegui salvar a compra.";
    } finally {
      setSalvando(false);
    }
  }

  function limparTela() {
    setOrders([]);
    setRevisao(null);
    setConfirmarLimpar(false);
    setConfirmarSalvar(false);
    setConfirmarDuplicar(null);
    setAvisoDuplicata("");
    setPedidoIgualDuplicar(null);
    setVerPedidoIgual(false);
    setMostrarColheita(false);
    setMostrarRota(false);
    limparRascunhoPedidos();
    publicar("Limpei a tela. Os pedidos já gravados continuam na busca.");
  }

  async function garantirClientes(): Promise<Cliente[]> {
    if (clientes.length) return clientes;
    const lista = await loadClientes();
    setClientes(lista);
    return lista;
  }

  function nomeCasaFunil(grade: string, pedido: string, lista: Cliente[] = clientes): boolean {
    return mesmoCliente(grade, pedido, lista);
  }

  function fecharPedidoFunil(forcar = false) {
    if (!forcar && avisarNaoSalvos("fechar-funil")) return;
    fecharAvisoNaoSalvos();
    setFunilPedido(null);
    setFunilJanela("normal");
    setFunilPos(null);
    abrirChat(false);
    setOrders([]);
    setRevisao(null);
    setSugestaoAlface(null);
    setFunilVersao((n) => n + 1);
  }

  function arrastarJanelaFunil(event: ReactMouseEvent<HTMLElement>) {
    if (funilJanela === "max") return;
    if ((event.target as HTMLElement).closest("button, .funil-janela-btns")) return;
    const janela = event.currentTarget.parentElement;
    if (!janela) return;
    event.preventDefault();
    const rect = janela.getBoundingClientRect();
    const offsetX = event.clientX - rect.left;
    const offsetY = event.clientY - rect.top;
    setFunilPos({ left: rect.left, top: rect.top });

    function mover(ev: MouseEvent) {
      const largura = rect.width;
      const left = Math.max(0, Math.min(window.innerWidth - Math.min(largura, 160), ev.clientX - offsetX));
      const top = Math.max(0, Math.min(window.innerHeight - 40, ev.clientY - offsetY));
      setFunilPos({ left, top });
    }
    function soltar() {
      window.removeEventListener("mousemove", mover);
      window.removeEventListener("mouseup", soltar);
    }
    window.addEventListener("mousemove", mover);
    window.addEventListener("mouseup", soltar);
  }

  async function pedirDoFunil(clienteGrade: string, dataIso: string) {
    const nome = nomeClienteGrade(clienteGrade);
    const dataNota = dataParaNota(dataIso);
    if (!nome || !dataNota) return;
    setFiltroDe(dataIso);
    setFiltroAte("");
    setFiltroCliente("");
    setFiltroClienteNome(nome);
    setModoNota("venda");
    setMostrarColheita(false);
    setMostrarRota(false);
    setFunilJanela("normal");
    setFunilPos(null);
    abrirChat(true);
    try {
      const lista = await garantirClientes();
      const cadastro = clienteDoApelido(nome, lista);
      const quem = cadastro?.name || nome;
      const titulo = cadastro && quem !== nome ? `${quem} · ${nome}` : nome;
      setFiltroClienteNome(quem);
      setFunilPedido({ cliente: titulo, dataIso });
      const extrato = await consultarBoletas(dataIso, dataIso);
      const notas = notasDoExtrato(extrato).filter(
        (order) => order.tipo !== "compra" && nomeCasaFunil(nome, order.cliente, lista),
      );
      if (notas.length) {
        setOrders(garantirCompra(notas));
        publicar(
          `Pedido de ${quem} em ${dataNota}. Cole a conversa — se for do mesmo cliente, pergunto se acrescento neste ou incluo outro.`,
        );
      } else {
        setOrders(
          garantirCompra([
            {
              tipo: "venda",
              cliente: quem,
              clienteId: cadastro?.id,
              data: dataNota,
              endereco: cadastro?.endereco || "",
              desconto: cadastro?.desconto_pedido || 0,
              tabela: cadastro?.price_list_name || "",
              itens: [],
            },
          ]),
        );
        publicar(`O que ${quem} quer para ${dataNota}? Cole a conversa ou diga os itens — tudo entra neste pedido.`);
      }
    } catch (err) {
      setOrders(
        garantirCompra([
          {
            tipo: "venda",
            cliente: nome,
            data: dataNota,
            endereco: "",
            desconto: 0,
            itens: [],
          },
        ]),
      );
      publicar(err instanceof Error ? err.message : `O que ${nome} quer para ${dataNota}?`);
    }
  }

  async function pedidoSalvoDoFunil(clienteGrade: string, dataIso: string): Promise<Order | null> {
    const nome = nomeClienteGrade(clienteGrade);
    if (!nome) return null;
    const lista = await garantirClientes();
    const extrato = await consultarBoletas(dataIso, dataIso);
    const notas = notasDoExtrato(extrato).filter(
      (order) => order.tipo !== "compra" && nomeCasaFunil(nome, order.cliente, lista),
    );
    if (!notas.length) return null;
    const concluido = notas.find((order) => order.concluido);
    return concluido || notas[0];
  }

  async function alternarEntregueFunil(clienteGrade: string, dataIso: string): Promise<string> {
    const order = await pedidoSalvoDoFunil(clienteGrade, dataIso);
    const nome = nomeClienteGrade(clienteGrade) || "cliente";
    if (!order?.id) throw new Error(`Não achei boleta de ${nome} em ${diaMes(dataIso)}. Salve o pedido pelo chat antes.`);
    if (order.concluido) {
      await salvarBoletas([pedidoParaSalvar(order, false, true)]);
      return `${nome}: reabri o pedido (${diaMes(dataIso)}).`;
    }
    const falta = faltaParaSalvar([order]);
    if (falta) throw new Error(falta);
    await salvarBoletas([pedidoParaSalvar(semReagenda(order), true)]);
    return `${nome}: entregue em ${diaMes(dataIso)}.`;
  }

  async function alternarPagoFunil(clienteGrade: string, dataIso: string): Promise<string> {
    const order = await pedidoSalvoDoFunil(clienteGrade, dataIso);
    const nome = nomeClienteGrade(clienteGrade) || "cliente";
    if (!order?.id) throw new Error(`Não achei boleta de ${nome} em ${diaMes(dataIso)}. Salve o pedido pelo chat antes.`);
    const pago = !order.pago;
    const proximo = { ...order, pago };
    const falta = faltaParaSalvar([proximo]);
    if (falta) throw new Error(falta);
    await salvarBoletas([pedidoParaSalvar(semReagenda(proximo))]);
    return pago ? `${nome}: paga (${diaMes(dataIso)}).` : `${nome}: em aberto (${diaMes(dataIso)}).`;
  }

  async function duplicarDoFunil(clienteGrade: string, deIso: string, paraIso: string): Promise<string> {
    const nome = nomeClienteGrade(clienteGrade);
    const dataDestino = dataParaNota(paraIso);
    if (!nome || !dataDestino) return "Informe a data de destino.";
    try {
      const lista = await garantirClientes();
      const extrato = await consultarBoletas(deIso, deIso);
      const fontes = notasDoExtrato(extrato).filter(
        (order) => order.tipo !== "compra" && nomeCasaFunil(nome, order.cliente, lista),
      );
      if (!fontes.length) {
        return `Nome na grade para ${diaMes(paraIso)}. Não achei boleta de ${nome} em ${diaMes(deIso)} para copiar.`;
      }
      let copiados = 0;
      for (const fonte of fontes) {
        const resultado = await copiarUma(fonte, paraIso, false);
        if (resultado.status === "ok") copiados += 1;
        else if (resultado.status === "ja-existe") {
          return `Já existe pedido igual de ${nome} em ${dataDestino}. A grade foi atualizada.`;
        }
      }
      return copiados
        ? `Copiei ${copiados} ${copiados === 1 ? "pedido" : "pedidos"} de ${nome} para ${dataDestino}.`
        : `Grade atualizada para ${dataDestino}.`;
    } catch (err) {
      throw err instanceof Error ? err : new Error("Não consegui duplicar o pedido.");
    }
  }

  async function abrirPedidos(ignorarNaoSalvos = false) {
    if (!ignorarNaoSalvos && avisarNaoSalvos("abrir-pedidos")) return;
    setBuscando(true);
    try {
      const ateAjustada = filtroAte && filtroDe > filtroAte ? filtroDe : filtroAte;
      if (ateAjustada !== filtroAte) setFiltroAte(ateAjustada);
      const ate = ateAjustada || filtroDe;
      const extrato = await consultarBoletas(filtroDe, ate, filtroCliente ? Number(filtroCliente) : undefined);
      const buscaNome = foldTexto(filtroClienteNome);
      const notas = notasDoExtrato(extrato).filter((order) => {
        if (filtroCliente || !buscaNome) return true;
        const nomeNota = foldTexto(order.cliente);
        return nomeNota === buscaNome || nomeNota.includes(buscaNome) || buscaNome.includes(nomeNota);
      });
      setOrders(notas);
      registrarPedidosSalvos(notas);
      setRevisao(null);
      publicar(
        notas.length
          ? `Abri ${notas.length} ${notas.length === 1 ? "pedido" : "pedidos"}.`
          : filtroAte && filtroAte !== filtroDe
            ? "Nenhum pedido nesse período."
            : "Nenhum pedido nesse dia.",
      );
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui abrir os pedidos.");
    } finally {
      setBuscando(false);
    }
  }

  function pedirInclusao(cliente: ClienteParaIncluir) {
    setIncluir({ ...cliente, seq: Date.now() });
    irPara("clientes");
  }

  async function buscarSugestaoAlface(orders: Order[]): Promise<SugestaoAlface | null> {
    for (let index = 0; index < orders.length; index += 1) {
      const order = orders[index];
      if (order.tipo === "compra") continue;
      if (!order.itens.some((item) => item.qtd > 0 && alfaceSemVariedade(item.produto))) continue;
      const clienteId =
        order.clienteId ?? listarClientes(order.cliente, clientes).find((item) => item.id)?.id;
      if (!clienteId) continue;
      try {
        const ate = new Date();
        const de = new Date();
        de.setDate(de.getDate() - 120);
        const extrato = await consultarBoletas(iso(de), iso(ate), clienteId);
        const pedidos = (extrato.clientes[0]?.pedidos ?? [])
          .filter((pedido) => pedido.tipo !== "compra" && pedido.id !== order.id)
          .slice()
          .reverse();
        for (const pedido of pedidos) {
          const achado = alfaceDoHistorico(pedido.itens);
          if (!achado) continue;
          return {
            orderIndex: index,
            clienteId,
            clienteNome: order.cliente.trim() || "cliente",
            variedade: achado.variedade,
            produtoSugerido: achado.produtoSugerido,
          };
        }
      } catch {
        /* sem histórico, segue sem perguntar */
      }
    }
    return null;
  }

  function decidirAlface(aceitar: boolean) {
    const pendente = sugestaoAlfaceRef.current;
    setSugestaoAlface(null);
    if (!pendente) return;
    if (!aceitar) {
      publicar("Ok, deixei a alface sem especificar. Pode ajustar na nota.");
      return;
    }
    const catalogo = { clientes, listas, produtos };
    const proximos = comPrecos(aplicarSugestaoAlface(ordersRef.current, pendente), catalogo);
    setOrders(proximos);
    publicar(`Pronto: coloquei ${pendente.produtoSugerido.toLocaleLowerCase("pt-BR")} como da última vez.`);
  }

  async function decidirAvisoAdministrador(avisar: boolean): Promise<string> {
    setInterpretadorFora(false);
    if (!avisar) return "Ok. Insira o pedido na nota ou tente mais tarde.";
    try {
      await avisarAdministrador(
        "O interpretador de conversa está indisponível. O operador pediu para avisar.",
      );
      return "Avisei o administrador.";
    } catch (err) {
      const texto = err instanceof Error ? err.message : "";
      if (/não achei administrador/i.test(texto)) return "Não achei administrador com celular para avisar.";
      if (/whatsapp gateway não configurado/i.test(texto)) {
        return "O WhatsApp não está configurado. Não avisei o administrador.";
      }
      return "Não consegui avisar o administrador.";
    }
  }

  function fatosParaIa(): { cliente: string; data: string; tabela: string; endereco: string } {
    if (funilPedido) {
      const nome = funilPedido.cliente.split("·")[0].trim();
      const nota = ordersRef.current.find(
        (order) => order.tipo !== "compra" && foldTexto(order.cliente) === foldTexto(nome),
      );
      return {
        cliente: nota?.cliente.trim() || nome,
        data: nota?.data.trim() || dataParaNota(funilPedido.dataIso),
        tabela: nota?.tabela || "",
        endereco: nota?.endereco || "",
      };
    }
    const vendas = ordersRef.current.filter((order) => order.tipo !== "compra" && order.cliente.trim());
    const nomes = [...new Set(vendas.map((order) => foldTexto(order.cliente)))];
    if (nomes.length !== 1) return { cliente: "", data: "", tabela: "", endereco: "" };
    const nota = vendas[vendas.length - 1];
    return {
      cliente: nota.cliente.trim(),
      data: nota.data.trim(),
      tabela: nota.tabela || "",
      endereco: nota.endereco || "",
    };
  }

  async function onEnviar(frase: string): Promise<string> {
    const pendenteAlface = sugestaoAlfaceRef.current;
    if (pendenteAlface) {
      if (pareceAfirmacao(frase)) {
        setSugestaoAlface(null);
        const catalogoAtual = { clientes, listas, produtos };
        const proximos = comPrecos(aplicarSugestaoAlface(ordersRef.current, pendenteAlface), catalogoAtual);
        setOrders(proximos);
        return `Pronto: coloquei ${pendenteAlface.produtoSugerido.toLocaleLowerCase("pt-BR")} como da última vez.`;
      }
      if (pareceNegacao(frase)) {
        setSugestaoAlface(null);
        return "Ok, deixei a alface sem especificar. Pode ajustar na nota.";
      }
    }

    if (interpretadorForaRef.current) {
      if (pareceAfirmacao(frase)) return decidirAvisoAdministrador(true);
      if (pareceNegacao(frase)) return decidirAvisoAdministrador(false);
      setInterpretadorFora(false);
    }

    let pessoas = clientes;
    let folhas = listas;
    let itens = produtos;
    try {
      const [tabelas, lista] = await Promise.all([loadTabelas(), loadClientes()]);
      pessoas = lista;
      folhas = tabelas.listas;
      itens = tabelas.produtos;
      setClientes(lista);
      setListas(tabelas.listas);
      setProdutos(tabelas.produtos);
    } catch {
      /* segue com o cadastro que já está na tela */
    }
    const catalogo = { clientes: pessoas, listas: folhas, produtos: itens };
    const atuais = ordersRef.current;
    const ajuste = aplicarResposta(atuais, frase, catalogo);
    if (ajuste) {
      setRevisao(null);
      const proximos = comPrecos(ajuste, catalogo);
      setOrders(proximos);
      const sugestao = await buscarSugestaoAlface(proximos);
      if (sugestao) {
        setSugestaoAlface(sugestao);
        return `${respostaDoPedido(proximos, pessoas)} ${perguntaAlface(sugestao)}`;
      }
      return respostaDoPedido(proximos, pessoas);
    }
    try {
      const textoIa = modoNota === "compra" ? `Compra de fornecedor.\n${frase}` : frase;
      const telaIa = funilPedido && modoNota !== "compra" ? "funil" : "pedidos";
      const fatos = fatosParaIa();
      let contexto = "";
      let clienteFixo = "";
      let observacaoCom = false;
      try {
        const bases = await carregarContextosIa();
        const base = bases.find((item) => item.tela === telaIa);
        if (base) {
          contexto = montarContexto(base.instrucao, fatos);
          observacaoCom = base.observacao_com;
          if (base.cliente_da_tela && fatos.cliente.trim()) clienteFixo = fatos.cliente.trim();
        }
      } catch {
        /* a frase segue sem o texto desta tela */
      }
      let result;
      try {
        result = await convertConversation(textoIa, {
          contexto,
          cliente: clienteFixo,
          observacaoCom,
        });
      } catch (err) {
        console.error("[commerce-frontend] interpretador", err);
        setInterpretadorFora(true);
        return TEXTO_INTERPRETADOR_FORA;
      }
      const recebidos = modoNota === "compra" ? result.orders.map((order) => ({ ...order, tipo: "compra" as const })) : result.orders;
      const formatados = prepararPedidos(aplicarFormatoDaConversa(recebidos, frase, itens), frase, catalogo);
      const novos = comPrecos(
        amarrarAoPedidoUnico(atuais, completarDatas(formatados, atuais, frase)),
        catalogo,
      );
      setCatalog(rotulosDoCatalogo(itens, result.catalog));
      if (!atuais.length) {
        setRevisao(null);
        setOrders(novos);
        const sugestao = await buscarSugestaoAlface(novos);
        if (sugestao) {
          setSugestaoAlface(sugestao);
          return `${respostaDoPedido(novos, pessoas)} ${perguntaAlface(sugestao)}`;
        }
        return respostaDoPedido(novos, pessoas);
      }
      const livres = novos.filter((novo) => temNomeNovo(atuais, [novo]));
      const conflitos = novos.filter((novo) => !temNomeNovo(atuais, [novo]));
      if (conflitos.length) {
        const automaticos = conflitos.filter((novo) => podeAcrescentarDireto(atuais, novo, frase));
        const manuais = conflitos.filter((novo) => !podeAcrescentarDireto(atuais, novo, frase));
        let proximos = livres.length ? [...atuais, ...livres] : [...atuais];
        for (const novo of automaticos) {
          proximos = atualizarUm(proximos, novo);
        }
        if (automaticos.length && !manuais.length) {
          setRevisao(null);
          const comTabela = comPrecos(proximos, catalogo);
          setOrders(comTabela);
          const nomes = automaticos.map((item) => item.cliente.trim() || "pedido").join(", ");
          const sugestao = await buscarSugestaoAlface(comTabela);
          const base = livres.length
            ? `${respostaDoPedido(livres, pessoas)} Acrescentei em ${nomes}.`
            : `Acrescentei em ${nomes}.`;
          if (sugestao) {
            setSugestaoAlface(sugestao);
            return `${base} ${perguntaAlface(sugestao)}`;
          }
          return base;
        }
        setOrders(comPrecos(proximos, catalogo));
        if (manuais.length) {
          setRevisao({ fila: manuais, indice: 0 });
          const extra = [
            livres.length ? respostaDoPedido(livres, pessoas) : "",
            automaticos.length
              ? `Acrescentei em ${automaticos.map((item) => item.cliente.trim() || "pedido").join(", ")}.`
              : "",
          ]
            .filter(Boolean)
            .join(" ");
          return `${extra ? `${extra} ` : ""}${perguntaDeUm(manuais[0], 1, manuais.length)}`;
        }
      }
      setRevisao(null);
      const juntos = [...atuais, ...novos];
      setOrders(juntos);
      const quem = atuais.map((item) => item.cliente.trim()).filter(Boolean).join(", ");
      const segue = quem ? ` O pedido de ${quem} continua na tela.` : " O pedido que já estava na tela continua.";
      const sugestao = await buscarSugestaoAlface(juntos);
      if (sugestao) {
        setSugestaoAlface(sugestao);
        return `${respostaDoPedido(novos, pessoas)}${segue} ${perguntaAlface(sugestao)}`;
      }
      return `${respostaDoPedido(novos, pessoas)}${segue}`;
    } catch (err) {
      console.error("[commerce-frontend] nota", err);
      const texto = err instanceof Error ? err.message : "";
      return texto || "Não consegui montar a nota. Insira o pedido manualmente.";
    }
  }

  function decidirListagem(modo: DecisaoListagem) {
    if (!revisao) return;
    const atuais = ordersRef.current;
    const resto = revisao.fila.slice(revisao.indice);
    const atual = resto[0];
    if (!atual) {
      setRevisao(null);
      return;
    }
    if (modo === "todos-atualizar" || modo === "todos-substituir" || modo === "todos-incluir") {
      const escolha =
        modo === "todos-atualizar" ? "atualizar" : modo === "todos-substituir" ? "substituir" : "incluir";
      const proximos = resto.reduce((acc, novo) => aplicarDecisao(acc, novo, escolha), atuais);
      ordersRef.current = proximos;
      setOrders(proximos);
      setRevisao(null);
      publicar(
        escolha === "atualizar"
          ? `Acrescentei em ${resto.length} ${resto.length === 1 ? "pedido" : "pedidos"}.`
          : escolha === "substituir"
            ? `Substituí ${resto.length} ${resto.length === 1 ? "pedido" : "pedidos"}.`
            : `Incluí ${resto.length} ${resto.length === 1 ? "pedido" : "pedidos"}.`,
      );
      return;
    }
    const proximos = aplicarDecisao(atuais, atual, modo);
    ordersRef.current = proximos;
    setOrders(proximos);
    const seguinte = revisao.indice + 1;
    const nome = atual.cliente.trim() || "este pedido";
    if (seguinte >= revisao.fila.length) {
      setRevisao(null);
      publicar(
        modo === "atualizar"
          ? `Acrescentei em ${nome}.`
          : modo === "substituir"
            ? `Substituí os itens de ${nome}.`
            : modo === "incluir"
              ? `Incluí ${nome}.`
              : `Deixei ${nome} como estava.`,
      );
      return;
    }
    setRevisao({ fila: revisao.fila, indice: seguinte });
    publicar(perguntaDeUm(revisao.fila[seguinte], seguinte + 1, revisao.fila.length));
  }

  const impressao = ordemDeImpressao(orders);
  const cobranca = resumoCobranca(orders);
  const contabilidade = contabilidadeCobranca(orders);
  const periodoCobranca = periodoDaPesquisa(filtroDe, filtroAte || filtroDe);
  const totalCobranca = cobranca.reduce((soma, bloco) => soma + bloco.total, 0);
  const compraAberta = orders.find((order) => order.tipo === "compra" && !order.id) ?? null;
  const notasNaTela = orders.some((order) => order.tipo !== "compra" || Boolean(order.id));

  const gravados = orders.length > 0 && orders.every((order) => order.id);

  return (
    <div className="area">
      <AreaTrabalho tela={tela} ferramentasAbertas={ferramentasAbertas} onTela={irPara} onFerramentas={abrirFerramentas}>
        {tela === "pedidos" ? (
          <>
            <label className="ferramenta-marca" title="Mostrar somente produtos com quantidade">
              <input
                type="checkbox"
                checked={onlyWithQty}
                onChange={(event) => setOnlyWithQty(event.target.checked)}
              />
              Só com quantidade
            </label>
            <button
              className="acao"
              type="button"
              disabled={atualizando}
              title="Recarrega clientes e tabelas do cadastro"
              onClick={() => void aoAtualizar()}
            >
              <IconeAcao nome="atualizar" />
              {atualizando ? "Atualizando…" : "Atualizar"}
            </button>
            <button
              className="acao"
              type="button"
              disabled={atualizando || orders.length === 0}
              title="Atualiza os preços das boletas abertas com a tabela do cadastro"
              onClick={() => void aoAtualizarPrecosTela()}
            >
              <IconeAcao nome="atualizar" />
              Preços
            </button>
            <button className="acao" type="button" onClick={() => window.print()} disabled={orders.length === 0}>
              <IconeAcao nome="imprimir" />
              Imprimir
            </button>
            <button className="acao" type="button" onClick={imprimirCobranca} disabled={cobranca.length === 0}>
              <IconeAcao nome="cobranca" />
              Cobrança
            </button>
            <button
              className="acao"
              type="button"
              title="Relatório CONTABILIDADE (palitos, período, quem recebeu)"
              onClick={imprimirContabilidade}
              disabled={contabilidade.length === 0}
            >
              <IconeAcao nome="cobranca" />
              Contabilidade
            </button>
            <button
              className="acao"
              type="button"
              title="Lista de colheita"
              disabled={orders.length === 0}
              onClick={() => {
                setMostrarRota(false);
                setMostrarColheita(true);
              }}
            >
              <IconeAcao nome="colheita" />
              Colheita
            </button>
            <button
              className="acao"
              type="button"
              title="Criar rota"
              disabled={orders.length === 0}
              onClick={() => {
                setMostrarColheita(false);
                setMostrarRota(true);
              }}
            >
              <IconeAcao nome="rota" />
              Rota
            </button>
            <button
              className="acao"
              type="button"
              title="Enviar listas no WhatsApp"
              disabled={orders.length === 0}
              onClick={() => setMostrarWhatsApp(true)}
            >
              <IconeAcao nome="whatsapp" />
              WhatsApp
            </button>
            {confirmarSalvar ? (
              <div className="confirma">
                <span>
                  {orders.every((order) => order.id)
                    ? "Gravar as alterações destes pedidos?"
                    : "Salvar estes pedidos?"}
                </span>
                <button className="primary" type="button" disabled={salvando} onClick={() => void salvarDia()}>
                  {salvando ? "Salvando…" : "Confirmar"}
                </button>
                <button type="button" onClick={() => setConfirmarSalvar(false)} disabled={salvando}>
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                className="acao primary"
                type="button"
                title={gravados ? "Atualizar pedidos" : "Salvar o dia"}
                disabled={orders.length === 0}
                onClick={() => {
                  setConfirmarLimpar(false);
                  setConfirmarDuplicar(null);
                  setAvisoDuplicata("");
                  setConfirmarSalvar(true);
                }}
              >
                <IconeAcao nome="salvar" />
                Salvar
              </button>
            )}
            {confirmarDuplicar === "forcar" ? (
              <div className="confirma">
                <span>{avisoDuplicata || "Já existe pedido igual neste dia. Duplicar de novo?"}</span>
                {pedidoIgualDuplicar ? (
                  <button
                    type="button"
                    disabled={salvando}
                    onClick={() => setVerPedidoIgual((aberto) => !aberto)}
                  >
                    {verPedidoIgual ? "Ocultar pedido" : "Ver pedido"}
                  </button>
                ) : null}
                <button
                  className="primary"
                  type="button"
                  disabled={salvando || !dataDuplicar}
                  onClick={() => void duplicarDia(dataDuplicar, true)}
                >
                  {salvando ? "Duplicando…" : "Duplicar mesmo assim"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setConfirmarDuplicar(null);
                    setAvisoDuplicata("");
                    setPedidoIgualDuplicar(null);
                    setVerPedidoIgual(false);
                  }}
                  disabled={salvando}
                >
                  Cancelar
                </button>
              </div>
            ) : confirmarDuplicar === "data" ? (
              <div className="confirma">
                <span>Duplicar estes pedidos para</span>
                <input
                  type="date"
                  aria-label="Data de destino da duplicação"
                  value={dataDuplicar}
                  onChange={(event) => setDataDuplicar(event.target.value)}
                  disabled={salvando}
                />
                <button
                  className="primary"
                  type="button"
                  disabled={salvando || !dataDuplicar}
                  onClick={() => void duplicarDia(dataDuplicar)}
                >
                  {salvando ? "Conferindo…" : "Confirmar"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setConfirmarDuplicar(null);
                    setAvisoDuplicata("");
                    setPedidoIgualDuplicar(null);
                    setVerPedidoIgual(false);
                  }}
                  disabled={salvando}
                >
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                className="acao"
                type="button"
                title="Duplicar os pedidos da tela para outro dia"
                disabled={!notasNaTela || orders.every((order) => order.tipo === "compra")}
                onClick={() => {
                  setConfirmarSalvar(false);
                  setConfirmarLimpar(false);
                  setAvisoDuplicata("");
                  setPedidoIgualDuplicar(null);
                  setVerPedidoIgual(false);
                  setDataDuplicar(amanhaIso());
                  setConfirmarDuplicar("data");
                }}
              >
                <IconeAcao nome="duplicar" />
                Duplicar
              </button>
            )}
            {confirmarLimpar ? (
              <div className="confirma">
                <span>
                  {orders.some(pedidoPendenteNaTela)
                    ? "Limpar a tela? Alterações e boletas ainda não salvas saem daqui."
                    : "Limpar a tela? Os pedidos gravados continuam na busca."}
                </span>
                <button type="button" onClick={limparTela}>
                  Limpar
                </button>
                <button type="button" onClick={() => setConfirmarLimpar(false)}>
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                className="acao"
                type="button"
                title="Limpar tela"
                disabled={orders.length === 0}
                onClick={() => {
                  setConfirmarSalvar(false);
                  setConfirmarDuplicar(null);
                  setAvisoDuplicata("");
                  setPedidoIgualDuplicar(null);
                  setVerPedidoIgual(false);
                  setConfirmarLimpar(true);
                }}
              >
                <IconeAcao nome="limpar" />
                Limpar
              </button>
            )}
          </>
        ) : (
          <p className="vazio">Nesta tela não há ferramentas.</p>
        )}
      </AreaTrabalho>
      <div className="area-miolo">
      <div hidden={tela === "pedidos" || tela === "contas" || tela === "funil" || tela === "colaboradores" || tela === "contexto"}>
        <Cadastro aba={tela === "tabelas" ? "tabelas" : "clientes"} incluir={incluir} />
      </div>
      <div hidden={tela !== "colaboradores"}>
        <Colaboradores />
      </div>
      <div hidden={tela !== "contexto"}>
        <ContextoIa ativo={tela === "contexto"} />
      </div>
      <div hidden={tela !== "contas"}>
        <Contas />
      </div>
      <div hidden={tela !== "funil"}>
        <FunilVendas
          ativo={tela === "funil"}
          versao={funilVersao}
          onPedirCliente={(cliente, dataIso) => void pedirDoFunil(cliente, dataIso)}
          onDuplicarPedido={(cliente, deIso, paraIso) => duplicarDoFunil(cliente, deIso, paraIso)}
          onAlternarEntregue={(cliente, dataIso) => alternarEntregueFunil(cliente, dataIso)}
          onAlternarPago={(cliente, dataIso) => alternarPagoFunil(cliente, dataIso)}
        />
      </div>
      {funilPedido ? (
        <div
          className={
            funilJanela === "min"
              ? "funil-pedido-janela minimizada no-print"
              : funilJanela === "max"
                ? "funil-pedido-janela maximizada no-print"
                : "funil-pedido-janela no-print"
          }
          style={
            funilJanela !== "max" && funilPos
              ? { left: funilPos.left, top: funilPos.top, right: "auto", bottom: "auto" }
              : undefined
          }
          role="dialog"
          aria-label={`Pedido ${funilPedido.cliente}`}
        >
          <header
            className={funilJanela === "max" ? "funil-pedido-cabeca" : "funil-pedido-cabeca arrastavel"}
            onMouseDown={arrastarJanelaFunil}
          >
            <strong>
              Pedido
              <span className="funil-pedido-meta">
                {funilPedido.cliente} · {dataParaNota(funilPedido.dataIso)}
              </span>
            </strong>
            <span className="funil-janela-btns">
              <button
                type="button"
                className="funil-salvar"
                title="Salvar"
                onClick={() => {
                  void (async () => {
                    for (let i = 0; i < orders.length; i++) {
                      const order = orders[i];
                      if (order.tipo === "compra" && !order.id) continue;
                      if (order.concluido) continue;
                      await salvarUma(order, i);
                    }
                    setFunilVersao((n) => n + 1);
                  })();
                }}
              >
                Salvar
              </button>
              <button
                type="button"
                title="Minimizar"
                aria-label="Minimizar"
                onClick={() => setFunilJanela((atual) => (atual === "min" ? "normal" : "min"))}
              >
                ─
              </button>
              <button
                type="button"
                title={funilJanela === "max" ? "Restaurar" : "Maximizar"}
                aria-label={funilJanela === "max" ? "Restaurar" : "Maximizar"}
                onClick={() => {
                  setFunilJanela((atual) => (atual === "max" ? "normal" : "max"));
                  if (funilJanela !== "max") setFunilPos(null);
                }}
              >
                {funilJanela === "max" ? "❐" : "□"}
              </button>
              <button
                type="button"
                className="fechar"
                title="Fechar"
                aria-label="Fechar"
                onClick={() => fecharPedidoFunil(true)}
              >
                ✕
              </button>
            </span>
          </header>
          {funilJanela === "min" ? null : (
            <div className="funil-pedido-corpo">
              <div className="funil-pedido-boleta">
                {orders.filter((order) => order.tipo !== "compra" || Boolean(order.id)).length === 0 ? (
                  <p className="empty">A nota aparece aqui quando você colar a conversa.</p>
                ) : (
                  orders.map((order, index) =>
                    order.tipo === "compra" && !order.id ? null : (
                      <OrderSheet
                        key={order.id || `funil-nota-${index}`}
                        order={order}
                        catalog={catalog}
                        clientes={clientes}
                        listas={listas}
                        onlyWithQty={onlyWithQty}
                        ordemImpressao={index}
                        onCliente={(nome, commit) => aoDigitarCliente(index, nome, commit)}
                        onChange={(next) => {
                          if (order.concluido) return;
                          const catalogo = { clientes, listas, produtos };
                          const trocouTabela = (order.tabela || "") !== (next.tabela || "");
                          const nota = trocouTabela
                            ? precosForcadosNaNota(next, catalogo)
                            : precosNaTroca(order, next, catalogo);
                          setOrders((current) =>
                            sincronizarCompra(current.map((item, i) => (i === index ? nota : item))),
                          );
                        }}
                        onFechar={() => fecharPedidoFunil(true)}
                        onExcluir={() => void excluirUma(order, index)}
                        onSalvar={async () => {
                          await salvarUma(order, index);
                          setFunilVersao((n) => n + 1);
                        }}
                        onConcluir={async () => {
                          await salvarUma(order, index, true);
                          setFunilVersao((n) => n + 1);
                        }}
                        onDesconcluir={() => void desconcluirUma(order, index)}
                        onPago={() => void marcarPagoUma(order, index)}
                        onPrecos={() => void aoAtualizarPrecosNota(index)}
                        onCopiar={(dataIso, forcar) => copiarUma(order, dataIso, forcar)}
                        onAviso={publicar}
                        onCadastrar={(item) => abrirCadastroProduto(item, order.tabela || "")}
                        onCadastrarCliente={
                          order.tipo !== "compra" && order.cliente.trim() && !order.clienteId
                            ? () =>
                                pedirInclusao({
                                  nome: order.cliente.trim(),
                                  tabela: order.tabela,
                                  endereco: order.endereco.trim() || undefined,
                                })
                            : undefined
                        }
                      />
                    ),
                  )
                )}
              </div>
              <div className="funil-pedido-chat">
                <PedidoChat
                  aberto
                  embutido
                  soVenda
                  aviso={aviso}
                  novos={clientesNovos(orders, clientes)}
                  opcoes={opcoesDeCliente(orders, clientes)}
                  revisao={revisao ? revisaoDe(revisao.fila, revisao.indice) : null}
                  onDecidir={decidirListagem}
                  sugestaoAlface={sugestaoAlface}
                  onDecidirAlface={decidirAlface}
                  interpretadorFora={interpretadorFora}
                  onAvisarAdministrador={(avisar) => {
                    void decidirAvisoAdministrador(avisar).then(publicar);
                  }}
                  onEscolher={escolherCliente}
                  onIncluir={pedirInclusao}
                  onToggle={() => setFunilJanela("min")}
                  onSend={onEnviar}
                  modo="venda"
                  onModo={setModoNota}
                  compra={null}
                  fornecedores={clientes}
                  onFornecedor={() => undefined}
                  onCompra={() => undefined}
                  onFalar={falarCompra}
                  onSalvar={salvarCompra}
                  onSalvarVenda={() => {
                    void (async () => {
                      for (let i = 0; i < orders.length; i++) {
                        const order = orders[i];
                        if (order.tipo === "compra" && !order.id) continue;
                        if (order.concluido) continue;
                        await salvarUma(order, i);
                      }
                      setFunilVersao((n) => n + 1);
                    })();
                  }}
                />
              </div>
            </div>
          )}
        </div>
      ) : null}
      <div hidden={tela !== "pedidos"}>
    <div className={chatAberto ? "app com-popup" : "app"}>
      <section className="notes">
        <div className="toolbar">
          <form
            className="linha toolbar-busca no-print"
            onSubmit={(event) => {
              event.preventDefault();
              void abrirPedidos();
            }}
          >
            <BuscaCliente
              nome={filtroClienteNome}
              onChange={(id, nome) => {
                setFiltroCliente(id);
                setFiltroClienteNome(nome);
              }}
            />
            <div className="busca-dia">
              <input
                type="date"
                aria-label="Dia"
                title="Busca deste dia. Se o segundo campo estiver vazio, fica só este dia."
                value={filtroDe}
                onChange={(event) => setFiltroDe(event.target.value)}
              />
              <button
                type="submit"
                className="buscar"
                title="Buscar pedidos do dia"
                aria-label="Buscar pedidos do dia"
                disabled={buscando || !filtroDe}
              >
                <svg viewBox="0 0 16 16" aria-hidden="true">
                  <circle cx="6.5" cy="6.5" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M10 10l4 4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <input
              type="date"
              aria-label="Até"
              title="Opcional. Preencha só se a busca for de mais de um dia."
              value={filtroAte}
              onChange={(event) => setFiltroAte(event.target.value)}
            />
            <button className="primary" type="submit" disabled={buscando || !filtroDe}>
              {buscando ? "Buscando…" : "Buscar"}
            </button>
          </form>
        </div>
        {mostrarColheita ? (
          <ListaColheita orders={orders.filter((order) => order.tipo !== "compra")} onFechar={() => setMostrarColheita(false)} />
        ) : null}
        {mostrarRota ? (
          <ListaRota
            orders={orders.filter((order) => order.tipo !== "compra")}
            clientes={clientes}
            onFechar={() => setMostrarRota(false)}
            onAviso={publicar}
          />
        ) : null}
        {mostrarWhatsApp ? (
          <EnviarWhatsApp
            orders={orders}
            clientes={clientes}
            onFechar={() => setMostrarWhatsApp(false)}
            onAviso={publicar}
          />
        ) : null}
        {!notasNaTela ? (
          <p className="empty">A nota convertida aparece aqui.</p>
        ) : (
          <div className="page">
            {orders.map((order, index) =>
              order.tipo === "compra" && !order.id ? null : (
              <OrderSheet
                key={order.id || `nota-${index}`}
                order={order}
                catalog={catalog}
                clientes={clientes}
                listas={listas}
                onlyWithQty={onlyWithQty}
                ordemImpressao={impressao[index]}
                onCliente={(nome, commit) => aoDigitarCliente(index, nome, commit)}
                onChange={(next) => {
                  if (order.concluido) return;
                  if (order.tipo === "compra") {
                    setOrders((current) => current.map((item, i) => (i === index ? { ...next, tipo: "compra" } : item)));
                    return;
                  }
                  const marcou = next.itens.some(
                    (item, itemIndex) => item.qtdComprada !== order.itens[itemIndex]?.qtdComprada && item.qtdComprada != null,
                  );
                  if (marcou) {
                    setModoNota("compra");
                    abrirChat(true);
                  }
                  const catalogo = { clientes, listas, produtos };
                  const trocouTabela = (order.tabela || "") !== (next.tabela || "");
                  const nota = trocouTabela
                    ? precosForcadosNaNota(next, catalogo)
                    : precosNaTroca(order, next, catalogo);
                  setOrders((current) => sincronizarCompra(current.map((item, i) => (i === index ? nota : item))));
                }}
                onFechar={() => tirarDaTela(order, index)}
                onExcluir={() => excluirUma(order, index)}
                onSalvar={() => salvarUma(order, index)}
                onConcluir={() => salvarUma(order, index, true)}
                onDesconcluir={() => desconcluirUma(order, index)}
                onPago={() => marcarPagoUma(order, index)}
                onPrecos={() => aoAtualizarPrecosNota(index)}
                onCopiar={(dataIso, forcar) => copiarUma(order, dataIso, forcar)}
                onAviso={publicar}
                onCadastrar={(item) => abrirCadastroProduto(item, order.tabela || "")}
                onCadastrarCliente={
                  order.tipo !== "compra" && order.cliente.trim() && !order.clienteId
                    ? () =>
                        pedirInclusao({
                          nome: order.cliente.trim(),
                          tabela: order.tabela,
                          endereco: order.endereco.trim() || undefined,
                        })
                    : undefined
                }
              />
              ),
            )}
            {cobranca.length > 0 ? (
              <section className="resumo-cobranca">
                <h2>Resumo de {periodoCobranca}</h2>
                {cobranca.map((bloco) => (
                  <div key={bloco.cliente}>
                    {cobranca.length > 1 ? <h3>{bloco.cliente}</h3> : null}
                    <p>Resumo</p>
                    <ul>
                      {bloco.linhas.map((linha) => (
                        <li key={linha.chave}>
                          {linha.rotulo}: {formatMoney(linha.total)}
                        </li>
                      ))}
                    </ul>
                    {cobranca.length > 1 ? <p className="resumo-parcial">TOTAL: {formatMoney(bloco.total)}</p> : null}
                  </div>
                ))}
                <p className="resumo-geral">TOTAL GERAL: {formatMoney(totalCobranca)}</p>
              </section>
            ) : null}
            {contabilidade.length > 0 ? (
              <section className="resumo-contabilidade">
                {contabilidade.map((bloco) => {
                  const precoP =
                    bloco.desconto > 0.009 ? bloco.precoPalitoComDesconto : bloco.precoPalito;
                  const precoS =
                    bloco.desconto > 0.009 ? bloco.precoSalsaComDesconto : bloco.precoSalsa;
                  return (
                  <article key={bloco.cliente} className="contabilidade-bloco">
                    <h2>CONTABILIDADE — {bloco.cliente.toLocaleUpperCase("pt-BR")}</h2>
                    {periodoCobranca ? <p className="contabilidade-periodo">Período {periodoCobranca}</p> : null}
                    <p className="contabilidade-precos">
                      {bloco.precoPalito > 0 ? (
                        <span>
                          Valor por palito: {formatMoney(bloco.precoPalito)}
                          {bloco.desconto > 0.009
                            ? ` → com desconto ${formatMoney(bloco.precoPalitoComDesconto)}`
                            : ""}
                        </span>
                      ) : null}
                      {bloco.temSalsa && bloco.precoSalsa > 0 ? (
                        <span>
                          Salsa: {formatMoney(bloco.precoSalsa)}
                          {bloco.desconto > 0.009
                            ? ` → com desconto ${formatMoney(bloco.precoSalsaComDesconto)}`
                            : ""}
                        </span>
                      ) : null}
                    </p>
                    <table className="contabilidade-tabela">
                      <thead>
                        <tr>
                          <th>Data</th>
                          <th>Dia da semana</th>
                          <th>Período</th>
                          <th>Recebeu</th>
                          <th className="num">Palitos</th>
                          {bloco.temSalsa ? <th className="num">Salsas</th> : null}
                          <th className="num">Valor</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bloco.linhas.map((linha) => (
                          <tr key={linha.chave}>
                            {linha.mostrarData ? (
                              <td rowSpan={linha.rowspan}>{linha.dataCurta}</td>
                            ) : null}
                            {linha.mostrarData ? (
                              <td rowSpan={linha.rowspan}>{linha.dia}</td>
                            ) : null}
                            <td>{linha.periodo}</td>
                            <td>{linha.recebeu}</td>
                            <td className="num">{qtdContabilidade(linha.palitos)}</td>
                            {bloco.temSalsa ? <td className="num">{qtdContabilidade(linha.salsas)}</td> : null}
                            <td className="num">{formatMoney(linha.valor)}</td>
                          </tr>
                        ))}
                        <tr className="contabilidade-total">
                          <td colSpan={4}>Total</td>
                          <td className="num">{qtdContabilidade(bloco.totalPalitos)}</td>
                          {bloco.temSalsa ? <td className="num">{qtdContabilidade(bloco.totalSalsas)}</td> : null}
                          <td className="num">{formatMoney(bloco.total)}</td>
                        </tr>
                      </tbody>
                    </table>
                    <ul className="contabilidade-conta">
                      {bloco.precoPalito > 0 && bloco.totalPalitos > 0 ? (
                        <li>
                          {qtdContabilidade(bloco.totalPalitos)} palitos × {formatMoney(precoP)} ={" "}
                          {formatMoney(bloco.totalPalitos * precoP)}
                        </li>
                      ) : null}
                      {bloco.temSalsa && bloco.precoSalsa > 0 && bloco.totalSalsas > 0 ? (
                        <li>
                          {qtdContabilidade(bloco.totalSalsas)} salsas × {formatMoney(precoS)} ={" "}
                          {formatMoney(bloco.totalSalsas * precoS)}
                        </li>
                      ) : null}
                      {bloco.temSalsa && bloco.totalSalsas > 0 ? (
                        <li className="resumo-geral">Total {formatMoney(bloco.total)}</li>
                      ) : null}
                    </ul>
                  </article>
                  );
                })}
                {contabilidade.length > 1 ? (
                  <p className="resumo-geral">TOTAL GERAL: {formatMoney(totalCobranca)}</p>
                ) : null}
              </section>
            ) : null}
          </div>
        )}
      </section>
      <PedidoChat
        aberto={chatAberto}
        aviso={aviso}
        novos={clientesNovos(orders, clientes)}
        opcoes={opcoesDeCliente(orders, clientes)}
        revisao={revisao ? revisaoDe(revisao.fila, revisao.indice) : null}
        onDecidir={decidirListagem}
        sugestaoAlface={sugestaoAlface}
        onDecidirAlface={decidirAlface}
        interpretadorFora={interpretadorFora}
        onAvisarAdministrador={(avisar) => {
          void decidirAvisoAdministrador(avisar).then(publicar);
        }}
        onEscolher={escolherCliente}
        onIncluir={pedirInclusao}
        onToggle={() => abrirChat((atual) => !atual)}
        onSend={onEnviar}
        modo={modoNota}
        onModo={setModoNota}
        compra={compraAberta}
        fornecedores={clientes}
        onFornecedor={(nome, commit) => {
          const catalogo = { clientes, listas, produtos };
          setOrders((current) => {
            const lista = garantirCompra(current);
            const index = rascunhoDeCompra(lista);
            const nota = nomeNaBoleta(lista[index], nome, catalogo, commit);
            return lista.map((item, i) => (i === index ? { ...nota, tipo: "compra" as const, id: undefined } : item));
          });
        }}
        onCompra={(next) =>
          setOrders((current) => {
            const index = rascunhoDeCompra(current);
            const nota = { ...next, tipo: "compra" as const, id: undefined };
            if (index < 0) return [...current, nota];
            return current.map((item, i) => (i === index ? nota : item));
          })
        }
        onFalar={falarCompra}
        onSalvar={salvarCompra}
      />
      {verPedidoIgual && pedidoIgualDuplicar ? (
        <PedidoIgualPopup pedido={pedidoIgualDuplicar} onFechar={() => setVerPedidoIgual(false)} />
      ) : null}
      {pendenciaNaoSalvos ? (
        <div
          className={`aviso-nao-salvos no-print${avisoNaoSalvosSolto ? " aviso-nao-salvos-solto" : ""}`}
          role="alertdialog"
          aria-labelledby="aviso-nao-salvos-titulo"
          style={
            avisoNaoSalvosPos
              ? { left: avisoNaoSalvosPos.x, top: avisoNaoSalvosPos.y, transform: "none" }
              : undefined
          }
          onMouseDown={() => setAvisoNaoSalvosSolto(true)}
        >
          <div
            className="aviso-nao-salvos-cabeca"
            title="Arraste para o lado"
            onMouseDown={iniciarArrastoAviso}
          >
            <strong id="aviso-nao-salvos-titulo">Pedidos não salvos</strong>
            <button
              type="button"
              className="aviso-nao-salvos-fechar"
              title="Fechar"
              aria-label="Fechar aviso"
              onClick={fecharAvisoNaoSalvos}
            >
              ✕
            </button>
          </div>
          <p>
            {pendenciaNaoSalvos === "abrir-pedidos"
              ? "Você está saindo da listagem e há boletas novas ou alteradas ainda não gravadas:"
              : "Você está saindo e há boletas novas ou alteradas ainda não gravadas:"}
          </p>
          <ul>
            {boletasNaoSalvas().map(({ order, index }) => {
              const nome = order.cliente.trim() || "Sem nome";
              return (
                <li key={`${nome}-${index}`}>
                  <span className="aviso-nao-salvos-nome">{nome}</span>
                  <span className="aviso-nao-salvos-icones">
                    <button
                      type="button"
                      className="aviso-nao-salvos-icone"
                      title={`Salvar ${nome}`}
                      aria-label={`Salvar ${nome}`}
                      disabled={salvando}
                      onClick={() => void salvarUmaNaoSalva(order, index)}
                    >
                      <IconeAcao nome="salvar" />
                    </button>
                    <button
                      type="button"
                      className="aviso-nao-salvos-icone aviso-nao-salvos-icone-excluir"
                      title={`Descartar ${nome}`}
                      aria-label={`Descartar ${nome}`}
                      disabled={salvando}
                      onClick={() => descartarUmaNaoSalva(order, index)}
                    >
                      <IconeAcao nome="limpar" />
                    </button>
                  </span>
                </li>
              );
            })}
          </ul>
          <div className="aviso-nao-salvos-acoes">
            <button
              className="primary"
              type="button"
              disabled={salvando}
              onClick={() => void resolverNaoSalvos("salvar")}
            >
              {salvando ? "Salvando…" : "Salvar"}
            </button>
            <button type="button" disabled={salvando} onClick={() => void resolverNaoSalvos("descartar")}>
              Descartar pedidos
            </button>
          </div>
        </div>
      ) : null}
    </div>
      </div>
      {produtoNovo ? (
        <ProdutoPopup
          abertura={produtoNovo}
          listas={listas}
          produtos={produtos}
          onFechar={() => setProdutoNovo(null)}
          onSalvar={salvarProdutoDoPedido}
        />
      ) : null}
      </div>
    </div>
  );
}
