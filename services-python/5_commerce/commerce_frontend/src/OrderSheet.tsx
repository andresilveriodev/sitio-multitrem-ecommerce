import { useId, useState, type FocusEvent, type KeyboardEvent, type MouseEvent } from "react";
import type { Cliente } from "./cadastroApi";
import type { Order, OrderItem } from "./types";
import { discountLabel, formatMoney, lineTotal, orderDiscountValue, orderOrderedTotal, orderSubtotal, orderTotal, qtdCobrada, reais } from "./orderMath";

type Props = {
  order: Order;
  catalog: string[];
  clientes: Cliente[];
  onlyWithQty: boolean;
  ordemImpressao: number;
  onChange: (order: Order) => void;
  onCliente: (nome: string, commit: boolean) => void;
  onDelete: () => void;
};

function blankItem(): OrderItem {
  return { produto: "", qtd: 1, valor: 0, conhecido: false };
}

function selecionarCampo(event: FocusEvent<HTMLInputElement>) {
  const campo = event.currentTarget;
  campo.select();
  requestAnimationFrame(() => campo.select());
}

function manterSelecao(event: MouseEvent<HTMLInputElement>) {
  event.preventDefault();
}

function numeroDoCampo(texto: string): number | undefined {
  const normal = texto.trim().replace(",", ".");
  if (normal === "" || normal === ".") return undefined;
  const valor = Number(normal);
  return Number.isFinite(valor) ? valor : undefined;
}

function textoNumero(value: number, vazio: boolean, dinheiro = false): string {
  if (vazio) return "";
  if (dinheiro) return reais(value);
  return String(value).replace(".", ",");
}

function qtdDoCampo(texto: string): Pick<OrderItem, "qtd" | "quantidadeEmBranco"> {
  const qtd = numeroDoCampo(texto);
  if (qtd == null || qtd <= 0) return { qtd: 0, quantidadeEmBranco: true };
  return { qtd, quantidadeEmBranco: false };
}

function CampoNumero({
  value,
  vazio,
  dinheiro = false,
  ariaLabel,
  title,
  onValue,
}: {
  value: number;
  vazio: boolean;
  dinheiro?: boolean;
  ariaLabel?: string;
  title?: string;
  onValue: (texto: string) => void;
}) {
  const [rascunho, setRascunho] = useState<string | null>(null);
  return (
    <input
      type="text"
      inputMode="decimal"
      aria-label={ariaLabel}
      title={title}
      value={rascunho ?? textoNumero(value, vazio, dinheiro)}
      onMouseDown={(event) => {
        event.preventDefault();
        const campo = event.currentTarget;
        campo.focus();
        setRascunho(campo.value);
        campo.select();
      }}
      onFocus={(event) => {
        setRascunho(event.currentTarget.value);
        selecionarCampo(event);
      }}
      onBlur={() => setRascunho(null)}
      onMouseUp={manterSelecao}
      onChange={(event) => {
        setRascunho(event.target.value);
        onValue(event.target.value);
      }}
    />
  );
}

function linhaVisivel(item: OrderItem, onlyWithQty: boolean): boolean {
  return !onlyWithQty || item.qtd > 0 || Boolean(item.quantidadeEmBranco);
}

function dinheiro(valor: number): string {
  return valor > 0 ? formatMoney(valor) : "";
}

function NotaImpressa({ order, items }: { order: Order; items: OrderItem[] }) {
  const comDesconto = items.some((item) => discountLabel(item) !== "");
  const colunas = comDesconto ? 5 : 4;
  const rotulo = colunas - 1;
  const subtotal = orderSubtotal(order);
  const desconto = orderDiscountValue(order);
  const total = orderTotal(order);
  const pedidoValor = orderOrderedTotal(order);
  const cobrouMenos = pedidoValor - total > 0.004;
  return (
    <table className="so-impressao">
      <tbody>
        {order.cliente.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>Nome: {order.cliente}</td>
          </tr>
        ) : null}
        {order.data.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>Data: {order.data}</td>
          </tr>
        ) : null}
        {order.endereco.trim() ? (
          <tr className="topo">
            <td colSpan={colunas}>End.: {order.endereco}</td>
          </tr>
        ) : null}
        <tr>
          <th>Produto</th>
          <th className="qtde">Qtde</th>
          <th className="valor">Preço</th>
          {comDesconto ? <th className="valor">Desc.</th> : null}
          <th className="valor">Val. Tot</th>
        </tr>
        {items.map((item, index) => (
          <tr key={index}>
            <td>{item.produto}</td>
            <td className="qtde">{item.quantidadeEmBranco || !(item.qtd > 0) ? "" : item.qtd}</td>
            <td className="valor">{dinheiro(item.valor)}</td>
            {comDesconto ? <td className="valor">{discountLabel(item)}</td> : null}
            <td className="valor">{dinheiro(lineTotal(item))}</td>
          </tr>
        ))}
        {order.desconto > 0 ? (
          <>
            <tr className="total">
              <td colSpan={rotulo}>SUBTOTAL</td>
              <td className="valor">{formatMoney(subtotal)}</td>
            </tr>
            <tr className="total">
              <td colSpan={rotulo}>DESCONTO {order.desconto}%</td>
              <td className="valor">- {formatMoney(desconto)}</td>
            </tr>
            {cobrouMenos ? (
              <tr className="total">
                <td colSpan={rotulo}>PEDIDO</td>
                <td className="valor">{formatMoney(pedidoValor)}</td>
              </tr>
            ) : null}
            <tr className="total">
              <td colSpan={rotulo}>VALOR DA NOTA</td>
              <td className="valor">{formatMoney(total)}</td>
            </tr>
          </>
        ) : (
          <>
            {cobrouMenos ? (
              <tr className="total">
                <td colSpan={rotulo}>PEDIDO</td>
                <td className="valor">{formatMoney(pedidoValor)}</td>
              </tr>
            ) : null}
            <tr className="total">
              <td colSpan={rotulo}>VALOR DA NOTA</td>
              <td className="valor">{formatMoney(total)}</td>
            </tr>
          </>
        )}
      </tbody>
    </table>
  );
}

export function OrderSheet({ order, catalog, clientes, onlyWithQty, ordemImpressao, onChange, onCliente, onDelete }: Props) {
  const listaClientes = useId();
  const [excluir, setExcluir] = useState(false);
  const [excluirLinha, setExcluirLinha] = useState<number | null>(null);
  const items = order.itens
    .map((item, index) => ({ item, index }))
    .filter(({ item }) => linhaVisivel(item, onlyWithQty));
  const pedidoValor = orderOrderedTotal(order);
  const cobrouMenos = pedidoValor - orderTotal(order) > 0.004;

  function update(patch: Partial<Order>) {
    onChange({ ...order, ...patch });
  }

  function updateItem(index: number, patch: Partial<OrderItem>) {
    const itens = order.itens.map((item, i) => (i === index ? { ...item, ...patch } : item));
    update({ itens });
  }

  function removerLinha(index: number) {
    update({ itens: order.itens.filter((_, i) => i !== index) });
    setExcluirLinha(null);
  }

  const subtotal = orderSubtotal(order);
  const discount = orderDiscountValue(order);
  const total = orderTotal(order);

  const entrega = (item: OrderItem) => (
    <CampoNumero
      value={item.qtdEntregue ?? item.qtd}
      vazio={item.qtdEntregue == null && !(item.qtd > 0)}
      ariaLabel={`Entregue de ${item.produto || "produto"}`}
      title="O que foi entregue. A nota cobra esta quantidade."
      onValue={(texto) => {
        const valor = numeroDoCampo(texto);
        const index = order.itens.indexOf(item);
        updateItem(index, { qtdEntregue: valor == null ? 0 : valor });
      }}
    />
  );

  return (
    <div className="pedido folha" style={{ "--print-order": ordemImpressao } as React.CSSProperties}>
      <div className="caixa screen-only">
      <div className="pedido-acoes no-print">
        {excluir ? (
          <>
            <span>Excluir este pedido?</span>
            <button className="danger" type="button" onClick={onDelete}>
              Confirmar
            </button>
            <button type="button" onClick={() => setExcluir(false)}>
              Cancelar
            </button>
          </>
        ) : (
          <button className="danger" type="button" onClick={() => setExcluir(true)}>
            Excluir
          </button>
        )}
      </div>
      <div className="cabecalho">
        <label className={order.cliente.trim() ? undefined : "missing"}>
          <span>Nome</span>
          <input
            value={order.cliente}
            placeholder="quem pediu"
            list={listaClientes}
            onChange={(event) => onCliente(event.target.value, false)}
            onBlur={(event) => onCliente(event.target.value, true)}
            onKeyDown={(event: KeyboardEvent<HTMLInputElement>) => {
              if (event.key === "Enter") onCliente(event.currentTarget.value, true);
            }}
          />
          <datalist id={listaClientes}>
            {clientes.map((cliente) => (
              <option key={cliente.id} value={cliente.name} />
            ))}
          </datalist>
        </label>
        <label className={order.data.trim() ? undefined : "missing"}>
          <span>Data</span>
          <input
            value={order.data}
            placeholder="DD/MM"
            onChange={(event) => update({ data: event.target.value })}
          />
        </label>
        <label>
          <span>Endereço</span>
          <input
            value={order.endereco}
            onChange={(event) => update({ endereco: event.target.value })}
          />
        </label>
      </div>
      </div>
      <div className="faixa screen-only">
      <div className="nota-linha">
        <div className="miolo titulo">
          <div>Produto</div>
          <div className="num" title="O que foi pedido">Qtde</div>
          <div className="num">Preço</div>
          <div className="num">Desc.</div>
          <div className="num">Val. Tot</div>
          <div />
        </div>
        <div className="entrega-rotulo" title="O que foi entregue. A nota cobra esta quantidade.">Entregue</div>
      </div>
          {items.map(({ item, index }) => {
            const options = catalog.includes(item.produto) || !item.produto ? catalog : [item.produto, ...catalog];
            const entregue = qtdCobrada(item);
            const faltou = item.qtd > 0 && entregue < item.qtd;
            return (
              <div className="nota-linha" key={index}>
              <div className={faltou ? "miolo falta" : item.conhecido === false ? "miolo unknown" : "miolo"}>
                <div className="produto">
                  <span className="print-only">{item.produto}</span>
                  <select
                    className="screen-only"
                    value={item.produto}
                    onChange={(event) =>
                      updateItem(index, {
                        produto: event.target.value,
                        conhecido: catalog.includes(event.target.value),
                      })
                    }
                  >
                    <option value="">—</option>
                    {options.map((name) => (
                      <option key={name} value={name}>
                        {name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="num">
                  <CampoNumero
                    value={item.qtd}
                    vazio={Boolean(item.quantidadeEmBranco)}
                    ariaLabel="Quantidade"
                    onValue={(texto) => updateItem(index, qtdDoCampo(texto))}
                  />
                </div>
                <div className={item.valor > 0 ? "num" : "num missing"}>
                  <CampoNumero
                    value={item.valor}
                    vazio={!(item.valor > 0)}
                    dinheiro
                    ariaLabel="Valor unitário"
                    onValue={(texto) =>
                      updateItem(index, { valor: numeroDoCampo(texto) ?? 0, preco_tabela: false })
                    }
                  />
                  {item.preco_tabela ? <span className="origem">{order.tabela || "tabela"}</span> : null}
                </div>
                <div className="num">
                  <span className="descontos screen-only">
                    <span>R$</span>
                    <CampoNumero
                      ariaLabel="Desconto em reais"
                      title="Desconto em reais por unidade"
                      dinheiro
                      value={item.desconto ?? 0}
                      vazio={item.desconto == null}
                      onValue={(texto) => {
                        const valor = numeroDoCampo(texto);
                        updateItem(index, { desconto: valor == null ? undefined : valor });
                      }}
                    />
                    <span>%</span>
                    <CampoNumero
                      ariaLabel="Desconto percentual"
                      title="Desconto percentual da linha"
                      value={item.descontoPercentual ?? 0}
                      vazio={item.descontoPercentual == null}
                      onValue={(texto) => {
                        const valor = numeroDoCampo(texto);
                        updateItem(index, { descontoPercentual: valor == null ? undefined : valor });
                      }}
                    />
                  </span>
                  <span className="print-only">{discountLabel(item)}</span>
                </div>
                <div className="num">{formatMoney(lineTotal(item))}</div>
                <div className="linha-acao no-print">
                  {excluirLinha === index ? (
                    <span className="confirma-linha">
                      <span>Excluir esta linha?</span>
                      <button className="danger" type="button" onClick={() => removerLinha(index)}>
                        Confirmar
                      </button>
                      <button type="button" onClick={() => setExcluirLinha(null)}>
                        Cancelar
                      </button>
                    </span>
                  ) : (
                    <button className="danger" type="button" onClick={() => setExcluirLinha(index)}>
                      Excluir linha
                    </button>
                  )}
                </div>
              </div>
              <div className={faltou ? "entrega-campo menor" : "entrega-campo"}>{entrega(item)}</div>
              </div>
            );
          })}
          <div className="nota-linha">
            <div className="miolo uma">
              <button type="button" onClick={() => update({ itens: [...order.itens, blankItem()] })}>
                Incluir item
              </button>
            </div>
          </div>
          {order.desconto > 0 ? (
            <>
              <div className="nota-linha">
                <div className="miolo faixa-total">
                  <div>SUBTOTAL</div>
                  <div className="num">{formatMoney(subtotal)}</div>
                  <div />
                </div>
              </div>
              <div className="nota-linha">
                <div className="miolo faixa-total">
                  <div>
                    DESCONTO{" "}
                    <input
                      className="num"
                      type="number"
                      min={0}
                      step="1"
                      value={order.desconto}
                      onChange={(event) => update({ desconto: Number(event.target.value) })}
                    />
                    %
                  </div>
                  <div className="num">- {formatMoney(discount)}</div>
                  <div />
                </div>
              </div>
              {cobrouMenos ? (
                <div className="nota-linha">
                  <div className="miolo faixa-total">
                    <div>PEDIDO</div>
                    <div className="num">{formatMoney(pedidoValor)}</div>
                    <div />
                  </div>
                </div>
              ) : null}
              <div className="nota-linha">
                <div className="miolo faixa-total">
                  <div>VALOR DA NOTA</div>
                  <div className="num">{formatMoney(total)}</div>
                  <div />
                </div>
              </div>
            </>
          ) : (
            <>
              {cobrouMenos ? (
                <div className="nota-linha">
                  <div className="miolo faixa-total">
                    <div>PEDIDO</div>
                    <div className="num">{formatMoney(pedidoValor)}</div>
                    <div />
                  </div>
                </div>
              ) : null}
              <div className="nota-linha">
                <div className="miolo faixa-total">
                  <div>
                    VALOR DA NOTA
                    <span className="no-print">
                      {" "}
                      desconto %{" "}
                      <input
                        className="num"
                        type="number"
                        min={0}
                        step="1"
                        value={order.desconto}
                        onChange={(event) => update({ desconto: Number(event.target.value) })}
                      />
                      %
                    </span>
                  </div>
                  <div className="num">{formatMoney(total)}</div>
                  <div />
                </div>
              </div>
            </>
          )}
      </div>
      <NotaImpressa order={order} items={items.map(({ item }) => item)} />
      <p className="no-print origem">
        A quantidade entregue fica ao lado da nota. A nota cobra o que foi entregue.
      </p>
      <p className="no-print empty">{items.length === 0 ? "Nenhum item neste pedido." : ""}</p>
    </div>
  );
}
