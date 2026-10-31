export type DiaSemana = "segunda" | "terca" | "quarta" | "quinta" | "sexta" | "sabado" | "domingo";

export type LinhaRecorrente = {
  id: string;
  horario: string;
  dias: Partial<Record<DiaSemana, string>>;
};

export type PlanilhaRecorrente = {
  linhas: LinhaRecorrente[];
  extras: string[];
};

/** Semana da grade: segunda a domingo (domingo sem entrega padrão, mas entra na visão). */
export const DIAS: { id: DiaSemana; rotulo: string }[] = [
  { id: "segunda", rotulo: "Segunda" },
  { id: "terca", rotulo: "Terça" },
  { id: "quarta", rotulo: "Quarta" },
  { id: "quinta", rotulo: "Quinta" },
  { id: "sexta", rotulo: "Sexta" },
  { id: "sabado", rotulo: "Sábado" },
  { id: "domingo", rotulo: "Domingo" },
];

const MAPA_DIA: DiaSemana[] = ["domingo", "segunda", "terca", "quarta", "quinta", "sexta", "sabado"];

const CHAVE = "sitio-pedidos-recorrentes";

/** Planilha inicial tirada da grade manual de avisos. */
export function planilhaPadrao(): PlanilhaRecorrente {
  return {
    linhas: [
      { id: "1", horario: "08h30", dias: { quinta: "kokorikor" } },
      {
        id: "2",
        horario: "08h30",
        dias: {
          segunda: "Ademar",
          terca: "Ademar",
          quarta: "Ademar",
          quinta: "Ademar",
          sexta: "Ademar",
        },
      },
      {
        id: "3",
        horario: "07h-09h30",
        dias: {
          segunda: "Edgar",
          terca: "Edgar",
          quarta: "Edgar",
          quinta: "Edgar",
          sexta: "Edgar",
          sabado: "Edgar",
        },
      },
      {
        id: "4",
        horario: "07h30-08h45",
        dias: { terca: "Dilma", quarta: "Simone", sexta: "Dilma" },
      },
      {
        id: "5",
        horario: "até 10h00",
        dias: {
          segunda: "Emerson",
          terca: "Emerson",
          quarta: "Emerson",
          quinta: "Emerson",
          sexta: "Emerson",
        },
      },
      { id: "6", horario: "07h30-08h45", dias: { segunda: "Alex" } },
      {
        id: "7",
        horario: "",
        dias: {
          segunda: "Will",
          quarta: "Will",
          sabado: "Will (16h00/19h00)",
        },
      },
      { id: "8", horario: "", dias: { sexta: "Brendo" } },
      { id: "9", horario: "", dias: { sexta: "José Carlos" } },
      {
        id: "10",
        horario: "manhã",
        dias: { segunda: "Paulo Tiraboschi", sexta: "Paulo" },
      },
      { id: "11", horario: "manhã", dias: { segunda: "Mariana", sexta: "Mariana" } },
      { id: "12", horario: "manhã", dias: { segunda: "Edileusa", sexta: "Edileusa" } },
      { id: "13", horario: "", dias: {} },
    ],
    extras: ["Tereza Bahia", "Divina Virgulinho", "Gustavo (Mecanica Oriente)"],
  };
}

export function lerPlanilhaRecorrente(): PlanilhaRecorrente {
  try {
    if (typeof localStorage === "undefined") return planilhaPadrao();
    const raw = localStorage.getItem(CHAVE);
    if (!raw) return planilhaPadrao();
    const data = JSON.parse(raw) as Partial<PlanilhaRecorrente>;
    if (!Array.isArray(data.linhas)) return planilhaPadrao();
    return {
      linhas: data.linhas.map((linha, index) => ({
        id: String(linha.id || index + 1),
        horario: String(linha.horario || ""),
        dias: linha.dias && typeof linha.dias === "object" ? linha.dias : {},
      })),
      extras: Array.isArray(data.extras) ? data.extras.map((nome) => String(nome)) : [],
    };
  } catch {
    return planilhaPadrao();
  }
}

export function gravarPlanilhaRecorrente(planilha: PlanilhaRecorrente): void {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.setItem(CHAVE, JSON.stringify(planilha));
  } catch {
    /* quota / modo privado */
  }
}

/** 0=domingo … 6=sábado → dia da planilha do amanhã. */
export function diaDeAmanha(hoje = new Date()): DiaSemana {
  const amanha = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate() + 1);
  return MAPA_DIA[amanha.getDay()] ?? "segunda";
}

export function rotuloDia(dia: DiaSemana): string {
  return DIAS.find((item) => item.id === dia)?.rotulo || dia;
}

export type AvisoAmanha = {
  cliente: string;
  horario: string;
};

export function avisosDeAmanha(planilha: PlanilhaRecorrente, hoje = new Date()): {
  dia: DiaSemana;
  rotulo: string;
  avisos: AvisoAmanha[];
} {
  const dia = diaDeAmanha(hoje);
  const avisos: AvisoAmanha[] = [];
  for (const linha of planilha.linhas) {
    const cliente = (linha.dias[dia] || "").trim();
    if (!cliente) continue;
    avisos.push({ cliente, horario: linha.horario.trim() });
  }
  return { dia, rotulo: rotuloDia(dia), avisos };
}

export function novaLinha(id: string): LinhaRecorrente {
  return { id, horario: "", dias: {} };
}

/** Nome sem horário entre parênteses — para casar com o cadastro. */
export function nomeClienteGrade(valor: string): string {
  return valor.replace(/\s*\([^)]*\)\s*/g, " ").replace(/\s+/g, " ").trim();
}

function isoLocal(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

/** Segunda-feira da semana (offset 0 = semana atual). */
export function segundaDaSemana(offsetSemanas = 0, hoje = new Date()): Date {
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const dia = base.getDay();
  const paraSegunda = dia === 0 ? -6 : 1 - dia;
  base.setDate(base.getDate() + paraSegunda + offsetSemanas * 7);
  return base;
}

export type ColunaSemana = {
  dia: DiaSemana;
  rotulo: string;
  data: Date;
  iso: string;
  curta: string;
};

export function colunasDaSemana(offsetSemanas = 0, hoje = new Date()): ColunaSemana[] {
  const segunda = segundaDaSemana(offsetSemanas, hoje);
  return DIAS.map((item, index) => {
    const data = new Date(segunda.getFullYear(), segunda.getMonth(), segunda.getDate() + index);
    const iso = isoLocal(data);
    const [, mes, dia] = iso.split("-");
    return {
      dia: item.id,
      rotulo: item.rotulo,
      data,
      iso,
      curta: `${dia}/${mes}`,
    };
  });
}

export function somarDiasIso(iso: string, dias: number): string {
  const [ano, mes, dia] = iso.split("-").map(Number);
  if (!ano || !mes || !dia) return "";
  const data = new Date(ano, mes - 1, dia + dias);
  return isoLocal(data);
}

export function rotuloSemana(offsetSemanas = 0, hoje = new Date()): string {
  const cols = colunasDaSemana(offsetSemanas, hoje);
  const primeira = cols[0];
  const ultima = cols[cols.length - 1];
  if (!primeira || !ultima) return "";
  if (offsetSemanas === 0) return `Esta semana · ${primeira.curta} a ${ultima.curta}`;
  if (offsetSemanas === 1) return `Próxima semana · ${primeira.curta} a ${ultima.curta}`;
  if (offsetSemanas === -1) return `Semana passada · ${primeira.curta} a ${ultima.curta}`;
  return `${primeira.curta} a ${ultima.curta}`;
}

export function diaSemanaId(data: Date): DiaSemana {
  return MAPA_DIA[data.getDay()] ?? "segunda";
}

export function isoHoje(hoje = new Date()): string {
  return isoLocal(new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate()));
}

export function foldNomeGrade(valor: string): string {
  return nomeClienteGrade(valor)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/\s+/g, " ")
    .trim();
}

/** Próximo dia da grade (inclui domingo). */
export function proximoDiaGrade(iso: string): string {
  return somarDiasIso(iso, 1);
}

export function diaIdDeIso(iso: string): DiaSemana | null {
  const [ano, mes, dia] = iso.split("-").map(Number);
  if (!ano || !mes || !dia) return null;
  return diaSemanaId(new Date(ano, mes - 1, dia));
}

function nomesDoMesmoCliente(a: string, b: string): boolean {
  const x = foldNomeGrade(a);
  const y = foldNomeGrade(b);
  if (!x || !y) return false;
  if (x === y) return true;
  if (x.length >= 4 && (y.startsWith(x) || x.startsWith(y))) return true;
  return false;
}

/** Tira da grade a razão social repetida no mesmo dia, ficando o nome que mais aparece na semana. */
export function fundirApelidosNaGrade(
  planilha: PlanilhaRecorrente,
  mesmo: (a: string, b: string) => boolean,
): PlanilhaRecorrente | null {
  const linhas = planilha.linhas.map((linha) => ({ ...linha, dias: { ...linha.dias } }));
  const frequencia = new Map<string, number>();
  for (const linha of linhas) {
    for (const dia of DIAS) {
      const nome = (linha.dias[dia.id] || "").trim();
      if (!nome) continue;
      const chave = foldNomeGrade(nome);
      frequencia.set(chave, (frequencia.get(chave) || 0) + 1);
    }
  }
  let mudou = false;
  for (const dia of DIAS) {
    const ocupadas: { index: number; nome: string }[] = [];
    linhas.forEach((linha, index) => {
      const nome = (linha.dias[dia.id] || "").trim();
      if (nome) ocupadas.push({ index, nome });
    });
    const removidas = new Set<number>();
    for (let i = 0; i < ocupadas.length; i += 1) {
      if (removidas.has(ocupadas[i].index)) continue;
      const grupo = [ocupadas[i]];
      for (let j = i + 1; j < ocupadas.length; j += 1) {
        if (removidas.has(ocupadas[j].index)) continue;
        if (mesmo(ocupadas[i].nome, ocupadas[j].nome)) grupo.push(ocupadas[j]);
      }
      if (grupo.length < 2) continue;
      grupo.sort((a, b) => {
        const fa = frequencia.get(foldNomeGrade(a.nome)) || 0;
        const fb = frequencia.get(foldNomeGrade(b.nome)) || 0;
        if (fb !== fa) return fb - fa;
        return a.index - b.index;
      });
      for (const item of grupo.slice(1)) {
        delete linhas[item.index].dias[dia.id];
        removidas.add(item.index);
        mudou = true;
      }
    }
  }
  return mudou ? { ...planilha, linhas } : null;
}

/** Troca o texto da célula quando `rotulo` devolve outro nome. */
export function renomearNaGrade(
  planilha: PlanilhaRecorrente,
  rotulo: (nome: string) => string | null,
): PlanilhaRecorrente | null {
  let mudou = false;
  const linhas = planilha.linhas.map((linha) => {
    const dias = { ...linha.dias };
    for (const dia of DIAS) {
      const atual = (dias[dia.id] || "").trim();
      if (!atual) continue;
      const novo = rotulo(atual);
      if (!novo || foldNomeGrade(novo) === foldNomeGrade(atual)) continue;
      dias[dia.id] = novo;
      mudou = true;
    }
    return { ...linha, dias };
  });
  return mudou ? { ...planilha, linhas } : null;
}

/**
 * Coloca o cliente na lista do dia (grade por horário).
 * Reusa célula vazia do dia; se não houver, cria linha nova sem horário.
 * Retorna null se já estava naquele dia.
 * `mesmo` reconhece razão e dono como o mesmo cliente.
 */
export function incluirClienteNoDia(
  planilha: PlanilhaRecorrente,
  nome: string,
  dia: DiaSemana,
  mesmo: (a: string, b: string) => boolean = nomesDoMesmoCliente,
): PlanilhaRecorrente | null {
  const limpo = nome.trim();
  if (!limpo) return null;
  for (const linha of planilha.linhas) {
    const atual = (linha.dias[dia] || "").trim();
    if (atual && mesmo(atual, limpo)) return null;
  }
  const livre = planilha.linhas.findIndex((linha) => !(linha.dias[dia] || "").trim());
  if (livre >= 0) {
    const linhas = planilha.linhas.map((linha, index) =>
      index === livre ? { ...linha, dias: { ...linha.dias, [dia]: limpo } } : linha,
    );
    return { ...planilha, linhas };
  }
  return {
    ...planilha,
    linhas: [...planilha.linhas, { ...novaLinha(`p-${Date.now()}`), dias: { [dia]: limpo } }],
  };
}
