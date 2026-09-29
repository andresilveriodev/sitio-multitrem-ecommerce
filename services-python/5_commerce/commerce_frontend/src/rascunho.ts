export type Pessoa = {
  nome: string;
  celular: string;
  papeis: string[];
};

export type Formulario = {
  nome: string;
  celular1: string;
  celular2: string;
  endereco: string;
  localizacao: string;
  observacao: string;
  lista: number | null;
  tipo: "pessoa" | "comercio";
  pessoas: Pessoa[];
  descontoPedido: string;
};

export type Marcados = Partial<Record<keyof Formulario, boolean>>;

export type Rascunho = {
  clienteId: number | null;
  form: Formulario;
  marcados: Marcados;
  clientePendente: boolean;
  produtoId: number | null;
  desconto: string;
  descontoPendente: boolean;
  precosPendentes: Record<string, string>;
  original: Formulario | null;
};

const CHAVE = "sitio-cadastro-rascunho";

export const formularioVazio: Formulario = {
  nome: "",
  celular1: "",
  celular2: "",
  endereco: "",
  localizacao: "",
  observacao: "",
  lista: null,
  tipo: "pessoa",
  pessoas: [],
  descontoPedido: "",
};

export function acaoDaFrase(
  frase: string,
  nomes: string[],
): { nome: string; celular1?: string; localizacao?: string } | null {
  const folded = frase.toLocaleLowerCase("pt-BR");
  const nome = [...nomes]
    .filter((item) => item.trim())
    .sort((a, b) => b.length - a.length)
    .find((item) => folded.includes(item.toLocaleLowerCase("pt-BR")));
  if (!nome) return null;
  const acao: { nome: string; celular1?: string; localizacao?: string } = { nome };
  const url = frase.match(/https?:\/\/\S+/i);
  if (url) acao.localizacao = url[0].replace(/[),.;]+$/, "");
  if (/celular|telefone|fone/i.test(frase)) {
    const phone = frase.match(/(?:\+?55\s*)?(?:\(?\d{2}\)?[\s-]*)?\d{4,5}[\s-]?\d{4}/);
    if (phone) acao.celular1 = phone[0].trim();
  }
  return acao;
}

const LISTA_ALIAS: [string, string][] = [
  ["varejo", "Varejo"],
  ["restaurantes", "Restaurantes"],
  ["restaurante", "Restaurantes"],
  ["revenda", "Revenda"],
  ["amigos", "Amigos"],
  ["amigo", "Amigos"],
];

export function formatarReais(value: number): string {
  return value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function lerReais(raw: string): number {
  const texto = raw.trim().replace(/R\$/gi, "").replace(/\s/g, "");
  if (!texto) return Number.NaN;
  const normal = texto.includes(",") ? texto.replace(/\./g, "").replace(",", ".") : texto;
  return Number(normal);
}

function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export type ItemPreco = { nome: string; formato: string };

export function normalizarFormato(valor: string): string {
  const texto = valor.trim().replace(/\s+/g, " ");
  const key = fold(texto);
  if (!key || key === "un" || key === "und" || key === "unid" || key === "unidade") return "unidade";
  if (key === "maco") return "maço";
  if (key === "kg" || key === "quilo" || key === "quilos") return "kg";
  if (key === "peso fixo" || key === "fixo") return "peso fixo";
  return texto;
}

export function rotuloProduto(nome: string, formato: string): string {
  return `${nome} (${normalizarFormato(formato)})`;
}

export function separarFormato(texto: string): { nome: string; formato: string } {
  const limpo = texto.trim().replace(/\s+/g, " ");
  const parenteses = limpo.match(/^(.*?)\s*\(([^)]+)\)\s*$/);
  if (parenteses?.[1].trim()) return { nome: parenteses[1].trim(), formato: normalizarFormato(parenteses[2]) };
  const pacote = limpo.match(/^(.*?)\s+(c\/\s*\d+\s*unidades?)\s*$/i);
  if (pacote?.[1].trim()) return { nome: pacote[1].trim(), formato: pacote[2].replace(/\s+/g, " ") };
  const solto = limpo.match(/^(.*?)\s+(unidade|maço|maco|kg|peso fixo)\s*$/i);
  if (solto?.[1].trim()) return { nome: solto[1].trim(), formato: normalizarFormato(solto[2]) };
  return { nome: limpo, formato: "" };
}

function casarQualquer(nome: string, produtos: ItemPreco[]): string[] | null {
  const limpo = nome.trim().replace(/\s+/g, " ");
  const qualquer = limpo.match(/^(.*?)\s*\(\s*qualquer\s+([^)]+?)\s*\)\s*$/i);
  if (!qualquer) return null;
  const termo = fold(qualquer[2] ?? "");
  if (!termo) return [];
  const titulo = fold(qualquer[1] ?? "");
  const formatoLinha = /\bpalito\b/.test(titulo) ? "palito" : "";
  const seguro = termo.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const regex = new RegExp(`\\b${seguro}\\b`);
  const vistos = new Set<string>();
  const rotulos: string[] = [];
  for (const produto of produtos) {
    if (!regex.test(fold(produto.nome))) continue;
    const rotulo = rotuloProduto(produto.nome, formatoLinha || produto.formato);
    const chave = fold(rotulo);
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    rotulos.push(rotulo);
  }
  return rotulos;
}

function listasNaFrase(frase: string, listas: string[]): string[] {
  const folded = fold(frase);
  const achadas: string[] = [];
  const vistas = new Set<string>();
  for (const [alias, nome] of LISTA_ALIAS) {
    if (!folded.includes(alias)) continue;
    const canon = listas.find((item) => fold(item) === fold(nome)) ?? nome;
    const chave = fold(canon);
    if (vistas.has(chave)) continue;
    vistas.add(chave);
    achadas.push(canon);
  }
  return achadas;
}

function casarProduto(nome: string, produtos: ItemPreco[]): string[] {
  const qualquer = casarQualquer(nome, produtos);
  if (qualquer) return qualquer;
  const linha = fold(nome);
  if (/\b30\b/.test(linha) && linha.includes("ovo")) {
    const achado = produtos.find((produto) => fold(produto.nome) === "cartela 30 ovos");
    return achado ? [rotuloProduto(achado.nome, achado.formato)] : [];
  }
  if (linha.includes("ovo") && (linha.includes("duzia") || /\b12\b/.test(linha))) {
    const achado = produtos.find((produto) => fold(produto.nome) === "ovos");
    return achado ? [rotuloProduto(achado.nome, achado.formato)] : [];
  }
  const separado = separarFormato(nome);
  const key = fold(separado.nome);
  if (!key) return [];
  let candidatos = produtos.filter((produto) => fold(produto.nome) === key);
  if (!candidatos.length) {
    const contidos = produtos.filter((produto) => fold(produto.nome) && key.includes(fold(produto.nome)));
    if (contidos.length) {
      const maior = Math.max(...contidos.map((produto) => fold(produto.nome).length));
      candidatos = contidos.filter((produto) => fold(produto.nome).length === maior);
    }
  }
  if (!candidatos.length) {
    const prefixo = produtos.filter((produto) => fold(produto.nome).startsWith(key));
    if (prefixo.length === 1) candidatos = prefixo;
    else if (key === "brocolis" && prefixo.length && prefixo.every((produto) => fold(produto.nome).startsWith("brocolis"))) {
      candidatos = prefixo;
    }
  }
  if (separado.formato) {
    return candidatos
      .filter(
        (produto) =>
          normalizarFormato(produto.formato) === separado.formato || fold(produto.formato) === fold(separado.formato),
      )
      .map((produto) => rotuloProduto(produto.nome, produto.formato));
  }
  const unidade = candidatos.filter((produto) => normalizarFormato(produto.formato) === "unidade");
  const escolhidos = unidade.length ? unidade : candidatos.length === 1 ? candidatos : [];
  return escolhidos.map((produto) => rotuloProduto(produto.nome, produto.formato));
}

export function precosDaFrase(
  frase: string,
  produtos: ItemPreco[],
  listas: string[],
): { acoes: { tipo: "preco"; produto: string; lista: string; valor: number }[]; faltando: string[] } {
  const listasAlvo = listasNaFrase(frase, listas);
  if (!listasAlvo.length) return { acoes: [], faltando: [] };
  const porChave = new Map<string, { tipo: "preco"; produto: string; lista: string; valor: number }>();
  const faltando: string[] = [];
  for (const bruta of frase.split(/\r?\n/)) {
    const linha = bruta.replace(/[\u{1F000}-\u{1FAFF}\u2600-\u27BF]/gu, "").trim();
    if (!linha) continue;
    const achado = linha.match(/(?:R\$\s*(\d{1,6}(?:\.\d{3})*(?:,\d{1,2})?|\d{1,6}(?:\.\d{2})?)|(\d{1,6},\d{2}))\s*$/i);
    if (!achado) continue;
    const valor = lerReais(achado[1] || achado[2]);
    if (Number.isNaN(valor) || valor < 0) continue;
    const nome = linha
      .slice(0, achado.index ?? 0)
      .replace(/[\s\-–—:|]+$/g, "")
      .replace(/\s+/g, " ")
      .trim();
    if (!nome) continue;
    const casados = casarProduto(nome, produtos);
    if (!casados.length) {
      faltando.push(nome);
      continue;
    }
    for (const lista of listasAlvo) {
      for (const produto of casados) {
        porChave.set(`${fold(produto)}:${fold(lista)}`, { tipo: "preco", produto, lista, valor });
      }
    }
  }
  return { acoes: [...porChave.values()], faltando };
}

export function descreverPrecos(
  acoes: { produto: string; lista: string; valor: number }[],
  faltando: string[],
): string {
  const grupos = new Map<string, string[]>();
  for (const acao of acoes) {
    const atual = grupos.get(acao.lista) ?? [];
    atual.push(`${acao.produto} R$ ${formatarReais(acao.valor)}`);
    grupos.set(acao.lista, atual);
  }
  const partes = [...grupos.entries()].map(([lista, itens]) => `Preço ${lista}: ${itens.join(", ")}`);
  if (faltando.length) partes.push("Não achei " + faltando.join(", "));
  return partes.join(". ") + ". Confirme para salvar.";
}

export function mesmoNome(a: string, b: string): boolean {
  return a.trim().toLocaleLowerCase("pt-BR") === b.trim().toLocaleLowerCase("pt-BR");
}

export function lerRascunho(): Rascunho | null {
  try {
    if (typeof localStorage === "undefined") return null;
    const raw = localStorage.getItem(CHAVE);
    if (!raw) return null;
    const data = JSON.parse(raw) as Rascunho;
    if (!data || typeof data !== "object" || !data.form) return null;
    if (data.form.tipo !== "comercio") data.form.tipo = "pessoa";
    if (!Array.isArray(data.form.pessoas)) data.form.pessoas = [];
    if (typeof data.form.descontoPedido !== "string") data.form.descontoPedido = "";
    return data;
  } catch {
    return null;
  }
}

export function gravarRascunho(rascunho: Rascunho): void {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(rascunho));
  } catch {
    /* a tela segue com o rascunho na memória */
  }
}

export function limparRascunho(): void {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    /* ignore */
  }
}

type AcaoCliente = {
  nome: string;
  celular1?: string;
  celular2?: string;
  endereco?: string;
  localizacao?: string;
  observacao?: string;
  preco_base?: string;
};

export function mesclarCliente(
  estado: {
    form: Formulario;
    id: number | null;
    pendente: boolean;
    marcados: Marcados;
    original: Formulario | null;
  },
  acao: AcaoCliente,
  salvo: { id: number | null; form: Formulario } | null,
  listaId: (nome: string) => number | null,
): {
  form: Formulario;
  id: number | null;
  pendente: boolean;
  marcados: Marcados;
  original: Formulario | null;
  bloqueado: boolean;
} {
  const foundId = salvo?.id ?? null;
  const mesmo =
    (foundId !== null && foundId === estado.id) || mesmoNome(estado.form.nome, acao.nome);
  const outro =
    estado.pendente &&
    estado.form.nome.trim() !== "" &&
    !mesmoNome(estado.form.nome, acao.nome) &&
    !(foundId !== null && foundId === estado.id);
  if (outro) {
    return { ...estado, bloqueado: true };
  }

  let form = estado.form;
  let id = estado.id;
  let marcados = { ...estado.marcados };
  let original = estado.original;

  if (mesmo && (estado.pendente || estado.id !== null)) {
    if (!original) original = { ...form };
  } else {
    form = salvo ? { ...salvo.form } : { ...formularioVazio, nome: acao.nome, lista: form.lista };
    id = foundId;
    original = salvo ? { ...salvo.form } : { ...formularioVazio, lista: form.lista };
    marcados = {};
  }

  const campos: Array<[keyof Formulario, string | undefined]> = [
    ["celular1", acao.celular1],
    ["celular2", acao.celular2],
    ["endereco", acao.endereco],
    ["localizacao", acao.localizacao],
    ["observacao", acao.observacao],
  ];
  if (acao.nome && !mesmoNome(form.nome, acao.nome)) {
    form = { ...form, nome: acao.nome };
    marcados.nome = true;
  } else if (!form.nome.trim() && acao.nome) {
    form = { ...form, nome: acao.nome };
  }
  for (const [campo, valor] of campos) {
    if (!valor || form[campo] === valor) continue;
    form = { ...form, [campo]: valor };
    marcados[campo] = true;
  }
  if (acao.preco_base) {
    const lista = listaId(acao.preco_base);
    if (lista && form.lista !== lista) {
      form = { ...form, lista };
      marcados.lista = true;
    }
  }
  return { form, id, pendente: true, marcados, original, bloqueado: false };
}
