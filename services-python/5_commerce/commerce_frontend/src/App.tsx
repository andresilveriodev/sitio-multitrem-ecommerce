import { useEffect, useRef, useState } from "react";
import { Cadastro } from "./Cadastro";
import { Contas } from "./Contas";
import { convertConversation } from "./api";
import { consultarBoletas, loadClientes, loadTabelas, salvarBoletas, type Cliente, type Extrato, type Lista, type Produto } from "./cadastroApi";
import { ordemDeImpressao } from "./orderMath";
import { OrderSheet } from "./OrderSheet";
import { PedidoChat } from "./PedidoChat";
import { aplicarFormatoDaConversa, aplicarResposta, atualizarListagem, clientesNovos, comPrecos, listarClientes, nomeNaBoleta, opcoesDeCliente, perguntaDaListagem, respostaDoPedido, rotulosDoCatalogo, temNomeNovo, type ClienteParaIncluir } from "./pedidoConversa";
import type { Order } from "./types";

type Tela = "pedidos" | "clientes" | "tabelas" | "contas";

function iso(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function semanaAtual(hoje = new Date()): { de: string; ate: string } {
  const dia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const segunda = (dia.getDay() + 6) % 7;
  const inicio = new Date(dia);
  inicio.setDate(dia.getDate() - segunda);
  const fim = new Date(inicio);
  fim.setDate(inicio.getDate() + 6);
  return { de: iso(inicio), ate: iso(fim) };
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
      itens: pedido.itens.map((item) => ({
        produto: item.produto,
        qtd: item.qtd,
        qtdEntregue: item.qtd_entregue,
        valor: item.valor,
        desconto: item.desconto ? item.desconto : undefined,
        descontoPercentual: item.desconto_percentual ? item.desconto_percentual : undefined,
        conhecido: true,
        preco_tabela: false,
      })),
    })),
  );
}

function faltaParaSalvar(orders: Order[]): string {
  const faltas: string[] = [];
  orders.forEach((order, index) => {
    const quem = order.cliente.trim() || `A nota ${index + 1}`;
    if (!order.clienteId) faltas.push(`${quem} ainda não está ligado a um cliente do cadastro.`);
    if (!order.data.trim()) faltas.push(`${quem} está sem data de entrega.`);
    const itens = order.itens.filter((item) => item.qtd > 0 && item.produto.trim());
    if (!itens.length) faltas.push(`${quem} não tem item com quantidade.`);
    itens.forEach((item) => {
      if (!(item.valor > 0)) faltas.push(`${quem}: falta o preço de ${item.produto}.`);
    });
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
  const [tela, setTela] = useState<Tela>("pedidos");
  const [orders, setOrders] = useState<Order[]>([]);
  const [catalog, setCatalog] = useState<string[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [listas, setListas] = useState<Lista[]>([]);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [onlyWithQty, setOnlyWithQty] = useState(true);
  const [chatAberto, setChatAberto] = useState(true);
  const [atualizando, setAtualizando] = useState(false);
  const [aviso, setAviso] = useState<Aviso | null>(null);
  const [incluir, setIncluir] = useState<(ClienteParaIncluir & { seq: number }) | null>(null);
  const [pendente, setPendente] = useState<Order[] | null>(null);
  const [confirmarSalvar, setConfirmarSalvar] = useState(false);
  const [confirmarLimpar, setConfirmarLimpar] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const periodo = semanaAtual();
  const [filtroCliente, setFiltroCliente] = useState("");
  const [filtroDe, setFiltroDe] = useState(periodo.de);
  const [filtroAte, setFiltroAte] = useState(periodo.ate);
  const [buscando, setBuscando] = useState(false);
  const ordersRef = useRef(orders);
  ordersRef.current = orders;
  const avisoId = useRef(0);

  function publicar(texto: string) {
    if (!texto) return;
    avisoId.current += 1;
    setAviso({ id: avisoId.current, texto });
  }

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

  async function salvarDia() {
    const atuais = ordersRef.current;
    const falta = faltaParaSalvar(atuais);
    if (falta) {
      setConfirmarSalvar(false);
      publicar(falta);
      return;
    }
    setSalvando(true);
    try {
      const resposta = await salvarBoletas(
        atuais.map((order) => ({
          cliente_id: order.clienteId,
          data: order.data,
          endereco: order.endereco,
          desconto: order.desconto,
          id: order.id,
          tabela: order.tabela || "",
          itens: order.itens
            .filter((item) => item.qtd > 0 && item.produto.trim())
            .map((item) => ({
              produto: item.produto,
              qtd: item.qtd,
              qtd_entregue: item.qtdEntregue ?? item.qtd,
              valor: item.valor,
              desconto: item.desconto || 0,
              desconto_percentual: item.descontoPercentual || 0,
            })),
        })),
      );
      const atualizando = atuais.every((order) => order.id);
      setPendente(null);
      setConfirmarSalvar(false);
      if (atualizando) {
        setOrders(atuais.map((order, index) => ({ ...order, id: resposta.ids[index] || order.id })));
        publicar(
          `Atualizei ${resposta.salvos} ${resposta.salvos === 1 ? "pedido" : "pedidos"}. A conta usa o que foi entregue.`,
        );
      } else {
        setOrders([]);
        publicar(`Salvei ${resposta.salvos} ${resposta.salvos === 1 ? "pedido" : "pedidos"} e limpei a tela.`);
      }
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui salvar os pedidos.");
    } finally {
      setSalvando(false);
    }
  }

  function limparTela() {
    setOrders([]);
    setPendente(null);
    setConfirmarLimpar(false);
    setConfirmarSalvar(false);
    publicar("Limpei a tela. Os pedidos já gravados continuam na busca.");
  }

  async function abrirPedidos() {
    if (ordersRef.current.some((order) => !order.id)) {
      publicar("Tem pedido novo na tela. Salve o dia antes de abrir os pedidos gravados.");
      return;
    }
    setBuscando(true);
    try {
      const extrato = await consultarBoletas(filtroDe, filtroAte, filtroCliente ? Number(filtroCliente) : undefined);
      const notas = notasDoExtrato(extrato);
      setOrders(notas);
      setPendente(null);
      publicar(
        notas.length
          ? `Abri ${notas.length} ${notas.length === 1 ? "pedido" : "pedidos"}.`
          : "Nenhum pedido nesse período.",
      );
    } catch (err) {
      publicar(err instanceof Error ? err.message : "Não consegui abrir os pedidos.");
    } finally {
      setBuscando(false);
    }
  }

  function pedirInclusao(cliente: ClienteParaIncluir) {
    setIncluir({ ...cliente, seq: Date.now() });
    setTela("clientes");
  }

  async function onEnviar(frase: string): Promise<string> {
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
      setPendente(null);
      const proximos = comPrecos(ajuste, catalogo);
      setOrders(proximos);
      return respostaDoPedido(proximos, pessoas);
    }
    try {
      const result = await convertConversation(frase);
      const novos = comPrecos(aplicarFormatoDaConversa(result.orders, frase, itens), catalogo);
      setCatalog(rotulosDoCatalogo(itens, result.catalog));
      if (!atuais.length) {
        setPendente(null);
        setOrders(novos);
        return respostaDoPedido(novos, pessoas);
      }
      if (temNomeNovo(atuais, novos)) {
        setPendente(null);
        setOrders([...atuais, ...novos]);
        const quem = atuais.map((item) => item.cliente.trim()).filter(Boolean).join(", ");
        const segue = quem ? ` O pedido de ${quem} continua na tela.` : " O pedido que já estava na tela continua.";
        return `${respostaDoPedido(novos, pessoas)}${segue}`;
      }
      setPendente(novos);
      return perguntaDaListagem(atuais);
    } catch {
      if (atuais.length) return respostaDoPedido(atuais, pessoas);
      return "Não vi os itens. Cole a conversa do WhatsApp.";
    }
  }

  function decidirListagem(modo: "atualizar" | "inserir") {
    const novos = pendente;
    if (!novos) return;
    const atuais = ordersRef.current;
    const catalogo = { clientes, listas, produtos };
    const montados = modo === "inserir" ? [...atuais, ...novos] : atualizarListagem(atuais, novos);
    const proximos = comPrecos(montados, catalogo);
    setOrders(proximos);
    setPendente(null);
    const foco = modo === "inserir" ? proximos.slice(atuais.length) : proximos.filter((_, index) => montados[index] !== atuais[index]);
    const resumo = respostaDoPedido(foco.length ? foco : proximos, clientes);
    publicar(modo === "inserir" ? `Incluí outro pedido. ${resumo}` : `Atualizei a listagem. ${resumo}`);
  }

  const impressao = ordemDeImpressao(orders, onlyWithQty);

  return (
    <div>
      <nav className="menu no-print">
        <button type="button" className={tela === "pedidos" ? "primary" : undefined} onClick={() => setTela("pedidos")}>
          Pedidos
        </button>
        <button type="button" className={tela === "clientes" ? "primary" : undefined} onClick={() => setTela("clientes")}>
          Clientes
        </button>
        <button type="button" className={tela === "tabelas" ? "primary" : undefined} onClick={() => setTela("tabelas")}>
          Preços
        </button>
        <button type="button" className={tela === "contas" ? "primary" : undefined} onClick={() => setTela("contas")}>
          Contas
        </button>
      </nav>
      <div hidden={tela === "pedidos" || tela === "contas"}>
        <Cadastro aba={tela === "tabelas" ? "tabelas" : "clientes"} incluir={incluir} />
      </div>
      <div hidden={tela !== "contas"}>
        <Contas />
      </div>
      <div hidden={tela !== "pedidos"}>
    <div className={chatAberto ? "app com-popup" : "app"}>
      <section className="notes">
        <div className="toolbar">
          <label>
            <input
              type="checkbox"
              checked={onlyWithQty}
              onChange={(event) => setOnlyWithQty(event.target.checked)}
            />{" "}
            Mostrar somente produtos com quantidade
          </label>
          <span className="toolbar-acoes">
            <button type="button" disabled={atualizando} onClick={() => void aoAtualizar()}>
              {atualizando ? "Atualizando…" : "Atualizar"}
            </button>
            <button type="button" onClick={() => window.print()} disabled={orders.length === 0}>
              Imprimir
            </button>
            {confirmarSalvar ? (
              <>
                <span>
                  {orders.every((order) => order.id)
                    ? "Gravar as alterações destes pedidos?"
                    : "Salvar estes pedidos e limpar a tela?"}
                </span>
                <button className="primary" type="button" disabled={salvando} onClick={() => void salvarDia()}>
                  {salvando ? "Salvando…" : "Confirmar"}
                </button>
                <button type="button" onClick={() => setConfirmarSalvar(false)} disabled={salvando}>
                  Cancelar
                </button>
              </>
            ) : (
              <button className="primary" type="button" disabled={orders.length === 0} onClick={() => { setConfirmarLimpar(false); setConfirmarSalvar(true); }}>
                {orders.length > 0 && orders.every((order) => order.id) ? "Atualizar pedidos" : "Salvar o dia"}
              </button>
            )}
            {confirmarLimpar ? (
              <>
                <span>
                  {orders.some((order) => !order.id)
                    ? "Limpar a tela? O que ainda não foi salvo sai daqui."
                    : "Limpar a tela? Os pedidos gravados continuam na busca."}
                </span>
                <button type="button" onClick={limparTela}>
                  Limpar
                </button>
                <button type="button" onClick={() => setConfirmarLimpar(false)}>
                  Cancelar
                </button>
              </>
            ) : (
              <button type="button" disabled={orders.length === 0} onClick={() => { setConfirmarSalvar(false); setConfirmarLimpar(true); }}>
                Limpar tela
              </button>
            )}
          </span>
          <form
            className="linha toolbar-busca no-print"
            onSubmit={(event) => {
              event.preventDefault();
              void abrirPedidos();
            }}
          >
            <select
              aria-label="Cliente"
              value={filtroCliente}
              onChange={(event) => setFiltroCliente(event.target.value)}
            >
              <option value="">Todos os clientes</option>
              {clientes.map((cliente) => (
                <option key={cliente.id} value={cliente.id}>
                  {cliente.name}
                </option>
              ))}
            </select>
            <input type="date" aria-label="De" value={filtroDe} onChange={(event) => setFiltroDe(event.target.value)} />
            <input type="date" aria-label="Até" value={filtroAte} onChange={(event) => setFiltroAte(event.target.value)} />
            <button className="primary" type="submit" disabled={buscando || !filtroDe || !filtroAte}>
              {buscando ? "Buscando…" : "Buscar"}
            </button>
          </form>
        </div>
        {orders.length === 0 ? (
          <p className="empty">A nota convertida aparece aqui.</p>
        ) : (
          <div className="page">
            {orders.map((order, index) => (
              <OrderSheet
                key={index}
                order={order}
                catalog={catalog}
                clientes={clientes}
                onlyWithQty={onlyWithQty}
                ordemImpressao={impressao[index]}
                onCliente={(nome, commit) => aoDigitarCliente(index, nome, commit)}
                onChange={(next) =>
                  setOrders((current) => current.map((item, i) => (i === index ? next : item)))
                }
                onDelete={() => setOrders((current) => current.filter((_, i) => i !== index))}
              />
            ))}
          </div>
        )}
      </section>
      <PedidoChat
        aberto={chatAberto}
        aviso={aviso}
        novos={clientesNovos(orders, clientes)}
        opcoes={opcoesDeCliente(orders, clientes)}
        decidir={pendente !== null}
        onDecidir={decidirListagem}
        onEscolher={escolherCliente}
        onIncluir={pedirInclusao}
        onToggle={() => setChatAberto((atual) => !atual)}
        onSend={onEnviar}
      />
    </div>
      </div>
    </div>
  );
}
