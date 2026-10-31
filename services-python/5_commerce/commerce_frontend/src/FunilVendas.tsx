import { useEffect, useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { consultarBoletas, loadClientes, type Cliente } from "./cadastroApi";
import { clienteDoApelido, mesmoCliente, nomeParaGrade } from "./nomeCliente";
import {
  avisosDeAmanha,
  colunasDaSemana,
  diaIdDeIso,
  DIAS,
  foldNomeGrade,
  fundirApelidosNaGrade,
  gravarPlanilhaRecorrente,
  incluirClienteNoDia,
  isoHoje,
  lerPlanilhaRecorrente,
  nomeClienteGrade,
  novaLinha,
  planilhaPadrao,
  proximoDiaGrade,
  renomearNaGrade,
  rotuloSemana,
  somarDiasIso,
  type DiaSemana,
  type PlanilhaRecorrente,
} from "./pedidosRecorrentes";

type Props = {
  ativo?: boolean;
  /** Incrementa após salvar pedido no popup — recarrega boletas da semana. */
  versao?: number;
  onPedirCliente: (cliente: string, dataIso: string) => void;
  onDuplicarPedido: (cliente: string, deIso: string, paraIso: string) => Promise<string>;
  onAlternarEntregue: (cliente: string, dataIso: string) => Promise<string>;
  onAlternarPago: (cliente: string, dataIso: string) => Promise<string>;
};

type MenuContexto = {
  x: number;
  y: number;
  linha: number;
  dia: DiaSemana;
  nome: string;
  dataIso: string;
};

type PedidoRegistrado = { nome: string; dataIso: string; concluido: boolean; pago: boolean };

type StatusCelula = "vazio" | "previo" | "pediu" | "entregue" | "faltou";

function gradeTemNome(planilha: PlanilhaRecorrente, nome: string): boolean {
  const alvo = foldNomeGrade(nome);
  if (!alvo) return false;
  return planilha.linhas.some((linha) => DIAS.some((dia) => foldNomeGrade(linha.dias[dia.id] || "") === alvo));
}

export function FunilVendas({
  ativo = true,
  versao = 0,
  onPedirCliente,
  onDuplicarPedido,
  onAlternarEntregue,
  onAlternarPago,
}: Props) {
  const [planilha, setPlanilha] = useState<PlanilhaRecorrente>(() => lerPlanilhaRecorrente());
  const [aviso, setAviso] = useState("");
  const [offsetSemana, setOffsetSemana] = useState(0);
  const [pedidosRegistrados, setPedidosRegistrados] = useState<PedidoRegistrado[]>([]);
  const [carregandoPedidos, setCarregandoPedidos] = useState(false);
  const [menu, setMenu] = useState<MenuContexto | null>(null);
  const [duplicando, setDuplicando] = useState(false);
  const [marcando, setMarcando] = useState<string | null>(null);
  const [recarga, setRecarga] = useState(0);
  const [catalogo, setCatalogo] = useState<Cliente[] | null>(null);
  const [editando, setEditando] = useState<{ linha: number; dia: DiaSemana } | null>(null);
  const editarRef = useRef<HTMLInputElement | null>(null);
  const cliqueNomeRef = useRef<number | null>(null);

  const amanha = useMemo(() => avisosDeAmanha(planilha), [planilha]);
  const colunas = useMemo(() => colunasDaSemana(offsetSemana), [offsetSemana]);
  const hojeIso = isoHoje();

  useEffect(() => {
    if (!editando) return;
    editarRef.current?.focus();
    editarRef.current?.select();
  }, [editando]);

  useEffect(() => {
    return () => {
      if (cliqueNomeRef.current != null) window.clearTimeout(cliqueNomeRef.current);
    };
  }, []);

  useEffect(() => {
    if (!ativo) return;
    let vivo = true;
    loadClientes()
      .then((lista) => {
        if (vivo) setCatalogo(lista);
      })
      .catch(() => {
        if (vivo) setCatalogo([]);
      });
    return () => {
      vivo = false;
    };
  }, [ativo]);

  useEffect(() => {
    if (!ativo) return;
    const de = colunas[0]?.iso;
    const ate = colunas[colunas.length - 1]?.iso;
    if (!de || !ate) return;
    let vivo = true;
    setCarregandoPedidos(true);
    consultarBoletas(de, ate)
      .then((extrato) => {
        if (!vivo) return;
        const lista: PedidoRegistrado[] = [];
        for (const cliente of extrato.clientes) {
          for (const pedido of cliente.pedidos) {
            if (pedido.tipo === "compra") continue;
            const dataIso = isoDaNota(pedido.data);
            if (!dataIso) continue;
            lista.push({
              nome: cliente.nome,
              dataIso,
              concluido: Boolean(pedido.concluido),
              pago: Boolean(pedido.pago),
            });
          }
        }
        setPedidosRegistrados(lista);
      })
      .catch(() => {
        if (vivo) setPedidosRegistrados([]);
      })
      .finally(() => {
        if (vivo) setCarregandoPedidos(false);
      });
    return () => {
      vivo = false;
    };
  }, [ativo, colunas, recarga, versao]);

  /** Dono e comércio viram um só; pedido confirmado não abre outra linha no mesmo dia. */
  useEffect(() => {
    if (!ativo || carregandoPedidos || catalogo == null) return;
    let atual = planilha;
    let mudou = false;
    const mesmo = (a: string, b: string) => mesmoCliente(a, b, catalogo);
    const renomeada = renomearNaGrade(atual, (nome) =>
      nomeParaGrade(nome, catalogo, (dono) => gradeTemNome(atual, dono)),
    );
    if (renomeada) {
      atual = renomeada;
      mudou = true;
    }
    const fundida = fundirApelidosNaGrade(atual, (a, b) => {
      const ca = clienteDoApelido(a, catalogo);
      const cb = clienteDoApelido(b, catalogo);
      return Boolean(ca && cb && ca.id === cb.id);
    });
    if (fundida) {
      atual = fundida;
      mudou = true;
    }
    for (const pedido of pedidosRegistrados) {
      const dia = diaIdDeIso(pedido.dataIso);
      if (!dia) continue;
      const proxima = incluirClienteNoDia(atual, pedido.nome, dia, mesmo);
      if (proxima) {
        atual = proxima;
        mudou = true;
      }
    }
    if (mudou) {
      setPlanilha(atual);
      gravarPlanilhaRecorrente(atual);
    }
  }, [ativo, carregandoPedidos, pedidosRegistrados, catalogo]);

  useEffect(() => {
    if (!menu) return;
    const fechar = () => setMenu(null);
    window.addEventListener("click", fechar);
    window.addEventListener("scroll", fechar, true);
    return () => {
      window.removeEventListener("click", fechar);
      window.removeEventListener("scroll", fechar, true);
    };
  }, [menu]);

  function atualizar(proxima: PlanilhaRecorrente) {
    setPlanilha(proxima);
    gravarPlanilhaRecorrente(proxima);
    setAviso("");
  }

  function mudarHorario(index: number, horario: string) {
    const linhas = planilha.linhas.map((linha, i) => (i === index ? { ...linha, horario } : linha));
    atualizar({ ...planilha, linhas });
  }

  function mudarCelula(index: number, dia: DiaSemana, valor: string) {
    const linhas = planilha.linhas.map((linha, i) => {
      if (i !== index) return linha;
      const dias = { ...linha.dias };
      if (valor.trim()) dias[dia] = valor;
      else delete dias[dia];
      return { ...linha, dias };
    });
    atualizar({ ...planilha, linhas });
  }

  function copiarNomeNaGrade(linhaIndex: number, deDia: DiaSemana, paraIso: string) {
    const paraDia = diaIdDeIso(paraIso);
    if (!paraDia) return false;
    const nome = (planilha.linhas[linhaIndex]?.dias[deDia] || "").trim();
    if (!nome) return false;
    const linhas = planilha.linhas.map((linha, i) => {
      if (i !== linhaIndex) return linha;
      return { ...linha, dias: { ...linha.dias, [paraDia]: nome } };
    });
    atualizar({ ...planilha, linhas });
    return true;
  }

  async function duplicarPara(destinoIso: string) {
    if (!menu || duplicando) return;
    const { linha, dia, nome, dataIso } = menu;
    setMenu(null);
    setDuplicando(true);
    try {
      copiarNomeNaGrade(linha, dia, destinoIso);
      const msg = await onDuplicarPedido(nome, dataIso, destinoIso);
      setAviso(msg || `Dupliquei ${nomeClienteGrade(nome)} para ${formatarCurta(destinoIso)}.`);
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui duplicar o pedido.");
    } finally {
      setDuplicando(false);
    }
  }

  function adicionarLinha() {
    const id = String(Date.now());
    atualizar({ ...planilha, linhas: [...planilha.linhas, novaLinha(id)] });
  }

  function removerLinha(index: number) {
    if (planilha.linhas.length <= 1) return;
    atualizar({ ...planilha, linhas: planilha.linhas.filter((_, i) => i !== index) });
  }

  function restaurarPadrao() {
    atualizar(planilhaPadrao());
    setAviso("Voltei a planilha inicial da grade de avisos.");
  }

  function tituloCliente(nome: string): string {
    const limpo = nomeClienteGrade(nome);
    const cliente = clienteDoApelido(limpo, catalogo ?? []);
    if (!cliente || foldNomeGrade(limpo) === foldNomeGrade(cliente.name)) return limpo;
    return `${cliente.name} (${limpo})`;
  }

  function pedidoDoDia(nome: string, dataIso: string): PedidoRegistrado | null {
    if (!nome.trim()) return null;
    const lista = catalogo ?? [];
    let achado: PedidoRegistrado | null = null;
    for (const pedido of pedidosRegistrados) {
      if (pedido.dataIso !== dataIso) continue;
      if (!mesmoCliente(nome, pedido.nome, lista)) continue;
      if (!achado || (pedido.concluido && !achado.concluido)) achado = pedido;
    }
    return achado;
  }

  function statusCelula(nome: string, dataIso: string): StatusCelula {
    if (!nome.trim()) return "vazio";
    const pedido = pedidoDoDia(nome, dataIso);
    if (pedido?.concluido) return "entregue";
    if (pedido) return "pediu";
    if (dataIso >= hojeIso) return "previo";
    return "faltou";
  }

  async function marcarEntregue(nome: string, dataIso: string) {
    const chave = `${foldNomeGrade(nome)}|${dataIso}|entregue`;
    if (marcando) return;
    setMarcando(chave);
    try {
      const msg = await onAlternarEntregue(nome, dataIso);
      setAviso(msg);
      setRecarga((n) => n + 1);
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui marcar a entrega.");
    } finally {
      setMarcando(null);
    }
  }

  async function marcarPago(nome: string, dataIso: string) {
    const chave = `${foldNomeGrade(nome)}|${dataIso}|pago`;
    if (marcando) return;
    setMarcando(chave);
    try {
      const msg = await onAlternarPago(nome, dataIso);
      setAviso(msg);
      setRecarga((n) => n + 1);
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui marcar o pagamento.");
    } finally {
      setMarcando(null);
    }
  }

  return (
    <section className="cadastro funil-vendas">
      <h1>Funil de vendas</h1>
      <p>
        Grade por horário de entrega. Pedido confirmado entra na lista daquele dia (mesma tabela). Cores:
        pediu / entregue / não pediu. Use o chat ao lado do nome para montar o pedido.
      </p>

      <div className="funil-amanha">
        <strong>Avisar para amanhã ({amanha.rotulo})</strong>
        {amanha.avisos.length === 0 ? (
          <p>
            {amanha.dia === "domingo"
              ? "Amanhã é domingo — sem entrega padrão; nenhum cliente na grade."
              : "Nenhum cliente marcado para amanhã."}
          </p>
        ) : (
          <ul>
            {amanha.avisos.map((item, index) => (
              <li key={`${item.cliente}-${index}`}>
                {item.horario ? <span className="funil-hora">{item.horario}</span> : null}
                {item.cliente}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="linha funil-acoes no-print">
        <button type="button" onClick={() => setOffsetSemana((atual) => atual - 1)} title="Semana anterior">
          ← Semana
        </button>
        <button type="button" onClick={() => setOffsetSemana(0)} disabled={offsetSemana === 0}>
          Esta semana
        </button>
        <button type="button" onClick={() => setOffsetSemana((atual) => atual + 1)} title="Semana seguinte">
          Semana →
        </button>
        <span className="funil-semana-rotulo">{rotuloSemana(offsetSemana)}</span>
        {carregandoPedidos ? <span className="funil-status">Conferindo pedidos…</span> : null}
      </div>

      <div className="linha funil-acoes no-print">
        <button type="button" onClick={adicionarLinha}>
          Nova linha (horário)
        </button>
        <button type="button" onClick={restaurarPadrao}>
          Restaurar grade inicial
        </button>
        {aviso ? <span className="funil-status">{aviso}</span> : null}
      </div>

      <p className="funil-legenda no-print">
        <span className="funil-legenda-previo">Costuma pedir</span>
        <span className="funil-legenda-pediu">Pediu</span>
        <span className="funil-legenda-entregue">Entregue</span>
        <span className="funil-legenda-faltou">Não pediu</span>
        <span>
          {" "}
          — clique no nome: abrir a boleta; duplo clique: editar; botão direito: duplicar.
        </span>
      </p>

      <div className="funil-grade-wrap">
        <table className="funil-grade">
          <thead>
            <tr>
              <th className="funil-num">#</th>
              <th className="funil-horario">Horário</th>
              {colunas.map((coluna) => {
                const classes = [
                  coluna.iso === hojeIso ? "funil-hoje-col" : "",
                  amanha.dia === coluna.dia && offsetSemana === 0 ? "funil-amanha-col" : "",
                ]
                  .filter(Boolean)
                  .join(" ");
                return (
                  <th key={coluna.dia} className={classes || undefined}>
                    {coluna.rotulo}
                    <span className="funil-data-col">{coluna.curta}</span>
                    {coluna.iso === hojeIso ? <span className="funil-tag">hoje</span> : null}
                    {amanha.dia === coluna.dia && offsetSemana === 0 ? <span className="funil-tag">amanhã</span> : null}
                  </th>
                );
              })}
              <th className="funil-op no-print" />
            </tr>
          </thead>
          <tbody>
            {planilha.linhas.map((linha, index) => (
              <tr key={linha.id}>
                <td className="funil-num">{index + 1}</td>
                <td>
                  <input
                    aria-label={`Horário linha ${index + 1}`}
                    value={linha.horario}
                    onChange={(event) => mudarHorario(index, event.target.value)}
                    placeholder="ex: 08h30"
                  />
                </td>
                {colunas.map((coluna) => {
                  const nome = linha.dias[coluna.dia] || "";
                  const pedido = nome.trim() ? pedidoDoDia(nome, coluna.iso) : null;
                  const status = statusCelula(nome, coluna.iso);
                  const classes = [
                    coluna.iso === hojeIso ? "funil-hoje-col" : "",
                    amanha.dia === coluna.dia && offsetSemana === 0 ? "funil-amanha-col" : "",
                    status === "previo" ? "funil-celula-previo" : "",
                    status === "pediu" ? "funil-celula-pediu" : "",
                    status === "entregue" ? "funil-celula-entregue" : "",
                    status === "faltou" ? "funil-celula-faltou" : "",
                    pedido?.pago ? "funil-celula-paga" : "",
                  ]
                    .filter(Boolean)
                    .join(" ");
                  const chaveBase = `${foldNomeGrade(nome)}|${coluna.iso}`;
                  const editandoEsta = editando?.linha === index && editando?.dia === coluna.dia;
                  const abrirMenu = (event: ReactMouseEvent) => {
                    if (!nome.trim()) return;
                    event.preventDefault();
                    setMenu({
                      x: event.clientX,
                      y: event.clientY,
                      linha: index,
                      dia: coluna.dia,
                      nome,
                      dataIso: coluna.iso,
                    });
                  };
                  return (
                    <td key={coluna.dia} className={classes || undefined}>
                      <div className="funil-celula">
                        {nome.trim() && !editandoEsta ? (
                          <button
                            type="button"
                            className="funil-nome"
                            title={`Abrir boleta de ${tituloCliente(nome)} em ${coluna.curta}. Duplo clique para editar o nome.`}
                            onClick={() => {
                              if (cliqueNomeRef.current != null) window.clearTimeout(cliqueNomeRef.current);
                              cliqueNomeRef.current = window.setTimeout(() => {
                                cliqueNomeRef.current = null;
                                onPedirCliente(nome, coluna.iso);
                              }, 220);
                            }}
                            onDoubleClick={(event) => {
                              event.preventDefault();
                              event.stopPropagation();
                              if (cliqueNomeRef.current != null) {
                                window.clearTimeout(cliqueNomeRef.current);
                                cliqueNomeRef.current = null;
                              }
                              setEditando({ linha: index, dia: coluna.dia });
                            }}
                            onContextMenu={abrirMenu}
                          >
                            {nome}
                          </button>
                        ) : (
                          <input
                            ref={editandoEsta ? editarRef : undefined}
                            aria-label={`${coluna.rotulo} ${coluna.curta} linha ${index + 1}`}
                            value={nome}
                            placeholder="nome"
                            onChange={(event) => mudarCelula(index, coluna.dia, event.target.value)}
                            onBlur={() => setEditando(null)}
                            onKeyDown={(event) => {
                              if (event.key === "Enter" || event.key === "Escape") {
                                event.currentTarget.blur();
                              }
                            }}
                            onContextMenu={abrirMenu}
                          />
                        )}
                        {nome.trim() ? (
                          <span className="funil-celula-acoes">
                            <button
                              type="button"
                              className={pedido?.concluido ? "funil-acao ligado entregue" : "funil-acao"}
                              title={
                                !pedido
                                  ? "Salve o pedido pelo chat antes de marcar entregue"
                                  : pedido.concluido
                                    ? "Entregue — clique para reabrir"
                                    : "Marcar como entregue / concluído"
                              }
                              aria-label="Entregue"
                              aria-pressed={Boolean(pedido?.concluido)}
                              disabled={!pedido || marcando === `${chaveBase}|entregue`}
                              onClick={() => void marcarEntregue(nome, coluna.iso)}
                            >
                              <IconeEntregue />
                            </button>
                            <button
                              type="button"
                              className={pedido?.pago ? "funil-acao ligado pago" : "funil-acao"}
                              title={
                                !pedido
                                  ? "Salve o pedido pelo chat antes de marcar pagamento"
                                  : pedido.pago
                                    ? "Paga — clique para voltar a em aberto"
                                    : "Marcar como paga"
                              }
                              aria-label="Pagamento"
                              aria-pressed={Boolean(pedido?.pago)}
                              disabled={!pedido || marcando === `${chaveBase}|pago`}
                              onClick={() => void marcarPago(nome, coluna.iso)}
                            >
                              <IconePago />
                            </button>
                            <button
                              type="button"
                              className="funil-chat"
                              title={`Incluir pedido de ${nomeClienteGrade(nome)} em ${coluna.curta}`}
                              aria-label={`Chat pedido ${nomeClienteGrade(nome)}`}
                              onClick={() => onPedirCliente(nome, coluna.iso)}
                            >
                              <IconeChat />
                            </button>
                          </span>
                        ) : null}
                      </div>
                    </td>
                  );
                })}
                <td className="funil-op no-print">
                  <button type="button" title="Remover linha" onClick={() => removerLinha(index)}>
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {menu ? (
        <div
          className="funil-menu-contexto no-print"
          style={{ left: menu.x, top: menu.y }}
          role="menu"
          onClick={(event) => event.stopPropagation()}
        >
          <strong>{nomeClienteGrade(menu.nome)}</strong>
          <button
            type="button"
            role="menuitem"
            disabled={duplicando}
            onClick={() => void duplicarPara(proximoDiaGrade(menu.dataIso))}
          >
            Duplicar para o dia seguinte
          </button>
          <button
            type="button"
            role="menuitem"
            disabled={duplicando}
            onClick={() => void duplicarPara(somarDiasIso(menu.dataIso, 7))}
          >
            Duplicar para a semana seguinte
          </button>
        </div>
      ) : null}
    </section>
  );
}

function isoDaNota(data: string): string {
  const iso = /^(\d{4})-(\d{2})-(\d{2})$/.exec(data.trim());
  if (iso) return `${iso[1]}-${iso[2]}-${iso[3]}`;
  const br = /^(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?$/.exec(data.trim());
  if (!br) return "";
  const dia = br[1].padStart(2, "0");
  const mes = br[2].padStart(2, "0");
  let ano = br[3] ? Number(br[3]) : new Date().getFullYear();
  if (ano < 100) ano += 2000;
  return `${ano}-${mes}-${dia}`;
}

function formatarCurta(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!match) return iso;
  return `${match[3]}/${match[2]}`;
}

function IconeChat() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M2.5 3.5h11v8H6.2L2.5 14.2V3.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function IconeEntregue() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M3.5 8.2 6.5 11.2 12.5 4.8" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

function IconePago() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M8 2.2v11.6" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M10.6 4.8c-.7-1.2-1.7-1.8-2.6-1.8-1.2 0-2.2.7-2.2 1.8 0 1.1.7 1.6 2.8 2.2 2.2.6 3.1 1.5 3.1 2.9 0 1.5-1.3 2.5-3.1 2.5-1.2 0-2.3-.5-3.1-1.6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      />
    </svg>
  );
}
