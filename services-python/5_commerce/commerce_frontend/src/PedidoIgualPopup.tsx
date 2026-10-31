import { formatMoney, lineTotal, nomeDiaSemana, orderDiscountValue, orderSubtotal, orderTotal, qtdCobrada } from "./orderMath";
import type { Order } from "./types";

type Props = {
  pedido: Order;
  onFechar: () => void;
};

function qtdTexto(valor: number): string {
  if (Number.isInteger(valor)) return String(valor);
  return valor.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

/** Popup flutuante sem modal: a página continua rolável por baixo. */
export function PedidoIgualPopup({ pedido, onFechar }: Props) {
  const itens = pedido.itens.filter((item) => item.qtd > 0 && item.produto.trim());
  const subtotal = orderSubtotal(pedido);
  const desconto = orderDiscountValue(pedido);
  const total = orderTotal(pedido);
  const dia = nomeDiaSemana(pedido.data);

  return (
    <aside
      className="pedido-igual-popup no-print"
      role="complementary"
      aria-label="Pedido já gravado"
    >
      <header>
        <strong>Pedido já gravado</strong>
        <button type="button" title="Fechar" aria-label="Fechar" onClick={onFechar}>
          ×
        </button>
      </header>
      <div className="pedido-igual-meta">
        <p>
          <span>Nome</span> {pedido.cliente.trim() || "—"}
        </p>
        <p>
          <span>Data</span> {pedido.data.trim() || "—"}
          {dia ? ` (${dia})` : ""}
        </p>
        {pedido.endereco.trim() ? (
          <p>
            <span>End.</span> {pedido.endereco.trim()}
          </p>
        ) : null}
        {pedido.observacao?.trim() ? (
          <p>
            <span>Obs.</span> {pedido.observacao.trim()}
          </p>
        ) : null}
      </div>
      <table>
        <thead>
          <tr>
            <th>Produto</th>
            <th className="num">Qtde</th>
            <th className="num">Preço</th>
            <th className="num">Total</th>
          </tr>
        </thead>
        <tbody>
          {itens.map((item, index) => (
            <tr key={`${item.produto}-${index}`}>
              <td>{item.produto}</td>
              <td className="num">
                {qtdTexto(item.qtd)}
                {qtdCobrada(item) !== item.qtd ? ` / ${qtdTexto(qtdCobrada(item))}` : ""}
              </td>
              <td className="num">{formatMoney(item.valor)}</td>
              <td className="num">{formatMoney(lineTotal(item))}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          {pedido.desconto > 0 ? (
            <>
              <tr>
                <td colSpan={3}>Subtotal</td>
                <td className="num">{formatMoney(subtotal)}</td>
              </tr>
              <tr>
                <td colSpan={3}>Desconto {pedido.desconto}%</td>
                <td className="num">- {formatMoney(desconto)}</td>
              </tr>
            </>
          ) : null}
          <tr>
            <td colSpan={3}>
              <strong>Total</strong>
            </td>
            <td className="num">
              <strong>{formatMoney(total)}</strong>
            </td>
          </tr>
        </tfoot>
      </table>
    </aside>
  );
}
