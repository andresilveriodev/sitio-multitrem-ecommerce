import { useEffect, useMemo, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { carregarListaCompra, salvarListaCompra } from "./cadastroApi";
import {
  chaveColheita,
  montarListaColheita,
  qtdParaComprar,
  quantidadeColheita,
  textoListaCompra,
  type LinhaColheita,
} from "./colheitaMath";
import type { Order } from "./types";

type Props = {
  orders: Order[];
  onFechar: () => void;
};

/** Altura útil A4 com margem de 8mm (bate com @page no CSS). */
const PAGINA_UTIL_MM = 297 - 16;

function chaveListaLocal(periodo: string): string {
  return `lista-compra:${periodo}`;
}

function lerComprasLocal(periodo: string): Record<string, string> | null {
  if (!periodo) return null;
  try {
    const bruto = localStorage.getItem(chaveListaLocal(periodo));
    if (!bruto) return null;
    const dados = JSON.parse(bruto) as unknown;
    if (!dados || typeof dados !== "object") return null;
    const saida: Record<string, string> = {};
    for (const [chave, valor] of Object.entries(dados as Record<string, unknown>)) {
      if (typeof valor === "string") saida[chave] = valor;
    }
    return saida;
  } catch {
    return null;
  }
}

function gravarComprasLocal(periodo: string, mapa: Record<string, string>) {
  if (!periodo) return;
  try {
    localStorage.setItem(chaveListaLocal(periodo), JSON.stringify(mapa));
  } catch {
    /* ignore quota */
  }
}

function temQuantidadeLocal(mapa: Record<string, string>): boolean {
  return Object.values(mapa).some((valor) => valor.trim().length > 0);
}

function pxParaMm(px: number): number {
  return (px / 96) * 25.4;
}

function dividirColunas(linhas: LinhaColheita[]): LinhaColheita[][] {
  if (linhas.length <= 1) return [linhas];
  const meio = Math.ceil(linhas.length / 2);
  return [linhas.slice(0, meio), linhas.slice(meio)];
}

function medirAlturaMm(el: HTMLElement, larguraMm: number, duas: boolean): number {
  const prev = el.getAttribute("style");
  const layout = duas
    ? "display:grid!important;grid-template-columns:1fr 1fr;gap:8px 14px;align-items:start;"
    : "display:block!important;";
  el.style.cssText = `${layout}position:absolute;left:-12000px;top:0;width:${larguraMm}mm;visibility:hidden;`;
  const altura = pxParaMm(el.getBoundingClientRect().height);
  if (prev == null) el.removeAttribute("style");
  else el.setAttribute("style", prev);
  return altura;
}

/** true = duas colunas só quando uma não aproveita bem o espaço. */
function precisaDuasColunas(altura1Mm: number, altura2Mm: number, sobraMm: number): boolean {
  if (altura1Mm <= sobraMm + 1) return false;
  if (altura2Mm <= sobraMm + 1) return true;
  if (altura1Mm <= PAGINA_UTIL_MM + 1) return false;
  return altura2Mm + 1 < altura1Mm;
}

export function ListaColheita({ orders, onFechar }: Props) {
  const linhas = useMemo(() => montarListaColheita(orders), [orders]);
  const datas = useMemo(
    () => [...new Set(orders.map((order) => order.data.trim()).filter(Boolean))],
    [orders],
  );
  const periodo = datas.join(", ");
  const [comprar, setComprar] = useState<Record<string, string>>({});
  const [pronto, setPronto] = useState(false);
  const [aviso, setAviso] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [duasColunasPrint, setDuasColunasPrint] = useState(false);
  const [copiou, setCopiou] = useState(false);
  const impressaoRef = useRef<HTMLDivElement>(null);
  const comprarRef = useRef(comprar);
  const periodoRef = useRef(periodo);
  const linhasRef = useRef(linhas);
  const datasRef = useRef(datas);
  comprarRef.current = comprar;
  periodoRef.current = periodo;
  linhasRef.current = linhas;
  datasRef.current = datas;

  const compras = linhas.map((linha) => ({
    produto: linha.produto,
    qtd: qtdParaComprar(comprar[chaveColheita(linha.produto)] ?? ""),
  }));
  const texto = textoListaCompra(compras, datas);
  const temCompra = compras.some((item) => item.qtd > 0);

  useEffect(() => {
    if (!periodo) {
      setPronto(false);
      setComprar({});
      return;
    }
    let vivo = true;
    setPronto(false);
    const local = lerComprasLocal(periodo);
    if (local && temQuantidadeLocal(local)) setComprar(local);
    else setComprar({});

    carregarListaCompra(periodo)
      .then((lista) => {
        if (!vivo) return;
        const localAgora = lerComprasLocal(periodo);
        if (localAgora && temQuantidadeLocal(localAgora)) {
          setComprar(localAgora);
        } else if (lista?.itens.length) {
          const proximo: Record<string, string> = {};
          for (const item of lista.itens) {
            proximo[chaveColheita(item.produto)] = quantidadeColheita(item.qtd).replace(/^0+(?=\d)/, "");
          }
          setComprar(proximo);
          gravarComprasLocal(periodo, proximo);
        }
        setPronto(true);
      })
      .catch(() => {
        if (!vivo) return;
        setPronto(true);
        if (!(local && temQuantidadeLocal(local))) {
          setAviso("Não consegui abrir a lista de compras salva.");
        }
      });
    return () => {
      vivo = false;
    };
  }, [periodo]);

  useEffect(() => {
    if (!pronto || !periodo) return;
    gravarComprasLocal(periodo, comprar);
    const itens = linhas
      .map((linha) => ({
        produto: linha.produto,
        qtd: qtdParaComprar(comprar[chaveColheita(linha.produto)] ?? ""),
      }))
      .filter((item) => item.qtd > 0);
    if (!itens.length) return;
    const mensagem = textoListaCompra(itens, datas);
    const timer = window.setTimeout(() => {
      setSalvando(true);
      void salvarListaCompra({ periodo, texto: mensagem, itens })
        .then(() => setAviso("Lista salva automaticamente."))
        .catch((err) =>
          setAviso(err instanceof Error ? err.message : "Não consegui salvar a lista de compras."),
        )
        .finally(() => setSalvando(false));
    }, 700);
    return () => window.clearTimeout(timer);
  }, [comprar, pronto, periodo, linhas, datas]);

  useEffect(() => {
    return () => {
      const periodoAtual = periodoRef.current;
      if (!periodoAtual) return;
      const mapa = comprarRef.current;
      gravarComprasLocal(periodoAtual, mapa);
      const itens = linhasRef.current
        .map((linha) => ({
          produto: linha.produto,
          qtd: qtdParaComprar(mapa[chaveColheita(linha.produto)] ?? ""),
        }))
        .filter((item) => item.qtd > 0);
      if (!itens.length) return;
      void salvarListaCompra({
        periodo: periodoAtual,
        texto: textoListaCompra(itens, datasRef.current),
        itens,
      }).catch(() => undefined);
    };
  }, []);

  function escolherColunas(comPedidos: boolean): boolean {
    const alvo = impressaoRef.current;
    if (!alvo || linhas.length <= 1) return false;

    // Com pedidos a lista vira card no grid 3 colunas (~1/3 ou ~2/3 da folha).
    const largura1 = comPedidos ? 62 : 194;
    const largura2 = comPedidos ? 128 : 194;
    flushSync(() => setDuasColunasPrint(false));
    const altura1 = medirAlturaMm(alvo, largura1, false);

    flushSync(() => setDuasColunasPrint(true));
    const altura2 = medirAlturaMm(alvo, largura2, true);

    // No grid das boletas a altura útil é a da página (célula ao lado / abaixo).
    const sobra = PAGINA_UTIL_MM;
    return precisaDuasColunas(altura1, altura2, sobra);
  }

  function imprimir(comPedidos: boolean) {
    const usarDuas = escolherColunas(comPedidos);
    flushSync(() => setDuasColunasPrint(usarDuas));
    const classe = comPedidos ? "imprimindo-colheita-pedidos" : "imprimindo-colheita";
    const limpar = () => {
      document.body.classList.remove(classe);
      setDuasColunasPrint(false);
      window.removeEventListener("afterprint", limpar);
    };
    document.body.classList.add(classe);
    window.addEventListener("afterprint", limpar);
    window.print();
    setTimeout(limpar, 1000);
  }

  async function copiar() {
    if (!texto) return;
    try {
      await navigator.clipboard.writeText(texto);
      setAviso("Lista de compras copiada.");
      setCopiou(true);
      window.setTimeout(() => setCopiou(false), 1200);
    } catch {
      setAviso("Não consegui copiar. Selecione o texto da lista.");
    }
  }

  async function salvar() {
    const itens = compras.filter((item) => item.qtd > 0);
    if (!itens.length || salvando) return;
    gravarComprasLocal(periodo, comprar);
    setSalvando(true);
    setAviso("");
    try {
      await salvarListaCompra({ periodo, texto, itens });
      setAviso("Lista de compras salva.");
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui salvar a lista de compras.");
    } finally {
      setSalvando(false);
    }
  }

  function renderTabela(bloco: LinhaColheita[], editavel: boolean) {
    return (
      <table>
        <thead>
          <tr>
            <th>Produto</th>
            <th className="num">Qtde</th>
            <th>Clientes</th>
            <th className="num">Comprar</th>
          </tr>
        </thead>
        <tbody>
          {bloco.map((linha) => {
            const chave = chaveColheita(linha.produto);
            const informado = comprar[chave] ?? "";
            const qtd = qtdParaComprar(informado);
            return (
              <tr key={chave}>
                <td>{linha.produto}</td>
                <td className="num">{quantidadeColheita(linha.qtd)}</td>
                <td className="clientes">
                  {linha.clientes.map((c) => `${c.nome} ${quantidadeColheita(c.qtd)}`).join(" · ")}
                </td>
                <td className="num comprar">
                  {editavel ? (
                    <input
                      inputMode="decimal"
                      aria-label={`Comprar ${linha.produto}`}
                      title="Quantidade para comprar. Em branco, o produto fica só na colheita."
                      value={informado}
                      onChange={(event) => {
                        const valor = event.target.value;
                        setComprar((atual) => ({ ...atual, [chave]: valor }));
                        setAviso("");
                      }}
                    />
                  ) : qtd > 0 ? (
                    quantidadeColheita(qtd)
                  ) : (
                    ""
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  }

  const blocosPrint = duasColunasPrint ? dividirColunas(linhas) : [linhas];

  return (
    <section className={duasColunasPrint ? "lista-colheita com-duas-colunas" : "lista-colheita"}>
      <div className="lista-colheita-acoes no-print">
        <h2>Lista de colheita</h2>
        <span className="lista-colheita-btns">
          <button type="button" className="primary" onClick={() => imprimir(false)} disabled={!linhas.length}>
            Imprimir lista
          </button>
          <button
            type="button"
            className="primary"
            title="Imprime a lista e os pedidos na mesma impressão. Se couber, a lista aproveita o espaço livre da folha."
            onClick={() => imprimir(true)}
            disabled={!linhas.length || orders.length === 0}
          >
            Imprimir com pedidos
          </button>
          <button
            type="button"
            onClick={() => void copiar()}
            disabled={!temCompra}
            title="Copia a lista de compras (quantidades e produtos)"
          >
            Copiar lista de compras
          </button>
          <button
            type="button"
            className="primary"
            title="A lista já grava sozinha ao digitar. Use este botão para forçar agora."
            onClick={() => void salvar()}
            disabled={!temCompra || salvando}
          >
            {salvando ? "Salvando…" : "Salvar lista"}
          </button>
          <button type="button" onClick={onFechar}>
            Fechar
          </button>
        </span>
      </div>
      <div className="lista-colheita-folha">
        <h1>Lista de colheita</h1>
        <p className="lista-colheita-meta">
          {orders.length} {orders.length === 1 ? "pedido" : "pedidos"}
          {datas.length ? ` · ${datas.join(", ")}` : ""}
          {` · ${linhas.length} ${linhas.length === 1 ? "produto" : "produtos"}`}
        </p>
        {linhas.length === 0 ? (
          <p className="empty">Não há produto com quantidade nestes pedidos.</p>
        ) : (
          <>
            <div className="lista-colheita-tela">{renderTabela(linhas, true)}</div>
            <div
              ref={impressaoRef}
              className={
                duasColunasPrint ? "lista-colheita-impressao lista-colheita-colunas" : "lista-colheita-impressao"
              }
            >
              {blocosPrint.map((bloco, indice) => (
                <div key={indice} className="lista-colheita-coluna">
                  {renderTabela(bloco, false)}
                </div>
              ))}
            </div>
          </>
        )}
        <div className="lista-compra-texto no-print">
          {temCompra ? (
            <>
              <div className="lista-compra-cabeca">
                <p>Mensagem para enviar</p>
                <button
                  type="button"
                  className={copiou ? "copiar-lista ok" : "copiar-lista"}
                  aria-label={copiou ? "Lista copiada" : "Copiar lista de compras"}
                  title={copiou ? "Copiado" : "Copiar lista de compras"}
                  onClick={() => void copiar()}
                >
                  {copiou ? (
                    "✓"
                  ) : (
                    <svg viewBox="0 0 16 16" aria-hidden="true">
                      <rect x="5" y="5" width="8" height="8" fill="none" stroke="currentColor" strokeWidth="1.4" />
                      <path d="M3 11V3h8" fill="none" stroke="currentColor" strokeWidth="1.4" />
                    </svg>
                  )}
                </button>
              </div>
              <textarea readOnly value={texto} aria-label="Mensagem da lista de compras" />
            </>
          ) : (
            <p className="empty">Na coluna Comprar, informe a quantidade de cada produto que vai comprar.</p>
          )}
          {aviso ? <p className="lista-compra-aviso">{aviso}</p> : null}
        </div>
      </div>
    </section>
  );
}
