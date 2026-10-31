import { useEffect, useMemo, useState } from "react";
import { CadastroChat } from "./CadastroChat";
import {
  excluirColaborador,
  inativarColaborador,
  loadColaboradores,
  saveColaborador,
  type Colaborador,
  type PapelColaborador,
} from "./cadastroApi";
import {
  interpretarComandoColaborador,
  type FormColaborador,
} from "./comandoColaborador";

const PAPEIS: { id: PapelColaborador; label: string }[] = [
  { id: "dono", label: "Dono" },
  { id: "funcionario", label: "Funcionário" },
  { id: "entregador", label: "Entregador" },
  { id: "colheiteiro", label: "Colheiteiro" },
  { id: "granjeiro", label: "Granjeiro" },
  { id: "separador_pedidos", label: "Separador de pedidos" },
  { id: "fornecedor", label: "Fornecedor" },
];

function showPhone(value: string | null | undefined): string {
  if (!value) return "";
  const digits = value.replace(/\D/g, "");
  const local = digits.startsWith("55") && digits.length > 11 ? digits.slice(2) : digits;
  if (local.length === 11) return `${local.slice(0, 2)} ${local.slice(2, 7)}-${local.slice(7)}`;
  if (local.length === 10) return `${local.slice(0, 2)} ${local.slice(2, 6)}-${local.slice(6)}`;
  return value;
}

function labelPapel(role: string): string {
  return PAPEIS.find((item) => item.id === role)?.label ?? role;
}

function IconeBotao({
  nome,
  titulo,
  onClick,
}: {
  nome: "editar" | "inativar" | "excluir";
  titulo: string;
  onClick: () => void;
}) {
  return (
    <button type="button" className="icone-acao" title={titulo} aria-label={titulo} onClick={onClick}>
      <svg viewBox="0 0 16 16" aria-hidden="true">
        {nome === "editar" ? (
          <>
            <path d="M2.5 11.5 11 3l2 2-8.5 8.5H2.5v-2Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M9.2 4.2 11.8 6.8" fill="none" stroke="currentColor" strokeWidth="1.4" />
          </>
        ) : null}
        {nome === "inativar" ? (
          <>
            <circle cx="8" cy="8" r="5.2" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M4.4 4.4 11.6 11.6" fill="none" stroke="currentColor" strokeWidth="1.4" />
          </>
        ) : null}
        {nome === "excluir" ? (
          <>
            <path d="M3.5 5.5h9" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M6 5.5V3.5h4v2" fill="none" stroke="currentColor" strokeWidth="1.4" />
            <path d="M4.5 5.5 5.2 13h5.6l.7-7.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
          </>
        ) : null}
      </svg>
    </button>
  );
}

function rolesDe(item: Colaborador): PapelColaborador[] {
  if (item.roles?.length) return item.roles;
  return item.role ? [item.role] : [];
}

const vazio: FormColaborador = {
  name: "",
  phone: "",
  roles: ["entregador"],
  endereco: "",
  localizacao: "",
  active: true,
  notes: "",
};

function payloadDe(form: FormColaborador) {
  return {
    name: form.name.trim(),
    phone_e164: form.phone,
    roles: form.roles,
    endereco: form.endereco.trim() || undefined,
    localizacao: form.localizacao.trim() || undefined,
    active: form.active,
    notes: form.notes.trim() || undefined,
  };
}

const ORDEM_FUNCAO: PapelColaborador[] = PAPEIS.map((item) => item.id);

function indiceFuncao(role: PapelColaborador): number {
  const i = ORDEM_FUNCAO.indexOf(role);
  return i === -1 ? 99 : i;
}

/** Função principal para agrupar a linha (primeira na ordem do catálogo). */
function funcaoPrincipal(item: Colaborador): PapelColaborador {
  const roles = rolesDe(item);
  if (!roles.length) return "funcionario";
  return [...roles].sort((a, b) => indiceFuncao(a) - indiceFuncao(b))[0];
}

export function Colaboradores() {
  const [lista, setLista] = useState<Colaborador[]>([]);
  const [form, setForm] = useState<FormColaborador>(vazio);
  const [formAberto, setFormAberto] = useState(false);
  const [pendente, setPendente] = useState(false);
  const [inativarPendente, setInativarPendente] = useState(false);
  const [filtro, setFiltro] = useState("");
  const [papelFiltro, setPapelFiltro] = useState<PapelColaborador | "">("");
  const [aviso, setAviso] = useState("");
  const [erroForm, setErroForm] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [carregando, setCarregando] = useState(false);

  async function carregar(q = filtro, role = papelFiltro) {
    setCarregando(true);
    try {
      const rows = await loadColaboradores({
        q: q.trim() || undefined,
        role: role || undefined,
      });
      setLista(rows);
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui carregar colaboradores.");
    } finally {
      setCarregando(false);
    }
  }

  useEffect(() => {
    void carregar();
  }, []);

  const linhasTabela = useMemo(() => {
    const ordenada = [...lista].sort((a, b) => {
      const fa = indiceFuncao(funcaoPrincipal(a));
      const fb = indiceFuncao(funcaoPrincipal(b));
      if (fa !== fb) return fa - fb;
      return a.name.localeCompare(b.name, "pt-BR");
    });
    type Linha =
      | { tipo: "grupo"; role: PapelColaborador }
      | { tipo: "pessoa"; item: Colaborador };
    const linhas: Linha[] = [];
    if (papelFiltro) {
      for (const item of ordenada) linhas.push({ tipo: "pessoa", item });
      return linhas;
    }
    let grupoAtual: PapelColaborador | null = null;
    for (const item of ordenada) {
      const grupo = funcaoPrincipal(item);
      if (grupo !== grupoAtual) {
        grupoAtual = grupo;
        linhas.push({ tipo: "grupo", role: grupo });
      }
      linhas.push({ tipo: "pessoa", item });
    }
    return linhas;
  }, [lista, papelFiltro]);

  function abrirNovo() {
    setForm(vazio);
    setPendente(false);
    setInativarPendente(false);
    setErroForm("");
    setFormAberto(true);
  }

  function editar(item: Colaborador) {
    setForm({
      id: item.id,
      name: item.name,
      phone: showPhone(item.phone_e164),
      roles: rolesDe(item),
      endereco: item.endereco ?? "",
      localizacao: item.localizacao ?? "",
      active: item.active,
      notes: item.notes ?? "",
    });
    setPendente(false);
    setInativarPendente(false);
    setErroForm("");
    setFormAberto(true);
  }

  function fecharForm() {
    setForm(vazio);
    setFormAberto(false);
    setPendente(false);
    setInativarPendente(false);
    setErroForm("");
  }

  function aoCampo<K extends keyof FormColaborador>(campo: K, valor: FormColaborador[K]) {
    setForm((atual) => ({ ...atual, [campo]: valor }));
    setPendente(false);
  }

  function alternarFuncao(papel: PapelColaborador) {
    setForm((atual) => {
      const tem = atual.roles.includes(papel);
      const roles = tem ? atual.roles.filter((item) => item !== papel) : [...atual.roles, papel];
      return { ...atual, roles };
    });
    setPendente(false);
  }

  async function salvarDireto() {
    if (!form.name.trim()) {
      setErroForm("Informe o nome.");
      return;
    }
    if (!form.phone.replace(/\D/g, "")) {
      setErroForm("Informe o WhatsApp.");
      return;
    }
    if (!form.roles.length) {
      setErroForm("Marque ao menos uma função.");
      return;
    }
    setSalvando(true);
    setErroForm("");
    try {
      await saveColaborador(payloadDe(form), form.id);
      setAviso(form.id ? "Colaborador atualizado." : "Colaborador cadastrado.");
      fecharForm();
      await carregar();
    } catch (err) {
      setErroForm(err instanceof Error ? err.message : "Não consegui salvar.");
    } finally {
      setSalvando(false);
    }
  }

  async function onChat(frase: string): Promise<string> {
    const resultado = interpretarComandoColaborador(frase, lista);
    if (resultado.tipo === "resposta") return resultado.texto;
    setForm(resultado.form);
    setPendente(true);
    setInativarPendente(Boolean(resultado.inativar));
    setFormAberto(true);
    setErroForm("");
    setAviso("");
    return resultado.texto;
  }

  async function confirmarChat() {
    if (!pendente) return;
    setSalvando(true);
    try {
      if (inativarPendente && form.id) {
        await inativarColaborador(form.id);
      } else {
        if (!form.roles.length) throw new Error("Marque ao menos uma função.");
        await saveColaborador(payloadDe(form), form.id);
      }
      fecharForm();
      setAviso("Alteração gravada.");
      await carregar();
    } catch (err) {
      setErroForm(err instanceof Error ? err.message : "Não consegui gravar.");
    } finally {
      setSalvando(false);
    }
  }

  function descartarChat() {
    fecharForm();
    setAviso("Alteração descartada.");
  }

  async function inativar(item: Colaborador) {
    if (!window.confirm(`Inativar ${item.name}?`)) return;
    try {
      await inativarColaborador(item.id);
      if (form.id === item.id) fecharForm();
      setAviso(`${item.name} ficou inativo.`);
      await carregar();
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui inativar.");
    }
  }

  async function excluir(item: Colaborador) {
    if (!window.confirm(`Excluir ${item.name} do cadastro? Isso não dá para desfazer.`)) return;
    try {
      await excluirColaborador(item.id);
      if (form.id === item.id) fecharForm();
      setAviso(`${item.name} foi excluído.`);
      await carregar();
    } catch (err) {
      setAviso(err instanceof Error ? err.message : "Não consegui excluir.");
    }
  }

  return (
    <section className="cadastro com-chat">
      <div className="conteudo">
        <div className="colaboradores-lista">
          <header className="dt-toolbar no-print">
            <div className="dt-toolbar-esq">
              <h1>Colaboradores</h1>
              <button className="primary" type="button" onClick={abrirNovo}>
                Novo
              </button>
            </div>
            <form
              className="dt-toolbar-dir"
              onSubmit={(event) => {
                event.preventDefault();
                void carregar(filtro, papelFiltro);
              }}
            >
              <label className="dt-busca">
                Buscar
                <input
                  value={filtro}
                  onChange={(event) => setFiltro(event.target.value)}
                  placeholder="Nome, telefone ou endereço"
                  aria-label="Buscar"
                />
              </label>
              <select
                value={papelFiltro}
                onChange={(event) => setPapelFiltro(event.target.value as PapelColaborador | "")}
                aria-label="Filtrar função"
              >
                <option value="">Todas as funções</option>
                {PAPEIS.map((papel) => (
                  <option key={papel.id} value={papel.id}>
                    {papel.label}
                  </option>
                ))}
              </select>
              <button type="submit" disabled={carregando}>
                {carregando ? "…" : "Filtrar"}
              </button>
            </form>
          </header>

          {aviso ? <p className="dt-aviso no-print">{aviso}</p> : null}
          {pendente ? (
            <p className="dt-aviso no-print">Alteração do chat no formulário — confirme no chat para gravar.</p>
          ) : null}

          <div className="dt-tabela-wrap">
            <table className="grade dt-tabela">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>WhatsApp</th>
                  <th>Funções</th>
                  <th>Endereço</th>
                  <th>Localização</th>
                  <th>Status</th>
                  <th className="no-print" />
                </tr>
              </thead>
              <tbody>
                {lista.length === 0 ? (
                  <tr>
                    <td colSpan={7}>{carregando ? "Carregando…" : "Nenhum colaborador cadastrado."}</td>
                  </tr>
                ) : (
                  linhasTabela.map((linha) =>
                    linha.tipo === "grupo" ? (
                      <tr key={`grupo-${linha.role}`} className="dt-grupo">
                        <td colSpan={7}>{labelPapel(linha.role)}</td>
                      </tr>
                    ) : (
                      <tr
                        key={linha.item.id}
                        className={
                          formAberto && form.id === linha.item.id ? "destaque" : undefined
                        }
                      >
                        <td>{linha.item.name}</td>
                        <td>{showPhone(linha.item.phone_e164)}</td>
                        <td>
                          <span className="dt-tags">
                            {rolesDe(linha.item).map((role) => (
                              <span key={role} className={`dt-tag dt-tag-${role}`}>
                                {labelPapel(role)}
                              </span>
                            ))}
                          </span>
                        </td>
                        <td>{linha.item.endereco || "—"}</td>
                        <td>
                          {linha.item.localizacao ? (
                            <a href={linha.item.localizacao} target="_blank" rel="noreferrer">
                              Maps
                            </a>
                          ) : (
                            "—"
                          )}
                        </td>
                        <td>
                          <span
                            className={
                              linha.item.active ? "dt-status-ativo" : "dt-status-inativo"
                            }
                          >
                            {linha.item.active ? "Ativo" : "Inativo"}
                          </span>
                        </td>
                        <td className="no-print acoes-icone">
                          <IconeBotao
                            nome="editar"
                            titulo="Editar"
                            onClick={() => editar(linha.item)}
                          />
                          {linha.item.active ? (
                            <IconeBotao
                              nome="inativar"
                              titulo="Inativar"
                              onClick={() => void inativar(linha.item)}
                            />
                          ) : null}
                          <IconeBotao
                            nome="excluir"
                            titulo="Excluir"
                            onClick={() => void excluir(linha.item)}
                          />
                        </td>
                      </tr>
                    ),
                  )
                )}
              </tbody>
            </table>
            <p className="dt-rodape no-print">
              {carregando
                ? "Atualizando…"
                : `${lista.length} ${lista.length === 1 ? "colaborador" : "colaboradores"}`}
            </p>
          </div>

          {formAberto ? (
            <aside className="popup-colaborador no-print" aria-label={form.id ? "Editar colaborador" : "Novo colaborador"}>
              <header>
                <strong>{form.id ? "Editar colaborador" : "Novo colaborador"}</strong>
                <button type="button" className="icone-acao" title="Fechar" aria-label="Fechar" onClick={fecharForm}>
                  ×
                </button>
              </header>
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  void salvarDireto();
                }}
              >
                <label>
                  Nome
                  <input
                    value={form.name}
                    onChange={(event) => aoCampo("name", event.target.value)}
                    autoFocus
                  />
                </label>
                <label>
                  WhatsApp
                  <input
                    value={form.phone}
                    onChange={(event) => aoCampo("phone", event.target.value)}
                    placeholder="62 9…"
                  />
                </label>
                <fieldset className="popup-funcoes">
                  <legend>Funções</legend>
                  {PAPEIS.map((papel) => (
                    <label key={papel.id}>
                      <input
                        type="checkbox"
                        checked={form.roles.includes(papel.id)}
                        onChange={() => alternarFuncao(papel.id)}
                      />{" "}
                      {papel.label}
                    </label>
                  ))}
                </fieldset>
                <label>
                  Endereço
                  <input
                    value={form.endereco}
                    onChange={(event) => aoCampo("endereco", event.target.value)}
                  />
                </label>
                <label>
                  Localização (Maps)
                  <input
                    value={form.localizacao}
                    onChange={(event) => aoCampo("localizacao", event.target.value)}
                    placeholder="https://maps…"
                  />
                </label>
                <label className="popup-ativo">
                  <input
                    type="checkbox"
                    checked={form.active}
                    onChange={(event) => aoCampo("active", event.target.checked)}
                  />{" "}
                  Ativo
                </label>
                {erroForm ? <p className="error">{erroForm}</p> : null}
                {pendente ? (
                  <p className="popup-pendente">Veio do chat — confirme lá ou salve aqui.</p>
                ) : null}
                <div className="popup-acoes">
                  <button className="primary" type="submit" disabled={salvando || pendente}>
                    {salvando ? "Salvando…" : form.id ? "Salvar" : "Cadastrar"}
                  </button>
                  <button type="button" disabled={salvando} onClick={fecharForm}>
                    Cancelar
                  </button>
                </div>
              </form>
            </aside>
          ) : null}
        </div>
      </div>

      <CadastroChat
        pending={pendente}
        saving={salvando}
        onSend={onChat}
        onConfirm={confirmarChat}
        onDiscard={descartarChat}
        intro="Lista no centro. Novo abre o formulário. Ex.: Maurão é dono, colheiteiro, entregador e granjeiro. Digite quem é entregador para ver quem recebe a mensagem."
        placeholder="Maurão é dono, colheiteiro, entregador e granjeiro"
      />
    </section>
  );
}
