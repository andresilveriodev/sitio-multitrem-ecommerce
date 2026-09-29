import { useEffect, useState } from "react";
import { consultarBoletas, loadClientes, type Cliente, type Extrato } from "./cadastroApi";
import { formatMoney, reais } from "./orderMath";

function iso(data: Date): string {
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${data.getFullYear()}-${mes}-${dia}`;
}

function semanaAtual(hoje = new Date()): { de: string; ate: string } {
  const dia = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  const segunda = (dia.getDay() + 6) % 7;
  const inicio = new Date(dia);
  inicio.setDate(dia.getDate() - segunda);
  const fim = new Date(inicio);
  fim.setDate(inicio.getDate() + 6);
  return { de: iso(inicio), ate: iso(fim) };
}

function mostrarData(isoData: string): string {
  const [ano, mes, dia] = isoData.split("-");
  if (!dia || !mes) return isoData;
  return ano ? `${dia}/${mes}/${ano}` : `${dia}/${mes}`;
}

function quantidade(qtd: number): string {
  if (Number.isInteger(qtd)) return String(qtd).padStart(2, "0");
  return String(qtd).replace(".", ",");
}

export function Contas() {
  const periodo = semanaAtual();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clienteId, setClienteId] = useState("");
  const [de, setDe] = useState(periodo.de);
  const [ate, setAte] = useState(periodo.ate);
  const [extrato, setExtrato] = useState<Extrato | null>(null);
  const [erro, setErro] = useState("");
  const [buscando, setBuscando] = useState(false);

  async function buscar(inicio = de, fim = ate, cliente = clienteId) {
    setBuscando(true);
    setErro("");
    try {
      const resposta = await consultarBoletas(inicio, fim, cliente ? Number(cliente) : undefined);
      setExtrato(resposta);
    } catch (err) {
      setExtrato(null);
      setErro(err instanceof Error ? err.message : "Não consegui consultar os pedidos.");
    } finally {
      setBuscando(false);
    }
  }

  useEffect(() => {
    loadClientes()
      .then(setClientes)
      .catch(() => undefined);
    void buscar(periodo.de, periodo.ate, "");
  }, []);

  return (
    <section className="cadastro">
      <h1>Contas</h1>
      <p className="no-print">
        Escolha o cliente e o período. O total é o que ele tem para acertar, pelo que foi entregue. A coluna Pedido guarda o que foi pedido.
      </p>
      <form
        className="linha no-print"
        onSubmit={(event) => {
          event.preventDefault();
          void buscar();
        }}
      >
        <select value={clienteId} onChange={(event) => setClienteId(event.target.value)} aria-label="Cliente">
          <option value="">Todos os clientes</option>
          {clientes.map((cliente) => (
            <option key={cliente.id} value={cliente.id}>
              {cliente.name}
            </option>
          ))}
        </select>
        <input type="date" aria-label="De" value={de} onChange={(event) => setDe(event.target.value)} />
        <input type="date" aria-label="Até" value={ate} onChange={(event) => setAte(event.target.value)} />
        <button className="primary" type="submit" disabled={buscando || !de || !ate}>
          {buscando ? "Buscando…" : "Buscar"}
        </button>
        <button type="button" onClick={() => window.print()} disabled={!extrato?.clientes.length}>
          Imprimir
        </button>
      </form>
      {erro ? <p className="error">{erro}</p> : null}
      {extrato && !extrato.clientes.length ? <p className="empty">Nenhum pedido nesse período.</p> : null}
      {extrato && extrato.clientes.length ? (
        <div className="extrato">
          <p className="periodo">
            {mostrarData(extrato.de)} a {mostrarData(extrato.ate)}
            {extrato.clientes.length > 1 ? ` · Total geral ${formatMoney(extrato.total)}` : ""}
          </p>
          {extrato.clientes.map((cliente) => (
            <article key={cliente.id}>
              <h2>{cliente.nome}</h2>
              {cliente.pedidos.map((pedido) => (
                <div className="nota" key={pedido.id}>
                  <strong>
                    {pedido.data}
                    {pedido.endereco ? ` · ${pedido.endereco}` : ""}
                  </strong>
                  <table>
                    <thead>
                      <tr>
                        <th>Produto</th>
                        <th className="num">Pedido</th>
                        <th className="num">Entregue</th>
                        <th className="num">Preço</th>
                        <th className="num">Val. Tot</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pedido.itens.map((item, index) => {
                        const faltou = item.qtd > 0 && item.qtd_entregue < item.qtd;
                        return (
                          <tr key={index} className={faltou ? "falta" : undefined}>
                            <td>{item.produto}</td>
                            <td className="num">{quantidade(item.qtd)}</td>
                            <td className="num">{quantidade(item.qtd_entregue)}</td>
                            <td className="num">{reais(item.valor)}</td>
                            <td className="num">{formatMoney(item.total)}</td>
                          </tr>
                        );
                      })}
                      {pedido.desconto > 0 ? (
                        <tr>
                          <td colSpan={4}>Desconto {pedido.desconto}%</td>
                          <td className="num">{formatMoney(pedido.total)}</td>
                        </tr>
                      ) : null}
                      <tr>
                        <td colSpan={4}>Valor da nota</td>
                        <td className="num">{formatMoney(pedido.total)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              ))}
              <p className="periodo">Total do período: {formatMoney(cliente.total)}</p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
