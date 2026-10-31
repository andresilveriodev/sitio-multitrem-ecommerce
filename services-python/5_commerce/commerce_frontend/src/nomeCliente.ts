import type { Cliente } from "./cadastroApi";

/** Palavras que não ajudam a identificar o cliente. */
const STOP = new Set([
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
  "a",
  "o",
  "as",
  "os",
  "dona",
  "seu",
  "sr",
  "sra",
  "novo",
  "restaurante",
  "restaurantes",
  "eventos",
  "comercio",
  "comercial",
  "ltda",
  "me",
  "epp",
]);

/** Abaixo disso não entra na lista de candidatos. */
const LIMIAR = 0.78;
/** Se o 2º ficar a menos que isso do 1º, a escolha é ambígua. */
const FOLGA = 0.06;

function fold(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Tokens úteis do nome (sem stopwords). */
export function tokensNome(value: string): string[] {
  return fold(value)
    .split(" ")
    .filter((palavra) => palavra.length >= 2 && !STOP.has(palavra));
}

/** Esqueleto consonantal: Recando/Recanto → rcnd/rcnt. */
export function esqueleto(value: string): string {
  return fold(value).replace(/[aeiou\s]/g, "");
}

function compacto(value: string): string {
  return fold(value).replace(/ /g, "");
}

/** Jaro-Winkler (0..1). Bom para tipinhos curtos. */
export function jaroWinkler(a: string, b: string): number {
  if (a === b) return 1;
  if (!a.length || !b.length) return 0;

  const alcance = Math.max(0, Math.floor(Math.max(a.length, b.length) / 2) - 1);
  const marcaA = new Array<boolean>(a.length).fill(false);
  const marcaB = new Array<boolean>(b.length).fill(false);

  let matches = 0;
  for (let i = 0; i < a.length; i += 1) {
    const inicio = Math.max(0, i - alcance);
    const fim = Math.min(i + alcance + 1, b.length);
    for (let j = inicio; j < fim; j += 1) {
      if (marcaB[j] || a[i] !== b[j]) continue;
      marcaA[i] = true;
      marcaB[j] = true;
      matches += 1;
      break;
    }
  }
  if (!matches) return 0;

  const seqA: string[] = [];
  const seqB: string[] = [];
  for (let i = 0; i < a.length; i += 1) if (marcaA[i]) seqA.push(a[i]);
  for (let j = 0; j < b.length; j += 1) if (marcaB[j]) seqB.push(b[j]);

  let trocas = 0;
  for (let i = 0; i < seqA.length; i += 1) {
    if (seqA[i] !== seqB[i]) trocas += 1;
  }

  const jaro =
    (matches / a.length + matches / b.length + (matches - trocas / 2) / matches) / 3;

  let prefixo = 0;
  const limite = Math.min(4, a.length, b.length);
  while (prefixo < limite && a[prefixo] === b[prefixo]) prefixo += 1;

  return jaro + prefixo * 0.1 * (1 - jaro);
}

/** Similaridade de uma palavra (grafo + tipinho + esqueleto). */
export function similaridadeToken(a: string, b: string): number {
  if (!a || !b) return 0;
  if (a === b) return 1;
  // Alex ≠ Alexandre: prefixo longo não conta como o mesmo nome.

  const jw = jaroWinkler(a, b);
  const esqA = esqueleto(a);
  const esqB = esqueleto(b);
  const esq =
    esqA.length >= 2 && esqB.length >= 2
      ? jaroWinkler(esqA, esqB) * (esqA === esqB ? 1 : 0.96)
      : 0;

  let nota = Math.max(jw, esq);
  // Nomes curtos (Vera/Verde) enganam o Jaro; exige esqueleto igual ou tipinho mínimo.
  if (Math.min(a.length, b.length) <= 4 && a !== b) {
    if (esqA === esqB && esqA.length >= 2 && Math.abs(a.length - b.length) <= 1) {
      return Math.max(nota, 0.88);
    }
    if (Math.abs(a.length - b.length) > 1 || nota < 0.93) return nota * 0.65;
  }
  return nota;
}

/**
 * Alinha tokens digitados aos do cadastro.
 * Aceita nome curto como prefixo do nome longo (Recanto Verde ⊂ … Restaurante e Eventos).
 */
function similaridadeTokens(digitado: string[], cadastrado: string[]): number {
  if (!digitado.length || !cadastrado.length) return 0;
  if (digitado.length > cadastrado.length + 2) return 0;

  // Uma palavra só: casa com nome de uma palavra, ou com a 1ª palavra forte do composto.
  // Apelido curto ok a partir de 4 letras (Will → Willy; "Ana" com 3 continua fora).
  if (digitado.length === 1) {
    if (cadastrado.length === 1) return similaridadeToken(digitado[0], cadastrado[0]);
    const nota = similaridadeToken(digitado[0], cadastrado[0]);
    return digitado[0].length >= 4 && nota >= 0.9 ? nota * 0.9 : 0;
  }

  // Prefixo ordenado: o caso mais comum na operação.
  if (cadastrado.length >= digitado.length) {
    const notas = digitado.map((palavra, indice) => similaridadeToken(palavra, cadastrado[indice]));
    if (notas.every((nota) => nota >= 0.72)) {
      const media = notas.reduce((soma, nota) => soma + nota, 0) / notas.length;
      const cobertura = digitado.length / Math.max(cadastrado.length, digitado.length);
      // Prefixo curto não é penalizado demais se as palavras baterem bem.
      return media * (0.88 + 0.12 * Math.max(cobertura, 0.85));
    }
  }

  // Saco de palavras: ordem livre (pessoa / comércio misturados).
  const usados = new Set<number>();
  let soma = 0;
  let cobertos = 0;
  for (const palavra of digitado) {
    let melhor = 0;
    let indiceMelhor = -1;
    for (let i = 0; i < cadastrado.length; i += 1) {
      if (usados.has(i)) continue;
      const nota = similaridadeToken(palavra, cadastrado[i]);
      if (nota > melhor) {
        melhor = nota;
        indiceMelhor = i;
      }
    }
    if (indiceMelhor >= 0 && melhor >= 0.72) {
      usados.add(indiceMelhor);
      soma += melhor;
      cobertos += 1;
    }
  }
  if (cobertos < digitado.length) return 0;
  return soma / digitado.length;
}

/** Pontuação 0..1 entre dois nomes livres. */
export function pontuarNome(digitado: string, cadastrado: string): number {
  const q = fold(digitado);
  const c = fold(cadastrado);
  if (!q || !c) return 0;
  if (q === c) return 1;

  const qTok = tokensNome(digitado);
  const cTok = tokensNome(cadastrado);
  if (!qTok.length || !cTok.length) return 0;

  // Um token de cada lado: só a regra de palavra (evita Vera≈Verde pelo Jaro cru).
  if (qTok.length === 1 && cTok.length === 1) {
    return similaridadeToken(qTok[0], cTok[0]);
  }

  // Contenção só com 2+ tokens (evita "verde" ⊂ "recanto verde…").
  if (qTok.length >= 2 && c.includes(q)) return 0.96;
  if (cTok.length >= 2 && q.includes(c)) return 0.93;

  const porTokens = similaridadeTokens(qTok, cTok);
  // Nome composto: tokens mandam. Compacto sozinho faz João Carlos ≈ João Batista.
  if (qTok.length >= 2 && cTok.length >= 2) {
    return porTokens;
  }

  const porCompacto = jaroWinkler(compacto(digitado), compacto(cadastrado));
  const porEsqueleto = jaroWinkler(esqueleto(digitado), esqueleto(cadastrado));

  // Compacto/esqueleto só contam se os nomes tiverem tamanho parecido
  // (evita "Ana" ≈ qualquer coisa longa).
  const tamQ = compacto(digitado).length;
  const tamC = compacto(cadastrado).length;
  const razao = Math.min(tamQ, tamC) / Math.max(tamQ, tamC);
  const grafia = razao >= 0.55 ? Math.max(porCompacto, porEsqueleto * 0.98) : 0;

  return Math.max(porTokens, grafia * (qTok.length === cTok.length ? 1 : 0.9));
}

/** Melhor pontuação do nome digitado contra comércio e contatos. */
export function pontuarCliente(digitado: string, cliente: Cliente): number {
  const alvos = [
    cliente.name,
    cliente.tratamento || "",
    cliente.nome_funil || "",
    ...(cliente.pessoas ?? []).flatMap((pessoa) => [pessoa.nome, pessoa.tratamento || ""]),
  ];
  let melhor = 0;
  for (const alvo of alvos) {
    melhor = Math.max(melhor, pontuarNome(digitado, alvo));
  }
  for (const pessoa of cliente.pessoas ?? []) {
    // "Recanto Maria" / "Maria do Recanto"
    melhor = Math.max(melhor, pontuarNome(digitado, `${cliente.name} ${pessoa.nome}`));
    melhor = Math.max(melhor, pontuarNome(digitado, `${pessoa.nome} ${cliente.name}`));
  }
  return melhor;
}

type Candidato = { cliente: Cliente; score: number };

function ranquear(nome: string, clientes: Cliente[]): Candidato[] {
  const alvo = fold(nome);
  if (alvo.length < 2) return [];

  return clientes
    .map((cliente) => ({ cliente, score: pontuarCliente(nome, cliente) }))
    .filter((item) => item.score >= LIMIAR)
    .sort((a, b) => b.score - a.score || a.cliente.name.localeCompare(b.cliente.name, "pt-BR"));
}

/**
 * Candidatos acima do limiar.
 * Se houver um líder claro, devolve só ele; se empatados, devolve o empate (UI pergunta).
 */
export function listarClientesPorNome(nome: string, clientes: Cliente[]): Cliente[] {
  const lista = ranquear(nome, clientes);
  if (!lista.length) return [];
  const melhor = lista[0].score;
  // Líder claro → um só; empate perto do topo → UI pergunta.
  return lista.filter((item) => melhor - item.score <= FOLGA).map((item) => item.cliente);
}

export function acharClientePorNome(nome: string, clientes: Cliente[]): Cliente | undefined {
  const lista = listarClientesPorNome(nome, clientes);
  return lista.length === 1 ? lista[0] : undefined;
}

function nomeSemParenteses(valor: string): string {
  return valor.replace(/\s*\([^)]*\)\s*/g, " ").replace(/\s+/g, " ").trim();
}

/** Igual, ou um é prefixo do outro (mínimo 4 letras). */
function textosCasam(a: string, b: string): boolean {
  const x = fold(nomeSemParenteses(a));
  const y = fold(nomeSemParenteses(b));
  if (!x || !y) return false;
  if (x === y) return true;
  if (x.length >= 4 && (y.startsWith(x) || x.startsWith(y))) return true;
  return false;
}

/** Razão, nome escolhido no funil, tratamento e dono. Contato financeiro não entra — evita juntar homônimos. */
function apelidosFunil(cliente: Cliente): string[] {
  const donos = (cliente.pessoas ?? [])
    .filter((pessoa) => (pessoa.papeis ?? []).includes("proprietario"))
    .flatMap((pessoa) => [pessoa.nome, pessoa.tratamento || ""]);
  return [cliente.name, cliente.tratamento || "", cliente.nome_funil || "", ...donos]
    .map((item) => item.trim())
    .filter(Boolean);
}

function nomesDosDonos(cliente: Cliente): string[] {
  return (cliente.pessoas ?? [])
    .filter((pessoa) => (pessoa.papeis ?? []).includes("proprietario"))
    .map((pessoa) => pessoa.nome.trim())
    .filter(Boolean);
}

/**
 * Cadastro único cujo nome ou dono casa com o texto.
 * "Edgar" → Sandu Uai, porque Edgar é o proprietário.
 */
export function clienteDoApelido(nome: string, clientes: Cliente[]): Cliente | undefined {
  const alvo = nomeSemParenteses(nome);
  if (alvo.length < 2) return undefined;
  const hits = clientes.filter((cliente) => apelidosFunil(cliente).some((apelido) => textosCasam(alvo, apelido)));
  return hits.length === 1 ? hits[0] : undefined;
}

/** Dois textos da grade são o mesmo cliente (razão e dono, ou o mesmo nome). */
export function mesmoCliente(a: string, b: string, clientes: Cliente[]): boolean {
  const ca = clienteDoApelido(a, clientes);
  const cb = clienteDoApelido(b, clientes);
  if (ca && cb) return ca.id === cb.id;
  if (ca || cb) {
    const cliente = (ca || cb) as Cliente;
    return apelidosFunil(cliente).some((apelido) => textosCasam(a, apelido) && textosCasam(b, apelido));
  }
  return textosCasam(a, b);
}

/**
 * Nome que a célula da grade deve mostrar.
 * Se o cadastro escolheu um nome de funil, usa esse (Will → Willy).
 * Senão, a razão social vira o dono quando o dono já está na grade.
 */
export function nomeParaGrade(
  nome: string,
  clientes: Cliente[],
  gradeTem: (dono: string) => boolean,
): string | null {
  const cru = nome.trim();
  const limpo = nomeSemParenteses(cru);
  if (!limpo) return null;
  const cliente = clienteDoApelido(limpo, clientes);
  const escolhido = (cliente?.nome_funil || "").trim();
  if (cliente && escolhido && fold(limpo) !== fold(escolhido)) {
    const nota = cru.match(/\(([^)]*)\)/);
    return nota ? `${escolhido} (${nota[1].trim()})` : escolhido;
  }
  if (escolhido) return null;
  return nomeDoDonoNaGrade(nome, clientes, gradeTem);
}

/**
 * Célula com a razão social vira o nome do dono, se o dono já está na grade.
 * "Sandu Uai" → "Edgar". Não mexe em célula com horário entre parênteses.
 */
export function nomeDoDonoNaGrade(
  nome: string,
  clientes: Cliente[],
  gradeTem: (dono: string) => boolean,
): string | null {
  const cru = nome.trim();
  const limpo = nomeSemParenteses(cru);
  if (!cru || cru !== limpo) return null;
  const cliente = clienteDoApelido(limpo, clientes);
  if (!cliente || fold(limpo) !== fold(cliente.name)) return null;
  const donos = nomesDosDonos(cliente);
  if (donos.length !== 1 || fold(donos[0]) === fold(limpo)) return null;
  if (!gradeTem(donos[0])) return null;
  return donos[0];
}
