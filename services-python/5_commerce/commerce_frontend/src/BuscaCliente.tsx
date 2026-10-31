import { useEffect, useRef, useState } from "react";
import { buscarClientes, type ClienteBusca } from "./cadastroApi";

type Props = {
  nome: string;
  onChange: (id: string, nome: string) => void;
};

export function BuscaCliente({ nome, onChange }: Props) {
  const [texto, setTexto] = useState(nome);
  const [sugestoes, setSugestoes] = useState<ClienteBusca[]>([]);
  const [aberto, setAberto] = useState(false);
  const [consultou, setConsultou] = useState(false);
  const pedido = useRef(0);

  useEffect(() => {
    setTexto(nome);
  }, [nome]);

  useEffect(() => {
    const consulta = texto.trim();
    if (consulta.length < 2 || consulta === nome.trim()) {
      setSugestoes([]);
      setConsultou(false);
      return;
    }
    const seq = ++pedido.current;
    setConsultou(false);
    const timer = window.setTimeout(() => {
      buscarClientes(consulta)
        .then((lista) => {
          if (seq !== pedido.current) return;
          setSugestoes(lista);
          setConsultou(true);
        })
        .catch(() => {
          if (seq !== pedido.current) return;
          setSugestoes([]);
          setConsultou(true);
        });
    }, 200);
    return () => window.clearTimeout(timer);
  }, [texto, nome]);

  function escolher(cliente: ClienteBusca) {
    setTexto(cliente.name);
    setSugestoes([]);
    setAberto(false);
    onChange(String(cliente.id), cliente.name);
  }

  function digitar(valor: string) {
    setTexto(valor);
    setAberto(true);
    if (!valor.trim()) onChange("", "");
    else if (valor.trim() !== nome.trim()) onChange("", valor);
  }

  function limpar() {
    setTexto("");
    setSugestoes([]);
    setAberto(false);
    setConsultou(false);
    onChange("", "");
  }

  return (
    <div className="busca-cliente">
      <input
        aria-label="Cliente"
        placeholder="Cliente"
        title="Digite a razão social ou o nome de um responsável."
        value={texto}
        autoComplete="off"
        onChange={(event) => digitar(event.target.value)}
        onFocus={() => setAberto(true)}
        onBlur={() => window.setTimeout(() => setAberto(false), 150)}
        onKeyDown={(event) => {
          if (event.key === "Escape") setAberto(false);
          if (event.key === "Enter" && aberto && sugestoes.length) {
            event.preventDefault();
            escolher(sugestoes[0]);
          }
        }}
      />
      {texto ? (
        <button
          type="button"
          className="limpar"
          title="Apagar"
          aria-label="Apagar texto da pesquisa"
          onMouseDown={(event) => event.preventDefault()}
          onClick={limpar}
        >
          ×
        </button>
      ) : null}
      {aberto && texto.trim().length >= 2 && texto.trim() !== nome.trim() && (sugestoes.length > 0 || consultou) ? (
        <ul>
          {consultou && sugestoes.length === 0 ? (
            <li className="vazio">Nenhum cliente com esse nome.</li>
          ) : (
            sugestoes.map((cliente) => (
              <li key={cliente.id}>
                <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => escolher(cliente)}>
                  {cliente.name}
                  {cliente.detalhe ? <small>responsável {cliente.detalhe}</small> : null}
                </button>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  );
}
