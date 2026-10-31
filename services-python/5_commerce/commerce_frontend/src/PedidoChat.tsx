import { useEffect, useId, useRef, useState } from "react";
import {
  conversaAtual,
  gravarMensagemConversa,
  limparConversaPainel,
  listarConversas,
  type Cliente,
  type ConversaGravada,
} from "./cadastroApi";
import type { ClienteOpcao, ClienteParaIncluir, DecisaoListagem, RevisaoPedido, SugestaoAlface } from "./pedidoConversa";
import { perguntaAlface } from "./pedidoConversa";
import { formatMoney } from "./orderMath";
import type { Order, OrderItem } from "./types";

type Mensagem = { papel: "voce" | "bot"; texto: string };
type Painel = "venda" | "compra";

const TEXTO_VENDA = "Cole a conversa do WhatsApp. Eu leio, respondo aqui e a nota aparece à esquerda para você corrigir.";
const TEXTO_COMPRA = "Diga o preço por aqui. Exemplo: o preço de todos os itens foi 3 reais cada.";

const avisosGravados = new Set<number>();

function papelDe(valor: string): "voce" | "bot" {
  return valor === "voce" ? "voce" : "bot";
}

function IconeCopiar() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <rect x="5" y="5" width="8" height="8" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <path d="M3 11V3h8" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

function Balao({ papel, texto, rotulo }: { papel: string; texto: string; rotulo?: string }) {
  const [copiado, setCopiado] = useState(false);
  async function copiar() {
    try {
      await navigator.clipboard.writeText(texto);
    } catch {
      const area = document.createElement("textarea");
      area.value = texto;
      area.setAttribute("readonly", "");
      area.style.position = "fixed";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      if (!ok) return;
    }
    setCopiado(true);
    window.setTimeout(() => setCopiado(false), 1200);
  }
  return (
    <div className={`balao ${papel}`}>
      <button
        type="button"
        className="copiar-mensagem"
        aria-label={copiado ? "Mensagem copiada" : "Copiar mensagem"}
        title={copiado ? "Copiado" : "Copiar mensagem"}
        onClick={() => void copiar()}
      >
        {copiado ? "✓" : <IconeCopiar />}
      </button>
      {rotulo ? <small>{rotulo}</small> : null}
      {texto}
    </div>
  );
}

function quando(iso: string): string {
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return "";
  return data.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function useConversa(painel: Painel, inicial: string) {
  const [mensagens, setMensagens] = useState<Mensagem[]>([{ papel: "bot", texto: inicial }]);
  const pronta = useRef(false);
  const fila = useRef<Mensagem[]>([]);

  useEffect(() => {
    let vivo = true;
    pronta.current = false;
    conversaAtual(painel)
      .then((conversa) => {
        if (!vivo) return;
        pronta.current = true;
        const gravadas = conversa.mensagens.map((item) => ({ papel: papelDe(item.papel), texto: item.texto }));
        const extras = fila.current.filter(
          (item) => !gravadas.some((outra) => outra.papel === item.papel && outra.texto === item.texto),
        );
        fila.current = [];
        setMensagens(gravadas.length || extras.length ? [...gravadas, ...extras] : [{ papel: "bot", texto: inicial }]);
      })
      .catch(() => {
        if (!vivo) return;
        pronta.current = true;
      });
    return () => {
      vivo = false;
    };
  }, [painel, inicial]);

  function acrescentar(papel: "voce" | "bot", texto: string) {
    const limpo = texto.trim();
    if (!limpo) return;
    const item = { papel, texto: limpo };
    if (!pronta.current) fila.current = [...fila.current, item];
    setMensagens((atual) => [...atual, item]);
    void gravarMensagemConversa(painel, papel, limpo).catch(() => {
      setMensagens((atual) => [
        ...atual,
        { papel: "bot", texto: "Essa mensagem ficou na tela, mas não entrou no histórico." },
      ]);
    });
  }

  async function limpar() {
    await limparConversaPainel(painel);
    fila.current = [];
    setMensagens([{ papel: "bot", texto: inicial }]);
  }

  return { mensagens, acrescentar, limpar };
}

function HistoricoConversa({ painel }: { painel: Painel }) {
  const [lista, setLista] = useState<ConversaGravada[] | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    let vivo = true;
    setLista(null);
    setErro("");
    listarConversas(painel)
      .then((itens) => {
        if (vivo) setLista(itens);
      })
      .catch((err) => {
        if (vivo) setErro(err instanceof Error ? err.message : "Não consegui abrir o histórico.");
      });
    return () => {
      vivo = false;
    };
  }, [painel]);

  return (
    <div className="historico-conversa">
      <p>O que sai da tela continua aqui.</p>
      {erro ? <p>{erro}</p> : null}
      {lista === null && !erro ? <p>Abrindo o histórico…</p> : null}
      {lista && lista.length === 0 ? <p>Nenhuma conversa gravada ainda.</p> : null}
      {lista?.map((conversa) => (
        <article key={conversa.id} className="historico-bloco">
          <p className="quando">
            {quando(conversa.mensagens[0]?.criada_em || conversa.iniciada_em)}
            {conversa.encerrada_em ? "" : " · na tela"}
          </p>
          {conversa.mensagens.map((mensagem) => (
            <Balao
              key={mensagem.id}
              papel={papelDe(mensagem.papel)}
              rotulo={mensagem.papel === "voce" ? "Você" : "Sistema"}
              texto={mensagem.texto}
            />
          ))}
        </article>
      ))}
    </div>
  );
}

export function PedidoChat({
  aberto,
  embutido = false,
  soVenda = false,
  aviso,
  novos,
  opcoes,
  revisao,
  onDecidir,
  sugestaoAlface,
  onDecidirAlface,
  interpretadorFora = false,
  onAvisarAdministrador,
  onEscolher,
  onIncluir,
  onToggle,
  onSend,
  modo,
  onModo,
  compra,
  fornecedores,
  onFornecedor,
  onCompra,
  onFalar,
  onSalvar,
  onSalvarVenda,
}: {
  aberto: boolean;
  /** Dentro de outro modal (ex.: funil) — sem posição fixa e sem botão flutuante. */
  embutido?: boolean;
  /** Esconde a aba Compra (ex.: popup do funil). */
  soVenda?: boolean;
  aviso: { id: number; texto: string } | null;
  novos: ClienteParaIncluir[];
  opcoes: ClienteOpcao[];
  revisao: RevisaoPedido | null;
  onDecidir: (modo: DecisaoListagem) => void;
  sugestaoAlface: SugestaoAlface | null;
  onDecidirAlface: (aceitar: boolean) => void;
  interpretadorFora?: boolean;
  onAvisarAdministrador?: (avisar: boolean) => void;
  onEscolher: (id: number) => void;
  onIncluir: (cliente: ClienteParaIncluir) => void;
  onToggle: () => void;
  onSend: (texto: string) => Promise<string>;
  modo: "venda" | "compra";
  onModo: (modo: "venda" | "compra") => void;
  compra: Order | null;
  fornecedores: Cliente[];
  onFornecedor: (nome: string, commit: boolean) => void;
  onCompra: (order: Order) => void;
  onFalar: (frase: string) => Promise<string>;
  onSalvar: () => Promise<string>;
  onSalvarVenda?: () => void;
}) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [historico, setHistorico] = useState(false);
  const [confirmandoLimpeza, setConfirmandoLimpeza] = useState(false);
  const [limpando, setLimpando] = useState(false);
  const venda = useConversa("venda", TEXTO_VENDA);
  const compraConversa = useConversa("compra", TEXTO_COMPRA);
  const ativa = modo === "compra" ? compraConversa : venda;
  const fim = useRef<HTMLDivElement>(null);
  const registrarVenda = useRef(venda.acrescentar);
  registrarVenda.current = venda.acrescentar;

  useEffect(() => {
    fim.current?.scrollIntoView({ block: "end" });
  }, [venda.mensagens, enviando, aberto]);

  useEffect(() => {
    if (!aviso?.texto || avisosGravados.has(aviso.id)) return;
    avisosGravados.add(aviso.id);
    registrarVenda.current("bot", aviso.texto);
  }, [aviso]);

  async function enviar() {
    const frase = texto.trim();
    if (!frase || enviando) return;
    setTexto("");
    venda.acrescentar("voce", frase);
    setEnviando(true);
    try {
      const resposta = await onSend(frase);
      venda.acrescentar("bot", resposta);
    } catch (err) {
      const motivo = err instanceof Error ? err.message : "Não consegui ler a conversa";
      venda.acrescentar("bot", motivo);
    } finally {
      setEnviando(false);
    }
  }

  async function limparConversa() {
    setLimpando(true);
    try {
      await ativa.limpar();
      setConfirmandoLimpeza(false);
      setHistorico(false);
    } catch (err) {
      ativa.acrescentar("bot", err instanceof Error ? err.message : "Não consegui limpar a conversa da tela.");
    } finally {
      setLimpando(false);
    }
  }

  if (!aberto) {
    if (embutido) return null;
    return (
      <button
        className="pedido-abrir no-print"
        type="button"
        title={modo === "compra" ? "Compra" : "Incluir pedido"}
        aria-label={modo === "compra" ? "Abrir compra" : "Abrir incluir pedido"}
        onClick={onToggle}
      >
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M2.5 3.5h11v8H6.2L2.5 14.2V3.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      </button>
    );
  }

  const classePopup = [
    "pedido-popup",
    "no-print",
    modo === "compra" ? "compra-flutuante" : "",
    embutido ? "embutido" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <aside className={classePopup}>
      <header>
        <strong>{modo === "compra" ? "Compra" : "Incluir pedido"}</strong>
        <span className="pedido-acoes">
          {historico ? (
            <button type="button" onClick={() => setHistorico(false)}>
              Voltar
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setConfirmandoLimpeza(false);
                setHistorico(true);
              }}
            >
              Histórico
            </button>
          )}
          {historico ? null : (
            <button type="button" onClick={() => setConfirmandoLimpeza(true)}>
              Limpar
            </button>
          )}
          <button type="button" className="recolher" title="Recolher" aria-label="Recolher" onClick={onToggle}>
            <svg viewBox="0 0 16 16" aria-hidden="true">
              <path d="M6 3.5 11 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
            </svg>
          </button>
        </span>
      </header>
      {soVenda ? null : (
        <div className="modo-nota">
          <button type="button" className={modo === "venda" ? "primary" : undefined} onClick={() => onModo("venda")}>
            Venda
          </button>
          <button type="button" className={modo === "compra" ? "primary" : undefined} onClick={() => onModo("compra")}>
            Compra
          </button>
        </div>
      )}
      {!historico && confirmandoLimpeza ? (
        <div className="pedido-limpar">
          <p>Limpar a conversa da tela? O que foi dito continua no histórico.</p>
          <button type="button" disabled={limpando} onClick={() => void limparConversa()}>
            {limpando ? "Limpando…" : "Limpar"}
          </button>
          <button type="button" disabled={limpando} onClick={() => setConfirmandoLimpeza(false)}>
            Cancelar
          </button>
        </div>
      ) : null}
      {historico ? (
        <HistoricoConversa painel={modo === "compra" ? "compra" : "venda"} />
      ) : modo === "compra" ? (
        <CompraPainel
          compra={compra}
          fornecedores={fornecedores}
          mensagens={compraConversa.mensagens}
          onAcrescentar={compraConversa.acrescentar}
          onFornecedor={onFornecedor}
          onCompra={onCompra}
          onFalar={onFalar}
          onSalvar={onSalvar}
        />
      ) : (
      <>
      <div className="chat-log">
        {venda.mensagens.map((mensagem, index) => (
          <Balao key={index} papel={mensagem.papel} texto={mensagem.texto} />
        ))}
        <div ref={fim} />
      </div>
      {opcoes.length > 0 ? (
        <div className="pedido-opcoes">
          {opcoes.map((opcao) => (
            <button
              key={opcao.id}
              type="button"
              onClick={() => {
                venda.acrescentar("voce", `${opcao.nome}\n${opcao.detalhe}`);
                onEscolher(opcao.id);
              }}
            >
              {opcao.nome}
              <small>{opcao.detalhe}</small>
            </button>
          ))}
        </div>
      ) : null}
      {interpretadorFora ? (
        <div className="pedido-opcoes">
          <p className="passo">Deseja avisar o administrador?</p>
          <button
            type="button"
            className="primary"
            onClick={() => {
              venda.acrescentar("voce", "Sim");
              onAvisarAdministrador?.(true);
            }}
          >
            Sim
          </button>
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", "Não");
              onAvisarAdministrador?.(false);
            }}
          >
            Não
          </button>
        </div>
      ) : null}
      {sugestaoAlface && !revisao && !interpretadorFora ? (
        <div className="pedido-opcoes">
          <p className="passo">{perguntaAlface(sugestaoAlface)}</p>
          <button
            type="button"
            className="primary"
            onClick={() => {
              venda.acrescentar("voce", "Sim");
              onDecidirAlface(true);
            }}
          >
            Sim, colocar
          </button>
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", "Não");
              onDecidirAlface(false);
            }}
          >
            Não
          </button>
        </div>
      ) : null}
      {revisao && !interpretadorFora ? (
        <div className="pedido-opcoes">
          <p className="passo">
            {revisao.total > 1 ? `Pedido ${revisao.ordem} de ${revisao.total}. ` : ""}
            {revisao.cliente}
            {revisao.data ? ` · ${revisao.data}` : ""}
          </p>
          {revisao.resumo ? <p className="resumo">{revisao.resumo}</p> : null}
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", `Acrescentar em ${revisao.cliente}`);
              onDecidir("atualizar");
            }}
          >
            Acrescentar neste
          </button>
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", `Substituir ${revisao.cliente}`);
              onDecidir("substituir");
            }}
          >
            Substituir itens
          </button>
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", `Deixar ${revisao.cliente} como está`);
              onDecidir("deixar");
            }}
          >
            Deixar como está
          </button>
          <button
            type="button"
            onClick={() => {
              venda.acrescentar("voce", `Incluir outro pedido de ${revisao.cliente}`);
              onDecidir("incluir");
            }}
          >
            Incluir outro
          </button>
          {revisao.total > revisao.ordem ? (
            <>
              <p className="todos-iguais">Todos iguais</p>
              <button
                type="button"
                onClick={() => {
                  venda.acrescentar("voce", "Acrescentar na listagem");
                  onDecidir("todos-atualizar");
                }}
              >
                Acrescentar na listagem
              </button>
              <button
                type="button"
                onClick={() => {
                  venda.acrescentar("voce", "Substituir a listagem");
                  onDecidir("todos-substituir");
                }}
              >
                Substituir a listagem
              </button>
              <button
                type="button"
                onClick={() => {
                  venda.acrescentar("voce", "Inserir o novo pedido");
                  onDecidir("todos-incluir");
                }}
              >
                Inserir o novo pedido
              </button>
            </>
          ) : null}
        </div>
      ) : null}
      {novos.length > 0 ? (
        <div className="pedido-incluir">
          {novos.map((cliente) => (
            <button
              key={cliente.nome}
              className="primary"
              type="button"
              onClick={() => {
                venda.acrescentar(
                  "bot",
                  cliente.fornecedor
                    ? `Abri o fornecedor ${cliente.nome}. Confirme o nome, o proprietário e o setor.`
                    : `Abri o cadastro de ${cliente.nome}. Complete celular, endereço e localização e confirme.`,
                );
                onIncluir(cliente);
              }}
            >
              {cliente.fornecedor ? `Incluir fornecedor ${cliente.nome}` : `Cadastrar ${cliente.nome}`}
            </button>
          ))}
        </div>
      ) : null}
      {onSalvarVenda ? (
        <button type="button" className="primary funil-chat-salvar" onClick={onSalvarVenda}>
          Salvar
        </button>
      ) : null}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void enviar();
        }}
      >
        <textarea
          value={texto}
          placeholder="Cole aqui a conversa do cliente"
          onChange={(event) => setTexto(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void enviar();
            }
          }}
        />
        <button className="primary" type="submit" disabled={enviando || !texto.trim()}>
          {enviando ? "Lendo…" : "Enviar"}
        </button>
      </form>
      </>
      )}
    </aside>
  );
}

function PrecoCompra({ item, onValor }: { item: OrderItem; onValor: (valor: number) => void }) {
  const [rascunho, setRascunho] = useState<string | null>(null);
  const mostrado = item.valor > 0 ? String(item.valor).replace(".", ",") : "";
  return (
    <input
      aria-label={`Preço de ${item.produto}`}
      value={rascunho ?? mostrado}
      placeholder="R$"
      onFocus={() => setRascunho(mostrado)}
      onBlur={() => setRascunho(null)}
      onChange={(event) => {
        setRascunho(event.target.value);
        onValor(lerNumero(event.target.value) ?? 0);
      }}
    />
  );
}

function lerNumero(texto: string): number | undefined {
  const normal = texto.trim().replace(",", ".");
  if (normal === "" || normal === ".") return undefined;
  const valor = Number(normal);
  return Number.isFinite(valor) ? valor : undefined;
}

function CompraPainel({
  compra,
  fornecedores,
  mensagens,
  onAcrescentar,
  onFornecedor,
  onCompra,
  onFalar,
  onSalvar,
}: {
  compra: Order | null;
  fornecedores: Cliente[];
  mensagens: Mensagem[];
  onAcrescentar: (papel: "voce" | "bot", texto: string) => void;
  onFornecedor: (nome: string, commit: boolean) => void;
  onCompra: (order: Order) => void;
  onFalar: (frase: string) => Promise<string>;
  onSalvar: () => Promise<string>;
}) {
  const lista = useId();
  const fim = useRef<HTMLDivElement>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [confirmar, setConfirmar] = useState(false);
  const itens = (compra?.itens ?? []).filter((item) => item.qtd > 0 && item.produto.trim());
  const total = itens.reduce((soma, item) => soma + item.qtd * item.valor, 0);
  const semPreco = itens.filter((item) => !(item.valor > 0)).map((item) => item.produto);

  useEffect(() => {
    fim.current?.scrollIntoView({ block: "end" });
  }, [mensagens, enviando]);

  async function enviar() {
    const frase = texto.trim();
    if (!frase || enviando) return;
    setTexto("");
    onAcrescentar("voce", frase);
    setEnviando(true);
    try {
      const resposta = await onFalar(frase);
      onAcrescentar("bot", resposta);
    } catch (err) {
      const motivo = err instanceof Error ? err.message : "Não consegui ler isso";
      onAcrescentar("bot", motivo);
    } finally {
      setEnviando(false);
    }
  }

  async function salvar() {
    setSalvando(true);
    try {
      const resposta = await onSalvar();
      setConfirmar(false);
      onAcrescentar("bot", resposta);
    } finally {
      setSalvando(false);
    }
  }

  function mudarItem(produto: string, patch: Partial<OrderItem>) {
    if (!compra) return;
    onCompra({
      ...compra,
      itens: compra.itens.map((item) => (item.produto === produto ? { ...item, ...patch } : item)),
    });
  }

  return (
    <div className="compra-painel">
      <p>Marque Comprados em cada pedido. A quantidade entra aqui, sem digitar o produto de novo.</p>
      <label>
        <span>Fornecedor</span>
        <input
          value={compra?.cliente ?? ""}
          placeholder="quem vendeu"
          list={lista}
          onChange={(event) => onFornecedor(event.target.value, false)}
          onBlur={(event) => onFornecedor(event.target.value, true)}
        />
        <datalist id={lista}>
          {fornecedores
            .filter((cliente) => cliente.kind === "fornecedor")
            .map((cliente) => (
              <option key={cliente.id} value={cliente.name} />
            ))}
        </datalist>
      </label>
      <label>
        <span>Data</span>
        <input
          value={compra?.data ?? ""}
          placeholder="DD/MM"
          onChange={(event) => compra && onCompra({ ...compra, data: event.target.value })}
        />
      </label>
      {itens.length ? (
        <table>
          <thead>
            <tr>
              <th>Produto</th>
              <th>Qtde</th>
              <th>Preço</th>
            </tr>
          </thead>
          <tbody>
            {itens.map((item) => (
              <tr key={item.produto}>
                <td>{item.produto}</td>
                <td className="num">{item.qtd}</td>
                <td>
                  <PrecoCompra item={item} onValor={(valor) => mudarItem(item.produto, { valor, preco_tabela: false })} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="empty">Nenhum item marcado ainda.</p>
      )}
      <p className="compra-total">Total {formatMoney(total)}</p>
      <div className="compra-chat">
        <div className="chat-log">
          {mensagens.map((mensagem, index) => (
            <Balao key={index} papel={mensagem.papel} texto={mensagem.texto} />
          ))}
          <div ref={fim} />
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void enviar();
          }}
        >
          <textarea
            value={texto}
            placeholder="O preço de todos os itens foi 3 reais cada"
            onChange={(event) => setTexto(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void enviar();
              }
            }}
          />
          <button className="primary" type="submit" disabled={enviando || !texto.trim()}>
            {enviando ? "Lendo…" : "Enviar"}
          </button>
        </form>
      </div>
      <div className="compra-salvar">
        {confirmar ? (
          <>
            <p>
              {semPreco.length
                ? `${semPreco.join(", ")} está sem preço. Gravar a compra mesmo assim?`
                : `Gravar a compra${compra?.cliente.trim() ? ` de ${compra.cliente.trim()}` : ""}?`}
            </p>
            <button className="primary" type="button" disabled={salvando} onClick={() => void salvar()}>
              {salvando ? "Salvando…" : "Confirmar"}
            </button>
            <button type="button" disabled={salvando} onClick={() => setConfirmar(false)}>
              Cancelar
            </button>
          </>
        ) : (
          <button className="primary" type="button" disabled={!itens.length || salvando} onClick={() => setConfirmar(true)}>
            {compra?.id ? "Atualizar compra" : "Salvar compra"}
          </button>
        )}
      </div>
    </div>
  );
}
