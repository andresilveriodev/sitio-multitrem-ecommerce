import type { ReactNode } from "react";
import type { Tela } from "./preferenciaArea";

type Item = {
  id: string;
  titulo: string;
  icone: IconeNome;
  tela?: Tela;
};

const GRUPOS: Item[][] = [
  [{ id: "pedidos", titulo: "Pedidos", icone: "pedidos", tela: "pedidos" }],
  [
    { id: "clientes", titulo: "Clientes", icone: "clientes", tela: "clientes" },
    { id: "precos", titulo: "Preços", icone: "precos", tela: "tabelas" },
    { id: "colaboradores", titulo: "Colaboradores", icone: "colaboradores", tela: "colaboradores" },
    { id: "contexto", titulo: "Contexto da IA", icone: "contexto", tela: "contexto" },
  ],
  [
    { id: "funil", titulo: "Funil de vendas", icone: "funil", tela: "funil" },
  ],
  [
    { id: "contas", titulo: "Contas", icone: "contas", tela: "contas" },
    { id: "receber", titulo: "A receber", icone: "receber" },
    { id: "pagar", titulo: "A pagar", icone: "pagar" },
  ],
  [
    { id: "whatsapp", titulo: "WhatsApp", icone: "conversa" },
    { id: "instagram", titulo: "Instagram", icone: "instagram" },
    { id: "telegram", titulo: "Telegram", icone: "telegram" },
  ],
];

type Props = {
  tela: Tela;
  ferramentasAbertas: boolean;
  onTela: (tela: Tela) => void;
  onFerramentas: (abertas: boolean) => void;
  children: ReactNode;
};

export function AreaTrabalho({ tela, ferramentasAbertas, onTela, onFerramentas, children }: Props) {
  return (
    <div className="area-casco no-print">
      <nav className="trilho" aria-label="Menu">
        {GRUPOS.map((grupo, indice) => (
          <div className="trilho-grupo" key={grupo[0].id}>
            {indice > 0 ? <span className="trilho-separador" /> : null}
            {grupo.map((item) =>
              item.tela ? (
                <button
                  key={item.id}
                  type="button"
                  className={tela === item.tela ? "ativo" : undefined}
                  title={item.titulo}
                  aria-label={item.titulo}
                  aria-current={tela === item.tela ? "page" : undefined}
                  onClick={() => onTela(item.tela as Tela)}
                >
                  <Icone nome={item.icone} />
                </button>
              ) : (
                <button
                  key={item.id}
                  type="button"
                  className="reservado"
                  title={item.titulo}
                  aria-label={item.titulo}
                  disabled
                >
                  <Icone nome={item.icone} />
                </button>
              ),
            )}
          </div>
        ))}
      </nav>
      {ferramentasAbertas ? (
        <aside className="painel-ferramentas" aria-label="Ferramentas">
          <header>
            <strong>Ferramentas</strong>
            <button
              type="button"
              title="Recolher ferramentas"
              aria-label="Recolher ferramentas"
              aria-expanded={true}
              onClick={() => onFerramentas(false)}
            >
              <Icone nome="recolher" />
            </button>
          </header>
          {children}
        </aside>
      ) : (
        <button
          type="button"
          className="painel-ferramentas-toggle"
          title="Expandir ferramentas"
          aria-label="Expandir ferramentas"
          aria-expanded={false}
          onClick={() => onFerramentas(true)}
        >
          <Icone nome="expandir" />
        </button>
      )}
    </div>
  );
}

export function IconeAcao({
  nome,
}: {
  nome:
    | "atualizar"
    | "imprimir"
    | "cobranca"
    | "colheita"
    | "rota"
    | "salvar"
    | "duplicar"
    | "limpar"
    | "whatsapp";
}) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      {nome === "atualizar" ? (
        <path d="M3 8a5 5 0 0 1 8.5-3.5M13 3.5V7H9.5M13 8a5 5 0 0 1-8.5 3.5M3 12.5V9h3.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
      {nome === "whatsapp" ? (
        <path
          d="M8 2.2a5.8 5.8 0 0 0-5 8.7L2.2 13.8l3-0.8A5.8 5.8 0 1 0 8 2.2Zm3.2 8.3c-.1.4-.7.7-1.1.8-.3.1-.7.1-1.1 0-1.7-.4-3-1.7-3.5-3.3-.1-.3 0-.7.1-1 .1-.3.4-.5.7-.6h.5c.2 0 .3 0 .4.3l.5 1.2c.1.2 0 .3-.1.5l-.2.3c-.1.1-.2.3-.1.4.3.5.8 1 1.3 1.3.2.1.3.1.4 0l.4-.4c.1-.1.3-.1.4 0l1 .5c.2.1.3.2.3.4 0 .2-.1.5-.3.6Z"
          fill="currentColor"
        />
      ) : null}
      {nome === "imprimir" ? (
        <>
          <path d="M4 6V2.5h8V6" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <rect x="3" y="6" width="10" height="5" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5 11h6v3H5v-3Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "cobranca" ? (
        <>
          <rect x="3" y="2.5" width="10" height="11" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M6 6.5h4M6 9h2.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "colheita" ? (
        <path d="M8 13.5V8M8 8c0-3 2.5-5 5-5-0.5 3-2 5-5 5Zm0 0c0-3-2.5-5-5-5 0.5 3 2 5 5 5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
      {nome === "rota" ? (
        <>
          <circle cx="4" cy="4" r="1.4" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="12" cy="12" r="1.4" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.2 5.2 10.8 10.8" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "salvar" ? (
        <>
          <path d="M3 2.5h8l2 2V13.5H3V2.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.5 2.5V6h5" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "duplicar" ? (
        <>
          <path d="M2.2 2.4h5.2l1.6 1.6v5.8H2.2V2.4z" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M4.2 4.2h1.8M4.2 5.8h2.4M4.2 7.4h1.6" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M6.2 5.2h5.2l1.6 1.6v5.8H6.2V5.2z" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M8 8.4h2.6M8 10h2.6M8 11.6h1.8" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M3.4 11.2c.4 1.6 1.8 2.4 3.4 2.4" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.6 12.4 6.8 13.6 5.4 14.2" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "limpar" ? (
        <>
          <path d="M3.5 5.5h9" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M6 5.5V3.5h4v2" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M4.5 5.5 5.2 13h5.6l.7-7.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
    </svg>
  );
}

type IconeNome =
  | "pedidos"
  | "clientes"
  | "precos"
  | "colaboradores"
  | "contexto"
  | "funil"
  | "contas"
  | "receber"
  | "pagar"
  | "conversa"
  | "instagram"
  | "telegram"
  | "expandir"
  | "recolher";

function Icone({ nome }: { nome: IconeNome }) {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      {nome === "pedidos" ? (
        <>
          <rect x="3" y="2" width="10" height="12" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.5 6h5M5.5 8.5h5M5.5 11h3" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "clientes" ? (
        <>
          <circle cx="8" cy="5.2" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M3.5 13.2c.8-2.2 2.4-3.2 4.5-3.2s3.7 1 4.5 3.2" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "precos" ? (
        <>
          <path d="M3 8.5 7.5 3H13v5.5L8.5 13 3 8.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="10.5" cy="5.5" r="0.8" fill="currentColor" />
        </>
      ) : null}
      {nome === "contexto" ? (
        <>
          <path d="M3 3.5h7.5L13 6v6.5H3V3.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M10.5 3.5V6H13" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5 8h4M5 10.2h3" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "colaboradores" ? (
        <>
          <circle cx="5.5" cy="5" r="1.8" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="10.5" cy="5" r="1.8" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M2.2 13c.5-2 1.8-3 3.3-3s2.8 1 3.3 3" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M7.2 13c.5-2 1.8-3 3.3-3s2.8 1 3.3 3" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "funil" ? (
        <path
          d="M3 3.5h10l-3.5 5v4L7 14v-5.5L3 3.5Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.4"
        />
      ) : null}
      {nome === "contas" ? (
        <>
          <rect x="2.5" y="4" width="11" height="8" rx="1" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M2.5 7h11" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "receber" ? (
        <>
          <path d="M8 2.5v7" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5 7.5 8 10.5 11 7.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M3.5 13h9" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "pagar" ? (
        <>
          <path d="M8 13.5v-7" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5 8.5 8 5.5 11 8.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M3.5 3h9" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </>
      ) : null}
      {nome === "conversa" ? (
        <path d="M3 3.5h10v7H6.5L3 13V3.5Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
      {nome === "instagram" ? (
        <>
          <rect x="3" y="3" width="10" height="10" rx="2.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="8" cy="8" r="2.2" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <circle cx="11" cy="5" r="0.6" fill="currentColor" />
        </>
      ) : null}
      {nome === "telegram" ? (
        <path d="M2.5 8 13.5 3 11 13.2 7.8 9.2 2.5 8Zm5.3 1.2 4.2-4" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
      {nome === "expandir" ? (
        <path d="M6 3.5 11 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
      {nome === "recolher" ? (
        <path d="M10 3.5 5 8 10 12.5" fill="none" stroke="currentColor" strokeWidth="1.4" />
      ) : null}
    </svg>
  );
}
