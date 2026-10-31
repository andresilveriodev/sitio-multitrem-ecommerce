import { useEffect, useMemo, useState, type DragEvent } from "react";
import {
  carregarRotaDoDia,
  otimizarRota,
  salvarRotaDoDia,
  type Cliente,
  type RotaOtimizada,
} from "./cadastroApi";
import {
  formatarDuracao,
  formatarKm,
  inverterParadas,
  linkParadaMaps,
  entradaComOrdemManual,
  mapsUrlDaRota,
  montarParadasDaTela,
  reordenarParadas,
  sincronizarParadasComTela,
  textoListaRota,
  textoMensagemLocalizacao,
} from "./rotaMath";
import type { Order } from "./types";

const CHAVE_PARTIDA = "sitio-rota-partida";
const PARTIDA_PADRAO = "Setor Urias Magalhães, Goiânia, GO";

type Props = {
  orders: Order[];
  clientes: Cliente[];
  onFechar: () => void;
  onAviso: (texto: string) => void;
};

function isoHoje(): string {
  const hoje = new Date();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  const dia = String(hoje.getDate()).padStart(2, "0");
  return `${hoje.getFullYear()}-${mes}-${dia}`;
}

function isoDaDataNota(data: string): string {
  const match = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(data.trim());
  if (!match) return "";
  const dia = match[1].padStart(2, "0");
  const mes = match[2].padStart(2, "0");
  let ano = match[3] ? Number(match[3]) : new Date().getFullYear();
  if (ano < 100) ano += 2000;
  return `${ano}-${mes}-${dia}`;
}

/** Data mais comum nas boletas da tela; senão hoje. */
function dataIsoDaTela(orders: Order[]): string {
  const contagem = new Map<string, number>();
  for (const order of orders) {
    if (order.tipo === "compra") continue;
    const iso = isoDaDataNota(order.data);
    if (!iso) continue;
    contagem.set(iso, (contagem.get(iso) || 0) + 1);
  }
  let melhor = "";
  let votos = 0;
  for (const [iso, n] of contagem) {
    if (n > votos) {
      melhor = iso;
      votos = n;
    }
  }
  return melhor || isoHoje();
}

export function ListaRota({ orders, clientes, onFechar, onAviso }: Props) {
  const [partida, setPartida] = useState(() => localStorage.getItem(CHAVE_PARTIDA) || PARTIDA_PADRAO);
  const [carregando, setCarregando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [rota, setRota] = useState<RotaOtimizada | null>(null);
  const [rotaId, setRotaId] = useState<number | null>(null);
  const [invertida, setInvertida] = useState(false);
  const [modificada, setModificada] = useState(false);
  const [arrastoDe, setArrastoDe] = useState<number | null>(null);
  const [arrastoSobre, setArrastoSobre] = useState<number | null>(null);
  const [copiouMsg, setCopiouMsg] = useState(false);
  const dataIso = useMemo(() => dataIsoDaTela(orders), [orders]);
  const paradasTela = montarParadasDaTela(orders, clientes);
  const paradasPedido = invertida ? [...paradasTela].reverse() : paradasTela;

  function aplicarOrdem(paradas: RotaOtimizada["paradas"]) {
    setModificada(true);
    setRota((atual) => {
      if (!atual) return atual;
      return {
        ...atual,
        paradas,
        modo: "tela",
        distancia_m: null,
        duracao_s: null,
        maps_url: mapsUrlDaRota(atual.partida, paradas),
      };
    });
  }

  useEffect(() => {
    localStorage.setItem(CHAVE_PARTIDA, partida);
  }, [partida]);

  useEffect(() => {
    let ativo = true;
    void (async () => {
      try {
        const salva = await carregarRotaDoDia(dataIso);
        if (!ativo || !salva?.rota?.paradas?.length) return;
        setRota(salva.rota);
        setRotaId(salva.id);
        if (salva.partida.trim()) setPartida(salva.partida);
        setModificada(false);
      } catch {
        /* sem rota salva ou API fora */
      }
    })();
    return () => {
      ativo = false;
    };
  }, [dataIso]);

  // Pedido novo na tela (ex.: Emerson) entra no fim da rota já montada.
  useEffect(() => {
    if (!rota?.paradas.length || !paradasTela.length) return;
    const sync = sincronizarParadasComTela(rota.paradas, paradasTela);
    if (!sync.novos && !sync.removidos) return;
    if (
      sync.paradas.length === rota.paradas.length &&
      sync.paradas.every((parada, i) => parada.cliente === rota.paradas[i]?.cliente && parada.endereco === rota.paradas[i]?.endereco)
    ) {
      return;
    }
    setModificada(true);
    setRota((atual) => {
      if (!atual) return atual;
      return {
        ...atual,
        paradas: sync.paradas,
        modo: "tela",
        distancia_m: null,
        duracao_s: null,
        maps_url: mapsUrlDaRota(atual.partida, sync.paradas),
      };
    });
    if (sync.novos) {
      onAviso(
        sync.novos === 1
          ? "Incluí 1 parada nova no fim da rota. Salve ou atualize."
          : `Incluí ${sync.novos} paradas novas no fim da rota. Salve ou atualize.`,
      );
    }
  }, [paradasTela, rota, onAviso]);

  async function gerar() {
    if (!paradasPedido.length) {
      onAviso("Não há entrega na tela para montar rota.");
      return;
    }
    setCarregando(true);
    try {
      // Sempre inclui quem está na tela; se a rota foi reordenada à mão, preserva essa ordem.
      const entrada = modificada ? entradaComOrdemManual(rota?.paradas, paradasPedido) : paradasPedido;
      const resultado = await otimizarRota(partida, entrada);
      const comLink = entrada.filter((p) => p.localizacao).length;
      let paradas = resultado.paradas.map((parada) => {
        const origem =
          entrada.find((item) => item.cliente_id && item.cliente_id === parada.cliente_id) ||
          entrada.find(
            (item) =>
              item.cliente.trim().toLocaleLowerCase("pt-BR") === parada.cliente.trim().toLocaleLowerCase("pt-BR"),
          );
        return {
          ...parada,
          localizacao: parada.localizacao || origem?.localizacao || "",
        };
      });
      if (modificada && rota?.paradas.length) {
        const sync = sincronizarParadasComTela(
          rota.paradas,
          paradas.map((p) => ({
            cliente: p.cliente,
            endereco: p.endereco,
            cliente_id: p.cliente_id ?? undefined,
            order_id: p.order_id ?? undefined,
            localizacao: p.localizacao,
          })),
        );
        const porChave = new Map(
          paradas.map((p) => [`${p.cliente_id ?? p.order_id ?? p.cliente}|${p.endereco}`.toLocaleLowerCase("pt-BR"), p]),
        );
        const reordenadas = sync.paradas
          .map((p) => porChave.get(`${p.cliente_id ?? p.order_id ?? p.cliente}|${p.endereco}`.toLocaleLowerCase("pt-BR")))
          .filter(Boolean) as typeof paradas;
        if (reordenadas.length === paradas.length) {
          paradas = reordenadas.map((parada, index) => ({ ...parada, seq: index + 1 }));
        }
      }
      const maps_url = mapsUrlDaRota(resultado.partida, paradas) || resultado.maps_url;
      setRota({
        ...resultado,
        paradas,
        maps_url,
        modo: modificada ? "tela" : resultado.modo,
        distancia_m: modificada ? null : resultado.distancia_m,
        duracao_s: modificada ? null : resultado.duracao_s,
      });
      setModificada(false);
      const modo = modificada
        ? "ordem manual (com quem estava na tela)"
        : resultado.modo === "osrm"
          ? "otimizada pelo OSRM"
          : invertida
            ? "ordem invertida da tela"
            : "na ordem da tela";
      onAviso(`Rota com ${paradas.length} paradas (${modo}).`);
      if (comLink) onAviso(`Usei localização do cadastro em ${comLink} ${comLink === 1 ? "cliente" : "clientes"}.`);
      const semLink = paradas.filter((p) => !p.localizacao && p.lat == null).length;
      if (semLink) onAviso(`${semLink} ${semLink === 1 ? "cliente está" : "clientes estão"} sem link de localização no cadastro.`);
      for (const aviso of resultado.avisos.slice(0, 3)) onAviso(aviso);
    } catch (err) {
      onAviso(err instanceof Error ? err.message : "Não consegui montar a rota.");
    } finally {
      setCarregando(false);
    }
  }

  async function salvar() {
    if (!rota?.paradas.length) {
      onAviso("Monte a rota antes de salvar.");
      return;
    }
    setSalvando(true);
    try {
      const salva = await salvarRotaDoDia(dataIso, partida, rota);
      setRotaId(salva.id);
      setModificada(false);
      onAviso(`Rota salva no banco (${salva.rota.paradas.length} paradas · ${dataIso.split("-").reverse().join("/")}).`);
    } catch (err) {
      onAviso(err instanceof Error ? err.message : "Não consegui salvar a rota.");
    } finally {
      setSalvando(false);
    }
  }

  function inverter() {
    setInvertida((atual) => !atual);
    setRota((atual) => {
      if (!atual) return atual;
      setModificada(true);
      const paradas = inverterParadas(atual.paradas);
      return {
        ...atual,
        paradas,
        modo: "tela",
        distancia_m: null,
        duracao_s: null,
        maps_url: mapsUrlDaRota(atual.partida, paradas),
      };
    });
    onAviso(invertida ? "Ordem da tela restaurada." : "Ordem das entregas invertida.");
  }

  function aoArrastarInicio(event: DragEvent<HTMLTableRowElement>, index: number) {
    setArrastoDe(index);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(index));
  }

  function aoArrastarSobre(event: DragEvent<HTMLTableRowElement>, index: number) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    if (arrastoSobre !== index) setArrastoSobre(index);
  }

  function aoSoltar(event: DragEvent<HTMLTableRowElement>, para: number) {
    event.preventDefault();
    const bruto = event.dataTransfer.getData("text/plain");
    const de = Number.isFinite(Number(bruto)) ? Number(bruto) : arrastoDe;
    setArrastoDe(null);
    setArrastoSobre(null);
    if (de == null || !rota || de === para) return;
    aplicarOrdem(reordenarParadas(rota.paradas, de, para));
    onAviso("Ordem da rota ajustada. Salve no banco para guardar.");
  }

  function aoArrastarFim() {
    setArrastoDe(null);
    setArrastoSobre(null);
  }

  function imprimir() {
    document.body.classList.add("imprimindo-rota");
    const limpar = () => {
      document.body.classList.remove("imprimindo-rota");
      window.removeEventListener("afterprint", limpar);
    };
    window.addEventListener("afterprint", limpar);
    window.print();
    setTimeout(limpar, 1000);
  }

  const paradas = rota?.paradas ?? [];
  const mapsUrl = rota ? rota.maps_url || mapsUrlDaRota(rota.partida, rota.paradas) : "";
  const mensagem = useMemo(() => textoMensagemLocalizacao(paradas), [paradas]);
  const listaTexto = useMemo(() => textoListaRota(paradas, rota?.partida), [paradas, rota?.partida]);

  async function copiarTexto(texto: string, ok: string, vazio: string) {
    if (!texto) {
      onAviso(vazio);
      return;
    }
    try {
      await navigator.clipboard.writeText(texto);
      onAviso(ok);
    } catch {
      onAviso("Não consegui copiar. Selecione o texto e copie à mão.");
    }
  }

  async function copiarMensagem() {
    await copiarTexto(mensagem, "Mensagem copiada. Pode colar no WhatsApp.", "Monte a rota e cadastre o link de localização do cliente.");
    if (mensagem) {
      setCopiouMsg(true);
      window.setTimeout(() => setCopiouMsg(false), 1200);
    }
  }

  async function copiarLista() {
    await copiarTexto(listaTexto, "Lista da rota copiada.", "Monte a rota antes de copiar a lista.");
  }

  return (
    <section className="lista-colheita lista-rota">
      <div className="lista-colheita-acoes no-print">
        <h2>Rota de entrega</h2>
        <span className="lista-colheita-btns">
          <button type="button" className="primary" onClick={() => void gerar()} disabled={carregando || !paradasPedido.length}>
            {carregando ? "Montando…" : rota ? "Atualizar rota" : "Montar rota"}
          </button>
          <button
            type="button"
            className={modificada ? "ligado" : undefined}
            onClick={() => void salvar()}
            disabled={salvando || !rota?.paradas.length}
            title="Grava a ordem atual no banco de dados"
          >
            {salvando ? "Salvando…" : rotaId && !modificada ? "Rota salva" : "Salvar rota"}
          </button>
          <button
            type="button"
            className={invertida ? "ligado" : undefined}
            onClick={inverter}
            disabled={!paradasTela.length}
            title="Inverte a ordem das entregas (primeiro vira último)"
          >
            {invertida ? "Ordem invertida" : "Inverter ordem"}
          </button>
          <button type="button" onClick={imprimir} disabled={!paradas.length}>
            Imprimir
          </button>
          <button type="button" onClick={() => void copiarLista()} disabled={!listaTexto} title="Copia a lista numerada da rota">
            Copiar lista
          </button>
          <button type="button" onClick={() => void copiarMensagem()} disabled={!mensagem}>
            Copiar mensagem
          </button>
          {mapsUrl ? (
            <a className="botao-link" href={mapsUrl} target="_blank" rel="noreferrer">
              Abrir no Maps
            </a>
          ) : null}
          <button type="button" onClick={onFechar}>
            Fechar
          </button>
        </span>
      </div>
      <div className="lista-colheita-folha">
        <h1>Rota de entrega</h1>
        <label className="rota-partida no-print">
          Partida
          <input
            type="text"
            value={partida}
            onChange={(event) => setPartida(event.target.value)}
            placeholder={PARTIDA_PADRAO}
          />
        </label>
        <p className="lista-colheita-meta">
          {paradasTela.length} {paradasTela.length === 1 ? "parada" : "paradas"} na tela
          {invertida ? " · invertida" : ""}
          {modificada ? " · modificada" : rotaId ? " · salva no banco" : ""}
          {rota
            ? ` · ${rota.modo === "osrm" ? "otimizada" : "ordem da tela"} · ${formatarKm(rota.distancia_m)} · ${formatarDuracao(rota.duracao_s)} · arraste as linhas para reordenar`
            : " · clique em Montar rota"}
        </p>
        {rota?.partida ? (
          <p className="rota-origem">
            <strong>0.</strong> Partida — {rota.partida.endereco}
            {rota.partida.lat != null ? ` (${rota.partida.lat.toFixed(5)}, ${rota.partida.lng?.toFixed(5)})` : ""}
          </p>
        ) : null}
        {!paradasTela.length ? (
          <p className="empty">Não há pedido na tela.</p>
        ) : !rota ? (
          <p className="empty">Informe a partida e monte a rota.</p>
        ) : paradas.length === 0 ? (
          <p className="empty">Nenhuma parada montada.</p>
        ) : (
          <table className="rota-tabela">
            <thead>
              <tr>
                <th className="num no-print" aria-label="Arrastar" />
                <th className="num">#</th>
                <th>Cliente</th>
                <th>Endereço</th>
                <th className="no-print">Maps</th>
              </tr>
            </thead>
            <tbody>
              {paradas.map((parada, index) => {
                const link = linkParadaMaps(parada);
                const classes = [
                  "rota-linha",
                  arrastoDe === index ? "arrastando" : "",
                  arrastoSobre === index && arrastoDe !== index ? "alvo" : "",
                ]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <tr
                    key={`${parada.cliente_id ?? parada.cliente}-${parada.order_id ?? index}`}
                    className={classes}
                    draggable
                    onDragStart={(event) => aoArrastarInicio(event, index)}
                    onDragOver={(event) => aoArrastarSobre(event, index)}
                    onDrop={(event) => aoSoltar(event, index)}
                    onDragEnd={aoArrastarFim}
                  >
                    <td className="rota-pega no-print" title="Arraste para mudar a ordem" aria-hidden="true">
                      ⋮⋮
                    </td>
                    <td className="num">{parada.seq}</td>
                    <td>
                      {parada.cliente}
                      {parada.aviso ? <div className="rota-aviso">{parada.aviso}</div> : null}
                      {parada.localizacao || parada.origem === "localizacao" || parada.origem === "cadastro" ? (
                        <div className="rota-ok no-print">Localização do cadastro</div>
                      ) : (
                        <div className="rota-aviso no-print">Sem link de localização no cadastro</div>
                      )}
                    </td>
                    <td>{parada.endereco || "—"}</td>
                    <td className="no-print">
                      {link ? (
                        <a href={link} target="_blank" rel="noreferrer">
                          Abrir
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
        {rota && mensagem ? (
          <div className="lista-compra-texto no-print">
            <div className="lista-compra-cabeca">
              <p>Mensagem para o WhatsApp</p>
              <button
                type="button"
                className={copiouMsg ? "copiar-lista ok" : "copiar-lista"}
                aria-label={copiouMsg ? "Mensagem copiada" : "Copiar mensagem"}
                title={copiouMsg ? "Copiado" : "Copiar mensagem"}
                disabled={!mensagem}
                onClick={() => void copiarMensagem()}
              >
                {copiouMsg ? (
                  "✓"
                ) : (
                  <svg viewBox="0 0 16 16" aria-hidden="true">
                    <rect x="5" y="5" width="8" height="8" fill="none" stroke="currentColor" strokeWidth="1.4" />
                    <path d="M3 11V3h8" fill="none" stroke="currentColor" strokeWidth="1.4" />
                  </svg>
                )}
              </button>
            </div>
            <textarea readOnly aria-label="Mensagem das localizações" value={mensagem} />
            <p className="empty">Cada bloco é o link do Maps, o nome e a linha de #.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
