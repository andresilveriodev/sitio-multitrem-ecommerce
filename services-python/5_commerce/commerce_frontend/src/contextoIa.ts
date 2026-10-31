export type ContextoTela = {
  tela: string;
  titulo: string;
  instrucao: string;
  cliente_da_tela: boolean;
  observacao_com: boolean;
};

export type FatosTela = {
  cliente?: string;
  data?: string;
  tabela?: string;
  endereco?: string;
};

const API = "http://127.0.0.1:8002/api/v1/cadastro";

const VAZIO: Record<"cliente" | "data" | "tabela" | "endereco", string> = {
  cliente: "não informado",
  data: "não informada",
  tabela: "não informada",
  endereco: "não informado",
};

let cache: ContextoTela[] | null = null;

export function invalidarContextosIa(): void {
  cache = null;
}

export function montarContexto(instrucao: string, fatos: FatosTela): string {
  const valores = {
    cliente: fatos.cliente?.trim() || VAZIO.cliente,
    data: fatos.data?.trim() || VAZIO.data,
    tabela: fatos.tabela?.trim() || VAZIO.tabela,
    endereco: fatos.endereco?.trim() || VAZIO.endereco,
  };
  return instrucao.replace(/\{(cliente|data|tabela|endereco)\}/g, (_trecho, chave: keyof typeof valores) => valores[chave]);
}

async function lerLista(response: Response): Promise<ContextoTela[]> {
  const body = await response.json().catch(() => null);
  if (!response.ok || !Array.isArray(body)) {
    const detail = body && typeof body.detail === "string" ? body.detail : "Não carreguei o contexto das telas";
    throw new Error(detail);
  }
  return body as ContextoTela[];
}

export async function carregarContextosIa(): Promise<ContextoTela[]> {
  if (cache) return cache;
  const response = await fetch(`${API}/contexto-ia`);
  const lista = await lerLista(response);
  cache = lista;
  return lista;
}

export async function salvarContextoIa(
  tela: string,
  dados: { instrucao: string; cliente_da_tela: boolean; observacao_com: boolean },
): Promise<ContextoTela> {
  const response = await fetch(`${API}/contexto-ia/${tela}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Não salvei o contexto";
    throw new Error(detail);
  }
  const salvo = body as ContextoTela;
  cache = (cache ?? []).map((item) => (item.tela === tela ? salvo : item));
  if (cache.length === 0) cache = null;
  return salvo;
}
