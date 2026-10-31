const API = "http://127.0.0.1:8002/api/v1/cadastro";

function pedir(url: string, init?: RequestInit): Promise<Response> {
  return fetch(url, init).catch((err: unknown) => {
    if (err instanceof TypeError) {
      throw new Error("O servidor não respondeu. A alteração continua na tela. Tente de novo.");
    }
    throw err instanceof Error ? err : new Error("O servidor não respondeu.");
  });
}

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
export type EnderecoCliente = {
  id?: number;
  rotulo: string;
  endereco: string;
  localizacao: string | null;
  padrao: boolean;
};

export type Cliente = {
  id: number;
  name: string;
  phone_e164: string | null;
  phone2_e164: string | null;
  endereco: string | null;
  localizacao: string | null;
  enderecos?: EnderecoCliente[];
  observacao: string | null;
  kind: "pessoa" | "comercio" | "fornecedor";
  tratamento: string | null;
  nome_funil: string | null;
  pessoas: { nome: string; celular: string | null; papeis: string[]; tratamento: string | null }[];
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
      papel?: "fornecedor";
      proprietario?: string;
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
  return pedir(`${API}/tabelas`).then((response) => read<Tabelas>(response));
}

export function saveFormato(productId: number, formato: string): Promise<void> {
  return pedir(`${API}/produtos/${productId}/formato`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ formato }),
  }).then((response) => read(response));
}

export function deleteCliente(customerId: number, modo: "base" | "inativar"): Promise<void> {
  return pedir(`${API}/clientes/${customerId}?modo=${modo}`, { method: "DELETE" }).then((response) => read(response));
}

export function deleteProduto(productId: number): Promise<void> {
  return pedir(`${API}/produtos/${productId}`, { method: "DELETE" }).then((response) => read(response));
}

export function createProduto(name: string, formato: string): Promise<Produto> {
  return pedir(`${API}/produtos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, formato }),
  }).then((response) => read<Produto>(response));
}

export function saveTablePrice(priceListId: number, productId: number, price: number): Promise<void> {
  return pedir(`${API}/tabelas/${priceListId}/produtos/${productId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ price }),
  }).then((response) => read(response));
}

export function loadClientes(): Promise<Cliente[]> {
  return pedir(`${API}/clientes`).then((response) => read<Cliente[]>(response));
}

export type ClienteBusca = { id: number; name: string; detalhe: string };

export function buscarClientes(texto: string): Promise<ClienteBusca[]> {
  const params = new URLSearchParams({ q: texto });
  return pedir(`${API}/clientes/busca?${params}`).then((response) => read<ClienteBusca[]>(response));
}

export function saveCliente(input: {
  id?: number;
  name: string;
  price_list_id: number;
  phone_e164?: string;
  phone2_e164?: string;
  endereco?: string;
  localizacao?: string;
  enderecos?: { rotulo: string; endereco: string; localizacao: string; padrao: boolean }[];
  observacao?: string;
  kind?: "pessoa" | "comercio" | "fornecedor";
  tratamento?: string | null;
  nome_funil?: string | null;
  pessoas?: { nome: string; celular: string; papeis: string[]; tratamento?: string }[];
  desconto_pedido?: number | null;
}): Promise<Cliente> {
  const url = input.id ? `${API}/clientes/${input.id}` : `${API}/clientes`;
  return pedir(url, {
    method: input.id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: input.name,
      price_list_id: input.price_list_id,
      phone_e164: input.phone_e164 ?? null,
      phone2_e164: input.phone2_e164 ?? null,
      endereco: input.endereco ?? null,
      localizacao: input.localizacao ?? null,
      enderecos: input.enderecos ?? [],
      observacao: input.observacao ?? null,
      kind: input.kind ?? "pessoa",
      nickname: input.tratamento ?? null,
      funnel_name: input.nome_funil ?? null,
      pessoas: (input.pessoas ?? []).map((pessoa) => ({
        name: pessoa.nome,
        phone_e164: pessoa.celular,
        papeis: pessoa.papeis,
        nickname: pessoa.tratamento ?? null,
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
  contexto?: string;
}): Promise<{ reply: string; acoes: Acao[] }> {
  const url = `${BOT}/chatbot/cadastro/interpret`;
  return pedir(url, {
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
  return pedir(`${API}/clientes/${customerId}/descontos/${productId}`, {
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
  qtd_reagendada?: number;
  data_reagendada?: string;
  observacao?: string;
  origem_id?: string;
  origem_data?: string;
};
export type PedidoSalvo = {
  id: string;
  data: string;
  endereco: string;
  desconto: number;
  tabela: string;
  tipo?: "venda" | "compra";
  concluido?: boolean;
  pago?: boolean;
  observacao?: string;
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
    tipo?: "venda" | "compra";
    concluir?: boolean;
    desconcluir?: boolean;
    pago?: boolean;
    observacao?: string;
    itens: {
      produto: string;
      qtd: number;
      qtd_entregue: number;
      valor: number;
      desconto: number;
      desconto_percentual: number;
      qtd_reagendada?: number;
      data_reagendada?: string;
      reagenda_conduta?: "somar" | "substituir";
      observacao?: string;
      origem_id?: string;
    }[];
  }[],
): Promise<{ salvos: number; ids: string[]; reagendados: number }> {
  return pedir(`${API}/boletas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pedidos }),
  }).then((response) => read(response));
}

export function excluirBoleta(id: string): Promise<{ excluido: string }> {
  return pedir(`${API}/boletas/${id}`, { method: "DELETE" }).then((response) => read(response));
}

export function consultarBoletas(de: string, ate: string, clienteId?: number): Promise<Extrato> {
  const params = new URLSearchParams({ de, ate });
  if (clienteId) params.set("cliente_id", String(clienteId));
  return pedir(`${API}/boletas?${params}`).then((response) => read(response));
}

export type RotaParada = {
  seq: number;
  cliente: string;
  endereco: string;
  lat: number | null;
  lng: number | null;
  cliente_id: number | null;
  order_id: string | null;
  origem: string;
  aviso: string;
  localizacao?: string;
};

export type RotaOtimizada = {
  partida: {
    rotulo: string;
    endereco: string;
    lat: number | null;
    lng: number | null;
    origem: string;
    localizacao?: string;
  };
  paradas: RotaParada[];
  modo: "osrm" | "tela" | string;
  distancia_m: number | null;
  duracao_s: number | null;
  maps_url: string;
  osrm_ok: boolean;
  avisos: string[];
};

const DELIVERIES = "http://127.0.0.1:8002/api/v1/deliveries";

export function otimizarRota(
  partida: string,
  paradas: {
    cliente: string;
    endereco: string;
    cliente_id?: number;
    order_id?: string;
    localizacao?: string;
  }[],
): Promise<RotaOtimizada> {
  return pedir(`${DELIVERIES}/otimizar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ partida, paradas }),
  }).then((response) => read<RotaOtimizada>(response));
}

export type RotaDoDia = {
  id: number;
  data: string;
  partida: string;
  rota: RotaOtimizada;
};

export function salvarRotaDoDia(dataIso: string, partida: string, rota: RotaOtimizada): Promise<RotaDoDia> {
  return pedir(`${DELIVERIES}/rota-do-dia`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ data: dataIso, partida, rota }),
  }).then((response) => read<RotaDoDia>(response));
}

export function carregarRotaDoDia(dataIso: string): Promise<RotaDoDia | null> {
  return pedir(`${DELIVERIES}/rota-do-dia?data=${encodeURIComponent(dataIso)}`).then(async (response) => {
    if (response.status === 404) return null;
    return read<RotaDoDia>(response);
  });
}

export type MensagemGravada = {
  id: number;
  papel: "voce" | "bot";
  texto: string;
  criada_em: string;
};

export type ConversaGravada = {
  id: number;
  painel: "venda" | "compra";
  iniciada_em: string;
  encerrada_em: string | null;
  mensagens: MensagemGravada[];
};

export function conversaAtual(painel: "venda" | "compra"): Promise<ConversaGravada> {
  return pedir(`${API}/conversas/atual?painel=${painel}`).then((response) => read<ConversaGravada>(response));
}

export function listarConversas(painel: "venda" | "compra"): Promise<ConversaGravada[]> {
  return pedir(`${API}/conversas?painel=${painel}`).then((response) => read<ConversaGravada[]>(response));
}

export function gravarMensagemConversa(
  painel: "venda" | "compra",
  papel: "voce" | "bot",
  texto: string,
): Promise<MensagemGravada> {
  return pedir(`${API}/conversas/mensagens`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ painel, papel, texto }),
  }).then((response) => read<MensagemGravada>(response));
}

export type ItemListaCompra = { produto: string; qtd: number };
export type ListaCompra = {
  id: number;
  periodo: string;
  texto: string;
  criada_em: string;
  itens: ItemListaCompra[];
};

export function carregarListaCompra(periodo: string): Promise<ListaCompra | null> {
  const params = new URLSearchParams({ periodo });
  return pedir(`${API}/listas-compra?${params}`).then(async (response) => {
    if (response.status === 404) return null;
    return read<ListaCompra>(response);
  });
}

export function salvarListaCompra(lista: { periodo: string; texto: string; itens: ItemListaCompra[] }): Promise<ListaCompra> {
  return pedir(`${API}/listas-compra`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(lista),
  }).then((response) => read<ListaCompra>(response));
}

export type PreferenciaOperador = {
  usuario: string;
  tela: "pedidos" | "clientes" | "tabelas" | "contas" | "funil" | "colaboradores" | "contexto";
  chat_aberto: boolean;
  ferramentas_abertas: boolean;
};

export function carregarPreferencia(usuario = "operacao"): Promise<PreferenciaOperador> {
  const params = new URLSearchParams({ usuario });
  return pedir(`${API}/preferencia?${params}`).then((response) => read<PreferenciaOperador>(response));
}

export function salvarPreferencia(pref: PreferenciaOperador): Promise<PreferenciaOperador> {
  return pedir(`${API}/preferencia`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(pref),
  }).then((response) => read<PreferenciaOperador>(response));
}

export function limparConversaPainel(painel: "venda" | "compra"): Promise<ConversaGravada> {
  return pedir(`${API}/conversas/limpar?painel=${painel}`, { method: "POST" }).then((response) =>
    read<ConversaGravada>(response),
  );
}

export function removeDesconto(customerId: number, productId: number): Promise<Cliente> {
  return pedir(`${API}/clientes/${customerId}/descontos/${productId}`, { method: "DELETE" }).then((response) =>
    read<Cliente>(response),
  );
}

export type PapelColaborador =
  | "dono"
  | "funcionario"
  | "entregador"
  | "colheiteiro"
  | "granjeiro"
  | "separador_pedidos"
  | "fornecedor";

export type Colaborador = {
  id: number;
  name: string;
  phone_e164: string;
  roles: PapelColaborador[];
  role: PapelColaborador;
  endereco: string | null;
  localizacao: string | null;
  active: boolean;
  notes: string | null;
};

export type ColaboradorIn = {
  name: string;
  phone_e164: string;
  roles: PapelColaborador[];
  endereco?: string;
  localizacao?: string;
  active: boolean;
  notes?: string;
};

export type GrupoFuncao = {
  role: PapelColaborador;
  pessoas: { id: number; name: string; phone_e164: string; roles: PapelColaborador[] }[];
};

export function loadColaboradores(params?: {
  q?: string;
  role?: PapelColaborador | "";
  ativos?: boolean;
}): Promise<Colaborador[]> {
  const search = new URLSearchParams();
  if (params?.q) search.set("q", params.q);
  if (params?.role) search.set("role", params.role);
  if (params?.ativos !== undefined) search.set("ativos", String(params.ativos));
  const qs = search.toString();
  return pedir(`${API}/colaboradores${qs ? `?${qs}` : ""}`).then((response) =>
    read<Colaborador[]>(response),
  );
}

export function loadColaboradoresPorFuncao(): Promise<{ funcoes: GrupoFuncao[] }> {
  return pedir(`${API}/colaboradores/por-funcao`).then((response) =>
    read<{ funcoes: GrupoFuncao[] }>(response),
  );
}

export function saveColaborador(body: ColaboradorIn, id?: number): Promise<Colaborador> {
  const url = id ? `${API}/colaboradores/${id}` : `${API}/colaboradores`;
  return pedir(url, {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((response) => read<Colaborador>(response));
}

export function inativarColaborador(id: number): Promise<{ ok: boolean }> {
  return pedir(`${API}/colaboradores/${id}/inativar`, { method: "POST" }).then((response) =>
    read<{ ok: boolean }>(response),
  );
}

export function excluirColaborador(id: number): Promise<{ ok: boolean }> {
  return pedir(`${API}/colaboradores/${id}`, { method: "DELETE" }).then((response) =>
    read<{ ok: boolean }>(response),
  );
}

export type EnvioListaWhatsApp = {
  text: string;
  colaborador_ids: number[];
};

export type ResultadoEnvioListas = {
  success: boolean;
  enviados: number;
  falhas: number;
  resultados: {
    lista: string;
    skipped?: boolean;
    reason?: string;
    enviados?: number;
    falhas?: number;
    envios?: { name?: string; success?: boolean; error?: string }[];
  }[];
};

export function avisarAdministrador(texto: string): Promise<{ enviados: number }> {
  return pedir(`${API}/whatsapp/avisar-administrador`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
  }).then((response) => read<{ enviados: number }>(response));
}

export function enviarListasWhatsApp(body: {
  colheita?: EnvioListaWhatsApp;
  pedidos?: EnvioListaWhatsApp;
  compras?: EnvioListaWhatsApp;
  rota?: EnvioListaWhatsApp;
}): Promise<ResultadoEnvioListas> {
  return pedir(`${API}/whatsapp/enviar-listas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then((response) => read<ResultadoEnvioListas>(response));
}
