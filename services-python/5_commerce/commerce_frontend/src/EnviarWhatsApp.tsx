import { useEffect, useMemo, useState } from "react";
import {
  carregarListaCompra,
  carregarRotaDoDia,
  enviarListasWhatsApp,
  loadColaboradores,
  type Cliente,
  type Colaborador,
  type PapelColaborador,
  type RotaParada,
} from "./cadastroApi";
import { montarListaColheita, textoListaColheita } from "./colheitaMath";
import { montarParadasDaTela, textoMensagemLocalizacao } from "./rotaMath";
import type { Order } from "./types";
import {
  dataPrincipalBoletas,
  periodoDasBoletas,
  textoListaPedidos,
} from "./whatsappListas";

type Props = {
  orders: Order[];
  clientes?: Cliente[];
  onFechar: () => void;
  onAviso?: (texto: string) => void;
};

function paradasDaTela(orders: Order[], clientes: Cliente[]): RotaParada[] {
  const vendas = orders.filter((o) => o.tipo !== "compra");
  return montarParadasDaTela(vendas, clientes).map((p, i) => ({
    seq: i + 1,
    cliente: p.cliente,
    endereco: p.endereco,
    lat: null,
    lng: null,
    cliente_id: p.cliente_id ?? null,
    order_id: p.order_id ?? null,
    origem: "tela",
    aviso: "",
    localizacao: p.localizacao,
  }));
}

function textoRotaDaTela(orders: Order[], clientes: Cliente[]): string {
  return textoMensagemLocalizacao(paradasDaTela(orders, clientes));
}

function showPhone(value: string): string {
  const digits = value.replace(/\D/g, "");
  const local = digits.startsWith("55") && digits.length > 11 ? digits.slice(2) : digits;
  if (local.length === 11) return `${local.slice(0, 2)} ${local.slice(2, 7)}-${local.slice(7)}`;
  if (local.length === 10) return `${local.slice(0, 2)} ${local.slice(2, 6)}-${local.slice(6)}`;
  return value;
}

function rolesDe(pessoa: Colaborador): PapelColaborador[] {
  return pessoa.roles?.length ? pessoa.roles : pessoa.role ? [pessoa.role] : [];
}

function temPapel(pessoa: Colaborador, papeis: PapelColaborador[]): boolean {
  const roles = rolesDe(pessoa);
  return papeis.some((papel) => roles.includes(papel));
}

function unicosPorId(lista: Colaborador[]): Colaborador[] {
  const vistos = new Set<number>();
  const saida: Colaborador[] = [];
  for (const pessoa of lista) {
    if (vistos.has(pessoa.id)) continue;
    vistos.add(pessoa.id);
    saida.push(pessoa);
  }
  return saida;
}

function nomeCurto(valor: string): string {
  return valor
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}

function SeletorPessoas({
  titulo,
  padrao,
  catalogo,
  selecionados,
  onChange,
  aviso,
  preview,
  enviando,
  onEnviar,
}: {
  titulo: string;
  padrao: Colaborador[];
  catalogo: Colaborador[];
  selecionados: number[];
  onChange: (ids: number[]) => void;
  aviso?: string;
  preview: string;
  enviando: boolean;
  onEnviar: () => void;
}) {
  const [extras, setExtras] = useState<Colaborador[]>([]);
  const [busca, setBusca] = useState("");

  const listados = useMemo(
    () => unicosPorId([...padrao, ...extras]),
    [padrao, extras],
  );
  const idsListados = useMemo(() => new Set(listados.map((p) => p.id)), [listados]);

  const sugestoes = useMemo(() => {
    const q = nomeCurto(busca);
    if (q.length < 2) return [];
    return catalogo
      .filter((p) => p.active && !idsListados.has(p.id) && nomeCurto(p.name).includes(q))
      .slice(0, 8);
  }, [busca, catalogo, idsListados]);

  function alternar(id: number) {
    if (selecionados.includes(id)) onChange(selecionados.filter((x) => x !== id));
    else onChange([...selecionados, id]);
  }

  function incluir(pessoa: Colaborador) {
    setExtras((atual) => (atual.some((p) => p.id === pessoa.id) ? atual : [...atual, pessoa]));
    if (!selecionados.includes(pessoa.id)) onChange([...selecionados, pessoa.id]);
    setBusca("");
  }

  const podeEnviar = Boolean(preview.trim()) && selecionados.length > 0 && !enviando;
  const todosMarcados =
    listados.length > 0 && listados.every((p) => selecionados.includes(p.id));

  return (
    <section className="wa-bloco">
      <header>
        <strong>{titulo}</strong>
        {listados.length > 0 ? (
          <button
            type="button"
            className="wa-link"
            onClick={() =>
              onChange(todosMarcados ? [] : listados.map((p) => p.id))
            }
          >
            {todosMarcados ? "Limpar" : "Todos"}
          </button>
        ) : null}
      </header>
      {aviso ? <p className="wa-aviso">{aviso}</p> : null}
      {!listados.length ? (
        <p className="wa-vazio">Ninguém nesta função. Pesquise abaixo para incluir.</p>
      ) : (
        <ul className="wa-pessoas">
          {listados.map((pessoa) => {
            const extra = !padrao.some((p) => p.id === pessoa.id);
            return (
              <li key={pessoa.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={selecionados.includes(pessoa.id)}
                    onChange={() => alternar(pessoa.id)}
                    disabled={!preview}
                  />{" "}
                  {pessoa.name}
                  {extra ? <em className="wa-extra">extra</em> : null}
                  <span>{showPhone(pessoa.phone_e164)}</span>
                </label>
              </li>
            );
          })}
        </ul>
      )}
      <div className="wa-busca">
        <input
          type="search"
          value={busca}
          onChange={(event) => setBusca(event.target.value)}
          placeholder="Incluir outro colaborador…"
          aria-label={`Pesquisar colaborador em ${titulo}`}
        />
        {sugestoes.length > 0 ? (
          <ul className="wa-sugestoes">
            {sugestoes.map((pessoa) => (
              <li key={pessoa.id}>
                <button type="button" onClick={() => incluir(pessoa)}>
                  {pessoa.name}
                  <span>{showPhone(pessoa.phone_e164)}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <pre className="wa-preview">{preview || "(sem texto para enviar)"}</pre>
      <button
        type="button"
        className="wa-enviar-um"
        disabled={!podeEnviar}
        onClick={onEnviar}
      >
        Enviar
      </button>
    </section>
  );
}

export function EnviarWhatsApp({ orders, clientes = [], onFechar, onAviso }: Props) {
  const vendas = useMemo(() => orders.filter((o) => o.tipo !== "compra"), [orders]);
  const datas = useMemo(
    () => [...new Set(vendas.map((o) => o.data.trim()).filter(Boolean))],
    [vendas],
  );
  const textoColheita = useMemo(
    () => textoListaColheita(montarListaColheita(vendas), datas),
    [vendas, datas],
  );
  const textoPedidos = useMemo(() => textoListaPedidos(vendas), [vendas]);
  const periodo = useMemo(() => periodoDasBoletas(vendas), [vendas]);
  const dataRota = useMemo(() => dataPrincipalBoletas(vendas), [vendas]);
  const rotaFallback = useMemo(
    () => textoRotaDaTela(orders, clientes),
    [orders, clientes],
  );

  const [catalogo, setCatalogo] = useState<Colaborador[]>([]);
  const [idsColheita, setIdsColheita] = useState<number[]>([]);
  const [idsPedidos, setIdsPedidos] = useState<number[]>([]);
  const [idsCompras, setIdsCompras] = useState<number[]>([]);
  const [idsRota, setIdsRota] = useState<number[]>([]);
  const [textoCompras, setTextoCompras] = useState("");
  const [textoRota, setTextoRota] = useState("");
  const [avisoCompras, setAvisoCompras] = useState("");
  const [avisoRota, setAvisoRota] = useState("");
  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [status, setStatus] = useState("");

  const colheiteiros = useMemo(
    () => catalogo.filter((p) => temPapel(p, ["colheiteiro"])),
    [catalogo],
  );
  const separadores = useMemo(
    () => catalogo.filter((p) => temPapel(p, ["separador_pedidos"])),
    [catalogo],
  );
  const comprasPadrao = useMemo(
    () => catalogo.filter((p) => temPapel(p, ["fornecedor", "dono", "entregador"])),
    [catalogo],
  );
  const entregadores = useMemo(
    () => catalogo.filter((p) => temPapel(p, ["entregador"])),
    [catalogo],
  );

  useEffect(() => {
    let vivo = true;
    setCarregando(true);
    Promise.all([
      loadColaboradores({ ativos: true }),
      periodo
        ? carregarListaCompra(periodo).catch(() => null)
        : Promise.resolve(null),
      carregarRotaDoDia(dataRota).catch(() => null),
    ])
      .then(([pessoas, lista, rotaDia]) => {
        if (!vivo) return;
        setCatalogo(pessoas.filter((p) => p.active));
        if (lista?.texto?.trim()) {
          setTextoCompras(lista.texto.trim());
          setAvisoCompras("");
        } else if (lista?.itens?.length) {
          const linhas = lista.itens
            .filter((i) => i.qtd > 0)
            .map((i) => `${i.qtd} ${i.produto}`);
          setTextoCompras(["Lista de compras", periodo, "", ...linhas].join("\n").trim());
          setAvisoCompras("");
        } else {
          setTextoCompras("");
          setAvisoCompras("Monte e salve a lista de compras (Colheita) antes de enviar.");
        }
        if (rotaDia?.rota?.paradas?.length) {
          const msg = textoMensagemLocalizacao(rotaDia.rota.paradas);
          setTextoRota(msg);
          setAvisoRota(
            msg
              ? ""
              : "Monte a rota e cadastre o link de localização do cliente.",
          );
        } else if (rotaFallback) {
          setTextoRota(rotaFallback);
          setAvisoRota("Usando ordem das boletas na tela. Em Rota, monte e salve para a ordem otimizada.");
        } else {
          setTextoRota("");
          setAvisoRota(
            "Monte a rota (e cadastre localização dos clientes) para gerar a mensagem.",
          );
        }
      })
      .catch((err) => {
        if (!vivo) return;
        setStatus(err instanceof Error ? err.message : "Falha ao carregar dados.");
      })
      .finally(() => {
        if (vivo) setCarregando(false);
      });
    return () => {
      vivo = false;
    };
  }, [periodo, dataRota, rotaFallback]);

  type ListaKey = "colheita" | "pedidos" | "compras" | "rota";

  async function enviar(
    quais: ListaKey[] = ["colheita", "pedidos", "compras", "rota"],
  ) {
    const payload: Parameters<typeof enviarListasWhatsApp>[0] = {};
    if (quais.includes("colheita") && idsColheita.length && textoColheita.trim()) {
      payload.colheita = { text: textoColheita, colaborador_ids: idsColheita };
    }
    if (quais.includes("pedidos") && idsPedidos.length && textoPedidos.trim()) {
      payload.pedidos = { text: textoPedidos, colaborador_ids: idsPedidos };
    }
    if (quais.includes("compras") && idsCompras.length && textoCompras.trim()) {
      payload.compras = { text: textoCompras, colaborador_ids: idsCompras };
    }
    if (quais.includes("rota") && idsRota.length && textoRota.trim()) {
      payload.rota = { text: textoRota, colaborador_ids: idsRota };
    }
    if (!Object.keys(payload).length) {
      setStatus("Escolha destinatário e confira se há texto nesta lista.");
      return;
    }
    setEnviando(true);
    setStatus("");
    try {
      const result = await enviarListasWhatsApp(payload);
      const msg =
        result.enviados > 0
          ? `Enviado: ${result.enviados} mensagem(ns)${result.falhas ? `, ${result.falhas} falha(s)` : ""}.`
          : "Nada foi enviado. Confira textos e destinatários.";
      setStatus(msg);
      onAviso?.(msg);
    } catch (err) {
      const motivo = err instanceof Error ? err.message : "Não consegui enviar.";
      setStatus(motivo);
      onAviso?.(motivo);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <aside className="popup-whatsapp no-print" aria-label="Enviar WhatsApp">
      <header>
        <strong>Enviar WhatsApp</strong>
        <button type="button" className="icone-acao" title="Fechar" aria-label="Fechar" onClick={onFechar}>
          ×
        </button>
      </header>
      <p className="wa-intro">
        Colheita → colheiteiros · pedidos → separadores · compras → fornecedores/donos/entregadores · rota → entregadores.
        Em cada lista dá para pesquisar e incluir qualquer colaborador.
      </p>
      {carregando ? <p>Carregando…</p> : null}
      <div className="wa-grid wa-grid-4">
        <SeletorPessoas
          titulo="1. Colheita → Colheiteiros"
          padrao={colheiteiros}
          catalogo={catalogo}
          selecionados={idsColheita}
          onChange={setIdsColheita}
          preview={textoColheita}
          aviso={!textoColheita ? "Não há produtos para colher nas boletas da tela." : undefined}
          enviando={enviando}
          onEnviar={() => void enviar(["colheita"])}
        />
        <SeletorPessoas
          titulo="2. Pedidos → Separadores"
          padrao={separadores}
          catalogo={catalogo}
          selecionados={idsPedidos}
          onChange={setIdsPedidos}
          preview={textoPedidos}
          aviso={!textoPedidos ? "Não há pedidos na tela." : undefined}
          enviando={enviando}
          onEnviar={() => void enviar(["pedidos"])}
        />
        <SeletorPessoas
          titulo="3. Compras → Fornecedores / Donos / Entregadores"
          padrao={comprasPadrao}
          catalogo={catalogo}
          selecionados={idsCompras}
          onChange={setIdsCompras}
          preview={textoCompras}
          aviso={avisoCompras || undefined}
          enviando={enviando}
          onEnviar={() => void enviar(["compras"])}
        />
        <SeletorPessoas
          titulo="4. Rota → Entregadores"
          padrao={entregadores}
          catalogo={catalogo}
          selecionados={idsRota}
          onChange={setIdsRota}
          preview={textoRota}
          aviso={avisoRota || undefined}
          enviando={enviando}
          onEnviar={() => void enviar(["rota"])}
        />
      </div>
      {status ? <p className="wa-status">{status}</p> : null}
      <div className="popup-acoes">
        <button
          className="primary"
          type="button"
          disabled={enviando || carregando}
          onClick={() => void enviar()}
        >
          {enviando ? "Enviando…" : "Enviar todos"}
        </button>
        <button type="button" disabled={enviando} onClick={onFechar}>
          Fechar
        </button>
      </div>
    </aside>
  );
}
