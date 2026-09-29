import type { ConvertResponse } from "./types";

const BOT_URL = import.meta.env.VITE_BOT_URL ?? "http://localhost:8011";

export async function convertConversation(conversation: string): Promise<ConvertResponse> {
  const url = `${BOT_URL}/chatbot/orders/from-conversation`;
  const origin = window.location.origin;
  console.info("[commerce-frontend] POST", url, { origin, chars: conversation.length });
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation }),
    });
  } catch (err) {
    const reason = err instanceof Error ? err.message : String(err);
    console.error("[commerce-frontend] rede", { url, origin, reason, err });
    throw new Error(
      `Não alcançou o bot em ${url}. Tela em ${origin}. ${reason}. Confira se o chatbot está na porta 8011 e se essa origem está liberada.`,
    );
  }
  const body = await response.json().catch(() => ({}));
  console.info("[commerce-frontend] resposta", response.status, body);
  if (!response.ok) {
    const detail = typeof body.detail === "string" ? body.detail : "Não foi possível converter a conversa";
    console.error("[commerce-frontend] HTTP", response.status, detail);
    throw new Error(`${response.status}: ${detail}`);
  }
  return body as ConvertResponse;
}
