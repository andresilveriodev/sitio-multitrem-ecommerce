import type { Cliente, RotaOtimizada, RotaParada } from "./cadastroApi";
import type { Order } from "./types";

export type ParadaTela = {
  cliente: string;
  endereco: string;
  cliente_id?: number;
  order_id?: string;
  localizacao?: string;
};

function fold(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function clienteDaParada(order: Order, clientes: Cliente[]): Cliente | undefined {
  if (order.clienteId) {
    const porId = clientes.find((item) => item.id === order.clienteId);
    if (porId) return porId;
  }
  const nome = fold(order.cliente);
  if (!nome) return undefined;
  return clientes.find((item) => fold(item.name) === nome);
}

/** Localização do cadastro que bate com o endereço da boleta (cliente pode ter vários). */
export function localizacaoDoEndereco(cliente: Cliente | undefined, endereco: string): string {
  if (!cliente) return "";
  const lista = cliente.enderecos ?? [];
  const alvo = fold(endereco);
  if (lista.length && alvo) {
    const batendo = lista.find((item) => {
      const rua = fold(item.endereco || "");
      return rua && (rua === alvo || alvo.includes(rua) || rua.includes(alvo));
    });
    if (batendo?.localizacao?.trim()) return batendo.localizacao.trim();
  }
  const padrao = lista.find((item) => item.padrao) || lista[0];
  return (padrao?.localizacao || cliente.localizacao || "").trim();
}

/** Uma parada por cliente+endereço, na ordem da tela, com link do cadastro. */
export function montarParadasDaTela(orders: Order[], clientes: Cliente[] = []): ParadaTela[] {
  const vistos = new Set<string>();
  const paradas: ParadaTela[] = [];
  for (const order of orders) {
    const cliente = order.cliente.trim();
    const endereco = order.endereco.trim();
    if (!cliente && !endereco) continue;
    const ficha = clienteDaParada(order, clientes);
    const chave = `${order.clienteId ?? ficha?.id ?? cliente}|${endereco.toLowerCase()}`;
    if (vistos.has(chave)) continue;
    vistos.add(chave);
    const end = endereco || ficha?.endereco || "";
    const localizacao = localizacaoDoEndereco(ficha, end);
    paradas.push({
      cliente: cliente || ficha?.name || "Cliente",
      endereco: end,
      cliente_id: order.clienteId ?? ficha?.id,
      order_id: order.id,
      localizacao: localizacao || undefined,
    });
  }
  return paradas;
}

export function formatarKm(metros: number | null | undefined): string {
  if (metros == null || Number.isNaN(metros)) return "—";
  if (metros < 1000) return `${Math.round(metros)} m`;
  return `${(metros / 1000).toFixed(1).replace(".", ",")} km`;
}

export function formatarDuracao(segundos: number | null | undefined): string {
  if (segundos == null || Number.isNaN(segundos)) return "—";
  const total = Math.round(segundos / 60);
  if (total < 60) return `${total} min`;
  const h = Math.floor(total / 60);
  const m = total % 60;
  return m ? `${h} h ${m} min` : `${h} h`;
}

function refMaps(ponto: {
  lat?: number | null;
  lng?: number | null;
  localizacao?: string | null;
  endereco?: string;
  cliente?: string;
  rotulo?: string;
}): string {
  if (ponto.lat != null && ponto.lng != null) return `${ponto.lat},${ponto.lng}`;
  const loc = (ponto.localizacao || "").trim();
  if (loc) return loc;
  return (ponto.endereco || ponto.cliente || ponto.rotulo || "").trim();
}

/** Monta o link do Google Maps priorizando coords / localização do cadastro. */
export function mapsUrlDaRota(
  partida: RotaOtimizada["partida"],
  paradas: RotaParada[],
): string {
  const pontos = [
    {
      lat: partida.lat,
      lng: partida.lng,
      localizacao: partida.localizacao,
      endereco: partida.endereco,
      rotulo: partida.rotulo,
    },
    ...paradas,
  ];
  const refs = pontos.map(refMaps).filter(Boolean);
  if (refs.length < 2) return refs[0]?.startsWith("http") ? refs[0] : "";

  const comCoord = pontos.every((p) => p.lat != null && p.lng != null);
  const origem = refMaps(pontos[0]);
  const destino = refMaps(pontos[pontos.length - 1]);
  const meios = pontos.slice(1, -1).map(refMaps).filter(Boolean);
  const params = new URLSearchParams({
    api: "1",
    origin: origem,
    destination: destino,
    travelmode: "driving",
  });
  if (meios.length) params.set("waypoints", meios.join("|"));
  if (comCoord || pontos.some((p) => (p.localizacao || "").trim())) {
    return `https://www.google.com/maps/dir/?${params.toString()}`;
  }
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function inverterParadas(paradas: RotaParada[]): RotaParada[] {
  return [...paradas].reverse().map((parada, index) => ({ ...parada, seq: index + 1 }));
}

/** Move a parada de `de` para `para` e renumerar seq. */
export function reordenarParadas(paradas: RotaParada[], de: number, para: number): RotaParada[] {
  if (de === para || de < 0 || para < 0 || de >= paradas.length || para >= paradas.length) {
    return paradas;
  }
  const proxima = [...paradas];
  const [item] = proxima.splice(de, 1);
  if (!item) return paradas;
  proxima.splice(para, 0, item);
  return proxima.map((parada, index) => ({ ...parada, seq: index + 1 }));
}

function chaveParadaRef(parada: {
  cliente_id?: number | null;
  order_id?: string | null;
  cliente: string;
  endereco: string;
}): string {
  return `${parada.cliente_id ?? parada.order_id ?? fold(parada.cliente)}|${fold(parada.endereco)}`;
}

/**
 * Mantém a ordem da rota para quem já estava; remove quem saiu da tela;
 * acrescenta no fim quem entrou depois (ex.: Emerson incluído após montar).
 */
export function sincronizarParadasComTela(rotaParadas: RotaParada[], tela: ParadaTela[]): {
  paradas: RotaParada[];
  novos: number;
  removidos: number;
} {
  const porChave = new Map(tela.map((parada) => [chaveParadaRef(parada), parada]));
  const usadas = new Set<string>();
  const mantidas: RotaParada[] = [];
  for (const atual of rotaParadas) {
    const chave = chaveParadaRef(atual);
    const naTela = porChave.get(chave);
    if (!naTela) continue;
    usadas.add(chave);
    mantidas.push({
      ...atual,
      cliente: naTela.cliente || atual.cliente,
      endereco: naTela.endereco || atual.endereco,
      cliente_id: naTela.cliente_id ?? atual.cliente_id,
      order_id: naTela.order_id ?? atual.order_id,
      localizacao: naTela.localizacao || atual.localizacao || "",
    });
  }
  const extras: RotaParada[] = [];
  for (const [chave, naTela] of porChave) {
    if (usadas.has(chave)) continue;
    extras.push({
      seq: 0,
      cliente: naTela.cliente,
      endereco: naTela.endereco,
      lat: null,
      lng: null,
      cliente_id: naTela.cliente_id ?? null,
      order_id: naTela.order_id ?? null,
      origem: naTela.localizacao ? "localizacao" : "",
      aviso: "",
      localizacao: naTela.localizacao || "",
    });
  }
  const juntas = [...mantidas, ...extras].map((parada, index) => ({ ...parada, seq: index + 1 }));
  return {
    paradas: juntas,
    novos: extras.length,
    removidos: rotaParadas.length - mantidas.length,
  };
}

/** Ordem da rota atual + paradas novas da tela no fim (para Atualizar sem perder quem entrou). */
export function entradaComOrdemManual(rotaParadas: RotaParada[] | undefined, tela: ParadaTela[]): ParadaTela[] {
  if (!rotaParadas?.length) return tela;
  const { paradas } = sincronizarParadasComTela(rotaParadas, tela);
  return paradas.map((parada) => ({
    cliente: parada.cliente,
    endereco: parada.endereco,
    cliente_id: parada.cliente_id ?? undefined,
    order_id: parada.order_id ?? undefined,
    localizacao: parada.localizacao || undefined,
  }));
}

export function linkParadaMaps(parada: RotaParada): string {
  if (parada.lat != null && parada.lng != null) {
    return `https://www.google.com/maps?q=${parada.lat},${parada.lng}`;
  }
  const loc = (parada.localizacao || "").trim();
  if (loc) return loc.startsWith("http") ? loc : `https://www.google.com/maps?q=${encodeURIComponent(loc)}`;
  const end = (parada.endereco || "").trim();
  if (!end) return "";
  return `https://www.google.com/maps?q=${encodeURIComponent(end)}`;
}

const SEPARADOR_WHATSAPP = "#".repeat(28);

/** Texto para colar no WhatsApp: link, nome curto com 👆 e a linha de #. */
export function textoMensagemLocalizacao(paradas: RotaParada[]): string {
  const blocos: string[] = [];
  for (const parada of paradas) {
    const link = linkParadaMaps(parada);
    if (!link) continue;
    const nome = (parada.cliente.trim().split(/\s+/)[0] || parada.cliente.trim() || "Cliente").trim();
    blocos.push(`${link}\n${nome} 👆\n${SEPARADOR_WHATSAPP}`);
  }
  return blocos.join("\n");
}

/** Lista numerada da rota (cliente + endereço) para copiar. */
export function textoListaRota(
  paradas: RotaParada[],
  partida?: { endereco?: string } | null,
): string {
  if (!paradas.length) return "";
  const linhas = ["Rota de entrega"];
  if (partida?.endereco?.trim()) linhas.push(`0. Partida — ${partida.endereco.trim()}`);
  for (const parada of paradas) {
    const quem = parada.cliente.trim() || "Cliente";
    const onde = parada.endereco.trim();
    linhas.push(onde ? `${parada.seq}. ${quem} — ${onde}` : `${parada.seq}. ${quem}`);
  }
  return linhas.join("\n");
}
