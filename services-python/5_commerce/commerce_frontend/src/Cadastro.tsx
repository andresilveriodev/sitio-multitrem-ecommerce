import { useEffect, useMemo, useRef, useState } from "react";
import { CadastroChat } from "./CadastroChat";
import {
  createProduto,
  deleteCliente,
  deleteProduto,
  interpretCadastro,
  loadClientes,
  loadTabelas,
  removeDesconto,
  saveCliente,
  saveDesconto,
  saveFormato,
  saveTablePrice,
  type Acao,
  type Cliente,
  type Lista,
  type Produto,
} from "./cadastroApi";
import {
  acaoDaFrase,
  descreverPrecos,
  formatarReais,
  formularioVazio,
  gravarRascunho,
  lerReais,
  lerRascunho,
  limparRascunho,
  mesclarCliente,
  mesmoNome,
  normalizarFormato,
  precosDaFrase,
  rotuloProduto,
  separarFormato,
  type Formulario,
} from "./rascunho";

type Aba = "clientes" | "tabelas";

export type InclusaoCliente = {
  seq: number;
  nome: string;
  tabela?: string;
  endereco?: string;
};

const vazio = formularioVazio;
const FORMATOS = ["unidade", "maço", "kg", "peso fixo"];
const rascunhoInicial = lerRascunho();

function money(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function showPhone(value: string | null | undefined): string {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  const local = digits.startsWith("55") && digits.length > 11 ? digits.slice(2) : digits;
  if (local.length === 11) return `${local.slice(0, 2)} ${local.slice(2, 7)}-${local.slice(7)}`;
  if (local.length === 10) return `${local.slice(0, 2)} ${local.slice(2, 6)}-${local.slice(6)}`;
  return value;
}

function formFrom(item: Cliente | null, listaPadrao: number | null): Formulario {
  if (!item) return { ...vazio, lista: listaPadrao };
  return {
    nome: item.name,
    celular1: showPhone(item.phone_e164),
    celular2: showPhone(item.phone2_e164),
    endereco: item.endereco ?? "",
    localizacao: item.localizacao ?? "",
    observacao: item.observacao ?? "",
    lista: item.price_list_id ?? listaPadrao,
    tipo: item.kind === "comercio" ? "comercio" : "pessoa",
    pessoas: (item.pessoas ?? []).map((pessoa) => ({
      nome: pessoa.nome,
      celular: showPhone(pessoa.celular),
      papeis: pessoa.papeis ?? [],
    })),
    descontoPedido: item.desconto_pedido ? String(item.desconto_pedido).replace(".", ",") : "",
  };
}

const PAPEIS = [
  ["proprietario", "Proprietário"],
  ["pedidos", "Faz o pedido e recebe"],
  ["financeiro", "Financeiro"],
] as const;

function descontoGeral(valor: string): number | null | undefined {
  const texto = valor.trim();
  if (!texto) return null;
  const numero = Number(texto.replace(",", "."));
  if (Number.isNaN(numero) || numero < 0 || numero > 100) return undefined;
  return Math.round(numero * 100) / 100;
}

function faltando(form: Formulario): string[] {
  const itens: string[] = [];
  if (!form.nome.trim()) itens.push("nome completo");
  if (!form.celular1.trim()) itens.push("celular 1");
  if (!form.endereco.trim()) itens.push("endereço");
  if (!form.localizacao.trim()) itens.push("localização");
  return itens;
}

export function Cadastro({ aba, incluir }: { aba: Aba; incluir?: InclusaoCliente | null }) {
  const [listas, setListas] = useState<Lista[]>([]);
  const [produtos, setProdutos] = useState<Produto[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clienteId, setClienteId] = useState<number | null>(rascunhoInicial?.clienteId ?? null);
  const [form, setForm] = useState<Formulario>(rascunhoInicial?.form ?? vazio);
  const [marcados, setMarcados] = useState(rascunhoInicial?.marcados ?? {});
  const [clientePendente, setClientePendente] = useState(rascunhoInicial?.clientePendente ?? false);
  const [original, setOriginal] = useState<Formulario | null>(rascunhoInicial?.original ?? null);
  const [produtoId, setProdutoId] = useState<number | null>(rascunhoInicial?.produtoId ?? null);
  const [desconto, setDesconto] = useState(rascunhoInicial?.desconto ?? "");
  const [descontoPendente, setDescontoPendente] = useState(rascunhoInicial?.descontoPendente ?? false);
  const [precosPendentes, setPrecosPendentes] = useState<Record<string, string>>(rascunhoInicial?.precosPendentes ?? {});
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [novoNome, setNovoNome] = useState("");
  const [novoFormato, setNovoFormato] = useState("unidade");
  const [novoOutro, setNovoOutro] = useState("");
  const [excluirId, setExcluirId] = useState<number | null>(null);
  const [excluirCliente, setExcluirCliente] = useState(false);
  const cadastroRef = useRef({ clientePendente, form, listas });
  cadastroRef.current = { clientePendente, form, listas };

  async function refresh() {
    const [tabelas, lista] = await Promise.all([loadTabelas(), loadClientes()]);
    setListas(tabelas.listas);
    setProdutos(tabelas.produtos);
    setClientes(lista);
    setError("");
    setForm((atual) => (atual.lista ? atual : { ...atual, lista: tabelas.listas[0]?.id ?? null }));
  }

  useEffect(() => {
    if (!incluir) return;
    const { clientePendente: pendente, form: atual, listas: folhas } = cadastroRef.current;
    if (pendente && atual.nome.trim() && !mesmoNome(atual.nome, incluir.nome)) {
      setError("Confirme ou descarte a alteração deste cliente antes de incluir outro.");
      return;
    }
    const listaPedido = folhas.find((item) => incluir.tabela && mesmoNome(item.name, incluir.tabela));
    if (pendente && mesmoNome(atual.nome, incluir.nome)) {
      if (listaPedido && atual.lista !== listaPedido.id) {
        setForm({ ...atual, lista: listaPedido.id });
        setMarcados((marcados) => ({ ...marcados, lista: true }));
      }
      return;
    }
    const base = { ...vazio, lista: folhas[0]?.id ?? null };
    setError("");
    setClienteId(null);
    setExcluirCliente(false);
    setForm({
      ...base,
      nome: incluir.nome,
      lista: listaPedido?.id ?? base.lista,
      endereco: incluir.endereco ?? "",
    });
    setMarcados({
      nome: true,
      ...(incluir.tabela ? { lista: true } : {}),
      ...(incluir.endereco ? { endereco: true } : {}),
    });
    setOriginal(base);
    setProdutoId(null);
    setDesconto("");
    setDescontoPendente(false);
    setClientePendente(true);
  }, [incluir]);

  useEffect(() => {
    refresh().catch(async (err: Error) => {
      setError(err.message);
      await new Promise((resolve) => setTimeout(resolve, 800));
      refresh().catch((again: Error) => setError(again.message));
    });
  }, []);

  useEffect(() => {
    if (!clientePendente && !descontoPendente && Object.keys(precosPendentes).length === 0) {
      limparRascunho();
      return;
    }
    gravarRascunho({
      clienteId,
      form,
      marcados,
      clientePendente,
      produtoId,
      desconto,
      descontoPendente,
      precosPendentes,
      original,
    });
  }, [clienteId, form, marcados, clientePendente, produtoId, desconto, descontoPendente, precosPendentes, original]);

  const cliente = clientes.find((item) => item.id === clienteId) ?? null;
  const baseId = form.lista;
  const produto = produtos.find((item) => item.id === produtoId) ?? null;
  const precoBase = produto && baseId ? produto.precos[String(baseId)] : undefined;
  const descontoNumero = Number(desconto.replace(",", "."));
  const precoFinal =
    precoBase !== undefined && desconto !== "" && !Number.isNaN(descontoNumero)
      ? Math.max(0, Math.round((precoBase - descontoNumero) * 100) / 100)
      : null;
  const pending = clientePendente || descontoPendente || Object.keys(precosPendentes).length > 0;

  const linhasPreco = useMemo(
    () =>
      produtos.flatMap((product) =>
        listas.map((lista, index) => ({
          product,
          lista,
          price: product.precos[String(lista.id)],
          pending: precosPendentes[`${product.id}:${lista.id}`],
          first: index === 0,
        })),
      ),
    [produtos, listas, precosPendentes],
  );

  function editar<K extends keyof Formulario>(campo: K, valor: Formulario[K]) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({ ...atual, [campo]: valor }));
    setMarcados((atual) => ({ ...atual, [campo]: true }));
    setClientePendente(true);
  }

  function escolherTipo(tipo: "pessoa" | "comercio") {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({
      ...atual,
      tipo,
      pessoas: tipo === "comercio" && atual.pessoas.length === 0 ? [{ nome: "", celular: "", papeis: [] }] : atual.pessoas,
    }));
    setMarcados((atual) => ({ ...atual, tipo: true }));
    setClientePendente(true);
  }

  function alterarPessoa(index: number, patch: Partial<Formulario["pessoas"][number]>) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({
      ...atual,
      pessoas: atual.pessoas.map((pessoa, i) => (i === index ? { ...pessoa, ...patch } : pessoa)),
    }));
    setClientePendente(true);
  }

  function alternarPapel(index: number, papel: string) {
    const pessoa = form.pessoas[index];
    if (!pessoa) return;
    const papeis = pessoa.papeis.includes(papel)
      ? pessoa.papeis.filter((item) => item !== papel)
      : [...pessoa.papeis, papel];
    alterarPessoa(index, { papeis });
  }

  function adicionarPessoa() {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({ ...atual, pessoas: [...atual.pessoas, { nome: "", celular: "", papeis: [] }] }));
    setClientePendente(true);
  }

  function removerPessoa(index: number) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({ ...atual, pessoas: atual.pessoas.filter((_, i) => i !== index) }));
    setClientePendente(true);
  }

  function openCliente(item: Cliente) {
    if (clientePendente && item.id !== clienteId) {
      setError("Confirme ou descarte a alteração deste cliente antes de abrir outro.");
      return;
    }
    if (clientePendente && item.id === clienteId) return;
    setError("");
    setClienteId(item.id);
    setForm(formFrom(item, listas[0]?.id ?? null));
    setOriginal(null);
    setMarcados({});
    setProdutoId(null);
    setDesconto("");
    setDescontoPendente(false);
    setExcluirCliente(false);
  }

  function novoCliente() {
    if (clientePendente) {
      setError("Confirme ou descarte a alteração deste cliente antes de abrir outro.");
      return;
    }
    setClienteId(null);
    setExcluirCliente(false);
    setForm({ ...vazio, lista: listas[0]?.id ?? null });
    setMarcados({});
    setOriginal(null);
    setProdutoId(null);
    setDesconto("");
    setDescontoPendente(false);
    setClientePendente(false);
  }

  function acharCliente(nome: string): Cliente | undefined {
    return (
      clientes.find((item) => mesmoNome(item.name, nome)) ??
      clientes.find((item) => item.name.toLocaleLowerCase("pt-BR").includes(nome.trim().toLocaleLowerCase("pt-BR")))
    );
  }

  function acharProduto(nome: string): Produto | undefined {
    const peloRotulo = produtos.find((item) => mesmoNome(rotuloProduto(item.name, item.formato || "unidade"), nome));
    if (peloRotulo) return peloRotulo;
    const peloNome = produtos.filter((item) => mesmoNome(item.name, nome));
    if (peloNome.length === 1) return peloNome[0];
    return peloNome.find((item) => normalizarFormato(item.formato || "unidade") === "unidade");
  }

  function acharLista(nome: string): Lista | undefined {
    return listas.find((item) => mesmoNome(item.name, nome));
  }

  async function abrirFormato(rotulo: string, lista: Produto[]): Promise<{ catalogo: Produto[]; produto?: Produto }> {
    const existente = lista.find((item) => mesmoNome(rotuloProduto(item.name, item.formato || "unidade"), rotulo));
    if (existente) return { catalogo: lista, produto: existente };
    const partes = separarFormato(rotulo);
    if (!partes.nome || !partes.formato || !lista.some((item) => mesmoNome(item.name, partes.nome))) {
      return { catalogo: lista };
    }
    try {
      const criado = await createProduto(partes.nome, partes.formato);
      return { catalogo: [...lista, criado], produto: criado };
    } catch {
      const tabelas = await loadTabelas();
      const achado = tabelas.produtos.find((item) =>
        mesmoNome(rotuloProduto(item.name, item.formato || "unidade"), rotulo),
      );
      return { catalogo: tabelas.produtos, produto: achado };
    }
  }

  async function onChat(frase: string): Promise<string> {
    let reply = "";
    let recebidas: Acao[] = [];
    try {
      const result = await interpretCadastro({
        message: frase,
        tela: aba === "tabelas" ? "precos" : "clientes",
        clientes: clientes.map((item) => ({ nome: item.name })),
        produtos: produtos.map((item) => rotuloProduto(item.name, item.formato || "unidade")),
        listas: listas.map((item) => item.name),
      });
      reply = result.reply;
      recebidas = result.acoes;
    } catch (err) {
      reply = err instanceof Error ? err.message : "A IA não respondeu";
    }
    const locais = precosDaFrase(
      frase,
      produtos.map((item) => ({ nome: item.name, formato: item.formato || "unidade" })),
      listas.map((item) => item.name),
    );
    if (locais.acoes.length) {
      recebidas = [...recebidas.filter((acao) => acao.tipo !== "preco"), ...locais.acoes];
      reply = descreverPrecos(locais.acoes, locais.faltando);
    }
    const daFrase = acaoDaFrase(frase, clientes.map((item) => item.name));
    if (daFrase) {
      const indice = recebidas.findIndex((acao) => acao.tipo === "cliente" && mesmoNome(acao.nome, daFrase.nome));
      if (indice === -1) {
        recebidas = [{ tipo: "cliente", ...daFrase }, ...recebidas];
      } else {
        const atual = recebidas[indice];
        if (atual.tipo === "cliente") {
          recebidas[indice] = {
            ...atual,
            localizacao: atual.localizacao || daFrase.localizacao,
            celular1: atual.celular1 || daFrase.celular1,
          };
        }
      }
    }
    if (!recebidas.length) throw new Error(reply || "Não identifiquei o que mudar.");
    setError("");
    const ordem = { cliente: 0, desconto: 1, preco: 2 };
    const acoes = [...recebidas].sort((a, b) => ordem[a.tipo] - ordem[b.tipo]);
    let nextForm = form;
    let nextId = clienteId;
    let nextMarcados = { ...marcados };
    let nextClientePendente = clientePendente;
    let nextProduto = produtoId;
    let nextDesconto = desconto;
    let nextDescontoPendente = descontoPendente;
    const nextPrecos = { ...precosPendentes };
    const avisos: string[] = [];
    let catalogo = produtos;

    let nextOriginal = original;
    for (const acao of acoes) {
      if (acao.tipo === "cliente") {
        const found = acharCliente(acao.nome);
        const mesclado = mesclarCliente(
          { form: nextForm, id: nextId, pendente: nextClientePendente, marcados: nextMarcados, original: nextOriginal },
          acao,
          found ? { id: found.id, form: formFrom(found, listas[0]?.id ?? null) } : null,
          (nome) => acharLista(nome)?.id ?? null,
        );
        if (mesclado.bloqueado) {
          avisos.push("Confirme ou descarte o cliente atual antes de alterar outro.");
          continue;
        }
        nextForm = mesclado.form;
        nextId = mesclado.id;
        nextMarcados = mesclado.marcados;
        nextOriginal = mesclado.original;
        nextClientePendente = true;
      }
      if (acao.tipo === "preco") {
        const aberto = await abrirFormato(acao.produto, catalogo);
        catalogo = aberto.catalogo;
        const lista = acharLista(acao.lista);
        if (!aberto.produto || !lista) avisos.push(`Não achei ${acao.produto} em ${acao.lista}.`);
        else nextPrecos[`${aberto.produto.id}:${lista.id}`] = formatarReais(acao.valor);
      }
      if (acao.tipo === "desconto") {
        const person = acharCliente(acao.cliente);
        const product = acharProduto(acao.produto);
        if (!person || !product) {
          avisos.push(`Não achei o desconto de ${acao.cliente} em ${acao.produto}.`);
          continue;
        }
        if (!nextClientePendente) {
          nextId = person.id;
          nextForm = formFrom(person, listas[0]?.id ?? null);
        }
        const listId = nextForm.lista ?? person.price_list_id;
        const base = listId ? product.precos[String(listId)] : undefined;
        if (base === undefined) {
          avisos.push(`${product.name} ainda não tem preço base para calcular o desconto.`);
          continue;
        }
        nextProduto = product.id;
        nextDesconto = String(acao.desconto).replace(".", ",");
        nextDescontoPendente = true;
      }
    }

    setForm(nextForm);
    setClienteId(nextId);
    setMarcados(nextMarcados);
    setOriginal(nextOriginal);
    setClientePendente(nextClientePendente);
    setProdutoId(nextProduto);
    setDesconto(nextDesconto);
    setDescontoPendente(nextDescontoPendente);
    if (catalogo !== produtos) setProdutos(catalogo);
    setPrecosPendentes(nextPrecos);

    const falta = nextClientePendente ? faltando(nextForm) : [];
    if (falta.length) avisos.push("Para salvar ainda precisa de " + falta.join(", ") + ".");
    const resposta = [reply, ...avisos].filter(Boolean).join(" ");
    return resposta || "Não identifiquei o que mudar.";
  }

  async function confirmar() {
    setSaving(true);
    setError("");
    try {
      for (const [key, raw] of Object.entries(precosPendentes)) {
        const [productId, listId] = key.split(":").map(Number);
        const price = lerReais(raw);
        if (Number.isNaN(price) || price < 0) continue;
        await saveTablePrice(listId, productId, price);
      }
      setPrecosPendentes({});
      let id = clienteId;
      if (clientePendente) {
        const falta = faltando(form);
        if (falta.length) throw new Error("Para salvar precisa de " + falta.join(", ") + ".");
        if (descontoGeral(form.descontoPedido) === undefined) {
          throw new Error("O desconto geral do pedido fica entre 0 e 100%.");
        }
        const listaId = form.lista ?? listas[0]?.id;
        if (!listaId) throw new Error("Escolha o preço base.");
        const saved = await saveCliente({
          id: id ?? undefined,
          name: form.nome.trim(),
          price_list_id: listaId,
          phone_e164: form.celular1,
          phone2_e164: form.celular2,
          endereco: form.endereco,
          localizacao: form.localizacao,
          observacao: form.observacao,
          kind: form.tipo,
          pessoas: form.tipo === "comercio" ? form.pessoas : [],
          desconto_pedido: descontoGeral(form.descontoPedido),
        });
        id = saved.id;
        setClienteId(saved.id);
        setForm(formFrom(saved, listas[0]?.id ?? null));
        setOriginal(null);
        setClientePendente(false);
        setMarcados({});
      }
      if (descontoPendente) {
        if (!id || produtoId === null || precoFinal === null) throw new Error("Não deu para calcular o desconto.");
        await saveDesconto(id, produtoId, precoFinal);
        setDesconto("");
        setProdutoId(null);
        setDescontoPendente(false);
      }
      await refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Não salvou";
      setError(message);
      throw err instanceof Error ? err : new Error(message);
    } finally {
      setSaving(false);
    }
  }

  function descartar() {
    const item = clientes.find((atual) => atual.id === clienteId) ?? null;
    setForm(formFrom(item, listas[0]?.id ?? null));
    setOriginal(null);
    setMarcados({});
    setClientePendente(false);
    setDesconto("");
    setProdutoId(null);
    setDescontoPendente(false);
    setPrecosPendentes({});
    setError("");
  }

  async function onSaveFormato(productId: number, formato: string) {
    setError("");
    try {
      await saveFormato(productId, formato);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não salvou o formato");
    }
  }

  async function onExcluirCliente(modo: "base" | "inativar") {
    if (!clienteId) return;
    setSaving(true);
    setError("");
    try {
      await deleteCliente(clienteId, modo);
      setExcluirCliente(false);
      setClienteId(null);
      setForm({ ...vazio, lista: listas[0]?.id ?? null });
      setMarcados({});
      setOriginal(null);
      setClientePendente(false);
      setProdutoId(null);
      setDesconto("");
      setDescontoPendente(false);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não excluiu o cliente");
    } finally {
      setSaving(false);
    }
  }

  async function onExcluirProduto(product: Produto) {
    setSaving(true);
    setError("");
    try {
      await deleteProduto(product.id);
      setExcluirId(null);
      setPrecosPendentes((atual) => {
        const next = { ...atual };
        for (const key of Object.keys(next)) {
          if (key.startsWith(`${product.id}:`)) delete next[key];
        }
        return next;
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não excluiu o produto");
    } finally {
      setSaving(false);
    }
  }

  async function onNovoProduto() {
    const formato = novoFormato === "outro" ? novoOutro.trim() : novoFormato;
    if (!novoNome.trim() || !formato) {
      setError("Informe o nome e o formato. Ex.: Alface Palito, c/ 03 unidades.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await createProduto(novoNome.trim(), formato);
      setNovoNome("");
      setNovoFormato("unidade");
      setNovoOutro("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não adicionou o produto");
    } finally {
      setSaving(false);
    }
  }

  async function onSavePrice(priceListId: number, productId: number, raw: string) {
    const price = lerReais(raw);
    if (Number.isNaN(price) || price < 0) return;
    setError("");
    try {
      await saveTablePrice(priceListId, productId, price);
      setPrecosPendentes((atual) => {
        const next = { ...atual };
        delete next[`${productId}:${priceListId}`];
        return next;
      });
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não salvou o preço");
    }
  }

  async function onSaveDesconto() {
    if (!clienteId || !produtoId || precoFinal === null) return;
    setSaving(true);
    setError("");
    try {
      const saved = await saveDesconto(clienteId, produtoId, precoFinal);
      setClientes((current) => current.map((item) => (item.id === saved.id ? saved : item)));
      setDesconto("");
      setProdutoId(null);
      setDescontoPendente(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não salvou o desconto");
    } finally {
      setSaving(false);
    }
  }

  async function onRemove(productId: number) {
    if (!clienteId) return;
    setError("");
    try {
      const saved = await removeDesconto(clienteId, productId);
      setClientes((current) => current.map((item) => (item.id === saved.id ? saved : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não removeu o desconto");
    }
  }

  function gravado(campo: keyof Formulario): string | undefined {
    if (!original || !clientePendente) return undefined;
    const antigo = original[campo];
    const atual = form[campo];
    if (String(antigo ?? "") === String(atual ?? "")) return undefined;
    return String(antigo || "—");
  }

  const chat = (
    <CadastroChat pending={pending} saving={saving} onSend={onChat} onConfirm={confirmar} onDiscard={descartar} />
  );

  return (
    <section className={aba === "tabelas" ? "cadastro com-chat" : "cadastro duas com-chat"}>
      <div className="conteudo">
        {aba === "tabelas" ? (
        <div>
          <h1>Preços</h1>
          <p>
            Cada produto tem quatro preços: Varejo, Restaurantes, Revenda e Amigos. O preço vale para o formato da
            quantidade: unidade, maço, kg ou peso fixo.
          </p>
          {error ? <p className="error">{error}</p> : null}
          <form
            className="linha"
            onSubmit={(event) => {
              event.preventDefault();
              void onNovoProduto();
            }}
          >
            <input value={novoNome} placeholder="Ex.: Alface Palito" onChange={(event) => setNovoNome(event.target.value)} />
            <select value={novoFormato} onChange={(event) => setNovoFormato(event.target.value)}>
              {FORMATOS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
              <option value="outro">outro</option>
            </select>
            {novoFormato === "outro" ? (
              <input
                value={novoOutro}
                placeholder="Ex.: c/ 03 unidades"
                onChange={(event) => setNovoOutro(event.target.value)}
              />
            ) : null}
            <button className="primary" type="submit" disabled={saving}>
              Adicionar
            </button>
          </form>
          <table className="grade">
            <thead>
              <tr>
                <th>Produto</th>
                <th>Formato</th>
                <th>Preço</th>
                <th>Valor</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {linhasPreco.map(({ product, lista, price, pending: valor, first }) => (
                <PriceRow
                  key={`${product.id}-${lista.id}`}
                  name={first ? product.name : ""}
                  formato={first ? product.formato || "unidade" : ""}
                  excluindo={first && excluirId === product.id}
                  onAskDelete={first ? () => setExcluirId(product.id) : undefined}
                  onCancelDelete={() => setExcluirId(null)}
                  onDelete={first ? () => onExcluirProduto(product) : undefined}
                  tipo={lista.name}
                  price={price}
                  pending={valor}
                  onSave={(raw) => onSavePrice(lista.id, product.id, raw)}
                  onSaveFormato={(formato) => onSaveFormato(product.id, formato)}
                  onDraft={(raw) =>
                    setPrecosPendentes((atual) => ({ ...atual, [`${product.id}:${lista.id}`]: raw }))
                  }
                />
              ))}
            </tbody>
          </table>
        </div>
        ) : (
        <>
      <div>
        <h1>Clientes</h1>
        <div className="linha">
          <button type="button" onClick={novoCliente}>
            Novo
          </button>
        </div>
        <ul className="lista">
          {!clienteId && form.nome.trim() ? (
            <li>
              <button type="button" className="primary">
                {form.nome}
                <small>na tela, falta confirmar</small>
              </button>
            </li>
          ) : null}
          {clientes.map((item) => (
            <li key={item.id}>
              <button type="button" className={item.id === clienteId ? "primary" : undefined} onClick={() => openCliente(item)}>
                {item.name}
                <small>
                  {item.kind === "comercio" ? "Comércio" : "Pessoa física"}
                  {showPhone(item.phone_e164) ? ` · ${showPhone(item.phone_e164)}` : ""}
                </small>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h2>{clienteId ? "Cliente" : "Novo cliente"}</h2>
        {clienteId ? (
          <div className="linha">
            {excluirCliente ? (
              <>
                <span>Excluir este cliente?</span>
                <button className="danger" type="button" disabled={saving} onClick={() => void onExcluirCliente("base")}>
                  Excluir da base de dados
                </button>
                <button type="button" disabled={saving} onClick={() => void onExcluirCliente("inativar")}>
                  Inativar Cliente
                </button>
                <button type="button" disabled={saving} onClick={() => setExcluirCliente(false)}>
                  Cancelar
                </button>
              </>
            ) : (
              <button className="danger" type="button" onClick={() => setExcluirCliente(true)}>
                Excluir
              </button>
            )}
          </div>
        ) : null}
        <div className="linha">
          <button type="button" className={form.tipo !== "comercio" ? "primary" : undefined} onClick={() => escolherTipo("pessoa")}>
            Pessoa física
          </button>
          <button type="button" className={form.tipo === "comercio" ? "primary" : undefined} onClick={() => escolherTipo("comercio")}>
            Comércio
          </button>
        </div>
        <Campo
          label={form.tipo === "comercio" ? "Nome do comércio" : "Nome completo"}
          required
          pending={marcados.nome}
          antes={gravado("nome")}
          value={form.nome}
          onChange={(valor) => editar("nome", valor)}
        />
        <Campo
          label={form.tipo === "comercio" ? "Telefone do comércio" : "Celular 1"}
          required
          pending={marcados.celular1}
          antes={gravado("celular1")}
          value={form.celular1}
          onChange={(valor) => editar("celular1", valor)}
        />
        <Campo label="Celular 2" pending={marcados.celular2} antes={gravado("celular2")} value={form.celular2} onChange={(valor) => editar("celular2", valor)} />
        <Campo label="Endereço" required pending={marcados.endereco} antes={gravado("endereco")} value={form.endereco} onChange={(valor) => editar("endereco", valor)} />
        <Campo
          label="Localização"
          required
          pending={marcados.localizacao}
          antes={gravado("localizacao")}
          value={form.localizacao}
          placeholder="Link do mapa ou ponto de referência"
          onChange={(valor) => editar("localizacao", valor)}
        />
        <label className="campo">
          Observação de entrega
          <textarea
            className={marcados.observacao ? "pendente" : undefined}
            value={form.observacao}
            placeholder="Se não estiver no local, onde deixar"
            onChange={(event) => editar("observacao", event.target.value)}
          />
        </label>
        <label className="campo">
          Preço base
          <select
            className={marcados.lista ? "pendente" : undefined}
            value={form.lista ?? ""}
            onChange={(event) => editar("lista", Number(event.target.value))}
          >
            {listas.map((lista) => (
              <option key={lista.id} value={lista.id}>
                {lista.name}
              </option>
            ))}
          </select>
        </label>
        <p>Celular 2 e a observação são opcionais. O restante precisa estar preenchido para confirmar.</p>
        {form.tipo === "comercio" ? (
          <div className="desconto-box">
            <h2>Pessoas</h2>
            <p>Pode ser uma pessoa nos três papéis, ou várias em cada um. Proprietário, quem pede e recebe, e quem cuida do financeiro.</p>
            {form.pessoas.map((pessoa, index) => (
              <div className="pessoa" key={index}>
                <Campo
                  label="Nome"
                  value={pessoa.nome}
                  onChange={(valor) => alterarPessoa(index, { nome: valor })}
                />
                <Campo
                  label="Celular"
                  value={pessoa.celular}
                  onChange={(valor) => alterarPessoa(index, { celular: valor })}
                />
                <div className="papeis">
                  {PAPEIS.map(([id, rotulo]) => (
                    <label key={id}>
                      <input
                        type="checkbox"
                        checked={pessoa.papeis.includes(id)}
                        onChange={() => alternarPapel(index, id)}
                      />{" "}
                      {rotulo}
                    </label>
                  ))}
                </div>
                <button type="button" onClick={() => removerPessoa(index)}>
                  Remover
                </button>
              </div>
            ))}
            <button type="button" onClick={adicionarPessoa}>
              Adicionar pessoa
            </button>
          </div>
        ) : null}
        <div className="desconto-box">
          <h2>Desconto geral do pedido</h2>
          <Campo
            label="Percentual"
            pending={marcados.descontoPedido}
            antes={gravado("descontoPedido")}
            value={form.descontoPedido}
            placeholder="Ex.: 10"
            onChange={(valor) => editar("descontoPedido", valor)}
          />
          <p>Vale em todos os pedidos deste cliente, em cima do total.</p>
        </div>
        {error ? <p className="error">{error}</p> : null}

        {cliente ? (
          <div className="desconto-box">
            <h2>Desconto em um produto</h2>
            <p>Vale só neste produto, em reais, em cima do preço {cliente.price_list_name}.</p>
            <label className="campo">
              Produto
              <select
                className={descontoPendente ? "pendente" : undefined}
                value={produtoId ?? ""}
                onChange={(event) => setProdutoId(event.target.value ? Number(event.target.value) : null)}
              >
                <option value="">—</option>
                {produtos.map((product) => (
                  <option key={product.id} value={product.id}>
                    {rotuloProduto(product.name, product.formato || "unidade")}
                  </option>
                ))}
              </select>
            </label>
            <p>Preço base: {money(precoBase)}</p>
            <label className="campo">
              Desconto em R$
              <input
                className={descontoPendente ? "pendente" : undefined}
                value={desconto}
                disabled={precoBase === undefined}
                onChange={(event) => setDesconto(event.target.value)}
              />
            </label>
            <p>Fica {money(precoFinal)}</p>
            <button className="primary" type="button" disabled={saving || precoFinal === null} onClick={onSaveDesconto}>
              Salvar desconto
            </button>
            <table className="grade">
              <thead>
                <tr>
                  <th>Produto</th>
                  <th>Preço base</th>
                  <th>Desconto</th>
                  <th>Fica</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cliente.descontos.map((item) => (
                  <tr key={item.product_id}>
                    <td>{item.product_name}</td>
                    <td>{money(item.preco_base)}</td>
                    <td>{money(item.desconto)}</td>
                    <td>{money(item.preco)}</td>
                    <td>
                      <button type="button" onClick={() => onRemove(item.product_id)}>
                        Remover
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
        </>
        )}
      </div>
      {chat}
    </section>
  );
}

function FormatoCampo({ value, onSave }: { value: string; onSave: (formato: string) => void }) {
  const [outro, setOutro] = useState(false);
  const [texto, setTexto] = useState("");
  const opcoes = FORMATOS.includes(value) ? FORMATOS : [value, ...FORMATOS];
  return (
    <div className="formato">
      <select
        value={outro ? "outro" : value}
        onChange={(event) => {
          const escolhido = event.target.value;
          if (escolhido === "outro") {
            setOutro(true);
            return;
          }
          setOutro(false);
          if (escolhido !== value) onSave(escolhido);
        }}
      >
        {opcoes.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
        <option value="outro">outro</option>
      </select>
      {outro ? (
        <span className="linha">
          <input value={texto} placeholder="Ex.: c/ 03 unidades" onChange={(event) => setTexto(event.target.value)} />
          <button
            type="button"
            onClick={() => {
              if (!texto.trim()) return;
              onSave(texto.trim());
              setOutro(false);
              setTexto("");
            }}
          >
            Salvar
          </button>
        </span>
      ) : null}
    </div>
  );
}

function Campo({
  label,
  value,
  onChange,
  pending,
  required,
  placeholder,
  antes,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  pending?: boolean;
  required?: boolean;
  placeholder?: string;
  antes?: string;
}) {
  return (
    <label className="campo">
      {label}
      {required ? " *" : ""}
      <input
        className={pending ? "pendente" : undefined}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value)}
      />
      {antes ? <small className="gravado">gravado: {antes}</small> : null}
    </label>
  );
}

function PriceRow({
  name,
  formato,
  tipo,
  price,
  pending,
  excluindo,
  onSave,
  onSaveFormato,
  onDraft,
  onAskDelete,
  onCancelDelete,
  onDelete,
}: {
  name: string;
  formato: string;
  tipo: string;
  price?: number;
  pending?: string;
  excluindo?: boolean;
  onSave: (raw: string) => void;
  onSaveFormato: (formato: string) => void;
  onDraft: (raw: string) => void;
  onAskDelete?: () => void;
  onCancelDelete?: () => void;
  onDelete?: () => void;
}) {
  const [raw, setRaw] = useState(price === undefined ? "" : formatarReais(price));
  useEffect(() => {
    if (pending !== undefined) setRaw(pending);
    else setRaw(price === undefined ? "" : formatarReais(price));
  }, [price, pending]);
  return (
    <tr className={pending !== undefined ? "pendente" : undefined}>
      <td>
        {name ? (
          <div className="produto-nome">
            <span>{name}</span>
            {excluindo ? (
              <span className="linha">
                <span>Excluir este produto?</span>
                <button className="danger" type="button" onClick={onDelete}>
                  Confirmar
                </button>
                <button type="button" onClick={onCancelDelete}>
                  Cancelar
                </button>
              </span>
            ) : (
              <button className="danger" type="button" onClick={onAskDelete}>
                Excluir
              </button>
            )}
          </div>
        ) : null}
      </td>
      <td>{formato ? <FormatoCampo value={formato} onSave={onSaveFormato} /> : null}</td>
      <td>{tipo}</td>
      <td>
        <input
          value={raw}
          onChange={(event) => {
            setRaw(event.target.value);
            if (pending !== undefined) onDraft(event.target.value);
          }}
        />
        {pending !== undefined ? (
          <small className="gravado">gravado: {price === undefined ? "—" : formatarReais(price)}</small>
        ) : null}
      </td>
      <td>
        <button type="button" onClick={() => onSave(raw)}>
          Salvar
        </button>
      </td>
    </tr>
  );
}
