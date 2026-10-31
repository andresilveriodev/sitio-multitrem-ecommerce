import { useEffect, useMemo, useRef, useState } from "react";
import { CadastroChat } from "./CadastroChat";
import { carregarContextosIa, montarContexto } from "./contextoIa";
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
  opcoesNomeFunil,
  precosDaFrase,
  rotuloProduto,
  separarFormato,
  sincronizarEnderecoPrincipal,
  type Formulario,
} from "./rascunho";

type Aba = "clientes" | "tabelas";

export type InclusaoCliente = {
  seq: number;
  nome: string;
  tabela?: string;
  endereco?: string;
  fornecedor?: boolean;
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
  const enderecos =
    item.enderecos && item.enderecos.length > 0
      ? item.enderecos.map((end) => ({
          rotulo: end.rotulo || "Entrega",
          endereco: end.endereco || "",
          localizacao: end.localizacao || "",
          padrao: Boolean(end.padrao),
        }))
      : [
          {
            rotulo: "Entrega",
            endereco: item.endereco ?? "",
            localizacao: item.localizacao ?? "",
            padrao: true,
          },
        ];
  return sincronizarEnderecoPrincipal({
    nome: item.name,
    celular1: showPhone(item.phone_e164),
    celular2: showPhone(item.phone2_e164),
    endereco: item.endereco ?? "",
    localizacao: item.localizacao ?? "",
    enderecos,
    observacao: item.observacao ?? "",
    lista: item.price_list_id ?? listaPadrao,
    tipo: item.kind === "comercio" ? "comercio" : item.kind === "fornecedor" ? "fornecedor" : "pessoa",
    pessoas: (item.pessoas ?? []).map((pessoa) => ({
      nome: pessoa.nome,
      celular: showPhone(pessoa.celular),
      papeis: pessoa.papeis ?? [],
      tratamento: pessoa.tratamento ?? "",
    })),
    tratamento: item.tratamento ?? "",
    nomeFunil: item.nome_funil ?? "",
    descontoPedido: item.desconto_pedido ? String(item.desconto_pedido).replace(".", ",") : "",
  });
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
  if (!form.nome.trim()) itens.push(form.tipo === "fornecedor" ? "nome do fornecedor" : "nome completo");
  const enderecos = form.enderecos.filter((item) => item.endereco.trim() || item.localizacao.trim());
  if (form.tipo === "fornecedor") {
    if (!enderecos.length && !form.localizacao.trim() && !form.endereco.trim()) itens.push("localização");
  } else {
    if (!form.celular1.trim()) itens.push("celular 1");
    if (!enderecos.length) {
      itens.push("endereço e localização");
    } else {
      enderecos.forEach((item, index) => {
        const nome = item.rotulo.trim() || `endereço ${index + 1}`;
        if (!item.endereco.trim()) itens.push(`endereço de ${nome}`);
        if (!item.localizacao.trim()) itens.push(`localização de ${nome}`);
      });
    }
  }
  if (form.tipo !== "pessoa") {
    form.pessoas.forEach((pessoa) => {
      if (pessoa.nome.trim() && pessoa.papeis.length === 0) itens.push(`o papel de ${pessoa.nome.trim()}`);
    });
  }
  return itens;
}

function avisoParaSalvar(form: Formulario): string {
  const falta = faltando(form);
  if (!falta.length) return "";
  const papeis = falta.filter((item) => item.startsWith("o papel de "));
  const resto = falta.filter((item) => !item.startsWith("o papel de "));
  const partes: string[] = [];
  if (resto.length) partes.push("Para salvar precisa de " + resto.join(", ") + ".");
  papeis.forEach((item) => partes.push(`Marque ${item}.`));
  return partes.join(" ");
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
  const [novoPrecos, setNovoPrecos] = useState<Record<number, string>>({});
  const [destaqueProdutoId, setDestaqueProdutoId] = useState<number | null>(null);
  const [buscaProduto, setBuscaProduto] = useState("");
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
      tipo: incluir.fornecedor ? "fornecedor" : "pessoa",
      lista: listaPedido?.id ?? base.lista,
      endereco: incluir.fornecedor ? "" : incluir.endereco ?? "",
      localizacao: incluir.fornecedor ? incluir.endereco ?? "" : "",
      pessoas: incluir.fornecedor ? [{ nome: "", celular: "", papeis: ["proprietario"], tratamento: "" }] : [],
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
    let ativo = true;
    refresh().catch(async (err: Error) => {
      if (!ativo) return;
      setError(err.message);
      await new Promise((resolve) => setTimeout(resolve, 800));
      if (!ativo) return;
      refresh().catch((again: Error) => {
        if (ativo) setError(again.message);
      });
    });
    return () => {
      ativo = false;
    };
  }, [aba]);

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

  const linhasPreco = useMemo(() => {
    const alvo = buscaProduto
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
    const filtrados = alvo
      ? produtos.filter((product) => {
          const nome = `${product.name} ${product.formato || ""}`
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase();
          return nome.includes(alvo);
        })
      : produtos;
    return filtrados.flatMap((product) =>
      listas.map((lista, index) => ({
        product,
        lista,
        price: product.precos[String(lista.id)],
        pending: precosPendentes[`${product.id}:${lista.id}`],
        first: index === 0,
      })),
    );
  }, [produtos, listas, precosPendentes, buscaProduto]);
  const qtdeProdutosLista = useMemo(() => linhasPreco.filter((linha) => linha.first).length, [linhasPreco]);

  function editar<K extends keyof Formulario>(campo: K, valor: Formulario[K]) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({ ...atual, [campo]: valor }));
    setMarcados((atual) => ({ ...atual, [campo]: true }));
    setClientePendente(true);
  }

  function escolherTipo(tipo: "pessoa" | "comercio" | "fornecedor") {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({
      ...atual,
      tipo,
      pessoas:
        tipo !== "pessoa" && atual.pessoas.length === 0
          ? [{ nome: "", celular: "", papeis: tipo === "fornecedor" ? ["proprietario"] : [], tratamento: "" }]
          : atual.pessoas,
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
    setForm((atual) => ({ ...atual, pessoas: [...atual.pessoas, { nome: "", celular: "", papeis: [], tratamento: "" }] }));
    setClientePendente(true);
  }

  function removerPessoa(index: number) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => ({ ...atual, pessoas: atual.pessoas.filter((_, i) => i !== index) }));
    setClientePendente(true);
  }

  function alterarEndereco(index: number, patch: Partial<Formulario["enderecos"][number]>) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => {
      let enderecos = atual.enderecos.map((item, i) => (i === index ? { ...item, ...patch } : item));
      if (patch.padrao) {
        enderecos = enderecos.map((item, i) => ({ ...item, padrao: i === index }));
      }
      return sincronizarEnderecoPrincipal({ ...atual, enderecos });
    });
    setMarcados((atual) => ({ ...atual, endereco: true, localizacao: true }));
    setClientePendente(true);
  }

  function adicionarEndereco() {
    setOriginal((atual) => atual ?? form);
    setForm((atual) =>
      sincronizarEnderecoPrincipal({
        ...atual,
        enderecos: [
          ...atual.enderecos,
          { rotulo: `Entrega ${atual.enderecos.length + 1}`, endereco: "", localizacao: "", padrao: atual.enderecos.length === 0 },
        ],
      }),
    );
    setMarcados((atual) => ({ ...atual, endereco: true, localizacao: true }));
    setClientePendente(true);
  }

  function removerEndereco(index: number) {
    setOriginal((atual) => atual ?? form);
    setForm((atual) => {
      const resto = atual.enderecos.filter((_, i) => i !== index);
      const enderecos =
        resto.length > 0
          ? resto
          : [{ rotulo: "Entrega", endereco: "", localizacao: "", padrao: true }];
      if (!enderecos.some((item) => item.padrao)) enderecos[0].padrao = true;
      return sincronizarEnderecoPrincipal({ ...atual, enderecos });
    });
    setMarcados((atual) => ({ ...atual, endereco: true, localizacao: true }));
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
      let contexto = "";
      try {
        const bases = await carregarContextosIa();
        const base = bases.find((item) => item.tela === (aba === "tabelas" ? "tabelas" : "clientes"));
        if (base) contexto = montarContexto(base.instrucao, { cliente: cliente?.name || "" });
      } catch {
        /* a frase segue sem o texto desta tela */
      }
      const result = await interpretCadastro({
        message: frase,
        tela: aba === "tabelas" ? "precos" : "clientes",
        clientes: clientes.map((item) => ({ nome: item.name })),
        produtos: produtos.map((item) => rotuloProduto(item.name, item.formato || "unidade")),
        listas: listas.map((item) => item.name),
        contexto,
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

    const falta = nextClientePendente ? avisoParaSalvar(nextForm) : "";
    if (falta) avisos.push(falta);
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
        const aviso = avisoParaSalvar(form);
        if (aviso) throw new Error(aviso);
        if (descontoGeral(form.descontoPedido) === undefined) {
          throw new Error("O desconto geral do pedido fica entre 0 e 100%.");
        }
        const listaId = form.lista ?? listas[0]?.id;
        if (!listaId) throw new Error("Escolha o preço base.");
        const pronto = sincronizarEnderecoPrincipal(form);
        const saved = await saveCliente({
          id: id ?? undefined,
          name: pronto.nome.trim(),
          price_list_id: listaId,
          phone_e164: pronto.celular1,
          phone2_e164: pronto.celular2,
          endereco: pronto.tipo === "fornecedor" ? pronto.endereco || pronto.localizacao : pronto.endereco,
          localizacao: pronto.localizacao || pronto.endereco,
          enderecos: pronto.enderecos
            .filter((item) => item.endereco.trim() || item.localizacao.trim())
            .map((item) => ({
              rotulo: item.rotulo.trim() || "Entrega",
              endereco: pronto.tipo === "fornecedor" ? item.endereco || item.localizacao : item.endereco,
              localizacao: item.localizacao || item.endereco,
              padrao: item.padrao,
            })),
          observacao: pronto.observacao,
          kind: pronto.tipo,
          tratamento: pronto.tipo === "pessoa" ? pronto.tratamento : "",
          nome_funil: pronto.nomeFunil,
          pessoas: pronto.tipo === "pessoa" ? [] : pronto.pessoas,
          desconto_pedido: descontoGeral(pronto.descontoPedido),
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
      const criado = await createProduto(novoNome.trim(), formato);
      for (const lista of listas) {
        const raw = (novoPrecos[lista.id] || "").trim();
        if (!raw) continue;
        const price = lerReais(raw);
        if (Number.isNaN(price) || price < 0) continue;
        await saveTablePrice(lista.id, criado.id, price);
      }
      setNovoNome("");
      setNovoFormato("unidade");
      setNovoOutro("");
      setNovoPrecos({});
      setDestaqueProdutoId(criado.id);
      await refresh();
      requestAnimationFrame(() => {
        document.getElementById(`produto-${criado.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
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
            className="novo-produto"
            onSubmit={(event) => {
              event.preventDefault();
              void onNovoProduto();
            }}
          >
            <div className="linha">
              <input
                value={novoNome}
                placeholder="Ex.: Alface Palito"
                aria-label="Nome do produto"
                onChange={(event) => setNovoNome(event.target.value)}
              />
              <select
                value={novoFormato}
                aria-label="Formato"
                onChange={(event) => setNovoFormato(event.target.value)}
              >
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
                  aria-label="Outro formato"
                  onChange={(event) => setNovoOutro(event.target.value)}
                />
              ) : null}
            </div>
            <div className="linha precos-novos">
              {listas.map((lista) => (
                <label key={lista.id} className="preco-novo">
                  <span>{lista.name}</span>
                  <input
                    inputMode="decimal"
                    placeholder="0,00"
                    aria-label={`Preço ${lista.name}`}
                    value={novoPrecos[lista.id] ?? ""}
                    onChange={(event) =>
                      setNovoPrecos((atual) => ({ ...atual, [lista.id]: event.target.value }))
                    }
                  />
                </label>
              ))}
              <button className="primary" type="submit" disabled={saving}>
                {saving ? "Salvando…" : "Adicionar"}
              </button>
            </div>
            <p className="origem">Pode deixar preço em branco e completar depois na lista.</p>
          </form>
          <div className="linha">
            <input
              value={buscaProduto}
              placeholder="Pesquisar produto…"
              aria-label="Pesquisar produto"
              onChange={(event) => setBuscaProduto(event.target.value)}
            />
            {buscaProduto ? (
              <button type="button" onClick={() => setBuscaProduto("")}>
                Limpar
              </button>
            ) : null}
            {buscaProduto ? (
              <span className="origem">
                {qtdeProdutosLista} {qtdeProdutosLista === 1 ? "produto" : "produtos"}
              </span>
            ) : null}
          </div>
          {buscaProduto && qtdeProdutosLista === 0 ? (
            <p className="empty">Nenhum produto com “{buscaProduto}”.</p>
          ) : null}
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
                  rowId={first ? `produto-${product.id}` : undefined}
                  destaque={first && destaqueProdutoId === product.id}
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
                  {item.kind === "comercio" ? "Comércio" : item.kind === "fornecedor" ? "Fornecedor" : "Pessoa física"}
                  {item.nome_funil && item.nome_funil !== item.name ? ` · funil: ${item.nome_funil}` : ""}
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
          <button type="button" className={form.tipo === "pessoa" ? "primary" : undefined} onClick={() => escolherTipo("pessoa")}>
            Pessoa física
          </button>
          <button type="button" className={form.tipo === "comercio" ? "primary" : undefined} onClick={() => escolherTipo("comercio")}>
            Comércio
          </button>
          <button type="button" className={form.tipo === "fornecedor" ? "primary" : undefined} onClick={() => escolherTipo("fornecedor")}>
            Fornecedor
          </button>
        </div>
        <Campo
          label={form.tipo === "comercio" ? "Nome do comércio" : form.tipo === "fornecedor" ? "Nome do fornecedor" : "Nome completo"}
          required
          pending={marcados.nome}
          antes={gravado("nome")}
          value={form.nome}
          onChange={(valor) => editar("nome", valor)}
        />
        {form.tipo === "pessoa" ? (
          <>
            <Campo
            label="Como deseja ser chamado"
            pending={marcados.tratamento}
            value={form.tratamento}
            onChange={(valor) => editar("tratamento", valor)}
            />
            <NomeNoFunil form={form} onChange={(valor) => editar("nomeFunil", valor)} />
          </>
        ) : null}
        <Campo
          label={form.tipo === "comercio" ? "Telefone do comércio" : form.tipo === "fornecedor" ? "Telefone" : "Celular 1"}
          required={form.tipo !== "fornecedor"}
          pending={marcados.celular1}
          antes={gravado("celular1")}
          value={form.celular1}
          onChange={(valor) => editar("celular1", valor)}
        />
        <Campo label="Celular 2" pending={marcados.celular2} antes={gravado("celular2")} value={form.celular2} onChange={(valor) => editar("celular2", valor)} />
        <div className={`campo enderecos-lista ${marcados.endereco || marcados.localizacao ? "pendente" : ""}`}>
          <div className="enderecos-cabecalho">
            <span>Endereços {form.tipo === "fornecedor" ? "" : "*"}</span>
            <button type="button" className="link" onClick={adicionarEndereco}>
              Incluir endereço
            </button>
          </div>
          {form.enderecos.map((item, index) => (
            <div className="endereco-card" key={`end-${index}`}>
              <div className="endereco-card-topo">
                <Campo
                  label="Rótulo"
                  value={item.rotulo}
                  placeholder="Casa, loja, depósito…"
                  onChange={(valor) => alterarEndereco(index, { rotulo: valor })}
                />
                <label className="endereco-padrao">
                  <input
                    type="checkbox"
                    checked={item.padrao}
                    onChange={(event) => alterarEndereco(index, { padrao: event.target.checked })}
                  />
                  Padrão
                </label>
                {form.enderecos.length > 1 ? (
                  <button type="button" className="link danger" onClick={() => removerEndereco(index)}>
                    Remover
                  </button>
                ) : null}
              </div>
              <Campo
                label="Endereço completo"
                required={form.tipo !== "fornecedor"}
                value={item.endereco}
                onChange={(valor) => alterarEndereco(index, { endereco: valor })}
              />
              <Campo
                label="Localização"
                required
                value={item.localizacao}
                placeholder="Link do Google Maps"
                onChange={(valor) => alterarEndereco(index, { localizacao: valor })}
              />
            </div>
          ))}
        </div>
        <label className="campo">
          Observação de entrega
          <textarea
            className={marcados.observacao ? "pendente" : undefined}
            value={form.observacao}
            placeholder="Se não estiver no local, onde deixar"
            onChange={(event) => editar("observacao", event.target.value)}
          />
        </label>
        {form.tipo === "fornecedor" ? null : (
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
        )}
        <p>
          {form.tipo === "fornecedor"
            ? "O nome e o setor bastam. O telefone e o endereço são opcionais. A pessoa é o contato, como o Seu Pedro."
            : "Celular 2 e a observação são opcionais. O restante precisa estar preenchido para confirmar."}
        </p>
        {form.tipo !== "pessoa" ? (
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
                  label="Como deseja ser chamado"
                  value={pessoa.tratamento}
                  onChange={(valor) => alterarPessoa(index, { tratamento: valor })}
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
            <NomeNoFunil form={form} onChange={(valor) => editar("nomeFunil", valor)} />
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

function NomeNoFunil({ form, onChange }: { form: Formulario; onChange: (valor: string) => void }) {
  const opcoes = opcoesNomeFunil(form);
  const atual = form.nomeFunil.trim();
  const lista =
    atual && !opcoes.some((item) => item.valor.toLocaleLowerCase("pt-BR") === atual.toLocaleLowerCase("pt-BR"))
      ? [{ valor: atual, rotulo: atual }, ...opcoes]
      : opcoes;
  return (
    <label className="campo">
      Nome no funil
      <select value={atual} onChange={(event) => onChange(event.target.value)}>
        <option value="">Como está na grade</option>
        {lista.map((item) => (
          <option key={item.valor} value={item.valor}>
            {item.rotulo}
          </option>
        ))}
      </select>
      <small className="gravado">Esse nome entra na grade de avisos. O pedido continua no cadastro.</small>
    </label>
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
  rowId,
  destaque,
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
  rowId?: string;
  destaque?: boolean;
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
  const classe = [pending !== undefined ? "pendente" : "", destaque ? "destaque" : ""].filter(Boolean).join(" ") || undefined;
  return (
    <tr id={rowId} className={classe}>
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
