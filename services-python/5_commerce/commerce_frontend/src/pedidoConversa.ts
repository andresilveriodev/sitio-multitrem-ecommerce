import type { Cliente, Lista, Produto } from "./cadastroApi";
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

export function listarClientes(nome: string, clientes: Cliente[]): Cliente[] {
  const alvo = fold(nome);
  if (!alvo) return [];
  const exatos = clientes.filter((item) => fold(item.name) === alvo);
  const parecidos = clientes.filter(
    (item) => alvo.length >= 3 && fold(item.name) !== alvo && fold(item.name).includes(alvo),
  );
  return [...exatos, ...parecidos];
}

export function acharCliente(nome: string, clientes: Cliente[]): Cliente | undefined {
  const lista = listarClientes(nome, clientes);
  return lista.length === 1 ? lista[0] : undefined;
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
    tabela: undefined,
    desconto: descontoVeioDoCadastro ? 0 : order.desconto,
    itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
  };
}

export function nomeNaBoleta(order: Order, nome: string, catalogo: CatalogoPedido, commit: boolean): Order {
  const digitado = commit ? nome.trim().replace(/\s+/g, " ") : nome;
  const alvo = fold(digitado.trim());
  const anterior = order.clienteId ? catalogo.clientes.find((item) => item.id === order.clienteId) : undefined;
  if (anterior && alvo && fold(anterior.name).startsWith(alvo) && alvo !== fold(anterior.name)) {
    return { ...order, cliente: digitado };
  }
  const exatos = alvo ? catalogo.clientes.filter((item) => fold(item.name) === alvo) : [];
  const cliente = exatos.length === 1 ? exatos[0] : commit ? acharCliente(digitado, catalogo.clientes) : undefined;
  if (!cliente) return soltarCliente(order, digitado, catalogo.clientes);
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

function clienteDaNota(order: Order, clientes: Cliente[]): Cliente | undefined {
  if (order.clienteId) return clientes.find((item) => item.id === order.clienteId);
  return acharCliente(order.cliente, clientes);
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

export function aplicarFormatoDaConversa(orders: Order[], frase: string, produtos: Produto[]): Order[] {
  const linhas = frase
    .split(/\r?\n/)
    .map((linha) => fold(linha))
    .filter((linha) => /\bpalitos?\b/.test(linha));
  if (!linhas.length) return orders;
  const todas = frase.split(/\r?\n/).map((linha) => fold(linha)).filter(Boolean);
  return orders.map((order) => ({
    ...order,
    itens: order.itens.map((item) => {
      const baseTexto = nomeBase(item.produto);
      const base = fold(baseTexto);
      if (!base) return item;
      const cadastrado = produtos.find((produto) => fold(produto.name) === base);
      const nome = cadastrado?.name || baseTexto;
      const dizPalito = /\bpalitos?\b/.test(fold(item.produto));
      const casa = linhas.filter((linha) => linha.includes(base));
      if (!dizPalito && !casa.length) return item;
      if (!dizPalito) {
        const outras = todas.filter((linha) => linha.includes(base) && !/\bpalitos?\b/.test(linha));
        if (outras.length) {
          const qtds = casa.flatMap((linha) => [...linha.matchAll(/\b(\d+)\b/g)].map((achado) => Number(achado[1])));
          if (qtds.length && !qtds.includes(item.qtd)) return item;
        }
      }
      return { ...item, produto: `${nome} (palito)`, tipo: "palito", conhecido: cadastrado ? true : item.conhecido };
    }),
  }));
}

function aplicarPrecos(order: Order, catalogo: CatalogoPedido): Order {
  if (!order.clienteId && listarClientes(order.cliente, catalogo.clientes).length > 1) {
    return {
      ...order,
      clienteId: undefined,
      tabela: undefined,
      itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
    };
  }
  const cliente = clienteDaNota(order, catalogo.clientes);
  const tabelaNome = cliente?.price_list_name || order.tabela || "";
  const lista = catalogo.listas.find((item) => fold(item.name) === fold(tabelaNome));
  if (!lista) {
    return {
      ...order,
      tabela: tabelaNome || undefined,
      itens: order.itens.map((item) => (item.preco_tabela ? { ...item, valor: 0, preco_tabela: false } : item)),
    };
  }
  const itens = order.itens.map((item) => precoDoItem(item, lista.id, cliente, catalogo.produtos));
  const desconto =
    order.desconto > 0 || cliente?.desconto_pedido == null ? order.desconto : cliente.desconto_pedido;
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

function precoDoItem(item: OrderItem, listaId: number, cliente: Cliente | undefined, produtos: Produto[]): OrderItem {
  if (item.valor > 0 && !item.preco_tabela) return item;
  const produto = acharProduto(item.produto, produtos, item.tipo);
  if (!produto) return { ...item, valor: 0, preco_tabela: false };
  const rotulo = rotuloPedido(produto, produtos);
  const tipo = fold(produto.formato) === "palito" ? "palito" : item.tipo;
  const base = produto.precos[String(listaId)];
  if (base === undefined) return { ...item, produto: rotulo, tipo, valor: 0, preco_tabela: false };
  const especial = cliente?.descontos.find((desconto) => desconto.product_id === produto.id);
  const diferenca = especial?.desconto;
  return {
    ...item,
    produto: rotulo,
    tipo,
    valor: base,
    preco_tabela: true,
    desconto: diferenca && diferenca > 0 ? diferenca : item.desconto,
  };
}

export function comPrecos(orders: Order[], catalogo: CatalogoPedido): Order[] {
  return orders.map((order) => aplicarPrecos(order, catalogo));
}

export function temNomeNovo(atuais: Order[], novos: Order[]): boolean {
  return novos.some((novo) => {
    const nome = fold(novo.cliente);
    if (!nome) return false;
    return !atuais.some((atual) => fold(atual.cliente) === nome);
  });
}

function mesclarPedido(atual: Order, novo: Order): Order {
  const nome = novo.cliente.trim();
  return {
    ...atual,
    cliente: nome || atual.cliente,
    clienteId: nome ? novo.clienteId : atual.clienteId,
    data: novo.data.trim() || atual.data,
    endereco: novo.endereco.trim() || atual.endereco,
    desconto: novo.desconto > 0 ? novo.desconto : atual.desconto,
    tabela: novo.tabela || atual.tabela,
    itens: novo.itens,
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

export function perguntaDaListagem(atuais: Order[]): string {
  const nomes = [...new Set(atuais.map((item) => item.cliente.trim()).filter(Boolean))];
  if (nomes.length === 1) {
    return `Já tem um pedido de ${nomes[0]}. Atualizo a listagem ou incluo outro pedido?`;
  }
  return "Já tem pedido na tela. Atualizo a listagem ou incluo outro pedido?";
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

export type ClienteParaIncluir = { nome: string; tabela?: string; endereco?: string };

export function clientesNovos(orders: Order[], clientes: Cliente[]): ClienteParaIncluir[] {
  const vistos = new Set<string>();
  const lista: ClienteParaIncluir[] = [];
  for (const order of orders) {
    const nome = order.cliente.trim();
    if (!nome || order.clienteId || listarClientes(nome, clientes).length > 0) continue;
    const chave = fold(nome);
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    lista.push({
      nome,
      tabela: order.tabela,
      endereco: order.endereco.trim() || undefined,
    });
  }
  return lista;
}

export function respostaDoPedido(orders: Order[], clientes: Cliente[] = []): string {
  if (!orders.length) return "Não vi os itens. Cole a conversa do WhatsApp.";
  const primeiro = orders[0];
  const itens = primeiro.itens.filter((item) => item.qtd > 0);
  const quando = primeiro.data.trim() ? ` para ${primeiro.data}` : "";
  const abertura =
    orders.length === 1
      ? `Separei ${itens.length} ${itens.length === 1 ? "item" : "itens"}${quando}.`
      : `Separei ${orders.length} pedidos${quando}.`;
  if (!primeiro.cliente.trim()) {
    return `${abertura} Qual é o cliente? Sem o nome eu não sei a tabela de preço.`;
  }
  if (!primeiro.clienteId && listarClientes(primeiro.cliente, clientes).length > 1) {
    return `${abertura} Achei mais de um ${primeiro.cliente}. Escolha qual é o cliente.`;
  }
  if (!primeiro.tabela) {
    const cadastrado = acharCliente(primeiro.cliente, clientes);
    const motivo = cadastrado
      ? `${primeiro.cliente} está sem tabela no cadastro.`
      : `Não achei ${primeiro.cliente} no cadastro.`;
    return `${abertura} ${motivo} Qual é a tabela: Varejo, Restaurantes, Revenda ou Amigos?`;
  }
  if (!primeiro.data.trim()) {
    return `${abertura} ${primeiro.cliente} está na tabela ${primeiro.tabela}. Qual é o dia da entrega?`;
  }
  const faltam = itens.filter((item) => !(item.valor > 0)).map((item) => item.produto);
  const aviso = faltam.length ? ` ${faltam.join(", ")} ainda não tem preço nessa tabela.` : "";
  const escolhido = clienteDaNota(primeiro, clientes);
  const fone = telefone(escolhido?.phone_e164);
  const quem = fone ? `${primeiro.cliente} (${fone})` : primeiro.cliente;
  return `${abertura} Usei a tabela ${primeiro.tabela} de ${quem}.${aviso}`;
}

export type ClienteOpcao = { id: number; nome: string; detalhe: string };

export function opcoesDeCliente(orders: Order[], clientes: Cliente[]): ClienteOpcao[] {
  const order = orders.find(
    (item) => item.cliente.trim() && !item.clienteId && listarClientes(item.cliente, clientes).length > 1,
  );
  if (!order) return [];
  return listarClientes(order.cliente, clientes).map((cliente) => ({
    id: cliente.id,
    nome: cliente.name,
    detalhe: [
      cliente.kind === "comercio" ? "Comércio" : "Pessoa física",
      telefone(cliente.phone_e164) || "sem celular",
      cliente.price_list_name || "sem tabela",
    ].join(" · "),
  }));
}
