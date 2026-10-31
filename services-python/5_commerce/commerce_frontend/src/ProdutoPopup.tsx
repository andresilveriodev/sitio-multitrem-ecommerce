import { useEffect, useId, useMemo, useState } from "react";
import type { Lista, Produto } from "./cadastroApi";
import { lerReais, mesmoNome, normalizarFormato, separarFormato, formatarReais } from "./rascunho";
import type { OrderItem } from "./types";

const FORMATOS = ["unidade", "maço", "kg", "peso fixo"];

export type AberturaProduto = {
  origem: string;
  nome: string;
  formato: string;
  tabela: string;
};

export type ProdutoSalvo = {
  origem: string;
  nome: string;
  formato: string;
  precos: Record<number, number>;
};

export function aberturaDoItem(item: OrderItem, tabela: string): AberturaProduto {
  const partes = separarFormato(item.produto);
  const formato = normalizarFormato(item.tipo || partes.formato || "unidade");
  return {
    origem: item.produto,
    nome: (partes.nome || item.produto).trim(),
    formato: FORMATOS.includes(formato) ? formato : formato || "unidade",
    tabela,
  };
}

function acharProduto(produtos: Produto[], nome: string, formato: string): Produto | undefined {
  const alvo = normalizarFormato(formato);
  return produtos.find(
    (item) => mesmoNome(item.name, nome) && normalizarFormato(item.formato || "unidade") === alvo,
  );
}

export function ProdutoPopup({
  abertura,
  listas,
  produtos,
  onFechar,
  onSalvar,
}: {
  abertura: AberturaProduto;
  listas: Lista[];
  produtos: Produto[];
  onFechar: () => void;
  onSalvar: (dados: ProdutoSalvo) => Promise<void>;
}) {
  const tituloId = useId();
  const [nome, setNome] = useState(abertura.nome);
  const [formato, setFormato] = useState(FORMATOS.includes(abertura.formato) ? abertura.formato : "outro");
  const [outro, setOutro] = useState(FORMATOS.includes(abertura.formato) ? "" : abertura.formato);
  const [precos, setPrecos] = useState<Record<number, string>>({});
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);
  const formatoFinal = formato === "outro" ? outro.trim() : formato;
  const existente = useMemo(
    () => acharProduto(produtos, nome.trim(), formatoFinal),
    [produtos, nome, formatoFinal],
  );
  const tabelaNota = listas.find((lista) => mesmoNome(lista.name, abertura.tabela));

  useEffect(() => {
    const proximos: Record<number, string> = {};
    if (existente) {
      for (const lista of listas) {
        const valor = existente.precos[String(lista.id)];
        if (valor > 0) proximos[lista.id] = formatarReais(valor);
      }
    }
    setPrecos(proximos);
  }, [existente, listas]);

  useEffect(() => {
    function tecla(event: KeyboardEvent) {
      if (event.key === "Escape" && !salvando) onFechar();
    }
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [onFechar, salvando]);

  async function salvar() {
    if (!nome.trim() || !formatoFinal) {
      setErro("Informe o nome e o formato.");
      return;
    }
    const gravados: Record<number, number> = {};
    for (const lista of listas) {
      const raw = (precos[lista.id] || "").trim();
      if (!raw) continue;
      const valor = lerReais(raw);
      if (Number.isNaN(valor) || valor < 0) {
        setErro(`O preço de ${lista.name} não é um valor válido.`);
        return;
      }
      if (valor > 0) gravados[lista.id] = valor;
    }
    if (tabelaNota && !(gravados[tabelaNota.id] > 0)) {
      setErro(`Informe o preço de ${tabelaNota.name}. É a tabela desta nota.`);
      return;
    }
    if (!tabelaNota && !Object.keys(gravados).length) {
      setErro("Informe ao menos um preço.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      await onSalvar({
        origem: abertura.origem,
        nome: nome.trim(),
        formato: normalizarFormato(formatoFinal),
        precos: gravados,
      });
    } catch (err) {
      setErro(err instanceof Error ? err.message : "Não salvou o produto");
      setSalvando(false);
    }
  }

  return (
    <div
      className="produto-popup-fundo"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !salvando) onFechar();
      }}
    >
      <form
        className="produto-popup"
        role="dialog"
        aria-modal="true"
        aria-labelledby={tituloId}
        onSubmit={(event) => {
          event.preventDefault();
          void salvar();
        }}
      >
        <h2 id={tituloId}>{existente ? "Preço do produto" : "Incluir produto"}</h2>
        <p>
          {existente
            ? "Este produto já está no cadastro. Complete o preço que falta."
            : "O produto entra no cadastro e o preço da tabela desta nota volta para a linha."}
        </p>
        {erro ? <p className="error">{erro}</p> : null}
        <label className="campo">
          Nome
          <input aria-label="Nome do produto" value={nome} onChange={(event) => setNome(event.target.value)} />
        </label>
        <label className="campo">
          Formato
          <select
            aria-label="Formato"
            value={formato}
            onChange={(event) => setFormato(event.target.value)}
          >
            {FORMATOS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
            <option value="outro">outro</option>
          </select>
        </label>
        {formato === "outro" ? (
          <label className="campo">
            Outro formato
            <input
              aria-label="Outro formato"
              placeholder="Ex.: c/ 03 unidades"
              value={outro}
              onChange={(event) => setOutro(event.target.value)}
            />
          </label>
        ) : null}
        <p className="origem">Se a quantidade foi em quilo, o formato é kg.</p>
        <div className="precos-novos">
          {listas.map((lista) => (
            <label key={lista.id} className="preco-novo">
              <span>
                {lista.name}
                {tabelaNota?.id === lista.id ? " · esta nota" : ""}
              </span>
              <input
                inputMode="decimal"
                placeholder="0,00"
                aria-label={`Preço ${lista.name}`}
                autoFocus={tabelaNota?.id === lista.id}
                value={precos[lista.id] ?? ""}
                onChange={(event) => setPrecos((atual) => ({ ...atual, [lista.id]: event.target.value }))}
              />
            </label>
          ))}
        </div>
        <div className="actions">
          <button className="primary" type="submit" disabled={salvando}>
            {salvando ? "Salvando…" : existente ? "Salvar preço" : "Incluir"}
          </button>
          <button type="button" onClick={onFechar} disabled={salvando}>
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
