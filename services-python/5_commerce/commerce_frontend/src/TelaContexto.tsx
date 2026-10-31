import { useEffect, useState } from "react";
import {
  carregarContextosIa,
  invalidarContextosIa,
  montarContexto,
  salvarContextoIa,
  type ContextoTela,
} from "./contextoIa";

const EXEMPLO = {
  cliente: "Sandu Uai",
  data: "28/10",
  tabela: "Restaurantes",
  endereco: "12ª Avenida, Praça São Francisco, 148",
};

type Props = { ativo: boolean };

export function ContextoIa({ ativo }: Props) {
  const [lista, setLista] = useState<ContextoTela[]>([]);
  const [tela, setTela] = useState("funil");
  const [instrucao, setInstrucao] = useState("");
  const [clienteDaTela, setClienteDaTela] = useState(false);
  const [observacaoCom, setObservacaoCom] = useState(false);
  const [aviso, setAviso] = useState("");
  const [erro, setErro] = useState("");
  const [gravando, setGravando] = useState(false);

  useEffect(() => {
    if (!ativo) return;
    let vivo = true;
    invalidarContextosIa();
    carregarContextosIa()
      .then((itens) => {
        if (!vivo || !itens.length) return;
        setLista(itens);
        const atual = itens.find((item) => item.tela === tela) ?? itens[0];
        setTela(atual.tela);
        setInstrucao(atual.instrucao);
        setClienteDaTela(atual.cliente_da_tela);
        setObservacaoCom(atual.observacao_com);
      })
      .catch((err: unknown) => {
        if (!vivo) return;
        setErro(err instanceof Error ? err.message : "Não carreguei o contexto das telas");
      });
    return () => {
      vivo = false;
    };
    // A lista abre na tela que já estava selecionada.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ativo]);

  function abrir(item: ContextoTela) {
    setTela(item.tela);
    setInstrucao(item.instrucao);
    setClienteDaTela(item.cliente_da_tela);
    setObservacaoCom(item.observacao_com);
    setAviso("");
    setErro("");
  }

  async function salvar() {
    setGravando(true);
    setAviso("");
    setErro("");
    try {
      const salvo = await salvarContextoIa(tela, {
        instrucao,
        cliente_da_tela: clienteDaTela,
        observacao_com: observacaoCom,
      });
      setLista((atual) => atual.map((item) => (item.tela === salvo.tela ? salvo : item)));
      setAviso(`Contexto de ${salvo.titulo} salvo. A próxima frase desta tela já usa este texto.`);
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não salvei o contexto");
    } finally {
      setGravando(false);
    }
  }

  const titulo = lista.find((item) => item.tela === tela)?.titulo ?? "Tela";

  return (
    <div className="contexto-ia">
      <header className="contexto-ia-topo">
        <h1>Contexto da IA</h1>
        <p>
          O texto de cada tela vai junto com a frase. {"{cliente}"}, {"{data}"}, {"{tabela}"} e {"{endereco}"}{" "}
          são trocados pelo que estiver aberto na hora.
        </p>
      </header>
      <div className="contexto-ia-corpo">
        <ul className="contexto-ia-telas">
          {lista.map((item) => (
            <li key={item.tela}>
              <button type="button" className={item.tela === tela ? "primary" : undefined} onClick={() => abrir(item)}>
                {item.titulo}
              </button>
            </li>
          ))}
        </ul>
        <div className="contexto-ia-editor">
          <h2>{titulo}</h2>
          <label className="contexto-ia-marca">
            <input type="checkbox" checked={clienteDaTela} onChange={(event) => setClienteDaTela(event.target.checked)} />
            Os pedidos da frase ficam no cliente que já está aberto nesta tela
          </label>
          <label className="contexto-ia-marca">
            <input type="checkbox" checked={observacaoCom} onChange={(event) => setObservacaoCom(event.target.checked)} />
            “com a …” é observação do item, não cliente e não produto
          </label>
          <textarea value={instrucao} onChange={(event) => setInstrucao(event.target.value)} spellCheck />
          <p className="contexto-ia-preview-titulo">Exemplo do que segue para a IA</p>
          <pre className="contexto-ia-preview">{montarContexto(instrucao, EXEMPLO)}</pre>
          {aviso ? <p className="contexto-ia-aviso">{aviso}</p> : null}
          {erro ? <p className="contexto-ia-erro">{erro}</p> : null}
          <button type="button" className="primary" disabled={gravando || !lista.length} onClick={() => void salvar()}>
            {gravando ? "Salvando…" : "Salvar"}
          </button>
        </div>
      </div>
    </div>
  );
}
