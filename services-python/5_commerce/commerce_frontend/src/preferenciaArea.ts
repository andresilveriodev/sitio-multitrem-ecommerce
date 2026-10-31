export type Tela = "pedidos" | "clientes" | "tabelas" | "contas" | "funil" | "colaboradores" | "contexto";

const TELAS: Tela[] = ["pedidos", "clientes", "tabelas", "contas", "funil", "colaboradores", "contexto"];
const CHAVE = "sitio-area-trabalho";

export type AreaLocal = {
  tela: Tela;
  chatAberto: boolean;
  ferramentasAbertas: boolean;
};

export function telaValida(valor: string): valor is Tela {
  return TELAS.includes(valor as Tela);
}

export function lerAreaLocal(): AreaLocal | null {
  try {
    if (typeof localStorage === "undefined") return null;
    const raw = localStorage.getItem(CHAVE);
    if (!raw) return null;
    const data = JSON.parse(raw) as Partial<AreaLocal>;
    if (typeof data.tela !== "string" || !telaValida(data.tela)) return null;
    return {
      tela: data.tela,
      chatAberto: data.chatAberto !== false,
      ferramentasAbertas: data.ferramentasAbertas === true,
    };
  } catch {
    return null;
  }
}

export function gravarAreaLocal(area: AreaLocal): void {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(CHAVE, JSON.stringify(area));
  } catch {
    /* quota / modo privado */
  }
}
