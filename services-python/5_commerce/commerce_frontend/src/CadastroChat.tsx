import { useState } from "react";

type Mensagem = { papel: "voce" | "bot"; texto: string };

export function CadastroChat({
  pending,
  saving,
  onSend,
  onConfirm,
  onDiscard,
}: {
  pending: boolean;
  saving: boolean;
  onSend: (text: string) => Promise<string>;
  onConfirm: () => Promise<void>;
  onDiscard: () => void;
}) {
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [mensagens, setMensagens] = useState<Mensagem[]>([
    {
      papel: "bot",
      texto:
        "Pode pedir a alteração. Exemplo: atualiza o celular da Waldeth para 62 981414141. A tela muda na hora e só grava quando você confirmar.",
    },
  ]);

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
      const motivo = err instanceof Error ? err.message : "Não consegui ler o comando";
      setMensagens((atual) => [...atual, { papel: "bot", texto: motivo }]);
    } finally {
      setEnviando(false);
    }
  }

  async function confirmar() {
    try {
      await onConfirm();
      setMensagens((atual) => [...atual, { papel: "bot", texto: "Gravei." }]);
    } catch (err) {
      const motivo = err instanceof Error ? err.message : "Não salvou";
      setMensagens((atual) => [...atual, { papel: "bot", texto: motivo }]);
    }
  }

  return (
    <aside className="chat-lado">
      <h2>Chat</h2>
      <div className="chat-log">
        {mensagens.map((mensagem, index) => (
          <p key={index} className={`balao ${mensagem.papel}`}>
            {mensagem.texto}
          </p>
        ))}
      </div>
      {pending ? (
        <div className="confirmar">
          <p>A tela já mostra a alteração. Confirme para salvar.</p>
          <div className="linha">
            <button className="primary" type="button" disabled={saving} onClick={confirmar}>
              {saving ? "Salvando…" : "Confirmar"}
            </button>
            <button type="button" disabled={saving} onClick={onDiscard}>
              Descartar
            </button>
          </div>
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
          placeholder="Atualiza o celular da Waldeth para 62 981414141"
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
