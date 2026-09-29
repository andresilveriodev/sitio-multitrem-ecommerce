const API = "http://127.0.0.1:8002/api/v1/cadastro";

export type Lista = { id: number; name: string };
export type Produto = { id: number; name: string; formato: string; precos: Record<string, number> };
export type Desconto = {
  id: number;
  product_id: number;
  product_name: string;
  preco_base: number | null;
  preco: number;
  desconto: number | null;
};
export type Cliente = {
  id: number;
  name: string;
  phone_e164: string | null;
  phone2_e164: string | null;
  endereco: string | null;
  localizacao: string | null;
  observacao: string | null;
  kind: "pessoa" | "comercio";
  pessoas: { nome: string; celular: string | null; papeis: string[] }[];
  desconto_pedido: number | null;
  price_list_id: number | null;
  price_list_name: string | null;
  descontos: Desconto[];
};

export type Acao =
  | {
      tipo: "cliente";
      nome: string;
      celular1?: string;
      celular2?: string;
      endereco?: string;
      localizacao?: string;
      observacao?: string;
      preco_base?: string;
    }
  | { tipo: "preco"; produto: string; lista: string; valor: number }
  | { tipo: "desconto"; cliente: string; produto: string; desconto: number };
export type Tabelas = { listas: Lista[]; produtos: Produto[] };

async function read<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Falha no cadastro";
    throw new Error(detail);
  }
  return body as T;
}

export function loadTabelas(): Promise<Tabelas> {
  return fetch(`${API}/tabelas`).then((response) => read<Tabelas>(response));
}

export function saveFormato(productId: number, formato: string): Promise<void> {
  return fetch(`${API}/produtos/${productId}/formato`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ formato }),
  }).then((response) => read(response));
}

export function deleteCliente(customerId: number, modo: "base" | "inativar"): Promise<void> {
  return fetch(`${API}/clientes/${customerId}?modo=${modo}`, { method: "DELETE" }).then((response) => read(response));
}

export function deleteProduto(productId: number): Promise<void> {
  return fetch(`${API}/produtos/${productId}`, { method: "DELETE" }).then((response) => read(response));
}

export function createProduto(name: string, formato: string): Promise<Produto> {
  return fetch(`${API}/produtos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, formato }),
  }).then((response) => read<Produto>(response));
}

export function saveTablePrice(priceListId: number, productId: number, price: number): Promise<void> {
  return fetch(`${API}/tabelas/${priceListId}/produtos/${productId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price }),
  }).then((response) => read(response));
}

export function loadClientes(): Promise<Cliente[]> {
  return fetch(`${API}/clientes`).then((response) => read<Cliente[]>(response));
}

export function saveCliente(input: {
  id?: number;
  name: string;
  price_list_id: number;
  phone_e164?: string;
  phone2_e164?: string;
  endereco?: string;
  localizacao?: string;
  observacao?: string;
  kind?: "pessoa" | "comercio";
  pessoas?: { nome: string; celular: string; papeis: string[] }[];
  desconto_pedido?: number | null;
}): Promise<Cliente> {
  const url = input.id ? `${API}/clientes/${input.id}` : `${API}/clientes`;
  return fetch(url, {
    method: input.id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      price_list_id: input.price_list_id,
      phone_e164: input.phone_e164 ?? null,
      phone2_e164: input.phone2_e164 ?? null,
      endereco: input.endereco ?? null,
      localizacao: input.localizacao ?? null,
      observacao: input.observacao ?? null,
      kind: input.kind ?? "pessoa",
      pessoas: (input.pessoas ?? []).map((pessoa) => ({
        name: pessoa.nome,
        phone_e164: pessoa.celular,
        papeis: pessoa.papeis,
      })),
      desconto_pedido: input.desconto_pedido ?? null,
    }),
  }).then((response) => read<Cliente>(response));
}

const BOT = import.meta.env.VITE_BOT_URL ?? `http://${window.location.hostname || "127.0.0.1"}:8011`;

export function interpretCadastro(input: {
  message: string;
  tela: "clientes" | "precos";
  clientes: { nome: string }[];
  produtos: string[];
  listas: string[];
}): Promise<{ reply: string; acoes: Acao[] }> {
  const url = `${BOT}/chatbot/cadastro/interpret`;
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  }).then(async (response) => {
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = typeof body.detail === "string" ? body.detail : "A IA não respondeu";
      throw new Error(detail);
    }
    return body as { reply: string; acoes: Acao[] };
  });
}

export function saveDesconto(customerId: number, productId: number, price: number): Promise<Cliente> {
  return fetch(`${API}/clientes/${customerId}/descontos/${productId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, price }),
  }).then((response) => read<Cliente>(response));
}

export type ItemSalvo = {
  produto: string;
  qtd: number;
  qtd_entregue: number;
  valor: number;
  total: number;
  desconto?: number;
  desconto_percentual?: number;
};
export type PedidoSalvo = {
  id: string;
  data: string;
  endereco: string;
  desconto: number;
  tabela: string;
  subtotal: number;
  total: number;
  itens: ItemSalvo[];
};
export type ContaCliente = { id: number; nome: string; total: number; pedidos: PedidoSalvo[] };
export type Extrato = { de: string; ate: string; total: number; clientes: ContaCliente[] };

export function salvarBoletas(
  pedidos: {
    id?: string;
    cliente_id?: number;
    data: string;
    endereco: string;
    desconto: number;
    tabela: string;
    itens: {
      produto: string;
      qtd: number;
      qtd_entregue: number;
      valor: number;
      desconto: number;
      desconto_percentual: number;
    }[];
  }[],
): Promise<{ salvos: number; ids: string[] }> {
  return fetch(`${API}/boletas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pedidos }),
  }).then((response) => read(response));
}

export function consultarBoletas(de: string, ate: string, clienteId?: number): Promise<Extrato> {
  const params = new URLSearchParams({ de, ate });
  if (clienteId) params.set("cliente_id", String(clienteId));
  return fetch(`${API}/boletas?${params}`).then((response) => read(response));
}

export function removeDesconto(customerId: number, productId: number): Promise<Cliente> {
  return fetch(`${API}/clientes/${customerId}/descontos/${productId}`, { method: "DELETE" }).then((response) =>
    read<Cliente>(response),
  );
}
