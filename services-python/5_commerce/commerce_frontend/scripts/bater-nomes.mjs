/**
 * Bateria de tipinhos reais: deve achar o cliente/produto cadastrado.
 * Roda: npx tsx scripts/bater-nomes.mjs
 */
import {
  acharClientePorNome,
  listarClientesPorNome,
  pontuarCliente,
  pontuarNome,
} from "../src/nomeCliente.ts";
import { prepararPedidos, comPrecos } from "../src/pedidoConversa.ts";

const API = "http://127.0.0.1:8002/api/v1/cadastro";

const clientes = await (await fetch(`${API}/clientes`)).json();
const tabelas = await (await fetch(`${API}/tabelas`)).json();
const catalogo = { clientes, listas: tabelas.listas, produtos: tabelas.produtos };

let ok = 0;
let falha = 0;
const falhas = [];

function assert(condicao, titulo, detalhe = "") {
  if (condicao) {
    ok += 1;
    console.log(`  OK  ${titulo}`);
  } else {
    falha += 1;
    falhas.push(`${titulo}${detalhe ? ` — ${detalhe}` : ""}`);
    console.log(` FAIL ${titulo}${detalhe ? ` — ${detalhe}` : ""}`);
  }
}

function deveAcharCliente(digitado, esperadoSubstr) {
  const achado = acharClientePorNome(digitado, clientes);
  const lista = listarClientesPorNome(digitado, clientes).map((c) => c.name);
  const hit = achado?.name || "";
  const pass = hit.toLocaleLowerCase("pt-BR").includes(esperadoSubstr.toLocaleLowerCase("pt-BR"));
  assert(
    pass,
    `cliente "${digitado}" → ${esperadoSubstr}`,
    pass ? "" : `obtido: ${hit || `(lista: ${lista.join(" | ") || "vazio"})`}`,
  );
}

function naoDeveAcharClienteUnico(digitado) {
  const achado = acharClientePorNome(digitado, clientes);
  assert(!achado, `cliente "${digitado}" não inventa match único`, achado ? `obtido: ${achado.name}` : "");
}

console.log("\n=== CLIENTES (tipinho → cadastro) ===\n");

// Recanto
deveAcharCliente("RECando Verde", "Recanto Verde");
deveAcharCliente("Recanto Verde", "Recanto Verde");
deveAcharCliente("Recanto", "Recanto Verde");
deveAcharCliente("recanto verde restaurante", "Recanto Verde");
deveAcharCliente("João Batista", "Recanto Verde"); // pessoa cadastrada
deveAcharCliente("Dilma", "Recanto Verde");

// Outros tipinhos comuns
deveAcharCliente("Ademar", "Ademar");
deveAcharCliente("Admar", "Ademar");
deveAcharCliente("Waldeth", "Waldeth");
deveAcharCliente("Waldette", "Waldeth");
deveAcharCliente("Emersom", "Emerson");
deveAcharCliente("Emerson", "Emerson");
deveAcharCliente("Copinhos", "Copinhos");
deveAcharCliente("Copinho Bar", "Copinhos");
deveAcharCliente("Sandu Uai", "Sandu Uai");
deveAcharCliente("Sanduuai", "Sandu Uai");
deveAcharCliente("Edgar", "Sandu Uai");
deveAcharCliente("Hidroponia", "Hidroponia");
deveAcharCliente("Seu Pedro", "Hidroponia");
deveAcharCliente("Jessica pamonharia", "Jessica");
deveAcharCliente("Jessika da Pamonharia", "Jessica");
deveAcharCliente("Brendo Guanabara", "Brendo");
deveAcharCliente("Vando Guanabara", "Vando");
deveAcharCliente("Vandair", "Vando");
deveAcharCliente("Maria Lourdes", "Maria de Lourdes");
deveAcharCliente("Olga Escola", "Olga");
deveAcharCliente("Patricia professora", "Patricia");
deveAcharCliente("Willy Cardoso", "Willy");
deveAcharCliente("Ze Carlos tio", "Zé Carlos");
deveAcharCliente("Zé Carlos", "Zé Carlos");
deveAcharCliente("Jose Carlos Guanabara", "José Carlos");
deveAcharCliente("Alex Lanchonete", "Alex");
deveAcharCliente("Arte Sabor", "Alex");
deveAcharCliente("Reginea", "Regínea");
deveAcharCliente("Euriselia", "Euriselia");
deveAcharCliente("Vera Lucia", "Vera Lucia");
deveAcharCliente("Simone", "Simone");

// Não deve confundir
naoDeveAcharClienteUnico("Verde"); // comum demais
naoDeveAcharClienteUnico("Maria"); // duas Marias
naoDeveAcharClienteUnico("xyzabc");

console.log("\n=== PRODUTOS via prepararPedidos + comPrecos ===\n");

function pedidoComItens(cliente, itens) {
  return [
    {
      cliente,
      data: "16/10",
      endereco: "",
      desconto: 0,
      itens: itens.map((produto) => ({
        produto,
        qtd: 1,
        valor: 0,
      })),
    },
  ];
}

function deveAcharProduto(fraseProduto, esperadoNome, esperadoFormato = null) {
  const bruto = pedidoComItens("Recanto Verde", [fraseProduto]);
  const pronto = comPrecos(prepararPedidos(bruto, `Recanto Verde\n1 ${fraseProduto}`, catalogo), catalogo);
  const item = pronto[0]?.itens?.[0];
  const nome = item?.produto || "";
  const conhecido = item?.conhecido !== false && (item?.valor > 0 || item?.preco_tabela || nome);
  const nomeOk = nome.toLocaleLowerCase("pt-BR").includes(esperadoNome.toLocaleLowerCase("pt-BR"));
  const formatoOk =
    !esperadoFormato ||
    (item?.tipo || "").toLocaleLowerCase("pt-BR") === esperadoFormato.toLocaleLowerCase("pt-BR") ||
    nome.toLocaleLowerCase("pt-BR").includes(`(${esperadoFormato.toLocaleLowerCase("pt-BR")})`);
  assert(
    nomeOk && formatoOk && conhecido,
    `produto "${fraseProduto}" → ${esperadoNome}${esperadoFormato ? ` [${esperadoFormato}]` : ""}`,
    `obtido: ${nome || "(vazio)"} tipo=${item?.tipo || "-"} valor=${item?.valor ?? "-"} conhecido=${item?.conhecido}`,
  );
}

deveAcharProduto("Palito alface roxo", "Alface Roxa", "palito");
deveAcharProduto("alface roxa palito", "Alface Roxa", "palito");
deveAcharProduto("1 palito alface americana", "Alface Americana", "palito");
deveAcharProduto("palito alface crespa", "Alface Crespa", "palito");
deveAcharProduto("palito alface frizze", "Alface Frizze", "palito");
deveAcharProduto("palito alface frise", "Alface Frizze", "palito");
deveAcharProduto("alface americana", "Alface Americana");
deveAcharProduto("rúcula", "Rúcula");
deveAcharProduto("rucula", "Rúcula");
deveAcharProduto("maço de couve", "Couve");
deveAcharProduto("couve", "Couve");
deveAcharProduto("cebolinha", "Cebolinha");
deveAcharProduto("coentro", "Coentro");
deveAcharProduto("salsinha", "Salsinha");
deveAcharProduto("salsa", "Salsinha");
deveAcharProduto("cheiro verde", "Cheiro-verde");
deveAcharProduto("agrião", "Agrião");
deveAcharProduto("agriao", "Agrião");
deveAcharProduto("almeirão", "Almeirão");
deveAcharProduto("espinafre", "Espinafre");
deveAcharProduto("hortelã", "Hortelã");
deveAcharProduto("manjericão", "Manjericão");
deveAcharProduto("brócolis ninja", "Brócolis Ninja");
deveAcharProduto("brocolis piracicaba", "Brócolis Piracicaba");
deveAcharProduto("cartela 30 ovos", "Cartela 30");
deveAcharProduto("cartelas de 30 ovos", "Cartela 30");
deveAcharProduto("dúzia de ovos", "Dúzia");
deveAcharProduto("duzia de ovos", "Dúzia");
deveAcharProduto("jiló", "Jiló");
deveAcharProduto("limão", "Limão");
deveAcharProduto("pão de queijo", "Pão de queijo");
deveAcharProduto("repolho", "Repolho");
deveAcharProduto("rabanete", "Rabanete");
deveAcharProduto("mostarda", "Mostarda");
deveAcharProduto("acelga", "Acelga");

console.log("\n=== PEDIDO COMPLETO Recanto (como na conversa) ===\n");

const conversa = `16/10
RECando Verde

1 Palito alface roxo
1 palito alface americana
1 palito alface crespa
1 palito alface frizze
5 rúcula
12 maço de couve
4 cebolinha
4 coentro`;

const itensBrutos = [
  "Palito alface roxo",
  "palito alface americana",
  "palito alface crespa",
  "palito alface frizze",
  "rúcula",
  "maço de couve",
  "cebolinha",
  "coentro",
].map((produto) => ({ produto, qtd: 1, valor: 0 }));

const pedido = comPrecos(
  prepararPedidos(
    [{ cliente: "RECando Verde", data: "16/10", endereco: "", desconto: 0, itens: itensBrutos }],
    conversa,
    catalogo,
  ),
  catalogo,
)[0];

assert(
  pedido?.cliente?.includes("Recanto Verde") && pedido?.tabela === "Restaurantes",
  `pedido cliente/tabela`,
  `cliente=${pedido?.cliente} tabela=${pedido?.tabela} id=${pedido?.clienteId}`,
);

const esperados = [
  "Alface Roxa",
  "Alface Americana",
  "Alface Crespa",
  "Alface Frizze",
  "Rúcula",
  "Couve",
  "Cebolinha",
  "Coentro",
];
for (const nome of esperados) {
  const item = pedido?.itens?.find((i) => i.produto?.toLocaleLowerCase("pt-BR").includes(nome.toLocaleLowerCase("pt-BR")));
  assert(Boolean(item), `pedido tem ${nome}`, item ? `valor=${item.valor}` : "ausente");
}

const alfacesPalito = (pedido?.itens || []).filter((i) =>
  /alface/i.test(i.produto || ""),
);
assert(alfacesPalito.length === 4, `4 alfaces (sem duplicar roxa)`, `qtd=${alfacesPalito.length}: ${alfacesPalito.map((i) => i.produto).join(", ")}`);

const roxa = alfacesPalito.find((i) => /roxa/i.test(i.produto || ""));
assert(roxa && roxa.valor > 0, `Alface Roxa palito com preço Restaurantes`, `valor=${roxa?.valor ?? "-"}`);

console.log(`\n=== RESULTADO: ${ok} ok, ${falha} falhas ===\n`);
if (falhas.length) {
  console.log("Falhas:");
  for (const f of falhas) console.log(" -", f);
  process.exit(1);
}
