import type { Colaborador, PapelColaborador } from "./cadastroApi";

export type FormColaborador = {
  id?: number;
  name: string;
  phone: string;
  roles: PapelColaborador[];
  endereco: string;
  localizacao: string;
  active: boolean;
  notes: string;
};

export type ResultadoComando =
  | { tipo: "resposta"; texto: string }
  | { tipo: "formulario"; form: FormColaborador; texto: string; inativar?: boolean };

const PAPEIS: { id: PapelColaborador; palavras: string[] }[] = [
  { id: "dono", palavras: ["dono", "dona", "proprietario", "proprietaria"] },
  { id: "funcionario", palavras: ["funcionario", "funcionaria"] },
  { id: "entregador", palavras: ["entregador", "entregadora", "motoqueiro", "motoqueira"] },
  { id: "colheiteiro", palavras: ["colheiteiro", "colheiteira", "colheita"] },
  { id: "granjeiro", palavras: ["granjeiro", "granjeira", "granja"] },
  {
    id: "separador_pedidos",
    palavras: ["separador de pedidos", "separador", "separadores"],
  },
  { id: "fornecedor", palavras: ["fornecedor", "fornecedora", "fornecedores"] },
];

function fold(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .replace(/\s+/g, " ")
    .trim();
}

function mesmoNome(a: string, b: string): boolean {
  return fold(a) === fold(b);
}

function extrairTelefone(frase: string): string {
  const soDigitos = frase.replace(/\D/g, "");
  if (soDigitos.length >= 10) {
    const match = frase.match(/(?:\+?55\s*)?(?:\(?\d{2}\)?[\s-]*)?(?:9?\d{4}[\s-]?\d{4})/);
    if (match) return match[0].trim();
  }
  return "";
}

function extrairUrl(frase: string): string {
  const match = frase.match(/https?:\/\/\S+/i);
  return match ? match[0].replace(/[),.;]+$/, "") : "";
}

function extrairPapeis(frase: string): PapelColaborador[] {
  const f = fold(frase);
  const achados: PapelColaborador[] = [];
  for (const papel of PAPEIS) {
    if (papel.palavras.some((p) => f.includes(fold(p)))) {
      if (!achados.includes(papel.id)) achados.push(papel.id);
    }
  }
  return achados;
}

function acharPorNome(lista: Colaborador[], nome: string): Colaborador | undefined {
  const alvo = fold(nome);
  if (!alvo) return undefined;
  const exato = lista.find((item) => mesmoNome(item.name, nome));
  if (exato) return exato;
  return lista.find((item) => fold(item.name).includes(alvo) || alvo.includes(fold(item.name)));
}

function labelPapel(role: PapelColaborador): string {
  const mapa: Record<PapelColaborador, string> = {
    dono: "dono",
    funcionario: "funcionário",
    entregador: "entregador",
    colheiteiro: "colheiteiro",
    granjeiro: "granjeiro",
    separador_pedidos: "separador de pedidos",
    fornecedor: "fornecedor",
  };
  return mapa[role] ?? role;
}

function labels(roles: PapelColaborador[]): string {
  return roles.map(labelPapel).join(", ");
}

function rolesDe(item: Colaborador): PapelColaborador[] {
  if (item.roles?.length) return item.roles;
  return item.role ? [item.role] : [];
}

function formDe(item: Colaborador, patch: Partial<FormColaborador> = {}): FormColaborador {
  const digits = item.phone_e164.replace(/\D/g, "");
  const local = digits.startsWith("55") && digits.length > 11 ? digits.slice(2) : digits;
  let phone = item.phone_e164;
  if (local.length === 11) phone = `${local.slice(0, 2)} ${local.slice(2, 7)}-${local.slice(7)}`;
  else if (local.length === 10) phone = `${local.slice(0, 2)} ${local.slice(2, 6)}-${local.slice(6)}`;
  return {
    id: item.id,
    name: item.name,
    phone,
    roles: rolesDe(item),
    endereco: item.endereco ?? "",
    localizacao: item.localizacao ?? "",
    active: item.active,
    notes: item.notes ?? "",
    ...patch,
  };
}

function nomeAposCampo(texto: string, campo: RegExp): string {
  let nome = texto
    .replace(campo, "")
    .replace(/\s+(para|pra|=|:)\s*.+$/i, "")
    .replace(/^(o|a)\s+/i, "")
    .trim();
  if (!nome) {
    const m = texto.match(/(?:do|da|de)\s+(.+?)\s+(?:para|pra|=|:)/i);
    nome = m?.[1]?.trim() ?? "";
  }
  return nome;
}

/** Interpreta comandos do sistema no cadastro de colaboradores. */
export function interpretarComandoColaborador(
  frase: string,
  lista: Colaborador[],
): ResultadoComando {
  const texto = frase.trim();
  const f = fold(texto);
  if (!f) {
    return {
      tipo: "resposta",
      texto: "Digite um comando. Ex.: Maurão é dono, colheiteiro, entregador e granjeiro",
    };
  }

  if (/^(ajuda|help|\?)$/.test(f) || f.includes("o que posso") || f.includes("comandos")) {
    return {
      tipo: "resposta",
      texto:
        "Comandos:\n" +
        "• Maurão é dono, colheiteiro, entregador e granjeiro\n" +
        "• cadastra João 62 98141-2139 como entregador e colheiteiro\n" +
        "• funções do Maurão: dono, entregador\n" +
        "• quem é entregador / lista colheiteiros\n" +
        "• endereço / localização / WhatsApp / inativa\n" +
        "A tela muda na hora; confirme no chat para gravar.",
    };
  }

  if (
    f.startsWith("lista") ||
    f.startsWith("listar") ||
    f.startsWith("mostra") ||
    f.startsWith("quem e") ||
    f.startsWith("quem esta") ||
    f.startsWith("quem sao")
  ) {
    const papeis = extrairPapeis(f);
    const papel = papeis[0];
    const filtrados = lista.filter((item) => {
      if (!item.active && !f.includes("inativ")) return false;
      if (papel && !rolesDe(item).includes(papel)) return false;
      return true;
    });
    if (!filtrados.length) {
      return {
        tipo: "resposta",
        texto: papel ? `Ninguém ativo na função ${labelPapel(papel)}.` : "Nenhum colaborador ativo.",
      };
    }
    if (papel) {
      const linhas = filtrados.map(
        (item) => `• ${item.name} — ${item.phone_e164} (WhatsApp)`,
      );
      return {
        tipo: "resposta",
        texto: `${labelPapel(papel)}:\n${linhas.join("\n")}`,
      };
    }
    const linhas = filtrados.map(
      (item) => `• ${item.name} — ${labels(rolesDe(item))} — ${item.phone_e164}`,
    );
    return { tipo: "resposta", texto: linhas.join("\n") };
  }

  if (/\binativ/.test(f) || /\bdesativ/.test(f)) {
    const nome = texto
      .replace(/^(inativa|inativar|desativa|desativar)\s+(o|a|os|as)?\s*/i, "")
      .trim();
    const achado = acharPorNome(lista, nome);
    if (!achado) {
      return { tipo: "resposta", texto: nome ? `Não achei "${nome}".` : "Diga quem inativar." };
    }
    return {
      tipo: "formulario",
      form: formDe(achado, { active: false }),
      texto: `Vou inativar ${achado.name}. Confirme para gravar.`,
      inativar: true,
    };
  }

  // "Maurão é dono, colheiteiro..." ou "funções do Maurão: ..."
  const ehFuncoes =
    /\b(e|eh|sao|é)\b/.test(f) ||
    /\bfuncoes?\b/.test(f) ||
    /\bpapeis?\b/.test(f) ||
    /\bfuncoes do\b/.test(f);
  const papeisFrase = extrairPapeis(f);
  if (ehFuncoes && papeisFrase.length >= 1) {
    let nome = "";
    const mFuncoes = texto.match(/fun[cç][oõ]es?\s+(?:do|da|de)\s+(.+?)\s*[:\-]/i);
    const mEh = texto.match(/^(.+?)\s+(?:é|e|eh|são|sao)\s+/i);
    if (mFuncoes) nome = mFuncoes[1].trim();
    else if (mEh) nome = mEh[1].replace(/^(o|a)\s+/i, "").trim();
    // remove papéis do nome se vazou
    for (const p of PAPEIS) {
      for (const palavra of p.palavras) {
        nome = nome.replace(new RegExp(`\\b${palavra}\\b`, "ig"), "").trim();
      }
    }
    nome = nome.replace(/\s{2,}/g, " ").replace(/[,:.-]+$/g, "").trim();
    if (!nome) {
      return {
        tipo: "resposta",
        texto: "Diga o nome. Ex.: Maurão é dono, colheiteiro, entregador e granjeiro",
      };
    }
    const achado = acharPorNome(lista, nome);
    if (achado) {
      return {
        tipo: "formulario",
        form: formDe(achado, { roles: papeisFrase }),
        texto: `Funções de ${achado.name}: ${labels(papeisFrase)}. Confirme para gravar.`,
      };
    }
    const telefone = extrairTelefone(texto);
    if (!telefone) {
      return {
        tipo: "resposta",
        texto: `${nome} ainda não está cadastrado. Informe o WhatsApp. Ex.: cadastra ${nome} 62 9… como ${labels(papeisFrase)}`,
      };
    }
    return {
      tipo: "formulario",
      form: {
        name: nome,
        phone: telefone,
        roles: papeisFrase,
        endereco: "",
        localizacao: "",
        active: true,
        notes: "",
      },
      texto: `Cadastro: ${nome} · ${telefone} · ${labels(papeisFrase)}. Confirme para gravar.`,
    };
  }

  if (/\blocaliza/.test(f) || /\bmaps?\b/.test(f)) {
    const url = extrairUrl(texto);
    const valor =
      url ||
      texto
        .replace(/^.*?((localiza[cç][aã]o|maps?)\s+(d[oea]\s+)?)/i, "")
        .replace(/^(do|da|de)\s+/i, "")
        .replace(/^(.+?)\s+(é|e|=|:|para|pra)\s+/i, "")
        .trim();
    let nome = nomeAposCampo(
      texto,
      /^(atualiza|atualizar|muda|mudar)?\s*(a\s+)?(localiza[cç][aã]o|maps?)\s+(d[oea]\s+)?/i,
    );
    if (!nome) {
      const m = texto.match(/(?:do|da|de)\s+(.+?)\s+(?:é|e|=|:|para|pra)\s+/i);
      nome = m?.[1]?.trim() ?? "";
    }
    const achado = acharPorNome(lista, nome);
    if (!achado) {
      return { tipo: "resposta", texto: nome ? `Não achei "${nome}".` : "Diga o nome." };
    }
    if (!valor || fold(valor) === fold(nome)) {
      return { tipo: "resposta", texto: "Informe o link de localização." };
    }
    return {
      tipo: "formulario",
      form: formDe(achado, { localizacao: valor }),
      texto: `Localização de ${achado.name} atualizada. Confirme para gravar.`,
    };
  }

  if (/\bendere[cç]o\b/.test(f)) {
    const m = texto.match(/endere[cç]o\s+(?:do|da|de)\s+(.+?)\s+(?:é|e|=|:|para|pra)\s+(.+)$/i);
    const nome = m?.[1]?.trim() ?? "";
    const endereco = m?.[2]?.trim() ?? "";
    const achado = acharPorNome(lista, nome);
    if (!achado) {
      return {
        tipo: "resposta",
        texto: nome ? `Não achei "${nome}".` : "Ex.: endereço do João é Rua X, 10",
      };
    }
    if (!endereco) return { tipo: "resposta", texto: "Informe o endereço." };
    return {
      tipo: "formulario",
      form: formDe(achado, { endereco }),
      texto: `Endereço de ${achado.name} → ${endereco}. Confirme para gravar.`,
    };
  }

  if (/\bwhatsapp\b|\bcelular\b|\btelefone\b/.test(f) || /\batualiz/.test(f)) {
    const telefone = extrairTelefone(texto);
    if (!telefone) {
      return { tipo: "resposta", texto: "Informe o número." };
    }
    const nome = nomeAposCampo(
      texto,
      /^(atualiza|atualizar|muda|mudar)\s+(o\s+)?(whatsapp|celular|telefone)\s+(d[oea]\s+)?/i,
    );
    const achado = acharPorNome(lista, nome);
    if (!achado) {
      return { tipo: "resposta", texto: nome ? `Não achei "${nome}".` : "Diga o nome." };
    }
    return {
      tipo: "formulario",
      form: formDe(achado, { phone: telefone }),
      texto: `WhatsApp de ${achado.name} → ${telefone}. Confirme para gravar.`,
    };
  }

  if (/\bcadastr|\badicion|\binclui|\bcria|\bnovo\b/.test(f)) {
    const telefone = extrairTelefone(texto);
    const papeis = extrairPapeis(f);
    const roles = papeis.length ? papeis : (["entregador"] as PapelColaborador[]);
    const url = extrairUrl(texto);
    let nome = texto
      .replace(/^(cadastra|cadastrar|adiciona|adicionar|inclui|incluir|cria|criar|novo)\s+/i, "")
      .replace(/\s+(como|papel|funcoes?)\s+.+$/i, "")
      .replace(/(?:\+?55\s*)?(?:\(?\d{2}\)?[\s-]*)?(?:9?\d{4}[\s-]?\d{4})/g, "")
      .replace(/https?:\/\/\S+/gi, "")
      .trim();
    for (const p of PAPEIS) {
      for (const palavra of p.palavras) {
        nome = nome.replace(new RegExp(`\\b${palavra}\\b`, "ig"), "").trim();
      }
    }
    nome = nome.replace(/\s{2,}/g, " ").replace(/^[,.-]+|[,.-]+$/g, "").trim();
    if (!nome) {
      return { tipo: "resposta", texto: "Faltou o nome." };
    }
    if (!telefone) {
      return { tipo: "resposta", texto: `Faltou o WhatsApp de ${nome}.` };
    }
    const existente = acharPorNome(lista, nome);
    if (existente) {
      return {
        tipo: "formulario",
        form: formDe(existente, {
          phone: telefone,
          roles,
          active: true,
          ...(url ? { localizacao: url } : {}),
        }),
        texto: `${existente.name} já existe. Funções: ${labels(roles)}. Confirme para gravar.`,
      };
    }
    return {
      tipo: "formulario",
      form: {
        name: nome,
        phone: telefone,
        roles,
        endereco: "",
        localizacao: url,
        active: true,
        notes: "",
      },
      texto: `Cadastro: ${nome} · ${telefone} · ${labels(roles)}. Confirme para gravar.`,
    };
  }

  return {
    tipo: "resposta",
    texto:
      "Não entendi. Digite ajuda. Ex.: Maurão é dono, colheiteiro, entregador e granjeiro",
  };
}
