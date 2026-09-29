import { useEffect, useRef, useState } from "react";
import type { ClienteOpcao, ClienteParaIncluir } from "./pedidoConversa";

type Mensagem = { papel: "voce" | "bot"; texto: string };

export function PedidoChat({
  aberto,
  aviso,
  novos,
  opcoes,
  decidir,
  onDecidir,
  onEscolher,
  onIncluir,
  onToggle,
  onSend,
}: {
  aberto: boolean;
  aviso: { id: number; texto: string } | null;
  novos: ClienteParaIncluir[];
  opcoes: ClienteOpcao[];
  decidir: boolean;
  onDecidir: (modo: "atualizar" | "inserir") => void;
  onEscolher: (id: number) => void;
  onIncluir: (cliente: ClienteParaIncluir) => void;
  onToggle: () => void;
  onSend: (texto: string) => Promise<string>;
}) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [mensagens, setMensagens] = useState<Mensagem[]>([
    {
      papel: "bot",
      texto: "Cole a conversa do WhatsApp. Eu leio, respondo aqui e a nota aparece à esquerda para você corrigir.",
    },
  ]);
  const fim = useRef<HTMLDivElement>(null);
  const avisoVisto = useRef(0);

  useEffect(() => {
    fim.current?.scrollIntoView({ block: "end" });
  }, [mensagens, enviando, aberto]);

  useEffect(() => {
    if (!aviso || aviso.id === avisoVisto.current || !aviso.texto) return;
    avisoVisto.current = aviso.id;
    setMensagens((atual) => [...atual, { papel: "bot", texto: aviso.texto }]);
  }, [aviso]);

  async function enviar() {
    const frase = texto.trim();
    if (!frase || enviando) return;
    setTexto("");
    setMensagens((atual) => [...atual, { papel: "voce", texto: frase }]);
    setEnviando(true);
    try {
      const resposta = await onSend(frase);
      setMensagens((atual) => [...atual, { papel: "bot", texto: resposta }]);
    } catch (err) {
      const motivo = err instanceof Error ? err.message : "Não consegui ler a conversa";
      setMensagens((atual) => [...atual, { papel: "bot", texto: motivo }]);
    } finally {
      setEnviando(false);
    }
  }

  if (!aberto) {
    return (
      <button className="pedido-abrir no-print" type="button" onClick={onToggle}>
        Incluir pedido
      </button>
    );
  }

  return (
    <aside className="pedido-popup no-print">
      <header>
        <strong>Incluir pedido</strong>
        <button type="button" onClick={onToggle}>
          Fechar
        </button>
      </header>
      <div className="chat-log">
        {mensagens.map((mensagem, index) => (
          <p key={index} className={`balao ${mensagem.papel}`}>
            {mensagem.texto}
          </p>
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
                setMensagens((atual) => [...atual, { papel: "voce", texto: `${opcao.nome}\n${opcao.detalhe}` }]);
                onEscolher(opcao.id);
              }}
            >
              {opcao.nome}
              <small>{opcao.detalhe}</small>
            </button>
          ))}
        </div>
      ) : null}
      {decidir ? (
        <div className="pedido-opcoes">
          <button
            type="button"
            onClick={() => {
              setMensagens((atual) => [...atual, { papel: "voce", texto: "Atualizar a listagem" }]);
              onDecidir("atualizar");
            }}
          >
            Atualizar a listagem
          </button>
          <button
            type="button"
            onClick={() => {
              setMensagens((atual) => [...atual, { papel: "voce", texto: "Inserir o novo pedido" }]);
              onDecidir("inserir");
            }}
          >
            Inserir o novo pedido
          </button>
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
                setMensagens((atual) => [
                  ...atual,
                  {
                    papel: "bot",
                    texto: `Abri o cadastro de ${cliente.nome}. Complete celular, endereço e localização e confirme.`,
                  },
                ]);
                onIncluir(cliente);
              }}
            >
              Incluir {cliente.nome}
            </button>
          ))}
        </div>
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
    </aside>
  );
}
