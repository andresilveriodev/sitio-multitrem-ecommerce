import type { Cliente, Lista, Produto } from "./cadastroApi";
import { acharClientePorNome, listarClientesPorNome } from "./nomeCliente";
import { formatMoney, itemJaPago } from "./orderMath";
import type { Order, OrderItem } from "./types";

export type CatalogoPedido = {
  clientes: Cliente[];
  listas: Lista[];
  produtos: Produto[];
};

const LISTAS: [string, string][] = [
  ["restaurantes", "Restaurantes"],
  ["restaurante", "Restaurantes"],
  ["revenda", "Revenda"],
  ["varejo", "Varejo"],
  ["amigos", "Amigos"],
  ["amigo", "Amigos"],
];

const DIAS: [string, number][] = [
  ["segunda", 0],
  ["terca", 1],
  ["quarta", 2],
  ["quinta", 3],
  ["sexta", 4],
  ["sabado", 5],
  ["domingo", 6],
];

function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function formatarData(value: Date): string {
  const dia = String(value.getDate()).padStart(2, "0");
  const mes = String(value.getMonth() + 1).padStart(2, "0");
  return `${dia}/${mes}`;
}

export function dataDaFrase(texto: string, hoje = new Date()): string {
  const folded = fold(texto);
  const explicita = texto.match(/\b(\d{1,2})\/(\d{1,2})(?:\/\d{2,4})?\b/);
  if (explicita) {
    const dia = Number(explicita[1]);
    const mes = Number(explicita[2]);
    if (dia >= 1 && dia <= 31 && mes >= 1 && mes <= 12) {
      return `${String(dia).padStart(2, "0")}/${String(mes).padStart(2, "0")}`;
    }
  }
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const pyWeek = (base.getDay() + 6) % 7;
  if (/\bamanha\b/.test(folded)) {
    base.setDate(base.getDate() + 1);
    return formatarData(base);
  }
  if (/\bhoje\b/.test(folded)) return formatarData(base);
  for (const [nome, alvo] of DIAS) {
    if (new RegExp(`\\b${nome}\\b`).test(folded)) {
      base.setDate(base.getDate() + ((alvo - pyWeek + 7) % 7));
      return formatarData(base);
    }
  }
  return "";
}

export function listaDaFrase(texto: string, listas: Lista[]): string {
  const folded = fold(texto);
  for (const [alias, nome] of LISTAS) {
    if (new RegExp(`\\b${alias}\\b`).test(folded)) {
      return listas.find((item) => fold(item.name) === fold(nome))?.name ?? nome;
    }
  }
  return "";
}

export function parecePedido(texto: string): boolean {
  const linhas = texto.split(/\r?\n/).map((linha) => linha.trim()).filter(Boolean);
  if (linhas.length >= 3) return true;
  return /\d/.test(texto) && /\b(couve|alface|cebolinha|coentro|salsinha|rucula|rúcula|hortela|hortelã|agriao|agrião|espinafre|manjericao|manjericão|brocolis|brócolis|acelga|almeirao|almeirão|mostarda|ovos|repolho|rabanete|maço|maco|unidade|palito)\b/i.test(texto);
}

function nomeDaFrase(texto: string): string {
  const semLista = texto.replace(/\b(tabela|varejo|restaurantes|restaurante|revenda|amigos|amigo)\b/gi, " ");
  const semData = semLista.replace(/\b(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?|hoje|amanh[ãa]|segunda|ter[çc]a|quarta|quinta|sexta|s[áa]bado|domingo)\b/gi, " ");
  return semData
    .replace(/^(o cliente é|cliente é|o nome é|nome é|é|eh|cliente|nome)\s+/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Rankeia por similaridade (Jaro-Winkler + esqueleto + tokens). Ver nomeCliente.ts. */
export function listarClientes(nome: string, clientes: Cliente[]): Cliente[] {
  return listarClientesPorNome(nome, clientes);
}

export function acharCliente(nome: string, clientes: Cliente[]): Cliente | undefined {
  return acharClientePorNome(nome, clientes);
}

function clienteNaFrase(frase: string, clientes: Cliente[]): Cliente | undefined {
  const semData = frase.replace(/\b\d{1,2}\/\d{1,2}(?:\/\d{2,4})?\b/g, " ");
  const prefixo = semData.split(/\b\d+\b/)[0]?.trim() ?? "";
  if (prefixo.length < 3 || prefixo.length > 40) return undefined;
  return acharCliente(prefixo, clientes);
}

function avisoDePago(nome: string): boolean {
  return /\b(ja pag[oa]s?|pag[oa]s?|pagou)\b/.test(fold(nome));
}

function semAvisoDePago(nome: string): string {
  return nome
    .replace(/\bj[áa]\s+pag[oa]s?\b/gi, " ")
    .replace(/\bpag[oa]s?\b/gi, " ")
    .replace(/\bpagou\b/gi, " ")
    .replace(/\s*[\-–—]+\s*$/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function falaPagoNaFrase(frase: string, cliente: string, order?: Order): boolean {
  const quem = fold(cliente).split(/\s+/).filter((p) => p.length >= 3);
  if (!quem.length) return avisoDePago(frase);
  const linhas = frase.split(/\r?\n/).map((linha) => linha.trim()).filter(Boolean);
  let doCliente = linhas.filter((linha) => {
    const texto = fold(linha);
    return quem.every((parte) => texto.includes(parte)) || texto.includes(quem[0]);
  });
  // Mesmo cliente em duas linhas: casa a fala "paga" com as qtds desse pedido.
  if (order && doCliente.length > 1) {
    const qtds = order.itens.map((item) => Math.round(item.qtd)).filter((qtd) => qtd > 0);
    const bate = doCliente.filter((linha) =>
      qtds.some((qtd) => new RegExp(`(?<!\\d)0*${qtd}(?!\\d)`).test(linha)),
    );
    if (bate.length) doCliente = bate;
  }
  return (doCliente.length ? doCliente : [frase]).some((linha) => avisoDePago(linha));
}

function raizProduto(nome: string): string {
  return fold(nomeBase(nome))
    .replace(/s\b/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

const APELIDO_PRODUTO: Record<string, string> = {
  salsa: "salsinha",
  salsas: "salsinha",
  salsinhas: "salsinha",
  "alface roxo": "alface roxa",
  cartela: "cartela 30 ovos",
  cartelas: "cartela 30 ovos",
  "cartela 30": "cartela 30 ovos",
  "cartelas 30": "cartela 30 ovos",
  "cartela de ovos": "cartela 30 ovos",
  "cartelas de ovos": "cartela 30 ovos",
  "cartela de 30 ovos": "cartela 30 ovos",
  "cartelas de 30 ovos": "cartela 30 ovos",
};

const GENERO_TOKEN: Record<string, string> = {
  roxo: "roxa",
  americano: "americana",
  crespo: "crespa",
  frizze: "frisee",
  frise: "frisee",
};

function baseApelido(base: string): string {
  const chave = fold(base);
  if (APELIDO_PRODUTO[chave]) return APELIDO_PRODUTO[chave];
  const singular = chave.endsWith("s") ? chave.slice(0, -1) : chave;
  return APELIDO_PRODUTO[singular] || chave;
}

const FORMATO_PRODUTO: Record<string, string> = {
  un: "unidade",
  und: "unidade",
  unid: "unidade",
  unidade: "unidade",
  duzia: "duzia",
  maco: "maco",
  marcio: "maco",
  massa: "maco",
  palito: "palito",
};

const PALAVRA_SOLTA = new Set([
  "de",
  "do",
  "da",
  "dos",
  "das",
  "e",
  "em",
  "no",
  "na",
  "nos",
  "nas",
]);

function singularProduto(palavra: string): string {
  const base = palavra.length > 3 && palavra.endsWith("s") ? palavra.slice(0, -1) : palavra;
  return GENERO_TOKEN[base] || base;
}

function tokensProduto(nome: string): string[] {
  return fold(nomeBase(nome))
    .split(" ")
    .filter((palavra) => palavra.length >= 3 && !PALAVRA_SOLTA.has(palavra) && !/^\d+$/.test(palavra))
    .map(singularProduto);
}

function tipoQueSobra(produto: string, formatos: string[]): string {
  const partes = new Set(tokensProduto(produto));
  for (const forma of formatos) {
    if (partes.has(forma) || partes.has(singularProduto(forma))) continue;
    if (forma === "unidade" || forma === "palito" || forma === "maco") return forma;
  }
  return "";
}

function palavrasCruas(frase: string): string[] {
  return fold(frase)
    .split(" ")
    .filter((palavra) => palavra.length >= 3 && !PALAVRA_SOLTA.has(palavra) && !/^\d+$/.test(palavra))
    .map(singularProduto);
}

function produtoProximo(frase: string, produtos: Produto[]): { nome: string; formato: string } | undefined {
  const crus = palavrasCruas(frase);
  if (!crus.length) return undefined;
  const formatos: string[] = [];
  const nomes: string[] = [];
  for (const token of crus) {
    const forma = FORMATO_PRODUTO[token];
    if (forma) formatos.push(forma);
    else if (!nomes.includes(token)) nomes.push(token);
  }
  const catalogo = [...new Set(produtos.map((item) => item.name))];
  const coberto = (nome: string) => {
    const partes = tokensProduto(nome);
    return partes.length > 0 && partes.every((parte) => crus.includes(parte));
  };
  const cobertos = catalogo.filter(coberto);
  if (cobertos.length) {
    const maior = Math.max(...cobertos.map((nome) => tokensProduto(nome).length));
    const melhores = cobertos.filter((nome) => tokensProduto(nome).length === maior);
    if (melhores.length === 1) return { nome: melhores[0], formato: tipoQueSobra(melhores[0], formatos) };
  }
  if (!nomes.length) return undefined;
  const parciais = catalogo.filter((nome) => nomes.every((token) => tokensProduto(nome).includes(token)));
  if (parciais.length !== 1) return undefined;
  return { nome: parciais[0], formato: tipoQueSobra(parciais[0], formatos) };
}

const QTD_EXTENSO: Record<string, number> = {
  um: 1, uma: 1, dois: 2, duas: 2, tres: 3, quatro: 4, cinco: 5, seis: 6, sete: 7, oito: 8, nove: 9, dez: 10,
  onze: 11, doze: 12, treze: 13, quatorze: 14, catorze: 14, quinze: 15, dezesseis: 16, dezessete: 17, dezoito: 18,
  dezenove: 19, vinte: 20,
};

function separarQtdUnidade(texto: string): string {
  // '1kg de jiló' → '1 kg de jiló'
  return (texto || "").replace(
    /\b(\d{1,4}|um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|quatorze|catorze|quinze|dezesseis|dezessete|dezoito|dezenove|vinte)(kg|g|quilos?|kilos?|unid|und|un|d[uú]zias?|ma[cç]os?|cartelas?|palitos?)\b/gi,
    "$1 $2",
  );
}

function quantidadeDaLinha(linha: string): { qtd: number; resto: string } | undefined {
  const achado = separarQtdUnidade(linha)
    .trim()
    .match(/^(um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|quatorze|catorze|quinze|dezesseis|dezessete|dezoito|dezenove|vinte|\d{1,4})\s+(.+)$/i);
  if (!achado) return undefined;
  const token = fold(achado[1]);
  const qtd = /^\d+$/.test(token) ? Number(token) : QTD_EXTENSO[token];
  if (!qtd) return undefined;
  return { qtd, resto: achado[2].trim() };
}

function fraseDoItem(item: OrderItem, frase: string): string {
  const base = tokensProduto(`${item.tipo || ""} ${item.produto}`).filter((token) => !FORMATO_PRODUTO[token]);
  let melhor = `${item.tipo || ""} ${item.produto}`.trim();
  let tamanho = tokensProduto(melhor).length;
  if (!base.length) return melhor;
  for (const linha of frase.split(/\r?\n/)) {
    const achado = quantidadeDaLinha(linha);
    if (!achado || achado.qtd !== item.qtd) continue;
    const pedaco = achado.resto;
    const tokens = tokensProduto(pedaco);
    const cobre = base.every((token) => tokens.includes(token));
    if (cobre && tokens.length >= tamanho) {
      melhor = pedaco;
      tamanho = tokens.length;
    }
  }
  return melhor;
}

function nomeNoCatalogo(nome: string, produtos: Produto[]): string {
  const partes = partesProduto(nome);
  if (produtos.some((item) => fold(item.name) === partes.base)) return nome;
  const alvo = baseApelido(partes.base);
  if (alvo !== partes.base) {
    const apelido = produtos.find((item) => fold(item.name) === alvo);
    if (apelido) return apelido.name;
  }
  const raiz = raizProduto(nome);
  if (!raiz) return nome;
  const achados = produtos.filter((item) => raizProduto(item.name) === raiz);
  const nomes = [...new Set(achados.map((item) => item.name))];
  return nomes.length === 1 ? nomes[0] : nome;
}

function chaveDeItem(nome: string): string {
  const partes = partesProduto(nome);
  return `${baseApelido(partes.base)}|${partes.formato}`;
}

function soOProduto(nome: string): string {
  // "Cartela 30 ovos": o 30 é do nome do produto, não outro item.
  const guardados: string[] = [];
  const mascarado = (nome || "").replace(/\b(cartelas?\s+(?:de\s+)?)(\d{1,3})(\s+ovos?)\b/gi, (trecho) => {
    guardados.push(trecho);
    return `«CART${guardados.length - 1}»`;
  });
  const corte = mascarado.split(/\s*,\s*(?=\d)|\s+e\s+(?=\d)|\s+(?=\d{1,4}\s+[A-Za-zÀ-ÿ])/i)[0] ?? mascarado;
  return guardados
    .reduce((texto, original, indice) => texto.replace(`«CART${indice}»`, original), corte)
    .trim();
}

function juntarPagos(itens: OrderItem[], produtos: Produto[], frase = ""): OrderItem[] {
  const saida: OrderItem[] = [];
  for (const bruto of itens) {
    const perto = produtoProximo(fraseDoItem(bruto, frase), produtos);
    const item = perto
      ? {
          ...bruto,
          produto: perto.nome,
          tipo: perto.formato || bruto.tipo,
          conhecido: true,
        }
      : bruto;
    const pago = avisoDePago(item.produto);
    const limpo = soOProduto(semAvisoDePago(item.produto));
    const produto = nomeNoCatalogo(limpo || item.produto, produtos);
    if (!produto.trim()) continue;
    const chave = chaveDeItem(produto);
    const existente = saida.find((outro) => chave && chaveDeItem(outro.produto) === chave);
    if (existente) {
      if (pago) existente.observacao = existente.observacao || "já pagas";
      else if (item.observacao?.trim() && !existente.observacao?.trim()) existente.observacao = item.observacao;
      if (!(existente.qtd > 0) && item.qtd > 0) existente.qtd = item.qtd;
      continue;
    }
    saida.push({
      ...item,
      produto,
      conhecido: produtos.some((cadastrado) => fold(cadastrado.name) === fold(produto)) ? true : item.conhecido,
      observacao: pago ? item.observacao || "já pagas" : item.observacao,
    });
  }
  return saida;
}

export function prepararPedidos(orders: Order[], frase: string, catalogo: CatalogoPedido): Order[] {
  return orders.map((order) => {
    const pessoas = pessoasDaNota(order, catalogo.clientes);
    const daFrase = order.cliente.trim() ? undefined : clienteNaFrase(frase, pessoas);
    const doNome = !daFrase && order.cliente.trim() ? acharCliente(order.cliente, pessoas) : undefined;
    const achado = daFrase || doNome;
    const cliente = achado?.name || order.cliente;
    const clienteId = achado?.id ?? order.clienteId;
    // Cadastro traz a tabela; eventual sem cadastro usa Varejo (ou a já dita na conversa).
    const tabela =
      order.tabela ||
      achado?.price_list_name ||
      (!clienteId && order.tipo !== "compra" ? "Varejo" : undefined);
    return {
      ...order,
      cliente,
      clienteId,
      tabela,
      pago: Boolean(order.pago) || falaPagoNaFrase(frase, cliente, order),
      itens: juntarPagos(order.itens, catalogo.produtos, frase),
    };
  });
}

function soltarCliente(order: Order, nome: string, clientes: Cliente[]): Order {
  const anterior = order.clienteId ? clientes.find((item) => item.id === order.clienteId) : undefined;
  const enderecoVeioDoCadastro = anterior != null && order.endereco.trim() === (anterior.endereco || "").trim();
  const descontoVeioDoCadastro = anterior != null && order.desconto === (anterior.desconto_pedido ?? 0);
  return {
    ...order,
    cliente: nome,
    clienteId: undefined,
    endereco: enderecoVeioDoCadastro ? "" : order.endereco,
    // Venda eventual: tabela padrão Varejo.
    tabela: order.tipo === "compra" ? undefined : "Varejo",
    desconto: descontoVeioDoCadastro ? 0 : order.desconto,
    itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
  };
}

export function nomeNaBoleta(order: Order, nome: string, catalogo: CatalogoPedido, commit: boolean): Order {
  const pessoas = pessoasDaNota(order, catalogo.clientes);
  const digitado = commit ? nome.trim().replace(/\s+/g, " ") : nome;
  const alvo = fold(digitado.trim());
  const anterior = order.clienteId ? pessoas.find((item) => item.id === order.clienteId) : undefined;
  if (anterior && alvo && fold(anterior.name).startsWith(alvo) && alvo !== fold(anterior.name)) {
    return { ...order, cliente: digitado };
  }
  const exatos = alvo ? pessoas.filter((item) => fold(item.name) === alvo) : [];
  const cliente = exatos.length === 1 ? exatos[0] : commit ? acharCliente(digitado, pessoas) : undefined;
  if (!cliente) {
    const solto = soltarCliente(order, digitado, pessoas);
    if (solto.tipo === "compra") return solto;
    return comPrecos([solto], catalogo)[0];
  }
  const trocou = order.clienteId !== cliente.id;
  return comPrecos(
    [
      {
        ...order,
        cliente: cliente.name,
        clienteId: cliente.id,
        endereco: trocou ? cliente.endereco || "" : order.endereco.trim() ? order.endereco : cliente.endereco || "",
        tabela: undefined,
        desconto: trocou ? 0 : order.desconto,
      },
    ],
    catalogo,
  )[0];
}

function pessoasDaNota(order: Order, clientes: Cliente[]): Cliente[] {
  return order.tipo === "compra"
    ? clientes.filter((item) => item.kind === "fornecedor")
    : clientes.filter((item) => item.kind !== "fornecedor");
}

function clienteDaNota(order: Order, clientes: Cliente[]): Cliente | undefined {
  const pessoas = pessoasDaNota(order, clientes);
  if (order.clienteId) return pessoas.find((item) => item.id === order.clienteId);
  return acharCliente(order.cliente, pessoas);
}

function telefone(value: string | null | undefined): string {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  const local = digits.startsWith("55") && digits.length > 11 ? digits.slice(2) : digits;
  if (local.length === 11) return `${local.slice(0, 2)} ${local.slice(2, 7)}-${local.slice(7)}`;
  if (local.length === 10) return `${local.slice(0, 2)} ${local.slice(2, 6)}-${local.slice(6)}`;
  return value;
}

function nomeBase(nome: string): string {
  return nome
    .replace(/\s*\([^)]*\)\s*/g, " ")
    .replace(/\bpalitos?\b/gi, " ")
    .replace(/\bde\b/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function partesProduto(nome: string): { base: string; formato: string } {
  const marcado = nome.trim().match(/^(.*?)\s*\(([^)]+)\)\s*$/);
  if (marcado?.[1]?.trim()) return { base: fold(marcado[1]), formato: fold(marcado[2]) };
  const key = fold(nome);
  if (/\bpalitos?\b/.test(key)) {
    return { base: fold(nomeBase(nome)), formato: "palito" };
  }
  return { base: key, formato: "" };
}

function acharProduto(nome: string, produtos: Produto[], tipo = ""): Produto | undefined {
  const partes = partesProduto(nome);
  const formato = partes.formato || fold(tipo);
  const exatos = produtos.filter((item) => fold(item.name) === partes.base);
  if (!exatos.length) return undefined;
  if (formato) {
    const alvo = formato === "maco" ? "maco" : formato;
    const peloFormato = exatos.find((item) => fold(item.formato) === alvo);
    if (peloFormato) return peloFormato;
  }
  return (
    exatos.find((item) => fold(item.formato) === "unidade") ??
    exatos.find((item) => fold(item.formato) === "maco") ??
    exatos[0]
  );
}

function rotuloPedido(produto: Produto, produtos: Produto[]): string {
  const formato = produto.formato || "unidade";
  const irmaos = produtos.filter((item) => fold(item.name) === fold(produto.name));
  if (irmaos.length > 1 || fold(formato) === "palito") return `${produto.name} (${formato})`;
  return produto.name;
}

export function rotulosDoCatalogo(produtos: Produto[], extra: string[] = []): string[] {
  const contagem = new Map<string, number>();
  for (const produto of produtos) {
    const chave = fold(produto.name);
    contagem.set(chave, (contagem.get(chave) ?? 0) + 1);
  }
  const rotulos: string[] = [];
  const vistos = new Set<string>();
  for (const produto of produtos) {
    const formato = produto.formato || "unidade";
    const varios = (contagem.get(fold(produto.name)) ?? 0) > 1;
    const rotulo = varios || fold(formato) === "palito" ? `${produto.name} (${formato})` : produto.name;
    const chave = fold(rotulo);
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    rotulos.push(rotulo);
  }
  for (const nome of extra) {
    const chave = fold(nome);
    if (!chave || vistos.has(chave)) continue;
    const base = fold(nome.replace(/\s*\([^)]*\)\s*/g, " "));
    const temFormato = rotulos.some((item) => fold(item.replace(/\s*\([^)]*\)\s*/g, " ")) === base && item.includes("("));
    if (temFormato && !nome.includes("(")) continue;
    vistos.add(chave);
    rotulos.push(nome);
  }
  return rotulos;
}

function pedacosComQuantidade(trecho: string): string[] {
  const saida: string[] = [];
  for (const linha of trecho.split(/\r?\n/)) {
    const limpa = linha.trim();
    if (!limpa) continue;
    const partes = limpa.split(
      /(?<=\S)\s+(?=(?:um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|quatorze|catorze|quinze|dezesseis|dezessete|dezoito|dezenove|vinte|\d{1,4})\b(?!\/))/gi,
    );
    for (const parte of partes) {
      if (parte.trim()) saida.push(parte.trim());
    }
  }
  return saida;
}

export function aplicarFormatoDaConversa(orders: Order[], frase: string, produtos: Produto[]): Order[] {
  const clientes = orders.map((order) => order.cliente.trim()).filter(Boolean);
  return orders.map((order) => {
    const trecho = trechoDoCliente(frase, order.cliente, clientes);
    const pedacos = pedacosComQuantidade(trecho).map((linha) => fold(linha));
    const comPalito = pedacos.filter((linha) => /\bpalitos?\b/.test(linha));
    if (!comPalito.length) return order;
    return {
      ...order,
      itens: order.itens.map((item) => {
        if (fold(item.tipo || "") === "palito") return item;
        const baseTexto = nomeBase(item.produto);
        const base = fold(baseTexto);
        if (!base) return item;
        const cadastrado = produtos.find((produto) => fold(produto.name) === base);
        const nome = cadastrado?.name || baseTexto;
        const dizPalito = /\bpalitos?\b/.test(fold(item.produto));
        if (dizPalito) {
          return { ...item, produto: `${nome} (palito)`, tipo: "palito", conhecido: cadastrado ? true : item.conhecido };
        }
        const casa = comPalito.filter((linha) => {
          const achado = quantidadeDaLinha(linha);
          return achado?.qtd === item.qtd && linha.includes(base);
        });
        if (!casa.length) return item;
        return { ...item, produto: `${nome} (palito)`, tipo: "palito", conhecido: cadastrado ? true : item.conhecido };
      }),
    };
  });
}

function linhaCabecalhoCliente(linha: string, cliente: string): boolean {
  const alvo = fold(cliente);
  if (!alvo) return false;
  const limpa = fold(linha.replace(/[#*_`>-]+/g, " "));
  if (!limpa) return false;
  if (limpa === alvo) return true;
  return limpa.startsWith(alvo) && limpa.length <= alvo.length + 4;
}

function trechoDoCliente(frase: string, cliente: string, clientes: string[]): string {
  if (!frase.trim() || !cliente.trim()) return frase;
  const linhas = frase.split(/\r?\n/);
  const inicio = linhas.findIndex((linha) => linhaCabecalhoCliente(linha, cliente));
  if (inicio < 0) return frase;
  const outros = clientes.map((nome) => fold(nome)).filter((nome) => nome && nome !== fold(cliente));
  let fim = linhas.length;
  for (let i = inicio + 1; i < linhas.length; i += 1) {
    const limpa = fold(linhas[i].replace(/[#*_`>-]+/g, " "));
    if (
      limpa &&
      outros.some((outro) => limpa === outro || (limpa.startsWith(outro) && limpa.length <= outro.length + 4))
    ) {
      fim = i;
      break;
    }
  }
  return linhas.slice(inicio, fim).join("\n");
}

function aplicarPrecos(order: Order, catalogo: CatalogoPedido, forcar = false): Order {
  const pessoas = pessoasDaNota(order, catalogo.clientes);
  if (order.tipo === "compra") {
    const achados = listarClientes(order.cliente, pessoas);
    if (achados.length !== 1) return { ...order, clienteId: undefined };
    const fornecedor = achados[0];
    return {
      ...order,
      cliente: fornecedor.name,
      clienteId: fornecedor.id,
      endereco: order.endereco.trim() || fornecedor.endereco || "",
    };
  }
  if (!order.clienteId && listarClientes(order.cliente, pessoas).length > 1) {
    return {
      ...order,
      clienteId: undefined,
      tabela: undefined,
      itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
    };
  }
  const cliente = clienteDaNota(order, pessoas);
  const tabelaNome = cliente?.price_list_name || order.tabela || "";
  const lista = catalogo.listas.find((item) => fold(item.name) === fold(tabelaNome));
  if (!lista) {
    return {
      ...order,
      tabela: tabelaNome || undefined,
      itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
    };
  }
  const itens = order.itens.map((item) => precoDoItem(item, lista.id, cliente, catalogo.produtos, forcar));
  // Refresh: usa o desconto geral do cadastro (ou zera se foi removido).
  // Sem forçar: só preenche da ficha se a nota ainda não tem desconto.
  const desconto = forcar
    ? cliente?.desconto_pedido != null && cliente.desconto_pedido > 0
      ? cliente.desconto_pedido
      : 0
    : order.desconto > 0 || cliente?.desconto_pedido == null
      ? order.desconto
      : cliente.desconto_pedido;
  return {
    ...order,
    cliente: cliente?.name || order.cliente,
    clienteId: cliente?.id ?? order.clienteId,
    endereco: order.endereco.trim() ? order.endereco : cliente?.endereco || "",
    desconto,
    tabela: lista.name,
    itens,
  };
}

function precoDoItem(
  item: OrderItem,
  listaId: number,
  cliente: Cliente | undefined,
  produtos: Produto[],
  forcar = false,
): OrderItem {
  // Destino reagendado já pago: não cobra e não recoloca preço da tabela.
  if ((item.origemId || item.origemData) && itemJaPago(item.observacao)) {
    return { ...item, valor: 0, preco_tabela: false };
  }
  // Entrega já paga no reagendamento: não recoloca preço.
  if (forcar && !(item.valor > 0) && itemJaPago(item.observacao)) return item;
  if (!forcar && item.valor > 0 && !item.preco_tabela) return item;
  const produto = acharProduto(item.produto, produtos, item.tipo);
  if (!produto) return { ...item, valor: 0, preco_tabela: false };
  const rotulo = rotuloPedido(produto, produtos);
  const tipo = fold(produto.formato) === "palito" ? "palito" : item.tipo || (fold(produto.formato) !== "unidade" ? produto.formato : undefined);
  const base = produto.precos[String(listaId)];
  if (base === undefined) return { ...item, produto: rotulo, tipo, conhecido: true, valor: 0, preco_tabela: false };
  const especial = cliente?.descontos.find((desconto) => desconto.product_id === produto.id);
  const diferenca = especial?.desconto;
  return {
    ...item,
    produto: rotulo,
    tipo,
    conhecido: true,
    valor: base,
    preco_tabela: true,
    desconto: diferenca && diferenca > 0 ? diferenca : forcar ? undefined : item.desconto,
  };
}

export function comPrecos(orders: Order[], catalogo: CatalogoPedido): Order[] {
  return orders.map((order) => aplicarPrecos(order, catalogo));
}

/** Recarrega preços da tabela do cliente, inclusive itens que estavam com preço gravado. */
export function comPrecosForcados(orders: Order[], catalogo: CatalogoPedido): Order[] {
  return orders.map((order) => aplicarPrecos(order, catalogo, true));
}

export function precosForcadosNaNota(order: Order, catalogo: CatalogoPedido): Order {
  return aplicarPrecos(order, catalogo, true);
}

/** Produto trocado ou “já pago” desmarcado: aplica o preço da tabela do cliente da nota. */
export function precosNaTroca(antes: Order, depois: Order, catalogo: CatalogoPedido): Order {
  if (depois.tipo === "compra") return depois;
  const precisa = (item: OrderItem, ant: OrderItem | undefined) => {
    if (!ant) return false;
    if ((ant.produto || "") !== item.produto) return true;
    // Desmarcou pago no reagendado: busca de novo o preço (cliente já está na nota).
    return itemJaPago(ant.observacao) && !itemJaPago(item.observacao) && !(item.valor > 0);
  };
  const mudou = depois.itens.some((item, index) => precisa(item, antes.itens[index]));
  if (!mudou) return depois;
  const pessoas = pessoasDaNota(depois, catalogo.clientes);
  const cliente = clienteDaNota(depois, pessoas);
  const tabelaNome = cliente?.price_list_name || depois.tabela || "";
  const lista = catalogo.listas.find((item) => fold(item.name) === fold(tabelaNome));
  const itens = depois.itens.map((item, index) => {
    const ant = antes.itens[index];
    if (!precisa(item, ant)) return item;
    const trocouProduto = (ant?.produto || "") !== item.produto;
    const limpa = {
      ...item,
      valor: 0,
      preco_tabela: true,
      tipo: trocouProduto ? undefined : item.tipo,
      desconto: trocouProduto ? undefined : item.desconto,
      descontoPercentual: trocouProduto ? undefined : item.descontoPercentual,
    };
    if (!item.produto.trim() || !lista) return { ...limpa, preco_tabela: false, conhecido: Boolean(item.conhecido) };
    return precoDoItem(limpa, lista.id, cliente, catalogo.produtos);
  });
  return { ...depois, tabela: lista?.name || depois.tabela, itens };
}

function dataCitada(data: string, frase: string): boolean {
  const dia = diaDoPedido(data);
  if (!dia) return false;
  const [numeroDia, numeroMes] = dia.split("/").map(Number);
  const formas = [
    `${String(numeroDia).padStart(2, "0")}/${String(numeroMes).padStart(2, "0")}`,
    `${numeroDia}/${numeroMes}`,
    `${String(numeroDia).padStart(2, "0")}/${numeroMes}`,
    `${numeroDia}/${String(numeroMes).padStart(2, "0")}`,
  ];
  return formas.some((forma) => new RegExp(`(?<!\\d)${forma}(?!\\d)`).test(frase));
}

/** Data da conversa, senão a do lote, senão a que já está na tela. */
export function completarDatas(novos: Order[], atuais: Order[], frase: string): Order[] {
  if (!novos.length) return novos;
  const daFrase = dataDaFrase(frase);
  const doLote = novos.find((order) => order.data.trim())?.data.trim() || "";
  const daTela = [...atuais].reverse().find((order) => order.data.trim())?.data.trim() || "";
  const padrao = daFrase || doLote || daTela;
  if (!padrao) return novos;
  // Sem data explícita na conversa: herda a da tela e ignora data inventada pela IA.
  if (!daFrase && daTela) {
    return novos.map((order) => ({ ...order, data: daTela }));
  }
  return novos.map((order) => {
    const atual = order.data.trim();
    if (daFrase && (!atual || !dataCitada(atual, frase))) return { ...order, data: daFrase };
    return { ...order, data: atual || padrao };
  });
}

function diaDoPedido(data: string): string {
  const match = data.trim().match(/^(\d{1,2})\/(\d{1,2})(?:\/\d{2,4})?$/);
  if (!match) return "";
  return `${match[1].padStart(2, "0")}/${match[2].padStart(2, "0")}`;
}

export function temNomeNovo(atuais: Order[], novos: Order[]): boolean {
  return novos.some((novo) => {
    const nome = fold(novo.cliente);
    if (!nome) return true;
    return !atuais.some((atual) => fold(atual.cliente) === nome);
  });
}

/** Mesmo cliente, mesmo dia e mesmo tipo já virou boleta. Não entra outra igual. */
export function pedidoJaNaTela(atuais: Order[], novo: Order): boolean {
  const nome = fold(novo.cliente);
  if (!nome) return false;
  const dia = diaDoPedido(novo.data);
  const compra = novo.tipo === "compra";
  return atuais.some((atual) => {
    if ((atual.tipo === "compra") !== compra) return false;
    return fold(atual.cliente) === nome && diaDoPedido(atual.data) === dia;
  });
}

function mesmoTipo(atual: Order, novo: Order): boolean {
  return (atual.tipo === "compra") === (novo.tipo === "compra");
}

/** Acrescenta qtds dos mesmos produtos e inclui os novos; não apaga o que já estava. */
export function mesclarItens(atuais: OrderItem[], novos: OrderItem[]): OrderItem[] {
  const saida = atuais.map((item) => ({ ...item }));
  for (const bruto of novos) {
    if (!(bruto.qtd > 0) || !bruto.produto.trim()) continue;
    const chave = chaveDeItem(bruto.produto);
    const existente = chave ? saida.find((outro) => chaveDeItem(outro.produto) === chave) : undefined;
    if (existente) {
      existente.qtd += bruto.qtd;
      if (bruto.observacao?.trim() && !existente.observacao?.trim()) existente.observacao = bruto.observacao;
      if (bruto.conhecido) existente.conhecido = true;
      if (bruto.tipo && !existente.tipo) existente.tipo = bruto.tipo;
      continue;
    }
    saida.push({ ...bruto });
  }
  return saida;
}

export function atualizarUm(
  atuais: Order[],
  novo: Order,
  modoItens: "acrescentar" | "substituir" = "acrescentar",
): Order[] {
  const nome = fold(novo.cliente);
  if (!nome) return [...atuais, novo];
  const dia = diaDoPedido(novo.data);
  const noDia = atuais.findIndex(
    (atual) => mesmoTipo(atual, novo) && fold(atual.cliente) === nome && diaDoPedido(atual.data) === dia,
  );
  const indice = noDia >= 0 ? noDia : atuais.findIndex((atual) => mesmoTipo(atual, novo) && fold(atual.cliente) === nome);
  if (indice < 0) return [...atuais, novo];
  return atuais.map((atual, i) => (i === indice ? mesclarPedido(atual, novo, modoItens) : atual));
}

export function aplicarDecisao(
  atuais: Order[],
  novo: Order,
  modo: "atualizar" | "substituir" | "deixar" | "incluir",
): Order[] {
  if (modo === "deixar") return atuais;
  if (modo === "incluir") return [...atuais, novo];
  if (modo === "substituir") return atualizarUm(atuais, novo, "substituir");
  return atualizarUm(atuais, novo, "acrescentar");
}

/**
 * Antes acrescentava sem perguntar quando só havia um pedido do cliente.
 * Agora sempre pergunta (Acrescentar / Substituir / Deixar / Incluir outro).
 */
export function podeAcrescentarDireto(_atuais: Order[], _novo: Order, _frase: string): boolean {
  return false;
}

/**
 * Só um cliente na tela (mesmo com várias boletas) e a IA trouxe itens
 * sem nome (ou com o mesmo): preenche cliente/tabela/endereço a partir da tela.
 */
export function amarrarAoPedidoUnico(atuais: Order[], novos: Order[]): Order[] {
  if (!novos.length || !atuais.length) return novos;
  return novos.map((novo) => {
    const irmaos = atuais.filter((atual) => mesmoTipo(atual, novo));
    if (!irmaos.length) return novo;
    const nomes = [...new Set(irmaos.map((atual) => fold(atual.cliente)).filter(Boolean))];
    if (nomes.length !== 1) return novo;
    const referencia = irmaos.find((atual) => fold(atual.cliente) === nomes[0]);
    if (!referencia) return novo;
    const nomeNovo = fold(novo.cliente);
    if (nomeNovo && nomeNovo !== nomes[0]) return novo;
    return {
      ...novo,
      cliente: referencia.cliente,
      clienteId: referencia.clienteId ?? novo.clienteId,
      data: novo.data.trim() || referencia.data,
      endereco: novo.endereco.trim() || referencia.endereco,
      desconto: novo.desconto > 0 ? novo.desconto : referencia.desconto,
      tabela: novo.tabela || referencia.tabela,
      observacao: novo.observacao?.trim()
        ? novo.observacao
        : irmaos.length === 1
          ? referencia.observacao
          : novo.observacao,
    };
  });
}

function resumoItens(order: Order): string {
  const texto = order.itens
    .filter((item) => item.qtd > 0 && item.produto.trim())
    .map((item) => `${item.qtd} ${item.produto}`)
    .join(", ");
  if (texto.length <= 140) return texto;
  return `${texto.slice(0, 137)}…`;
}

export type RevisaoPedido = {
  ordem: number;
  total: number;
  cliente: string;
  data: string;
  resumo: string;
};

export type DecisaoListagem =
  | "atualizar"
  | "substituir"
  | "deixar"
  | "incluir"
  | "todos-atualizar"
  | "todos-substituir"
  | "todos-incluir";

export function revisaoDe(fila: Order[], indice: number): RevisaoPedido {
  const novo = fila[indice];
  const obs = novo.observacao?.trim();
  return {
    ordem: indice + 1,
    total: fila.length,
    cliente: obs ? `${novo.cliente.trim() || "Sem nome"} (${obs})` : novo.cliente.trim() || "Sem nome",
    data: novo.data.trim(),
    resumo: resumoItens(novo),
  };
}

export function perguntaDeUm(novo: Order, ordem: number, total: number): string {
  const nome = novo.cliente.trim() || "Sem nome";
  const dia = novo.data.trim();
  const passo = total > 1 ? `Pedido ${ordem} de ${total}. ` : "";
  const quando = dia ? ` em ${dia}` : "";
  const obs = novo.observacao?.trim() ? ` (${novo.observacao.trim()})` : "";
  const itens = resumoItens(novo);
  return `${passo}${nome}${quando}${obs} já está na tela.${itens ? ` ${itens}.` : ""} Acrescento nestes itens, substituo tudo, deixo como está ou incluo outro pedido?`;
}

function mesclarPedido(
  atual: Order,
  novo: Order,
  modoItens: "acrescentar" | "substituir" = "acrescentar",
): Order {
  const nome = novo.cliente.trim();
  return {
    ...atual,
    cliente: nome || atual.cliente,
    clienteId: nome ? novo.clienteId : atual.clienteId,
    data: novo.data.trim() || atual.data,
    endereco: novo.endereco.trim() || atual.endereco,
    desconto: novo.desconto > 0 ? novo.desconto : atual.desconto,
    tabela: novo.tabela || atual.tabela,
    observacao: novo.observacao?.trim() ? novo.observacao.trim() : atual.observacao,
    itens: modoItens === "substituir" ? novo.itens : mesclarItens(atual.itens, novo.itens),
  };
}

export function atualizarListagem(atuais: Order[], novos: Order[]): Order[] {
  if (!atuais.length) return novos;
  if (!novos.length) return atuais;
  const usados = new Set<number>();
  const resultado = atuais.map((atual) => {
    const indice = novos.findIndex(
      (novo, i) => !usados.has(i) && fold(novo.cliente) !== "" && fold(novo.cliente) === fold(atual.cliente),
    );
    if (indice < 0) return atual;
    usados.add(indice);
    return mesclarPedido(atual, novos[indice]);
  });
  const restantes = novos.filter((_, i) => !usados.has(i));
  if (!restantes.length) return resultado;
  const ultimo = resultado.length - 1;
  return [...resultado.slice(0, ultimo), mesclarPedido(resultado[ultimo], restantes[0]), ...restantes.slice(1)];
}

export function aplicarResposta(orders: Order[], frase: string, catalogo: CatalogoPedido): Order[] | null {
  if (!orders.length || parecePedido(frase)) return null;
  const tabela = listaDaFrase(frase, catalogo.listas);
  const data = dataDaFrase(frase);
  const nome = nomeDaFrase(frase);
  const encontrados = nome ? listarClientes(nome, catalogo.clientes) : [];
  const cliente = encontrados.length === 1 ? encontrados[0] : undefined;
  const ambiguo = encontrados.length > 1;
  const faltaCliente = orders.some((order) => !order.cliente.trim());
  const pareceNome = Boolean(nome) && nome.length <= 80 && !/\d/.test(nome) && (faltaCliente || Boolean(cliente) || ambiguo);
  if (!tabela && !data && !pareceNome) return null;
  return orders.map((order) => ({
    ...order,
    cliente: pareceNome && (!order.cliente.trim() || cliente || ambiguo) ? cliente?.name || nome : order.cliente,
    clienteId: pareceNome && (cliente || ambiguo) ? cliente?.id : order.clienteId,
    data: data && !order.data.trim() ? data : order.data,
    tabela: ambiguo ? undefined : tabela || order.tabela,
  }));
}

export type ClienteParaIncluir = { nome: string; tabela?: string; endereco?: string; fornecedor?: boolean };

export function clientesNovos(orders: Order[], clientes: Cliente[]): ClienteParaIncluir[] {
  const vistos = new Set<string>();
  const lista: ClienteParaIncluir[] = [];
  for (const order of orders) {
    const nome = order.cliente.trim();
    const pessoas = pessoasDaNota(order, clientes);
    if (!nome || order.clienteId || listarClientes(nome, pessoas).length > 0) continue;
    const chave = fold(nome);
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    const fornecedor = order.tipo === "compra";
    lista.push({
      nome,
      tabela: order.tabela,
      endereco: order.endereco.trim() || undefined,
      fornecedor,
    });
  }
  return lista;
}

export type CompraMarcada = { qtd: number; fornecedor: string };

/** Soma o que foi marcado em Comprados e monta a boleta de compra. */
export function sincronizarCompra(orders: Order[]): Order[] {
  const vendas = orders.filter((order) => order.tipo !== "compra");
  const marcado = vendas.some((order) => order.itens.some((item) => item.qtdComprada != null));
  if (!marcado) return orders;

  const soma = new Map<string, { produto: string; qtd: number }>();
  const tocados = new Set<string>();
  for (const order of vendas) {
    for (const item of order.itens) {
      if (item.qtdComprada == null || !item.produto.trim()) continue;
      const chave = fold(nomeBase(item.produto));
      tocados.add(chave);
      const qtd = item.qtdComprada > 0 ? item.qtdComprada : 0;
      const atual = soma.get(chave);
      if (atual) atual.qtd += qtd;
      else soma.set(chave, { produto: item.produto.trim(), qtd });
    }
  }

  const indice = orders.findIndex((order) => order.tipo === "compra" && !order.id);
  const base = indice >= 0 ? orders[indice] : undefined;
  const anteriores = new Map((base?.itens ?? []).map((item) => [fold(nomeBase(item.produto)), item]));
  const itens: OrderItem[] = [];
  for (const item of base?.itens ?? []) {
    const chave = fold(nomeBase(item.produto));
    if (tocados.has(chave) || !(item.qtd > 0) || !item.produto.trim()) continue;
    itens.push(item);
  }
  for (const [chave, parte] of soma) {
    if (!(parte.qtd > 0)) continue;
    const antes = anteriores.get(chave);
    itens.push({
      produto: antes?.produto || parte.produto,
      qtd: parte.qtd,
      valor: antes?.valor ?? 0,
      conhecido: antes?.conhecido ?? true,
      preco_tabela: false,
    });
  }

  const data = base?.data.trim() || vendas.find((order) => order.data.trim())?.data || "";
  const compra: Order = base
    ? { ...base, tipo: "compra", data, itens }
    : { tipo: "compra", cliente: "", data, endereco: "", desconto: 0, itens };
  if (!base && !itens.length) return orders;
  if (indice < 0) return [...orders, compra];
  return orders.map((order, index) => (index === indice ? compra : order));
}

/** Reparte a compra do dia nas notas de venda, na ordem da tela. */
export function compradoNaTela(orders: Order[]): Array<Array<CompraMarcada | null>> {
  const saldo = new Map<string, { qtd: number; fornecedor: string }[]>();
  for (const compra of orders) {
    if (compra.tipo !== "compra") continue;
    const fornecedor = compra.cliente.trim() || "Fornecedor";
    for (const item of compra.itens) {
      if (!(item.qtd > 0) || !item.produto.trim()) continue;
      const chave = `${compra.data.trim()}|${fold(nomeBase(item.produto))}`;
      const lote = saldo.get(chave) ?? [];
      lote.push({ qtd: item.qtd, fornecedor });
      saldo.set(chave, lote);
    }
  }
  return orders.map((order) =>
    order.itens.map((item) => {
      if (order.tipo === "compra" || !(item.qtd > 0)) return null;
      const chave = `${order.data.trim()}|${fold(nomeBase(item.produto))}`;
      const lote = saldo.get(chave);
      if (!lote?.length) return null;
      let falta = item.qtd;
      let qtd = 0;
      const nomes: string[] = [];
      for (const parte of lote) {
        if (falta <= 0 || parte.qtd <= 0) continue;
        const usa = Math.min(falta, parte.qtd);
        parte.qtd -= usa;
        falta -= usa;
        qtd += usa;
        if (!nomes.includes(parte.fornecedor)) nomes.push(parte.fornecedor);
      }
      return qtd > 0 ? { qtd, fornecedor: nomes.join(", ") } : null;
    }),
  );
}

type Peca = { tipo: "palavra" | "numero"; texto: string; valor?: number; index: number };

function pecasDaFala(frase: string): Peca[] {
  const re = /(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)|(\d{1,4}(?:[.,]\d{1,2})?)|([A-Za-zÀ-ÿ]+)/g;
  const lista: Peca[] = [];
  for (const match of frase.matchAll(re)) {
    const index = match.index ?? 0;
    if (match[1]) continue;
    if (match[2]) {
      const valor = Number(match[2].replace(",", "."));
      if (Number.isFinite(valor)) lista.push({ tipo: "numero", texto: match[2], valor, index });
    } else if (match[3]) lista.push({ tipo: "palavra", texto: fold(match[3]), index });
  }
  return lista;
}

function indiceDoNome(pecas: Peca[], nome: string): number {
  const alvo = fold(nomeBase(nome)).split(" ").filter(Boolean);
  if (!alvo.length || alvo.join("").length < 3) return -1;
  const palavras = pecas.filter((peca) => peca.tipo === "palavra");
  for (let i = 0; i <= palavras.length - alvo.length; i += 1) {
    if (alvo.every((palavra, indice) => palavras[i + indice].texto === palavra)) return palavras[i].index;
  }
  return -1;
}

function soLigacao(pecas: Peca[], de: number, ate: number): boolean {
  return pecas
    .filter((peca) => peca.tipo === "palavra" && peca.index > de && peca.index < ate)
    .every((peca) => peca.texto === "e" || peca.texto === "ou" || peca.texto === "com");
}

/** Lê o preço (e o fornecedor) ditos no chat da boleta de compra. */
export function aplicarFalaCompra(
  order: Order,
  frase: string,
  fornecedores: Cliente[] = [],
): { order: Order; resposta: string } {
  const itens = order.itens.filter((item) => item.qtd > 0 && item.produto.trim());
  const pecas = pecasDaFala(frase);
  const numeros = pecas.filter((peca) => peca.tipo === "numero" && peca.valor != null);
  const palavras = new Set(pecas.filter((peca) => peca.tipo === "palavra").map((peca) => peca.texto));
  const casa = fornecedores
    .filter((cliente) => cliente.kind === "fornecedor" && indiceDoNome(pecas, cliente.name) >= 0)
    .sort((a, b) => fold(b.name).length - fold(a.name).length);
  const fornecedor = casa.length === 1 ? casa[0] : undefined;
  let proximo = order;
  const falas: string[] = [];
  if (casa.length > 1 && !numeros.length) {
    return { order, resposta: "Achei mais de um fornecedor com esse nome. Escolha na lista." };
  }
  if (fornecedor && fornecedor.id !== order.clienteId) {
    proximo = { ...proximo, cliente: fornecedor.name, clienteId: fornecedor.id };
    falas.push(`Fornecedor ${fornecedor.name}.`);
  }
  if (!itens.length) {
    return {
      order: proximo,
      resposta: falas.join(" ") || "Marque Comprados numa nota de venda. Aí eu preencho o preço.",
    };
  }
  const paradas = new Set([
    "preco", "todos", "tudo", "cada", "item", "itens", "reais", "real", "foi", "foram", "para", "por", "que",
    "esse", "essa", "este", "esta", "tambem", "comprei", "custou", "custa", "unidade",
  ]);
  const nomesFornecedor = new Set(casa.flatMap((cliente) => fold(cliente.name).split(" ").filter(Boolean)));
  const sobra = pecas.filter(
    (peca) => peca.tipo === "palavra" && peca.texto.length >= 4 && !paradas.has(peca.texto) && !nomesFornecedor.has(peca.texto),
  );
  const mencionados = itens
    .map((item) => ({ item, index: indiceDoNome(pecas, item.produto) }))
    .filter((parte) => parte.index >= 0)
    .sort((a, b) => a.index - b.index);
  const mudancas = new Map<string, number>();
  if (!mencionados.length && sobra.length && numeros.length) {
    return { order: proximo, resposta: `${falas.join(" ")} Não achei ${sobra.map((peca) => peca.texto).join(" ")} nesta compra.`.trim() };
  }
  if (mencionados.length) {
    mencionados.forEach((parte, ordem) => {
      const fim = mencionados[ordem + 1]?.index ?? Number.POSITIVE_INFINITY;
      let numero = numeros.find((peca) => peca.index >= parte.index && peca.index < fim);
      if (!numero && mencionados[ordem + 1] && soLigacao(pecas, parte.index, mencionados[ordem + 1].index)) {
        numero = numeros.find((peca) => peca.index >= mencionados[ordem + 1].index);
      }
      if (numero?.valor != null) mudancas.set(parte.item.produto, numero.valor);
    });
  } else if (numeros.length && (palavras.has("todos") || palavras.has("tudo") || palavras.has("cada") || palavras.has("preco") || palavras.has("reais") || palavras.has("real"))) {
    const valor = numeros[numeros.length - 1].valor ?? 0;
    itens.forEach((item) => mudancas.set(item.produto, valor));
  }
  if (mudancas.size) {
    proximo = {
      ...proximo,
      itens: proximo.itens.map((item) =>
        mudancas.has(item.produto) ? { ...item, valor: mudancas.get(item.produto) ?? item.valor, preco_tabela: false } : item,
      ),
    };
    const grupos = new Map<number, string[]>();
    for (const [produto, valor] of mudancas) {
      const nomes = grupos.get(valor) ?? [];
      nomes.push(produto);
      grupos.set(valor, nomes);
    }
    if (grupos.size === 1 && mudancas.size === itens.length) {
      falas.push(`Coloquei ${formatMoney([...grupos.keys()][0])} em todos os itens.`);
    } else {
      const partes = [...grupos.entries()].map(([valor, nomes]) => `${formatMoney(valor)} em ${nomes.join(" e ")}`);
      falas.push(`Coloquei ${partes.join(", ")}.`);
    }
  }
  return {
    order: proximo,
    resposta: falas.join(" ") || "Não vi o preço. Diga, por exemplo: o preço de todos os itens foi 3 reais cada.",
  };
}

/** Alface sem crespa/americana/roxa etc. — só "alface" ou "alface (palito)". */
export function alfaceSemVariedade(produto: string): boolean {
  const base = fold(nomeBase(produto));
  return base === "alface";
}

export function variedadeAlface(produto: string): string | null {
  const base = fold(nomeBase(produto));
  if (!base.startsWith("alface")) return null;
  const resto = base.replace(/^alface\s*/, "").trim();
  return resto || null;
}

export type SugestaoAlface = {
  orderIndex: number;
  clienteId: number;
  clienteNome: string;
  variedade: string;
  produtoSugerido: string;
};

function primeiroNome(nome: string): string {
  return nome.trim().split(/\s+/)[0] || nome.trim();
}

export const TEXTO_INTERPRETADOR_FORA =
  "Interpretador de Conversa indisponível. Insira o pedido manualmente ou tente mais tarde. Deseja avisar o administrador?";

export function perguntaAlface(sugestao: SugestaoAlface): string {
  const quem = primeiroNome(sugestao.clienteNome) || "o cliente";
  const tipo = sugestao.variedade;
  return `A alface não foi especificada. Posso colocar alface ${tipo} para ${quem}? Foi assim que ele pediu da última vez.`;
}

export function pareceAfirmacao(frase: string): boolean {
  const t = fold(frase);
  if (!t || parecePedido(frase)) return false;
  return /^(sim|s|pode|pode sim|pode colocar|coloca|coloque|ok|isso|isso mesmo|confirma|confirmar|uhum|aham|claro|positivo)\b/.test(t) || t === "sim" || t === "pode";
}

export function pareceNegacao(frase: string): boolean {
  const t = fold(frase);
  if (!t || parecePedido(frase)) return false;
  return /^(nao|não|n|deixa|deixe|agora nao|agora não|negativo|cancela)\b/.test(t) || t === "nao" || t === "não";
}

/** Troca alfaces genéricas pelo produto sugerido (mantém palito/unidade). */
export function aplicarSugestaoAlface(orders: Order[], sugestao: SugestaoAlface): Order[] {
  return orders.map((order, index) => {
    if (index !== sugestao.orderIndex) return order;
    return {
      ...order,
      itens: order.itens.map((item) => {
        if (!alfaceSemVariedade(item.produto) || !(item.qtd > 0)) return item;
        const partes = partesProduto(item.produto);
        const formato = partes.formato || fold(item.tipo || "");
        const produto =
          formato === "palito"
            ? `${sugestao.produtoSugerido} (palito)`
            : formato && formato !== "unidade"
              ? `${sugestao.produtoSugerido} (${formato})`
              : sugestao.produtoSugerido;
        return {
          ...item,
          produto,
          tipo: formato === "palito" ? "palito" : item.tipo,
          valor: 0,
          preco_tabela: true,
          conhecido: true,
        };
      }),
    };
  });
}

/** Achados no histórico: última alface com variedade (crespa, americana…). */
export function alfaceDoHistorico(itens: { produto: string }[]): { variedade: string; produtoSugerido: string } | null {
  for (let i = itens.length - 1; i >= 0; i -= 1) {
    const produto = itens[i]?.produto || "";
    const tipo = variedadeAlface(produto);
    if (!tipo) continue;
    const sugerido = nomeBase(produto).trim() || produto.replace(/\s*\([^)]*\)\s*/g, " ").trim();
    if (!sugerido) continue;
    return { variedade: tipo, produtoSugerido: sugerido };
  }
  return null;
}

export function respostaDoPedido(orders: Order[], clientes: Cliente[] = []): string {
  if (!orders.length) return "Não vi os itens. Cole a conversa do WhatsApp.";
  const primeiro = orders[0];
  const itens = primeiro.itens.filter((item) => item.qtd > 0);
  const quando = primeiro.data.trim() ? ` para ${primeiro.data}` : "";
  const abertura =
    primeiro.tipo === "compra"
      ? `Separei a compra de ${itens.length} ${itens.length === 1 ? "item" : "itens"}${quando}.`
      : orders.length === 1
        ? `Separei ${itens.length} ${itens.length === 1 ? "item" : "itens"}${quando}.`
        : `Separei ${orders.length} pedidos${quando}.`;
  if (primeiro.tipo === "compra") {
    if (!primeiro.cliente.trim()) return `${abertura} Qual é o fornecedor?`;
    const pessoas = pessoasDaNota(primeiro, clientes);
    if (!primeiro.clienteId && listarClientes(primeiro.cliente, pessoas).length > 1) {
      return `${abertura} Achei mais de um ${primeiro.cliente}. Escolha qual é o fornecedor.`;
    }
    if (!primeiro.clienteId) return `${abertura} Não achei ${primeiro.cliente} nos fornecedores.`;
    return `${abertura} Fornecedor ${primeiro.cliente}.`;
  }
  if (!primeiro.cliente.trim()) {
    return `${abertura} Qual é o nome na nota?`;
  }
  if (!primeiro.clienteId && listarClientes(primeiro.cliente, clientes).length > 1) {
    return `${abertura} Achei mais de um ${primeiro.cliente}. Escolha qual é o cliente.`;
  }
  if (!primeiro.tabela) {
    const cadastrado = acharCliente(primeiro.cliente, clientes);
    const motivo = cadastrado
      ? `${primeiro.cliente} está sem tabela no cadastro.`
      : `${primeiro.cliente} pode ser eventual: diga a tabela (Varejo, Restaurantes, Revenda ou Amigos).`;
    return `${abertura} ${motivo}`;
  }
  if (!primeiro.data.trim()) {
    return `${abertura} ${primeiro.cliente} está na tabela ${primeiro.tabela}. Qual é o dia da entrega?`;
  }
  const faltam = itens.filter((item) => !(item.valor > 0) && !itemJaPago(item.observacao)).map((item) => item.produto);
  const aviso = faltam.length ? ` ${faltam.join(", ")} ainda não tem preço nessa tabela.` : "";
  const escolhido = clienteDaNota(primeiro, clientes);
  const fone = telefone(escolhido?.phone_e164);
  if (escolhido && fone) {
    return `${abertura} Usei a tabela ${primeiro.tabela} de ${primeiro.cliente} (${fone}).${aviso}`;
  }
  if (primeiro.clienteId) {
    return `${abertura} Usei a tabela ${primeiro.tabela} de ${primeiro.cliente}.${aviso}`;
  }
  return `${abertura} ${primeiro.cliente} como eventual na tabela ${primeiro.tabela}. Pode salvar sem cadastrar, ou use o botão para cadastrar.${aviso}`;
}

export type ClienteOpcao = { id: number; nome: string; detalhe: string };

export function opcoesDeCliente(orders: Order[], clientes: Cliente[]): ClienteOpcao[] {
  const order = orders.find((item) => {
    const pessoas = pessoasDaNota(item, clientes);
    return item.cliente.trim() && !item.clienteId && listarClientes(item.cliente, pessoas).length > 1;
  });
  if (!order) return [];
  const pessoas = pessoasDaNota(order, clientes);
  return listarClientes(order.cliente, pessoas).map((cliente) => ({
    id: cliente.id,
    nome: cliente.name,
    detalhe: [
      cliente.kind === "fornecedor" ? "Fornecedor" : cliente.kind === "comercio" ? "Comércio" : "Pessoa física",
      telefone(cliente.phone_e164) || "sem celular",
      cliente.kind === "fornecedor" ? cliente.localizacao || "sem setor" : cliente.price_list_name || "sem tabela",
    ].join(" · "),
  }));
}
